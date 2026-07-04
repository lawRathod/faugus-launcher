# .agents — Session Context Store

This directory maintains long-lived context between AI-coding-agent sessions.
It helps agents pick up where they left off without re-exploring the codebase.

## Structure

| File | Purpose |
|------|---------|
| `README.md` | This file — describes the directory |
| `session.md` | Current/active session log — updated each session |
| `decisions.md` | Key architectural decisions and their rationale |
| `context.json` | Machine-readable context summary (auto-updated) |

## Conventions

- **Session logs** capture: what was worked on, files changed, outstanding issues
- **Decisions** capture: why a particular approach was chosen, trade-offs considered
- **Context** captures: current branch, recent changes, active tasks
- Session files (files not in `.*.md` or `context.*`) should be added to `.gitignore`

## Usage for Agents

When starting a new session:
1. Read `session.md` for what happened last
2. Read `context.json` for current state
3. Read `decisions.md` if relevant to the task
4. On completion, append to `session.md` and update `context.json`
