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
