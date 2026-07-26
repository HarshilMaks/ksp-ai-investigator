from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from data.scenarios import build_scenarios, primary_demo_order, scenario_digest

ROOT = Path(__file__).resolve().parents[3]


class ScenarioIntegrationTests(unittest.TestCase):
    def test_all_ten_scenarios_have_route_engines_cards_citations_and_fallback(self) -> None:
        scenarios = build_scenarios()
        self.assertEqual(10, len(scenarios))
        self.assertEqual(tuple(range(1, 11)), tuple(item.number for item in scenarios))
        for scenario in scenarios:
            with self.subTest(scenario=scenario.number):
                self.assertIn(scenario.route, {"fast", "deep", "signals"})
                self.assertTrue(scenario.engines)
                self.assertTrue(scenario.cards)
                self.assertTrue(scenario.citations[0].startswith("SYNTHETIC-"))
                self.assertTrue(scenario.fallback)
        proactive = [item for item in scenarios if item.proactive]
        self.assertEqual([6], [item.number for item in proactive])
        self.assertFalse(proactive[0].opening_query)

    def test_scenario_replay_is_deterministic_and_demo_order_matches_locked_order(self) -> None:
        self.assertEqual(scenario_digest(build_scenarios()), scenario_digest(build_scenarios()))
        self.assertEqual((3, 1, 6, 5, 4, 10), primary_demo_order())
        self.assertNotEqual(scenario_digest(build_scenarios(1)), scenario_digest(build_scenarios(2)))

    def test_seed_and_smoke_scripts_run_locally_without_external_services(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            seed_file = Path(directory) / "seed.json"
            seeded = subprocess.run([sys.executable, str(ROOT / "scripts/seed_demo.py"), "--output", str(seed_file)], cwd=ROOT, capture_output=True, text=True, check=True)
            smoked = subprocess.run([sys.executable, str(ROOT / "scripts/smoke_demo.py"), "--seed-file", str(seed_file)], cwd=ROOT, capture_output=True, text=True, check=True)
            self.assertIn("seeded 10 synthetic scenarios", seeded.stdout)
            self.assertIn("smoke OK: 10 synthetic scenarios", smoked.stdout)


if __name__ == "__main__":
    unittest.main()
