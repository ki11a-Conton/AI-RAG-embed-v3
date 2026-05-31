# 架构说明

## 概览

这是一个本地 RAG 系统，分为两个阶段：

### 构建阶段（`--build`）

1. 从 `documents/` 目录加载所有 `.txt` 和 `.md` 文件
2. 使用带重叠的滑动窗口，将文件切分为文本块
3. 使用本地嵌入模型将文本块转换为向量嵌入
4. 将向量嵌入和原始文本存入 Chroma 向量数据库

### 查询阶段

1. （可选）增强用户问题：翻译并改写问题；如果有对话历史，也会结合历史上下文，以提升检索效果
2. 将增强后的问题转换为向量嵌入
3. 从向量数据库中检索 top-k 个最相似的文本块
4. 将**原始问题** + 检索到的文本块作为上下文发送给远程 LLM（增强后的问题仅用于检索，以保留回答时用户原本的语言）
5. 生成答案，并保存到 `output/` 目录

## 目录结构

```text
rag_runner.py           # 单一入口文件
config.json             # 运行时配置（被 git 忽略）
config_example.json     # 配置模板（提交到仓库）
documents/              # 原始 .txt / .md 文件
chroma_db/              # 持久化的 Chroma 数据库（生成文件，被 git 忽略）
output/                 # 对话日志（生成文件，被 git 忽略）
lib/
├── __init__.py
├── doc_loader.py       # os.walk + 滑动窗口切分 + 忽略规则
├── embed_engine.py     # SentenceTransformer 封装
├── vector_db.py        # Chroma PersistentClient 操作
├── llm_api.py          # openai.OpenAI 封装
└── query_enhancer.py   # 查询增强（问题翻译 + 改写）
```

## 配置说明

`rag_runner.py` 会在启动时读取 `config.json`。任何 lib 模块都不会直接读取配置文件——它们只接收自己需要的参数。

| 字段 | 分组 | 说明 |
| --- | --- | --- |
| `docs_dir` | 本地数据 | 源文档目录 |
| `docs_lang` | 本地数据 | 问题翻译的目标语言 |
| `chunk_size` | 本地数据 | 每个文本块的字符数（滑动窗口） |
| `chunk_overlap` | 本地数据 | 相邻文本块之间的重叠字符数 |
| `embedding_model_name` | 嵌入 | HuggingFace 模型 ID |
| `chroma_persist_dir` | 嵌入 | Chroma 持久化目录 |
| `retrieval_k` | 嵌入 | 要检索的文本块数量（默认：3） |
| `query_enhance_enabled` | 增强 | 是否启用查询增强 |
| `enhancer` | 增强 | 增强模型配置（api_base_url、api_key、model、temperature、thinking_mode） |
| `llm` | LLM | LLM 模型配置（api_base_url、api_key、model、temperature、thinking_mode） |
| `strict_context` | 行为 | `true` = 只基于上下文回答；`false` = 可补充自身知识 |
| `system_rules` | 行为 | 额外的系统提示词规则（可选） |

相对路径（`./`）会基于项目根目录进行解析。

## 系统提示词

由 `strict_context` 控制两种模式：

**strict_context = false**（默认）：
> You are a helpful assistant. Use the provided context to enrich your answer, but also draw on your own knowledge when the context is insufficient. If the context is provided, prefer it over your own knowledge for factual claims.

中文含义：你是一个有帮助的助手。使用提供的上下文来丰富回答，但当上下文不足时，也可以使用你自己的知识。如果提供了上下文，在事实性陈述上应优先使用上下文。

**strict_context = true**：
> You are a helpful assistant. Answer the user's question based ONLY on the provided context. If the answer is not in the context, say 'I don't know'.

中文含义：你是一个有帮助的助手。只能基于提供的上下文回答用户问题。如果答案不在上下文中，就回答“我不知道”。

如果设置了 `system_rules`，它会被追加到基础提示词之后。

## 入口文件

`rag_runner.py` 会根据 `sys.argv` 进行分发：

```text
python rag_runner.py              →  cmd_chat()    （交互模式）
python rag_runner.py "question"   →  cmd_ask()     （单次问答）
python rag_runner.py --build      →  cmd_build()   （构建索引）
```

