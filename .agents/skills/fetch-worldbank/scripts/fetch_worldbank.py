"""
Self-contained World Bank API v2 client and CLI. No API key required.

Usage
-----
  Search the indicator catalog:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-worldbank\\scripts\\fetch_worldbank.py' search "poverty"

  Fetch an indicator for one or more countries:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-worldbank\\scripts\\fetch_worldbank.py' fetch NY.GDP.MKTP.KD.ZG --country THA --start 2000 --end 2025 --out session/2026-07-14-my-task/thailand_gdp_growth.csv

No persistent cache: every call hits the live World Bank API.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = PROJECT_ROOT / ".env"
if not ENV_PATH.exists():
    ENV_PATH = PROJECT_ROOT.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def resilient_request(
    method: str,
    url: str,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    session: Optional[requests.Session] = None,
    **kwargs: Any,
) -> requests.Response:
    """Exponential-backoff HTTP request wrapper (handles 429/5xx transient failures)."""
    delay = initial_delay
    caller: Callable = session.request if session else requests.request
    last_response = None
    kwargs.setdefault("timeout", 60)

    for attempt in range(1, max_retries + 1):
        try:
            response = caller(method, url, **kwargs)
            last_response = response
            if response.status_code == 200:
                return response
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait_time = float(retry_after) if retry_after and retry_after.isdigit() else delay
                print(f"[Warning] Rate limited (429) on {url}. Waiting {wait_time:.1f}s (Attempt {attempt}/{max_retries})...")
                time.sleep(wait_time)
                delay *= backoff_factor
                continue
            if 500 <= response.status_code < 600:
                print(f"[Warning] Server error ({response.status_code}) on {url}. Retrying in {delay:.1f}s (Attempt {attempt}/{max_retries})...")
                time.sleep(delay)
                delay *= backoff_factor
                continue
            return response
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                print(f"[Error] Request failed after {max_retries} attempts: {e}")
                raise e
            print(f"[Warning] Network error on {url}: {e}. Retrying in {delay:.1f}s (Attempt {attempt}/{max_retries})...")
            time.sleep(delay)
            delay *= backoff_factor

    if last_response is not None:
        return last_response
    raise RuntimeError(f"Request failed without a response: {url}")


class WorldBankClient:
    """A client for the World Bank API v2. No API key required for public endpoints."""

    BASE_URL = "https://api.worldbank.org/v2"

    def __init__(self):
        self.session = requests.Session()

    def _standardize_date(self, date_str: str) -> str:
        date_str = str(date_str).strip()
        if not date_str:
            return ""
        try:
            if len(date_str) == 4 and date_str.isdigit():
                return f"{date_str}-12-31"
            if "Q" in date_str.upper():
                clean_q = date_str.upper().replace("-", "")
                year = clean_q[:4]
                q = clean_q[-1]
                q_map = {"1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31"}
                if q in q_map:
                    return f"{year}-{q_map[q]}"
            if "M" in date_str.upper():
                clean_m = date_str.upper().replace("-", "")
                year = clean_m[:4]
                month = int(clean_m[5:])
                period = pd.Period(year=int(year), month=month, freq='M')
                return period.to_timestamp(how='end').strftime('%Y-%m-%d')
        except Exception as e:
            print(f"[World Bank Client Warning] Failed to parse date '{date_str}': {e}")
        return date_str

    def get_indicators(self, search_query: Optional[str] = None, max_records: int = 2000) -> pd.DataFrame:
        url = f"{self.BASE_URL}/indicator"
        page = 1
        records = []
        while len(records) < max_records:
            params = {"format": "json", "per_page": 1000, "page": page}
            response = resilient_request("GET", url, session=self.session, params=params)
            response.raise_for_status()
            data = response.json()
            if len(data) < 2 or not isinstance(data[1], list) or not data[1]:
                break
            for item in data[1]:
                records.append({
                    "id": item.get("id"), "name": item.get("name"),
                    "source_id": item.get("source", {}).get("id"),
                    "source_value": item.get("source", {}).get("value"),
                    "sourceNote": item.get("sourceNote"),
                })
            pages = data[0].get("pages", 1)
            if page >= pages:
                break
            page += 1

        df = pd.DataFrame(records)
        if df.empty or not search_query:
            return df
        q = search_query.lower()
        return df[
            df["id"].str.lower().str.contains(q, na=False)
            | df["name"].str.lower().str.contains(q, na=False)
            | df["sourceNote"].str.lower().str.contains(q, na=False)
        ]

    def get_data(self, indicator: str, country: str = "all", start_period=None, end_period=None) -> pd.DataFrame:
        url = f"{self.BASE_URL}/country/{country}/indicator/{indicator}"
        params = {"format": "json", "per_page": 1000}
        if start_period and end_period:
            params["date"] = f"{start_period}:{end_period}"
        elif start_period:
            params["date"] = f"{start_period}:"
        elif end_period:
            params["date"] = f":{end_period}"

        records = []
        page = 1
        while True:
            params["page"] = page
            response = resilient_request("GET", url, session=self.session, params=params)
            if response.status_code == 404:
                print(f"[World Bank Client Warning] No data found (404) for query: {url}")
                return pd.DataFrame()
            response.raise_for_status()
            data = response.json()
            if len(data) < 2 or not isinstance(data[1], list) or not data[1]:
                break
            for item in data[1]:
                val = item.get("value")
                records.append({
                    "date": self._standardize_date(item.get("date")),
                    "value": float(val) if val is not None else None,
                    "country_iso3": item.get("countryiso3code"),
                    "country_name": item.get("country", {}).get("value"),
                })
            pages = data[0].get("pages", 1)
            if page >= pages:
                break
            page += 1

        df = pd.DataFrame(records)
        if df.empty:
            return df
        df['date'] = pd.to_datetime(df['date'])
        if df['country_iso3'].nunique() > 1:
            return df.pivot_table(index='date', columns='country_name', values='value', aggfunc='first').rename_axis('Date').sort_index()
        return df[['date', 'value']].rename(columns={'date': 'Date', 'value': indicator}).set_index('Date').sort_index()


def main():
    parser = argparse.ArgumentParser(description="Self-contained World Bank API fetch skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_p = subparsers.add_parser("search", help="Search the World Bank indicator catalog")
    search_p.add_argument("keyword")

    fetch_p = subparsers.add_parser("fetch", help="Fetch an indicator for one or more countries")
    fetch_p.add_argument("indicator", help="World Bank indicator ID, e.g. NY.GDP.MKTP.KD.ZG")
    fetch_p.add_argument("--country", default="all", help="Semicolon-separated ISO3 codes, e.g. THA;VNM, or 'all'")
    fetch_p.add_argument("--start", dest="start_period", default=None)
    fetch_p.add_argument("--end", dest="end_period", default=None)
    fetch_p.add_argument("--out", required=True)

    args = parser.parse_args()
    client = WorldBankClient()

    if args.command == "search":
        df = client.get_indicators(search_query=args.keyword)
        print(df.to_string(index=False))
    elif args.command == "fetch":
        df = client.get_data(args.indicator, country=args.country, start_period=args.start_period, end_period=args.end_period)
        if df.empty:
            print("No data retrieved.")
            sys.exit(1)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path)
        print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
