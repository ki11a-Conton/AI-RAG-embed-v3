"""
vector_db.py
Chroma 向量数据库封装，支持结构化元数据存储与检索结果返回。
query() 返回包含 text/source/page/chunk_index/distance 的字典列表。
"""
import uuid

import chromadb
from chromadb.api.types import EmbeddingFunction
from chromadb.config import Settings


class _DummyEmbeddingFunction(EmbeddingFunction):
    """No-op embedding function that returns fixed-dimension zero vectors.

    Used by ParentStore to prevent Chroma from downloading the default
    sentence-transformers model.  The vectors are never queried／searched,
    so the actual values don't matter.
    """

    def __init__(self):
        pass

    def __call__(self, input):
        return [[0.0] * 384] * len(input)

    @staticmethod
    def name():
        return "parent-store-dummy"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return _DummyEmbeddingFunction()


class VectorDb:
    def __init__(self, persist_dir: str, embed_engine):
        self._embed_engine = embed_engine
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

    def rebuild(self, chunks: list[dict]) -> None:
        """
        重建向量索引（分批处理，控制内存峰值）。
        chunks 格式：[{"text": str, "metadata": {"source": str, "file_type": str, "chunk_index": int, "page": int|None}}]
        兼容旧格式：[{"text": str, "source": str}]
        """
        BATCH_SIZE = 256

        try:
            self._client.delete_collection("documents")
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

        for batch_start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[batch_start: batch_start + BATCH_SIZE]
            texts = []
            metadatas = []
            ids = []

            for i, chunk in enumerate(batch):
                global_i = batch_start + i
                text = chunk["text"]
                # 兼容旧格式
                if "metadata" in chunk:
                    meta = chunk["metadata"]
                else:
                    meta = {"source": chunk.get("source", "unknown"), "file_type": "unknown", "chunk_index": global_i, "page": None}

                # Chroma 不允许 metadata value 为 None，转成 -1
                safe_meta = {
                    "source": meta.get("source", "unknown"),
                    "file_type": meta.get("file_type", "unknown"),
                    "chunk_index": meta.get("chunk_index", global_i),
                    "page": meta.get("page") if meta.get("page") is not None else -1,
                }
                # Preserve parent-child metadata so pipeline can replace child text with parent text.
                if "parent_id" in meta:
                    safe_meta["parent_id"] = meta["parent_id"]
                if "chunk_role" in meta:
                    safe_meta["chunk_role"] = meta["chunk_role"]

                texts.append(text)
                metadatas.append(safe_meta)
                ids.append(str(uuid.uuid4()))

            embeddings = self._embed_engine.embed_batch(texts)

            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

    def query(self, question: str, k: int = 5) -> list[dict]:
        """
        检索最相关的 k 个 chunk。

        返回：
            list of {
                "text": str,
                "source": str,
                "file_type": str,
                "chunk_index": int,
                "page": int|None,
                "distance": float,
            }
        """
        if k <= 0:
            return []
        total = self._collection.count()
        if total == 0:
            return []
        # Chroma 要求 n_results <= 集合中文档数，否则抛异常
        n = min(k, total)

        question_embedding = self._embed_engine.get_embedding(question)

        results = self._collection.query(
            query_embeddings=[question_embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        output = []
        for doc, meta, distance in zip(docs, metas, distances):
            meta = meta or {}
            page = meta.get("page")
            if page == -1:
                page = None
            output.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "file_type": meta.get("file_type", "unknown"),
                "chunk_index": meta.get("chunk_index"),
                "page": page,
                "distance": round(float(distance), 4),
                "parent_id": meta.get("parent_id"),
                "chunk_role": meta.get("chunk_role"),
            })

        return output

    def count(self) -> int:
        return self._collection.count()

    def get_indexed_sources(self) -> set[str]:
        """返回已索引的所有文件来源路径集合"""
        result = self._collection.get(include=["metadatas"])
        return {m["source"] for m in result["metadatas"] if m}

    def get_source_stats(self) -> dict[str, int]:
        """返回每个已索引 source 对应的 chunk 数。"""
        result = self._collection.get(include=["metadatas"])
        stats: dict[str, int] = {}
        for meta in result["metadatas"]:
            if not meta:
                continue
            source = meta.get("source", "unknown")
            stats[source] = stats.get(source, 0) + 1
        return stats

    def delete_by_source(self, source: str) -> int:
        """Delete all chunks whose metadata.source exactly matches source."""
        result = self._collection.get(
            where={"source": source},
            include=["metadatas"],
        )
        ids = result.get("ids", [])
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    def add_chunks(self, chunks: list[dict]) -> None:
        """
        增量添加新 chunks（不清空旧数据）。
        chunks 格式同 rebuild()。
        """
        BATCH_SIZE = 256
        existing_count = self._collection.count()

        for batch_start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[batch_start: batch_start + BATCH_SIZE]
            texts = []
            metadatas = []
            ids = []

            for i, chunk in enumerate(batch):
                global_i = existing_count + batch_start + i
                text = chunk["text"]
                if "metadata" in chunk:
                    meta = chunk["metadata"]
                else:
                    meta = {"source": chunk.get("source", "unknown"), "file_type": "unknown", "chunk_index": global_i, "page": None}

                safe_meta = {
                    "source": meta.get("source", "unknown"),
                    "file_type": meta.get("file_type", "unknown"),
                    "chunk_index": meta.get("chunk_index", global_i),
                    "page": meta.get("page") if meta.get("page") is not None else -1,
                }
                # Preserve parent-child metadata so pipeline can replace child text with parent text.
                if "parent_id" in meta:
                    safe_meta["parent_id"] = meta["parent_id"]
                if "chunk_role" in meta:
                    safe_meta["chunk_role"] = meta["chunk_role"]

                texts.append(text)
                metadatas.append(safe_meta)
                ids.append(str(uuid.uuid4()))

            embeddings = self._embed_engine.embed_batch(texts)

            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )


