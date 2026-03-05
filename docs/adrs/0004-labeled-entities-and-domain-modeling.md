# ADR-0004: Labeled Entities & Domain Modeling (Person)

## Status

Accepted

## Context

Initially, we considered removing Person to simplify the framework. However, financial modeling relies heavily on
individual statuses (e.g., "Is the person retired?").

## Decision

Reintroduce Person to the Data Model and introduce a lightweight Label system (Facet: Value). Labels will be applied to
Accounts, Transactions, and Persons.

## Consequences

Enables Flows to condition their logic on standardized or custom semantic tags without bloating the core classes.
