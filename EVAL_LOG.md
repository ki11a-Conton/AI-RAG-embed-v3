# EVAL_LOG.md — Operations Guide Part 1 Baseline

## Metadata

| Field | Value |
|-------|-------|
| **Knowledge base** | `documents/fpp3_textbook` — Forecasting: Principles and Practice (3rd ed.) |
| **Evaluation date** | 2026-05-25 (Asia/Shanghai) |
| **Question set** | `evals/questions.jsonl` — 23 questions total |
| **Boundary questions** | 2 (Kubernetes, OAuth/JWT) — intentionally outside the knowledge base |

## Config Snapshot (baseline)

| Parameter | Value |
|-----------|-------|
| `embedding_model_name` | `mixedbread-ai/mxbai-embed-large-v1` |
| `chunk_size` | 800 |
| `chunk_overlap` | 120 |
| `retrieval_k` | 6 |
| `bm25_enabled` | `false` |
| `rerank_enabled` | `false` |
| `parent_child_enabled` | `false` |
| `multi_query_enabled` | `false` |
| `search_distance_threshold` | 0.4 |
| `enhancer_mode` | `offline_translate` (irrelevant for English eval) |
| `llm` | `deepseek-chat` via `api.deepseek.com/v1` |
| `system_rules` | Full system prompt with citation + formatting rules |

## Baseline Command & Retrieval Results

**Command:** `python eval_retrieval.py`

| Metric | Value |
|--------|-------|
| Domain retrieval hit rate | **21/21 = 100.00%** |
| Boundary rejection | **2/2 correctly rejected** |

The 2 boundary questions are expected to be rejected: the knowledge base contains zero documents about Kubernetes or OAuth/JWT, so the correct behavior is low-confidence / out-of-corpus handling. All 21 in-domain questions hit successfully.

## Compare Command & Results

**Command:** `python eval_retrieval.py --compare`

| Mode | Hit Rate |
|------|----------|
| Vector (baseline) | 21/21 domain, 2/2 boundary rejected |
| Hybrid (BM25 fallback) | 21/21 domain, 2/2 boundary rejected |

Both modes produce identical results. Since BM25 is disabled in the config (`bm25_enabled: false`), the hybrid mode behaves equivalently to the vector-only mode. The same 2 boundary questions are correctly rejected in both modes.

## Full Command & Answer-Quality Results

**Command:** `python eval_retrieval.py --full`

| Metric | Value | Notes |
|--------|-------|-------|
| Domain retrieval hit rate | **21/21 = 100.00%** | Same as baseline retrieval |
| Boundary rejection | **2/2 correctly rejected** | Boundary questions are skipped by `--full` answer-quality scoring |
| Answer quality rate | **not measured** | **BLOCKED** — LLM API key returns 401 authentication error; expected denominator is 21 after a valid key is configured |

### Blocked Status

The `--full` pipeline requires a valid LLM API key to generate answers and evaluate answer quality. The current key returns HTTP 401. No answer-quality metrics can be collected until a valid key is configured.

The eval_retrieval.py script was fixed during this run to continue past generation errors (previously it would abort on the first failure), so retrieval hit-rate collection succeeds even when answer generation fails.

**Remediation required:** Set a valid `llm.api_key` (and optionally `enhancer.api_key`) in `config.json`, then re-run `python eval_retrieval.py --full`.

## retrieval_k Experiment

Three `retrieval_k` values were tested without modifying `config.json` or rebuilding the index. Each test ran `python eval_retrieval.py` with the `retrieval_k` parameter overridden at runtime.

| `retrieval_k` | Domain Retrieval / Boundary Rejection | Notes |
|:---:|:---:|---|
| 4 | 20/21 = 95.24% domain, 2/2 boundary rejected | Theta method question missed |
| 6 | 21/21 = 100.00% domain, 2/2 boundary rejected | Selected baseline |
| 8 | 21/21 = 100.00% domain, 2/2 boundary rejected | No gain over k=6 |

