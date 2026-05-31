"""
app.py
Streamlit Web UI for AI-RAG-embed.
运行方式：streamlit run app.py
"""
import os
import hashlib
import json

import streamlit as st

from lib.config import load_config, resolve_path as _resolve_path
from lib.kb_registry import kb_config, list_knowledge_bases
from lib.kb_status import get_kb_status
from lib.upload_safety import find_upload_conflicts, save_uploaded_files
from rag_runner import (
    cmd_build,
    _init_ask_chat,
    _retrieve_context,
    _format_source_citation,
)

st.set_page_config(
    page_title="AI-RAG-embed",
    page_icon="📚",
    layout="wide",
)

st.title("📚 AI-RAG-embed 本地知识库问答")
st.caption("支持 TXT / Markdown / PDF / DOCX / HTML / CSV · 本地 Embedding · 来源引用")

# ──────────────────────────────────────────────
# Bug 2 修复：config 提升到模块级，确保后续代码全局可用
# 原来 config 定义在 sidebar 的 try 块内，若 st.stop() 前代码执行完
# 但后面 _retrieve_context 调用时 config 可能未定义 -> NameError
# ──────────────────────────────────────────────
try:
    config = load_config()
except FileNotFoundError:
    st.error("❌ 未找到 config.json，请先复制 config_example.json 并填写配置。")
    st.stop()
except Exception as e:
    st.error(f"❌ 配置加载失败：{e}")
    st.stop()

# ──────────────────────────────────────────────
# 侧边栏：系统信息
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 系统配置")
    st.success("✅ config.json 加载成功")

    available_kbs = list_knowledge_bases()
    if len(available_kbs) > 1:
        selected_kb = st.selectbox(
            "🗂️ 选择知识库",
            options=available_kbs,
            index=0,
            key="selected_kb",
        )
    else:
        selected_kb = "default"
        st.caption("知识库：default（单库模式）")

    active_config = kb_config(config, selected_kb)
    if "active_kb" not in st.session_state:
        st.session_state.active_kb = selected_kb
    elif st.session_state.active_kb != selected_kb:
        st.session_state.active_kb = selected_kb
        st.session_state.messages = []
        st.toast(f"已切换到知识库 `{selected_kb}`，对话历史已清空", icon="🔄")

    st.markdown(f"**Embedding 模型：** `{active_config.get('embedding_model_name', 'N/A')}`")
    st.markdown(f"**LLM 模型：** `{active_config.get('llm', {}).get('model', 'N/A')}`")
    st.markdown(f"**Chunk Size：** {active_config.get('chunk_size', 'N/A')}")
    st.markdown(f"**Retrieval K：** {active_config.get('retrieval_k', 'N/A')}")
    st.markdown(f"**Rerank：** {'✅ 开启' if active_config.get('rerank_enabled') else '❌ 关闭'}")
    st.markdown(f"**Query Enhancement：** {'✅ 开启' if active_config.get('query_enhance_enabled') else '❌ 关闭'}")
    st.markdown(f"**Strict Context：** {'✅ 开启' if active_config.get('strict_context') else '❌ 关闭'}")

    st.divider()

    # ── Knowledge‑base Status Panel ──
    st.subheader("🗂️ 知识库状态")
    kb_status = get_kb_status(active_config)
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**文档目录**")
            st.caption(kb_status["docs_dir"])
            st.markdown("**向量库目录**")
            st.caption(kb_status["chroma_persist_dir"])
        with col2:
            st.markdown("**源文件数**")
            st.caption(
                str(kb_status["docs_file_count"])
                if kb_status["docs_dir_exists"]
                else "目录不存在"
            )
            st.markdown("**索引片段数**")
            chunk_count = kb_status["chroma_chunk_count"]
            st.caption(
                str(chunk_count) if chunk_count is not None else "未构建"
            )

    if kb_status["file_index_exists"]:
        st.markdown(f"**已索引文件：** {kb_status['chroma_source_count']} 个")
    else:
        st.markdown("**已索引文件：** 未构建（请运行 `--build`）")

    bm25_status = (
        "✅ 已就绪" if kb_status["bm25_file_exists"]
        else "⚠️ 未构建" if kb_status["bm25_enabled_in_config"]
        else "❌ 未启用"
    )
    st.markdown(f"**BM25 状态：** {bm25_status}")

    st.divider()

    # ── Upload section ──
    st.subheader("📁 上传文档")
    upload_ext_display = " / ".join(ext.upper() for ext in [".txt", ".md", ".pdf", ".docx", ".pptx", ".html", ".htm", ".csv", ".xlsx"])
    st.caption(f"支持 {upload_ext_display}")
    uploaded = st.file_uploader(
        "选择文件上传至知识库",
        type=["txt", "md", "pdf", "docx", "pptx", "html", "htm", "csv", "xlsx"],
        accept_multiple_files=True,
    )
    should_import = False
    if uploaded:
        docs_dir = _resolve_path(active_config, "docs_dir")
        os.makedirs(docs_dir, exist_ok=True)
        conflicts = find_upload_conflicts(docs_dir, uploaded)
        if conflicts:
            st.warning(
                "以下文件已存在，上传会覆盖原文件：\n"
                + "\n".join(f"- `{name}`" for name in conflicts)
            )
            col1, col2 = st.columns(2)
            with col1:
                overwrite_confirmed = st.button(
                    "✅ 确认覆盖并继续",
                    key="confirm_overwrite",
                )
            with col2:
                cancel_overwrite = st.button("❌ 取消", key="cancel_overwrite")

            if cancel_overwrite:
                st.stop()
            should_import = overwrite_confirmed
        else:
            should_import = st.button("📥 导入并重建索引")

    if uploaded and should_import:
        saved_count = save_uploaded_files(docs_dir, uploaded)
        with st.spinner("正在重建索引..."):
            try:
                cmd_build(active_config)
                init_system.clear()
                st.success(f"✅ 已导入 {saved_count} 个文件并重建索引，请刷新页面")
            except (Exception, SystemExit) as e:
                st.error(f"❌ 重建失败：{e}")

    st.divider()

    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

