"""
api.py
FastAPI HTTP 接口，提供 /ask 端点。
运行方式：uvicorn api:app --reload --host 0.0.0.0 --port 8000

请求示例：
    curl -X POST http://localhost:8000/ask \
      -H "Content-Type: application/json" \
      -d '{"question":"什么是指数平滑法？"}'
"""
import hashlib
import hmac
import json
import os
import threading
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from lib.config import load_config
from lib.kb_registry import kb_config, list_knowledge_bases
from lib.pipeline import (
    _init_ask_chat,
    _init_clip_image_store,
    _init_search_system,
    _retrieve_context,
    _retrieve_context_chunks,
)
from lib.search_cache import SearchCache
from lib.session_store import SessionStore

app = FastAPI(
    title="AI-RAG-embed API",
    description="本地知识库 RAG 问答接口",
    version="2.0.0",
)

config = load_config()
_API_KEY = os.getenv("RAG_API_KEY", "").strip()
_API_KEYS_RAW = os.getenv("RAG_API_KEYS", "").strip()
_system_cache: dict[str, object] | None = {}
_search_system_cache: dict[str, object] | None = {}
_clip_search_system_cache: dict[str, object | None] | None = {}
_search_cache: dict[str, SearchCache] | None = {}
_search_cache_fingerprint: dict[str, str] | None = {}
_init_lock = threading.RLock()
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_KNOWLEDGE_GAPS_PATH = os.path.join(_PROJECT_DIR, "logs", "knowledge_gaps.jsonl")