**Interpretation:**
- `k=6` is the current baseline and a reasonable setting. All 21 in-domain questions are captured.
- `k=8` adds no measured retrieval gain over `k=6`.
- `k=4` drops one in-domain question (Theta method), reducing the hit rate below the acceptable threshold.
- The 2 boundary questions are never retrieved regardless of `k`, confirming they are outside the knowledge base.

## Historical TODO — Superseded Where Covered Below

- [ ] **Run ≥3 config experiments** with a valid end-to-end setup (e.g., vary `chunk_size`, toggle `bm25_enabled`, `rerank_enabled`, `parent_child_enabled`, `multi_query_enabled`) and record answer quality rates. *(retrieval_k experiment completed — see section above; chunk_size and full-quality experiments remain blocked/not done)*
- [ ] **Re-run `--full`** with a valid LLM API key to obtain meaningful answer-quality baseline.
- [x] **Manually validate boundary questions** — confirmed 2026-05-25: Kubernetes and OAuth/JWT boundary questions returned confidence: low / out-of-corpus behavior, consistent with RUNBOOK.md.
- [ ] **Record final config decision** in OPERATIONS_GUIDE.md with rationale based on experimental data.

## Operations Completion Pass - 2026-05-25

This section records the retrieval and operations items completed after the
initial baseline notes above. It separates completed evidence from the one
remaining external blocker: a valid LLM key for end-to-end answer-quality
judging.

### Question Set Review

`evals/questions.jsonl` contains 23 valid JSONL questions:

| Category | Count | Notes |
|---|---:|---|
| Precise facts | 8 | Definitions and named concepts such as exponential smoothing, stationarity, tsibble, KPSS |
| Concept explanations | 5 | Additive vs multiplicative decomposition, ETS vs ARIMA, reconciliation, Theta, NNAR |
| Operational steps | 4 | Box-Cox, decomposition + smoothing, dynamic regression, time-series cross-validation |
| Cross-section synthesis | 4 | Model choice, bias adjustment, decomposition workflows, hierarchical reconciliation |
| Boundary questions | 2 | Kubernetes Deployment and OAuth2/JWT, intentionally outside the fpp3 corpus |

Keyword audit result: all 21 in-domain questions have at least one expected
keyword present in `documents/`; the 2 boundary questions have zero expected
keywords present, as intended.

### Rebuilt Configuration Experiments

All rows below were run with a full `python rag_runner.py --build`, followed by
`python eval_retrieval.py` and `python eval_retrieval.py --compare`.

| Experiment | Chunk Size | BM25 | Parent-Child | Indexed Chunks | Build Time | Retrieval Hit Rate | Vector Compare | Hybrid Compare |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `chunk600_vector` | 600 | false | false | 1749 | 62.3s | 21/21 domain, 2/2 boundary rejected | 21/21 domain | 21/21 domain |
| `chunk800_vector` | 800 | false | false | 1327 | 65.5s | 21/21 domain, 2/2 boundary rejected | 21/21 domain | 21/21 domain |
| `chunk1000_vector` | 1000 | false | false | 1065 | 51.0s | 21/21 domain, 2/2 boundary rejected | 21/21 domain | 21/21 domain |
| `chunk800_bm25` | 800 | true | false | 1327 | 60.1s | 21/21 domain, 2/2 boundary rejected | 21/21 domain | 21/21 domain |
| `chunk800_parent_child` | 800 | false | true | 3797 | 67.1s | 21/21 domain, 2/2 boundary rejected | 21/21 domain | 21/21 domain |

### Boundary Question Validation

Validated through `/search` using FastAPI `TestClient`:

| Question | `/search` Confidence | Low Confidence | Top Source | Top Distance |
|---|---|---:|---|---:|
| Kubernetes Deployment high availability | low | true | `fpp3_textbook\99_appendix\a_appendix_using_r.md` | 0.5593 |
| OAuth2 JWT token refresh | low | true | `fpp3_textbook\05_forecaster_toolbox\5_2_simple_methods.md` | 0.55 |

This validates the retrieval-layer guardrail. End-to-end `/ask` hallucination
validation remains blocked by the invalid LLM key.

