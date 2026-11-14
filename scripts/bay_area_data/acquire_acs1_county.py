"""Acquire published ACS 1-YEAR county tables for the study counties from the Census table-based summary files
(www2.census.gov), years 2021-2025: B08303 (travel time), B08013 (aggregate travel time), C08301 (means of
transportation, collapsed).

Why: the 2025 ACS 1-year PUMS person file was not yet published when this was written (latest PUMS year: 2024), but
the 2025 ACS 1-year summary tables were (released 2026-10-29). These tables are the most recent commute data.
They are county totals for workers 16+, NOT age-specific. The table-based 1-year format exists from 2021.

C08301 is used instead of B08301 because the detailed table is withheld for smaller counties in 1-year data
(San Benito every year; Napa and Merced in some years); the two tables were verified identical on shared cells.

Usage: python acquire_acs1_county.py [year ...]
"""
import os, sys, datetime, requests, pandas as pd

BASE = "https://www2.census.gov/programs-surveys/acs/summary_file/"
YEARS = [2021, 2022, 2023, 2024, 2025]
TABLES = ["b08303", "b08013", "c08301"]
RAW = "raw/acs1"

def fetch(year, table, geo_ids):
    url = f"{BASE}{year}/table-based-SF/data/1YRData/acsdt1y{year}-{table}.dat"; rows = []
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status(); lines = r.iter_lines(); header = next(lines).decode("utf-8").split("|")
        if header[0] != "GEO_ID": raise RuntimeError(f"{url}: unexpected first line (server rejection page?): {header[0][:80]!r}")
        for raw in lines:
            if raw.startswith(b"0500000US06"):
                f = raw.decode("utf-8").split("|")
                if f[0] in geo_ids: rows.append(f)
        modified = r.headers.get("last-modified")
    df = pd.DataFrame(rows, columns=header)
    for c in header[1:]: df[c] = pd.to_numeric(df[c], errors="coerce")
    df.insert(1, "year", int(year))
    os.makedirs(RAW, exist_ok=True); out = os.path.join(RAW, f"acs1_{year}_{table}.parquet"); df.to_parquet(out, index=False)
    return {"year": int(year), "table": table, "url": url, "county_rows": len(df), "n_cols": len(header), "source_last_modified": modified,
            "downloaded_utc": datetime.datetime.utcnow().isoformat(timespec="seconds"), "file": out}

if __name__ == "__main__":
    years = [int(y) for y in sys.argv[1:]] or YEARS
    c = pd.read_csv("ref/study_counties.csv", dtype=str); ids = set("0500000US" + c.county_geoid)
    log = []
    for y in years:
        for t in TABLES:
            try: info = fetch(y, t, ids)
            except Exception as e: info = {"year": y, "table": t, "error": f"{type(e).__name__}: {e}"}
            log.append(info); print(info, flush=True)
    pd.DataFrame(log).to_csv(os.path.join(RAW, "acs1_download_log.csv"), index=False)