def _parse_api_keys(raw: str) -> dict[str, str]:
    """Parse optional per-user API keys from JSON or comma-separated pairs."""
    if not raw:
        return {}
    if raw.lstrip().startswith("{"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return {
            str(user).strip(): str(key).strip()
            for user, key in data.items()
            if str(user).strip() and str(key).strip()
        }

    pairs: dict[str, str] = {}
    for item in raw.replace("\n", ",").split(","):
        item = item.strip()
        if not item:
            continue
        sep = ":" if ":" in item else "="
        if sep not in item:
            continue
        user, key = item.split(sep, 1)
        user = user.strip()
        key = key.strip()
        if user and key:
            pairs[user] = key
    return pairs


_API_KEYS = _parse_api_keys(_API_KEYS_RAW)
_API_KEYS_CONFIG_INVALID = bool(_API_KEYS_RAW and not _API_KEYS)


def _verify_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> str:
    if _API_KEYS_CONFIG_INVALID:
        raise HTTPException(status_code=500, detail="RAG_API_KEYS is invalid.")

    auth_user = "anonymous"
    if _API_KEYS:
        supplied = x_api_key or ""
        for user, expected in _API_KEYS.items():
            if hmac.compare_digest(supplied, expected):
                auth_user = user
                break
        else:
            raise HTTPException(status_code=403, detail="Invalid or missing API key.")
    elif _API_KEY:
        if not hmac.compare_digest(x_api_key or "", _API_KEY):
            raise HTTPException(status_code=403, detail="Invalid or missing API key.")
        auth_user = "default"

    request.state.auth_user = auth_user
    return auth_user


def _auth_user_from_request(request: Request) -> str:
    return getattr(request.state, "auth_user", "anonymous")


def _auth_user_is_scoped(auth_user: str | None) -> bool:
    return bool(auth_user and auth_user not in {"anonymous", "default"})


def _normalize_kb_name(kb_name: str | None) -> str:
    return (kb_name or "default").strip() or "default"


def _get_config_for_kb(kb_name: str) -> dict:
    return kb_config(config, kb_name)


def _get_system(kb_name: str = "default"):
    global _system_cache
    kb_name = _normalize_kb_name(kb_name)
    if _system_cache is None or not isinstance(_system_cache, dict):
        _system_cache = {}
    if kb_name not in _system_cache:
        with _init_lock:
            if kb_name not in _system_cache:
                try:
                    _system_cache[kb_name] = _init_ask_chat(_get_config_for_kb(kb_name))
                except Exception as e:
                    raise RuntimeError(f"系统初始化失败：{e}") from e
    return _system_cache[kb_name]


def _get_search_system(kb_name: str = "default"):
    global _search_system_cache
    kb_name = _normalize_kb_name(kb_name)
    if _search_system_cache is None or not isinstance(_search_system_cache, dict):
        _search_system_cache = {}
    if kb_name not in _search_system_cache:
        with _init_lock:
            if kb_name not in _search_system_cache:
                try:
                    _search_system_cache[kb_name] = _init_search_system(_get_config_for_kb(kb_name))
                except Exception as e:
                    raise RuntimeError(f"检索系统初始化失败：{e}") from e
    return _search_system_cache[kb_name]


def _get_clip_search_system(kb_name: str = "default"):
    global _clip_search_system_cache
    kb_name = _normalize_kb_name(kb_name)
    active_config = _get_config_for_kb(kb_name)
    if not active_config.get("clip_image_enabled", False):
        return None
    if _clip_search_system_cache is None or not isinstance(_clip_search_system_cache, dict):
        _clip_search_system_cache = {}
    if kb_name not in _clip_search_system_cache:
        with _init_lock:
            if kb_name not in _clip_search_system_cache:
                try:
                    _clip_search_system_cache[kb_name] = _init_clip_image_store(active_config)
                except Exception:
                    _clip_search_system_cache[kb_name] = None
    return _clip_search_system_cache[kb_name]


def _float_config(name: str, default: float, active_config: dict | None = None) -> float:
    cfg = active_config or config
    value = cfg.get(name, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _confidence_level(chunks: list[dict], active_config: dict | None = None) -> str:
    if not chunks:
        return "low"
    distances = [
        c.get("distance")
        for c in chunks
        if isinstance(c.get("distance"), int | float)
    ]
    if not distances:
        return "low"

    best = min(distances)
    high_threshold = _float_config("confidence_high_threshold", 0.2, active_config)
    low_threshold = _float_config(
        "confidence_low_threshold",
        _float_config("search_distance_threshold", 0.4, active_config),
        active_config,
    )
    high_threshold = min(high_threshold, low_threshold)
    if best < high_threshold:
        return "high"
    if best < low_threshold:
        return "medium"
    return "low"


def _is_low_confidence(chunks: list[dict]) -> bool:
    return _confidence_level(chunks) == "low"


def _stream_sources(chunks: list[dict]) -> list[dict]:
    sources = []
    seen_sources: set[str] = set()
    for chunk in chunks:
        source = chunk.get("source") or "unknown"
        if source in seen_sources:
            continue
        seen_sources.add(source)
        sources.append({"source": source, "page": chunk.get("page")})
    return sources


def _log_knowledge_gap(question: str, searched_question: str, kb_name: str = "default") -> None:
    os.makedirs(os.path.dirname(_KNOWLEDGE_GAPS_PATH), exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "original": question,
        "searched": searched_question,
        "kb": kb_name,
    }
    with open(_KNOWLEDGE_GAPS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _get_positive_int_config(name: str, default: int, active_config: dict | None = None) -> int:
    cfg = active_config or config
    value = cfg.get(name, default)
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


_session_store = SessionStore(
    ttl_seconds=_get_positive_int_config("session_ttl_seconds", 3600),
    max_sessions=_get_positive_int_config("session_max_count", 500),
)


_RETRIEVAL_FINGERPRINT_FIELDS: list[str] = [
    "embedding_model_name",
    "docs_dir",
    "chroma_persist_dir",
    "retrieval_k",
    "retrieval_candidate_k",
    "bm25_enabled",
    "rerank_enabled",
    "rerank_model_name",
    "rerank_top_n",
    "search_distance_threshold",
    "confidence_high_threshold",
    "confidence_low_threshold",
    "query_enhance_enabled",
    "enhancer_mode",
    "translator_source_lang",
    "translator_target_lang",
    "clip_image_enabled",
    "clip_model_name",
    "clip_retrieval_k",
    "parent_child_enabled",
    "multi_query_enabled",
    "multi_query_n",
    "child_chunk_size",
    "child_chunk_overlap",
]


def _compute_config_fingerprint(active_config: dict | None = None) -> str:
    """Build a stable hash from retrieval-affecting config fields.

    Only the listed fields are included; API keys and secrets are excluded.
    """
    cfg = active_config or config
    parts: list[str] = []
    for field in _RETRIEVAL_FINGERPRINT_FIELDS:
        value = cfg.get(field)
        parts.append(f"{field}={value}")
    joined = ";".join(parts)
    return hashlib.md5(joined.encode("utf-8")).hexdigest()


def _get_search_cache(kb_name: str = "default") -> SearchCache:
    global _search_cache, _search_cache_fingerprint
    kb_name = _normalize_kb_name(kb_name)
    active_config = _get_config_for_kb(kb_name)
    if _search_cache is None or not isinstance(_search_cache, dict):
        _search_cache = {}
    if _search_cache_fingerprint is None or not isinstance(_search_cache_fingerprint, dict):
        _search_cache_fingerprint = {}
    fingerprint = _compute_config_fingerprint(active_config)
    if _search_cache.get(kb_name) is None or _search_cache_fingerprint.get(kb_name) != fingerprint:
        with _init_lock:
            active_config = _get_config_for_kb(kb_name)
            fingerprint = _compute_config_fingerprint(active_config)
            if _search_cache.get(kb_name) is None or _search_cache_fingerprint.get(kb_name) != fingerprint:
                _search_cache[kb_name] = SearchCache(
                    max_size=_get_positive_int_config("cache_max_size", 200, active_config),
                    ttl_seconds=_get_positive_int_config("cache_ttl_seconds", 3600, active_config),
                    config_fingerprint=fingerprint,
                )
                _search_cache_fingerprint[kb_name] = fingerprint
    return _search_cache[kb_name]


class HistoryTurn(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str
    history: list[HistoryTurn] = Field(default_factory=list)
    session_id: str | None = Field(default=None)
    kb_name: str | None = Field(default=None)


class ContextChunk(BaseModel):
    text: str
    source: str
    file_type: str | None = None
    page: int | None = None
    chunk_index: int | None = None
    image_index: int | None = None
    distance: float | None = None
    rerank_score: float | None = None
    rrf_score: float | None = None
    retrieval_path: str | None = None


class AskResponse(BaseModel):
    answer: str
    rewritten_question: str
    contexts: list[ContextChunk]
    confidence: str


class SearchResponse(BaseModel):
    original_question: str
    searched_question: str
    confidence: str
    low_confidence: bool
    chunks: list[ContextChunk]


@app.get("/")
def root():
    return {"status": "ok", "service": "AI-RAG-embed API"}


@app.get("/knowledge-bases", dependencies=[Depends(_verify_api_key)])
def list_kbs():
    return {"knowledge_bases": list_knowledge_bases()}


@app.get("/cache/stats", dependencies=[Depends(_verify_api_key)])
def cache_stats(kb_name: str | None = Query(default=None)):
    resolved_kb, _ = _resolve_request_kb(kb_name)
    cache = _get_search_cache(resolved_kb)
    return {
        "kb_name": resolved_kb,
        "cached_queries": len(cache),
        "max_size": cache.max_size,
        "ttl_seconds": cache.ttl_seconds,
    }


@app.post("/cache/clear", dependencies=[Depends(_verify_api_key)])
def cache_clear(kb_name: str | None = Query(default=None)):
    resolved_kb, _ = _resolve_request_kb(kb_name)
    _get_search_cache(resolved_kb).clear()
    return {"status": "cleared", "kb_name": resolved_kb}


@app.delete("/session/{session_id}", dependencies=[Depends(_verify_api_key)])
def delete_session(
    session_id: str,
    request: Request,
    kb_name: str | None = Query(default=None),
):
    resolved_kb, _ = _resolve_request_kb(kb_name)
    store_key = _session_store_key(
        resolved_kb,
        session_id,
        _auth_user_from_request(request),
    )
    existed = _session_store.clear_session(store_key)
    return {"session_id": session_id, "cleared": existed}


@app.get("/session/{session_id}/history", dependencies=[Depends(_verify_api_key)])
def get_session_history(
    session_id: str,
    request: Request,
    kb_name: str | None = Query(default=None),
):
    resolved_kb, _ = _resolve_request_kb(kb_name)
    store_key = _session_store_key(
        resolved_kb,
        session_id,
        _auth_user_from_request(request),
    )
    history = _session_store.get_history(store_key)
    return {
        "session_id": session_id,
        "kb_name": resolved_kb,
        "turns": len(history) // 2,
        "history": history,
    }


@app.get("/sessions/stats", dependencies=[Depends(_verify_api_key)])
def sessions_stats():
    return {"active_sessions": _session_store.session_count()}


@app.get("/index/status", dependencies=[Depends(_verify_api_key)])
def index_status(kb_name: str | None = Query(default=None)):
    """Return index status without initializing embedding models."""
    resolved_kb, active_config = _resolve_request_kb(kb_name)
    raw = active_config.get("chroma_persist_dir", "./chroma_db")
    if raw.startswith("./") or raw.startswith(".\\"):
        persist_dir = os.path.join(_PROJECT_DIR, raw[2:])
    else:
        persist_dir = raw

    exists = os.path.isdir(persist_dir)
    result: dict = {
        "kb_name": resolved_kb,
        "exists": exists,
        "persist_dir": persist_dir,
        "total_chunks": 0,
        "source_count": 0,
        "sources": {},
        "file_index_exists": False,
        "indexed_files": 0,
        "total_file_chunks": 0,
    }

    if not exists:
        return result

    # ChromaDB statistics. This intentionally avoids embedder initialization.
    try:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection(name="documents")
        result["total_chunks"] = collection.count()

        get_result = collection.get(include=["metadatas"])
        sources: dict[str, int] = {}
        for meta in get_result["metadatas"]:
            if not meta:
                continue
            source = meta.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        result["sources"] = sources
        result["source_count"] = len(sources)
    except Exception:
        # ChromaDB may not be fully initialized; return partial stats.
        pass

    file_index_path = os.path.join(persist_dir, "file_index.json")
    if os.path.isfile(file_index_path):
        result["file_index_exists"] = True
        try:
            with open(file_index_path, "r", encoding="utf-8") as f:
                file_index = json.load(f)
            result["indexed_files"] = len(file_index)
            result["total_file_chunks"] = sum(
                v.get("chunk_count", 0) for v in file_index.values()
            )
        except Exception:
            pass

    return result


def _session_store_key(
    kb_name: str,
    session_id: str,
    auth_user: str | None = None,
) -> str:
    if _auth_user_is_scoped(auth_user):
        return f"user:{auth_user}:kb:{kb_name}:session:{session_id}"
    if kb_name == "default":
        return session_id
    return f"kb:{kb_name}:session:{session_id}"


def _messages_history_from_request(
    req: AskRequest,
    kb_name: str,
    auth_user: str | None = None,
) -> list[dict] | None:
    if req.session_id:
        return _session_store.get_history(
            _session_store_key(kb_name, req.session_id, auth_user)
        ) or None
    return [turn.model_dump() for turn in req.history] or None


def _resolve_request_kb(kb_name: str | None) -> tuple[str, dict]:
    resolved = _normalize_kb_name(kb_name)
    try:
        active_config = _get_config_for_kb(resolved)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return resolved, active_config


@app.post("/ask", response_model=AskResponse, dependencies=[Depends(_verify_api_key)])
def ask(req: AskRequest, request: Request):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question 不能为空")

    kb_name, active_config = _resolve_request_kb(req.kb_name)
    try:
        store, parent_store, llm, query_enhancer, multi_query_enhancer, system_prompt, reranker, bm25_index = _get_system(kb_name)
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail="RAG ask system initialization failed.",
        ) from e
    auth_user = _auth_user_from_request(request)
    history = _messages_history_from_request(req, kb_name, auth_user)
    chunks, messages, rewritten_question = _retrieve_context(
        store=store,
        llm=llm,
        question=req.question,
        messages_history=history,
        system_prompt=system_prompt,
        retrieval_k=_get_positive_int_config("retrieval_k", 5, active_config),
        query_enhancer=query_enhancer,
        reranker=reranker,
        rerank_top_n=_get_positive_int_config("rerank_top_n", 5, active_config),
        max_context_chars=active_config.get("max_context_chars", 6000),
        bm25_index=bm25_index,
        retrieval_candidate_k=active_config.get("retrieval_candidate_k"),
        parent_store=parent_store,
        multi_query_enhancer=multi_query_enhancer,
    )

    confidence = _confidence_level(chunks, active_config)

    if not chunks:
        answer = "没有检索到相关内容。"
        if req.session_id:
            _session_store.append_turn(
                _session_store_key(kb_name, req.session_id, auth_user),
                req.question,
                answer,
            )
        return AskResponse(
            answer=answer,
            rewritten_question=rewritten_question,
            contexts=[],
            confidence=confidence,
        )

    try:
        answer = llm.generate(messages)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=(
                "LLM generation failed. Check llm.api_key, "
                "api_base_url, and model configuration."
            ),
        ) from e

    if req.session_id:
        _session_store.append_turn(
            _session_store_key(kb_name, req.session_id, auth_user),
            req.question,
            answer,
        )

    context_items = [
        ContextChunk(
            text=c["text"],
            source=c.get("source", "unknown"),
            file_type=c.get("file_type"),
            page=c.get("page"),
            chunk_index=c.get("chunk_index"),
            image_index=c.get("image_index"),
            distance=c.get("distance"),
            rerank_score=c.get("rerank_score"),
            rrf_score=c.get("rrf_score"),
            retrieval_path=c.get("retrieval_path"),
        )
        for c in chunks
    ]

    return AskResponse(
        answer=answer,
        rewritten_question=rewritten_question,
        contexts=context_items,
        confidence=confidence,
    )


@app.post("/ask/stream", dependencies=[Depends(_verify_api_key)])
def ask_stream(req: AskRequest, request: Request):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question 不能为空")

    kb_name, active_config = _resolve_request_kb(req.kb_name)
    try:
        store, parent_store, llm, query_enhancer, multi_query_enhancer, system_prompt, reranker, bm25_index = _get_system(kb_name)
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail="RAG ask system initialization failed.",
        ) from e
    auth_user = _auth_user_from_request(request)

    def generate():
        try:
            history = _messages_history_from_request(req, kb_name, auth_user)
            chunks, messages, rewritten_question = _retrieve_context(
                store=store,
                llm=llm,
                question=req.question,
                messages_history=history,
                system_prompt=system_prompt,
                retrieval_k=_get_positive_int_config("retrieval_k", 5, active_config),
                query_enhancer=query_enhancer,
                reranker=reranker,
                rerank_top_n=_get_positive_int_config("rerank_top_n", 5, active_config),
                max_context_chars=active_config.get("max_context_chars", 6000),
                bm25_index=bm25_index,
                retrieval_candidate_k=active_config.get("retrieval_candidate_k"),
                parent_store=parent_store,
                multi_query_enhancer=multi_query_enhancer,
            )
        except Exception:
            yield f"data: {json.dumps({'type': 'error', 'error': 'Context retrieval failed.'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            return

        metadata = {
            "type": "metadata",
            "confidence": _confidence_level(chunks, active_config),
            "rewritten_question": rewritten_question,
            "sources": _stream_sources(chunks),
        }
        yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"

        if not chunks:
            answer = "没有检索到相关内容。"
            if req.session_id:
                _session_store.append_turn(
                    _session_store_key(kb_name, req.session_id, auth_user),
                    req.question,
                    answer,
                )
            yield f"data: {json.dumps({'type': 'token', 'token': answer}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            return

        full_answer_parts = []
        try:
            for token in llm.generate_stream(messages):
                full_answer_parts.append(token)
                yield f"data: {json.dumps({'type': 'token', 'token': token}, ensure_ascii=False)}\n\n"
        except Exception:
            yield f"data: {json.dumps({'type': 'error', 'error': 'LLM generation failed.'}, ensure_ascii=False)}\n\n"
        else:
            if req.session_id and full_answer_parts:
                _session_store.append_turn(
                    _session_store_key(kb_name, req.session_id, auth_user),
                    req.question,
                    "".join(full_answer_parts),
                )

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/search", response_model=SearchResponse, dependencies=[Depends(_verify_api_key)])
def search(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question 不能为空")

    kb_name, active_config = _resolve_request_kb(req.kb_name)
    try:
        store, parent_store, query_enhancer, multi_query_enhancer, reranker, bm25_index = _get_search_system(kb_name)
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail="RAG search system initialization failed.",
        ) from e

    searched_question = req.question
    if query_enhancer:
        try:
            history = [turn.model_dump() for turn in req.history]
            searched_question = query_enhancer.enhance(req.question, history=history)
        except Exception:
            pass

    cache = _get_search_cache(kb_name)
    chunks = cache.get(searched_question)

    if chunks is None:
        retrieval_k = _get_positive_int_config("retrieval_k", 6, active_config)

        # Build config dict for _retrieve_context_chunks.
        # Note: we do NOT pass query_enhancer here because we already enhanced
        # the question above (searched_question).
        metric_config = {
            "retrieval_k": retrieval_k,
            "rerank_top_n": _get_positive_int_config("rerank_top_n", 5, active_config),
            "retrieval_candidate_k": active_config.get("retrieval_candidate_k"),
        }

        chunks, _ = _retrieve_context_chunks(
            store=store,
            question=searched_question,
            config=metric_config,
            reranker=reranker,
            bm25_index=bm25_index,
            parent_store=parent_store,
            multi_query_enhancer=multi_query_enhancer,
        )

        # ── CLIP image retrieval ───────────────────────────────
        if active_config.get("clip_image_enabled", False):
            clip_store = _get_clip_search_system(kb_name)
        else:
            clip_store = None
        if clip_store is not None:
            try:
                image_chunks = clip_store.query(
                    searched_question,
                    k=_get_positive_int_config("clip_retrieval_k", 3, active_config),
                )
            except Exception:
                image_chunks = []
            for c in image_chunks:
                c["retrieval_path"] = "clip_image"
            chunks.extend(image_chunks)

        cache.set(searched_question, chunks)

    confidence = _confidence_level(chunks, active_config)
    if confidence == "low":
        _log_knowledge_gap(req.question, searched_question, kb_name=kb_name)

    return {
        "original_question": req.question,
        "searched_question": searched_question,
        "confidence": confidence,
        "low_confidence": confidence == "low",
        "chunks": [
            {
                "text": c["text"],
                "source": c.get("source", "unknown"),
                "file_type": c.get("file_type"),
                "page": c.get("page"),
                "chunk_index": c.get("chunk_index"),
                "image_index": c.get("image_index"),
                "distance": c.get("distance"),
                "rerank_score": c.get("rerank_score"),
                "rrf_score": c.get("rrf_score"),
                "retrieval_path": c.get("retrieval_path"),
            }
            for c in chunks
        ],
    }
