# Step 15 Self-review and Rubric Assessment

Review date: **2026-08-06**

## Completion status

- **Steps 1-13: completed and re-verified.** The baseline and corruption/repair flows ran end-to-end from the saved Crossref snapshot.
- **Step 14: completed.** `corruption_report.md` now compares baseline, corrupted, and repaired states for all four agent metrics, data quality, and freshness.
- **Step 15: technically reviewed with two submission caveats.** The configured Gemini judge returned HTTP 404 and then quota 429, so the reproducible verification run used the explicitly configured heuristic judge. The group/member report templates still contain identity and ownership placeholders that require human input.

## Step 14 evidence

| Metric or signal | Baseline | Corrupted | Repaired | Corruption impact | Repair result |
| :--- | ---: | ---: | ---: | ---: | :--- |
| Retrieval hit rate | 1.0000 | 0.8000 | 1.0000 | -0.2000 | Restored |
| Mean token F1 | 0.3200 | 0.2621 | 0.3200 | -0.0579 | Restored |
| Judge accuracy | 0.3000 | 0.2000 | 0.3000 | -0.1000 | Restored |
| Mean judge score (1-5) | 1.6000 | 1.4000 | 1.6000 | -0.2000 | Restored |
| Quality checks | 6/6, PASSED | 3/6, FAILED | 6/6, PASSED | 3 checks failed | Restored |
| Freshness | FRESH, 0 stale | STALE, 1 stale | FRESH, 0 stale | Became stale | Restored |

Evidence supports both required conclusions:

1. Seven intentional corruption actions caused missing/noisy content, a duplicate ID, an invalid summary, and a stale date. Quality changed from PASSED to FAILED, freshness changed from FRESH to STALE, and all four tracked agent metrics decreased.
2. Rebuilding from the raw Crossref snapshot restored the clean dataset byte-for-byte at the JSON level, restored quality/freshness, and returned all four metrics exactly to baseline.

Judge results in this verification run are clearly labeled `heuristic_configured` (10/10 samples in every state). Ragas is recorded as skipped because `RUN_RAGAS` was not enabled; neither result is presented as an LLM/Ragas measurement.

## Step 15 checklist

- [x] Code is separated into clear ingestion, retrieval, evaluation, observability, and pipeline modules.
- [x] Raw, clean, embedding, evaluation, results, quality, freshness, and report artifacts exist.
- [x] Baseline and corruption/repair orchestration run successfully with the cached MiniLM model and explicit offline judge mode.
- [x] Metrics are internally consistent with their answer artifacts (validated by tests).
- [x] Baseline, corrupted, and repaired answers use the same frozen questions and ground truth IDs.
- [x] Markdown reports are readable and their values match the JSON artifacts.
- [x] Corruption impact and repair recovery are demonstrated numerically.
- [x] `.env` is ignored and is not tracked by Git.
- [ ] The configured Gemini model/provider must be corrected and rerun before claiming real LLM-judge or live-agent execution.
- [ ] `report/group_report.md` and `report/individual_report.md` require team/member details and ownership text that cannot be inferred safely from code.
- [ ] Before submission, decide whether generated Chroma UUID segment directories should be committed as complete artifacts or ignored and rebuilt from the tracked cleaned data/manifest.

## Validation performed

```powershell
$env:HF_HUB_OFFLINE='1'
$env:EVALUATION_JUDGE='heuristic'
.\.venv\Scripts\python.exe .\script\run_phase1.py
.\.venv\Scripts\python.exe .\script\run_corruption_flow.py
.\.venv\Scripts\python.exe -m unittest discover -s .\tests -v
```

Result: both pipelines completed and **5/5 tests passed**. Tests recompute summary metrics from answer artifacts, verify the frozen test set across all states, verify baseline/repaired dataset equality, and validate the Markdown comparison structure.

## Rubric score

| Rubric category | Score | Evidence and rationale |
| :--- | ---: | :--- |
| 1. Code structure and organization | 10/10 | Clear package boundaries, centralized settings/paths, pipeline entrypoints, and focused validation tests. |
| 2. Raw data ingestion | 15/15 | Crossref request parsing, retry handling, raw response, and normalized raw records are implemented and persisted. |
| 3. Cleaning and data modeling | 15/15 | Normalization, invalid-row filtering, deduplication, dates/age, stable schema, and `text_for_embedding` are complete. |
| 4. Embedding and vector store | 10/10 | MiniLM and persistent Chroma collections build and retrieve successfully; baseline hit rate is 1.0. |
| 5. Agent and multi-provider LLM | 7/10 | Abstraction supports six provider modes and agent/tools are implemented, but live agent execution was not verified because the configured Gemini endpoint/model returned 404/429. |
| 6. Evaluation and scoring | 10/10 | Frozen test set, four summary metrics, per-answer artifacts, backend disclosure, optional Ragas status, and consistency tests are present. |
| 7. Data observability | 10/10 | Six quality checks, freshness reports, JSON artifacts, and readable Markdown reporting cover all three states. |
| 8. Corruption and comparison | 10/10 | Seven logged corruption actions, measurable degradation, raw-snapshot repair, complete three-state comparison, and exact recovery are demonstrated. |
| **Base score** | **87/90** | No rubric deduction applied: the offline end-to-end run succeeds, paths are dynamic, artifacts match reports, and no secret file is tracked. |
| Bonus | 0/10 | Bonus is only eligible after a 90/90 base score. |
| **Final score under the supplied rubric** | **87/100** | Strict self-assessment; main gap is verified live-agent/LLM-provider execution. |

## Highest-priority next action

Set a currently available model for the selected provider, confirm quota, remove `EVALUATION_JUDGE=heuristic`, and rerun both flows. A successful LLM-backed judge/agent verification is the clearest path to closing the remaining rubric gap.