### Final Configuration Decision

Selected configuration:

- `chunk_size`: 800
- `retrieval_k`: 6
- `bm25_enabled`: false
- `rerank_enabled`: false
- `parent_child_enabled`: false
- `multi_query_enabled`: false

Rationale:

- `chunk_size` 600, 800, and 1000 all scored 21/21 in-domain with 2/2 boundary rejection, so 800 remains the balanced
  default for the fpp3 textbook corpus.
- BM25 produced no retrieval gain on this question set; final config keeps it
  disabled and the generated `chroma_db\bm25.pkl` artifact was removed.
- Parent-Child produced no retrieval gain and increased indexed chunks from
  1327 to 3797, so it is not worth enabling for this corpus.
- Rerank was not selected because the reranker model is not cached locally and
  would add model-download/runtime cost without existing evidence of gain.
- Multi-query was not selected because it requires a working LLM/enhancer API,
  which is currently blocked by authentication failure.

### Remaining External Blocker

`python eval_retrieval.py --full` was re-run on 2026-05-25 and every generation
call failed with HTTP 401 authentication. This is not considered a completed
answer-quality baseline, and no score should be recorded from that run. To
complete that specific LLM-as-judge requirement, configure a valid
OpenAI-compatible LLM key or start a local OpenAI-compatible model server and
re-run `python eval_retrieval.py --full`; boundary questions are skipped, so the
expected answer-quality denominator is 21.

---

## Monthly Maintenance Check - 2026-05-26

### Retrieval Layer (no LLM required)

**Command:** `python eval_retrieval.py`

| Metric | Value | Change from Baseline |
|--------|-------|---------------------|
| Domain retrieval hit rate | **21/21 = 100.00%** | Unchanged |
| Boundary rejection | **2/2 correctly rejected** | Same as baseline |

**No regression detected.** The 2 boundary questions are expected out-of-corpus cases and remain correctly rejected, identical to the 2026-05-25 baseline.

**Command:** `python rag_runner.py --gaps`

- 5 gap records, 4 unique questions: `time constant` (2x), Kubernetes Deployment HA, OAuth2 JWT token refresh, fpp3 OAuth2 support.
- All gaps are pre-existing or expected boundary questions; no new knowledge-base gaps emerged.

### Answer-Quality Layer (blocked)

`--full` run was attempted again on 2026-05-26. Every generation call returned HTTP 401, so answer quality remains **not measured**. The LLM-as-judge pipeline is still **BLOCKED** - not completed. Once a valid key is configured, boundary questions are skipped and the expected answer-quality denominator is 21.

### System-Limitation Retrieval Pass - 2026-05-27

Codex ran eight `/search` samples through FastAPI `TestClient`, two each for
numeric calculation, broad synthesis, unsupported features, and table/figure
understanding. The knowledge-gap log was redirected to a temporary file so this
validation did not add artificial gap records.

Summary:

| Category | Samples | Confidence Pattern | Interpretation |
|---|---:|---|---|
| Numeric calculation | 2 | medium, medium | Relevant source text is retrievable, but arithmetic/formula application must be checked separately |
| Broad synthesis | 2 | medium, high | The retriever finds relevant chapters, but broad multi-family answers may omit parts under `retrieval_k=6` |
| Unsupported features | 2 | low, low | Kubernetes/OAuth operational questions remain correctly outside the corpus |
| Table/figure understanding | 2 | medium, medium | Captions and surrounding text are retrievable; image-only interpretation is not guaranteed |

This completes retrieval-layer limitation coverage for the four categories.
Answer-layer validation remains blocked until a valid LLM key is configured.

### Upload Safety Code Verification

- `python -m compileall -q app.py lib/upload_safety.py` — passed
- `python -m pytest tests/test_upload_safety.py tests/test_config.py -q` — 17 passed

### Next Maintenance

- Re-run `--gaps` and `eval_retrieval.py` in approximately 1 month (due ~2026-06-26).
- Re-attempt `python eval_retrieval.py --full` if a valid LLM API key becomes available.
