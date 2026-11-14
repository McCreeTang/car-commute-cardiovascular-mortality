"""Acquire ACS PUMS California person files (1-year) from www2.census.gov and inventory their headers.
The 2020 1-year standard PUMS was not released (HTTP 404 at the standard path); it is recorded as a gap.

Usage: python acquire_pums.py            # download + header inventory
"""
import os, io, sys, csv, zipfile, datetime, requests, pandas as pd

PB = "https://www2.census.gov/programs-surveys/acs/data/pums/"
YEARS = [y for y in range(2010, 2025) if y != 2020]
RAW = "raw/pums"

def download(year, span="1-Year"):
    url = f"{PB}{year}/{span}/csv_pca.zip"
    path = os.path.join(RAW, f"pums_{year}_{span}_csv_pca.zip")
    os.makedirs(RAW, exist_ok=True)
    if not (os.path.exists(path) and zipfile.is_zipfile(path)):
        with requests.get(url, stream=True, timeout=1800) as r:
            if r.status_code != 200:
                return {"year": year, "span": span, "url": url, "status": r.status_code, "ok": False}
            with open(path, "wb") as f:
                for ch in r.iter_content(1 << 22): f.write(ch)
    ok = zipfile.is_zipfile(path)
    info = {"year": year, "span": span, "url": url, "status": 200, "ok": ok, "bytes": os.path.getsize(path), "path": path,
            "downloaded_utc": datetime.datetime.utcnow().isoformat(timespec="seconds")}
    if ok:
        zf = zipfile.ZipFile(path)
        csvs = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        info["members"] = ";".join(zf.namelist())
        with zf.open(csvs[0]) as f:
            info["header"] = f.readline().decode("latin-1").strip()
    return info

# ----------------------------------------------------------------------------------------------
# Extraction: persons aged 16+ living in study-area PUMAs, harmonized across 2010-2024
# ----------------------------------------------------------------------------------------------
import re
import numpy as np

PUMA_VINTAGE = lambda y: 2000 if y <= 2011 else (2010 if y <= 2021 else 2020)   # verified: 233 / 265 / 281 distinct CA PUMAs
BASE_COLS = ["SERIALNO", "SPORDER", "PUMA", "AGEP", "SEX", "JWMNP", "JWRIP", "JWDP", "JWAP", "POWPUMA", "POWSP", "WKHP",
             "ESR", "COW", "PINCP", "WAGP", "PERNP", "ADJINC", "RAC1P", "HISP", "SCHL", "PWGTP"]
# Means of transportation: JWTR (2010-2018) and JWTRNS (2019+) share codes 01, 02, 06-12 but codes 03-05 were
# redefined (pre-2019: 03 streetcar, 04 subway, 05 railroad; 2019+: 03 subway, 04 commuter rail, 05 light rail).
# mode_cat therefore pools 03-05 as "rail". Source: PUMS data dictionaries 2010-2014 (txt), 2017-2024 (csv).
MODE = {"02": "bus", "03": "rail", "04": "rail", "05": "rail", "06": "ferry", "07": "taxi", "08": "motorcycle",
        "09": "bicycle", "10": "walk", "11": "wfh", "12": "other"}

