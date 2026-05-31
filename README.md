# AI-RAG-embed

AI-RAG-embed 是一个本地文档知识库 RAG 项目：用本地 embedding 模型把资料切块、向量化并写入 Chroma，然后通过 CLI、Streamlit 网页端、FastAPI 或 Codex MCP 工具进行检索问答。

> 说明：embedding 模型负责“把资料和问题转换成向量并检索相似内容”，不负责生成自然语言回答。回答问题仍需要一个 OpenAI-compatible chat/LLM 接口；如果只做检索、评测命中率或给 Codex 提供知识库片段，可以不配置 LLM key。

## 当前功能状态

| 功能 | 状态 | 说明 |
|---|---:|---|
| TXT / Markdown / PDF / DOCX / PPTX / HTML / CSV / XLSX | 支持 | XLSX 通过 `openpyxl` 读取，每个 sheet 会作为页面进入切块流程。 |
| 本地 embedding | 支持 | 默认 `mixedbread-ai/mxbai-embed-large-v1`，由 `sentence-transformers` 加载。 |
| Chroma 向量库持久化 | 支持 | 默认写入 `./chroma_db`，可在 `config.json` 中修改。 |
| 混合检索：向量 + BM25 | 支持，默认开启 | 设置 `"bm25_enabled": false` 可关闭；首次启用后需要重新 build 生成 `bm25.pkl`。 |
| Reranker | 支持，默认关闭 | 设置 `"rerank_enabled": true`，默认模型 `BAAI/bge-reranker-base`。 |
| Query enhancement / 离线翻译增强 | 支持 | 默认 `offline_translate`，用于中英文资料检索适配。 |
| Parent-child chunk | 支持，默认关闭 | 设置 `"parent_child_enabled": true`。 |
| Multi-query 多路召回 | 支持，默认关闭 | 设置 `"multi_query_enabled": true`。 |
| 图片 caption / CLIP 图片检索 | 支持，默认关闭 | 图片 caption 需要视觉模型 API；CLIP 图片检索使用本地 CLIP。 |
| CLI 问答与检索 | 支持 | `rag_runner.py`。 |
| Streamlit 网页聊天 | 支持 | `streamlit run app.py`。 |
| FastAPI HTTP / SSE | 支持 | `api.py`，包含 `/ask`、`/ask/stream`、`/search` 等。 |
| API key 认证 | 支持，默认关闭 | 支持单个 `RAG_API_KEY`，也支持 `RAG_API_KEYS` 配置多用户 key；多用户模式会按用户隔离会话历史。 |
| Codex MCP 知识库工具 | 支持 | `mcp_server.py` 暴露 `search_knowledge_base(question)`。 |
| 多知识库切换 | 支持 | CLI 使用 `--kb NAME`，Streamlit 侧边栏可选择，FastAPI 支持 `kb_name`。 |
| 诊断检查 | 支持 | `--doctor` 无需 LLM key / embedding 模型即可检查系统状态。 |

## 快速开始

### 1. 安装依赖

```powershell
pip install -r requirements.txt
```

### 2. 初始化项目

```powershell
python init_project.py
```

初始化脚本会自动创建 `config.json`、`.env`、`documents/`、`logs/` 和 `knowledge_bases/`，不会覆盖已经存在的本地文件。

然后编辑 `.env` 填入 LLM API key。`.env` 用于放密钥，不要提交到 GitHub：

```env
LLM_API_KEY=your-llm-api-key
ENHANCER_API_KEY=your-enhancer-api-key
RAG_API_KEY=
RAG_API_KEYS=
```

`config.json` 里 `llm.api_key`、`enhancer.api_key` 可以留空，程序会优先从 `.env` 读取。

### 3. 放入资料并构建索引

把资料放到 `documents/` 目录。支持：

```text
documents/
├── manual.pdf
├── notes.md
├── report.docx
├── slides.pptx
├── page.html
├── table.csv
├── workbook.xlsx
└── plain.txt
```

如需排除某些文件，可在资料目录或子目录放 `.doc_loader_ignore`，语法类似 `.gitignore`。

```powershell
python rag_runner.py --build
```

只处理新增、修改、删除的文件：

```powershell
python rag_runner.py --build-incremental
```

查看当前索引里有哪些来源文件：

```powershell
python rag_runner.py --list-sources
```

### 4. 诊断检查（无需 LLM key / embedding 模型）

