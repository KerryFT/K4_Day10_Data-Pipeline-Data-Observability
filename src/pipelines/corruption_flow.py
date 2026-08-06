from __future__ import annotations

from datetime import datetime, UTC
import logging

import pandas as pd

# Imports từ core module
from core.config import Settings, load_settings
from core.utils import read_json

# Imports từ evaluation module
from evaluation.metrics import evaluate_pipeline

# Imports từ ingestion module
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records

# Imports từ observability module
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report

# Imports từ retrieval module
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main(settings: Settings | None = None) -> None:
    """Xây dựng corruption -> evaluate -> repair -> compare flow.

    Pseudo-code:
    1. Load baseline metrics và clean dataset.
    2. Tạo corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index và evaluate.
    5. Run quality checks/freshness trên corrupted data.
    6. Repair lại từ raw records.
    7. Evaluate repaired dataset.
    8. Tạo comparison report.
    """
    if settings is None:
        settings = load_settings()

    paths = settings.paths

    # Đảm bảo các thư mục tồn tại
    for p in [
        paths.corrupted_clean_json.parent,
        paths.repaired_clean_json.parent,
        paths.corrupted_metrics.parent,
        paths.comparison_report.parent,
        paths.quality_dir,
    ]:
        p.mkdir(parents=True, exist_ok=True)

    # 1. Load baseline metrics và clean dataset.
    if not paths.baseline_metrics.exists():
        raise FileNotFoundError(f"Chưa tìm thấy baseline metrics tại {paths.baseline_metrics}. Vui lòng chạy Phase 1 trước!")
    if not paths.clean_json.exists():
        raise FileNotFoundError(f"Chưa tìm thấy clean dataset tại {paths.clean_json}. Vui lòng chạy Phase 1 trước!")

    logger.info("[Step 1] Loading baseline metrics và clean dataset...")
    baseline_metrics = read_json(paths.baseline_metrics)
    clean_df = pd.read_json(paths.clean_json)

    # 2. Tạo corrupted dataframe.
    logger.info("[Step 2] Creating corrupted dataframe...")
    corrupted_df = corrupt_clean_dataframe(clean_df, output_log_path=paths.corruption_log)

    # 3. Save corrupted artifacts.
    logger.info("[Step 3] Saving corrupted artifacts...")
    corrupted_df.to_json(paths.corrupted_clean_json, orient="records", indent=2, force_ascii=False)
    corrupted_df.to_csv(paths.corrupted_clean_csv, index=False, encoding="utf-8")

    # 4. Rebuild index và evaluate (Corrupted State).
    logger.info(f"[Step 4] Rebuilding index ({settings.corrupted_collection_name}) và evaluating corrupted dataset...")
    corrupted_index = LocalEmbeddingIndex.build(
        df=corrupted_df,
        settings=settings,
        embeddings_output_path=paths.corrupted_embeddings_json,
    )
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.corrupted_metrics,
        answers_output_path=paths.corrupted_answers,
    )

    # 5. Run quality checks/freshness trên corrupted data.
    logger.info("[Step 5] Running quality checks và freshness report trên corrupted data...")
    corrupted_quality = run_data_quality_checks(
        corrupted_df,
        settings=settings,
        report_name="corrupted_quality_report.json",
    )
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings=settings,
        report_path=paths.quality_dir / "corrupted_freshness.json",
    )

    # 6. Repair lại từ raw records.
    logger.info(f"[Step 6] Repairing dataset từ raw records: {paths.raw_records_json}...")
    if not paths.raw_records_json.exists():
        raise FileNotFoundError(f"Chưa tìm thấy file raw records snapshot tại {paths.raw_records_json}")

    raw_records = load_raw_records(paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date=datetime.now(UTC))

    repaired_df.to_json(paths.repaired_clean_json, orient="records", indent=2, force_ascii=False)
    repaired_df.to_csv(paths.repaired_clean_csv, index=False, encoding="utf-8")

    # 7. Evaluate repaired dataset.
    logger.info(f"[Step 7] Rebuilding index ({settings.repaired_collection_name}) và evaluating repaired dataset...")
    repaired_index = LocalEmbeddingIndex.build(
        df=repaired_df,
        settings=settings,
        embeddings_output_path=paths.repaired_embeddings_json,
    )
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.repaired_metrics,
        answers_output_path=paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(
        repaired_df,
        settings=settings,
        report_name="repaired_quality_report.json",
    )
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings=settings,
        report_path=paths.quality_dir / "repaired_freshness.json",
    )

    # 8. Tạo comparison report.
    logger.info(f"[Step 8] Creating comparison report tại {paths.comparison_report}...")
    generate_corruption_report(
        report_path=paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    logger.info("=== HOÀN THÀNH CORRUPTION & REPAIR FLOW! ===")


if __name__ == "__main__":
    main()