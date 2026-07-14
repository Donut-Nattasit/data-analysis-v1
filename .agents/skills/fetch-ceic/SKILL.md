---
name: fetch-ceic
description: >
  Searches and retrieves economic time-series data from the CEIC database (World Trend Plus / GEM, China Premium, Global, Daily). Use whenever the user asks to fetch, search for, or download a macroeconomic indicator, GDP/CPI/trade/financial series, or any cross-country economic data — even if they don't explicitly say "CEIC".
---

# Fetch: CEIC

Self-contained skill for searching and fetching series from the CEIC database. No project-wide imports — everything needed lives in this skill folder.

## Prerequisites

- `CEIC_API_KEY` must be set in the repository-root `.env` (a parent-directory `.env` is supported as a fallback).
- The proprietary `ceic-api-client` is optional. Authorized users place its wheel in `wheels/` and rerun `setup.ps1`; see `THIRD_PARTY_NOTICES.md`.

## Usage

### 1. Search for a series

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-ceic\scripts\fetch_ceic.py' search "Real GDP Thailand" --limit 20
```

Prints candidate series with ID, name, country, frequency, unit, and source database. Read `references/ceic_patterns.md` first if the search returns noisy or ambiguous results — it documents CEIC's database hierarchy and naming conventions.

### 2. Fetch series data

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-ceic\scripts\fetch_ceic.py' fetch 12345678 87654321 --out session/2026-07-14-my-task/gdp_thailand.csv
```

- Accepts one or more series IDs (space-separated).
- Always writes a **wide-format** CSV (Date index, one column per series) — never long/stacked format.
- `--out` should point inside the active session folder (`session/YYYY-MM-DD-<slug>/...`). Create the session folder first if it doesn't exist yet.
- No persistent cache: every call fetches live from the CEIC API. If the same series is needed again in a later session, just fetch it again — don't try to reuse an old CSV from a different session's folder.

## Execution pattern

Always invoke through the project's launcher (`bin\python.ps1`), never call system Python directly. No need to write a wrapper script in `temp/` — this skill's own CLI handles search and fetch directly.

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `CEIC_API_KEY not found` | `.env` missing or key not set | Check the repository-root `.env` has `CEIC_API_KEY=...` |
| `ceic-api-client is not installed` | Authorized wheel is absent | Place the CEIC wheel in `wheels/` and rerun `setup.ps1` |
| Noisy / irrelevant search results | Ambiguous keyword (e.g. bilateral trade partner noise) | See `references/ceic_patterns.md` §Search heuristics |
| `NON_CONTINUOUS_SERIES` error | Series has a break requiring non-historical-extension fetch | Handled automatically — the client retries with `--no-history` internally for that one series |
| Empty result on fetch | Invalid/stale series ID | Re-run `search` to confirm the current ID |