```powershell
python rag_runner.py --doctor
```

`--doctor` 会检查配置文件、文档目录、Chroma 向量库状态、BM25 索引文件和 LLM 密钥配置等，并输出简明报告。报告内容不会加载 embedding 模型或调用 LLM。

### 5. 指定知识库名称

```powershell
python rag_runner.py --kb electronics --build
python rag_runner.py --kb electronics --retrieve "问题"
```

`--kb NAME` 会自动将文档目录指向 `knowledge_bases/<NAME>/documents`，向量目录指向 `knowledge_bases/<NAME>/chroma_db`。NAME 只允许字母、数字、下划线、连字符和点，拒绝路径穿越风险。

### 6. 提问或检索

只检索知识库片段，不调用 LLM：

```powershell
python rag_runner.py --retrieve "这个系统如何启用 BM25？"
```

调用 LLM 生成回答：

```powershell
python rag_runner.py "什么是指数平滑？"
```

进入命令行多轮对话：

```powershell
python rag_runner.py
```

## 常用配置

核心配置位于 `config.json`。

| 字段 | 作用 | 默认值 |
|---|---|---|
| `docs_dir` | 文档目录 | `./documents` |
| `chroma_persist_dir` | Chroma 持久化目录 | `./chroma_db` |
| `docs_lang` | 文档主语言 | `en` |
| `chunk_size` | 普通切块大小 | `800` |
| `chunk_overlap` | 普通切块重叠 | `120` |
| `embedding_model_name` | 本地 embedding 模型 | `mixedbread-ai/mxbai-embed-large-v1` |
| `retrieval_k` | 返回 chunk 数 | `6` |
| `max_context_chars` | 送入 LLM 的最大上下文字符数 | `6000` |
| `query_enhance_enabled` | 是否启用问题增强 | `true` |
| `enhancer_mode` | 问题增强模式 | `offline_translate` |
| `bm25_enabled` | 是否启用 BM25 混合检索 | `true` |
| `rerank_enabled` | 是否启用 reranker | `false` |
| `parent_child_enabled` | 是否启用 parent-child chunk | `false` |
| `multi_query_enabled` | 是否启用 multi-query 多路召回 | `false` |
| `strict_context` | 是否严格只基于资料回答 | `false` |

启用混合检索示例：

```json
{
  "bm25_enabled": true,
  "retrieval_k": 6,
  "bm25_top_k": 6
}
```

修改后需要重新构建：

```powershell
python rag_runner.py --build
```

## Streamlit 网页端

启动：

```powershell
streamlit run app.py
```

默认访问：

```text
http://localhost:8501
```

网页端支持：

- 多轮聊天问答。
- 显示检索过程状态。
- 展示来源 chunk、文件名、页码和相似度。
- 侧边栏查看当前配置。
- 侧边栏切换已构建的本地知识库。
- 上传文档并重建索引。

注意：网页端可以选择聊天模型相关配置，但 embedding 模型不能直接当作回答模型使用。embedding 只负责检索，回答仍由 `llm` 配置里的 chat model 完成。

## FastAPI HTTP 服务

启动：

```powershell
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### API 认证

API 认证默认关闭。单用户或本机使用时，可以在 `.env` 里设置 `RAG_API_KEY`：

```env
RAG_API_KEY=your-secret-key-here
```

小团队共享服务时，推荐改用 `RAG_API_KEYS` 配置每个用户自己的 key：

```env
RAG_API_KEY=
RAG_API_KEYS=alice:alice-secret,bob:bob-secret
```

`RAG_API_KEYS` 也可以写成 JSON 对象：

```env
RAG_API_KEYS={"alice":"alice-secret","bob":"bob-secret"}
```

启用任一认证配置后，`/ask`、`/ask/stream`、`/search`、会话管理、缓存管理和索引状态端点都需要携带请求头：

```text
X-API-Key: your-secret-key-here
```

示例：

```powershell
curl -X POST http://localhost:8000/ask ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: your-secret-key-here" ^
  -d "{\"question\":\"什么是指数平滑？\"}"
