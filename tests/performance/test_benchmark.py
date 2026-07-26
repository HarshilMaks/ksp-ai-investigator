from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from benchmarks.benchmark import run_benchmark, write_report


class BenchmarkTests(unittest.TestCase):
    def test_report_is_machine_readable_bounded_and_quality_qualified(self) -> None:
        report = run_benchmark(iterations=5)
        self.assertEqual("p19.1", report.schema_version)
        self.assertEqual(10, report.quality["scenario_count"])
        self.assertEqual(1.0, report.quality["citation_coverage"])
        self.assertTrue(report.resilience["optional_model_degrades_without_assets"])
        self.assertEqual(4, len(report.timings))
        self.assertTrue(all(item.p50_ms >= 0 and item.p95_ms >= item.p50_ms and item.p99_ms >= item.p95_ms for item in report.timings))
        self.assertTrue(report.pending)

    def test_same_seed_has_same_fixture_digest(self) -> None:
        self.assertEqual(run_benchmark(iterations=5, seed=11).scenario_digest, run_benchmark(iterations=5, seed=11).scenario_digest)
        self.assertNotEqual(run_benchmark(iterations=5, seed=11).scenario_digest, run_benchmark(iterations=5, seed=12).scenario_digest)

    def test_report_can_be_written_and_reloaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_report(Path(directory) / "benchmark.json", run_benchmark(iterations=5))
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("p19.1", record["schema_version"])
            self.assertIn("pending", record)


if __name__ == "__main__":
    unittest.main()
