______________________________________________________________________

## name: Writing Architecture Decision Records (ADRs) description: How to identify decisions that warrant an ADR, write one well, and keep the ADR index up to date.

# Writing Architecture Decision Records (ADRs)

ADRs are short, numbered documents that capture a single significant design decision: the context that motivated it, the
decision itself, and its consequences. They are "designs in the small" — not system-wide architecture documents.

## When to Write an ADR

Write an ADR when a decision meets **one or more** of these criteria:

| Signal                           | Example                                                     |
| -------------------------------- | ----------------------------------------------------------- |
| **Cross-cutting**                | Affects multiple modules, layers, or subsystems             |
| **Non-obvious**                  | Future contributors would ask "why was this done this way?" |
| **Costly to reverse**            | Changing it later requires significant refactoring          |
| **Alternatives were considered** | The rejected options are worth remembering                  |

**Skip the ADR** for: routine implementation choices, style preferences, or decisions entirely local to one function or
file.

### Detection heuristics

During planning or code review, ask yourself:

- "Would a new contributor question this?"
- "Did we discuss multiple approaches before landing here?"
- "Does this decision constrain future decisions?"
- "Is this inconsistent with what the code looks like elsewhere, intentionally?"

If yes to any of these, propose an ADR.

## Structure

Follow the standard four-section format:

```markdown
# ADR-NNNN: Short Descriptive Title

## Status
[Draft | Proposed | Accepted | Rejected | Superseded]

## Context
What is the problem or situation that forced a decision?
What constraints or forces are at play?
Keep this factual and brief.

## Decision
What was decided, and why?
If alternatives were considered, name them and explain why they were rejected.

## Consequences
What are the effects of this decision?
Include both positives and negatives / tradeoffs.
```

### Tips for writing well

- **Context**: describe the problem, not the solution. Avoid advocating here.
- **Decision**: be direct — "We decided to X" not "It was felt that X might be better."
- **Consequences**: be honest about the downsides. An ADR that acknowledges tradeoffs is more credible and more useful.
- **Keep it short**: a good ADR is typically 200–400 words. If you need more, the decision may need to be split.

## Process

1. **Draft** — copy the template (`0000-adr-template.md`), assign the next sequential number, fill in Context and
   Decision. Set status `Draft`.
1. **Discuss** — put it in the PR alongside the code it describes. Invite feedback.
1. **Resolve** — update status to `Accepted`, `Rejected`, or `Superseded by ADR-XXXX`.
1. **Index** — add a row to the `## Index` table in `docs/adrs/README.md`.

ADRs are **additive only**: never delete or heavily rewrite an accepted ADR. Write a new superseding ADR instead, and
update both.

## File Naming

```
NNNN-short-hyphenated-title.md
```

`NNNN` is zero-padded and monotonically increasing. The title should be descriptive enough to scan in a list without
reading the full document.

## Checklist Before Committing an ADR

- [ ] Status is set (not left blank)
- [ ] Context explains the *problem*, not the solution
- [ ] Decision is stated directly and justified
- [ ] Consequences include at least one negative/tradeoff
- [ ] Index table in `docs/adrs/README.md` updated
- [ ] ADR is committed alongside (or just before) the code it describes
