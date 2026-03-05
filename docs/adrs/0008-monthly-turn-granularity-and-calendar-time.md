# ADR-0008: Monthly Turn Granularity & Calendar Time

## Status

Accepted

## Context

Selecting the correct time step granularity is crucial. Yearly intervals fail to capture sequence-of-return risks and
distort compounding math. Daily intervals are overly computationally expensive for long-term retirement planning.
Furthermore, financial events are often tied to specific times of the year (e.g., US tax season).

## Decision

A Turn strictly correlates to one calendar month. The simulation tracks an actual Date (Year, Month) that advances each
turn. The Engine automatically handles incrementing the Date for the Turn and the Age (Years, Months) for all Persons.

## Consequences

Provides the ideal balance of accuracy vs. performance. Allows Flows to correctly model delayed temporal events (like
paying prior-year taxes in March) and properly calculate annualized compounding rates.
