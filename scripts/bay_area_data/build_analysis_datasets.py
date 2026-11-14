"""Build the analysis-ready datasets from the acquired raw files.

Part 1 (this section): tract x cross-section table from ACS 5-year tables.
  Cross-sections stay on their NATIVE tract boundaries: ACS 2010-2014 and 2015-2019 on 2010 tracts, 2020-2024 on 2020 tracts.
  ACS jam values (-666666666 estimate; -222222222, -333333333, -555555555 margins) are set to missing.
  Margins of error (90%) for derived quantities use the Census Bureau approximation formulas:
     sum:        sqrt(sum of squared MOEs)
     proportion: sqrt(MOE_num^2 - p^2 * MOE_den^2) / den   (ratio formula with + when the radicand is negative)
     ratio:      sqrt(MOE_num^2 + R^2 * MOE_den^2) / den
"""
import os, re, json, numpy as np, pandas as pd

VINTAGES = {2014: ("2010-2014", 2010), 2019: ("2015-2019", 2010), 2024: ("2020-2024", 2020)}
TABLES = ["B08303", "B08013", "B08301", "B08302", "B01001", "B19013", "B17001", "B15003", "B03002", "B25044", "B25077", "B25064"]
JAM = [-666666666, -222222222, -333333333, -555555555, -888888888, -999999999]

def load_acs(vintage, sumlevel):
    out = None
    for t in TABLES:
        d = pd.read_parquet(f"raw/acs/acs5_{vintage}_{t.lower()}.parquet"); d = d[d.sumlevel == sumlevel].drop(columns=["vintage", "sumlevel"])
        out = d if out is None else out.merge(d, on="GEO_ID", how="outer", validate="1:1")
    num = out.columns.drop("GEO_ID"); out[num] = out[num].astype("float64").mask(out[num].isin(JAM))
    return out

def cells(t, idx): return [f"{t}_E{i:03d}" for i in idx], [f"{t}_M{i:03d}" for i in idx]
def est_sum(d, t, idx):
    e, m = cells(t, idx); return d[e].sum(axis=1, min_count=len(e)), np.sqrt((d[m] ** 2).sum(axis=1, min_count=len(m)))
def prop(num, mnum, den, mden):
    p = (num / den).where(den > 0)
    rad = mnum ** 2 - (p ** 2) * (mden ** 2)
    moe = (np.sqrt(rad.where(rad >= 0, mnum ** 2 + (p ** 2) * (mden ** 2))) / den).where(den > 0)
    return p, moe
def ratio(num, mnum, den, mden):
    r = (num / den).where(den > 0); return r, (np.sqrt(mnum ** 2 + (r ** 2) * (mden ** 2)) / den).where(den > 0)

AGE = {"under18": [3, 4, 5, 6], "18_34": [7, 8, 9, 10, 11, 12], "35_64": [13, 14, 15, 16, 17, 18, 19], "65plus": [20, 21, 22, 23, 24, 25]}   # male cells; female = +24
SHARES = {  # name: (table, numerator cells, denominator cell)
    "share_commute_45plus": ("B08303", [11, 12, 13], 1), "share_commute_60plus": ("B08303", [12, 13], 1), "share_commute_90plus": ("B08303", [13], 1),
    "share_commute_lt15": ("B08303", [2, 3, 4], 1),
    "share_drive_alone": ("B08301", [3], 1), "share_carpool": ("B08301", [4], 1), "share_transit": ("B08301", [10], 1), "share_walk": ("B08301", [19], 1),
    "share_bike": ("B08301", [18], 1), "share_wfh": ("B08301", [21], 1), "share_taxi_moto_other": ("B08301", [16, 17, 20], 1),
    "share_depart_before_6am": ("B08302", [2, 3, 4], 1), "share_depart_before_7am": ("B08302", [2, 3, 4, 5, 6], 1),
    "share_female": ("B01001", [26], 1), "poverty_rate": ("B17001", [2], 1), "share_bachelors_plus": ("B15003", [22, 23, 24, 25], 1),
    "share_nh_white": ("B03002", [3], 1), "share_nh_black": ("B03002", [4], 1), "share_nh_asian": ("B03002", [6], 1), "share_hispanic": ("B03002", [12], 1),
    "share_no_vehicle_hh": ("B25044", [3, 10], 1)}
