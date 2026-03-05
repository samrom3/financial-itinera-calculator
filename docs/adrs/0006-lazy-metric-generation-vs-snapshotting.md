# ADR-0006: Lazy Metric Generation vs. Snapshotting

## Status

Accepted

## Context

If Flows compute Metrics, order strictly matters, and it conflates state-mutation (Flow) with state-observation
(Metrics). Alternatively, computing metrics only at the end of a turn means mid-turn Flows operate on stale data.

## Decision

Separate mutators (Flow) from observers (MetricGenerator). MetricGenerators are evaluated lazily on-demand when
view.get_metric("MetricName") is called mid-turn, returning the exact value based on current intra-turn balances. At the
very end of the Turn, the Engine evaluates all generators one final time and freezes the results into the immutable Turn
snapshot.

## Consequences

Resolves the causality dilemma. Mid-turn Flows always get perfectly accurate metrics, while historical data remains a
clean snapshot.
