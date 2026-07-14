"""
Self-contained U.S. Energy Information Administration (EIA) API v2 client and CLI.

Usage
-----
  Search the EIA route hierarchy for a keyword:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-eia\\scripts\\fetch_eia.py' search "petroleum"

  Fetch STEO series (energy short-term outlook, most common use case):
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-eia\\scripts\\fetch_eia.py' steo WTIPUUS BREPUUS --out session/2026-07-14-my-task/oil_prices.csv

  Fetch from any other EIA route:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-eia\\scripts\\fetch_eia.py' route petroleum/pri/spt --series-id RWTC --frequency daily --out session/2026-07-14-my-task/wti_spot.csv

No persistent cache: every call hits the live EIA API.
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


class EIAClient:
    """A resilient client for the EIA API v2."""

    BASE_URL = "https://api.eia.gov/v2"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("EIA_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in EIA_API_KEY environment variable.")
        self.session = requests.Session()
        self.session.params = {'api_key': self.api_key}

    def _get_with_pagination(self, url, params):
        all_data = []
        offset = 0
        length = 5000
        params = params.copy()
        params['length'] = length

        while True:
            params['offset'] = offset
            try:
                response = resilient_request("GET", url, session=self.session, params=params)
                response.raise_for_status()
                res_json = response.json().get('response', {})
                data = res_json.get('data', [])
                total = int(res_json.get('total', 0))

                if not data:
                    break
                all_data.extend(data)
                offset += len(data)
                if offset >= total or len(data) < length:
                    break
                time.sleep(0.1)
            except Exception as e:
                print(f"[EIA Client Warning] Pagination error at offset {offset}: {e}")
                break

        return all_data

    def get_metadata(self, route=""):
        url = f"{self.BASE_URL}/{route.strip('/')}"
        response = resilient_request("GET", url, session=self.session)
        response.raise_for_status()
        return response.json().get('response', {})

    def search_routes(self, keyword, start_route="", max_depth=3):
        """Recursively search the EIA route hierarchy for routes matching a keyword."""
        results = []
        keyword = keyword.lower()

        def _search(current_route, depth):
            if depth > max_depth:
                return
            metadata = self.get_metadata(current_route)
            name = metadata.get('name', '').lower()
            desc = metadata.get('description', '').lower()
            if keyword in name or keyword in desc:
                results.append({'route': current_route, 'name': metadata.get('name'), 'description': metadata.get('description')})
            for sub in metadata.get('routes', []):
                sub_id = sub.get('id')
                if sub_id:
                    next_route = f"{current_route.strip('/')}/{sub_id}" if current_route else sub_id
                    _search(next_route, depth + 1)

        _search(start_route, 0)
        return results

    def get_data_steo(self, series_ids, frequency='monthly'):
        if isinstance(series_ids, str):
            series_ids = [series_ids]
        url = f"{self.BASE_URL}/steo/data/"
        params = {'frequency': frequency, 'data[0]': 'value', 'sort[0][column]': 'period', 'sort[0][direction]': 'asc'}
        for i, sid in enumerate(series_ids):
            params[f'facets[seriesId][{i}]'] = sid

        data = self._get_with_pagination(url, params)
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['period'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        if len(series_ids) > 1:
            return df.pivot(index='date', columns='seriesId', values='value').rename_axis('Date').sort_index()
        return df[['date', 'value']].rename(columns={'date': 'Date', 'value': series_ids[0]}).set_index('Date').sort_index()

    def get_data(self, route, series_ids=None, frequency=None, facets=None, data_cols=None):
        """Generic fetch from any EIA route."""
        if not data_cols:
            data_cols = ['value']

        url = f"{self.BASE_URL}/{route.strip('/')}/data/"
        params = {'sort[0][column]': 'period', 'sort[0][direction]': 'asc'}
        if frequency:
            params['frequency'] = frequency
        for i, col in enumerate(data_cols):
            params[f'data[{i}]'] = col

        final_facets = facets.copy() if facets else {}
        if series_ids:
            if isinstance(series_ids, str):
                series_ids = [series_ids]
            final_facets['seriesId'] = series_ids

        for key, values in final_facets.items():
            if not isinstance(values, list):
                values = [values]
            for i, val in enumerate(values):
                params[f'facets[{key}][{i}]'] = val

        data = self._get_with_pagination(url, params)
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['period'])
        for col in data_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if series_ids and len(series_ids) > 1 and len(data_cols) == 1:
            return df.pivot(index='date', columns='seriesId', values=data_cols[0]).rename_axis('Date').sort_index()
        cols_to_keep = ['date'] + data_cols
        return df[cols_to_keep].rename(columns={'date': 'Date'}).set_index('Date').sort_index()


def main():
    parser = argparse.ArgumentParser(description="Self-contained EIA API fetch skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_p = subparsers.add_parser("search", help="Search the EIA route hierarchy for a keyword")
    search_p.add_argument("keyword")
    search_p.add_argument("--start-route", default="", dest="start_route")

    steo_p = subparsers.add_parser("steo", help="Fetch one or more STEO (Short-Term Energy Outlook) series")
    steo_p.add_argument("series_ids", nargs="+")
    steo_p.add_argument("--frequency", default="monthly")
    steo_p.add_argument("--out", required=True)

    route_p = subparsers.add_parser("route", help="Fetch from any EIA route generically")
    route_p.add_argument("route")
    route_p.add_argument("--series-id", dest="series_id", action="append", help="Repeatable: one or more series IDs")
    route_p.add_argument("--frequency", default=None)
    route_p.add_argument("--out", required=True)

    args = parser.parse_args()
    client = EIAClient()

    if args.command == "search":
        results = client.search_routes(args.keyword, start_route=args.start_route)
        if not results:
            print("No matching routes found.")
        for r in results:
            print(f"{r['route']}: {r['name']} — {r['description']}")
    elif args.command == "steo":
        df = client.get_data_steo(args.series_ids, frequency=args.frequency)
        if df.empty:
            print("No data retrieved.")
            sys.exit(1)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path)
        print(f"Wrote {len(df)} rows to {out_path}")
    elif args.command == "route":
        df = client.get_data(args.route, series_ids=args.series_id, frequency=args.frequency)
        if df.empty:
            print("No data retrieved.")
            sys.exit(1)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path)
        print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