```

不带 key 或 key 错误时返回 HTTP 403。健康检查 `GET /` 不需要认证。

兼容性规则：

- `RAG_API_KEYS` 非空时优先生效，并按匹配到的用户名隔离 `session_id` 历史。
- 只配置 `RAG_API_KEY` 时保持旧行为：所有通过该 key 的请求共享同一套会话历史。
- 两个变量都留空时认证关闭，适合纯本机开发。
- 不要把真实 key 写入 README、RUNBOOK、任务文档或提交记录。

普通问答：

```powershell
curl -X POST http://localhost:8000/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"什么是时间常数？\"}"
```

只检索，不生成回答：

```powershell
curl -X POST http://localhost:8000/search ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"什么是时间常数？\"}"
```

列出已构建知识库：

```powershell
curl http://localhost:8000/knowledge-bases
```

指定知识库请求：

```powershell
curl -X POST http://localhost:8000/search ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"什么是时间常数？\",\"kb_name\":\"electronics\"}"
```

SSE 流式回答：

```powershell
curl -N -X POST http://localhost:8000/ask/stream ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"什么是时间常数？\"}"
```

管理与状态端点同样支持多知识库参数：

```powershell
curl "http://localhost:8000/index/status?kb_name=electronics"
curl "http://localhost:8000/cache/stats?kb_name=electronics"
curl -X POST "http://localhost:8000/cache/clear?kb_name=electronics"
curl "http://localhost:8000/session/demo/history?kb_name=electronics"
```

当 `/ask` 或 `/ask/stream` 同时传入 `session_id` 和 `kb_name` 时，会话历史会按知识库隔离。
例如同一个 `session_id=demo` 在 `default` 和 `electronics` 中会保存为两份历史；删除
`/session/demo?kb_name=electronics` 不会删除默认知识库的 `demo` 历史。
启用 `RAG_API_KEYS` 后，会话历史还会按认证用户隔离；不同用户即使使用相同
`session_id` 和 `kb_name`，也不会读到彼此的历史。

`/search` 和 `/ask` 会返回 `confidence`。使用规则：

- `high`：可直接参考检索结果。
- `medium`：可参考，但应说明信息可能不完整。
- `low`：不要把结果当权威答案，应提示知识库没有可靠资料。

## Codex MCP 集成

项目提供 `mcp_server.py`，可以把本地知识库作为 Codex Desktop 的 MCP 工具使用。它复用 `lib.pipeline` 的检索逻辑，因此 BM25、reranker、multi-query、parent-child 等配置会随项目当前配置生效。

示例配置：

```toml
[[mcpServers]]
name = "rag-knowledge-base"
command = "python"
args = ["/absolute/path/to/AI-RAG-embed-v3/mcp_server.py"]
```

使用前请先：

```powershell
python rag_runner.py --build
```

MCP 工具名：

```text
search_knowledge_base(question)
```

它只返回相关片段和来源；最终回答由 Codex 根据片段组织。

## 多知识库切换

通过 `--kb NAME` 参数可以快速切换不同知识库，无需手动修改配置：

```powershell
python rag_runner.py --kb electronics --build
python rag_runner.py --kb electronics --retrieve "如何选择电容？"

python rag_runner.py --kb contracts --build
python rag_runner.py --kb contracts "合同期限是多久？"
```

每个知识库的数据存放在 `knowledge_bases/<NAME>/documents`（文档目录）和 `knowledge_bases/<NAME>/chroma_db`（向量目录）中。

`--kb` 后的 NAME 只允许字母、数字、下划线、连字符和点，拒绝路径穿越风险。

传统方式（不指定 `--kb`）仍然可用，此时使用 `config.json` 中的 `docs_dir` 和 `chroma_persist_dir`：

```json
{
  "docs_dir": "./knowledge_bases/manuals",
  "chroma_persist_dir": "./chroma_db_manuals"
}
```

每一套知识库需要分别运行 `--build`。

Streamlit 会在侧边栏列出已经构建过 `chroma_db/` 的知识库；FastAPI 的 `/ask`、`/ask/stream`、`/search` 请求体可传入可选字段 `kb_name`，不传时继续使用默认知识库。

## 自动索引

先完成一次全量构建，然后启动文件监听：

```powershell
python watch.py
```

调整防抖窗口：

```powershell
python watch.py --debounce 30
```

监听指定知识库的文档目录：

```powershell
python watch.py --kb project_a
python watch.py --kb project_a --debounce 10
```

当指定 `--kb NAME` 时，监听目录指向 `knowledge_bases/<NAME>/documents`，增量构建也会应用对应知识库的配置覆盖。不指定 `--kb` 则沿用 `config.json` 中的默认 `docs_dir`。

## 评测

评测问题在 `evals/questions.jsonl`，每行一个 JSON：

```json
{"question":"What does data.table prioritize?","expected_keywords":["speed","memory"],"expected_answer":"data.table prioritizes speed and memory efficiency."}
```

只测检索命中率，不需要 LLM key：

```powershell
python eval_retrieval.py
```

对比向量检索与混合检索：

```powershell
python eval_retrieval.py --compare
```

端到端回答质量评测，需要有效 LLM key：

```powershell
python eval_retrieval.py --full
```

查看低置信度知识缺口：

```powershell
python rag_runner.py --gaps
```

### 评测指标口径

`python eval_retrieval.py` 会把 in-domain 检索命中和 boundary 题拒答分开报告：

- `Domain retrieval hit rate` 只统计知识库应覆盖的领域内问题。
- `Boundary questions` 是知识库外问题，合格表现是被正确拒绝，而不是被检索命中。
- `python eval_retrieval.py --full` 会跳过 boundary 题，因此答案质量分母应是领域内问题数。
- `/search` 返回 `confidence: "low"` 时，返回 chunks 只能作为相邻文本参考，不能当作权威答案来源。

## Docker

```powershell
docker compose up --build
```

默认服务：

- Streamlit Web UI: `http://localhost:8501`
- FastAPI HTTP API: `http://localhost:8000`

