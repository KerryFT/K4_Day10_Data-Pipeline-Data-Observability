# Phase 1 Baseline Data Pipeline & Observability Report

## 1. Data Ingestion & Source Summary
- **Source API**: Crossref REST API
- **Query**: `agentic retrieval augmented generation large language model`
- **Total Records Ingested**: 24
- **Raw File**: `C:\Users\ADMIN\OneDrive\Máy tính\labs\K4_Day10_Data-Pipeline-Data-Observability\data\raw\crossref_records.json`
- **Clean File**: `C:\Users\ADMIN\OneDrive\Máy tính\labs\K4_Day10_Data-Pipeline-Data-Observability\data\clean\papers_clean.json`

## 2. RAG Evaluation Metrics (Baseline)
| Metric | Value | Description |
| :--- | :---: | :--- |
| **Retrieval Hit Rate** | `1.0000` | Proportion of ground truth documents retrieved in top-k context |
| **Mean Token F1** | `0.8599` | Token overlap score between agent answer and ground truth |
| **Judge Accuracy** | `1.0000` | Accuracy of LLM judge correctness assessment |
| **Mean Judge Score** | `4.8000` | Average LLM judge quality rating (0-1) |

## 3. Data Quality Observability
- **Overall Status**: `PASSED`
- **Passed Checks**: `6 / 6`

### Quality Checks Detail:
- `non_empty_dataframe`: **PASSED** — DataFrame contains at least 1 record
- `paper_id_not_null`: **PASSED** — No null paper_id values
- `paper_id_unique`: **PASSED** — All paper_id values are unique
- `title_not_null`: **PASSED** — All records have a non-empty title
- `summary_length_valid`: **PASSED** — Summary length is at least 20 characters
- `freshness_within_threshold`: **PASSED** — Publication age <= 180 days

## 4. Data Freshness Monitoring
- **Freshness Status**: **FRESH**
- **Latest Publication Date**: `2026-08-01`
- **Oldest Publication Date**: `2026-02-12`
- **Stale Rows (> 180 days)**: `0 / 24`

## 5. Key Findings
1. Baseline pipeline completed end-to-end with clean data.
2. Vector store built with sentence-transformers embedding model.
3. RAG Agent performance benchmarks established as baseline reference.
