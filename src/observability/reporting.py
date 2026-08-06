from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path: str | Path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Generate Markdown report for baseline phase."""
    out_path = Path(report_path)

    hit_rate = float(metrics.get("retrieval_hit_rate", 0.0))
    token_f1 = float(metrics.get("mean_token_f1", 0.0))
    judge_acc = float(metrics.get("judge_accuracy", 0.0))
    judge_score = float(metrics.get("mean_judge_score", 0.0))

    quality_status = quality.get("overall_status", "UNKNOWN")
    passed_checks = quality.get("passed_checks", 0)
    total_checks = quality.get("total_checks", 0)

    is_fresh = freshness.get("is_fresh", False)
    stale_rows = freshness.get("stale_rows", 0)
    total_rows = freshness.get("total_rows", 0)

    md_content = f"""# Phase 1 Baseline Data Pipeline & Observability Report

## 1. Data Ingestion & Source Summary
- **Source API**: {source_summary.get("source_api", "Crossref API")}
- **Query**: `{source_summary.get("source_query", "")}`
- **Total Records Ingested**: {source_summary.get("total_records", total_rows)}
- **Raw File**: `{source_summary.get("raw_file", "")}`
- **Clean File**: `{source_summary.get("clean_file", "")}`

## 2. RAG Evaluation Metrics (Baseline)
| Metric | Value | Description |
| :--- | :---: | :--- |
| **Retrieval Hit Rate** | `{hit_rate:.4f}` | Proportion of ground truth documents retrieved in top-k context |
| **Mean Token F1** | `{token_f1:.4f}` | Token overlap score between agent answer and ground truth |
| **Judge Accuracy** | `{judge_acc:.4f}` | Accuracy of LLM judge correctness assessment |
| **Mean Judge Score** | `{judge_score:.4f}` | Average judge quality rating (1-5) |

## 3. Data Quality Observability
- **Overall Status**: `{quality_status}`
- **Passed Checks**: `{passed_checks} / {total_checks}`

### Quality Checks Detail:
"""
    checks = quality.get("checks", {})
    for check_name, check_info in checks.items():
        status = check_info.get("status", "UNKNOWN")
        desc = check_info.get("description", check_name)
        md_content += f"- `{check_name}`: **{status}** — {desc}\n"

    md_content += f"""
## 4. Data Freshness Monitoring
- **Freshness Status**: **{"FRESH" if is_fresh else "STALE"}**
- **Latest Publication Date**: `{freshness.get("latest_published", "N/A")}`
- **Oldest Publication Date**: `{freshness.get("oldest_published", "N/A")}`
- **Stale Rows (> {freshness.get("freshness_threshold_days", 180)} days)**: `{stale_rows} / {total_rows}`

