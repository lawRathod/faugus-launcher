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
