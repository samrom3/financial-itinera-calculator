# f-Itinera Project: Agent Guidelines

This file captures project-specific conventions and preferences for AI coding assistants working in this repo.

## Project Identity

- **Package name**: `fitinera` — both the PyPI name and the directory under `src/`. Versioning belongs in
  `pyproject.toml`, never in directory or module names.
- **Import path**: `from fitinera import ...` (no version suffix).
- **Version scheme**: `MAJOR.MINOR.PATCH[aN]` — use pre-release (`a1`, `a2`, …) while stubs are unimplemented; drop
  suffix at first fully-functional release.

## Project Structure Conventions

```
src/fitinera/          # production package
tests/fitinera/        # test mirror (separate from src, matching pytest conventions)
docs/adrs/             # Architecture Decision Records
README.md              # primary project spec — always the source of truth
CONTRIBUTING.md        # contributor guide
```

- `docs/adrs/` is the home for all ADRs. Never create an `adrs/` directory at the root.
- `README.md` is the primary specification. User-facing elements, lifecycle, import paths, and installation all belong
  there, prominently.

## Architecture Decision Records (ADRs)

ADRs are "designs in the small" for this project. **At the start of every session**, read `docs/adrs/README.md` to
familiarise yourself with the index of decisions already made. Fetch individual ADR files on-demand when you encounter a
decision point relevant to an existing ADR topic — see the "When to Fetch Individual ADR Files" guidance in
`docs/adrs/README.md` for when this applies.

**During coding**, actively watch for ADR-worthy moments:

- You are choosing between two non-trivial approaches
- A decision affects multiple modules or will be hard to reverse
- You find yourself thinking "this is unusual, I should explain why"
- The user asks a design question that results in a deliberate tradeoff

When you detect one, **proactively propose writing an ADR** alongside the code. Read
`.agents/skills/writing-adrs/SKILL.md` to self-trigger the full ADR-writing process — it contains the format, detection
heuristics, and a pre-commit checklist.

Always update the index table in `docs/adrs/README.md` when adding an ADR.

## Tooling

```bash
uv run pre-commit run               # lint + format + test (run before every commit)
uv run pytest tests/fitinera/ -v    # run tests directly
uv sync                             # sync dependencies after pyproject.toml changes
```

- `pre-commit` is authoritative. Always ensure it's fully green before declaring work done.
- If pre-commit auto-fixes files, re-run until all hooks pass cleanly in a single pass.

## Design Philosophy

- **Prefer renaming over workarounds.** If a build system config requires a hack, the underlying structure is probably
  wrong — fix the structure.
- **Parameterise library components.** Built-in flows should be general-purpose (accepting account IDs, amounts, person
  IDs as constructor arguments), not hard-coded to specific scenarios.
- **Park problems cleanly.** If a design question needs thought (e.g. circular dependencies), defer it explicitly rather
  than resolving it with the first available workaround.
