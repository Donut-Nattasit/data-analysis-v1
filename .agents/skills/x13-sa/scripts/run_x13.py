"""
Self-contained X-13ARIMA-SEATS seasonal adjustment wrapper (via statsmodels).

Reads a two-column CSV (date, value) from the active session folder, validates
it meets X-13's prerequisites, runs seasonal adjustment, and writes the
seasonally-adjusted series (plus trend/irregular components and a short
diagnostics summary) back into the session folder.

Usage
-----
  & '.\\bin\\python.ps1' '.claude\\skills\\x13-sa\\scripts\\run_x13.py' session\\2026-07-14-my-task\\cpi_monthly.csv --date-col Date --value-col CPI --freq MS --out session\\2026-07-14-my-task\\cpi_seasonally_adjusted.csv

Points statsmodels at the project's locally installed bin/x13as.exe via a
relative walk-up -- a single source of truth rather than a duplicate copy
inside the skill folder.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from statsmodels.tsa.x13 import x13_arima_analysis

# data-analysis/.agents/skills/x13-sa/scripts/run_x13.py -> parents[4] = data-analysis (project root)
X13_BIN_DIR = Path(__file__).resolve().parents[4] / "bin"


def validate_series(series: pd.Series, freq: str) -> None:
    """Raise a clear error if the series doesn't meet X-13's prerequisites."""
    if series.isna().any():
        raise ValueError(
            f"Series has {series.isna().sum()} missing value(s). X-13 requires a complete, "
            "regularly-spaced series -- fill or interpolate gaps first."
        )

    periods_per_year = {"MS": 12, "M": 12, "QS": 4, "Q": 4}.get(freq)
    if periods_per_year is None:
        raise ValueError(f"Unsupported frequency '{freq}'. X-13 supports monthly ('MS'/'M') or quarterly ('QS'/'Q') only.")

    min_periods = periods_per_year * 3
    if len(series) < min_periods:
        raise ValueError(
            f"Series has only {len(series)} observations ({len(series) / periods_per_year:.1f} years). "
            f"X-13 needs at least 3 years ({min_periods} periods), 5+ years recommended for reliable seasonal factors."
        )


def run_seasonal_adjustment(df: pd.DataFrame, date_col: str, value_col: str, freq: str):
    df = df[[date_col, value_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()

    series = df[value_col].asfreq(freq)
    validate_series(series, freq)

    if not X13_BIN_DIR.exists() or not (X13_BIN_DIR / "x13as.exe").exists():
        raise FileNotFoundError(
            f"x13as.exe not found at {X13_BIN_DIR}. Download the Windows binary from "
            "https://www.census.gov/data/software/x13as.X-13ARIMA-SEATS.html and place it at bin/x13as.exe."
        )

    try:
        results = x13_arima_analysis(series, x12path=str(X13_BIN_DIR))
    except Exception as e:
        raise RuntimeError(f"X-13 seasonal adjustment failed: {e}") from e

    return results


def main():
    parser = argparse.ArgumentParser(description="Self-contained X-13ARIMA-SEATS seasonal adjustment skill")
    parser.add_argument("input_csv", help="Input CSV path (should be inside the active session folder)")
    parser.add_argument("--date-col", dest="date_col", default="date", help="Date column name (default: date)")
    parser.add_argument("--value-col", dest="value_col", required=True, help="Value column name to seasonally adjust")
    parser.add_argument("--freq", default="MS", choices=["MS", "M", "QS", "Q"],
                        help="Series frequency: MS/M for monthly, QS/Q for quarterly (default: MS)")
    parser.add_argument("--out", required=True, help="Output CSV path (inside the active session folder)")
    args = parser.parse_args()

    in_path = Path(args.input_csv)
    if not in_path.exists():
        print(f"[ERROR] Input file not found: {in_path}")
        sys.exit(1)

    df = pd.read_csv(in_path)
    try:
        results = run_seasonal_adjustment(df, args.date_col, args.value_col, args.freq)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    out_df = pd.DataFrame({
        "original": results.observed,
        "seasonally_adjusted": results.seasadj,
        "trend": results.trend,
        "irregular": results.irregular,
    })
    out_df.index.name = "Date"

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path)

    print(f"Wrote {len(out_df)} rows to {out_path}")
    print(f"Seasonal adjustment complete for '{args.value_col}' ({args.freq} frequency, {len(out_df)} periods).")


if __name__ == "__main__":
    main()
