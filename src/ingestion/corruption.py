from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

from core.utils import write_json

logger = logging.getLogger(__name__)


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: str | Path) -> pd.DataFrame:
    """Simulate nhiều dạng data corruption trên cleaned dataframe.

    Pseudo-code:
    1. Drop một số latest records.
    2. Blank summary ở một số dòng.
    3. Inject noise vào text.
    4. Làm title bị truncate.
    5. Làm published date cũ đi.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vào output_log_path.
    """
    if df.empty:
        logger.warning("DataFrame rỗng, không thể thực hiện corruption.")
        write_json(output_log_path, {"status": "empty", "corrupted_rows": 0})
        return df

    corrupted_df = df.copy()
    corruption_log: list[dict] = []
    total_original = len(corrupted_df)

    # 1. Drop một số latest records (bài báo mới nhất ở đầu sau khi sort)
    drop_count = min(3, max(1, total_original // 10))
    dropped_records = corrupted_df.iloc[:drop_count][["paper_id", "title"]].to_dict(orient="records")
    corrupted_df = corrupted_df.iloc[drop_count:].reset_index(drop=True)
    
    for rec in dropped_records:
        corruption_log.append({
            "paper_id": rec["paper_id"],
            "title": rec["title"],
            "action": "drop_latest_record",
            "details": "Đã xóa khỏi tập dữ liệu để mô phỏng mất mát thông tin bài báo mới."
        })

    num_rows = len(corrupted_df)

    if num_rows > 0:
        # 2. Blank summary ở một số dòng
        blank_idx = 0
        p_id = corrupted_df.loc[blank_idx, "paper_id"]
        corrupted_df.loc[blank_idx, "summary"] = ""
        corrupted_df.loc[blank_idx, "summary_chars"] = 0
        corruption_log.append({
            "paper_id": p_id,
            "action": "blank_summary",
            "details": "Đã xóa toàn bộ nội dung summary thành chuỗi rỗng."
        })

        # 3. Inject noise vào text
        if num_rows > 1:
            noise_idx = 1
            p_id = corrupted_df.loc[noise_idx, "paper_id"]
            noise_str = " [NOISE_TEXT_CORRUPTED_GARBAGE_ENTITY_XYZ] "
            current_summary = str(corrupted_df.loc[noise_idx, "summary"])
            corrupted_df.loc[noise_idx, "summary"] = noise_str * 5 + current_summary
            corrupted_df.loc[noise_idx, "summary_chars"] = len(corrupted_df.loc[noise_idx, "summary"])
            corruption_log.append({
                "paper_id": p_id,
                "action": "inject_noise",
                "details": "Đã chèn ký tự rác/nhiễu vào summary."
            })

        # 4. Làm title bị truncate (cắt ngắn tiêu đề)
        if num_rows > 2:
            trunc_idx = 2
            p_id = corrupted_df.loc[trunc_idx, "paper_id"]
            current_title = str(corrupted_df.loc[trunc_idx, "title"])
            corrupted_df.loc[trunc_idx, "title"] = current_title[:15] + "..." if len(current_title) > 15 else current_title
            corruption_log.append({
                "paper_id": p_id,
                "action": "truncate_title",
                "details": f"Đã cắt ngắn tiêu đề từ '{current_title}' còn '{corrupted_df.loc[trunc_idx, 'title']}'."
            })

        # 5. Làm published date cũ đi (stale date)
        if num_rows > 3:
            stale_idx = 3
            p_id = corrupted_df.loc[stale_idx, "paper_id"]
            corrupted_df.loc[stale_idx, "published"] = "2000-01-01"
            corrupted_df.loc[stale_idx, "age_days"] = 9999
            corruption_log.append({
                "paper_id": p_id,
                "action": "stale_published_date",
                "details": "Thay đổi ngày xuất bản về '2000-01-01' để vi phạm freshness check."
            })

        # 6. Add duplicate rows (tạo dòng trùng lặp)
        if num_rows > 4:
            dup_idx = 4
            p_id = corrupted_df.loc[dup_idx, "paper_id"]
            duplicate_row = corrupted_df.loc[[dup_idx]].copy()
            corrupted_df = pd.concat([corrupted_df, duplicate_row], ignore_index=True)
            corruption_log.append({
                "paper_id": p_id,
                "action": "add_duplicate_row",
                "details": "Nhân bản bản ghi và giữ nguyên paper_id để vi phạm uniqueness check."
            })

    # 7. Rebuild `text_for_embedding` cho toàn bộ DataFrame sau khi bị can thiệp
    text_list = []
    for _, row in corrupted_df.iterrows():
        title = str(row.get("title", ""))
        authors = str(row.get("authors_joined", row.get("authors", "")))
        categories = str(row.get("categories_joined", row.get("categories", "")))
        summary = str(row.get("summary", ""))

        parts = [f"Title: {title}"]
        if authors:
            parts.append(f"Authors: {authors}")
        if categories:
            parts.append(f"Categories: {categories}")
        parts.append(f"Abstract: {summary}")
        text_list.append("\n".join(parts))

    corrupted_df["text_for_embedding"] = text_list

    # 8. Ghi corruption log vào output_log_path
    log_payload = {
        "timestamp": datetime.now().isoformat(),
        "original_rows": total_original,
        "corrupted_rows": len(corrupted_df),
        "total_actions": len(corruption_log),
        "log": corruption_log,
    }
    write_json(output_log_path, log_payload)
    logger.info(f"Đã thực hiện {len(corruption_log)} hành động corruption và lưu log tại {output_log_path}")

    return corrupted_df


if __name__ == "__main__":
    # Test chạy thử độc lập
    from core.config import load_settings
    settings = load_settings()
    
    if settings.paths.clean_json.exists():
        clean_data = pd.read_json(settings.paths.clean_json)
        res_df = corrupt_clean_dataframe(clean_data, settings.paths.corruption_log)
        print(f"\n[Success] Corrupted DataFrame thành công ({len(res_df)} dòng).")
    else:
        print("Chưa có file clean data. Vui lòng chạy Phase 1 trước.")
