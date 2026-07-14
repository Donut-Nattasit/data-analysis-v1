"""
Self-contained Bank of Thailand (BOT) API client and CLI.

Usage
-----
  List categories:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-bot\\scripts\\fetch_bot.py' categories

  List series in a category:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-bot\\scripts\\fetch_bot.py' series --category <code>

  Fetch a series and write a wide-format CSV into the active session folder:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-bot\\scripts\\fetch_bot.py' fetch RP1D --start 2010-01-01 --out session/2026-07-14-my-task/bot_policy_rate.csv

No persistent cache: every call hits the live BOT API.
"""

import argparse
import os
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


class BOTClient:
    """A resilient client for the Bank of Thailand (BOT) API."""

    BASE_URL = "https://gateway.api.bot.or.th"

    def __init__(self, token=None):
        self.token = token or os.getenv("BOT_API_TOKEN")
        if not self.token:
            raise ValueError("API token must be provided or set in BOT_API_TOKEN environment variable.")

        self.headers = {
            "Accept": "application/xml, application/json",
            "Authorization": self.token,
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_category_list(self):
        url = f"{self.BASE_URL}/categorylist/category_list/"
        response = resilient_request("GET", url, session=self.session)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data["result"]["category"])

    def get_series_list(self, category_code):
        url = f"{self.BASE_URL}/categorylist/series_list/"
        params = {"category": category_code}
        response = resilient_request("GET", url, session=self.session, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data["result"]["series"])

    def _get_series_chunk(self, series_code, start_period, series_name_lang='en'):
        url = f"{self.BASE_URL}/observations/"
        params = {"series_code": series_code, "start_period": start_period}
        response = resilient_request("GET", url, session=self.session, params=params)
        response.raise_for_status()
        data = response.json()

        if not data["result"]["series"] or not data["result"]["series"][0]["observations"]:
            return pd.DataFrame()

        series_info = data["result"]["series"][0]
        df = pd.DataFrame(series_info["observations"])
        name_key = "series_name_th" if series_name_lang == 'th' else "series_name_eng"
        str_series_name = series_info.get(name_key, series_code)

        df = df.rename(columns={"value": str_series_name, "period_start": "date"})
        return df

    def get_data(self, series_code, start_period=None, series_name_lang='en'):
        """Retrieve full time series, handling BOT's 10-year-per-request pagination."""
        if not start_period:
            start_period = "2000-01-01"

        start_dt = pd.to_datetime(start_period)
        today = pd.to_datetime("today")
        all_data = []
        current_start = start_dt
        chunk_years = 5

        while current_start <= today:
            try:
                df_temp = self._get_series_chunk(series_code, current_start.strftime('%Y-%m-%d'), series_name_lang)
                if not df_temp.empty:
                    all_data.append(df_temp)
            except Exception as e:
                print(f"[BOT Client Warning] Failed to fetch chunk starting {current_start.strftime('%Y-%m-%d')}: {e}")
            current_start = current_start + pd.DateOffset(years=chunk_years)

        if not all_data:
            return pd.DataFrame()

        df_combined = pd.concat(all_data, ignore_index=True)
        df_combined['date'] = df_combined['date'].astype(str)
        df_combined = df_combined.drop_duplicates(subset=['date']).sort_values('date')
        df_combined['date'] = pd.to_datetime(df_combined['date'])
        return df_combined.set_index('date').rename_axis('Date')


def main():
    parser = argparse.ArgumentParser(description="Self-contained BOT API fetch skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("categories", help="List all BOT data categories")

    series_parser = subparsers.add_parser("series", help="List series within a category")
    series_parser.add_argument("--category", required=True, help="BOT category code")

    fetch_parser = subparsers.add_parser("fetch", help="Fetch a series and write a wide-format CSV")
    fetch_parser.add_argument("series_code", help="BOT series code, e.g. RP1D")
    fetch_parser.add_argument("--start", default="2000-01-01", help="Start date (YYYY-MM-DD)")
    fetch_parser.add_argument("--lang", default="en", choices=["en", "th"], dest="series_name_lang")
    fetch_parser.add_argument("--out", required=True, help="Output CSV path (inside the active session folder)")

    args = parser.parse_args()
    client = BOTClient()

    if args.command == "categories":
        print(client.get_category_list().to_string(index=False))
    elif args.command == "series":
        print(client.get_series_list(args.category).to_string(index=False))
    elif args.command == "fetch":
        df = client.get_data(args.series_code, start_period=args.start, series_name_lang=args.series_name_lang)
        if df.empty:
            print("No data retrieved.")
            sys.exit(1)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path)
        print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
