from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json


def build_test_set(df: pd.DataFrame, output_path: str | Path) -> list[dict[str, Any]]:
    """Create a fixed evaluation test set from the cleaned dataframe.

    Steps:
    1. Verify minimum document count.
    2. Select representative papers from cleaned dataset.
    3. Generate factual evaluation samples covering different categories (authors, factual, date).
    4. Format each sample according to schema:
       - id: str
       - question_type: str ("factual", "authors", "summary", "date")
       - question: str
       - ground_truth: str
       - ground_truth_doc_ids: list[str]
    5. Write result JSON to output_path and return list[dict].
    """
    if df.empty or len(df) < 3:
        raise ValueError(f"DataFrame must contain at least 3 documents to build evaluation set, got {len(df)}.")

    out_path = Path(output_path)
    test_samples: list[dict[str, Any]] = []

    records = df.to_dict(orient="records")

    for idx, row in enumerate(records[:10]):
        q_id = f"q{idx + 1}"
        paper_id = str(row.get("paper_id", ""))
        title = str(row.get("title", "")).strip()
        summary = str(row.get("summary", "")).strip()
        authors_joined = str(row.get("authors_joined", "")).strip()
        published = str(row.get("published", "")).strip()

        q_type_mod = idx % 4
        if q_type_mod == 0:
            question = f"What are the authors of the paper titled '{title}'?"
            ground_truth = f"The authors of '{title}' are {authors_joined}."
            q_type = "authors"
        elif q_type_mod == 1:
            question = f"What is the main framework or objective described in '{title}'?"
            sentences = [s.strip() for s in summary.replace("\n", " ").split(". ") if s.strip()]
            gt_text = ". ".join(sentences[:2]) if len(sentences) >= 2 else summary
            if not gt_text.endswith("."):
                gt_text += "."
            ground_truth = f"The paper '{title}' describes: {gt_text}"
            q_type = "factual"
        elif q_type_mod == 2:
            question = f"When was the paper '{title}' published?"
            ground_truth = f"The paper '{title}' was published on {published}."
            q_type = "date"
        else:
            question = f"Which paper discusses the following research: {summary[:120]}...?"
            ground_truth = f"The paper discussing this research is '{title}' (DOI: {paper_id})."
            q_type = "factual"

        test_samples.append({
            "id": q_id,
            "question_type": q_type,
            "question": question,
            "ground_truth": ground_truth,
            "ground_truth_doc_ids": [paper_id],
        })

    write_json(out_path, test_samples)
    return test_samples

