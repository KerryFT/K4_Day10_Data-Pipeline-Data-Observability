from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Execute data quality checks on a DataFrame and save JSON report.

    Checks:
    1. Row count > 0
    2. `paper_id` not null and unique
    3. `title` not null and non-empty
    4. `summary` length >= 20 chars
    5. Data freshness (`age_days` <= freshness_threshold_days)
    """
    total_rows = len(df)
    checks: dict[str, dict[str, Any]] = {}

    # Check 1: Non-empty DataFrame
    is_non_empty = total_rows > 0
    checks["non_empty_dataframe"] = {
        "status": "PASSED" if is_non_empty else "FAILED",
        "description": "DataFrame contains at least 1 record",
        "total_rows": total_rows,
    }

    if not is_non_empty:
        null_paper_ids = 0
        duplicate_paper_ids = 0
        null_titles = 0
        short_summaries = 0
        stale_records = 0
    else:
        # Check 2: paper_id not null & unique
        null_paper_ids = int(df["paper_id"].isna().sum()) if "paper_id" in df.columns else total_rows
        paper_id_series = df["paper_id"].dropna().astype(str) if "paper_id" in df.columns else pd.Series()
        duplicate_paper_ids = int(paper_id_series.duplicated().sum())

        checks["paper_id_not_null"] = {
            "status": "PASSED" if null_paper_ids == 0 else "FAILED",
            "description": "No null paper_id values",
            "failed_count": null_paper_ids,
        }
        checks["paper_id_unique"] = {
            "status": "PASSED" if duplicate_paper_ids == 0 else "FAILED",
            "description": "All paper_id values are unique",
            "failed_count": duplicate_paper_ids,
        }

        # Check 3: title not null & non-empty
        if "title" in df.columns:
            null_titles = int(df["title"].isna().sum() + (df["title"].astype(str).str.strip() == "").sum())
        else:
            null_titles = total_rows
        checks["title_not_null"] = {
            "status": "PASSED" if null_titles == 0 else "FAILED",
            "description": "All records have a non-empty title",
            "failed_count": null_titles,
        }

        # Check 4: summary length >= 20 chars
        if "summary" in df.columns:
            summary_lens = df["summary"].fillna("").astype(str).str.strip().str.len()
            short_summaries = int((summary_lens < 20).sum())
        else:
            short_summaries = total_rows
        checks["summary_length_valid"] = {
            "status": "PASSED" if short_summaries == 0 else "FAILED",
            "description": "Summary length is at least 20 characters",
            "failed_count": short_summaries,
        }

        # Check 5: Freshness threshold
        if "age_days" in df.columns:
            stale_records = int((df["age_days"] > settings.freshness_threshold_days).sum())
        else:
            stale_records = 0
        checks["freshness_within_threshold"] = {
            "status": "PASSED" if stale_records == 0 else "FAILED",
            "description": f"Publication age <= {settings.freshness_threshold_days} days",
            "failed_count": stale_records,
        }

    total_checks = len(checks)
    passed_checks = sum(1 for c in checks.values() if c["status"] == "PASSED")
    failed_checks = total_checks - passed_checks
    overall_status = "PASSED" if failed_checks == 0 else "FAILED"

    report_payload: dict[str, Any] = {
        "report_name": report_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "total_rows": total_rows,
        "overall_status": overall_status,
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "checks": checks,
    }

    out_file = settings.paths.quality_dir / report_name
    write_json(out_file, report_payload)
    return report_payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: str | Path) -> dict[str, Any]:
    """Consolidate data freshness monitoring report and save JSON."""
    total_rows = len(df)
    out_path = Path(report_path)

    if total_rows == 0:
        report_payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "latest_published": "",
            "oldest_published": "",
            "total_rows": 0,
            "stale_rows": 0,
            "fresh_rows": 0,
            "freshness_threshold_days": settings.freshness_threshold_days,
            "is_fresh": False,
        }
        write_json(out_path, report_payload)
        return report_payload

    published_series = df["published"].dropna().astype(str).str.strip() if "published" in df.columns else pd.Series()
    valid_dates = published_series[published_series != ""]

    latest_published = str(valid_dates.max()) if not valid_dates.empty else ""
    oldest_published = str(valid_dates.min()) if not valid_dates.empty else ""

    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0

    fresh_rows = total_rows - stale_rows
    is_fresh = stale_rows == 0

    report_payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "total_rows": total_rows,
        "stale_rows": stale_rows,
        "fresh_rows": fresh_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": is_fresh,
    }

    write_json(out_path, report_payload)
    return report_payload