for k, mc in AGE.items(): SHARES[f"share_age_{k}"] = ("B01001", mc + [c + 24 for c in mc], 1)

def derive(d, vintage, sumlevel):
    period, tv = VINTAGES[vintage]; o = pd.DataFrame({"geoid": d.GEO_ID.str.split("US").str[1]})
    o["acs_vintage"] = vintage; o["acs_period"] = period
    if sumlevel == "140": o["tract_vintage"] = tv
    for name, (t, c) in {"pop_total": ("B01001", 1), "workers_total": ("B08301", 1), "commuters_total": ("B08303", 1), "households_total": ("B25044", 1)}.items():
        o[name] = d[f"{t}_E{c:03d}"].values; o[name + "_moe"] = d[f"{t}_M{c:03d}"].values
    for name, (t, nc, dc) in SHARES.items():
        n, mn = est_sum(d, t, nc); p, mp = prop(n, mn, d[f"{t}_E{dc:03d}"], d[f"{t}_M{dc:03d}"]); o[name] = p.values; o[name + "_moe"] = mp.values
    # drive-alone share among commuters only (denominator excludes people who worked from home)
    den = d.B08301_E001 - d.B08301_E021; mden = np.sqrt(d.B08301_M001 ** 2 + d.B08301_M021 ** 2)
    p, mp = prop(d.B08301_E003, d.B08301_M003, den, mden); o["share_drive_alone_commuters"] = p.values; o["share_drive_alone_commuters_moe"] = mp.values
    r, mr = ratio(d.B08013_E001, d.B08013_M001, d.B08303_E001, d.B08303_M001); o["mean_commute_min"] = r.values; o["mean_commute_min_moe"] = mr.values
    for name, t in {"median_hh_income": "B19013", "median_home_value": "B25077", "median_gross_rent": "B25064"}.items():
        o[name] = d[f"{t}_E001"].values; o[name + "_moe"] = d[f"{t}_M001"].values
    o["income_dollar_year"] = vintage
    return o

def build_tract_acs(counties):
    parts = [derive(load_acs(v, "140"), v, "140") for v in VINTAGES]
    T = pd.concat(parts, ignore_index=True).rename(columns={"geoid": "tract_geoid"})
    T.insert(1, "county_fips", T.tract_geoid.str[2:5])
    T = T.merge(counties[["county_fips", "county_name", "core9"]], on="county_fips", how="left", validate="m:1")
    return T

def build_county_acs(counties):
    C = pd.concat([derive(load_acs(v, "050"), v, "050") for v in VINTAGES], ignore_index=True)
    C.insert(0, "county_fips", C.geoid.str[2:5]); return C.drop(columns="geoid")

def read_counties():
    c = pd.read_csv("ref/study_counties.csv", dtype=str); c["core9"] = c.core9.str.lower().eq("true"); return c


# ----------------------------------------------------------------------------------------------
# Part 2: top-code flags and PLACES outcomes
# ----------------------------------------------------------------------------------------------
TOPCODE = {"median_home_value": {2014: 1000001, 2019: 2000001, 2024: 2000001}, "median_gross_rent": {2014: 2001, 2019: 3501, 2024: 3501},
           "median_hh_income": {2014: 250001, 2019: 250001, 2024: 250001}}
PLACES_MEASURES = ["CHD", "STROKE", "BPHIGH", "OBESITY", "LPA", "DIABETES", "CSMOKING", "SLEEP", "MHLTH", "DEPRESSION"]

def flag_topcodes(T):
    """ACS publishes capped medians as cap+1 with no margin of error. The value is kept; the flag marks it as right-censored."""
    for var, caps in TOPCODE.items():
        T[var + "_topcoded"] = T[var].eq(T.acs_vintage.map(caps)) & T[var + "_moe"].isna()
    return T

def choose_places_release(P):
    """For each ACS period: the latest PLACES release on the same tract boundaries whose data years (all measures) fall within the period."""
    rel = P.groupby("release").agg(tract_vintage=("tract_vintage", "first"), y0=("data_year", "min"), y1=("data_year", "max")).reset_index()
    choice = {}
    for v, (period, tv) in VINTAGES.items():
        a, b = map(int, period.split("-")); ok = rel[(rel.tract_vintage == tv) & (rel.y0 >= a) & (rel.y1 <= b)]
        choice[v] = int(ok.release.max()) if len(ok) else None
    return choice, rel

