from __future__ import annotations

import logging
import re
from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord

logger = logging.getLogger(__name__)


def _normalize_text(value: str) -> str:
    """Strip HTML remnants, normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", value)
    return normalize_whitespace(text)


def _parse_date(date_str: str) -> pd.Timestamp | None:
    """Attempt to parse a date string into a pd.Timestamp."""
    if not date_str or not date_str.strip():
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return pd.Timestamp(datetime.strptime(date_str.strip(), fmt))
        except ValueError:
            continue
    return None


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw PaperRecords into a DataFrame ready for embedding.

    Steps:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Compute age_days from run_date.
    4. Create helper columns:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates and filter bad rows.
    6. Sort and return.
    """
    if not records:
        logger.warning("No records provided to build_clean_dataframe.")
        return pd.DataFrame()

    rows: list[dict] = []
    run_ts = pd.Timestamp(run_date).tz_localize(None)

    for rec in records:
        # --- Normalize text fields ---
        title = _normalize_text(rec.title)
        summary = _normalize_text(rec.summary)

        if not title or not summary:
            continue

        # --- Authors ---
        authors = [normalize_whitespace(a) for a in rec.authors if a.strip()]
        authors_joined = compact_join(authors)

        # --- Categories ---
        categories = [normalize_whitespace(c) for c in rec.categories if c.strip()]
        categories_joined = compact_join(categories)

        # --- Dates ---
        published_ts = _parse_date(rec.published)
        updated_ts = _parse_date(rec.updated)
        published_str = published_ts.strftime("%Y-%m-%d") if published_ts else ""
        updated_str = updated_ts.strftime("%Y-%m-%d") if updated_ts else ""

        # Age in days from run_date
        if published_ts:
            age_days = max(0, (run_ts - published_ts).days)
        else:
            age_days = -1  # unknown

        # --- Summary chars ---
        summary_chars = len(summary)

        # --- text_for_embedding ---
        # Combine title, summary, authors, and categories into a single
        # document that will be embedded for semantic search.
        parts = [f"Title: {title}"]
        if authors_joined:
            parts.append(f"Authors: {authors_joined}")
        if categories_joined:
            parts.append(f"Categories: {categories_joined}")
        parts.append(f"Abstract: {summary}")
        text_for_embedding = "\n".join(parts)

        rows.append(
            {
                "paper_id": rec.paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": normalize_whitespace(rec.primary_category),
                "published": published_str,
                "updated": updated_str,
                "age_days": age_days,
                "abs_url": rec.abs_url.strip(),
                "pdf_url": rec.pdf_url.strip(),
                "comment": normalize_whitespace(rec.comment),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "text_for_embedding": text_for_embedding,
            }
        )

    if not rows:
        logger.warning("All records were filtered out during cleaning.")
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # --- Drop duplicates by paper_id ---
    before = len(df)
    df = df.drop_duplicates(subset=["paper_id"], keep="first").copy()
    dropped = before - len(df)
    if dropped:
        logger.info("Dropped %d duplicate rows by paper_id.", dropped)

    # --- Filter rows with very short summaries (likely junk) ---
    min_summary_chars = 30
    mask_short = df["summary_chars"] < min_summary_chars
    if mask_short.any():
        logger.info("Dropping %d rows with summary < %d chars.", mask_short.sum(), min_summary_chars)
        df = df[~mask_short].copy()

    # --- Filter rows with unknown publish date ---
    mask_no_date = df["published"] == ""
    if mask_no_date.any():
        logger.info("Dropping %d rows with missing published date.", mask_no_date.sum())
        df = df[~mask_no_date].copy()

    # --- Sort by published date descending, then by title ---
    df = df.sort_values(by=["published", "title"], ascending=[False, True]).reset_index(drop=True)

    logger.info("Cleaned dataframe: %d rows, %d columns.", len(df), len(df.columns))
    return df
