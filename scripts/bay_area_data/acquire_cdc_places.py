"""Acquire CDC PLACES census-tract estimates (long format) for the study counties, every release in the
data.cdc.gov catalog (2020-2025 releases; no 2026 release was listed when this was written).

PLACES values are MODEL-BASED small-area estimates (multilevel regression and poststratification of BRFSS),
built partly from demographic predictors; tract values are CRUDE prevalences for adults 18+, not age-specific.
Each release mixes two BRFSS data years, so the data year is kept per measure (column data_year).

Each paged download is checked against a server-side count(*) for the same filter.

Usage: python acquire_cdc_places.py
"""
import io, os, datetime, requests, pandas as pd

RELEASES = {2020: "4ai3-zynv", 2021: "373s-ayzu", 2022: "nw2y-v4gm", 2023: "em5e-5hvn", 2024: "ai6z-tcin", 2025: "cwsq-ngmh"}
COLS = ["year", "countyfips", "countyname", "locationname", "category", "measureid", "measure", "short_question_text",
        "data_value_type", "datavaluetypeid", "data_value", "low_confidence_limit", "high_confidence_limit",
        "data_value_footnote_symbol", "data_value_footnote", "totalpopulation"]
RAW = "raw/places"

def fetch_release(release, counties, page=50000):
    did = RELEASES[release]; url = f"https://data.cdc.gov/resource/{did}"
    where = "countyfips in (" + ",".join(f"'{g}'" for g in sorted(counties.county_geoid)) + ")"
    probe = requests.get(url + ".json", params={"$limit": 1}, timeout=300); probe.raise_for_status()
    have = set(probe.json()[0].keys())
    cols = [c for c in COLS if c in have or c.startswith("data_value_footnote")] + (["totalpop18plus"] if "totalpop18plus" in have else [])
    n_server = int(requests.get(url + ".json", params={"$select": "count(*) as n", "$where": where}, timeout=300).json()[0]["n"])
    parts, off = [], 0
    while True:
        r = requests.get(url + ".csv", params={"$select": ",".join(cols), "$where": where, "$order": ":id", "$limit": page, "$offset": off}, timeout=900)
        r.raise_for_status()
        d = pd.read_csv(io.StringIO(r.text), dtype=str)
        if d.empty: break
        parts.append(d); off += len(d)
        if len(d) < page: break
    df = pd.concat(parts, ignore_index=True)
    assert len(df) == n_server, f"release {release}: downloaded {len(df)} rows, server count {n_server}"
    df = df.rename(columns={"year": "data_year", "locationname": "tract_geoid"})
    for c in ("data_value", "low_confidence_limit", "high_confidence_limit", "totalpopulation", "totalpop18plus"):
        if c in df.columns: df[c] = pd.to_numeric(df[c].str.replace(",", "", regex=False), errors="coerce")
    df["data_year"] = df.data_year.astype(int); df.insert(0, "release", release)
    os.makedirs(RAW, exist_ok=True); df.to_parquet(os.path.join(RAW, f"places_tract_{release}.parquet"), index=False)
    return df, {"release": release, "dataset_id": did, "url": url, "rows": len(df), "server_count": n_server,
                "downloaded_utc": datetime.datetime.utcnow().isoformat(timespec="seconds")}

if __name__ == "__main__":
    c = pd.read_csv("ref/study_counties.csv", dtype=str)
    logs = []
    for rel in RELEASES:
        df, lg = fetch_release(rel, c); logs.append(lg); print(lg, flush=True)
    pd.DataFrame(logs).to_csv(os.path.join(RAW, "places_download_log.csv"), index=False)
