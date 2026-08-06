from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

from core.config import Settings
from core.utils import ensure_parent, normalize_whitespace, read_json, write_json

logger = logging.getLogger(__name__)

CROSSREF_API_URL = "https://api.crossref.org/works"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_date_string(item: dict, field: str) -> str:
    """Extract an ISO date string from a Crossref date-parts field."""
    date_obj = item.get(field)
    if not date_obj:
        return ""
    parts = date_obj.get("date-parts", [[]])
    if not parts or not parts[0]:
        return ""
    components = parts[0]
    year = components[0] if len(components) > 0 else None
    month = components[1] if len(components) > 1 else 1
    day = components[2] if len(components) > 2 else 1
    if year is None:
        return ""
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _extract_authors(item: dict) -> list[str]:
    """Build a list of 'Given Family' author strings."""
    raw_authors = item.get("author", [])
    authors: list[str] = []
    for a in raw_authors:
        given = a.get("given", "").strip()
        family = a.get("family", "").strip()
        name = f"{given} {family}".strip()
        if name:
            authors.append(name)
    return authors


def _clean_abstract(raw: str) -> str:
    """Strip JATS XML tags and normalize whitespace in an abstract."""
    text = re.sub(r"<[^>]+>", " ", raw)
    return normalize_whitespace(text)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref JSON payload into a list of PaperRecord.

    Steps:
    1. Iterate over ``payload["message"]["items"]``.
    2. Extract DOI, title, abstract, authors, subjects, dates, URLs.
    3. Normalize text and skip records without a valid title or abstract.
    4. Return list of ``PaperRecord``.
    """
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        # --- DOI / paper_id ---
        doi = (item.get("DOI") or "").strip()
        if not doi:
            continue

        # --- Title ---
        title_list = item.get("title", [])
        raw_title = title_list[0] if title_list else ""
        title = normalize_whitespace(raw_title)
        if not title:
            continue

        # --- Abstract / summary ---
        raw_abstract = item.get("abstract", "")
        summary = _clean_abstract(raw_abstract) if raw_abstract else ""
        if not summary:
            continue  # we only want papers with abstracts

        # --- Authors ---
        authors = _extract_authors(item)

        # --- Categories / subjects ---
        categories = [s.strip() for s in item.get("subject", []) if s.strip()]
        primary_category = categories[0] if categories else ""

        # --- Dates ---
        published = _extract_date_string(item, "published") or _extract_date_string(item, "published-print")
        if not published:
            published = _extract_date_string(item, "published-online") or _extract_date_string(item, "created")
        updated = _extract_date_string(item, "deposited") or published

        # --- URLs ---
        abs_url = (item.get("URL") or f"https://doi.org/{doi}")
        pdf_links = [
            link.get("URL", "")
            for link in item.get("link", [])
            if "pdf" in link.get("content-type", "").lower()
        ]
        pdf_url = pdf_links[0] if pdf_links else ""

        # --- Comment ---
        comment = ""

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    logger.info("Parsed %d valid records from Crossref payload (%d items).", len(records), len(items))
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Call Crossref API, save raw response, parse into records and save them.

    Steps:
    1. Build query params from ``settings.source_query``, ``settings.source_filter``,
       ``settings.max_results``.
    2. Call API with retry for 429/503 status codes.
    3. Save raw response to ``settings.paths.raw_api_response``.
    4. Parse payload via ``parse_crossref_payload``.
    5. Save records to ``settings.paths.raw_records_json``.
    """
    # Build params ----------------------------------------------------------------
    params: dict[str, str | int] = {
        "query": settings.source_query,
        "rows": settings.max_results,
        "sort": "relevance",
        "order": "desc",
    }
    # source_filter looks like  "from-pub-date:2026-02-07,has-abstract:true"
    if settings.source_filter:
        for token in settings.source_filter.split(","):
            token = token.strip()
            if ":" in token:
                key, value = token.split(":", 1)
                params[f"filter"] = params.get("filter", "")  # type: ignore[assignment]
        # Crossref uses a single `filter` param with comma-separated key:value pairs
        params["filter"] = settings.source_filter

    headers = {
        "User-Agent": "DataPipelineLab/1.0 (student lab; mailto:student@example.com)",
        "Accept": "application/json",
    }

    # Retry logic -----------------------------------------------------------------
    max_retries = 5
    backoff = 2.0
    response = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Crossref API request attempt %d/%d  url=%s  params=%s",
                attempt, max_retries, CROSSREF_API_URL, params,
            )
            response = requests.get(CROSSREF_API_URL, params=params, headers=headers, timeout=30)

            if response.status_code == 200:
                break

            if response.status_code in (429, 503):
                wait = backoff * attempt
                logger.warning(
                    "Crossref returned %d, retrying in %.1fs …", response.status_code, wait,
                )
                time.sleep(wait)
                continue

            # Other error – raise immediately
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            if attempt == max_retries:
                raise
            wait = backoff * attempt
            logger.warning("Request error (%s), retrying in %.1fs …", exc, wait)
            time.sleep(wait)

    if response is None or response.status_code != 200:
        raise RuntimeError(f"Failed to fetch from Crossref after {max_retries} attempts.")

    payload = response.json()

    # Save raw response -----------------------------------------------------------
    ensure_parent(settings.paths.raw_api_response)
    settings.paths.raw_api_response.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    logger.info("Raw API response saved to %s", settings.paths.raw_api_response)

    # Parse -----------------------------------------------------------------------
    records = parse_crossref_payload(payload)

    # Save raw records ------------------------------------------------------------
    records_data = [asdict(r) for r in records]
    write_json(settings.paths.raw_records_json, records_data)
    logger.info("Raw records (%d) saved to %s", len(records_data), settings.paths.raw_records_json)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load a JSON snapshot of raw records and map each dict back to ``PaperRecord``."""
    data = read_json(path)
    records: list[PaperRecord] = []
    for entry in data:
        records.append(
            PaperRecord(
                paper_id=entry["paper_id"],
                title=entry["title"],
                summary=entry["summary"],
                authors=entry.get("authors", []),
                categories=entry.get("categories", []),
                primary_category=entry.get("primary_category", ""),
                published=entry.get("published", ""),
                updated=entry.get("updated", ""),
                abs_url=entry.get("abs_url", ""),
                pdf_url=entry.get("pdf_url", ""),
                comment=entry.get("comment", ""),
            )
        )
    logger.info("Loaded %d raw records from %s", len(records), path)
    return records
