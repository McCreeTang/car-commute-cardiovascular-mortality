"""Acquire ACS 5-year detailed tables from the Census Bureau table-based summary files
(www2.census.gov), filtered to study-area tracts (sumlevel 140) and counties (sumlevel 050).

Used instead of api.census.gov because the API rejects data queries without a key
(302 -> missing_key.html) and no key was configured. Estimates and margins of error are
the same published values. Table-based files exist for vintages 2021-2024 only.

Usage: python acquire_acs_tablebased.py <vintage> [table ...]
"""
import os, sys, datetime, requests, pandas as pd

BASE = "https://www2.census.gov/programs-surveys/acs/summary_file/"
TABLES = ["b08303", "b08013", "b08301", "b08302", "b01001", "b19013", "b17001",
          "b15003", "b03002", "b25044", "b25077", "b25064"]

def study_prefixes(counties_csv="ref/study_counties.csv"):
    c = pd.read_csv(counties_csv, dtype=str)
    pre = tuple("1400000US" + g for g in c.county_geoid) + tuple("0500000US" + g + "|" for g in c.county_geoid)
    return c, pre

def fetch_table(vintage, table, prefixes, outdir):
    url = f"{BASE}{vintage}/table-based-SF/data/5YRData/acsdt5y{vintage}-{table}.dat"
    rows, n_total = [], 0
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        lines = r.iter_lines()
        header = next(lines).decode("utf-8").split("|")
        if header[0] != "GEO_ID":
            raise RuntimeError(f"{url}: unexpected first line (server rejection page?): {header[0][:80]!r}")
        for raw in lines:
            n_total += 1
            if raw.startswith(b"1400000US06") or raw.startswith(b"0500000US06"):
                s = raw.decode("utf-8")
                if s.startswith(prefixes):
                    rows.append(s.split("|"))
    df = pd.DataFrame(rows, columns=header)
    for col in header[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.insert(1, "vintage", int(vintage))
    df.insert(2, "sumlevel", df.GEO_ID.str[:3])
    df.attrs = {}
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"acs5_{vintage}_{table}.parquet")
    df.to_parquet(out, index=False)
    return {"vintage": int(vintage), "table": table, "url": url, "national_rows": n_total,
            "tract_rows": int((df.sumlevel == "140").sum()), "county_rows": int((df.sumlevel == "050").sum()),
            "n_cols": len(header), "downloaded_utc": datetime.datetime.utcnow().isoformat(timespec="seconds"), "file": out}

if __name__ == "__main__":
    vintage = sys.argv[1]
    tables = [t.lower() for t in sys.argv[2:]] or TABLES
    _, pre = study_prefixes()
    outdir = "raw/acs"
    log = []
    for t in tables:
        try:
            info = fetch_table(vintage, t, pre, outdir)
        except Exception as e:
            info = {"vintage": int(vintage), "table": t, "error": f"{type(e).__name__}: {e}"}
        log.append(info); print(info, flush=True)
    lp = os.path.join(outdir, f"acs5_{vintage}_download_log.csv")
    old = pd.read_csv(lp) if os.path.exists(lp) else pd.DataFrame()
    pd.concat([old, pd.DataFrame(log)], ignore_index=True).to_csv(lp, index=False)
