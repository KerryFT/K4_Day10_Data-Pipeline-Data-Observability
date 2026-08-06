from __future__ import annotations

from datetime import datetime, UTC
import logging

# Imports từ core module
from core.config import Settings, load_settings

# Imports từ evaluation module
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set

# Imports từ ingestion module
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records

# Imports từ observability module
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report

# Imports từ retrieval module
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main(settings: Settings | None = None) -> dict:
    """Điều phối toàn bộ giai đoạn Phase 1 - Baseline Pipeline."""
    if settings is None:
        settings = load_settings()

    paths = settings.paths

    # Đảm bảo các thư mục đầu ra tồn tại
    for p in [
        paths.raw_records_json.parent,
        paths.clean_json.parent,
        paths.eval_testset.parent,
        paths.baseline_metrics.parent,
        paths.baseline_report.parent,
        paths.quality_dir,
    ]:
        p.mkdir(parents=True, exist_ok=True)

    # 1. Thu thập dữ liệu thô (Fetch hoặc Load Snapshot)
    if not paths.raw_records_json.exists() or settings.refresh_source:
        logger.info("[Phase 1] Đang gọi Crossref API để lấy dữ liệu mới...")
        paper_records = fetch_source_records(settings)
    else:
        logger.info(f"[Phase 1] Đang đọc dữ liệu raw sẵn có tại: {paths.raw_records_json}")
        paper_records = load_raw_records(paths.raw_records_json)

    # 2. Làm sạch dữ liệu (Data Cleaning)
    logger.info("[Phase 1] Đang làm sạch và chuẩn hóa dữ liệu...")
    run_date = datetime.now(UTC)
    clean_df = build_clean_dataframe(paper_records, run_date=run_date)

    # Lưu dữ liệu sạch dưới dạng JSON và CSV
    clean_df.to_json(paths.clean_json, orient="records", indent=2, force_ascii=False)
    clean_df.to_csv(paths.clean_csv, index=False, encoding="utf-8")
    logger.info(f"[Phase 1] Đã lưu {len(clean_df)} bản ghi sạch tại {paths.clean_json}")

    # 3. Tạo Vector Index (Sử dụng LocalEmbeddingIndex.build)
    logger.info(f"[Phase 1] Đang khởi tạo Embedding Index ({settings.baseline_collection_name})...")
    index = LocalEmbeddingIndex.build(
        df=clean_df,
        settings=settings,
        embeddings_output_path=paths.embeddings_json,
    )

    # 4. Sinh bộ câu hỏi đánh giá (Evaluation Test Set)
    if not paths.eval_testset.exists() or settings.refresh_test_set:
        logger.info("[Phase 1] Đang tạo bộ câu hỏi test set mới...")
        build_test_set(df=clean_df, output_path=paths.eval_testset)
    else:
        logger.info(f"[Phase 1] Đang sử dụng test set đóng băng tại: {paths.eval_testset}")

    # 5. Đánh giá RAG Pipeline (Hit Rate, Token F1, LLM Judge)
    logger.info("[Phase 1] Đang chạy đánh giá RAG Agent trên Test Set...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.baseline_metrics,
        answers_output_path=paths.baseline_answers,
    )

    # 6. Kiểm tra Data Quality & Báo cáo Freshness
    logger.info("[Phase 1] Đang kiểm tra chất lượng dữ liệu (Data Quality & Freshness)...")
    quality_report = run_data_quality_checks(clean_df, settings=settings, report_name="baseline_quality_report.json")
    freshness_report = build_freshness_report(clean_df, settings=settings, report_path=paths.freshness_report)

    # 7. Xuất Báo Cáo Markdown
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "total_records": len(paper_records),
        "raw_file": str(paths.raw_records_json),
        "clean_file": str(paths.clean_json),
    }

    generate_phase1_report(
        report_path=paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality_report,
        freshness=freshness_report,
    )

    logger.info(f"=== HOÀN THÀNH PHASE 1! Báo cáo đã lưu tại: {paths.baseline_report} ===")
    return bundle.summary


if __name__ == "__main__":
    main()