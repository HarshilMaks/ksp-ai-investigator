#!/usr/bin/env python3
"""Write the deterministic synthetic scenario seed used by local demos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data.scenarios import build_scenarios, primary_demo_order, scenario_digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/tmp/ksp-investigateai-demo-seed.json"))
    parser.add_argument("--seed", type=int, default=20260726)
    args = parser.parse_args()
    scenarios = build_scenarios(args.seed)
    payload = {"synthetic_only": True, "seed": args.seed, "primary_demo_order": primary_demo_order(), "digest": scenario_digest(scenarios), "scenarios": [scenario.to_record() for scenario in scenarios]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"seeded {len(scenarios)} synthetic scenarios -> {args.output}")
    print(f"digest={payload['digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