def attach_places(T, P):
    choice, rel = choose_places_release(P); wide = []
    for v, r in choice.items():
        if r is None: continue
        g = P[(P.release == r) & P.measureid.isin(PLACES_MEASURES)]
        assert not g.duplicated(["tract_geoid", "measureid"]).any()
        w = g.pivot(index="tract_geoid", columns="measureid", values=["data_value", "low_confidence_limit", "high_confidence_limit", "data_year"])
        w.columns = [f"{m.lower()}_{ {'data_value': 'prev', 'low_confidence_limit': 'prev_lo', 'high_confidence_limit': 'prev_hi', 'data_year': 'data_year'}[k]}" for k, m in w.columns]
        w = w.reset_index(); w["acs_vintage"] = v; w["places_release"] = r
        pop = g.groupby("tract_geoid").agg(places_totalpopulation=("totalpopulation", "first"), places_totalpop18plus=("totalpop18plus", "first")).reset_index()
        wide.append(w.merge(pop, on="tract_geoid", validate="1:1"))
    W = pd.concat(wide, ignore_index=True)
    out = T.merge(W, on=["tract_geoid", "acs_vintage"], how="left", validate="1:1")
    for m in PLACES_MEASURES:
        c = f"{m.lower()}_data_year"
        if c in out: out[c] = out[c].astype("Int16")
    out["places_release"] = out.places_release.astype("Int16"); out["has_places"] = out.places_release.notna()
    return out, choice, rel, W


# ----------------------------------------------------------------------------------------------
# Part 3: 2010 <-> 2020 tract relationship (Census relationship file) and boundary-stability flag
# ----------------------------------------------------------------------------------------------
REL_URL = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/tract/tab20_tract20_tract10_st06.txt"

def build_tract_relationship(counties, cache="raw/geo/tab20_tract20_tract10_st06.txt"):
    import requests
    if not os.path.exists(cache):
        r = requests.get(REL_URL, timeout=600); r.raise_for_status(); assert b"Request Rejected" not in r.content[:300]
        os.makedirs(os.path.dirname(cache), exist_ok=True); open(cache, "wb").write(r.content)
    d = pd.read_csv(cache, sep="|", dtype=str, encoding="utf-8-sig")
    d = d.rename(columns={"GEOID_TRACT_20": "tract_geoid_2020", "GEOID_TRACT_10": "tract_geoid_2010"})
    for c in ("AREALAND_TRACT_20", "AREAWATER_TRACT_20", "AREALAND_TRACT_10", "AREAWATER_TRACT_10", "AREALAND_PART", "AREAWATER_PART"): d[c] = pd.to_numeric(d[c])
    d = d[d.tract_geoid_2020.notna() & d.tract_geoid_2010.notna()]
    st = set(counties.county_geoid); d = d[d.tract_geoid_2020.str[:5].isin(st) | d.tract_geoid_2010.str[:5].isin(st)].copy()
    d["share_of_2020_land"] = (d.AREALAND_PART / d.AREALAND_TRACT_20).where(d.AREALAND_TRACT_20 > 0)
    d["share_of_2010_land"] = (d.AREALAND_PART / d.AREALAND_TRACT_10).where(d.AREALAND_TRACT_10 > 0)
    # pairs are kept when EITHER tract is in the study area; for a tract outside it, only its overlap with study tracts is
    # retained, so its shares need not sum to 1 - the flags make that explicit
    d["in_study_2020"] = d.tract_geoid_2020.str[:5].isin(st); d["in_study_2010"] = d.tract_geoid_2010.str[:5].isin(st)
    d.columns = [c.lower() for c in d.columns]
    keep = ["tract_geoid_2020", "tract_geoid_2010", "in_study_2020", "in_study_2010", "arealand_tract_20", "areawater_tract_20", "arealand_tract_10", "areawater_tract_10", "arealand_part", "areawater_part", "share_of_2020_land", "share_of_2010_land"]
    return d[keep].reset_index(drop=True)

