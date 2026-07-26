#!/usr/bin/env python3
"""Local, provider-independent demo smoke check."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data.scenarios import build_scenarios, primary_demo_order, scenario_digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-file", type=Path)
    args = parser.parse_args()
    scenarios = build_scenarios()
    if args.seed_file:
        payload = json.loads(args.seed_file.read_text(encoding="utf-8"))
        assert payload["synthetic_only"] is True
        assert payload["digest"] == scenario_digest(scenarios)
        assert tuple(payload["primary_demo_order"]) == primary_demo_order()
    assert len(scenarios) == 10
    assert all(scenario.citations and scenario.fallback for scenario in scenarios)
    assert any(scenario.proactive and not scenario.opening_query for scenario in scenarios)
    assert set(primary_demo_order()).issubset({scenario.number for scenario in scenarios})
    print(f"smoke OK: {len(scenarios)} synthetic scenarios; order={primary_demo_order()}; digest={scenario_digest(scenarios)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
