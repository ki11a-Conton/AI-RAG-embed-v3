# 运维手册

## 基本信息

- **知识库内容**：fpp3 预测教科书（Forecasting: Principles and Practice, 3rd Edition）英文 markdown 原文，以及 documents/ 下的示例文档。
- **文档数量**：144 个文件，约 0.72 MB（documents/ 目录，含 fpp3_textbook 各章节 markdown 文件）。
- **当前索引状态**：`--list-sources` 报告 140 个已索引文件，1327 个文本块（chunks）。
- **索引构建时间**：首次全量构建（含模型下载）未单独计时；模型缓存后全量重建约 61 秒（详见下方 2026-05-25 验证记录）。
- **增量构建时间**：单文件变更约 1.7 秒（详见下方 2026-05-25 验证记录）。
- **部署方式**：本地 Python 直接运行；Docker Compose 配置已可用但此运行周期未验证。
- **最后一次全量重建日期**：2026-05-25（详见下方验证记录）。

---

## 常用命令速查

```bash
# 全量重建（文档大改、换了 embedding 模型时用）
# ⚠️ 不要在执行 --build 的同时运行 API（api.py）或 Streamlit（app.py）
python rag_runner.py --build

# 增量更新（日常添加/修改文档，无需停止服务）
python rag_runner.py --build-incremental

# 自动监听（开着就不用手动跑增量了）
python watch.py

# 查看已索引文件
python rag_runner.py --list-sources

# 查看低命中问题
python rag_runner.py --gaps

# 跑检索命中率评估
python eval_retrieval.py

# 向量 vs 混合检索对比
python eval_retrieval.py --compare

# 端到端回答质量评估（需要有效的 LLM API key）
python eval_retrieval.py --full

# 启动 API 服务
uvicorn api:app --host 0.0.0.0 --port 8000

# 启动 Streamlit Web UI
streamlit run app.py

# 运行单元测试
pytest -q
```

> **关于 `--build` 的注意事项**：`python rag_runner.py --build` 会重建 Chroma 的 `documents` 集合（清空后重新索引），期间不应运行 API（`api.py`）或 Streamlit（`app.py`）服务。请在完整重建前停止相关服务，重建完成后重新启动。日常更新文档推荐使用 `--build-incremental`（增量索引），无需停止服务。

## 评测指标契约

- `python eval_retrieval.py` 分开报告 in-domain 检索命中和 boundary 题拒绝结果。
- in-domain 题目是知识库应该覆盖的问题，当前合格基线是 `21/21 = 100.00%`。
- boundary 题目是知识库外问题，合格表现是低置信度 / 正确拒绝；不要把 boundary 题当作检索失败。
- `python eval_retrieval.py --full` 跳过 boundary 题，因此答案质量分母是 in-domain 题目数；当前为 21。
- `/search` 返回 `confidence: "low"` 时，chunks 不能作为权威依据，只能说明当前知识库没有可靠覆盖该主题。

---

## API 认证与用户隔离契约

- 认证默认关闭：`.env` 中 `RAG_API_KEY` 和 `RAG_API_KEYS` 都为空时，FastAPI 保持本机开发友好模式。
- 单 key 模式：只设置 `RAG_API_KEY` 时，所有携带该 key 的请求属于同一默认身份，兼容旧版会话历史行为。
- 多用户模式：设置 `RAG_API_KEYS` 后优先生效，格式可为 `alice:alice-secret,bob:bob-secret` 或 JSON 对象；每个匹配到的用户名会拥有独立会话命名空间。
- 多用户模式下，同一个 `session_id` 和 `kb_name` 在不同用户之间不会共享 `/ask`、`/ask/stream` 写入的历史，也不能通过 `/session/{session_id}/history` 读取彼此内容。
- `/ask`、`/ask/stream`、`/search`、`/cache/stats`、`/cache/clear`、`/index/status`、`/knowledge-bases`、`/session/*` 和 `/sessions/stats` 都走同一认证依赖；`GET /` 健康检查仍公开。
- `RAG_API_KEYS` 配置错误且无法解析时，受保护端点返回 HTTP 500，避免服务静默降级到无认证。
- 运维记录和 issue 中只能写示例 key，不要复制真实 `X-API-Key`、`.env` 内容、token、cookie 或供应商密钥。

权限变更验收命令：