## 5. Key Findings
1. Baseline pipeline completed end-to-end with clean data.
2. Vector store built with sentence-transformers embedding model.
3. RAG Agent performance benchmarks established as baseline reference.
"""

    write_text(out_path, md_content)


def generate_corruption_report(
    report_path: str | Path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    baseline_quality: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    baseline_freshness: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Generate Markdown report comparing baseline, corrupted, and repaired states."""
    out_path = Path(report_path)

    def _get_m(m: dict[str, Any], key: str) -> float:
        return float(m.get(key, 0.0))

    def _judge_backends(m: dict[str, Any]) -> str:
        counts = m.get("judge_backend_counts", {})
        return ", ".join(f"{name}: {count}" for name, count in counts.items()) or "not recorded"

    metric_keys = (
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    )
    degraded_metrics = [
        key for key in metric_keys if _get_m(corrupted_metrics, key) < _get_m(baseline_metrics, key)
    ]
    recovered_metrics = [
        key
        for key in metric_keys
        if abs(_get_m(repaired_metrics, key) - _get_m(baseline_metrics, key)) < 1e-9
    ]
    impact_conclusion = (
        f"Corruption reduced {len(degraded_metrics)}/{len(metric_keys)} tracked agent metrics "
        f"({', '.join(degraded_metrics)})."
        if degraded_metrics
        else "The current run does not show a reduction in the tracked agent metrics; no degradation claim is made."
    )
    recovery_conclusion = (
        f"Repair restored {len(recovered_metrics)}/{len(metric_keys)} tracked metrics exactly to baseline "
        f"({', '.join(recovered_metrics)})."
        if recovered_metrics
        else "The repaired metrics did not exactly return to baseline in this run."
    )

    md_content = f"""# Data Pipeline Observability: Corruption & Repair Comparison Report

## 1. Executive Summary
This report analyzes the impact of intentional data corruption on RAG Agent performance and validates the recovery capability of the data repair pipeline across three states: **Baseline**, **Corrupted**, and **Repaired**.

---

## 2. RAG Evaluation Metrics Comparison

| Metric | Baseline | Corrupted | Repaired | Impact (Corrupted vs Baseline) | Recovery (Repaired vs Baseline) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Retrieval Hit Rate** | `{_get_m(baseline_metrics, "retrieval_hit_rate"):.4f}` | `{_get_m(corrupted_metrics, "retrieval_hit_rate"):.4f}` | `{_get_m(repaired_metrics, "retrieval_hit_rate"):.4f}` | `{_get_m(corrupted_metrics, "retrieval_hit_rate") - _get_m(baseline_metrics, "retrieval_hit_rate"):+.4f}` | `{_get_m(repaired_metrics, "retrieval_hit_rate") - _get_m(baseline_metrics, "retrieval_hit_rate"):+.4f}` |
| **Mean Token F1** | `{_get_m(baseline_metrics, "mean_token_f1"):.4f}` | `{_get_m(corrupted_metrics, "mean_token_f1"):.4f}` | `{_get_m(repaired_metrics, "mean_token_f1"):.4f}` | `{_get_m(corrupted_metrics, "mean_token_f1") - _get_m(baseline_metrics, "mean_token_f1"):+.4f}` | `{_get_m(repaired_metrics, "mean_token_f1") - _get_m(baseline_metrics, "mean_token_f1"):+.4f}` |
| **Judge Accuracy** | `{_get_m(baseline_metrics, "judge_accuracy"):.4f}` | `{_get_m(corrupted_metrics, "judge_accuracy"):.4f}` | `{_get_m(repaired_metrics, "judge_accuracy"):.4f}` | `{_get_m(corrupted_metrics, "judge_accuracy") - _get_m(baseline_metrics, "judge_accuracy"):+.4f}` | `{_get_m(repaired_metrics, "judge_accuracy") - _get_m(baseline_metrics, "judge_accuracy"):+.4f}` |
| **Mean Judge Score** | `{_get_m(baseline_metrics, "mean_judge_score"):.4f}` | `{_get_m(corrupted_metrics, "mean_judge_score"):.4f}` | `{_get_m(repaired_metrics, "mean_judge_score"):.4f}` | `{_get_m(corrupted_metrics, "mean_judge_score") - _get_m(baseline_metrics, "mean_judge_score"):+.4f}` | `{_get_m(repaired_metrics, "mean_judge_score") - _get_m(baseline_metrics, "mean_judge_score"):+.4f}` |

---

## 3. Data Quality Checks Comparison

| Dimension | Baseline | Corrupted | Repaired |
| :--- | :---: | :---: | :---: |
| **Overall Quality Status** | `{baseline_quality.get("overall_status", "N/A")}` | `{corrupted_quality.get("overall_status", "N/A")}` | `{repaired_quality.get("overall_status", "N/A")}` |
| **Passed / Total Checks** | `{baseline_quality.get("passed_checks", 0)} / {baseline_quality.get("total_checks", 0)}` | `{corrupted_quality.get("passed_checks", 0)} / {corrupted_quality.get("total_checks", 0)}` | `{repaired_quality.get("passed_checks", 0)} / {repaired_quality.get("total_checks", 0)}` |
| **Failed Checks Count** | `{baseline_quality.get("failed_checks", 0)}` | `{corrupted_quality.get("failed_checks", 0)}` | `{repaired_quality.get("failed_checks", 0)}` |

---

## 4. Data Freshness Monitoring Comparison

| Dimension | Baseline | Corrupted | Repaired |
| :--- | :---: | :---: | :---: |
| **Freshness Status** | **{"FRESH" if baseline_freshness.get("is_fresh") else "STALE"}** | **{"FRESH" if corrupted_freshness.get("is_fresh") else "STALE"}** | **{"FRESH" if repaired_freshness.get("is_fresh") else "STALE"}** |
| **Total Rows** | `{baseline_freshness.get("total_rows", 0)}` | `{corrupted_freshness.get("total_rows", 0)}` | `{repaired_freshness.get("total_rows", 0)}` |
| **Stale Rows** | `{baseline_freshness.get("stale_rows", 0)}` | `{corrupted_freshness.get("stale_rows", 0)}` | `{repaired_freshness.get("stale_rows", 0)}` |
| **Latest Published** | `{baseline_freshness.get("latest_published", "N/A")}` | `{corrupted_freshness.get("latest_published", "N/A")}` | `{repaired_freshness.get("latest_published", "N/A")}` |

---

## 5. Evidence-based Conclusions
1. **Data Corruption Impact**: {impact_conclusion}
2. **Data Observability Detection**: Quality moved from `{baseline_quality.get("overall_status", "N/A")}` ({baseline_quality.get("passed_checks", 0)}/{baseline_quality.get("total_checks", 0)} checks passed) to `{corrupted_quality.get("overall_status", "N/A")}` ({corrupted_quality.get("passed_checks", 0)}/{corrupted_quality.get("total_checks", 0)} passed), while freshness moved from **{"FRESH" if baseline_freshness.get("is_fresh") else "STALE"}** to **{"FRESH" if corrupted_freshness.get("is_fresh") else "STALE"}**.
3. **Data Repair Verification**: {recovery_conclusion} Quality returned to `{repaired_quality.get("overall_status", "N/A")}` and freshness returned to **{"FRESH" if repaired_freshness.get("is_fresh") else "STALE"}** after rebuilding from the raw snapshot.

## 6. Evaluation Notes
- All three states use the same frozen test set path.
- `mean_judge_score` uses a **1-5** scale.
- Judge backend — baseline: `{_judge_backends(baseline_metrics)}`; corrupted: `{_judge_backends(corrupted_metrics)}`; repaired: `{_judge_backends(repaired_metrics)}`.
- Ragas may be skipped unless `RUN_RAGAS=1`; its status is preserved in each metrics artifact.
"""

    write_text(out_path, md_content)

