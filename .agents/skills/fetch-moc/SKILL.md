---
name: fetch-moc
description: >
  Retrieves Thailand Ministry of Commerce (MOC) trade statistics (exports/imports by HS code, commodity code, or partner country) and daily retail/wholesale product prices. Use whenever the user asks for Thai trade data by product/country or Thai commodity price data — even if they don't explicitly say "MOC".
---

# Fetch: Ministry of Commerce (MOC)

Self-contained skill for Thailand's MOC Trade Statistic API and GIS Product Prices API. No project-wide imports, no API key required.

## Usage

### 1. Search product/commodity codes

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-moc\scripts\fetch_moc.py' search-products "rice"
```

### 2. Country trade summary

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-moc\scripts\fetch_moc.py' summary --year 2025 --month 6 --out session/2026-07-14-my-task/moc_summary.csv
```

### 3. Export/import breakdown by HS2 or commodity code

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-moc\scripts\fetch_moc.py' export-hs --year 2025 --month 6 --hs-code 10 --out session/2026-07-14-my-task/rice_exports.csv
& '.\bin\python.ps1' '.agents\skills\fetch-moc\scripts\fetch_moc.py' import-commodity --year 2025 --month 6 --com-code <code> --out session/2026-07-14-my-task/imports.csv
```

### 4. Daily product prices

```powershell
& '.\bin\python.ps1' '.agents\skills\fetch-moc\scripts\fetch_moc.py' product-prices P11009 --from 2025-01-01 --to 2025-12-31 --out session/2026-07-14-my-task/rice_prices.csv
```

No persistent cache — every call fetches live. No fabricated/mock data: if the live API fails, the script errors out rather than silently substituting synthetic prices.

## Priority note

Use MOC for retail/wholesale product prices and detailed HS/commodity-level trade breakdowns by country. For headline Thai trade or macro aggregates, prefer `fetch-bot` first.

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| Empty result | Wrong HS/commodity code, or no trade that month | Run `search-products` to confirm the code; try an adjacent month |
| `dataapi.moc.go.th` timeout | MOC's price API is occasionally slow | The client retries 3x with backoff automatically; re-run if it still fails |