```bash
python -m pytest tests/test_api_auth.py tests/test_session_api.py -q -p no:cacheprovider
python -m py_compile api.py
```

合格标准：测试必须证明缺失/错误 key 返回 HTTP 403，默认无 key 时保持兼容，多用户 key 可访问受保护端点，并且 alice/bob 使用相同 `session_id` 时会话历史互相隔离。

---

## 参数调优记录

### chunk_size

- **当前值**：800
- **说明**：每个文本块的字符数（滑动窗口），对检索质量影响最大。
- **调整历史**：
  - 初始值 800，尚未调优。技术文档建议 400-600，教科书类建议 800-1200。当前为 fpp3 教科书（长篇），可考虑测试 600、800、1000 三个值。

### chunk_overlap

- **当前值**：120
- **说明**：相邻文本块之间的重叠字符数。与 chunk_size 联动，尚未独立调优。

### retrieval_k

- **当前值**：6
- **说明**：返回的 chunk 数量，越大上下文越完整但可能引入噪音。
- **调整历史**：
  - 初始值 6，调优后确认当前值合理。
  - **实验**（2026-05-25）：测试了 k=4、6、8 三个值。
    - k=4：域内命中率 20/21 = 95.24%，边界题 2/2 正确拒绝；遗漏了一道域内题（Theta method），不可接受。
    - k=6：域内命中率 21/21 = 100.00%，边界题 2/2 正确拒绝，为当前合理设置。
    - k=8：域内命中率 21/21 = 100.00%，边界题 2/2 正确拒绝，与 k=6 相同，无提升。
  - **结论**：k=6 是合理的当前值；k=8 无额外收益，k=4 会丢失一道域内题目。

### embedding_model_name

- **当前值**：`mixedbread-ai/mxbai-embed-large-v1`
- **说明**：sentence-transformers 本地嵌入模型，自动添加查询前缀 `"Represent this sentence for searching relevant passages: "`。

### bm25_enabled

- **当前值**：`false`（未开启）
- **说明**：混合检索（向量 + BM25 关键词）。当前无开启计划。

### rerank_enabled

- **当前值**：`false`（未开启）
- **说明**：重排序模块。当前无开启计划。

### parent_child_enabled

- **当前值**：`false`（未开启）
- **说明**：Parent-Child 分块策略。当前无开启计划。

### multi_query_enabled

- **当前值**：`false`（未开启）
- **说明**：多路召回（LLM 生成多个查询变体）。当前无开启计划。

---

## 已知问题和解决方法

| 问题 | 现象 | 原因 | 解决方法 | 日期 |
|---|---|---|---|---|
| LLM API key 无效（401） | `--full` 评估和问答返回 401 错误 | `.env` 中 `LLM_API_KEY` 未配置或已过期 | 在 `.env` 中填入有效的 LLM API key（DeepSeek / OpenAI） | 2026-05-25 验证，仍阻塞 |
| 边界题命中率误判 | Kubernetes、OAuth/JWT 等非知识库内容被错误检索 | 评估题目的 `expected_keywords` 可能在文档中有巧合匹配 | 检查并收紧边界题的 keywords，确认文档中确实无相关内容 | 2026-05-25 验证，边界 `/search` 返回 low confidence，符合预期 |
| 构建期间服务冲突 | `--build` 时 API 或 Streamlit 仍在运行导致 Chroma 数据异常 | Chroma 集合被清空时其他进程正在读取 | 重建前停止 API/Streamlit，重建后重启 | 2026-05-25 验证，已知限制但未复现 |

---

## 文档维护规范

- 新增文档放入 `documents/` 后，`watch.py` 会自动触发增量构建（默认 5 秒聚合窗口）。
- 删除文档后，也会自动从索引中移除。
- 如果修改了大量文档（>20%），建议跑全量 `--build` 而不是增量。
- 每季度跑一次 `--full` 评估（需有效 LLM API key），确认质量没有下滑。
- 支持的文件格式：TXT / Markdown / PDF / DOCX / HTML / CSV。
- 可在子目录中创建 `.doc_loader_ignore` 文件（语法同 `.gitignore`）排除指定文件。

---

## 知识盲区记录

定期跑 `python rag_runner.py --gaps` 查看低命中查询，按月记录：