重量级依赖（`sentence-transformers`、`chromadb`、`openai`）会通过 `_import_lib()` 延迟加载。`cmd_ask` 和 `cmd_chat` 会通过 `_init_ask_chat()` 调用它；`cmd_build` 会直接调用它。这样可以避免在 IPython（`%run`）环境中产生导入时副作用，因为这些库的信号处理可能与 IPython 发生冲突。

## 构建流程

```text
cmd_build()
  ├─► doc_loader.load_documents(docs_dir, chunk_size, chunk_overlap)
  │     ├─ 预扫描：遍历目录树，收集 .doc_loader_ignore 规则
  │     ├─ os.walk：收集 .txt/.md 文件，跳过被忽略的文件
  │     ├─ 读取 UTF-8 内容
  │     └─ 滑动窗口：[start, start+chunk_size)，步长 = chunk_size - overlap
  │         返回 [{"text": str, "source": "relative/path"}, ...]
  │
  ├─► embed_engine.EmbedEngine(model_name)
  │     └─ SentenceTransformer(model_name)
  │
  └─► vector_db.VectorDb(persist_dir, embed_engine).rebuild(chunks)
        ├─ embed_batch(texts)  →  list[list[float]]
        ├─ 删除所有已有条目
        └─ 添加 ids、embeddings、documents、metadatas
```

`rebuild()` 会执行完整的“删除后重新添加”流程，确保已删除的文档不会留下孤立的旧文本块。

## 查询流程

`cmd_ask` 和 `cmd_chat` 共同使用 `_init_ask_chat()` 完成引擎初始化，并共同使用 `_retrieve_context()` 完成检索。
`cmd_chat` 额外维护一个跨轮次的 `history` 列表，并将其传入查询增强和消息构建流程，以支持上下文感知。

```text
_retrieve_context(store, llm, question, system_prompt, retrieval_k, query_enhancer=None, messages_history=None)
  ├─► print ">> Processing..."

  ├─► [可选] query_enhancer.enhance(question, messages_history)
  │     └─► enhancer llm：将问题翻译 + 改写为 docs_lang
  │           有历史记录时：结合对话上下文解析代词和省略表达
  │           无历史记录时：仅做独立问题翻译

  ├─► print ">> Retrieving..."
  ├─► store.query(rewritten_question, k)
  │     ├─ embed_engine.get_embedding(rewritten_question)  →  vector
  │     └─ collection.query(query_embeddings, n_results=k)
  │           Chroma 余弦相似度搜索
  │           返回 top-k 个文档文本块

  ├─► print ">> Retrieved N chunks. Generating..."

  └─► llm.generate_stream(messages)
        POST {base_url}/chat/completions (stream=True)
        messages: [system prompt, (conversation history ...), {user:
          "Context:\n{chunks}\n\nQuestion: {question}"}]

增强后的问题**只用于检索**。
LLM 始终接收**原始问题**，以保留用户的语言。
```

如果没有找到相关文本块，系统会打印提示并跳过当前轮次。

## 模块细节

### lib/doc_loader.py

```text
load_documents(docs_dir, chunk_size, chunk_overlap) -> list[dict]
```

- 使用 `os.walk` 遍历目录树。
- 预扫描 `.doc_loader_ignore` 文件（使用 `pathspec` 支持 `.gitignore` 语法）。
- 滑动窗口切分：窗口大小 = `chunk_size`，步长 = `chunk_size - chunk_overlap`。
- 每个文本块都会携带其相对于 `docs_dir` 的源文件路径。
- 跳过空文件。

### lib/embed_engine.py

```text
EmbedEngine(model_name)
  .get_embedding(text) -> list[float]
  .embed_batch(texts) -> list[list[float]]
```

- 封装 `SentenceTransformer`。
- 通过 `os.environ.setdefault` 设置 `HF_ENDPOINT=https://hf-mirror.com`（中国镜像；不会覆盖用户已设置的值）。
- `get_embedding(text)` 会在编码前添加 mxbai 查询前缀：`"Represent this sentence for searching relevant passages: "` —— 这是 mxbai 模型家族进行查询嵌入时所必需的。
- `embed_batch(texts)` **不会**添加该前缀 —— 文档嵌入应按原文编码，以保证查询嵌入与文档嵌入之间的语义对齐正确。

