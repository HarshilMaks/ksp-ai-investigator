from __future__ import annotations

import unittest
from benchmarks.benchmark import run_benchmark


class LoadContractTests(unittest.TestCase):
    def test_small_local_load_stays_bounded_and_external_free(self) -> None:
        report = run_benchmark(iterations=10)
        self.assertEqual(0, report.resilience["external_service_calls"])
        self.assertTrue(report.resilience["bounded_fixture_replay"])
        self.assertTrue(all(item.throughput_per_second > 0 for item in report.timings))


if __name__ == "__main__":
    unittest.main()