| 月份 | 高频低命中问题 | 处理方式 |
|---|---|---|
| 初始基线 | `time constant`（2 条 gap 记录，1 个唯一问题） | 检查索引是否遗漏了已有文档。`documents/` 下可能存在 `test_docs/time_constant.md` 等相关文件但未被索引；运行 `python rag_runner.py --build-incremental` 再执行 `python rag_runner.py --list-sources` 确认该文档是否应可检索。不能断言它一定是知识盲区或一定被文档覆盖。 |
| 2026-05-26 | 共 5 条 gap 记录，4 个唯一问题：`time constant`（2 条）、Kubernetes Deployment HA（1 条）、OAuth2 JWT token refresh（1 条）、fpp3 是否支持 OAuth2（1 条） | 边界题（Kubernetes、OAuth2/JWT）已验证为预期外知识库内容；`time constant` 可通过 `test_docs/time_constant.md` 检索；fpp3 OAuth2 支持问题同样属于知识库外边界。域内检索命中率 21/21 = 100.00%，边界题 2/2 正确拒绝，维持不变。 |

---

## 系统局限性（已验证）

| 问题类型 | 表现 | 建议处理方式 |
|---|---|---|
| 知识库边界问题 | 对文档未覆盖的话题（如 Kubernetes、OAuth/JWT），检索命中率低，属于预期行为 | 边界题已加入验证集，开启 `strict_context: true` 可强制 LLM 只基于检索内容回答 |
| 端到端回答质量评估不可用 | `--full` 评估因 LLM API key 无效（401）无法运行 | 配置有效的 LLM API key 后重试 |
| 知识盲区：`time constant` | `--gaps` 报告 2 条低命中记录。`documents/test_docs/time_constant.md` 可能未被索引，运行 `python rag_runner.py --build-incremental` 再执行 `python rag_runner.py --list-sources` 确认该文档是否应可检索 | 已记录在知识盲区表中，待确认是否为索引遗漏而非知识盲区 |

## 预期局限性（待验证）

| 问题类型 | 预期表现 | 待验证 |
|---|---|---|
| 需要数字计算 | 跨文档数字计算中 LLM 经常给出错误数字 | 未系统性测试 |
| 跨越 5 个以上文档综合 | 答案不完整，只覆盖部分来源 | 未系统性测试 |
| 答案是"没有"或"不支持" | 可能编造答案而非直接说"不支持" | 未系统性测试 |
| 需要理解表格或图表 | 无法理解图表内容，只能读取图表标题和说明文字 | 未系统性测试 |

---

## 下一步操作清单

- [ ] **配置 LLM API key**：在 `.env` 中填入有效的 `LLM_API_KEY` 和 `ENHANCER_API_KEY`，使问答和 `--full` 评估可用。（⚠️ 仍阻塞：当前 key 返回 401）
- [x] **调优 chunk_size**：对 fpp3 教科书测试 600、800、1000 三个值，记录命中率和答案质量变化。（已完成，详见下方 2026-05-25 验证记录）
- [x] **建立评估基线（检索部分）**：
  - [x] 确认 eval 题目覆盖五类题（精确事实、概念解释、操作步骤、跨段落综合、边界题）。
  - [x] 跑 `python eval_retrieval.py` 建立检索命中率基线（21 道域内题 21/21 = 100.00%，2 道边界题 2/2 正确拒绝）。
  - [ ] 跑 `python eval_retrieval.py --full` 建立答案质量基线（⚠️ 需先修复 API key）。
- [x] **验证边界题**：对 Kubernetes、OAuth/JWT 等边界题手动测试，确认系统正确返回低置信度。（已完成，详见下方 2026-05-25 验证记录）
- [x] **补全索引构建时间**：记录首次全量构建耗时、增量构建耗时。（已完成，详见下方 2026-05-25 验证记录）
- [x] **定期运行 `--gaps`**：收集用户低命中查询，补充文档或加入边界题。（2026-05-26 首次月度维护执行，详见下方记录）
- [x] **系统性测试局限性**：对数字计算、跨文档综合、"不支持"回答、表格理解四类问题各写 2-3 题，手动测试并记录结果。（检索层覆盖已完成，2026-05-27 每类至少 2 题，共 8 题；答案层验证仍阻塞于 HTTP 401，需有效 LLM API key）

## Operations Verification Update - 2026-05-25