def add_stability(T, REL, threshold=0.99):
    """overlap_same_geoid = min(share of the 2020 tract's land, share of the 2010 tract's land) for the pair with the SAME geoid
    in both vintages (missing if the code does not exist in the other vintage). boundary_stable_99: overlap >= 0.99."""
    same = REL[REL.tract_geoid_2020 == REL.tract_geoid_2010].copy()
    same["overlap_same_geoid"] = same[["share_of_2020_land", "share_of_2010_land"]].min(axis=1)
    ov = same.set_index("tract_geoid_2020").overlap_same_geoid
    T["overlap_same_geoid"] = T.tract_geoid.map(ov)
    T["boundary_stable_99"] = T.overlap_same_geoid.ge(threshold)
    n20 = REL.groupby("tract_geoid_2020").size(); n10 = REL.groupby("tract_geoid_2010").size()
    T["n_partner_tracts_other_vintage"] = np.where(T.tract_vintage == 2020, T.tract_geoid.map(n20), T.tract_geoid.map(n10))
    return T


# ----------------------------------------------------------------------------------------------
# Part 4: PUMS county x year x age-band commute measures with replicate-weight standard errors
# ----------------------------------------------------------------------------------------------
FINE = [("16_24", 16, 24), ("25_34", 25, 34), ("35_44", 35, 44), ("45_54", 45, 54), ("55_64", 55, 64), ("65plus", 65, 200)]
COARSE = {"16plus": ["16_24", "25_34", "35_44", "45_54", "55_64", "65plus"], "16_34": ["16_24", "25_34"], "35_64": ["35_44", "45_54", "55_64"]}
COMP = ["pop", "workers", "commuters", "minutes", "c45", "c60", "c90", "car_alone", "wfh"]
WCOLS = ["pwgtp"] + [f"pwgtp{i}" for i in range(1, 81)]

def _component_sums(PU):
    """Weighted sums of each component by year x county x fine age band, for the main weight and the 80 replicates."""
    P = PU[~PU.puma_mixed_outside & PU.county_fips.notna()]
    out = []
    for y, g in P.groupby("year"):
        band = pd.cut(g.agep, [15] + [hi for _, _, hi in FINE], labels=[n for n, _, _ in FINE]).astype(str)
        jw = g.jwmnp.astype("float64").fillna(0).values; com = g.commuter.values
        ind = {"pop": np.ones(len(g)), "workers": g.worker_at_work.values.astype(float), "commuters": com.astype(float), "minutes": jw,
               "c45": (com & (jw >= 45)).astype(float), "c60": (com & (jw >= 60)).astype(float), "c90": (com & (jw >= 90)).astype(float),
               "car_alone": (g.mode_cat == "car_alone").values.astype(float), "wfh": g.wfh.values.astype(float)}
        W = g[WCOLS].values.astype("float64"); key = pd.MultiIndex.from_arrays([g.county_fips.values, band.values], names=["county_fips", "age_band"])
        for c in COMP:
            s = pd.DataFrame(W * ind[c][:, None], index=key, columns=WCOLS).groupby(level=[0, 1]).sum()
            s.insert(0, "component", c); s.insert(0, "year", y); out.append(s.reset_index())
        n = pd.DataFrame({"n_persons": 1, "n_workers": ind["workers"], "n_commuters": ind["commuters"]}, index=key).groupby(level=[0, 1]).sum().reset_index(); n.insert(0, "year", y); n["component"] = "_n"; out.append(n)
    S = pd.concat(out, ignore_index=True)
    return S[S.component != "_n"].drop(columns=["n_persons", "n_workers", "n_commuters"]), S[S.component == "_n"][["year", "county_fips", "age_band", "n_persons", "n_workers", "n_commuters"]]

def _roll(S, N, counties):
    """Add coarse age bands and regional totals by summing the additive component sums."""
    def add_bands(df, val):
        extra = [df[df.age_band.isin(members)].assign(age_band=name).groupby([c for c in df.columns if c not in val], as_index=False)[val].sum() for name, members in COARSE.items()]
        return pd.concat([df] + extra, ignore_index=True)
    S = add_bands(S, WCOLS); N = add_bands(N, ["n_persons", "n_workers", "n_commuters"])
    core = set(counties[counties.core9].county_fips)
    def add_regions(df, val):
        keys = [c for c in df.columns if c not in val and c != "county_fips"]
        reg = [df[df.county_fips.isin(core)].groupby(keys, as_index=False)[val].sum().assign(county_fips="CORE9"),
               df[~df.county_fips.isin(core)].groupby(keys, as_index=False)[val].sum().assign(county_fips="EXT5"),
               df.groupby(keys, as_index=False)[val].sum().assign(county_fips="ALL14")]
        return pd.concat([df] + reg, ignore_index=True)
    return add_regions(S, WCOLS), add_regions(N, ["n_persons", "n_workers", "n_commuters"])

