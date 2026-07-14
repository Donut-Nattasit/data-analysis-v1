---
name: fetch-sp
description: >
  Retrieves PMI, business survey, and other saved-query series from S&P Global Connect (Databrowser API). Use whenever the user asks for PMI data, business/manufacturing surveys, or references an S&P Global Connect saved query — even if they don't explicitly say "S&P".
---

# Fetch: S&P Global Connect

Self-contained skill for the S&P Global Connect Databrowser saved-query API. No project-wide imports.

## Prerequisites

- `SP_USERNAME` / `SP_PASSWORD` must be set in the repository-root `.env` (or the parent-directory fallback). Auth is HTTP Basic — PAT as username, password as password.

## Usage

The user (or a saved-query catalog) provides the full saved-query URL directly — this skill does not search/discover queries, it fetches from a URL you already have.

### Long format (raw API response)

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-sp\scripts\fetch_sp.py' 'https://api.connect.spglobal.com/shared/v1/databrowser/savedqueries/348345/Annual' --out session/2026-07-14-my-task/pmi_long.csv
```

### Wide format (dates as rows, one column per series title)

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-sp\scripts\fetch_sp.py' 'https://api.connect.spglobal.com/shared/v1/databrowser/savedqueries/348345/Annual' --wide --out session/2026-07-14-my-task/pmi_wide.csv
```

- Pagination is handled automatically. For credential safety, the client accepts only HTTPS URLs on `api.connect.spglobal.com`.
- The frequency path segment (`/Annual`, `/Monthly`, `/Quarterly`) — most saved queries return the same rows regardless; use `/Annual` as a safe default if unsure.
- No persistent cache — every call fetches live.

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `S&P credentials not found` | Missing `SP_USERNAME`/`SP_PASSWORD` in `.env` | Add both to the repository-root `.env` |
| Empty result | Wrong/expired saved-query URL | Confirm the query still exists in the S&P Connect portal |
