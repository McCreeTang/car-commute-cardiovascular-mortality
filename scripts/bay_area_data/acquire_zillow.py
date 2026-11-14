"""Acquire Zillow Home Value Index (ZHVI) and Zillow Observed Rent Index (ZORI), county and ZIP level,
from files.zillowstatic.com; filter to the study counties; reduce monthly values to annual means.

ZHVI series: all homes (single-family + condo/co-op), mid-tier (33rd-67th percentile), smoothed, seasonally adjusted.
ZORI series: all homes plus multifamily, smoothed (not seasonally adjusted). ZORI begins 2015-01.
Annual value = mean of available monthly values in the calendar year; n_months records how many months entered.

Usage: python acquire_zillow.py
"""
import os, re, datetime, requests, pandas as pd

ZB = "https://files.zillowstatic.com/research/public_csvs/"
FILES = {("zhvi", "county"): "zhvi/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
         ("zhvi", "zip"): "zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
         ("zori", "county"): "zori/County_zori_uc_sfrcondomfr_sm_month.csv",
         ("zori", "zip"): "zori/Zip_zori_uc_sfrcondomfr_sm_month.csv"}
RAW = "raw/zillow"

def fetch(measure, level):
    url = ZB + FILES[(measure, level)]; path = os.path.join(RAW, os.path.basename(FILES[(measure, level)]))
    os.makedirs(RAW, exist_ok=True)
    with requests.get(url, stream=True, timeout=1800) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for ch in r.iter_content(1 << 22): f.write(ch)
    return url, path, datetime.datetime.utcnow().isoformat(timespec="seconds")

def load_study(measure, level, counties):
    url, path, when = fetch(measure, level)
    d = pd.read_csv(path, dtype={"RegionName": str, "StateCodeFIPS": str, "MunicipalCodeFIPS": str})
    assert "RegionID" in d.columns, f"unexpected header in {path}"
    dates = [c for c in d.columns if re.fullmatch(r"\d{4}-\d{2}-\d{2}", c)]
    if level == "county":
        d["county_fips"] = d.MunicipalCodeFIPS.str.zfill(3)
        d = d[(d.StateCodeFIPS.str.zfill(2) == "06") & d.county_fips.isin(set(counties.county_fips))].copy()
        d = d.merge(counties[["county_fips", "county_name", "core9"]], on="county_fips", how="left", validate="1:1")
        assert (d.RegionName == d.county_name + " County").all(), "Zillow county name does not match FIPS-based name"
        ids = ["county_fips", "county_name", "core9"]
    else:
        nm = {n + " County": (f, n, c) for f, n, c in zip(counties.county_fips, counties.county_name, counties.core9)}
        d = d[(d.State == "CA") & d.CountyName.isin(nm)].copy()
        d["zip"] = d.RegionName.str.zfill(5)
        d["county_fips"] = d.CountyName.map(lambda s: nm[s][0]); d["county_name"] = d.CountyName.map(lambda s: nm[s][1]); d["core9"] = d.CountyName.map(lambda s: nm[s][2])
        ids = ["zip", "City", "county_fips", "county_name", "core9"]
    long = d.melt(id_vars=ids, value_vars=dates, var_name="month_end", value_name=measure)
    long["year"] = long.month_end.str[:4].astype(int)
    key = [c for c in ids if c != "City"] + ["year"]
    ann = long.groupby(key, as_index=False).agg(**{f"{measure}_mean": (measure, "mean"), f"{measure}_n_months": (measure, "count")})
    meta = {"measure": measure, "level": level, "url": url, "downloaded_utc": when, "first_month": dates[0], "last_month": dates[-1],
            "n_units": len(d), "n_month_cols": len(dates)}
    return long, ann, meta

if __name__ == "__main__":
    c = pd.read_csv("ref/study_counties.csv", dtype={"county_fips": str}); c["core9"] = c.core9.astype(str).str.lower().eq("true")
    metas = []
    for level in ("county", "zip"):
        anns = []
        for measure in ("zhvi", "zori"):
            long, ann, meta = load_study(measure, level, c); metas.append(meta); anns.append(ann)
            long.to_parquet(os.path.join(RAW, f"{measure}_{level}_monthly_study.parquet"), index=False)
        key = [k for k in anns[0].columns if not k.startswith("zhvi")]
        out = anns[0].merge(anns[1], on=key, how="outer")
        out.to_parquet(f"zillow_{level}_annual.parquet", index=False)
    pd.DataFrame(metas).to_csv(os.path.join(RAW, "zillow_download_log.csv"), index=False)
    print(pd.DataFrame(metas).to_string(index=False))
