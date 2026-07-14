---
name: fetch-imf
description: >
  Retrieves global macroeconomic and financial statistics from the IMF (World Economic Outlook forecasts, International Financial Statistics, CPI, Balance of Payments) via the SDMX 3.0 API. Use whenever the user asks for IMF data, WEO forecasts, or global/country macro indicators not better covered by CEIC — even if they don't explicitly say "IMF".
---

# Fetch: IMF (International Monetary Fund)

Self-contained skill for the IMF SDMX 3.0 API. No project-wide imports.

## Prerequisites

- `IMF_API_KEY` must be set in the repository-root `.env` (or the parent-directory fallback) and is passed as the `Ocp-Apim-Subscription-Key` header.

## Usage

### 1. List available dataflows (databases)

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-imf\scripts\fetch_imf.py' dataflows
```

### 2. Fetch WEO (World Economic Outlook) forecasts — most common use case

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-imf\scripts\fetch_imf.py' weo THA NGDP_RPCH --start 2015 --end 2031 --out session/2026-07-14-my-task/thailand_gdp_growth.csv
```

Common WEO indicator codes: `NGDP_RPCH` (real GDP growth), `PCPIPCH` (inflation), `LUR` (unemployment rate), `GGXWDG_NGDP` (general government gross debt, % GDP).

### 3. Fetch from any other dataflow (IFS, CPI, BOP, ...)

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-imf\scripts\fetch_imf.py' data --dataflow CPI --key THA.PCPI_IX.M --agency IMF.STA --out session/2026-07-14-my-task/thailand_cpi.csv
```

The `--key` filter follows SDMX's `COUNTRY.INDICATOR.FREQUENCY` pattern. Use `dataflows` first to find the right dataflow ID, then consult the IMF Data Portal for that dataflow's exact dimension/key structure if uncertain.

## Priority note

Prefer `fetch-ceic` (World Trend Plus/GEM) first for standard cross-country GDP/CPI comparisons — it's more harmonized. Use IMF for WEO forecast vintages specifically, or IMF-specific datasets (BOP, GFS) not in CEIC.

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| 404 / empty result | Wrong dataflow, agency, or key structure | Confirm the dataflow ID via `dataflows`, check key structure on the IMF Data Portal |
| `IMF_API_KEY` warning | Missing key in `.env` | Add `IMF_API_KEY` to the repository-root `.env` |