def build_pums_county_year(PU, counties):
    S, N = _roll(*_component_sums(PU), counties)
    A = {c: S[S.component == c].set_index(["year", "county_fips", "age_band"])[WCOLS] for c in COMP}
    idx = A["pop"].index; A = {c: a.reindex(idx).fillna(0) for c, a in A.items()}
    def stat(num, den=None):
        th = A[num] if den is None else A[num] / A[den].where(A[den] > 0)
        est = th["pwgtp"]; se = np.sqrt(4 / 80 * ((th.drop(columns="pwgtp").sub(est, axis=0)) ** 2).sum(axis=1, min_count=80))
        return est, se
    spec = {"pop": ("pop", None), "workers": ("workers", None), "commuters": ("commuters", None), "mean_commute_min": ("minutes", "commuters"),
            "share_commute_45plus": ("c45", "commuters"), "share_commute_60plus": ("c60", "commuters"), "share_commute_90plus": ("c90", "commuters"),
            "share_drive_alone_workers": ("car_alone", "workers"), "share_wfh_workers": ("wfh", "workers"),
            "pop_share_commute_60plus": ("c60", "pop"), "pop_share_commuter": ("commuters", "pop")}
    out = pd.DataFrame(index=idx)
    for name, (num, den) in spec.items():
        out[name], out[name + "_se"] = stat(num, den)
    out = out.reset_index().merge(N, on=["year", "county_fips", "age_band"], how="left", validate="1:1")
    nm = counties.set_index("county_fips").county_name.to_dict(); nm.update({"CORE9": "Core nine counties", "EXT5": "Extended counties with PUMS (excl. San Benito)", "ALL14": "All 14 counties with PUMS"})
    out.insert(2, "county_name", out.county_fips.map(nm)); out.insert(3, "is_region_total", out.county_fips.isin(["CORE9", "EXT5", "ALL14"]))
    c9 = counties.set_index("county_fips").core9.to_dict(); c9.update({"CORE9": True, "EXT5": False, "ALL14": False})
    out.insert(4, "core9", out.county_fips.map(c9).astype(bool))
    out["puma_vintage"] = np.where(out.year <= 2011, 2000, np.where(out.year <= 2021, 2010, 2020))
    for c in ("n_persons", "n_workers", "n_commuters"): out[c] = out[c].astype(int)
    return out.sort_values(["county_fips", "year", "age_band"]).reset_index(drop=True)


# ----------------------------------------------------------------------------------------------
# Part 5: mortality (long) and the county x year panel
# ----------------------------------------------------------------------------------------------
TOPIC = {"Coronary heart disease (CHD)": "chd", "Heart failure": "hf", "All heart disease": "hd", "Cardiovascular disease (CVD)": "cvd", "All stroke": "stroke",
         "Major Cardiovascular Disease": "majorcvd", "Heart Disease Mortality": "hd", "Stroke Mortality": "stroke"}

def _age(label):
    """Source labels: 'Ages 35-64 years', 'Ages 65 years and older', and a double-encoded 'Ages >=65 years' in rsk5-566a."""
    return "35-64" if "35-64" in label else ("65+" if "65" in label else label)

