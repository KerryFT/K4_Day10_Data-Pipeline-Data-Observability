import json
import unittest
from pathlib import Path
from statistics import mean


PROJECT_DIR = Path(__file__).resolve().parents[1]


def _read_json(relative_path: str):
    return json.loads((PROJECT_DIR / relative_path).read_text(encoding="utf-8"))


class ArtifactConsistencyTests(unittest.TestCase):
    def test_metrics_match_answer_artifacts(self):
        for state in ("baseline", "corrupted", "repaired"):
            with self.subTest(state=state):
                metrics = _read_json(f"data/results/{state}_metrics.json")
                answers = _read_json(f"data/results/{state}_answers.json")
                self.assertEqual(metrics["samples"], len(answers))
                self.assertAlmostEqual(
                    metrics["retrieval_hit_rate"],
                    mean(float(item["retrieval_hit"]) for item in answers),
                )
                self.assertAlmostEqual(
                    metrics["mean_token_f1"],
                    mean(item["token_f1"] for item in answers),
                )
                self.assertAlmostEqual(
                    metrics["judge_accuracy"],
                    mean(float(item["judge"]["correct"]) for item in answers),
                )
                self.assertAlmostEqual(
                    metrics["mean_judge_score"],
                    mean(item["judge"]["score"] for item in answers),
                )

    def test_all_states_use_the_frozen_test_set(self):
        test_set = _read_json("data/eval/test_set.json")
        expected = [
            (item["id"], item["question"], item["ground_truth"], item["ground_truth_doc_ids"])
            for item in test_set
        ]
        for state in ("baseline", "corrupted", "repaired"):
            answers = _read_json(f"data/results/{state}_answers.json")
            actual = [
                (item["id"], item["question"], item["ground_truth"], item["ground_truth_doc_ids"])
                for item in answers
            ]
            self.assertEqual(expected, actual)

    def test_repair_restores_the_clean_dataset(self):
        baseline = _read_json("data/clean/papers_clean.json")
        repaired = _read_json("data/clean/papers_clean_repaired.json")
        self.assertEqual(baseline, repaired)


if __name__ == "__main__":
    unittest.main()