This section records the completed verification pass for `OPERATIONS_GUIDE.md`.
It overrides the older TBD placeholders above where the values differ.

### Current Indexed Knowledge Base

- Content: fpp3 forecasting textbook Markdown corpus plus local sample docs.
- Supported files under `documents/`: 142.
- Indexed sources: 140.
- Indexed chunks in final configuration: 1327.
- Ignored or intentionally unindexed supported-looking files: `fpp3_textbook\README.md`
  via `.doc_loader_ignore`, and `fpp3_textbook\99_appendix\e_bibliography.md`
  due loader/ignore behavior observed during source comparison.
- Final full rebuild date: 2026-05-25.
- Final full rebuild time: about 61 seconds after the embedding model was
  already cached locally.
- No-change incremental build time: about 1.7 seconds.

### Final Retrieval Parameters

| Parameter | Selected Value | Evidence |
|---|---:|---|
| `chunk_size` | 800 | 600, 800, and 1000 all scored 21/21 in-domain with 2/2 boundary rejection; 800 is the balanced default for textbook content |
| `chunk_overlap` | 120 | Kept unchanged; no evidence this parameter is causing domain failures |
| `retrieval_k` | 6 | k=4 lost the Theta question; k=6 and k=8 both scored 21/21 in-domain |
| `bm25_enabled` | false | BM25 scored 21/21 in-domain, no gain over vector-only |
| `rerank_enabled` | false | Reranker model is not cached locally; no measured gain yet |
| `parent_child_enabled` | false | Parent-Child scored 21/21 in-domain but expanded indexed chunks to 3797 |
| `multi_query_enabled` | false | Requires working LLM/enhancer API, currently blocked by 401 |

### Configuration Experiment Results

| Experiment | Indexed Chunks | Build Time | Retrieval Hit Rate | Decision |
|---|---:|---:|---:|---|
| `chunk600_vector` | 1749 | 62.3s | 21/21 domain, 2/2 boundary rejected | Not selected; more chunks, no gain |
| `chunk800_vector` | 1327 | 65.5s | 21/21 domain, 2/2 boundary rejected | Selected baseline |
| `chunk1000_vector` | 1065 | 51.0s | 21/21 domain, 2/2 boundary rejected | Acceptable, but coarser chunks |
| `chunk800_bm25` | 1327 | 60.1s | 21/21 domain, 2/2 boundary rejected | Not selected; no gain |
| `chunk800_parent_child` | 3797 | 67.1s | 21/21 domain, 2/2 boundary rejected | Not selected; more chunks, no gain |

### Boundary And Knowledge-Gap Verification

`/search` boundary validation:

| Question | Confidence | Result |
|---|---|---|
| Kubernetes Deployment high availability | low | Correctly treated as out of corpus |
| OAuth2 JWT token refresh | low | Correctly treated as out of corpus |

`python rag_runner.py --gaps` currently reports 4 gap records and 3 unique
questions: `time constant`, Kubernetes Deployment, and OAuth2/JWT. `time
constant` is now retrievable from `test_docs\time_constant.md`, so future gap
review should distinguish stale historical gap records from current retrieval
state.

### System Limitation Review

The following limitations are verified at the retrieval/operations layer. Full
answer-layer behavior still requires a valid LLM key.

| Question Type | Observed Behavior | Recommended Handling |
|---|---|---|
| Boundary topics outside fpp3 | `/search` returns low confidence but still includes nearest unrelated chunks | Treat `confidence=low` as non-authoritative and tell users the corpus does not cover the topic |
| Numeric calculation across sources | Retrieval can provide source passages but does not guarantee correct arithmetic | Ask the system for source values, then calculate separately or verify manually |
| Synthesis across more than 5 documents | `retrieval_k=6` limits context breadth; broad summaries may omit sources | Split into smaller questions by chapter/model family |
| Unsupported feature questions | Low confidence is the reliable signal; answer generation cannot be validated until LLM key is fixed | Prefer `/search` first; use `strict_context=true` once LLM answering is enabled |
| Tables and figures | Text extraction can retrieve captions/table text, but image understanding is not enabled in final config | Convert important figure/table content into explicit text notes before indexing |

### Remaining External Blocker

