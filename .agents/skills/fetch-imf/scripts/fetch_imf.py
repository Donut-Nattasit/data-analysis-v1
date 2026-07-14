"""
Self-contained IMF SDMX 3.0 API client and CLI.

Usage
-----
  List available dataflows (databases):
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-imf\\scripts\\fetch_imf.py' dataflows

  Fetch World Economic Outlook (WEO) data (most common use case):
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-imf\\scripts\\fetch_imf.py' weo THA NGDP_RPCH --start 2015 --end 2031 --out session/2026-07-14-my-task/thailand_gdp_growth.csv

  Fetch from any other dataflow (IFS, CPI, BOP, ...):
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-imf\\scripts\\fetch_imf.py' data --dataflow CPI --key THA.PCPI_IX.M --agency IMF.STA --out session/2026-07-14-my-task/thailand_cpi.csv

No persistent cache: every call hits the live IMF API.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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


class IMFClient:
    """A flexible client for the IMF SDMX 3.0 API."""

    BASE_URL = "https://api.imf.org/external/sdmx/3.0"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("IMF_API_KEY")
        if not self.api_key:
            print("[IMF Client Warning] IMF_API_KEY environment variable is not set. API calls will fail.")
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Ocp-Apim-Subscription-Key"] = self.api_key
        return headers

    def get_dataflows(self) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/structure/dataflow"
        response = resilient_request("GET", url, session=self.session, headers=self._get_headers())
        response.raise_for_status()
        data = response.json()
        dataflows_raw = data.get("data", {}).get("dataflows", [])
        dataflows = []
        for df in dataflows_raw:
            name_val = df.get("name")
            if isinstance(name_val, dict):
                name_str = name_val.get("en", df.get("id"))
            elif isinstance(name_val, str):
                name_str = name_val
            else:
                name_str = df.get("names", {}).get("en", df.get("id"))
            dataflows.append({"id": df.get("id"), "agency": df.get("agencyID"), "version": df.get("version"), "name": name_str})
        return dataflows

    def get_data(self, dataflow: str, key: str, agency: str = "IMF.STA", version: str = "~",
                 start_period: Optional[str] = None, end_period: Optional[str] = None) -> pd.DataFrame:
        """Retrieve a dataset from any IMF dataflow (dataflow=WEO/IFS/CPI/..., key=COUNTRY.INDICATOR.FREQUENCY)."""
        url = f"{self.BASE_URL}/data/dataflow/{agency}/{dataflow}/{version}/{key}"
        params = {}
        if start_period:
            params["startPeriod"] = start_period
        if end_period:
            params["endPeriod"] = end_period

        response = resilient_request("GET", url, session=self.session, headers=self._get_headers(), params=params)
        if response.status_code == 404:
            print(f"[IMF Client Warning] No data found (404) for query: {url}")
            return pd.DataFrame()
        response.raise_for_status()
        return self._parse_sdmx_json(response.json())

    def get_weo_data(self, country: str, indicator: str, start_period=None, end_period=None) -> pd.DataFrame:
        """High-level wrapper for World Economic Outlook (WEO) datasets. Annual frequency only."""
        key = f"{country}.{indicator}.A"
        return self.get_data(dataflow="WEO", key=key, agency="IMF.RES", start_period=start_period, end_period=end_period)

    def _parse_sdmx_json(self, sdmx_data: Dict[str, Any]) -> pd.DataFrame:
        """Generic parser for the SDMX-JSON data standard."""
        data_root = sdmx_data.get("data", {})
        datasets = data_root.get("dataSets", [])
        if not datasets:
            return pd.DataFrame()
        series_dict = datasets[0].get("series", {})
        if not series_dict:
            return pd.DataFrame()

        structures = data_root.get("structures", [{}])
        structure_info = structures[0] if structures else {}
        series_dims = structure_info.get("dimensions", {}).get("series", [])
        obs_dims = structure_info.get("dimensions", {}).get("observation", [])
        if not obs_dims:
            return pd.DataFrame()
        obs_periods = obs_dims[0].get("values", [])

        records = []
        for series_key, series_content in series_dict.items():
            key_indices = [int(idx) for idx in series_key.split(":")]
            series_metadata = {}
            for dim_idx, key_idx in enumerate(key_indices):
                if dim_idx < len(series_dims):
                    dim_name = series_dims[dim_idx]["id"]
                    dim_value = series_dims[dim_idx]["values"][key_idx]["id"]
                    series_metadata[dim_name] = dim_value

            for obs_idx_str, obs_val_list in series_content.get("observations", {}).items():
                obs_idx = int(obs_idx_str)
                if obs_idx < len(obs_periods):
                    time_period = obs_periods[obs_idx].get("value")
                    val = None
                    if obs_val_list and obs_val_list[0] is not None:
                        try:
                            val = float(obs_val_list[0])
                        except ValueError:
                            val = obs_val_list[0]
                    record = series_metadata.copy()
                    record["date"] = time_period
                    record["value"] = val
                    records.append(record)

        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df["date"] = df["date"].astype(str)
        return df


def main():
    parser = argparse.ArgumentParser(description="Self-contained IMF SDMX API fetch skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("dataflows", help="List available IMF dataflows (databases)")

    weo_p = subparsers.add_parser("weo", help="Fetch World Economic Outlook (WEO) data")
    weo_p.add_argument("country", help="ISO alpha-3 code, e.g. THA (or 'THA+USA' for multiple)")
    weo_p.add_argument("indicator", help="WEO indicator code, e.g. NGDP_RPCH (real GDP growth), PCPIPCH (inflation)")
    weo_p.add_argument("--start", dest="start_period", default=None)
    weo_p.add_argument("--end", dest="end_period", default=None)
    weo_p.add_argument("--out", required=True)

    data_p = subparsers.add_parser("data", help="Fetch from any IMF dataflow generically")
    data_p.add_argument("--dataflow", required=True, help="e.g. WEO, IFS, CPI")
    data_p.add_argument("--key", required=True, help="Filter key, e.g. THA.PCPI_IX.M")
    data_p.add_argument("--agency", default="IMF.STA", help="e.g. IMF.STA (statistics dept) or IMF.RES (WEO)")
    data_p.add_argument("--start", dest="start_period", default=None)
    data_p.add_argument("--end", dest="end_period", default=None)
    data_p.add_argument("--out", required=True)

    args = parser.parse_args()
    client = IMFClient()

    if args.command == "dataflows":
        for d in client.get_dataflows():
            print(f"{d['id']} ({d['agency']}, v{d['version']}): {d['name']}")
    elif args.command == "weo":
        df = client.get_weo_data(args.country, args.indicator, args.start_period, args.end_period)
        if df.empty:
            print("No data retrieved.")
            sys.exit(1)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"Wrote {len(df)} rows to {out_path}")
    elif args.command == "data":
        df = client.get_data(args.dataflow, args.key, agency=args.agency, start_period=args.start_period, end_period=args.end_period)
        if df.empty:
            print("No data retrieved.")
            sys.exit(1)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