## 项目结构

```text
AI-RAG-embed-v3/
├── app.py                 # Streamlit 网页聊天
├── api.py                 # FastAPI HTTP/SSE 接口
├── rag_runner.py          # CLI 构建、检索、问答入口
├── eval_retrieval.py      # 检索与端到端评测
├── mcp_server.py          # Codex MCP 工具
├── watch.py               # 文件监听与增量构建
├── config_example.json    # 配置模板
├── .env.example           # 环境变量模板
├── documents/             # 用户资料目录
├── evals/
│   └── questions.jsonl    # 评测问题
├── lib/
│   ├── doc_loader.py      # 多格式文档读取与切块
│   ├── embed_engine.py    # embedding / CLIP 封装
│   ├── vector_db.py       # Chroma 向量库封装
│   ├── bm25_index.py      # BM25 稀疏检索
│   ├── hybrid_retriever.py # RRF 融合
│   ├── pipeline.py        # 共享检索/问答管线
│   ├── kb_registry.py     # 多知识库发现与配置覆盖
│   ├── llm_api.py         # OpenAI-compatible LLM 封装
│   ├── query_enhancer.py  # 问题增强与翻译
│   └── reranker.py        # reranker 封装
└── tests/                 # pytest 测试
```

自动生成目录通常不要提交：

```text
chroma_db/
logs/
output/
.pytest_cache/
__pycache__/
```

## 测试

```powershell
python -m pytest -q
```

当前发布验证结果：

```text
383 passed, 1 warning
```

## FAQ

### 为什么有了本地 embedding 还需要 LLM API key？

embedding 模型只负责向量化和检索；自然语言回答由 chat/LLM 模型生成。若只运行 `--retrieve`、`/search`、`eval_retrieval.py`，可以不配置 LLM key。

### 401 AuthenticationError 是什么？

这是 LLM 或增强模型接口的 API key 无效，不是 embedding 模型问题。检查 `.env` 里的 `LLM_API_KEY`，以及 `config.json` 中 `llm.api_base_url`、`llm.model` 是否匹配你的服务商。

### XLSX 为什么没有被检索到？

确认文件扩展名是 `.xlsx`，依赖 `openpyxl` 已安装，并且放在 `docs_dir` 下。然后重新运行：

```powershell
python rag_runner.py --build
```

### BM25 打开后为什么没变化？

`bm25_enabled` 改成 `true` 后必须重新 build。成功后 `chroma_persist_dir` 下会出现 `bm25.pkl`。

### PDF 读不出来怎么办？

普通文本 PDF 会优先用 PyMuPDF，失败后回退到 pypdf。扫描版 PDF 没有文本层，需要先 OCR。

## Roadmap

- [x] XLSX 文档加载
- [x] 混合检索（向量 + BM25 + RRF）
- [x] Codex MCP 检索工具
- [x] FastAPI `/search` 低置信度知识缺口记录
- [x] Streamlit 网页聊天
- [x] 多知识库 UI/API 一键切换
- [x] API 静态 key 认证
- [x] 更完整的权限和用户隔离
- [x] 发布版自动安装/初始化脚本