The only Operations Guide requirement not fully completable in this environment
is meaningful `python eval_retrieval.py --full` answer-quality scoring. The
current configured LLM key returns HTTP 401. Configure a valid OpenAI-compatible
LLM key or start a local OpenAI-compatible model server, then run:

```bash
python eval_retrieval.py --full
```

Record the resulting answer-quality rate here and in `EVAL_LOG.md`.

### System-Limitation Sample Queries - 2026-05-25

Validated with `/search` through FastAPI `TestClient`:

| Limitation Type | Sample Question | Confidence | Top Source Pattern | Interpretation |
|---|---|---|---|---|
| Numeric calculation | Average of MASE and RMSSE values | medium | Accuracy/distribution accuracy chunks | Retrieval finds nearby metrics, but arithmetic must be checked manually |
| Broad synthesis | Compare ETS, ARIMA, dynamic regression, neural network, and judgmental limitations | medium | Mixed introductory/practical chunks | `retrieval_k=6` cannot guarantee full coverage across all model families |
| Unsupported feature | OAuth2 token refresh support | low | Appendix/simple-method nearest neighbors | Correctly outside corpus; do not answer as authoritative |
| Table/figure understanding | What Figure 2.1 shows | medium | Regression and graphics chunks | Text/caption retrieval is possible, but visual interpretation is not guaranteed |

### Retrieval-Layer Limitation Testing (Codex Search) - 2026-05-26

These are **retrieval-layer observations only**. Answer-layer testing remains blocked by HTTP 401 (LLM API key). At that time, the `系统性测试局限性` checkbox was **not** marked complete; this is now superseded by the 2026-05-27 retrieval-layer coverage section. Full answer-layer validation is still required.

Tested via `/search` through FastAPI `TestClient`. Top Sources column shows the top-3 retrieved source filenames (from `documents/fpp3_textbook/` unless otherwise noted).

| Limitation Type | Question | Confidence | Top Sources | Retrieval Path | Conclusion |
|---|---|---|---|---|---|
| Numeric calculation | What is the average of the MASE and RMSSE values reported for the example accuracy table? | medium | `5_9_distaccuracy.md`, `5_12_basics_reading.md`, `13_4_combinations.md` | vector+bm25 | Finds metric-related chunks but arithmetic must be manually verified |
| Numeric calculation | Calculate the percentage difference between two forecasting accuracy values in the fpp3 examples | medium | `5_8_accuracy.md`, `5_9_distaccuracy.md`, `2_6_scatterplots.md` | vector+bm25 | Finds accuracy examples but exact calculation is not validated |
| Broad synthesis | Summarize ETS, ARIMA, dynamic regression, neural network, and hierarchical reconciliation limitations together | medium | `8_6_estimation_and_model_selection.md`, `12_4_nnetar.md`, `10_5_dhr.md` | vector+bm25 | Retrieves some model-family chunks but not guaranteed all 5+ families |
| Broad synthesis | Compare the forecasting workflow across decomposition, regression, ARIMA, ETS, and practical issues chapters | medium | `preface.md`, `ch13_practical.md`, `8_8_expsmooth_exercises.md` | vector+bm25 | Broad query can pull mixed/introductory chunks and should be split |
| Unsupported feature | Does this knowledge base explain how to configure Terraform remote state locking? | low | `12_4_nnetar.md`, `12_6_advanced_exercises.md`, `2_10_graphics_exercises.md` | vector+bm25 | Outside corpus, low confidence |
| Unsupported feature | Can fpp3 teach me how to deploy a Kubernetes cluster with autoscaling? | low | `preface.md`, `a_appendix_using_r.md`, `c_appendix_reviews.md` | vector+bm25 | Outside corpus, low confidence |
| Table/figure understanding | What exact numeric values are shown in the example forecast accuracy table? | medium | `5_8_accuracy.md`, `7_6_forecasting_regression.md`, `7_9_regression_matrices.md` | vector+bm25 | Can retrieve table-adjacent text, exact values need manual checking |
| Table/figure understanding | What visual pattern appears in Figure 2.1 and what exact plotted values are shown? | medium | `2_4_seasonal_plots.md`, `2_7_lag_plots.md`, `7_10_regression_exercises.md` | vector+bm25 | Image/figure visual interpretation is not guaranteed |

### Retrieval-Layer Limitation Testing (Codex Search) - 2026-05-27