def build_mortality_long():
    log = pd.read_csv("raw/mortality/mortality_download_log.csv"); parts = []
    for _, x in log.iterrows():
        d = pd.read_parquet(f"raw/mortality/{x.tag}.parquet"); o = d[["dataset_id", "county_fips", "county_name", "core9"]].copy()
        o["series"] = "pooled_3yr_35plus" if x.tag.startswith("pooled_") else ("age_stratified_1999_2019" if x.dataset_id == "7b9s-s8ck" else "major_cvd_age_2010_2020")
        o["period"] = d.year.str.strip()
        if x.tag.startswith("pooled_"):
            per = re.search(r"(\d{4})-(\d{4})", x.tag); o["year"] = d.year.astype(int); o["period"] = f"{per.group(1)}-{per.group(2)}"
            o["period_inferred"] = x.tag.endswith("_inferred"); o["age_group"] = "35+"
            o["sex"] = d.stratification1; o["race"] = d.stratification2
        else:
            o["year"] = pd.to_numeric(d.year.where(d.year.str.fullmatch(r"\d{4}")), errors="coerce").astype("Int64"); o["period_inferred"] = False
            o["age_group"] = d.stratification1.map(_age)
            o["race"] = d.stratification2 if "stratification2" in d else "Overall"; o["sex"] = d.stratification3 if "stratification3" in d else "Overall"
        o["topic_label"] = d.topic; o["topic"] = d.topic.map(TOPIC); o["value_type"] = d.data_value_type; o["unit"] = d.data_value_unit
        o["value"] = pd.to_numeric(d.data_value, errors="coerce")
        for c in ("confidence_limit_low", "confidence_limit_high"): o[c.replace("confidence_limit_", "ci_")] = pd.to_numeric(d[c], errors="coerce") if c in d else np.nan
        o["footnote"] = d.data_value_footnote.replace({"NA": "", "nan": ""}); o["value_missing"] = o.value.isna()
        parts.append(o)
    M = pd.concat(parts, ignore_index=True); M["year"] = M.year.astype("Int64")
    assert M.topic.notna().all() and M.age_group.isin(["35-64", "65+", "35+"]).all()
    return M

def build_county_year_panel(counties, M, PCY, CACS, ACS1=None, years=range(2010, 2027)):
    P = pd.MultiIndex.from_product([counties.county_fips, list(years)], names=["county_fips", "year"]).to_frame(index=False)
    P = P.merge(counties[["county_fips", "county_name", "core9"]], on="county_fips")
    z = pd.read_parquet("zillow_county_annual.parquet")[["county_fips", "year", "zhvi_mean", "zhvi_n_months", "zori_mean", "zori_n_months"]]
    P = P.merge(z, on=["county_fips", "year"], how="left", validate="1:1")
    # PUMS commute measures (not available for San Benito, nor for 2020 and years after the latest release)
    meas = ["mean_commute_min", "share_commute_60plus", "share_commute_90plus", "share_drive_alone_workers", "share_wfh_workers", "pop_share_commute_60plus"]
    for band in ("16plus", "16_34", "35_64", "65plus"):
        g = PCY[(PCY.age_band == band) & ~PCY.is_region_total][["county_fips", "year", "commuters", "n_commuters"] + [c for m in meas for c in (m, m + "_se")]]
        g = g.rename(columns={c: f"pums_{c}_{band}" for c in g.columns if c not in ("county_fips", "year")})
        P = P.merge(g, on=["county_fips", "year"], how="left", validate="1:1")
    P["pums_available"] = P.pums_mean_commute_min_16plus.notna()
    # ACS 5-year county estimates, placed at the period end year
    keep = ["mean_commute_min", "share_commute_60plus", "share_commute_90plus", "share_drive_alone", "share_wfh", "median_home_value", "median_gross_rent", "median_hh_income", "pop_total", "commuters_total"]
    a = CACS[["county_fips", "acs_vintage", "acs_period"] + [c for k in keep for c in (k, k + "_moe")]].rename(columns={"acs_vintage": "year"})
    a = a.rename(columns={c: f"acs5_{c}" for c in a.columns if c not in ("county_fips", "year")})
    P = P.merge(a, on=["county_fips", "year"], how="left", validate="1:1")
    # mortality by age group: two sources kept as separate columns (different models and cause groupings; do not splice)
    A = M[(M.series == "age_stratified_1999_2019") & (M.race == "Overall") & (M.sex == "Overall") & M.year.notna() & M.value_type.str.contains("Smoothed Rate")]
    w = A.assign(col="mort_" + A.topic + "_" + A.age_group.map({"35-64": "35_64", "65+": "65plus"})).pivot(index=["county_fips", "year"], columns="col", values="value").reset_index()
    w["year"] = w.year.astype(int); P = P.merge(w, on=["county_fips", "year"], how="left", validate="1:1")
    B = M[(M.series == "major_cvd_age_2010_2020") & M.year.notna() & (M.value_type == "Age-Standardized, Spatially Smoothed Rate")]
    w = B.assign(col="mort_majorcvd_" + B.age_group.map({"35-64": "35_64", "65+": "65plus"})).pivot(index=["county_fips", "year"], columns="col", values="value").reset_index()
    w["year"] = w.year.astype(int); P = P.merge(w, on=["county_fips", "year"], how="left", validate="1:1")
    C = M[(M.series == "pooled_3yr_35plus") & (M.race == "Overall") & (M.sex == "Overall")]
    w = C.assign(col="pooled3yr_" + C.topic + "_35plus").pivot(index=["county_fips", "year"], columns="col", values="value").reset_index()
    w["year"] = w.year.astype(int); P = P.merge(w, on=["county_fips", "year"], how="left", validate="1:1")
    per = C.drop_duplicates(["year"]).set_index("year").period.to_dict(); P["pooled3yr_period"] = P.year.map({int(k): v for k, v in per.items()})
    if ACS1 is not None:            # appended last so that all earlier columns keep their position
        a1 = ACS1.rename(columns={c: f"acs1_{c}" for c in ACS1.columns if c not in ("county_fips", "year")})
        P = P.merge(a1, on=["county_fips", "year"], how="left", validate="1:1"); P["acs1_available"] = P.acs1_mean_commute_min.notna()
    return P.sort_values(["county_fips", "year"]).reset_index(drop=True)


