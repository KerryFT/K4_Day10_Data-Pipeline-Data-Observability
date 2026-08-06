# Data Pipeline Observability: Corruption & Repair Comparison Report

## 1. Executive Summary
This report analyzes the impact of intentional data corruption on RAG Agent performance and validates the recovery capability of the data repair pipeline across three states: **Baseline**, **Corrupted**, and **Repaired**.

---

## 2. RAG Evaluation Metrics Comparison

| Metric | Baseline | Corrupted | Repaired | Impact (Corrupted vs Baseline) | Recovery (Repaired vs Baseline) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Retrieval Hit Rate** | `1.0000` | `0.8000` | `1.0000` | `-0.2000` | `+0.0000` |
| **Mean Token F1** | `0.8599` | `0.6786` | `0.8599` | `-0.1813` | `+0.0000` |
| **Judge Accuracy** | `1.0000` | `1.0000` | `1.0000` | `+0.0000` | `+0.0000` |
| **Mean Judge Score** | `4.8000` | `4.5000` | `4.8000` | `-0.3000` | `+0.0000` |

---

## 3. Data Quality Checks Comparison

| Dimension | Corrupted State | Repaired State |
| :--- | :---: | :---: |
| **Overall Quality Status** | `FAILED` | `PASSED` |
| **Passed / Total Checks** | `3 / 6` | `6 / 6` |
| **Failed Checks Count** | `3` | `0` |

---

## 4. Data Freshness Monitoring Comparison

| Dimension | Corrupted State | Repaired State |
| :--- | :---: | :---: |
| **Freshness Status** | **STALE** | **FRESH** |
| **Total Rows** | `23` | `24` |
| **Stale Rows** | `1` | `0` |
| **Latest Published** | `2026-07-10` | `2026-08-01` |

---

## 5. Root Cause Analysis & Conclusion
1. **Data Corruption Impact**: Introducing empty summaries, text noise, deleted records, and stale publication dates degraded retrieval context quality and lowered answer accuracy.
2. **Data Observability Detection**: Quality checks successfully flagged invalid schemas, missing titles/summaries, and stale dates before user consumption.
3. **Data Repair Verification**: Re-ingesting raw artifacts restored full data integrity and returned RAG evaluation metrics to baseline levels.
