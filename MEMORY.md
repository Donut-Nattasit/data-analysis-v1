# Project Memory

A lean, Git-tracked log of durable decisions and open issues for this workspace.
Keep one dated line per entry and remove superseded status notes; Git history retains
the old record.

This file is distinct from `AGENTS.md`, which contains stable operating conventions,
and from any private per-user assistant memory outside the repository.

## General

- 2026-07-14: Created `data-analysis_v1` as the team-shareable edition of the session-based analysis toolkit.
- 2026-07-14: Repository-root `.env` is the default, with parent-directory fallback for internal compatibility.
- 2026-07-14: CEIC, X-13, and FC Vision are optional local components and their binaries must not be committed.
- 2026-07-14: `AGENTS.md`, `.agents/skills/`, and `.agents/roles/` are the vendor-neutral canonical AI configuration; provider-specific files are compatibility adapters.