class ParentStore:
    """只存父块，按 parent_id 查询，不做向量检索。"""

    def __init__(self, persist_dir: str):
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            "parent_chunks",
            embedding_function=_DummyEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )

    def rebuild(self, parent_chunks: list[dict]) -> None:
        """清空并重建父块存储。"""
        try:
            self._client.delete_collection("parent_chunks")
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(
            "parent_chunks",
            embedding_function=_DummyEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )
        if parent_chunks:
            self.add_chunks(parent_chunks)

    def add_chunks(self, parent_chunks: list[dict]) -> None:
        """增量添加父块。"""
        BATCH_SIZE = 256
        for batch_start in range(0, len(parent_chunks), BATCH_SIZE):
            batch = parent_chunks[batch_start: batch_start + BATCH_SIZE]
            texts = []
            metadatas = []
            ids = []
            for chunk in batch:
                text = chunk["text"]
                meta = chunk.get("metadata", {})
                safe_meta = {
                    "source": meta.get("source", "unknown"),
                    "file_type": meta.get("file_type", "unknown"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "page": meta.get("page") if meta.get("page") is not None else -1,
                    "chunk_role": meta.get("chunk_role", "parent"),
                    "parent_id": meta.get("parent_id", ""),
                }
                texts.append(text)
                metadatas.append(safe_meta)
                ids.append(str(uuid.uuid4()))
            self._collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
            )

    def get_by_parent_ids(self, parent_ids: list[str]) -> list[dict]:
        """按 parent_id 批量取出父块。返回 list[dict]，每个 dict 有 text 和 metadata。"""
        if not parent_ids:
            return []
        results = []
        # Chroma where $in 一次最多处理一定数量，分批
        BATCH_SIZE = 100
        for batch_start in range(0, len(parent_ids), BATCH_SIZE):
            batch_ids = parent_ids[batch_start: batch_start + BATCH_SIZE]
            try:
                fetched = self._collection.get(
                    where={"parent_id": {"$in": batch_ids}},
                    include=["documents", "metadatas"],
                )
            except Exception:
                continue
            docs = fetched.get("documents", [])
            metas = fetched.get("metadatas", [])
            for doc, meta in zip(docs, metas):
                meta = meta or {}
                page = meta.get("page")
                if page == -1:
                    page = None
                results.append({
                    "text": doc,
                    "metadata": {
                        "source": meta.get("source", "unknown"),
                        "file_type": meta.get("file_type", "unknown"),
                        "chunk_index": meta.get("chunk_index"),
                        "page": page,
                        "chunk_role": meta.get("chunk_role", "parent"),
                        "parent_id": meta.get("parent_id", ""),
                    },
                })
        return results

    def delete_by_source(self, source: str) -> int:
        """删除某个文件对应的所有父块。"""
        result = self._collection.get(
            where={"source": source},
            include=["metadatas"],
        )
        ids = result.get("ids", [])
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    def count(self) -> int:
        return self._collection.count()
