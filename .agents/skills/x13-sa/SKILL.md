---
name: x13-sa
description: >
  Performs X-13ARIMA-SEATS seasonal adjustment on a monthly or quarterly time series, using the U.S. Census Bureau's x13as.exe binary via the statsmodels wrapper. Use whenever the user asks to seasonally adjust a series, remove seasonality, or mentions X13/X-13ARIMA-SEATS/SEATS — even if they don't cite the skill by name.
---

# X-13ARIMA-SEATS Seasonal Adjustment

Skill wrapping the U.S. Census Bureau's X-13ARIMA-SEATS program (https://www.census.gov/data/software/x13as.X-13ARIMA-SEATS.html) via `statsmodels.tsa.x13.x13_arima_analysis`. It expects a separately downloaded Windows executable at `bin/x13as.exe`.

## Prerequisites (validated automatically, but know these before running)

- **At least 3 years of history** (36 monthly / 12 quarterly periods) — 5+ years recommended for reliable seasonal factor estimates.
- **Regular frequency**: monthly or quarterly only. Daily/weekly/irregular data must be resampled first (e.g. `.resample('MS').mean()`).
- **No gaps**: the series must be complete after `asfreq()` — fill or interpolate missing periods first.

The script checks all three and raises a clear error (not a raw traceback) if any fail.

## Usage

```powershell
& '.\bin\python.ps1' '.agents\skills\x13-sa\scripts\run_x13.py' session\2026-07-14-my-task\cpi_monthly.csv --date-col Date --value-col CPI --freq MS --out session\2026-07-14-my-task\cpi_seasonally_adjusted.csv
```

- `--freq`: `MS`/`M` for monthly, `QS`/`Q` for quarterly.
- Output CSV has 4 columns: `original`, `seasonally_adjusted`, `trend`, `irregular`, indexed by `Date`.
- Write input/output inside the active session folder (`session/YYYY-MM-DD-<slug>/`).

## Approach note

Uses the `statsmodels` wrapper around `x13as.exe` (not hand-written `.spc` spec files) — this matches the only prior precedent for X-13 in this workspace's lineage and avoids the added complexity of raw spec-file authoring, which is unnecessary unless fine-grained control (custom ARIMA orders, regression regressors, custom outlier detection) beyond the wrapper's defaults is needed.

## Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `x13as.exe not found` | Binary missing from `bin/` (it is not tracked in Git) | Download the Windows ASCII build from the Census Bureau and copy or rename its executable to `bin\x13as.exe` |
| Prerequisite error (missing values / too short / bad frequency) | Input series doesn't meet X-13's requirements | Fill gaps, resample to the target frequency, or fetch more history first |
| `X-13 seasonal adjustment failed` (wrapped exception) | X-13 itself rejected the series (e.g. can't identify a model) | Try a longer history window, or check the series for extreme outliers/structural breaks |
