"""
Self-contained Thailand Ministry of Commerce (MOC) Trade Statistic API client and CLI.

Usage
-----
  Search product/commodity codes:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-moc\\scripts\\fetch_moc.py' search-products "rice"

  Country trade summary for a year/month:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-moc\\scripts\\fetch_moc.py' summary --year 2025 --month 6 --out session/2026-07-14-my-task/moc_summary.csv

  Export/import by HS code or commodity code, broken down by country:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-moc\\scripts\\fetch_moc.py' export-hs --year 2025 --month 6 --hs-code 10 --out session/2026-07-14-my-task/rice_exports.csv

  Daily retail/wholesale product prices:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-moc\\scripts\\fetch_moc.py' product-prices P11009 --from 2025-01-01 --to 2025-12-31 --out session/2026-07-14-my-task/rice_prices.csv

No persistent cache: every call hits the live MOC API. No API key required.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

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


class MOCClient:
    """Client for Thailand's Ministry of Commerce (MOC) Trade Statistic API."""

    BASE_URL = "https://tradereport.moc.go.th/api"

    def __init__(self):
        self.session = requests.Session()

    def _cast_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['quantity', 'value', 'balance', 'trade']):
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                except Exception:
                    pass
        return df

    def _add_date_column(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'year' in df.columns and 'month' in df.columns and not df.empty:
            try:
                years = df['year'].astype(float).astype(int).astype(str)
                months = df['month'].astype(float).astype(int).astype(str).str.zfill(2)
                df['date'] = pd.to_datetime(years + '-' + months + '-01')
            except Exception as e:
                print(f"[MOC Client Warning] Could not generate date column: {e}")
        return df

    def search_products(self, keyword: str, revision: int = 2022, imex_type: Optional[str] = None, order_by: str = 'hs_code') -> pd.DataFrame:
        url = f"{self.BASE_URL}/products"
        params = {'keyword': keyword, 'revision': revision, 'order_by': order_by}
        if imex_type:
            params['imex_type'] = imex_type
        response = resilient_request("GET", url, session=self.session, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()

    def _country_breakdown(self, route: str, year: int, month: int, code_key: str, code_val: str, limit: Optional[int]) -> pd.DataFrame:
        url = f"{self.BASE_URL}/{route}"
        params: Dict[str, Any] = {'year': year, 'month': month, code_key: code_val}
        if limit is not None:
            params['limit'] = limit
        response = resilient_request("GET", url, session=self.session, params=params)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df = self._cast_numeric_columns(df)
        df = self._add_date_column(df)
        return df

    def get_export_harmonize_countries(self, year, month, hs_code, limit=None):
        return self._country_breakdown("exportharmonizecountries", year, month, "hs_code", hs_code, limit)

    def get_import_harmonize_countries(self, year, month, hs_code, limit=None):
        return self._country_breakdown("importharmonizecountries", year, month, "hs_code", hs_code, limit)

    def get_export_commodity_countries(self, year, month, com_code, limit=None):
        return self._country_breakdown("exportcommoditycountries", year, month, "com_code", com_code, limit)

    def get_import_commodity_countries(self, year, month, com_code, limit=None):
        return self._country_breakdown("importcommoditycountries", year, month, "com_code", com_code, limit)

    def get_summary_countries(self, year: int, month: int, limit: Optional[int] = None) -> pd.DataFrame:
        url = f"{self.BASE_URL}/summarycountries"
        params: Dict[str, Any] = {'year': year, 'month': month}
        if limit is not None:
            params['limit'] = limit
        response = resilient_request("GET", url, session=self.session, params=params)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df = self._cast_numeric_columns(df)
        df = self._add_date_column(df)
        return df

    def get_product_prices(self, product_id: str, from_date: str, to_date: str) -> pd.DataFrame:
        """Daily retail/wholesale product prices from the MOC GIS Product Prices API."""
        url = "https://dataapi.moc.go.th/gis-product-prices"
        params = {'product_id': product_id, 'from_date': from_date, 'to_date': to_date}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = resilient_request("GET", url, session=self.session, params=params, headers=headers,
                                      max_retries=3, initial_delay=2.0, timeout=20)
        response.raise_for_status()
        data = response.json()
        if 'price_list' not in data or not data['price_list']:
            return pd.DataFrame()
        df = pd.DataFrame(data['price_list'])
        if 'price_date' in df.columns:
            df = df.rename(columns={'price_date': 'date'})
            df['date'] = pd.to_datetime(df['date'])
        for price_col in ['price_min', 'price_max']:
            if price_col in df.columns:
                df[price_col] = pd.to_numeric(df[price_col], errors='coerce').fillna(0.0)
        return df


def _write_csv(df: pd.DataFrame, out: str):
    if df.empty:
        print("No data retrieved.")
        sys.exit(1)
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Self-contained MOC trade statistics fetch skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sp = subparsers.add_parser("search-products", help="Search HS/commodity product codes")
    sp.add_argument("keyword")
    sp.add_argument("--revision", type=int, default=2022)
    sp.add_argument("--imex-type", dest="imex_type", default=None)

    su = subparsers.add_parser("summary", help="Country trade summary for a year/month")
    su.add_argument("--year", type=int, required=True)
    su.add_argument("--month", type=int, required=True)
    su.add_argument("--limit", type=int, default=None)
    su.add_argument("--out", required=True)

    for name, help_text in [
        ("export-hs", "Exports by HS2 code, broken down by partner country"),
        ("import-hs", "Imports by HS2 code, broken down by partner country"),
    ]:
        p = subparsers.add_parser(name, help=help_text)
        p.add_argument("--year", type=int, required=True)
        p.add_argument("--month", type=int, required=True)
        p.add_argument("--hs-code", dest="hs_code", required=True)
        p.add_argument("--limit", type=int, default=None)
        p.add_argument("--out", required=True)

    for name, help_text in [
        ("export-commodity", "Exports by MOC commodity code, broken down by partner country"),
        ("import-commodity", "Imports by MOC commodity code, broken down by partner country"),
    ]:
        p = subparsers.add_parser(name, help=help_text)
        p.add_argument("--year", type=int, required=True)
        p.add_argument("--month", type=int, required=True)
        p.add_argument("--com-code", dest="com_code", required=True)
        p.add_argument("--limit", type=int, default=None)
        p.add_argument("--out", required=True)

    pp = subparsers.add_parser("product-prices", help="Daily retail/wholesale product prices")
    pp.add_argument("product_id")
    pp.add_argument("--from", dest="from_date", required=True)
    pp.add_argument("--to", dest="to_date", required=True)
    pp.add_argument("--out", required=True)

    args = parser.parse_args()
    client = MOCClient()

    if args.command == "search-products":
        df = client.search_products(args.keyword, imex_type=args.imex_type)
        print(df.to_string(index=False))
    elif args.command == "summary":
        _write_csv(client.get_summary_countries(args.year, args.month, args.limit), args.out)
    elif args.command == "export-hs":
        _write_csv(client.get_export_harmonize_countries(args.year, args.month, args.hs_code, args.limit), args.out)
    elif args.command == "import-hs":
        _write_csv(client.get_import_harmonize_countries(args.year, args.month, args.hs_code, args.limit), args.out)
    elif args.command == "export-commodity":
        _write_csv(client.get_export_commodity_countries(args.year, args.month, args.com_code, args.limit), args.out)
    elif args.command == "import-commodity":
        _write_csv(client.get_import_commodity_countries(args.year, args.month, args.com_code, args.limit), args.out)
    elif args.command == "product-prices":
        _write_csv(client.get_product_prices(args.product_id, args.from_date, args.to_date), args.out)


if __name__ == "__main__":
    main()
