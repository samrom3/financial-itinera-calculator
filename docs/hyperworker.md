# Fitinera Hyperworker — Python Multi-Agent Workflow

Hyperworker turns Claude Code CLI into a multi-agent development team lead. It generates a PRD, converts it into a
dependency-ordered task DAG, and dispatches autonomous agents that implement tasks in parallel while enforcing quality
gates — all adapted for fitinera's Python/uv toolchain.

______________________________________________________________________

## Included Skills

| Skill         | Command        | Purpose                                                                                   |
| ------------- | -------------- | ----------------------------------------------------------------------------------------- |
| `prd`         | `/prd`         | Interactive PRD generation with multi-phase refinement. Saves to `plans/<branch>-prd.md`. |
| `prd-tasks`   | `/prd-tasks`   | Converts a PRD into a dependency-ordered set of `TaskCreate` calls.                       |
| `hyperworker` | `/hyperworker` | Team Lead: reads the task DAG, dispatches up to 4 parallel agents, monitors completion.   |

______________________________________________________________________

## Agent Behaviour

Each agent dispatched by `/hyperworker` follows this exact sequence per task:

1. **Read context** — Load `plans/<branch>-progress.txt` (this feature's work log) and `CLAUDE.md` in full.
1. **Scan ADRs** — Read `docs/adrs/` for existing decisions that constrain the work.
1. **Search before coding** — Search the codebase before implementing; do not assume code is missing.
1. **TDD cycle** (repeated per sub-behaviour):
   - Write the test **first** — DAMP style, Google-style docstrings explaining why each test matters.
   - Implement only enough production code to make the test pass.
   - Refactor for high code quality, readability, maintainability.
1. **ADR creation** — If an ADR-worthy decision arises (cross-cutting, costly to reverse, choosing between
   alternatives), write the ADR and update `docs/adrs/README.md`.
1. **Backpressure gate** (always the last action before committing):
   ```
   uv run pre-commit run
   uv run pytest tests/fitinera/ -v
   ```
   If either fails, fix and re-run. **Do not implement anything after validation passes.**
1. **Commit** all changes: `[Story-ID] - [Story Title]`.
1. **Mark task complete** and append progress report to `plans/<branch>-progress.txt`. Reusable patterns are written to
   `CLAUDE.md`; this file remains after branch merge.
1. **Stop** — do not pick up another task.

> **Ralph constraint:** The backpressure gate is always the terminal action. No implementation work follows it. Once
> green, the agent commits and stops.

______________________________________________________________________

## Prerequisites

- **Claude Code CLI** installed and authenticated.
- **tmux** installed (default) — or Zellij (alternative; see below) — for sub-agent pane management.
- **Experimental agents/teams feature flag** enabled in your user-level settings (see Installation §3).
- **Python ≥ 3.13** available on your PATH.
- **uv** package manager installed (via the
  [official uv installer](https://docs.astral.sh/uv/getting-started/installation/)).
- **Pre-commit hooks** installed in the repo: `uv run pre-commit install`.

______________________________________________________________________

## Installation

### 1. Skills are already in `.claude/skills/`

No copy step needed — the three skills (`prd`, `prd-tasks`, `hyperworker`) ship with this repository and are
automatically discovered by Claude Code CLI as `/prd`, `/prd-tasks`, and `/hyperworker` slash commands.

### 2. Create `.claude/settings.json`

The project-level settings file is already present. Its structure is:

```json
{
  "env": {
    "CLAUDE_CODE_TASK_LIST_ID": ""
  },
  "permissions": {
    "allow": [
      "Bash(uv run*)",
      "Bash(uv sync*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(git checkout*)",
      "Bash(git branch*)",
      "Bash(git status*)",
      "Bash(git log*)",
      "Bash(git diff*)",
      "Bash(mkdir*)",
      "Bash(ln -sf*)",
      "Bash(find*)",
      "Bash(grep*)",
      "Bash(ls*)",
      "Bash(echo*)",
      "Bash(touch*)"
    ],
    "deny": [
      "Bash(cat *.env*)",
      "Bash(cat *.envrc*)",
      "Bash(git push*)",
      "Bash(pip install*)",
      "Bash(python -m pip*)"
    ]
  }
}
```

The `CLAUDE_CODE_TASK_LIST_ID` value is set automatically by the `/prd` skill when you start a new feature.

### 3. Apply user-level settings

Add (or merge) the following into `~/.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENTS_TEAMS": "1"
  },
  "teammateMode": "tmux",
  "bypassPermissions": true,
  "skipDangerousModePermissionPrompt": true,
  "spinnerTipsEnabled": false
}
```

> On macOS with iTerm2, replace `"teammateMode": "tmux"` with `"teammateMode": "iterm2"`.

### 4. Add `/plans` to `.gitignore`

Already done — the `plans/` directory is listed in `.gitignore`. It holds ephemeral agent state and should never be
committed.

### 5. Install pre-commit hooks

```bash
uv run pre-commit install
```

______________________________________________________________________

## Usage

Start a tmux session, launch Claude Code, and run the three-phase workflow:

```bash
tmux
claude
```

Then inside Claude Code:

```
> /prd <feature description>       # plain text description
> /prd path/to/seedling-prd.md     # or a draft PRD file as a starting point
```

Answer the clarifying questions across the three refinement phases. Once complete:

```
> /prd-tasks
```

Review the generated task list and approve the dependency graph. Then:

```
> /hyperworker
```

Approve the ASCII DAG and branch name. The Team Lead will dispatch agents to implement tasks in parallel.

______________________________________________________________________

## Sub-Agent Terminal Options

| Option         | Pros                                                                                              | Cons                                                                                | Recommendation                        |
| -------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------- |
| **tmux**       | Universal, battle-tested, Claude Code has native support via `teammateMode: "tmux"`               | Steeper learning curve, config-heavy                                                | **Recommended (default)**             |
| **Zellij**     | Modern Rust-based, intuitive defaults, discoverable UI, WASM plugin support, session resurrection | Less ecosystem support; Claude Code does not natively support it as a teammate mode | Alternative for modern terminal users |
| **GNU Screen** | Ubiquitous on servers, lightweight                                                                | Feature-sparse compared to tmux, aging interface                                    | Not recommended                       |
| **Byobu**      | Beginner-friendly frontend to tmux/screen                                                         | Adds abstraction layer over tmux, less precise control                              | Not recommended                       |
| **iTerm2**     | macOS-only, Claude Code supports `teammateMode: "iterm2"`                                         | Platform-locked, unavailable on Linux                                               | For macOS users only                  |

**Using Zellij as an alternative:**

Zellij does not have native Claude Code teammate mode support, but you can run agents in separate Zellij panes manually.
Start Zellij (`zellij`), open panes with `Ctrl+p n`, and launch `claude` in each pane for the tasks you want to
parallelise.

______________________________________________________________________

## The Ralph Algorithm: Why Validation Is Last

Hyperworker enforces the [Ralph algorithm](https://ghuntley.com/ralph/) as its core loop discipline.

**Core principles:**

- **One item per loop iteration.** Each agent works on exactly one task. It does not pick up a second task after
  finishing the first.
- **Backpressure via build/test is the FINAL step.** `uv run pre-commit run` and `uv run pytest` are always the last
  actions in an agent's loop. No implementation work follows validation.
- **If validation fails, loop back and fix — never proceed.** The agent fixes the code and re-runs validation. It does
  not commit broken code or move on.
- **Context window conservation.** The primary agent (Team Lead) is a scheduler — it reads the DAG and dispatches work,
  but does no implementation itself. Expensive work (search, implementation, validation) goes to subagents, keeping the
  Team Lead's context clean.

**Why validation must be last:**

Placing the build/test gate at the end ensures:

1. The agent only commits code that passes all quality gates.
1. The agent does not generate additional code after validation (which could introduce regressions).
1. Context window is not polluted with validation output that could trigger further rework within the same iteration.

**TDD pairs naturally with Ralph:**

The TDD cycle (write test → implement → refactor) gives agents a clear, deterministic inner loop. The test defines
expected behaviour before implementation, reducing drift. The backpressure gate then validates the result. Together they
form a tight feedback loop that keeps agents on track and code quality high.