# ──────────────────────────────────────────────
# 初始化系统（缓存，只加载一次）
# ──────────────────────────────────────────────

def _config_hash(config: dict) -> str:
    keys = [
        "embedding_model_name",
        "chroma_persist_dir",
        "llm",
        "enhancer",
        "docs_lang",
        "strict_context",
        "system_rules",
        "query_enhance_enabled",
        "rerank_enabled",
        "rerank_model_name",
        "rerank_top_n",
        "retrieval_k",
        "retrieval_candidate_k",
        "parent_child_enabled",
        "child_chunk_size",
        "child_chunk_overlap",
        "multi_query_enabled",
        "multi_query_n",
        "bm25_enabled",
        "clip_image_enabled",
        "clip_model_name",
        "clip_retrieval_k",
    ]
    subset = {key: config.get(key) for key in keys}
    payload = json.dumps(subset, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


@st.cache_resource(show_spinner="正在加载模型和向量索引，请稍候...")
def init_system(config_hash: str, kb_name: str):
    cfg = kb_config(load_config(), kb_name)
    return _init_ask_chat(cfg)


try:
    store, parent_store, llm, query_enhancer, multi_query_enhancer, system_prompt, reranker, bm25_index = init_system(
        _config_hash(active_config),
        selected_kb,
    )
except Exception as e:
    st.error(f"❌ 系统初始化失败：{e}")
    st.info("请确认：\n1. 已运行 `python rag_runner.py --build` 构建索引\n2. config.json 配置正确")
    st.stop()

# ──────────────────────────────────────────────
# 对话界面
# ──────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

# 展示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入框
question = st.chat_input("请输入你的问题……")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.status("正在处理...", expanded=True) as status:
            st.write("🔍 检索知识库...")
            history_for_context = [
                m for m in st.session_state.messages[:-1]
                if m["role"] in ("user", "assistant")
            ]

            chunks, messages, rewritten_question = _retrieve_context(
                store=store,
                llm=llm,
                question=question,
                system_prompt=system_prompt,
                retrieval_k=active_config.get("retrieval_k", 5),
                query_enhancer=query_enhancer,
                messages_history=history_for_context,
                reranker=reranker,
                rerank_top_n=active_config.get("rerank_top_n", 5),
                max_context_chars=active_config.get("max_context_chars", 6000),
                bm25_index=bm25_index,
                retrieval_candidate_k=active_config.get("retrieval_candidate_k"),
                parent_store=parent_store,
                multi_query_enhancer=multi_query_enhancer,
            )

            if not chunks:
                status.update(label="完成", state="complete")
                answer = "❌ 没有检索到相关内容，请确认已构建向量索引（`python rag_runner.py --build`）。"
                st.markdown(answer)
            else:
                st.write(f"✅ 检索到 {len(chunks)} 个相关片段")
                st.write("🤖 生成回答...")
                status.update(label="完成", state="complete")

                # 流式生成回答
                answer_placeholder = st.empty()
                answer = ""
                for token in llm.generate_stream(messages):
                    answer += token
                    answer_placeholder.markdown(answer + "▌")
                answer_placeholder.markdown(answer)

                # 来源引用
                seen = set()
                citations = []
                for chunk in chunks:
                    citation = _format_source_citation(chunk)
                    if citation not in seen:
                        citations.append(citation)
                        seen.add(citation)

                if citations:
                    st.markdown("**📎 来源引用：**")
                    for c in citations:
                        st.markdown(f"- {c}")

                # 检索上下文展开面板
                with st.expander("🔍 查看检索上下文", expanded=False):
                    if rewritten_question and rewritten_question != question:
                        st.markdown("**增强后的检索问题：**")
                        st.code(rewritten_question)

                    for i, chunk in enumerate(chunks, start=1):
                        citation = _format_source_citation(chunk)
                        score_info = ""
                        if chunk.get("rerank_score") is not None:
                            score_info = f" · rerank_score={chunk['rerank_score']}"
                        elif chunk.get("distance") is not None:
                            score_info = f" · distance={chunk['distance']}"
                        st.markdown(f"**Chunk {i}** — {citation}{score_info}")
                        st.text(chunk["text"][:600] + ("..." if len(chunk["text"]) > 600 else ""))
                        st.divider()

    # answer 在两个分支都有定义，安全 append
    st.session_state.messages.append({"role": "assistant", "content": answer})
