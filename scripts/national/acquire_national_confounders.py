"""Acquire national county reference files and confounders.

1. NCHS Urban-Rural Classification Scheme for Counties (ftp.cdc.gov, linked from
   https://www.cdc.gov/nchs/data-analysis-tools/urban-rural.html): 2013/2006/1990 codes (xlsx) and 2023 codes (csv).
2. Census Gazetteer county files 2010, 2014, 2019 (land area, internal point).
3. OMB metropolitan/micropolitan delineation files, February 2013 and September 2018 (Census Bureau copies).
4. Census 2010 percent urban and rural by county.
5. CDC PLACES county data (data.cdc.gov): 2020 release, GIS-friendly wide file mssc-ksj7 (BRFSS 2018; 2017 for high blood
   pressure and high cholesterol) and 2021 release, long file pqpp-u99h (BRFSS 2019; 2018 for sleep; no New Jersey).
   PLACES values are MODEL-BASED small-area estimates (multilevel regression and poststratification of BRFSS).

Output: raw/ref_nat/*, raw/places_nat/*.parquet, download logs. Usage: python acquire_national_confounders.py
"""
import io, os, time, datetime, requests, pandas as pd

REFS = {
    "NCHSURCodes2013-Past-Version.xlsx": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/OAE/urbanrural/NCHSURCodes2013-Past-Version.xlsx",
    "NCHSUR2023_3156.csv": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/OAE/urbanrural/NCHSUR2023_3156.csv",
    "2019_Gaz_counties_national.zip": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2019_Gazetteer/2019_Gaz_counties_national.zip",
    "2014_Gaz_counties_national.zip": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2014_Gazetteer/2014_Gaz_counties_national.zip",
    "2010_Gaz_counties_national.zip": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/Gaz_counties_national.zip",
    "cbsa_list1_Feb_2013.xls": "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2013/delineation-files/list1.xls",
    "cbsa_list1_Sep_2018.xls": "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2018/delineation-files/list1_Sep_2018.xls",
    "PctUrbanRural_County_2010.xls": "https://www2.census.gov/geo/docs/reference/ua/PctUrbanRural_County.xls",
}
PLACES_WIDE_2020 = "mssc-ksj7"; PLACES_LONG_2020 = "dv4u-3x3q"; PLACES_LONG_2021 = "pqpp-u99h"
MEASURES = ["CSMOKING", "OBESITY", "DIABETES", "LPA", "BPHIGH", "HIGHCHOL", "BINGE", "SLEEP", "ACCESS2", "CHD", "STROKE"]
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

def get(url, params=None, tries=6):
    for k in range(tries):
        r = requests.get(url, params=params, timeout=600)
        if r.status_code == 200: return r
        time.sleep(10 * (k + 1))          # www2.census.gov answers 429 when busy
    r.raise_for_status()

def refs(out="raw/ref_nat"):
    os.makedirs(out, exist_ok=True); log = []
    for fn, u in REFS.items():
        p = os.path.join(out, fn)
        if not os.path.exists(p):
            r = get(u); assert not r.content[:300].lstrip().lower().startswith((b"<!doctype", b"<html")), f"{u}: HTML, not a data file"
            open(p, "wb").write(r.content)
        log.append({"file": fn, "url": u, "bytes": os.path.getsize(p), "downloaded_utc": now()})
    pd.DataFrame(log).to_csv(os.path.join(out, "ref_download_log.csv"), index=False)

def soda_all(did, where=None, page=50000):
    url = f"https://data.cdc.gov/resource/{did}"; p = {"$select": "count(*) as n"}
    if where: p["$where"] = where
    n = int(get(url + ".json", p).json()[0]["n"]); parts = []; off = 0
    while off < n:
        q = {"$order": ":id", "$limit": page, "$offset": off}
        if where: q["$where"] = where
        d = pd.read_csv(io.StringIO(get(url + ".csv", q).text), dtype=str, keep_default_na=False)
        if d.empty: break
        parts.append(d); off += len(d)
    df = pd.concat(parts, ignore_index=True); assert len(df) == n, f"{did}: {len(df)} of {n}"
    return df, url

def places(out="raw/places_nat"):
    os.makedirs(out, exist_ok=True); log = []
    w, url = soda_all(PLACES_WIDE_2020); w.to_parquet(os.path.join(out, "places_county_2020release_wide.parquet"), index=False)
    log.append({"dataset_id": PLACES_WIDE_2020, "url": url, "rows": len(w), "release": 2020, "downloaded_utc": now()})
    # data year of every measure in the 2020 release, from the long file
    yr = get(f"https://data.cdc.gov/resource/{PLACES_LONG_2020}.json", {"$select": "measureid,year,count(*) as n", "$group": "measureid,year", "$limit": 1000}).json()
    pd.DataFrame(yr).to_csv(os.path.join(out, "places_county_2020release_measure_years.csv"), index=False)
    inlist = ",".join(f"'{m}'" for m in MEASURES)
    l, url = soda_all(PLACES_LONG_2021, where=f"measureid in ({inlist})"); l.to_parquet(os.path.join(out, "places_county_2021release_long.parquet"), index=False)
    log.append({"dataset_id": PLACES_LONG_2021, "url": url, "rows": len(l), "release": 2021, "downloaded_utc": now()})
    pd.DataFrame(log).to_csv(os.path.join(out, "places_nat_download_log.csv"), index=False); print(log, flush=True)

if __name__ == "__main__":
    refs(); places()