# ----------------------------------------------------------------------------------------------
# Part 6: cell-level ACS file (every estimate and margin of error of the 12 tables) and cell labels
# ----------------------------------------------------------------------------------------------
def build_acs_cells(counties):
    """One row per geography x vintage, tract (sumlevel 140) and county (050) rows, all cells of the 12 tables as
    <TABLE>_E### (estimate) and <TABLE>_M### (90% margin of error). Jam values are missing. Native tract boundaries."""
    parts = []
    for v, (period, tv) in VINTAGES.items():
        for sl in ("140", "050"):
            d = load_acs(v, sl).copy(); d.insert(1, "acs_vintage", v); d.insert(2, "acs_period", period); d.insert(3, "sumlevel", sl)
            d.insert(4, "tract_vintage", tv if sl == "140" else pd.NA); d.insert(5, "geoid", d.GEO_ID.str.split("US").str[1]); d.insert(6, "county_fips", d.geoid.str[2:5])
            parts.append(d)
    C = pd.concat(parts, ignore_index=True).merge(counties[["county_fips", "county_name", "core9"]], on="county_fips", how="left", validate="m:1")
    C["tract_vintage"] = C.tract_vintage.astype("Int16")
    lead = ["GEO_ID", "geoid", "sumlevel", "acs_vintage", "acs_period", "tract_vintage", "county_fips", "county_name", "core9"]
    return C[lead + [c for c in C.columns if c not in lead]]

def fetch_acs_cell_labels():
    """Cell labels per vintage from the Census API metadata endpoint (answers without a key, unlike data queries)."""
    import requests
    rows = []
    for v in VINTAGES:
        for t in TABLES:
            r = requests.get(f"https://api.census.gov/data/{v}/acs/acs5/groups/{t}.json", timeout=120, allow_redirects=False); r.raise_for_status()
            for k, x in r.json()["variables"].items():
                m = re.fullmatch(rf"{t}_(\d{{3}})E", k)
                if m: rows.append({"table": t, "cell": m.group(1), "estimate_column": f"{t}_E{m.group(1)}", "moe_column": f"{t}_M{m.group(1)}", "acs_vintage": v, "label": x["label"].replace("Estimate!!", "").replace(":", "").strip(), "concept": x.get("concept", "")})
    L = pd.DataFrame(rows).sort_values(["table", "cell", "acs_vintage"]).reset_index(drop=True)
    L["label_differs_across_vintages"] = L.groupby(["table", "cell"]).label.transform(lambda s: s.str.lower().str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip().nunique() > 1)
    return L

# ----------------------------------------------------------------------------------------------
# Part 7: published ACS 1-year county tables (2021-2025) - the most recent commute data; county level, NOT age-specific
# ----------------------------------------------------------------------------------------------
ACS1_YEARS = [2021, 2022, 2023, 2024, 2025]

