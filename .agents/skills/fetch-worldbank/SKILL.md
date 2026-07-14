---
name: fetch-worldbank
description: >
  Retrieves global development and macroeconomic indicators from the World Bank API (no API key required). Use whenever the user asks for World Bank data, development indicators, poverty/education/health statistics, or country structural data not better covered by CEIC — even if they don't explicitly say "World Bank".
---

# Fetch: World Bank

Self-contained skill for the World Bank API v2. No project-wide imports, no API key required.

## Usage

### 1. Search the indicator catalog

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-worldbank\scripts\fetch_worldbank.py' search "poverty"
```

### 2. Fetch an indicator

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-worldbank\scripts\fetch_worldbank.py' fetch NY.GDP.MKTP.KD.ZG --country THA --start 2000 --end 2025 --out session/2026-07-14-my-task/thailand_gdp_growth.csv
```

- `--country` accepts a single ISO3 code, semicolon-separated multiple codes (e.g. `THA;VNM;IDN`), or `all`.
- When fetching multiple countries, the output is automatically pivoted wide (one column per country).
- No persistent cache — every call fetches live.

## Priority note

Prefer `fetch-ceic` first for standard macro time series. Use World Bank specifically for structural development indicators (poverty, education, health, governance) that CEIC doesn't cover as comprehensively.

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| 404 / empty result | Wrong indicator ID or no data for that country/period | Run `search` to confirm the exact indicator ID |
