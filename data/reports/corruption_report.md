# Data Pipeline Observability: Corruption & Repair Comparison Report

## 1. Executive Summary
This report analyzes the impact of intentional data corruption on RAG Agent performance and validates the recovery capability of the data repair pipeline across three states: **Baseline**, **Corrupted**, and **Repaired**.

---

## 2. RAG Evaluation Metrics Comparison

| Metric | Baseline | Corrupted | Repaired | Impact (Corrupted vs Baseline) | Recovery (Repaired vs Baseline) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Retrieval Hit Rate** | `1.0000` | `0.8000` | `1.0000` | `-0.2000` | `+0.0000` |
| **Mean Token F1** | `0.3200` | `0.2621` | `0.3200` | `-0.0579` | `+0.0000` |
| **Judge Accuracy** | `0.3000` | `0.2000` | `0.3000` | `-0.1000` | `+0.0000` |
| **Mean Judge Score** | `1.6000` | `1.4000` | `1.6000` | `-0.2000` | `+0.0000` |

---

## 3. Data Quality Checks Comparison

| Dimension | Baseline | Corrupted | Repaired |
| :--- | :---: | :---: | :---: |
| **Overall Quality Status** | `PASSED` | `FAILED` | `PASSED` |
| **Passed / Total Checks** | `6 / 6` | `3 / 6` | `6 / 6` |
| **Failed Checks Count** | `0` | `3` | `0` |

---

## 4. Data Freshness Monitoring Comparison

| Dimension | Baseline | Corrupted | Repaired |
| :--- | :---: | :---: | :---: |
| **Freshness Status** | **FRESH** | **STALE** | **FRESH** |
| **Total Rows** | `24` | `23` | `24` |
| **Stale Rows** | `0` | `1` | `0` |
| **Latest Published** | `2026-08-01` | `2026-07-10` | `2026-08-01` |

---

## 5. Evidence-based Conclusions
1. **Data Corruption Impact**: Corruption reduced 4/4 tracked agent metrics (retrieval_hit_rate, mean_token_f1, judge_accuracy, mean_judge_score).
2. **Data Observability Detection**: Quality moved from `PASSED` (6/6 checks passed) to `FAILED` (3/6 passed), while freshness moved from **FRESH** to **STALE**.
3. **Data Repair Verification**: Repair restored 4/4 tracked metrics exactly to baseline (retrieval_hit_rate, mean_token_f1, judge_accuracy, mean_judge_score). Quality returned to `PASSED` and freshness returned to **FRESH** after rebuilding from the raw snapshot.

## 6. Evaluation Notes
- All three states use the same frozen test set path.
- `mean_judge_score` uses a **1-5** scale.
- Judge backend — baseline: `heuristic_fallback: 10`; corrupted: `heuristic_fallback: 10`; repaired: `heuristic_fallback: 10`.
- Ragas may be skipped unless `RUN_RAGAS=1`; its status is preserved in each metrics artifact.