Additional `/search` validation was run through FastAPI `TestClient` with the
knowledge-gap log redirected to a temporary file. This keeps the project gap log
clean while recording repeatable limitation evidence.

| Limitation Type | Question | Retrieval Summary | Conclusion |
|---|---|---|---|
| Numeric calculation | Difference between RMSE and MAE, plus average if RMSE is 10 and MAE is 6 | medium confidence; top source `5_8_accuracy.md` via vector+bm25 | Retrieves accuracy-measure section; arithmetic needs manual verification |
| Numeric calculation | MASE formula and extra inputs needed to compute it for a new series | medium confidence; top source `3_3_moving_averages.md` via vector+bm25 | Retrieves forecasting-method material; exact formula use should be checked |
| Broad synthesis | Compare limitations of ETS, ARIMA, dynamic regression, NNAR, and hierarchical reconciliation | medium confidence; top source `9_10_arima_ets.md` via vector+bm25 | Cross-model material found but cannot guarantee all 5+ families covered |
| Broad synthesis | Summarize how transformations, STL decomposition, and accuracy evaluation interact | high confidence; top source `3_6_stl.md` via vector+bm25 | Strong workflow-adjacent retrieval; answer completeness depends on LLM layer |
| Unsupported feature | Rotate Kubernetes secrets for a production cluster | low confidence; top source `3_1_transformations.md` via vector+bm25 | Outside corpus; do not use chunks as authoritative |
| Unsupported feature | Implement OAuth2 refresh-token rotation from fpp3 documentation | low confidence; top source `a_appendix_using_r.md` via vector+bm25 | Outside corpus; do not use chunks as authoritative |
| Table/figure understanding | What Figure 2.1 shows in the time series graphics chapter | medium confidence; top source `2_10_graphics_exercises.md` via vector+bm25 | Figure-adjacent material retrieved; visual interpretation not guaranteed |
| Table/figure understanding | What table/figure information can be retrieved, and what cannot be interpreted from images alone | medium confidence; top source `2_11_graphics_reading.md` via vector+bm25 | Text/caption retrieval works; image-only content remains a limitation |

Retrieval-layer coverage for the four documented limitation categories now has
at least two recorded samples per category. Full answer-layer validation is
still blocked by the invalid LLM API key.

---

## Monthly Maintenance Record - 2026-05-26

### Status Summary

"This month the system's retrieval-layer performance is unchanged from the initial baseline. The upload safety improvement (Task 3) is now deployed and tested. The one remaining blocker is the LLM API key for end-to-end answer-quality evaluation."

### Gaps Analysis

```bash
python rag_runner.py --gaps
```
- **5 gap records** from 4 unique questions:
  - `time constant` (2 records) — retrievable from `test_docs/time_constant.md`; may be stale records.
  - Kubernetes Deployment HA (1 record) — expected boundary question; outside fpp3 corpus.
  - OAuth2 JWT token refresh (1 record) — expected boundary question; outside fpp3 corpus.
  - fpp3 OAuth2 support (1 record) — also outside corpus; confirms no new gaps emerged.

### Retrieval Evaluation

```bash
python eval_retrieval.py
```
- **Domain hit rate**: 21/21 = **100.00%** (unchanged from baseline)
- **Boundary rejection**: 2/2 correctly rejected (Kubernetes, OAuth/JWT) — same as baseline.
- No regression detected.

### Maintenance Actions Completed

| Action | Status |
|---|---|
| Run `--gaps` and review results | ✅ Done |
| Run `eval_retrieval.py` and compare with baseline | ✅ Done — 21/21 domain and 2/2 boundary rejection unchanged |
| Update RUNBOOK top-section placeholders | ✅ Done |
| Upload safety (Task 3) code verified | ✅ `python -m compileall -q app.py lib/upload_safety.py` passed |
| Upload safety unit tests | ✅ `python -m pytest tests/test_upload_safety.py tests/test_config.py -q` → 17 passed |

### Remaining Blockers

- LLM API key still returns HTTP 401. `python eval_retrieval.py --full` was re-attempted on 2026-05-26; every generation call returned 401, so answer quality remains not measured. Boundary questions are skipped by `--full`, so the expected denominator is 21 after a valid key is configured. The baseline is still **BLOCKED**, not completed.
- The three-month habit is not yet established (only 1 maintenance record so far).
