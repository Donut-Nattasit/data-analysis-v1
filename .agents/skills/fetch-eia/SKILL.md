---
name: fetch-eia
description: >
  Retrieves global energy data (crude oil, petroleum products, liquid fuels production/consumption/prices) from the U.S. Energy Information Administration (EIA) API, including the Short-Term Energy Outlook (STEO). Use whenever the user asks for oil prices, energy balances, or petroleum/fuel market data — even if they don't explicitly say "EIA".
---

# Fetch: EIA (Energy Information Administration)

Self-contained skill for the EIA API v2. No project-wide imports.

## Prerequisites

- `EIA_API_KEY` must be set in the repository-root `.env` (or the parent-directory fallback). Free registration at https://www.eia.gov/opendata/register.php.

## Usage

### 1. Search for a route/series

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-eia\scripts\fetch_eia.py' search "petroleum"
```

### 2. Fetch STEO series (most common — Dubai/WTI/Brent prices, world balances)

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-eia\scripts\fetch_eia.py' steo WTIPUUS BREPUUS --out session/2026-07-14-my-task/oil_prices.csv
```

### 3. Fetch from any other EIA route

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-eia\scripts\fetch_eia.py' route petroleum/pri/spt --series-id RWTC --frequency daily --out session/2026-07-14-my-task/wti_spot.csv
```

- Multiple `--series-id` flags can be repeated to fetch several series at once (pivoted wide automatically).
- Always writes a **wide-format** CSV (Date index). No persistent cache — every call fetches live.

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `EIA_API_KEY` error | Missing key in `.env` | Register free at eia.gov/opendata and add it to the repository-root `.env` |
| Empty result | Wrong route or series ID | Use `search` first to confirm the exact route/series ID |
