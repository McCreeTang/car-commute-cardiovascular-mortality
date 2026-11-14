"""Acquire California Crash Reporting System (CCRS, California Highway Patrol) crash counts for the study counties
from the data.ca.gov datastore SQL API: grouped by county of occurrence, primary collision factor code and violation
text, hit-and-run and preliminary status, per year table (2016-2026 as published).

County Code is the alphabetical index of California's 58 counties (verified against City Name for the 15 study counties).
Each year's paged grouped result is checked against an independent count(*) for the same filter.

Usage: python acquire_ccrs.py
"""
import os, re, json, datetime, requests, pandas as pd

CK = "https://data.ca.gov/api/3/action/"
NEED = ["County Code", "Primary Collision Factor Code", "Primary Collision Factor Violation", "HitRun", "Is Preliminary"]
EXTRA = ["NumberKilled", "NumberInjured", "Latitude"]
RAW = "raw/crash"

def sql(q):
    r = requests.get(CK + "datastore_search_sql", params={"sql": q}, timeout=600); r.raise_for_status()
    j = r.json(); assert j.get("success"), j
    return j["result"]["records"]

def resources():
    p = requests.get(CK + "package_show", params={"id": "ccrs"}, timeout=120).json()["result"]
    out = {}
    for x in p["resources"]:
        m = re.match(r"^Crashes_(\d{4})$", x.get("name") or "")
        if m: out[int(m.group(1))] = x["id"]
    names = sorted(x.get("name") or "" for x in p["resources"])
    return out, names, p.get("metadata_modified")

def fetch_year(year, rid, codes, page=20000):
    fields = [f["id"] for f in requests.get(CK + "datastore_search", params={"resource_id": rid, "limit": 0}, timeout=120).json()["result"]["fields"]]
    missing = [c for c in NEED + EXTRA if c not in fields]
    if any(c in missing for c in NEED):
        return None, {"year": year, "resource_id": rid, "missing_fields": ";".join(missing), "error": "required field missing"}
    where = f'"County Code" IN ({",".join(map(str, codes))})'
    tot = sql(f'SELECT COUNT(*) AS n, COUNT("Latitude") AS n_lat, SUM(CASE WHEN "NumberKilled" > 0 THEN 1 ELSE 0 END) AS fatal, SUM(CASE WHEN "NumberInjured" > 0 THEN 1 ELSE 0 END) AS injury FROM "{rid}" WHERE {where}')[0]
    statewide = int(sql(f'SELECT COUNT(*) AS n FROM "{rid}"')[0]["n"])
    cols = ", ".join(f'"{c}"' for c in NEED); parts, off = [], 0
    while True:
        rec = sql(f'SELECT {cols}, COUNT(*) AS n FROM "{rid}" WHERE {where} GROUP BY {cols} ORDER BY {cols} LIMIT {page} OFFSET {off}')
        parts += rec; off += len(rec)
        if len(rec) < page: break
    g = pd.DataFrame(parts); g["n"] = g.n.astype(int); g.insert(0, "year", year)
    assert int(g.n.sum()) == int(tot["n"]), f"{year}: grouped sum {g.n.sum()} != total {tot['n']}"
    return g, {"year": year, "resource_id": rid, "missing_fields": ";".join(missing), "rows_statewide": statewide, "rows_study": int(tot["n"]),
               "groups": len(g), "with_latitude": int(tot["n_lat"]), "fatal_crashes": int(tot["fatal"] or 0), "injury_crashes": int(tot["injury"] or 0),
               "queried_utc": datetime.datetime.utcnow().isoformat(timespec="seconds")}

if __name__ == "__main__":
    c = pd.read_csv("ref/study_counties.csv", dtype=str)
    ca58 = pd.read_csv("ref/ca_county_names_58.csv", dtype=str)            # 58 names from the Census geography file
    rank = {n: i + 1 for i, n in enumerate(sorted(ca58.county_name))}
    c["ccrs_code"] = c.county_name.map(rank)
    res, names, modified = resources(); os.makedirs(RAW, exist_ok=True)
    json.dump({"package_modified": modified, "resource_names": names}, open(os.path.join(RAW, "ccrs_package_state.json"), "w"), indent=1)
    logs, frames = [], []
    for y in sorted(res):
        g, lg = fetch_year(y, res[y], list(c.ccrs_code)); logs.append(lg); print(lg, flush=True)
        if g is not None: frames.append(g)
    G = pd.concat(frames, ignore_index=True)
    G = G.merge(c[["ccrs_code", "county_fips", "county_name", "core9"]], left_on="County Code", right_on="ccrs_code", how="left", validate="m:1").drop(columns="ccrs_code")
    G.to_parquet(os.path.join(RAW, "ccrs_grouped_study.parquet"), index=False)
    pd.DataFrame(logs).to_csv(os.path.join(RAW, "ccrs_query_log.csv"), index=False)
