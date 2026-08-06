import unittest
from pathlib import Path

from observability.reporting import generate_corruption_report, generate_phase1_report


def _metrics(hit_rate: float, token_f1: float, accuracy: float, score: float) -> dict:
    return {
        "retrieval_hit_rate": hit_rate,
        "mean_token_f1": token_f1,
        "judge_accuracy": accuracy,
        "mean_judge_score": score,
    }


def _quality(status: str, passed: int) -> dict:
    return {
        "overall_status": status,
        "passed_checks": passed,
        "failed_checks": 6 - passed,
        "total_checks": 6,
    }


def _freshness(is_fresh: bool, stale_rows: int) -> dict:
    return {
        "is_fresh": is_fresh,
        "total_rows": 24,
        "stale_rows": stale_rows,
        "latest_published": "2026-08-01",
    }


class ReportingTests(unittest.TestCase):
    def _output_path(self, name: str) -> Path:
        path = Path(__file__).parent / name
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        return path

    def test_comparison_report_contains_all_three_states(self):
        report_path = self._output_path("_comparison_test_output.md")
        generate_corruption_report(
            report_path=report_path,
            baseline_metrics=_metrics(1.0, 0.32, 0.3, 1.6),
            corrupted_metrics=_metrics(0.8, 0.26, 0.2, 1.4),
            repaired_metrics=_metrics(1.0, 0.32, 0.3, 1.6),
            baseline_quality=_quality("PASSED", 6),
            corrupted_quality=_quality("FAILED", 3),
            repaired_quality=_quality("PASSED", 6),
            baseline_freshness=_freshness(True, 0),
            corrupted_freshness=_freshness(False, 1),
            repaired_freshness=_freshness(True, 0),
        )

        report = report_path.read_text(encoding="utf-8")
        self.assertIn("| Dimension | Baseline | Corrupted | Repaired |", report)
        self.assertIn("Corruption reduced 4/4 tracked agent metrics", report)
        self.assertIn("Repair restored 4/4 tracked metrics exactly to baseline", report)
        self.assertIn("`PASSED` | `FAILED` | `PASSED`", report)
        self.assertIn("**FRESH** | **STALE** | **FRESH**", report)
        self.assertIn("1-5", report)

    def test_phase1_report_documents_judge_scale(self):
        report_path = self._output_path("_phase1_test_output.md")
        generate_phase1_report(
            report_path=report_path,
            source_summary={},
            metrics=_metrics(1.0, 0.32, 0.3, 1.6),
            quality=_quality("PASSED", 6),
            freshness=_freshness(True, 0),
        )

        self.assertIn(
            "Average judge quality rating (1-5)",
            report_path.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
