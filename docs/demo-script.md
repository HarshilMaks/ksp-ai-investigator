# Synthetic demo script

The demo uses only deterministic synthetic fixtures. It does not require Catalyst, Neo4j, model assets, credentials, or network access.

## Local seed and smoke

```bash
uv run python scripts/seed_demo.py --output /tmp/ksp-demo-seed.json
uv run python scripts/smoke_demo.py --seed-file /tmp/ksp-demo-seed.json
```

The seed contains ten scenarios and a reproducible SHA-256 digest. The primary judge-facing order is **3 → 1 → 6 → 5 → 4 → 10**: UPI money trail, vehicle-theft ring, proactive alert, hypothesis testing, hotspot forecast, and strategic briefing.

## Scenario coverage

1. Organized vehicle theft ring — deep network/pattern/profile investigation.
2. Cybercrime repeat offender — behavioral escalation and forecast signals.
3. UPI fraud money trail — financial flow and layering analysis.
4. Chain-snatching hotspot forecast — bounded forecast and sociological-context cards.
5. Linked robbery hypothesis — evidence for/against and missing-evidence review.
6. Proactive new-FIR match — system-initiated signal with no opening query.
7. Entity-resolution name variants — approval-aware resolution evidence.
8. Drug network discovery — bounded graph and financial network analysis.
9. Investigation handover — deterministic state/package compilation.
10. Strategic briefing — district-scoped aggregate intelligence.

Every fixture includes a route, engine list, card list, synthetic citation, and deterministic fallback. The scenario suite checks structure and synchronization contracts; it does not claim measured accuracy, capacity, latency, or real-world investigative outcomes.
