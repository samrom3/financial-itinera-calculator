# Contributing to Fitinera

We welcome contributions to Fitinera. Fitinera V1 is a structural rewrite moving towards a functional data pipeline.

## Developer Workflow

This project explicitly uses `uv` for package management, building, and testing.

1. Install `uv` on your system.
1. Clone the repository and navigate into the project directory.
1. Sync dependencies using `uv sync`.
1. Run tests with `uv run pytest`.

## Code Quality & Pre-commit

We use `pre-commit` for automated code quality checks.

1. Install the pre-commit hooks: `uv run pre-commit install`
1. Run pre-commit hooks manually (optional): `uv run pre-commit run --all-files`

## Quality Guidelines

When contributing, ensure you adhere strictly to the following quality guidelines:

- **Immutability**: Ensure entities that should be immutable (like Turn, Transaction) use
  `dataclasses.dataclass(frozen=True)` or similar constructs.
- **Docstrings**: Include brief Google-style docstrings for all newly scaffolded classes and interfaces explaining their
  role in the V1 pipeline.
- **Separation of Concerns**: Do not mix Data Model state with Computational Model logic.
- **Strong Typing**: Try to reduce reliance on primitives where possible in favor of domain-specific types (e.g.,
  passing specialized objects rather than naked strings or integers).
- **Parameter Encapsulation & Builders**: Use objects to encapsulate function/method parameters instead of defining very
  long run-on parameter lists. It is preferred to provide a corresponding Builder for each Parameter class that sets
  reasonable defaults for optionally specified fields and allows users to specify the parameters as necessary in a
  builder-like style.
- **DAMP Test Style**: Ensure test code is written in a DAMP (Descriptive and Meaningful Phrases) style, optimizing for
  test readability and clear intent over strict DRY (Don't Repeat Yourself) principles.

## Agentic Development with Hyperworker

This project supports multi-agent development using Claude Code CLI and the Hyperworker workflow. See
[docs/hyperworker.md](docs/hyperworker.md) for setup instructions and usage.