### lib/vector_db.py

```text
VectorDb(persist_dir, embed_engine)
  .rebuild(chunks) -> None
  .query(question, k) -> list[str]
```

- 使用带余弦距离的 `chromadb.PersistentClient`（`hnsw:space: "cosine"`）。
- 集合名称：`"documents"`。
- 禁用遥测。

### lib/llm_api.py

```text
LlmApi(api_key, base_url, model, temperature=0.3, thinking_mode=False)
  .generate(messages) -> str
```

- 封装 `openai.OpenAI`。
- `temperature` 和 `thinking_mode` 在初始化时设置。
- 没有重试逻辑 —— 网络错误会直接向上传播给调用方。

### lib/query_enhancer.py

```text
QueryEnhancer(llm_api, docs_lang="en")
  .enhance(question, history=None) -> str
```

两种模式：

- **有对话历史**：结合对话上下文解析代词和省略表达，将问题改写为一个独立查询，然后翻译为 `docs_lang`。用于交互模式（`cmd_chat`），适合处理类似“那是什么意思”这样的追问。
- **无对话历史**（`cmd_ask` 中的单次问题）：将问题翻译并改写为 `docs_lang`，同时把技术术语替换为对应的目标语言表达。

返回值是改写后的单行字符串。它**只用于检索**——原始问题会被发送给回答用的 LLM，以保留用户语言。

## 输出导出

每一轮问答结束后，`_export_round()` 会写入一个 Markdown 文件：

```text
output/<sanitized_question>_<YYYYMMDD_HHMMSS>/
├── 01_round.md
└── 02_round.md
```

每个轮次文件：

========== *Round 1* ==========

**Question:**

```text
{original question}
```

**Enhanced Question:**

```text
{translated and reworded question}
```

**Answer:**

...

========== *Retrieved Context* ==========

```text
{chunk 1 content}
```

```text
{chunk 2 content}
```

### 文本块清理

检索到的文本块在包装前会被清理，以避免破坏 Markdown 渲染：

1. `strip("`")` —— 移除文本块边界处开头或结尾的反引号残留（常见于文本块被截断在代码块中间的情况）。
2. `replace("```", "``")` —— 将剩余的三反引号降为双反引号（防止提前关闭代码围栏）。

清理后，上下文块会被包裹在标准的三反引号代码围栏中，并使用 `text` 作为信息字符串。

## 环境配置

### Python

Python 3.10+。

### GPU 加速（CUDA）

嵌入模型运行在 PyTorch 内部。默认的 `pip install torch` 会安装 CPU-only 版本。若要使用 GPU：

```bash
pip uninstall torch torchvision -y
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

验证方式：`torch.cuda.is_available()` 必须为 `True`。

### sentence-transformers 版本

使用 3.x，不要使用 5.x。5.x 依赖 `torchcodec`（需要 FFmpeg，而文本嵌入不需要它）。如果遇到 `Could not load libtorchcodec`：

```bash
pip uninstall torchcodec sentence-transformers -y
pip install "sentence-transformers>=3.0,<5.0"
```

### HuggingFace 镜像（中国）

`embed_engine.py` 会自动设置 `HF_ENDPOINT=https://hf-mirror.com`。如有需要，也可以手动覆盖：

```bash
set HF_ENDPOINT=https://hf-mirror.com    # Windows
export HF_ENDPOINT=https://hf-mirror.com # Linux/Mac
```

模型在首次下载后会缓存到 `~/.cache/huggingface/`。

## 错误处理

| 条件 | 行为 |
| --- | --- |
| 构建时找不到 `documents/` | 打印提示信息，退出码为 1 |
| 找不到任何 `.txt`/`.md` 文件 | 打印提示信息，退出码为 1 |
| 某个问题没有相关文本块 | 打印提示信息，跳过该轮次（不会崩溃） |
| API 网络错误 | 未处理异常（会显示堆栈信息） |
| 嵌入模型下载失败 | `SentenceTransformer` 抛出异常，进程退出 |
| Chroma 持久化错误 | 由 `chromadb` 抛出，未捕获（通常是磁盘/权限问题） |
