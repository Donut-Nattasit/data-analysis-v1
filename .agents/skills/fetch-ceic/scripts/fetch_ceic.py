"""
Self-contained CEIC World Trend Plus / GEM client and CLI.

Usage
-----
  Search:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-ceic\\scripts\\fetch_ceic.py' search "Real GDP Thailand" --limit 20

  Fetch one or more series and write a wide-format CSV into the active session folder:
    & '.\\bin\\python.ps1' '.agents\\skills\\fetch-ceic\\scripts\\fetch_ceic.py' fetch 12345678 --out session/2026-07-14-my-task/gdp_thailand.csv

No persistent cache: every call hits the live CEIC API. If you need the same
series again in a later session, just fetch it again.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# Prefer a repository-local .env; retain the parent-folder layout as a fallback.
PROJECT_ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = PROJECT_ROOT / ".env"
if not ENV_PATH.exists():
    ENV_PATH = PROJECT_ROOT.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    from ceic_api_client.pyceic import Ceic
except ModuleNotFoundError:
    Ceic = None


class CeicSession:
    """A robust and optimized wrapper for CEIC API operations."""

    def __init__(self):
        self.api_key = os.environ.get("CEIC_API_KEY")
        self.is_authenticated = False

    def authenticate(self):
        """Authenticate using the API key from .env."""
        if Ceic is None:
            raise RuntimeError(
                "The optional ceic-api-client is not installed. Place an authorized "
                "CEIC wheel in wheels/ and run setup.ps1 again."
            )
        if not self.api_key:
            raise ValueError("CEIC_API_KEY not found in environment variables.")
        try:
            Ceic.set_token(self.api_key)
            self.is_authenticated = True
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

    def search_series(self, keyword, limit=100, prioritize_wtp=True):
        """
        Search for series with enhanced metadata and prioritization.
        Uses the 'layout' information from search results to identify WTP/GEM series.
        """
        if not self.is_authenticated:
            self.authenticate()

        try:
            results = Ceic.search(keyword, limit=limit)
            data_obj = getattr(results, 'data', None)
            items = getattr(data_obj, 'items', []) if data_obj else []

            if not items:
                return []

            series_list = []
            for item in items:
                m = getattr(item, 'metadata', None)
                if not m:
                    continue

                is_wtp = False
                db_name = "Other"

                layout_list = getattr(item, 'layout', [])
                if layout_list:
                    for layout in layout_list:
                        db_info = getattr(layout, 'database', None)
                        topic_info = getattr(layout, 'topic', None)

                        db_label = str(getattr(db_info, 'name', '')) if db_info else ""
                        topic_label = str(getattr(topic_info, 'name', '')) if topic_info else ""

                        if "World Trend Plus" in db_label or "Global Economic Monitor" in topic_label:
                            is_wtp = True
                            db_name = "World Trend Plus"
                            break
                        elif db_label:
                            db_name = db_label

                mnemonic = getattr(m, 'mnemonic', '')
                if not is_wtp and mnemonic and (".CPI." in mnemonic or ".GDP." in mnemonic):
                    is_wtp = True
                    db_name = "World Trend Plus (Inferred)"

                source_name = "N/A"
                source_info = getattr(m, 'source', None)
                if source_info:
                    source_name = getattr(source_info, 'name', 'N/A')

                series_list.append({
                    'id': getattr(m, 'id', 'N/A'),
                    'name': getattr(m, 'name', 'N/A'),
                    'frequency': getattr(getattr(m, 'frequency', None), 'name', 'N/A'),
                    'unit': getattr(getattr(m, 'unit', None), 'name', 'N/A'),
                    'country': getattr(getattr(m, 'country', None), 'name', 'N/A'),
                    'source': source_name,
                    'database': db_name,
                    'is_wtp': is_wtp
                })

            if prioritize_wtp:
                series_list.sort(key=lambda x: (x.get('is_wtp', False), -len(str(x.get('name', '')))), reverse=True)

            return series_list
        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def get_data(self, series_ids, with_historical_extension=True, count=10000, max_workers=10):
        """Fetch series data with parallel execution for speed."""
        if not self.is_authenticated:
            self.authenticate()

        if isinstance(series_ids, (str, int)):
            series_ids = [series_ids]

        series_ids = list(set([sid for sid in series_ids if sid]))

        if not series_ids:
            return pd.DataFrame()

        if len(series_ids) == 1:
            return self._fetch_single_series(series_ids[0], count)

        if not with_historical_extension:
            try:
                res = Ceic.series(series_ids, with_historical_extension=False, count=count)
                return self._parse_response(res)
            except Exception as e:
                print(f"Batch fetch failed: {e}")
                return pd.DataFrame()

        all_dfs = []
        with ThreadPoolExecutor(max_workers=max(1, min(len(series_ids), max_workers))) as executor:
            future_to_sid = {executor.submit(self._fetch_single_series, sid, count): sid for sid in series_ids}
            for future in as_completed(future_to_sid):
                try:
                    df = future.result()
                    if not df.empty:
                        all_dfs.append(df)
                except Exception as e:
                    print(f"Parallel fetch worker failed: {e}")

        if not all_dfs:
            return pd.DataFrame()

        return pd.concat(all_dfs, ignore_index=True)

    def _fetch_single_series(self, sid, count):
        try:
            res = Ceic.series([sid], with_historical_extension=True, count=count)
            return self._parse_response(res)
        except Exception as e:
            if "NON_CONTINUOUS_SERIES" in str(e):
                try:
                    res = Ceic.series([sid], with_historical_extension=False, count=count)
                    return self._parse_response(res)
                except Exception:
                    return pd.DataFrame()
            return pd.DataFrame()

    def _parse_response(self, res):
        points = []
        data_items = getattr(res, 'data', [])
        if not data_items:
            return pd.DataFrame()

        for item in data_items:
            m = getattr(item, 'metadata', None)
            if not m:
                continue

            series_name = getattr(m, 'name', 'Unknown')
            series_id = getattr(m, 'id', 'Unknown')
            source_info = getattr(m, 'source', None)
            source_name = getattr(source_info, 'name', 'Unknown') if source_info else 'Unknown'

            time_points = getattr(item, 'time_points', [])
            for tp in time_points:
                try:
                    points.append({
                        'date': tp.date,
                        'value': tp.value,
                        'series_id': series_id,
                        'series_name': series_name,
                        'source': source_name
                    })
                except Exception:
                    continue

        if not points:
            return pd.DataFrame()

        df = pd.DataFrame(points)
        df['date'] = pd.to_datetime(df['date'])
        return df


def to_wide(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot long-format CEIC output (date, value, series_id, series_name) to wide (Date index, one column per series)."""
    if df.empty:
        return df
    wide = df.pivot_table(index='date', columns='series_name', values='value', aggfunc='first')
    wide.index.name = 'Date'
    return wide.sort_index()


