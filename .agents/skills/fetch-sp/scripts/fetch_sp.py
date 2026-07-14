"""
Self-contained S&P Global Connect Databrowser API client and CLI.

Auth: HTTP Basic — PAT as username, password as password (SP_USERNAME / SP_PASSWORD in .env).

Usage
-----
  Fetch a saved query (long format):
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-sp\\scripts\\fetch_sp.py' 'https://api.connect.spglobal.com/shared/v1/databrowser/savedqueries/348345/Annual' --out session/2026-07-14-my-task/pmi_long.csv

  Fetch and pivot to wide format (dates as rows, one column per series title):
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-sp\\scripts\\fetch_sp.py' '<endpoint_url>' --wide --out session/2026-07-14-my-task/pmi_wide.csv

No persistent cache: every call hits the live API.
"""

import argparse
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = PROJECT_ROOT / ".env"
if not ENV_PATH.exists():
    ENV_PATH = PROJECT_ROOT.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

import os


class SPClient:
    """Client for the S&P Global Connect Databrowser saved-query API."""

    ALLOWED_HOST = "api.connect.spglobal.com"

    def __init__(self, username: str = None, password: str = None):
        self.username = username or os.getenv("SP_USERNAME")
        self.password = password or os.getenv("SP_PASSWORD")
        if not self.username or not self.password:
            raise ValueError("S&P credentials not found. Set SP_USERNAME and SP_PASSWORD in .env")
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

    def fetch(self, endpoint: str, page_size: int = 500) -> pd.DataFrame:
        """Fetch all records from a saved-query endpoint, handling pagination."""
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or parsed.hostname != self.ALLOWED_HOST:
            raise ValueError(
                "Refusing to send S&P credentials to an untrusted endpoint. "
                f"Expected https://{self.ALLOWED_HOST}/..."
            )
        base = endpoint.split("?")[0]
        all_records = []
        page = 0

        while True:
            try:
                r = self.session.get(base, params={"pageSize": page_size, "pageIndex": page}, timeout=60)
                r.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Request Error: {e}")
                break

            batch = r.json()
            if not batch:
                break
            all_records.extend(batch)
            if len(batch) < page_size:
                break
            page += 1

        if not all_records:
            return pd.DataFrame()

        df = pd.DataFrame(all_records)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.tz_localize(None)
        return df

    def fetch_wide(self, endpoint: str, value_col: str = "Value", series_col: str = "Title",
                   date_col: str = "Date", page_size: int = 500) -> pd.DataFrame:
        """Fetch and pivot to wide format: rows = Date, columns = series Title."""
        df = self.fetch(endpoint, page_size=page_size)
        if df.empty:
            return df
        return (
            df.pivot_table(index=date_col, columns=series_col, values=value_col, aggfunc="first")
            .rename_axis(index="Date", columns=None)
            .sort_index()
        )


def main():
    parser = argparse.ArgumentParser(description="Self-contained S&P Global Connect fetch skill")
    parser.add_argument("endpoint", help="Full saved-query URL")
    parser.add_argument("--wide", action="store_true", help="Pivot to wide format (Date index, one column per series)")
    parser.add_argument("--out", required=True, help="Output CSV path (inside the active session folder)")
    args = parser.parse_args()

    client = SPClient()
    try:
        df = client.fetch_wide(args.endpoint) if args.wide else client.fetch(args.endpoint)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        raise SystemExit(1) from exc

    if df.empty:
        print("No data retrieved.")
        raise SystemExit(1)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=args.wide)  # wide format has Date as the index; long format has it as a column
    print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
