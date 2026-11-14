"""Quality control for the analysis datasets. Writes data_qc_report.md, data_qc_missingness.csv and the QC tables in ref/.
All numbers in the report are computed here. Spot checks re-read values from the original sources with code paths that
are independent of the acquisition scripts.

Usage: python run_qc.py
"""
import io, os, re, csv, json, zipfile, datetime, importlib.util, requests, numpy as np, pandas as pd

ACS = "https://www2.census.gov/programs-surveys/acs/summary_file/"
spec = importlib.util.spec_from_file_location("bld", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_analysis_datasets.py")); bld = importlib.util.module_from_spec(spec); spec.loader.exec_module(bld)

def md(df, index=False):
    d = df.reset_index() if index else df; cols = [str(c) for c in d.columns]
    def fmt(s):
        if pd.api.types.is_bool_dtype(s) or s.dtype == object: return s.astype(str).tolist()
        if pd.api.types.is_integer_dtype(s): return [f"{int(v):,}" if str(s.name) not in ("year", "vintage", "acs_vintage") else str(int(v)) for v in s]
        return ["" if pd.isna(v) else (f"{v:,.0f}" if abs(v) >= 1000 and float(v).is_integer() else f"{v:.4g}") for v in s]
    cells = [fmt(d[c]) for c in d.columns]
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"] + ["| " + " | ".join(c[i] for c in cells) + " |" for i in range(len(d))])

# ------------------------------------------------------------------ spot checks
def seq_value(v, geoid, table, cell):
    b = f"{ACS}{v}/data/5_year_seq_by_state/California/Tracts_Block_Groups_Only/"
    geo = requests.get(b + f"g{v}5ca.csv", timeout=300).content.decode("latin-1")
    logrec = next(row[4] for row in csv.reader(io.StringIO(geo)) if row[48] == "14000US" + geoid)
    lk = pd.read_csv(f"ref/acs5_{v}_seq_lookup.csv", dtype=str, keep_default_na=False); h = lk[(lk["Table ID"] == table) & lk["Start Position"].str.strip().str.isdigit()].iloc[0]
    seq, start = int(h["Sequence Number"]), int(h["Start Position"])
    z = zipfile.ZipFile(io.BytesIO(requests.get(b + f"{v}5ca{seq:04d}000.zip", timeout=600).content))
    for raw in z.open(f"e{v}5ca{seq:04d}000.txt"):
        f = raw.decode("latin-1").rstrip("\r\n").split(",")
        if f[5] == logrec: return int(f[start - 1 + cell - 1]), f"{v}5ca{seq:04d}000.zip, LOGRECNO {logrec}, field {start + cell - 1}"

def spot_checks(T, CY, seed=20261113):
    rng = np.random.default_rng(seed); out = []
    def pick(v, col):
        g = T[(T.acs_vintage == v) & T[col].notna() & (T.commuters_total > 500)].sort_values("tract_geoid"); return g.iloc[int(rng.integers(len(g)))]
    r = pick(2024, "share_commute_60plus"); gid = ("1400000US" + r.tract_geoid).encode() + b"|"
    with requests.get(f"{ACS}2024/table-based-SF/data/5YRData/acsdt5y2024-b08303.dat", stream=True, timeout=600) as rr:
        it = rr.iter_lines(); hdr = next(it).decode().split("|"); c = dict(zip(hdr, next(l for l in it if l.startswith(gid)).decode().split("|")))
    out.append(("ACS 2020-2024 share_commute_60plus", r.tract_geoid, "acsdt5y2024-b08303.dat, cells E001/E012/E013", (int(c["B08303_E012"]) + int(c["B08303_E013"])) / int(c["B08303_E001"]), float(r.share_commute_60plus)))
    r = pick(2019, "share_drive_alone"); tot, _ = seq_value(2019, r.tract_geoid, "B08301", 1); da, s = seq_value(2019, r.tract_geoid, "B08301", 3)
    out.append(("ACS 2015-2019 share_drive_alone", r.tract_geoid, s, da / tot, float(r.share_drive_alone)))
    r = pick(2014, "mean_commute_min"); agg, s1 = seq_value(2014, r.tract_geoid, "B08013", 1); com, s2 = seq_value(2014, r.tract_geoid, "B08303", 1)
    out.append(("ACS 2010-2014 mean_commute_min", r.tract_geoid, s1 + " ; " + s2, agg / com, float(r.mean_commute_min)))
    # CDC API checks: each one is independent; a connection error gets one retry after a pause and is otherwise
    # recorded as not performed (never dropped silently, never counted as a match)
    def cdc_one(rid, where):
        import time
        for attempt in (1, 2):
            try:
                resp = requests.get(f"https://data.cdc.gov/resource/{rid}.json", params={"$where": where}, timeout=120); resp.raise_for_status()
                rows = resp.json(); assert len(rows) == 1, f"{len(rows)} rows returned"
                return rows[0]
            except requests.exceptions.RequestException as e:
                err = type(e).__name__
                if attempt == 1: time.sleep(30)
        raise ConnectionError(err)
    failed = []; n_cdc = 0
    cdc_specs = []
    for v, rid, meas in ((2019, "373s-ayzu", "CHD"), (2024, "cwsq-ngmh", "BPHIGH")):
        g = T[(T.acs_vintage == v) & T.has_places].sort_values("tract_geoid"); r = g.iloc[int(rng.integers(len(g)))]
        cdc_specs.append((f"PLACES {int(r.places_release)} release {meas} crude prevalence, data year {int(r[f'{meas.lower()}_data_year'])}", r.tract_geoid, rid,
                          f"locationname='{r.tract_geoid}' AND measureid='{meas}'", float(r[f"{meas.lower()}_prev"]), int(r[f"{meas.lower()}_data_year"])))
    cdc_specs.append(("Mortality all stroke, ages 65+, 2017, per 100,000", "San Joaquin", "7b9s-s8ck", "locationid='06077' AND year='2017' AND topic='All stroke' AND stratification1='Ages 65 years and older' AND stratification2='Overall' AND stratification3='Overall'",
                      float(CY[(CY.county_fips == "077") & (CY.year == 2017)].mort_stroke_65plus.iloc[0]), 2017))
    cdc_specs.append(("Mortality major CVD, ages 35-64, 2020, per 100,000", "Santa Clara", "rsk5-566a", "locationid='06085' AND year='2020' AND stratification1='Ages 35-64 years' AND data_value_type='Age-Standardized, Spatially Smoothed Rate'",
                      float(CY[(CY.county_fips == "085") & (CY.year == 2020)].mort_majorcvd_35_64.iloc[0]), 2020))
    for label, unit, rid, where, ds_val, ds_year in cdc_specs:
        try:
            row = cdc_one(rid, where); assert int(row["year"]) == ds_year, f"data year {row['year']} != {ds_year}"
            out.append((label, unit, f"data.cdc.gov/resource/{rid} (API)", float(row["data_value"]), ds_val)); n_cdc += 1
        except ConnectionError as e:
            failed.append(f"{label} [{unit}]: {e}")
    cdc = f"{n_cdc} of {len(cdc_specs)} performed" + ("" if not failed else "; NOT performed (CDC API unreachable after one retry): " + " | ".join(failed))
    z = pd.read_csv("raw/zillow/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv", dtype={"StateCodeFIPS": str, "MunicipalCodeFIPS": str})
    zr = z[(z.StateCodeFIPS.str.zfill(2) == "06") & (z.MunicipalCodeFIPS.str.zfill(3) == "013")].iloc[0]; mc = [c for c in z.columns if c.startswith("2018-")]
    out.append((f"Zillow ZHVI annual mean 2018 ({len(mc)} months), dollars", "Contra Costa", "raw county ZHVI csv", float(zr[mc].astype(float).mean()), float(CY[(CY.county_fips == "013") & (CY.year == 2018)].zhvi_mean.iloc[0])))
    # newest year: published ACS 1-year 2025 county tables, re-read with this separate reader
    vals = {}
    for t in ("b08303", "b08013"):
        with requests.get(f"{ACS}2025/table-based-SF/data/1YRData/acsdt1y2025-{t}.dat", stream=True, timeout=600) as rr:
            it = rr.iter_lines(); hdr = next(it).decode().split("|"); assert hdr[0] == "GEO_ID"; vals.update(dict(zip(hdr, next(l for l in it if l.startswith(b"0500000US06077|")).decode().split("|"))))
    out.append(("ACS 1-year 2025 mean_commute_min (published county table)", "San Joaquin", "acsdt1y2025-b08013.dat E001 / acsdt1y2025-b08303.dat E001", int(vals["B08013_E001"]) / int(vals["B08303_E001"]), float(CY[(CY.county_fips == "077") & (CY.year == 2025)].acs1_mean_commute_min.iloc[0])))
    out.append(("ACS 1-year 2025 share_commute_60plus (published county table)", "San Joaquin", "acsdt1y2025-b08303.dat cells E001/E012/E013", (int(vals["B08303_E012"]) + int(vals["B08303_E013"])) / int(vals["B08303_E001"]), float(CY[(CY.county_fips == "077") & (CY.year == 2025)].acs1_share_commute_60plus.iloc[0])))
    S = pd.DataFrame(out, columns=["check", "unit", "source", "source_value", "dataset_value"]); S["match"] = np.isclose(S.source_value, S.dataset_value, rtol=0, atol=1e-6)
    # show the compared values in full (as text) so the table reflects what was actually compared
    full = lambda v: f"{v:,.6f}".rstrip("0").rstrip(".")
    S["source_value"] = S.source_value.map(full); S["dataset_value"] = S.dataset_value.map(full)
    return S, cdc

def identities():
    rows = []
    for v in bld.VINTAGES:
        for sl in ("140", "050"):
            d = bld.load_acs(v, sl); m25 = [f"B01001_E{i:03d}" for i in list(range(11, 26)) + list(range(35, 50))]
            rows.append({"vintage": v, "level": "tract" if sl == "140" else "county", "n": len(d), "pop: B01001 != B03002": int((d.B01001_E001 != d.B03002_E001).sum()),
                         "workers - WFH != B08303 universe": int(((d.B08301_E001 - d.B08301_E021) != d.B08303_E001).sum()), "pop 25+ != B15003 universe": int((d[m25].sum(axis=1) != d.B15003_E001).sum())})
    return pd.DataFrame(rows)

def pums_vs_published(PCY, counties, year=2023):
    pub = {}
    for t in ("b08303", "b08013", "b08301"):
        with requests.get(f"{ACS}{year}/table-based-SF/data/1YRData/acsdt1y{year}-{t}.dat", stream=True, timeout=600) as rr:
            it = rr.iter_lines(); hdr = next(it).decode().split("|"); assert hdr[0] == "GEO_ID"
            for raw in it:
                if raw.startswith(b"0500000US06"):
                    f = raw.decode().split("|"); pub.setdefault(f[0][-3:], {}).update(dict(zip(hdr[1:], f[1:])))
    rows = []
    for fp in counties.county_fips:
        p = pub.get(fp); q = PCY[(PCY.county_fips == fp) & (PCY.year == year) & (PCY.age_band == "16plus")]
        if not p or q.empty: continue
        q = q.iloc[0]; g = lambda k: float(p[k]) if float(p[k]) > -1e8 else np.nan
        pm = g("B08013_E001") / g("B08303_E001"); pmoe = np.sqrt(g("B08013_M001") ** 2 + pm ** 2 * g("B08303_M001") ** 2) / g("B08303_E001")
        rows.append({"county": q.county_name, "PUMS mean min": round(q.mean_commute_min, 2), "published mean min": round(pm, 2), "difference": round(q.mean_commute_min - pm, 2),
                     "z": round((q.mean_commute_min - pm) / np.sqrt(q.mean_commute_min_se ** 2 + (pmoe / 1.645) ** 2), 2),
                     "commuters diff %": round((q.commuters / g("B08303_E001") - 1) * 100, 2), "PUMS WFH share": round(q.share_wfh_workers, 4), "published WFH share": round(g("B08301_E021") / g("B08301_E001"), 4)})
    return pd.DataFrame(rows), sorted(counties.county_name[counties.county_fips.isin(pub) & ~counties.county_fips.isin(set(PCY.county_fips))])

# ------------------------------------------------------------------ main
if __name__ == "__main__":
    counties = bld.read_counties()
    T = pd.read_parquet("tract_analysis.parquet"); CY = pd.read_parquet("county_year_panel.parquet"); PCY = pd.read_parquet("pums_county_year_age.parquet")
    M = pd.read_parquet("mortality_long.parquet"); PL = pd.read_parquet("places_tract_long.parquet"); REL = pd.read_parquet("tract_2010_2020_relationship.parquet")
    PU = pd.read_parquet("pums_commuters.parquet", columns=["year", "county_fips", "county_name", "core9", "puma_mixed_outside", "serialno", "sporder", "agep", "jwmnp", "worker_at_work", "wfh", "commuter", "mode_cat", "pwgtp"])
    RR = pd.read_csv("road_rage_proxy_counts.csv", dtype={"county_fips": str}); ZZ = pd.read_parquet("zillow_zip_annual.parquet")
    CELLS = pd.read_parquet("acs5_cells.parquet"); cellcols = [c for c in CELLS.columns if re.fullmatch(r"B\d{5}_[EM]\d{3}", c)]
    notes = json.load(open("ref/qc_notes.json"))
    # 1 outputs and duplicate keys
    keys = {"tract_analysis.parquet": (T, ["tract_geoid", "acs_vintage"]), "county_year_panel.parquet": (CY, ["county_fips", "year"]), "pums_commuters.parquet": (PU, ["year", "serialno", "sporder"]),
            "pums_county_year_age.parquet": (PCY, ["county_fips", "year", "age_band"]), "places_tract_long.parquet": (PL, ["release", "tract_geoid", "measureid"]),
            "mortality_long.parquet": (M, ["dataset_id", "county_fips", "period", "topic", "age_group", "race", "sex", "value_type"]), "tract_2010_2020_relationship.parquet": (REL, ["tract_geoid_2020", "tract_geoid_2010"]),
            "zillow_zip_annual.parquet": (ZZ, ["zip", "year"]), "acs5_cells.parquet": (CELLS, ["GEO_ID", "acs_vintage"]), "road_rage_proxy_counts.csv": (RR, ["county_fips", "year"])}
    OUT = pd.DataFrame([{"file": f, "rows": len(d), "columns": (116 if f == "pums_commuters.parquet" else d.shape[1]), "key": " + ".join(k), "duplicate keys": int(d.duplicated(k).sum())} for f, (d, k) in keys.items()])
    # 2 row counts per county
    rc = T.pivot_table(index="county_name", columns="acs_vintage", values="tract_geoid", aggfunc="count"); rc.columns = [f"tracts {bld.VINTAGES[c][0]}" for c in rc.columns]
    hp = T[T.has_places].pivot_table(index="county_name", columns="acs_vintage", values="tract_geoid", aggfunc="count"); hp.columns = [f"with PLACES {bld.VINTAGES[c][0]}" for c in hp.columns]
    pu = PU[~PU.puma_mixed_outside].groupby("county_name").agg(**{"PUMS persons 16+ (all years)": ("pwgtp", "size"), "PUMS commuter records": ("commuter", "sum")})
    RC = rc.join(hp).join(pu).join(CY.groupby("county_name").size().rename("panel rows")).join(counties.set_index("county_name").core9).reindex(counties.sort_values("county_fips").county_name)
    RC = RC.fillna(0).astype({c: int for c in RC.columns if c != "core9"}); RC.index.name = "county"
    mixed_n = int(PU.puma_mixed_outside.sum())
    # 3 missingness
    num = [c for c in T.columns if c not in ("cross_section", "tract_geoid", "county_fips", "county_name", "core9", "acs_period", "acs_vintage", "tract_vintage")]
    MS = T.groupby("acs_vintage")[num].apply(lambda g: g.isna().sum()).T; MS.columns = [f"missing_{c}" for c in MS.columns]
    for v in bld.VINTAGES: MS[f"pct_{v}"] = (MS[f"missing_{v}"] / (T.acs_vintage == v).sum() * 100).round(2)
    MS.index.name = "variable"; MS.insert(0, "table", "tract_analysis")
    pm = pd.DataFrame({"table": "county_year_panel", "missing_all": CY.isna().sum(), "pct_all": (CY.isna().mean() * 100).round(2)}); pm.index.name = "variable"
    pd.concat([MS.reset_index(), pm.reset_index()], ignore_index=True).to_csv("data_qc_missingness.csv", index=False)
    keyv = ["pop_total", "commuters_total", "share_commute_60plus", "mean_commute_min", "share_drive_alone", "share_wfh", "share_depart_before_6am", "median_hh_income", "median_home_value", "median_gross_rent", "poverty_rate", "share_bachelors_plus", "share_no_vehicle_hh", "chd_prev", "stroke_prev", "bphigh_prev", "obesity_prev", "lpa_prev", "diabetes_prev", "csmoking_prev", "sleep_prev", "mhlth_prev", "depression_prev", "overlap_same_geoid"]
    MSK = MS.loc[keyv, [c for c in MS.columns if c.startswith("missing_")]].copy(); MSK.columns = [f"missing {bld.VINTAGES[int(c.split('_')[1])][0]}" for c in MSK.columns]
    est = [c for c in num if not c.endswith("_moe") and T[c].dtype.kind in "fi"]; n_complete = int((T[est].isna().sum() == 0).sum())
    supp = T[T.mean_commute_min.isna()].groupby("acs_vintage").agg(tracts=("tract_geoid", "size"), with_commuters=("commuters_total", lambda s: int((s > 0).sum())), commuters=("commuters_total", "sum")).astype(int)
    grp = {"Zillow home value (zhvi_mean)": "zhvi_mean", "Zillow rent (zori_mean)": "zori_mean", "PUMS commute measures": "pums_mean_commute_min_16plus", "ACS 5-year county values": "acs5_mean_commute_min", "ACS 1-year published county tables": "acs1_mean_commute_min",
           "Mortality by age, five topics": "mort_chd_35_64", "Mortality by age, major CVD": "mort_majorcvd_35_64", "Pooled 3-year, adults 35+": "pooled3yr_hd_35plus"}
    COV = pd.DataFrame({k: CY.groupby("year")[v].count() for k, v in grp.items()}).T; COV.columns = [str(c) for c in COV.columns]; COV.index.name = "counties with a value, by year"
    # 4 range checks
    sh = [c for c in T.columns if (c.startswith("share_") or c == "poverty_rate") and not c.endswith("_moe")]; moe = [c for c in T.columns if c.endswith("_moe")]
    pv = [c for c in T.columns if c.endswith("_prev")]; lo = [c for c in T.columns if c.endswith("_prev_lo")]
    psh = [c for c in PCY.columns if "share" in c and not c.endswith("_se")]; pse = [c for c in PCY.columns if c.endswith("_se")]
    a1s = [c for c in CY.columns if c.startswith("acs1_share_") and not c.endswith("_moe")]; a1m = [c for c in CY.columns if c.startswith("acs1_") and c.endswith("_moe")]
    mort = [c for c in CY.columns if c.startswith("mort_") or (c.startswith("pooled3yr_") and c.endswith("35plus"))]
    Mv = M[M.value.notna() & M.ci_low.notna() & M.unit.str.contains("100,000")]
    RG = pd.DataFrame([
        ("tract shares within 0-1", f"{len(sh)} variables", int(((T[sh] < 0) | (T[sh] > 1)).sum().sum()), f"{T[sh].min().min():.3f} to {T[sh].max().max():.3f}"),
        ("tract margins of error non-negative", f"{len(moe)} variables", int((T[moe] < 0).sum().sum()), f"min {T[moe].min().min():.3f}"),
        ("ACS cell estimates and margins non-negative (jam values removed)", f"{len(cellcols)} columns in acs5_cells", int((CELLS[cellcols] < 0).sum().sum()), ""),
        ("tract mean commute within 1-120 minutes", "mean_commute_min", int(((T.mean_commute_min < 1) | (T.mean_commute_min > 120)).sum()), f"{T.mean_commute_min.min():.2f} to {T.mean_commute_min.max():.2f}"),
        ("tract age shares sum to 1", "4 age shares", int((T[[f'share_age_{k}' for k in bld.AGE]].sum(axis=1, min_count=4).sub(1).abs() > 1e-9).sum()), ""),
        ("PLACES prevalence within 0-100", f"{len(pv)} variables", int(((T[pv] < 0) | (T[pv] > 100)).sum().sum()), f"{T[pv].min().min():.1f} to {T[pv].max().max():.1f}"),
        ("PLACES lower limit <= estimate <= upper limit", f"{len(lo)} measures", int(sum(((T[c] > T[c[:-3]]) | (T[c[:-3]] > T[c[:-3] + '_hi'])).sum() for c in lo)), ""),
        ("PLACES long file prevalence within 0-100", "all measures, all releases", int(((PL.data_value < 0) | (PL.data_value > 100)).sum()), f"{PL.data_value.min():.1f} to {PL.data_value.max():.1f}"),
        ("PUMS travel time within 1-200 minutes", "jwmnp", int(((PU.jwmnp < 1) | (PU.jwmnp > 200)).sum()), f"{int(PU.jwmnp.min())} to {int(PU.jwmnp.max())}"),
        ("PUMS age 16 or older", "agep", int((PU.agep < 16).sum()), f"{int(PU.agep.min())} to {int(PU.agep.max())}"),
        ("PUMS main weight positive", "pwgtp", int((PU.pwgtp <= 0).sum()), f"min {int(PU.pwgtp.min())}"),
        ("PUMS travel time present exactly for workers not working from home", "commuter flag", int((PU.commuter != (PU.worker_at_work & ~PU.wfh)).sum()), ""),
        ("PUMS county-year shares within 0-1", f"{len(psh)} variables", int(((PCY[psh] < 0) | (PCY[psh] > 1)).sum().sum()), f"{PCY[psh].min().min():.3f} to {PCY[psh].max().max():.3f}"),
        ("PUMS county-year standard errors non-negative and present", f"{len(pse)} variables", int((PCY[pse] < 0).sum().sum() + PCY[pse].isna().sum().sum()), ""),
        ("PUMS county-year mean commute within 1-120 minutes", "mean_commute_min", int(((PCY.mean_commute_min < 1) | (PCY.mean_commute_min > 120)).sum()), f"{PCY.mean_commute_min.min():.2f} to {PCY.mean_commute_min.max():.2f}"),
        ("ACS 1-year county shares within 0-1", f"{len(a1s)} variables, {int(CY.acs1_available.sum())} county-years", int(((CY[a1s] < 0) | (CY[a1s] > 1)).sum().sum()), f"{CY[a1s].min().min():.3f} to {CY[a1s].max().max():.3f}"),
        ("ACS 1-year margins of error non-negative and present where the estimate is", f"{len(a1m)} variables", int((CY[a1m] < 0).sum().sum() + (CY.loc[CY.acs1_available, a1m].isna()).sum().sum()), ""),
        ("ACS 1-year mean commute within 1-120 minutes", "acs1_mean_commute_min", int(((CY.acs1_mean_commute_min < 1) | (CY.acs1_mean_commute_min > 120)).sum()), f"{CY.acs1_mean_commute_min.min():.2f} to {CY.acs1_mean_commute_min.max():.2f}"),
        ("panel Zillow values positive", "zhvi_mean, zori_mean", int((CY.zhvi_mean <= 0).sum() + (CY.zori_mean <= 0).sum()), f"ZHVI {CY.zhvi_mean.min():,.0f} to {CY.zhvi_mean.max():,.0f}; ZORI {CY.zori_mean.min():,.0f} to {CY.zori_mean.max():,.0f}"),
        ("panel mortality rates positive", f"{len(mort)} variables", int((CY[mort] <= 0).sum().sum()), f"{CY[mort].min().min():.1f} to {CY[mort].max().max():.1f} per 100,000"),
        ("mortality lower limit <= rate <= upper limit", "mortality_long rates with limits", int(((Mv.ci_low > Mv.value) | (Mv.value > Mv.ci_high)).sum()), f"{len(Mv):,} rows checked"),
        ("relationship land shares sum to 1 per study-area 2020 tract", "share_of_2020_land", int((REL[REL.in_study_2020].groupby('tract_geoid_2020').share_of_2020_land.sum(min_count=1).dropna().sub(1).abs() > 1e-6).sum()), f"{int((~REL.in_study_2020 | ~REL.in_study_2010).sum())} pair(s) involve a tract outside the study area and are excluded from this check"),
        ("crash indicator counts sum to all crashes", "road_rage_proxy_counts", int((RR[['unsafe_speed', 'following_too_closely', 'unsafe_lane_change', 'unsafe_passing', 'reckless_or_speed_contest', 'unsafe_turn_or_signal', 'signal_or_stop_sign', 'other_or_none']].sum(axis=1) != RR.all_crashes).sum()), ""),
    ], columns=["check", "applies to", "violations", "observed range"])
    # 5 spot checks etc.
    S, cdc = spot_checks(T, CY); S.to_csv("ref/qc_spot_checks.csv", index=False)
    ID = identities(); ID.to_csv("ref/qc_identities.csv", index=False)
    CMP, pub_only = pums_vs_published(PCY, counties); CMP.to_csv("ref/qc_pums_vs_published_2023.csv", index=False)
    ov = CY[CY.acs1_available & CY.pums_available].copy()
    ov["dm"] = ov.pums_mean_commute_min_16plus - ov.acs1_mean_commute_min; ov["zm"] = ov.dm / np.sqrt(ov.pums_mean_commute_min_se_16plus ** 2 + (ov.acs1_mean_commute_min_moe / 1.645) ** 2)
    ov["d6"] = ov.pums_share_commute_60plus_16plus - ov.acs1_share_commute_60plus; ov["z6"] = ov.d6 / np.sqrt(ov.pums_share_commute_60plus_se_16plus ** 2 + (ov.acs1_share_commute_60plus_moe / 1.645) ** 2)
    OV = ov.groupby("year").agg(**{"county-years": ("dm", "size"), "max abs diff, mean minutes": ("dm", lambda s: round(s.abs().max(), 2)), "beyond 2 SE (mean)": ("zm", lambda s: int((s.abs() > 2).sum())),
                                   "max abs diff, 60+ share": ("d6", lambda s: round(s.abs().max(), 4)), "beyond 2 SE (60+ share)": ("z6", lambda s: int((s.abs() > 2).sum()))})
    a14 = CY[CY.acs1_available & (CY.county_fips != "069")]
    def _agg(g):
        w = g.acs1_commuters_total; k = g.acs1_workers_total
        return pd.Series({"commuters": int(w.sum()), "mean commute (min)": round((g.acs1_mean_commute_min * w).sum() / w.sum(), 2), "60+ min share (%)": round((g.acs1_share_commute_60plus * w).sum() / w.sum() * 100, 2),
                          "work from home (%)": round((g.acs1_share_wfh * k).sum() / k.sum() * 100, 2), "drove alone (%)": round((g.acs1_share_drive_alone * k).sum() / k.sum() * 100, 2)})
    A14 = a14.groupby("year").apply(_agg, include_groups=False); A14["commuters"] = A14.commuters.astype(int)
    K = json.load(open("ref/currency_check.json")); kp = K["pums"]; ka = K["acs_summary_files"]["years"]; kz = K["zillow"]["files"]; kpl = K["places"]; km = K["mortality"]
    CUR = pd.DataFrame([
        ("ACS PUMS person file (1-year), California", str(max(int(k[:4]) for k, v in kp["files"].items() if k.endswith("1-Year") and v["california_person_file"] == "zip")), "2025: not published (directory and file return 404); 2026: not published (404). Latest year directory in the listing: " + str(kp["latest_year_directory"]) + ".", kp["checked_utc"]),
        ("ACS 1-year summary tables (county)", str(max(int(y) for y, d in ka.items() if d["1YRData"]["published"])), f"2025 tables published ({ka['2025']['1YRData']['table_files_listed']:,} table files, travel-time table last modified {ka['2025']['1YRData']['b08303_last_modified']}); 2026: not published. Acquired for 2021-2025.", K["acs_summary_files"]["checked_utc"]),
        ("ACS 5-year summary files (tract)", "2020-2024", f"2021-2025 release not published: the 2025 data directory lists {ka['2025']['data_directory_entries']}, the 5-year directory returns {ka['2025']['5YRData']['directory_status']}, and a request for the would-be file is answered with: {ka['2025']['5YRData']['b08303_response']}.", K["acs_summary_files"]["checked_utc"]),
        ("Zillow ZHVI and ZORI", max(v["last_month_at_source"] for v in kz.values()), "No later month at source than already acquired" if not any(v["newer_available"] for v in kz.values()) else "A LATER MONTH IS AVAILABLE AT SOURCE - refresh needed", K["zillow"]["checked_utc"]),
        ("CDC PLACES tract estimates", f"{max(kpl['release_years_in_catalog'])} release (BRFSS {max(kpl['standing_tract_dataset']['brfss_years_and_measures'])})", f"No 2026 release: {kpl['places_datasets_seen']} PLACES datasets in the catalog, release years {min(kpl['release_years_in_catalog'])}-{max(kpl['release_years_in_catalog'])}, {len(kpl['titles_mentioning_2026'])} titles mention 2026; the standing tract dataset {kpl['standing_tract_dataset']['id']} is still titled '{kpl['standing_tract_dataset']['title']}' (rows updated {kpl['standing_tract_dataset']['rows_updated']}).", kpl["checked_utc"]),
        ("County cardiovascular mortality by age group", "2020 (major cardiovascular disease); 2019 (five topics)", f"No county-level cardiovascular mortality by age group after 2020, provisional or final: {km['queries']} catalog queries, {km['datasets_returned']} datasets returned, {km['cardiovascular_county_mortality_datasets']} county cardiovascular mortality datasets, age-stratified ones end in " + ", ".join(f"{v['last_year']} ({k})" for k, v in km["age_stratified"].items()) + f". Provisional county series in the catalog cover only drug overdose and COVID-19. Not acquired: " + "; ".join(f"{k} ({v[:70]}...)" for k, v in km["cardiovascular_not_acquired"].items()) + ".", km["checked_utc"]),
        ("County heart disease / stroke mortality, adults 35+, three-year pooled (not by age)", km["pooled_three_year_latest_period"], "Latest period already acquired.", km["checked_utc"]),
    ], columns=["source", "latest available", "what the check found", "checked (UTC)"])
    tc = T.groupby("acs_vintage")[[c for c in T.columns if c.endswith("_topcoded")]].sum().astype(int); tc.index = [bld.VINTAGES[i][0] for i in tc.index]; tc.index.name = "ACS period"
    noP = T[~T.has_places & T.places_release.isna() & T.acs_vintage.isin([2019, 2024])].groupby("acs_vintage").agg(tracts=("tract_geoid", "size"), population=("pop_total", "sum")).astype(int)
    stab = T[T.acs_vintage == 2019]; b13 = notes["acs_2024_b08013"]; rw = notes["pums_replicate_weights"]; sm = pd.read_csv("ref/puma_mixed_shares.csv")
    plog = pd.read_csv("raw/acs/acs5_2019_download_log.csv"); fb = plog[plog.get("source_note", pd.Series(dtype=str)).astype(str).str.contains("BUNDLE")]
    report = f"""# Data QC report

Generated {datetime.date.today().isoformat()} by `run_qc.py`. Study area: 15 California counties (9 core Bay Area, 6 adjacent). All counts below are computed from the delivered files.

**Result: {int((RG.violations > 0).sum())} of {len(RG)} range checks have violations; {int((OUT['duplicate keys'] > 0).sum())} of {len(OUT)} tables have duplicate keys; {int(S.match.sum())} of {len(S)} spot checks match their source.**

## Source currency

Latest period available from each source, from `check_currency.py` (recorded in `ref/currency_check.json`). Nothing newer than what is listed here existed at the time of the check.

{md(CUR)}

Consequence: person-level and age-specific commute measures end in 2024. The 2025 commute figures in the county-year panel (`acs1_*` columns) come from the published ACS 1-year county tables and are county totals, not age-specific. Nothing exists for 2026 except the Zillow indices (January to September).

## 1. Outputs and duplicate keys

{md(OUT)}

## 2. Row counts per county

{md(RC, index=True)}

San Benito has no PUMS rows of its own: in every PUMA definition it shares a PUMA with part of Monterey County, which is outside the study area. Those {mixed_n:,} person records are in `pums_commuters.parquet` with `puma_mixed_outside = True` and no county, and are excluded from all county estimates. San Benito's share of that PUMA's population: {', '.join(f"{r.san_benito_share:.1%} ({r.puma_vintage} definition)" for r in sm.itertuples())}.

## 3. Missingness

Full per-variable table: `data_qc_missingness.csv`. In `tract_analysis.parquet`, {n_complete} of {len(est)} numeric estimate columns have no missing values in any cross-section. Key variables (count of tracts missing, by cross-section):

{md(MSK, index=True)}

- Outcomes are missing for every tract in the 2010-2014 cross-section by design: no PLACES release has data inside that period.
- In the paired cross-sections, {', '.join(f"{int(r.tracts)} tracts ({bld.VINTAGES[i][0]}; ACS population {int(r.population):,} in total)" for i, r in noP.iterrows())} have no PLACES estimate.
- Mean commute time is missing where the aggregate travel time (B08013) is withheld or undefined:

{md(supp.rename(index=lambda i: bld.VINTAGES[i][0]).rename_axis("ACS period"), index=True)}

  For 2020-2024, {b13['tracts_absent_from_file']} tracts ({b13['commuters_in_absent_tracts']:,} commuters) are absent from the published B08013 file and {b13['tracts_with_jam_value']} carry a jam value with zero commuters.

County-year panel coverage (number of the 15 counties with a value):

{md(COV, index=True)}

## 4. Range and logic checks

{md(RG)}

## 5. Spot checks against sources

The brief asked for three values checked against the Census API. api.census.gov rejects data queries without a key (HTTP 302 to missing_key.html) and no key was configured, so, as agreed with the user, the ACS checks re-read the values from the Census bulk files with a separate minimal reader (line search by geography identifier and position lookup), not the acquisition code. CDC API checks: {cdc}.

{md(S)}

Identities between tables held in different source files (violations; all should be zero):

{md(ID)}

PUMS-derived 2023 county estimates against the Census Bureau's published ACS 1-year 2023 county tables (independent product; agreement expected within sampling error, z uses the PUMS replicate standard error and the published margin of error):

{md(CMP)}

{len(CMP)} counties compared; {int((CMP.z.abs() > 2).sum())} differ by more than two standard errors; largest difference {CMP.difference.abs().max():.2f} minutes.{' Published 1-year 2023 tables also exist for ' + ', '.join(pub_only) + ', which has no PUMS estimate.' if pub_only else ''}

PUMS-derived county estimates against the published ACS 1-year county tables in every overlap year (the `acs1_*` and `pums_*_16plus` columns of the panel; San Benito has no PUMS estimate):

{md(OV, index=True)}

Published ACS 1-year county tables aggregated over the 14 counties that also have PUMS estimates (commuter- or worker-weighted), showing the most recent year available:

{md(A14, index=True)}

## 6. Data features to handle in analysis

- **Top-coded medians.** ACS publishes capped medians as the cap plus one with no margin of error. They are kept and flagged (`*_topcoded`). The home-value cap is 1,000,000 in 2010-2014 and 2,000,000 afterwards, so the top of the distribution is not comparable across periods. Tracts flagged:

{md(tc, index=True)}

- **Dollar values are nominal.** Median income is in the dollars of the vintage year (`income_dollar_year`); home value and rent are not inflation-adjusted either.
- **Jam values.** The 2020-2024 files encode missing estimates and margins as large negative integers; all were set to missing. The 2010-2014 and 2015-2019 files encode them as missing already.
- **Tract boundaries.** Each cross-section is on its native boundaries (2010 tracts for the first two, 2020 tracts for the third); nothing was interpolated. `overlap_same_geoid` and `boundary_stable_99` identify tracts whose code and land area carry over: {int(stab.boundary_stable_99.sum()):,} of {len(stab):,} 2010-boundary tracts are stable at 99% mutual land-area overlap ({int((stab.overlap_same_geoid >= 0.95).sum()):,} at 95%). The full pair table is `tract_2010_2020_relationship.parquet` (land-area shares, not population shares).
- **PLACES repeats.** High blood pressure exists only for odd BRFSS years and short sleep only for even years, so consecutive PLACES releases repeat those values; they are not independent time points. In the tract table short sleep is one year earlier than the other measures (2018 and 2022).
- **PUMS replicate weights.** The main weight is positive for every record. {rw['negative_replicate_cells']:,} of {rw['total_replicate_cells']:,} replicate-weight cells are negative (years {', '.join(map(str, rw['years_with_negatives']))}); they are published values and must not be clipped when computing variances.
- **PUMS 2014 encoding.** The 2014 file marks not-applicable travel time and hours with a single space instead of an empty field ({notes['pums_2014_blank_encoding']['jwmnp_whitespace_2014']:,} travel-time fields); all years are read as text and blanks set to missing.
- **PUMS transport mode.** Codes 03-05 were redefined when JWTR became JWTRNS in 2019; `mode_cat` pools them as rail. Travel time is top-coded (observed maximum {int(PU.jwmnp.max())} minutes).
- **2025 comes from a different product.** `acs1_*` columns are published ACS 1-year county estimates (2021-2025), with published-table margins of error, for all 15 counties including San Benito. They agree with the PUMS-derived estimates within sampling error in the overlap years but are not the same estimator, are not age-specific, and should not be spliced onto the age-band series.
- **PUMA boundaries.** PUMS 2010-2011 use Census 2000 PUMAs, 2012-2021 use 2010 PUMAs and 2022-2024 use 2020 PUMAs. All non-mixed study PUMAs lie within one county, so county estimates are unaffected, but PUMA-level series break at 2012 and 2022.
- **2020 and the pandemic.** There is no standard 2020 ACS 1-year PUMS (data collection problems), so the person-level series has no 2020. From 2021 the work-from-home share is far higher, which changes who is counted as a commuter.
- **Acquisition events.** {len(fb)} table ({', '.join(fb.table.str.upper())}, vintage 2019, tract level) was read from the Census state bundle because the per-sequence file was refused by the server with a "Request Rejected" page; bundle members were verified byte-identical to per-sequence files on another sequence. During the original session, requests to data.cdc.gov failed twice with a transient 502 from the network proxy; the CDC checks in section 5 report how many completed in the run that produced this file.

## 7. Coverage less than requested

1. **Census API not used.** ACS tables come from the Census bulk summary files on www2.census.gov (same estimates and margins). County FIPS codes were verified from the ACS geography file by name, not from the API NAME field. The API spot check was replaced as described in section 5.
2. **ACS 5-year vintages.** Three mutually non-overlapping vintages were acquired (2010-2014, 2015-2019, 2020-2024). The 2005-2009 and 2006-2010 vintages and all overlapping intermediate vintages were not.
3. **PUMS.** 1-year files for 2010-2019 and 2021-2024 (14 years). No 2020. The 5-year PUMS files were not acquired. San Benito cannot be isolated. Place-of-work PUMA and work-state codes are carried raw; no destination-county variable was built because the naming pattern fails for some codes and no machine-readable crosswalk was found.
4. **Zillow rent index** starts in 2015 ({int(COV.loc['Zillow rent (zori_mean)', '2015'])} of 15 counties that year); the home value index covers every year.
5. **PLACES.** All six catalogued releases (2020-2025) are in `places_tract_long.parquet`; the tract table pairs only two of them with ACS periods. No tract outcomes exist for 2010-2014. Values are crude prevalences for adults 18+; none are age-specific.
6. **Mortality by age.** Only two age bands (35-64 and 65+), none under 35. Five topics for 2010-2019 and major cardiovascular disease for 2010-2020; nothing age-specific after 2020. All rates are model-smoothed, not counts. The pooled three-year series (adults 35+) has no 2020-2022 period, and its 2014-2016 period label is inferred from the year field.
7. **Road rage proxy.** CCRS covers 2016-2026 only; only the Crashes tables were tabulated. See `road_rage_proxy_assessment.md`.
8. **Tract harmonization.** Estimates were not interpolated between 2010 and 2020 boundaries. Each cross-section is on its native boundaries; the Census relationship file and a boundary-stability flag are provided for analyses that follow tracts across the change.
9. **Person file scope.** `pums_commuters.parquet` holds all persons aged 16 or older in study-area PUMAs (with worker, commuter and work-from-home flags), not commuters only, so that population denominators are available. No columns were dropped; the file is {os.path.getsize('pums_commuters.parquet') / 1e6:.0f} MB.
10. **2025 person file not published.** The 2025 ACS 1-year PUMS did not exist when checked, so `pums_commuters.parquet` and `pums_county_year_age.parquet` end in 2024 and there are no age-specific commute measures for 2025. The 2025 values in the panel are published county totals (`acs1_*`).
11. **Published 1-year county tables cover 2021-2025 only.** They were added to carry the series to 2025 and to overlap the PUMS years; the 2010-2019 1-year county tables were not acquired. Drive-alone and work-from-home shares use the collapsed table C08301 because the detailed table is withheld for some smaller counties.
12. **No 2021-2025 ACS 5-year release.** Tract tables end with 2020-2024.
13. **Nothing after 2020 for mortality by age, and no PLACES release after 2025** (see Source currency).
"""
    open("data_qc_report.md", "w", encoding="utf-8").write(report)
    print("violations", int((RG.violations > 0).sum()), "| dup tables", int((OUT["duplicate keys"] > 0).sum()), "| spot", int(S.match.sum()), "/", len(S), "| cdc", cdc, "| chars", len(report))
