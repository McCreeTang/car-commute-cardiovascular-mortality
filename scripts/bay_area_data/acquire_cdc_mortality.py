"""Acquire CDC county-level cardiovascular mortality (data.cdc.gov, source NVSS) for the study counties.

AGE-STRATIFIED (ages 35-64 and 65+ only):
  7b9s-s8ck  Rates and Trends in Heart Disease and Stroke Mortality Among US Adults (35+) by County, Age Group,
             Race/Ethnicity, and Sex - 2000-2019   (annual rows 1999-2019; five topics)
  rsk5-566a  Cardiovascular Disease Death Rates, Trends, and Excess Death Rates Among US Adults (35+) by County
             and Age Group - 2010-2020             (annual rows 2010-2020; major cardiovascular disease only)
NOT AGE-STRATIFIED (all adults 35+), three-year pooled: heart disease and stroke mortality by county, POOLED dict below.

All values are MODEL-SMOOTHED age-standardized rates per 100,000 (not raw counts). The two age-stratified datasets
use different models and cause groupings and must not be spliced into one series.
Each download (all California county rows) is checked against a server-side count(*).

Usage: python acquire_cdc_mortality.py
"""
import io, os, datetime, requests, pandas as pd

AGE_STRATIFIED = {"7b9s-s8ck": "hd_stroke_by_age_race_sex_1999_2019", "rsk5-566a": "major_cvd_by_age_2010_2020"}
POOLED = {
    "mfvi-hkb9": {
        "cause": "heart_disease",
        "period": "2015-2017"
    },
    "6x7h-usvx": {
        "cause": "heart_disease",
        "period": "2016-2018"
    },
    "s6p7-fvbw": {
        "cause": "heart_disease",
        "period": "2017-2019"
    },
    "jiwm-ppbh": {
        "cause": "heart_disease",
        "period": "2018-2020"
    },
    "55yu-xksw": {
        "cause": "heart_disease",
        "period": "2019-2021"
    },
    "th8y-thx5": {
        "cause": "heart_disease",
        "period": "2021-2023"
    },
    "mri7-5jtw": {
        "cause": "heart_disease",
        "period": "2022-2024"
    },
    "v246-z5tb": {
        "cause": "stroke",
        "period": "2015-2017"
    },
    "tqwu-4a7k": {
        "cause": "stroke",
        "period": "2016-2018"
    },
    "ua33-yiiu": {
        "cause": "stroke",
        "period": "2017-2019"
    },
    "g5fg-bgtw": {
        "cause": "stroke",
        "period": "2018-2020"
    },
    "vutr-sfkh": {
        "cause": "stroke",
        "period": "2019-2021"
    },
    "cpdh-8cna": {
        "cause": "stroke",
        "period": "2021-2023"
    },
    "y5ii-knwc": {
        "cause": "stroke",
        "period": "2022-2024"
    }
}
# Two catalog entries carry no period in their title; their year field is 2015, which under the midpoint convention
# verified on the 14 titled datasets (year = middle year of the period) means 2014-2016. Period is therefore INFERRED.
UNTITLED = {"48mw-5apu": {"cause": "heart_disease", "period": "2014-2016"}, "kgsi-35re": {"cause": "stroke", "period": "2014-2016"}}
RAW = "raw/mortality"

def fetch(did, page=50000):
    url = f"https://data.cdc.gov/resource/{did}"; where = "locationabbr='CA'"
    n_server = int(requests.get(url + ".json", params={"$select": "count(*) as n", "$where": where}, timeout=300).json()[0]["n"])
    parts, off = [], 0
    while off < n_server:
        r = requests.get(url + ".csv", params={"$where": where, "$order": ":id", "$limit": page, "$offset": off}, timeout=900); r.raise_for_status()
        d = pd.read_csv(io.StringIO(r.text), dtype=str, keep_default_na=False)
        if d.empty: break
        parts.append(d); off += len(d)
    df = pd.concat(parts, ignore_index=True)
    assert len(df) == n_server, f"{did}: downloaded {len(df)}, server count {n_server}"
    return df, n_server, url

def to_study(df, counties):
    df = df.copy(); df["county_geoid"] = df.locationid.str.strip().str.zfill(5)
    df = df[df.county_geoid.isin(set(counties.county_geoid))]
    return df.merge(counties[["county_geoid", "county_fips", "county_name", "core9"]], on="county_geoid", how="left", validate="m:1")

if __name__ == "__main__":
    c = pd.read_csv("ref/study_counties.csv", dtype=str); c["core9"] = c.core9.str.lower().eq("true")
    os.makedirs(RAW, exist_ok=True); log = []
    for did, tag in list(AGE_STRATIFIED.items()) + [(k, f"pooled_{v['cause']}_{v['period']}") for k, v in POOLED.items()] + [(k, f"pooled_{v['cause']}_{v['period']}_inferred") for k, v in UNTITLED.items()]:
        df, n, url = fetch(did); s = to_study(df, c); s.insert(0, "dataset_id", did)
        s.to_parquet(os.path.join(RAW, f"{tag}.parquet"), index=False)
        log.append({"dataset_id": did, "tag": tag, "url": url, "rows_california": n, "rows_study": len(s), "counties": s.county_geoid.nunique(),
                    "columns": ";".join(df.columns), "downloaded_utc": datetime.datetime.utcnow().isoformat(timespec="seconds")})
        print({k: v for k, v in log[-1].items() if k != "columns"}, flush=True)
    pd.DataFrame(log).to_csv(os.path.join(RAW, "mortality_download_log.csv"), index=False)