def main():
    parser = argparse.ArgumentParser(description="Self-contained CEIC API fetch skill")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to run")

    search_parser = subparsers.add_parser("search", help="Search for series in CEIC")
    search_parser.add_argument("keyword", help="Search keyword")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum number of results (default: 10)")

    fetch_parser = subparsers.add_parser("fetch", help="Fetch series data from CEIC and write a wide-format CSV")
    fetch_parser.add_argument("series_ids", nargs="+", help="One or more series IDs")
    fetch_parser.add_argument("--limit", type=int, default=10000, dest="count", help="Limit number of data points per series")
    fetch_parser.add_argument("--no-history", action="store_false", dest="history", help="Disable historical extensions")
    fetch_parser.add_argument("--out", required=True, help="Output CSV path (should be inside the active session folder)")

    args = parser.parse_args()

    session = CeicSession()
    try:
        authenticated = session.authenticate()
    except (RuntimeError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    if not authenticated:
        sys.exit(1)

    if args.command == "search":
        print(f"Searching for '{args.keyword}'...")
        results = session.search_series(args.keyword, limit=args.limit)
        if not results:
            print("No matching series found.")
        for r in results:
            print(f"ID: {r['id']} | Name: {r['name']} | Country: {r['country']} | Freq: {r['frequency']} | Unit: {r['unit']} | DB: {r['database']}")

    elif args.command == "fetch":
        print(f"Fetching series: {args.series_ids}...")
        df = session.get_data(args.series_ids, with_historical_extension=args.history, count=args.count)
        if df.empty:
            print("No data retrieved.")
            sys.exit(1)
        wide = to_wide(df)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        wide.to_csv(out_path)
        print(f"Wrote {len(wide)} rows x {len(wide.columns)} series to {out_path}")


if __name__ == "__main__":
    main()