def build_acs1_county(counties):
    """Derived commute measures from the published ACS 1-year county tables B08303, B08013 and C08301 (collapsed means of
    transportation; identical to B08301 on shared cells and published for all 15 counties). Same formulas and
    margin-of-error approximations as the ACS 5-year values."""
    parts = []
    for y in ACS1_YEARS:
        d = None
        for t in ("b08303", "b08013", "c08301"):
            x = pd.read_parquet(f"raw/acs1/acs1_{y}_{t}.parquet").drop(columns="year"); d = x if d is None else d.merge(x, on="GEO_ID", how="outer", validate="1:1")
        num = d.columns.drop("GEO_ID"); d[num] = d[num].astype("float64").mask(d[num].isin(JAM))
        o = pd.DataFrame({"county_fips": d.GEO_ID.str[-3:], "year": y})
        o["commuters_total"] = d.B08303_E001.values; o["commuters_total_moe"] = d.B08303_M001.values
        o["workers_total"] = d.C08301_E001.values; o["workers_total_moe"] = d.C08301_M001.values
        r, mr = ratio(d.B08013_E001, d.B08013_M001, d.B08303_E001, d.B08303_M001); o["mean_commute_min"] = r.values; o["mean_commute_min_moe"] = mr.values
        for name, (t, nc) in {"share_commute_60plus": ("B08303", [12, 13]), "share_commute_90plus": ("B08303", [13]), "share_drive_alone": ("C08301", [3]), "share_wfh": ("C08301", [11])}.items():
            n, mn = est_sum(d, t, nc); p, mp = prop(n, mn, d[f"{t}_E001"], d[f"{t}_M001"]); o[name] = p.values; o[name + "_moe"] = mp.values
        parts.append(o)
    A = pd.concat(parts, ignore_index=True); assert set(A.county_fips) <= set(counties.county_fips) and not A.duplicated(["county_fips", "year"]).any()
    return A

# ----------------------------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------------------------
def main():
    counties = read_counties()
    P = pd.read_parquet("places_tract_long.parquet")
    T = flag_topcodes(build_tract_acs(counties)); T, choice, rel, _ = attach_places(T, P)
    REL = build_tract_relationship(counties); T = add_stability(T, REL)
    # design-level label (three cross-sections); whether an individual tract has outcomes is in has_places
    T.insert(0, "cross_section", T.acs_vintage.map(lambda v: f"{VINTAGES[v][0]} ACS / " + ("no PLACES release" if choice[v] is None else f"PLACES {choice[v]} release")))
    assert not T.duplicated(["tract_geoid", "acs_vintage"]).any()
    T.to_parquet("tract_analysis.parquet", index=False); REL.to_parquet("tract_2010_2020_relationship.parquet", index=False)
    CELLS = build_acs_cells(counties); assert not CELLS.duplicated(["GEO_ID", "acs_vintage"]).any(); CELLS.to_parquet("acs5_cells.parquet", index=False)
    LAB = fetch_acs_cell_labels(); LAB.to_csv("acs5_cell_labels.csv", index=False)
    PU = pd.read_parquet("pums_commuters.parquet")
    PCY = build_pums_county_year(PU, counties); PCY.to_parquet("pums_county_year_age.parquet", index=False)
    M = build_mortality_long(); M.to_parquet("mortality_long.parquet", index=False)
    ACS1 = build_acs1_county(counties)
    CY = build_county_year_panel(counties, M, PCY, build_county_acs(counties), ACS1); assert not CY.duplicated(["county_fips", "year"]).any()
    CY.to_parquet("county_year_panel.parquet", index=False)
    json.dump({"places_release_for_acs_vintage": {str(k): v for k, v in choice.items()},
               "rows": {"tract_analysis": len(T), "tract_2010_2020_relationship": len(REL), "pums_county_year_age": len(PCY), "mortality_long": len(M), "county_year_panel": len(CY), "acs5_cells": len(CELLS), "acs5_cell_labels": len(LAB)}},
              open("ref/build_summary.json", "w"), indent=1)
    print(json.load(open("ref/build_summary.json")))

if __name__ == "__main__":
    main()
