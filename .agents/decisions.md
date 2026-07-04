# Architectural Decisions

## 2026-07-04

### AD-001: Agent Context Files

**Context:** The project needed structured context files so AI coding agents can quickly understand the codebase without re-reading source files each session.

**Decision:** Create `AGENTS.md` at project root for agent instructions + `.agents/` directory for session persistence between agent sessions.

**Rationale:**
- `AGENTS.md` is a well-known convention (Claude Code, Cursor, Windsurf, etc.)
- `.agents/` keeps session-specific context separate from code
- Machine-readable `context.json` enables quick state inspection
- Human-readable markdown files enable rich documentation

**Trade-offs:**
- Requires discipline to update session logs
- Duplicates some knowledge already in code comments

## 2026-07-04

### AD-002: Web UI Architecture (Evaluate, Not Yet Decide)

**Context:** Replace the Python GTK3 UI with a Python HTTP server + web frontend, while maintaining upstream mergeability.

**Research outcome:** Feasible. ~70% of backend code reuses as-is. Detailed analysis in `.agents/research/web-ui-feasibility.md`.

**Recommended architecture:** FastAPI server + Svelte/React SPA + Tailwind CSS.
- ~35 REST endpoints covering games, config, runners, Steam, files, logs, backup, system, env vars
- Git merge strategy: ~80% of upstream commits merge trivially, ~15% need medium effort, ~5% are hard
- Key challenges: file picker, system tray, splash screen, flatpak, gamepad

**Decision:** No action taken yet — research saved for future implementation.

### AD-003: Phased Migration Plan v2

**Context:** The initial monolithic migration plan was reviewed by the `plan-critic` subagent and found to have 3 blocker-level issues (scope too large, non-UI logic in removed files unaccounted for, `faugus-run` entry point broken), plus 4 warnings and 4 suggestions.

**Decision:** Adopt the phased approach in `.agents/plans/phased-migration-v2.md`.

**5 Phases:**
- **Phase 0:** Foundation — split `utils.py`, extract `runner_core.py`, file locking, `faugus_run.py` survival path. Zero behavior change.
- **Phase 1:** Backend API — FastAPI server with ~30 endpoints, 9 router files, WebSocket support, entry point update.
- **Phase 2:** Basic frontend — Svelte/React SPA with game library, add/edit forms, launch flow.
- **Phase 3:** Settings + remaining features — settings page, file browser, Steam, Proton manager, backup, logs.
- **Phase 4:** Polish — system tray, gamepad, keyboard, flatpak, packaging.

**Key changes from v1:**
- Each phase is independently shippable and revertable
- Files marked "REMOVED" in v1 are now properly extracted first (Phase 0)
- `faugus-run` is preserved as a headless path independent of the server
- WebSocket replaces polling for real-time communication
- File locking added for concurrent-safe `games.json` access
- Shutdown/reboot API endpoints dropped (security)
- TypeScript mandated for type-safe SPA
- Tests required per phase

**File:** `.agents/plans/phased-migration-v2.md`

### AD-004: Code-Reviewer Subagent

**Context:** After implementing plans, code needs review before commit to catch bugs, security issues, and data model mismatches. Manual review is error-prone and inconsistent.

**Decision:** Create `.pi/agents/code-reviewer.md` — a subagent that reviews git diffs before commit.

**Key design choices:**
- Uses `requesting-code-review` skill template as baseline
- Reads every changed line in the diff — no shortcuts
- Checks 8 dimensions: semantics, security, TDD compliance, upstream compat, architecture cohesion, file I/O, API contract, stale imports
- Outputs severity-tagged issues (🔴 Critical / 🟡 Important / 🔵 Minor) + summary verdict
- Read-only — never mutates the working tree

**Result:** Caught 6 critical bugs and 4 important issues in the first Phase 1 commit that had already been pushed.

### AD-005: Phase 0 + Phase 1 Complete

**Context:** Phase 0 (Foundation) and Phase 1 (Backend API) of the phased migration plan have been implemented.

**Phase 0 deliverables:**
- `utils.py` split into pure + GTK modules (`gtk_utils.py`)
- `runner_core.py` extracted from `runner.py` — zero GTK, usable headless
- All 10 modules import correctly, 74 tests pass

**Phase 1 deliverables:**
- FastAPI server with 10 route modules covering ~30 endpoints
- Games CRUD (12 endpoints), Config, Runners, Steam, Files, Logs, Env, Backup, System, WebSockets
- File locking (`fcntl.flock`) on all read-modify-write operations
- TDD throughout — 74 tests across 10 test files
- code-reviewer invoked after each module, all issues fixed

**Status:** Ready for Phase 2 (Web frontend).
