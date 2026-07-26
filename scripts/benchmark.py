#!/usr/bin/env python3
"""CLI delegate for the reproducible P19 benchmark."""

from benchmarks.benchmark import run_benchmark, write_report

if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/tmp/ksp-investigateai-benchmark.json"))
    parser.add_argument("--iterations", type=int, default=25)
    args = parser.parse_args()
    report = run_benchmark(iterations=args.iterations)
    write_report(args.output, report)
    print(json.dumps(report.to_record(), indent=2, sort_keys=True))