def extract_year(year, puma_map_csv="ref/puma_county_map.csv", outdir="raw/pums/extract", min_age=16):
    path = os.path.join(RAW, f"pums_{year}_1-Year_csv_pca.zip")
    zf = zipfile.ZipFile(path); name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
    with zf.open(name) as f:
        header = f.readline().decode("latin-1").strip().split(",")
    up = {c.upper(): c for c in header}
    mode_var = "JWTR" if "JWTR" in up else "JWTRNS"
    wk_var = "WKW" if "WKW" in up else "WKWN"
    reps = [up[f"PWGTP{i}"] for i in range(1, 81)]
    use = [up[c] for c in BASE_COLS + [mode_var, wk_var]] + reps
    d = pd.read_csv(zf.open(name), usecols=use, dtype=str, keep_default_na=False)
    d.columns = [c.upper() for c in d.columns]
    n_file = len(d)
    # every field is text; whitespace-only means not applicable (the 2014 file uses ' ' where others use '')
    for c in d.columns: d[c] = d[c].str.strip()
    v = PUMA_VINTAGE(year)
    pmap = pd.read_csv(puma_map_csv, dtype={"puma": str, "county_fips": str}); pmap = pmap[pmap.puma_vintage == v]
    d["PUMA"] = d.PUMA.str.zfill(5)
    seen = set(d.PUMA)
    d = d.merge(pmap[["puma", "county_fips", "county_name", "core9", "puma_mixed_outside"]], left_on="PUMA", right_on="puma", how="inner").drop(columns="puma")
    n_study = len(d)
    num = lambda s: pd.to_numeric(s.replace("", np.nan), errors="raise")
    out = pd.DataFrame({"year": np.int16(year), "puma_vintage": np.int16(v), "puma": d.PUMA, "county_fips": d.county_fips,
                        "county_name": d.county_name, "core9": d.core9.astype(bool), "puma_mixed_outside": d.puma_mixed_outside.astype(bool),
                        "serialno": d.SERIALNO, "sporder": num(d.SPORDER).astype("int16")})
    out["agep"] = num(d.AGEP).astype("int16"); out["sex"] = num(d.SEX).astype("int8")
    for c in ("ESR", "COW", "SCHL", "RAC1P", "HISP", "JWRIP", "JWDP", "JWAP"): out[c.lower()] = num(d[c]).astype("Int16")
    out["wkhp"] = num(d.WKHP).astype("Int16"); out["wk_raw"] = num(d[wk_var]).astype("Int16"); out["wk_var"] = wk_var
    out["jwmnp"] = num(d.JWMNP).astype("Int16")
    out["jwtr_raw"] = d[mode_var].replace("", pd.NA); out["jwtr_scheme"] = mode_var
    car = d[mode_var] == "01"; occ = num(d.JWRIP)
    mode = d[mode_var].map(MODE)
    mode = mode.mask(car & (occ == 1), "car_alone").mask(car & (occ >= 2), "carpool").mask(car & occ.isna(), "car_unknown_occupancy")
    out["mode_cat"] = mode
    out["worker_at_work"] = d[mode_var] != ""            # universe of the journey-to-work items
    out["wfh"] = d[mode_var] == "11"
    out["commuter"] = out.jwmnp.notna()
    out["powpuma"] = d.POWPUMA.replace("", pd.NA); out["powsp"] = d.POWSP.replace("", pd.NA)
    for c in ("PINCP", "WAGP", "PERNP"): out[c.lower()] = num(d[c]).astype("Int32")
    out["adjinc"] = num(d.ADJINC).astype("float64") / 1e6
    w = d[["PWGTP"] + [f"PWGTP{i}" for i in range(1, 81)]].apply(pd.to_numeric, errors="raise")
    wmin, wmax = int(w.values.min()), int(w.values.max())
    for c in w.columns: out[c.lower()] = w[c].astype("int32").values
    n_all_ages = len(out); out = out[out.agep >= min_age].reset_index(drop=True)
    qc = {"year": year, "puma_vintage": v, "mode_var": mode_var, "wk_var": wk_var, "rows_file": n_file, "rows_study_all_ages": n_study,
          "rows_study_16plus": len(out), "pumas_in_map": len(pmap), "map_pumas_missing_from_data": len(set(pmap.puma) - seen),
          "dup_person_keys": int(out.duplicated(["serialno", "sporder"]).sum()),
          "pop16plus_wt": int(out.pwgtp.sum()), "workers_wt": int(out.pwgtp[out.worker_at_work].sum()),
          "commuters_n": int(out.commuter.sum()), "commuters_wt": int(out.pwgtp[out.commuter].sum()), "wfh_wt": int(out.pwgtp[out.wfh].sum()),
          # journey-to-work logic: travel time should exist exactly for workers who did not work from home
          "commuter_but_not_worker_or_wfh": int((out.commuter & (~out.worker_at_work | out.wfh)).sum()),
          "worker_not_wfh_without_time": int((out.worker_at_work & ~out.wfh & ~out.commuter).sum()),
          "car_unknown_occupancy": int((out.mode_cat == "car_unknown_occupancy").sum()),
          "mode_unmapped": int((out.worker_at_work & out.mode_cat.isna()).sum()),
          "jwmnp_min": int(out.jwmnp.min()), "jwmnp_max": int(out.jwmnp.max()), "weight_min": wmin, "weight_max": wmax,
          "mixed_puma_rows": int(out.puma_mixed_outside.sum())}
    os.makedirs(outdir, exist_ok=True)
    out.to_parquet(os.path.join(outdir, f"pums_study_{year}.parquet"), index=False, compression="zstd")
    qc["parquet_MB"] = round(os.path.getsize(os.path.join(outdir, f"pums_study_{year}.parquet")) / 1e6, 1)
    return qc

if __name__ == "__main__":
    log = [download(y) for y in YEARS]
    pd.DataFrame(log).to_csv(os.path.join(RAW, "pums_download_log.csv"), index=False)
    for i in log: print({k: v for k, v in i.items() if k not in ("header",)}, flush=True)
    # extraction: persons 16+ in study-area PUMAs, all 80 replicate weights kept (negative replicate values are
    # published as-is and must not be clipped); requires ref/puma_county_map.csv
    qcs = [extract_year(y) for y in YEARS]
    pd.DataFrame(qcs).to_csv(os.path.join(RAW, "pums_extract_qc.csv"), index=False)
    allp = pd.concat([pd.read_parquet(os.path.join(RAW, "extract", f"pums_study_{y}.parquet")) for y in YEARS], ignore_index=True)
    assert not allp.duplicated(["year", "serialno", "sporder"]).any()
    allp.to_parquet("pums_commuters.parquet", index=False, compression="zstd")
    print("pums_commuters.parquet rows", len(allp), flush=True)
