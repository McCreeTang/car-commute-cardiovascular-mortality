"""Build the analysis-ready national county dataset.

Inputs (written by acquire_acs_national.py, acquire_cdc_mortality_national.py, acquire_national_confounders.py):
  raw/acs_nat/acs5_<vintage>_<table>.parquet, raw/mortality_nat/cdc_7b9s-s8ck_race_overall.parquet,
  raw/ref_nat/*, raw/places_nat/*, ref/acs_nat_cell_labels.csv (cell labels, written by acquire_acs_national.py)
Outputs:
  national_county.parquet            one row per county unit x period (2006-2010, 2010-2014, 2015-2019)
  national_mortality_annual.parquet  county unit x year x cause x age band x sex
  national_county_crosswalk.csv      ACS / PLACES / reference county code -> analysis unit
  qc/national_topbin_calibration.csv          mean minutes assigned to the open-ended 60+ bin, by mode and vintage

ANALYSIS UNIT. The CDC mortality series is published for 3,136 county units. ACS counties are mapped onto those units
(XWALK below): three recodes/merges and two combined south-east Alaska units. Counts are summed over the component
counties; medians of combined units are household-weighted means of the component medians (flagged).

EXPOSURE. Weekly car-commute hours per adult resident =
    2 (trips per day) x aggregate one-way minutes of car commuters x DAYS / 60 / residents aged 16+ (or 18+),
with DAYS = 4.5 assumed commute days per week (same as the Bay Area burden model). The per-day component
(*_min_per_day_per_adult16) is kept so DAYS can be changed. Aggregate one-way minutes by mode come from
  (a) *_agg_min_pub: the published aggregate (B08136; C08136 in 2006-2010), suppressed for many small counties;
  (b) *_agg_min_mid: PRIMARY, available for every county. Bin-midpoint minutes from the mode-by-travel-time table
      (B08134; C08134 in 2006-2010) are computed for car, transit and all other modes, then scaled by one county factor
      so that the three modes sum to the county's published aggregate travel time for all modes (B08013, which is
      published for all but a handful of very small counties; those are scaled by the period median factor and
      flagged agg_scaled_with_median_factor). Midpoints (minutes): <10 -> 5; 10-14 -> 12; 15-19 -> 17; 20-24 -> 22; 25-29 -> 27;
      30-34 -> 32; 35-44 -> 39.5; 45-59 -> 52. Open-ended 60+ bin: assumed mean 75 minutes for car and other modes and
      80 minutes for public transit (TOP below; a bounded least-squares fit of published aggregates on bin counts gives
      top-bin coefficients of this size, see qc/national_topbin_calibration.csv). Because of the scaling, the midpoints only
      apportion the known county total between modes; the car estimate is insensitive to the top-bin assumption.
  (c) *_agg_min_midraw: the unscaled bin-midpoint total, kept for transparency and for the QC comparison only.
"""
import os, re, zipfile, numpy as np, pandas as pd

RAW = "raw/acs_nat"; DAYS = 4.5
PERIODS = {2010: ("2006-2010", list(range(2006, 2011)), 2008), 2014: ("2010-2014", list(range(2010, 2015)), 2012),
           2019: ("2015-2019", list(range(2015, 2020)), 2017)}
XWALK = {
    "51515": ("51019", "Bedford city VA (independent city) merged into Bedford County in July 2013; separate only in ACS 2006-2010"),
    "46113": ("46102", "Shannon County SD renamed Oglala Lakota County (new code) in 2015; ACS 2006-2010 and 2010-2014 use 46113"),
    "02270": ("02158", "Wade Hampton Census Area AK renamed Kusilvak Census Area (new code) in 2015; ACS 2006-2010 and 2010-2014 use 02270"),
    "02130": ("02901", "CDC combined unit Ketchikan-Prince of Wales-Wrangell-Petersburg (Alaska boundary changes 2008-2013)"),
    "02198": ("02901", "CDC combined unit Ketchikan-Prince of Wales-Wrangell-Petersburg"),
    "02275": ("02901", "CDC combined unit Ketchikan-Prince of Wales-Wrangell-Petersburg"),
    "02195": ("02901", "CDC combined unit Ketchikan-Prince of Wales-Wrangell-Petersburg"),
    "02110": ("02902", "CDC combined unit Juneau-Haines-Hoonah-Angoon-Skagway (Alaska boundary changes 2007-2013)"),
    "02100": ("02902", "CDC combined unit Juneau-Haines-Hoonah-Angoon-Skagway"),
    "02105": ("02902", "CDC combined unit Juneau-Haines-Hoonah-Angoon-Skagway"),
    "02230": ("02902", "CDC combined unit Juneau-Haines-Hoonah-Angoon-Skagway"),
}
UNIT_NAMES = {"02901": "Ketchikan-Prince of Wales-Wrangell-Petersburg (combined), Alaska", "02902": "Juneau-Haines-Hoonah-Angoon-Skagway (combined), Alaska"}
MEDIAN_TABLES = {"B19013": ("B25044", 1), "B25077": ("B25044", 2)}      # weight cell: occupied units / owner-occupied units
TOP = {"car": 75.0, "drivealone": 75.0, "transit": 80.0, "other": 75.0}      # assumed mean minutes of the open-ended 60+ bin
MID = {1: 5.0, 2: 12.0, 3: 17.0, 4: 22.0, 5: 27.0, 6: 32.0, 7: 39.5, 8: 52.0}     # offset within a mode block of B08134/C08134; offset 9 = 60+
TOPICS = {"Cardiovascular disease (CVD)": "cvd", "All heart disease": "hd", "Coronary heart disease (CHD)": "chd", "All stroke": "stroke", "Heart failure": "hf"}
AGES = {"Ages 35-64 years": "35_64", "Ages 65 years and older": "65plus"}
SEXES = {"Overall": "all", "Men": "men", "Women": "women"}
REGION = {"Northeast": {"New England": "09 23 25 33 44 50", "Middle Atlantic": "34 36 42"},
          "Midwest": {"East North Central": "17 18 26 39 55", "West North Central": "19 20 27 29 31 38 46"},
          "South": {"South Atlantic": "10 11 12 13 24 37 45 51 54", "East South Central": "01 21 28 47", "West South Central": "05 22 40 48"},
          "West": {"Mountain": "04 08 16 30 32 35 49 56", "Pacific": "02 06 15 41 53"}}

unit = lambda s: s.map(lambda f: XWALK.get(f, (f,))[0])

# ----------------------------------------------------------------------------------------------- ACS cells
def labels():
    L = pd.read_csv("ref/acs_nat_cell_labels.csv", dtype={"table": str})
    return {(int(v), t, int(c)): l for v, t, c, l in zip(L.vintage, L.table, L.cell, L.label)}

def tables_for(v):
    return sorted(os.path.basename(f)[10:-8].upper() for f in os.listdir(RAW) if f.startswith(f"acs5_{v}_") and f.endswith(".parquet"))

def load_cells(v):
    """County cells mapped to analysis units (summed) and state cells. Returns (county E, county M, state E, components)."""
    cE, cM, sE = [], [], []; comp = None; med = {}
    for t in tables_for(v):
        d = pd.read_parquet(os.path.join(RAW, f"acs5_{v}_{t.lower()}.parquet"))
        e = [c for c in d.columns if "_E" in c]; m = [c for c in d.columns if "_M" in c]
        c = d[d.sumlevel == "050"].copy(); c["fips"] = unit(c.geoid)
        if comp is None:
            comp = c[["geoid", "name", "fips"]].copy()
        if t in MEDIAN_TABLES:
            med[t] = c[["geoid", "fips"] + e + m]
        else:
            g = c.groupby("fips")
            cE.append(g[e].sum(min_count=1).mask(c[e].isna().groupby(c.fips).any()))          # missing if any component is missing
            cM.append(np.sqrt((c[m] ** 2).groupby(c.fips).sum(min_count=1)).mask(c[m].isna().groupby(c.fips).any()))
        sE.append(d[d.sumlevel == "040"].set_index("geoid")[e])
    E = pd.concat(cE, axis=1); M = pd.concat(cM, axis=1)
    n_comp = comp.groupby("fips").size()
    for t, (wt, wc) in MEDIAN_TABLES.items():           # medians: exact for single-county units, weighted mean otherwise
        w = pd.read_parquet(os.path.join(RAW, f"acs5_{v}_{wt.lower()}.parquet")).set_index("geoid")[f"{wt}_E{wc:03d}"]
        x = med[t].copy(); x["w"] = x.geoid.map(w); col = f"{t}_E001"
        x["wv"] = x[col] * x.w; x["wok"] = x.w.where(x[col].notna())
        g = x.groupby("fips"); E[col] = g.wv.sum(min_count=1) / g.wok.sum(min_count=1)
        single = x[x.fips.map(n_comp) == 1].set_index("fips")
        E.loc[single.index, col] = single[col]
        M[f"{t}_M001"] = np.nan; M.loc[single.index, f"{t}_M001"] = single[f"{t}_M001"]
    return E, M, pd.concat(sE, axis=1), comp

def cell(t, i): return f"{t}_E{i:03d}"
def mcell(t, i): return f"{t}_M{i:03d}"

def moe_sum(M, E, cells):
    """Census approximation for a sum: root sum of squares; among zero estimates only the largest margin is used once."""
    m = M[[c.replace("_E", "_M") for c in cells]].to_numpy(float); e = E[cells].to_numpy(float)
    z = e == 0; nz = np.where(z, 0.0, m); zmax = np.where(z, m, 0.0).max(axis=1)
    return pd.Series(np.sqrt(np.nansum(nz ** 2, axis=1) + zmax ** 2), index=E.index)

def moe_prop(num, den, m_num, m_den):
    p = num / den; u = m_num ** 2 - (p ** 2) * (m_den ** 2)
    return np.sqrt(np.where(u >= 0, u, m_num ** 2 + (p ** 2) * (m_den ** 2))) / den

def moe_ratio(num, den, m_num, m_den):
    return np.sqrt(m_num ** 2 + ((num / den) ** 2) * (m_den ** 2)) / den

def find(lab, v, t, pattern, n=None):
    """Cell numbers of table t whose label matches the regex (label-driven selection; asserted counts)."""
    out = [c for (vv, tt, c), l in lab.items() if vv == v and tt == t and re.search(pattern, l)]
    assert out and (n is None or len(out) == n), f"{v} {t} /{pattern}/: {len(out)} cells, expected {n}"
    return sorted(out)

def mode_blocks(v):
    """First cell of each mode block (10 cells: total + 9 time bins) of the mode-by-travel-time table, and aggregate cells."""
    if v == 2010:
        return ("C08134", {"all": [1], "drivealone": [11], "car": [11, 21], "transit": [31]},
                "C08136", {"all": [1], "drivealone": [2], "car": [2, 3], "transit": [4]})
    return ("B08134", {"all": [1], "car": [11], "drivealone": [21], "transit": [61]},
            "B08136", {"all": [1], "car": [2], "drivealone": [3], "transit": [7]})

def check_layout(lab, v):
    tt, blocks, ta, aggs = mode_blocks(v)
    want = {"all": "^Total", "drivealone": "rove alone", "transit": "^Public transportation", "car": "Car, truck, or van"}
    wagg = dict(want, all="^Aggregate")
    for k, starts in blocks.items():
        for s in starts:
            assert re.search(want[k], lab[(v, tt, s)]), (v, tt, s, lab[(v, tt, s)])
            assert lab[(v, tt, s + 1)].startswith("Less than 10") and lab[(v, tt, s + 8)].startswith("45 to 59") and lab[(v, tt, s + 9)].startswith("60 or more"), (v, tt, s)
    for k, cells_ in aggs.items():
        for c in cells_:
            assert re.search(wagg[k], lab[(v, ta, c)]), (v, ta, c, lab[(v, ta, c)])
    if v == 2010:   # the two car blocks must be drove alone + carpooled
        assert "drove alone" in lab[(v, tt, 11)] and "carpooled" in lab[(v, tt, 21)] and "drove alone" in lab[(v, ta, 2)] and "carpooled" in lab[(v, ta, 3)]
    b = {i: lab[(v, "B08303", i)] for i in range(1, 14)}
    assert b[11].startswith("45 to 59") and b[12].startswith("60 to 89") and b[13].startswith("90 or more"), b
    m = {i: lab[(v, "B08301", i)] for i in (2, 3, 4, 10, 18, 19, 21)}
    assert m[3].startswith("Drove alone") and m[4].startswith("Carpooled") and m[10].startswith("Public transportation") and m[18] == "Bicycle" and m[19] == "Walked" and m[21].startswith("Worked"), m

def bins(E, tt, starts, off):
    return sum(E[cell(tt, s + off)] for s in starts)

def topbin_diagnostics(E, sE, v):
    """Diagnostics behind the 60+ assumption (not used in the estimates): (1) the top-bin mean that would make the state
    midpoint totals equal the published state aggregates - below 60 for car, which shows that the closed-bin midpoints
    overstate (reported times heap at the lower bin bounds 10, 15, 20, 30, 45); (2) the 60+ coefficient of a bounded
    least-squares fit of the published aggregate on the nine bin counts (each coefficient constrained to its bin)."""
    from scipy.optimize import lsq_linear
    tt, blocks, ta, aggs = mode_blocks(v); rows = []
    lo = np.array([1, 10, 15, 20, 25, 30, 35, 45, 60.]); hi = np.array([9, 14, 19, 24, 29, 34, 44, 59, 240.])
    for k in blocks:
        agg = sum(sE[cell(ta, c)] for c in aggs[k]); low = sum(MID[o] * bins(sE, tt, blocks[k], o) for o in MID); n60 = bins(sE, tt, blocks[k], 9)
        ok = agg.notna() & n60.notna(); row = {"vintage": v, "mode": k, "states_used": int(ok.sum()),
               "top_bin_mean_matching_state_totals": float((agg[ok].sum() - low[ok].sum()) / n60[ok].sum())}
        for tag, df in (("states", sE), ("counties", E)):
            X = np.column_stack([bins(df, tt, blocks[k], o) for o in range(1, 10)]).astype(float); y = sum(df[cell(ta, c)] for c in aggs[k]).to_numpy(float)
            n = X.sum(1); g = np.isfinite(y) & (n > 0); w = 1 / np.sqrt(n[g])
            row[f"bounded_ls_top_bin_{tag}"] = float(lsq_linear(X[g] * w[:, None], y[g] * w, bounds=(lo, hi)).x[8]); row[f"bounded_ls_n_{tag}"] = int(g.sum())
        row["top_bin_assumed"] = TOP.get(k, np.nan); rows.append(row)
    return pd.DataFrame(rows)

def derive(v, lab):
    check_layout(lab, v)
    E, M, sE, comp = load_cells(v); tt, blocks, ta, aggs = mode_blocks(v)
    cal = topbin_diagnostics(E, sE, v)
    o = pd.DataFrame(index=E.index); o["acs_vintage"] = v; o["period"] = PERIODS[v][0]
    o["n_acs_components"] = comp.groupby("fips").size().reindex(o.index); o["unit_aggregated"] = o.n_acs_components > 1
    o["acs_component_geoids"] = comp.groupby("fips").geoid.agg(";".join).reindex(o.index)
    nm = comp.groupby("fips").name.first(); o["county_name_acs"] = [UNIT_NAMES.get(f, nm[f]) if o.n_acs_components[f] > 1 and f in UNIT_NAMES else nm[f] for f in o.index]
    S = lambda t, cells_: E[[cell(t, i) for i in cells_]].sum(axis=1, min_count=len(cells_))
    Ms = lambda t, cells_: moe_sum(M, E, [cell(t, i) for i in cells_])
    # ---- population denominators
    B = "B01001"; age = {"u18": [3, 4, 5, 6, 27, 28, 29, 30], "18_34": list(range(7, 13)) + list(range(31, 37)), "35_64": list(range(13, 20)) + list(range(37, 44)),
                        "65plus": list(range(20, 26)) + list(range(44, 50)), "45_64": list(range(15, 20)) + list(range(39, 44))}
    assert lab[(v, B, 6)].startswith("15 to 17") and lab[(v, B, 7)].startswith("18 and 19") and lab[(v, B, 13)].startswith("35 to 39") and lab[(v, B, 15)].startswith("45 to 49") and lab[(v, B, 20)].startswith("65 and 66") and lab[(v, B, 26)].startswith("Female") and lab[(v, B, 44)].startswith("65 and 66")
    o["pop_total"] = E[cell(B, 1)]; o["pop_total_moe"] = M[mcell(B, 1)]
    for k, c in age.items(): o[f"pop_{k}"] = S(B, c)
    o["pop_18plus"] = o.pop_total - o.pop_u18; o["pop_18plus_moe"] = Ms(B, [i for k in ("18_34", "35_64", "65plus") for i in age[k]])
    assert lab[(v, "B23001", 1)].startswith("Total")
    o["pop_16plus"] = E[cell("B23001", 1)]; o["pop_16plus_moe"] = M[mcell("B23001", 1)]
    for k in ("u18", "18_34", "35_64", "65plus"): o[f"share_age_{k.replace('u18', 'under18')}"] = o[f"pop_{k}"] / o.pop_total
    o["share_female"] = E[cell(B, 26)] / o.pop_total
    # ---- workers, modes
    W = "B08301"; o["workers_total"] = E[cell(W, 1)]; o["workers_total_moe"] = M[mcell(W, 1)]
    o["commuters_total"] = E[cell("B08303", 1)]
    for k, c in {"car": [2], "drive_alone": [3], "carpool": [4], "transit": [10], "bike": [18], "walk": [19], "wfh": [21]}.items():
        o[f"share_{k}"] = S(W, c) / o.workers_total
        if k in ("drive_alone", "transit", "wfh", "car"): o[f"share_{k}_moe"] = moe_prop(S(W, c), o.workers_total, M[mcell(W, c[0])], o.workers_total_moe)
    o["share_drive_alone_commuters"] = E[cell(W, 3)] / (E[cell(W, 1)] - E[cell(W, 21)])
    o["workers_per_adult16"] = o.workers_total / o.pop_16plus
    # ---- travel time distribution, all modes (B08303)
    Tt = "B08303"
    for k, c in {"45plus": [11, 12, 13], "60plus": [12, 13], "90plus": [13], "lt15": [2, 3, 4]}.items():
        o[f"share_commute_{k}"] = S(Tt, c) / E[cell(Tt, 1)]
        if k in ("45plus", "60plus"): o[f"share_commute_{k}_moe"] = moe_prop(S(Tt, c), E[cell(Tt, 1)], Ms(Tt, c), M[mcell(Tt, 1)])
    # ---- aggregate one-way minutes: all modes (published for every county) and by mode (published or raked midpoints)
    A = E[cell("B08013", 1)]; Am = M[mcell("B08013", 1)]; nall = E[cell(Tt, 1)]
    o["all_agg_min_pub"] = A; o["all_agg_min_pub_moe"] = Am; o["all_agg_pub_suppressed"] = A.isna()
    o["mean_tt_all_pub"] = A / nall; o["mean_tt_all_pub_moe"] = moe_ratio(A, nall, Am, M[mcell(Tt, 1)])
    def midraw(k):
        """Unscaled bin-midpoint minutes of a mode and an approximate margin of error."""
        if k == "other":      # all modes minus car minus transit, bin by bin
            cnt = {off: bins(E, tt, blocks["all"], off) - bins(E, tt, blocks["car"], off) - bins(E, tt, blocks["transit"], off) for off in range(1, 10)}
            return sum(MID[off] * cnt[off] for off in MID) + TOP[k] * cnt[9], None
        cells_ = [cell(tt, s + off) for s in blocks[k] for off in range(1, 10)]; w = np.array([MID.get(off, TOP[k]) for s in blocks[k] for off in range(1, 10)])
        e = E[cells_].to_numpy(float); m = M[[c.replace("_E", "_M") for c in cells_]].to_numpy(float) * w; z = e == 0
        return pd.Series(e @ w, index=E.index), pd.Series(np.sqrt(np.nansum(np.where(z, 0, m) ** 2, axis=1) + np.where(z, m, 0).max(axis=1) ** 2), index=E.index)
    raw = {k: midraw(k) for k in ("car", "drivealone", "transit", "other")}
    raw_sum = raw["car"][0] + raw["transit"][0] + raw["other"][0]
    o["rake_factor"] = A / raw_sum                      # < 1 where midpoints overstate (heaping at lower bin bounds)
    # B08013 is withheld for a handful of very small counties: scale those by the median factor of the period (flagged)
    o["agg_scaled_with_median_factor"] = A.isna() & raw_sum.notna() & (raw_sum > 0)
    f_med = float(o.rake_factor.median()); A_fill = A.where(A.notna(), raw_sum * f_med); Am = Am.where(A.notna(), 0.0)
    o["mean_tt_all_midraw"] = raw_sum / bins(E, tt, blocks["all"], 0)
    raw_sum_moe = np.sqrt(raw["car"][1] ** 2 + raw["transit"][1] ** 2)       # other modes ignored: approximate
    o["all_min_per_day_per_adult16"] = 2 * A / o.pop_16plus
    o["all_hours_wk_per_adult16"] = 2 * A * DAYS / 60 / o.pop_16plus
    for k in ("car", "drivealone", "transit"):
        n = bins(E, tt, blocks[k], 0); r, rm = raw[k]; o[f"{k}_commuters"] = n
        share = r / raw_sum; share_m = moe_prop(r, raw_sum, rm, raw_sum_moe)
        mid = A_fill * share; mid_moe = np.sqrt((A_fill * share_m) ** 2 + (share * Am) ** 2)
        pub = sum(E[cell(ta, c)] for c in aggs[k]); pub_moe = np.sqrt(sum(M[mcell(ta, c)] ** 2 for c in aggs[k]))
        o[f"{k}_agg_min_mid"] = mid; o[f"{k}_agg_min_mid_moe"] = mid_moe; o[f"{k}_agg_min_midraw"] = r
        o[f"{k}_agg_min_pub"] = pub; o[f"{k}_agg_min_pub_moe"] = pub_moe; o[f"{k}_agg_pub_suppressed"] = pub.isna()
        o[f"mean_tt_{k}_mid"] = mid / n; o[f"mean_tt_{k}_pub"] = pub / n
        o[f"share_{k}_commuters_45plus"] = (bins(E, tt, blocks[k], 8) + bins(E, tt, blocks[k], 9)) / n
        o[f"share_{k}_commuters_60plus"] = bins(E, tt, blocks[k], 9) / n
        o[f"{k}_commuters_per_adult16"] = n / o.pop_16plus
        o[f"{k}_commuters_45plus_per_adult16"] = (bins(E, tt, blocks[k], 8) + bins(E, tt, blocks[k], 9)) / o.pop_16plus
        o[f"{k}_commuters_60plus_per_adult16"] = bins(E, tt, blocks[k], 9) / o.pop_16plus
        for src, a, am in (("", mid, mid_moe), ("_pub", pub, pub_moe)):
            o[f"{k}_min_per_day_per_adult16{src}"] = 2 * a / o.pop_16plus
            o[f"{k}_hours_wk_per_adult16{src}"] = 2 * a * DAYS / 60 / o.pop_16plus
            o[f"{k}_hours_wk_per_adult16{src}_moe"] = 2 * DAYS / 60 * moe_ratio(a, o.pop_16plus, am, o.pop_16plus_moe)
            o[f"{k}_hours_wk_per_adult18{src}"] = 2 * a * DAYS / 60 / o.pop_18plus
        o[f"{k}_hours_wk_per_commuter"] = 2 * o[f"mean_tt_{k}_mid"] * DAYS / 60
    o["commute_days_assumed"] = DAYS; o["top_bin_minutes_car"] = TOP["car"]; o["top_bin_minutes_transit"] = TOP["transit"]
    # ---- workers by age and mode (B08101)
    A = "B08101"; al = {i: lab[(v, A, i)] for i in range(1, 57)}
    assert al[9].startswith("Car, truck, or van - drove alone") and al[17].startswith("Car, truck, or van - carpooled") and al[25].startswith("Public transportation") and al[5].startswith("45 to 54") and al[8].startswith("65 years")
    car_age = lambda offs: S(A, [9 + x for x in offs] + [17 + x for x in offs])
    o["workers_45_64"] = S(A, [5, 6, 7]); o["workers_65plus"] = E[cell(A, 8)]
    o["car_workers_45_64"] = car_age([4, 5, 6]); o["car_workers_65plus"] = car_age([7]); o["car_workers_16_44"] = car_age([1, 2, 3])
    o["transit_workers_45_64"] = S(A, [29, 30, 31]); o["transit_workers_65plus"] = E[cell(A, 32)]
    o["car_worker_share_pop_45_64"] = o.car_workers_45_64 / o.pop_45_64; o["car_worker_share_pop_65plus"] = o.car_workers_65plus / o.pop_65plus
    o["transit_worker_share_pop_45_64"] = o.transit_workers_45_64 / o.pop_45_64
    o["worker_share_pop_65plus"] = o.workers_65plus / o.pop_65plus
    # ---- covariates
    o["median_hh_income"] = E[cell("B19013", 1)]; o["median_hh_income_moe"] = M[mcell("B19013", 1)]; o["income_dollar_year"] = v
    o["median_home_value"] = E[cell("B25077", 1)]; o["median_home_value_moe"] = M[mcell("B25077", 1)]
    o["median_approx"] = o.unit_aggregated
    cap = {2010: 1000001, 2014: 2000001, 2019: 2000001}[v]; o["median_home_value_topcoded"] = o.median_home_value >= cap
    assert lab[(v, "B17001", 2)].startswith("Income in the past 12 months below poverty")
    o["poverty_rate"] = E[cell("B17001", 2)] / E[cell("B17001", 1)]
    Ed = "B15002"; el = {i: lab[(v, Ed, i)] for i in range(1, 36)}
    ba = find(lab, v, Ed, r"^(Bachelor's|Master's|Professional school|Doctorate) degree", 8); hs = find(lab, v, Ed, r"^(High school graduate)", 2)
    lths = [i for i in range(3, 11)] + [i for i in range(20, 28)]
    assert el[2].startswith("Male") and el[19].startswith("Female") and el[11].startswith("High school graduate") and el[10].startswith("12th grade") and el[27].startswith("12th grade"), el
    o["share_bachelors_plus"] = S(Ed, ba) / E[cell(Ed, 1)]; o["share_less_than_hs"] = S(Ed, lths) / E[cell(Ed, 1)]
    R = "B03002"; rl = {i: lab[(v, R, i)] for i in (3, 4, 5, 6, 12)}
    assert rl[3].startswith("White alone") and rl[4].startswith("Black") and rl[5].startswith("American Indian") and rl[6].startswith("Asian") and rl[12].startswith("Hispanic"), rl
    for k, c in {"nh_white": 3, "nh_black": 4, "nh_aian": 5, "nh_asian": 6, "hispanic": 12}.items(): o[f"share_{k}"] = E[cell(R, c)] / E[cell(R, 1)]
    L = "B23001"; emp = find(lab, v, L, r"^Employed$", 26); une = find(lab, v, L, r"^Unemployed$", 26); af = find(lab, v, L, r"Armed Forces", 20)
    o["unemployment_rate"] = S(L, une) / (S(L, emp) + S(L, une)); o["labor_force_participation"] = (S(L, emp) + S(L, une) + S(L, af)) / o.pop_16plus
    if v != 2010:
        o["unemployment_rate_b23025"] = E[cell("B23025", 5)] / E[cell("B23025", 3)]
        I = "B27001"; no = find(lab, v, I, r"^No health insurance coverage", 18); il = {i: lab[(v, I, i)] for i in range(1, 58)}
        a1864 = [i for i in range(1, 58) if re.match(r"^(18 to 24|19 to 25|25 to 34|26 to 34|35 to 44|45 to 54|55 to 64) years", il[i])]
        no1864 = [i + 2 for i in a1864]; assert all(il[i].startswith("No health insurance") for i in no1864), [il[i] for i in no1864]
        o["share_uninsured"] = S(I, no) / E[cell(I, 1)]; o["share_uninsured_18_64"] = S(I, no1864) / S(I, a1864)
        o["uninsured_18_64_youngest_age"] = 18 if any(il[i].startswith("18 to 24") for i in a1864) else 19
    else:
        o["unemployment_rate_b23025"] = np.nan; o["share_uninsured"] = np.nan; o["share_uninsured_18_64"] = np.nan; o["uninsured_18_64_youngest_age"] = np.nan
    H = "B25044"; hl = {i: lab[(v, H, i)] for i in (3, 10)}; assert hl[3].startswith("No vehicle") and hl[10].startswith("No vehicle"), hl
    o["households_total"] = E[cell(H, 1)]; o["share_no_vehicle_hh"] = S(H, [3, 10]) / E[cell(H, 1)]
    o["share_owner_occupied"] = E[cell(H, 2)] / E[cell(H, 1)]
    o = o.copy()
    return o.reset_index().rename(columns={"index": "fips"}), cal, comp

# ----------------------------------------------------------------------------------------------- mortality
def mortality():
    m = pd.read_parquet("raw/mortality_nat/cdc_7b9s-s8ck_race_overall.parquet")
    m = m[m.data_value_type.str.startswith("Age-Standardized") & m.year.str.fullmatch(r"\d{4}")].copy()
    a = pd.DataFrame({"fips": m.locationid.str.zfill(5), "state_abbr": m.locationabbr, "county_name_cdc": m.locationdesc, "year": m.year.astype(int),
                      "topic": m.topic.map(TOPICS), "age_band": m.stratification1.map(AGES), "sex": m.stratification3.map(SEXES),
                      "rate": pd.to_numeric(m.data_value, errors="coerce"), "ci_low": pd.to_numeric(m.confidence_limit_low, errors="coerce"),
                      "ci_high": pd.to_numeric(m.confidence_limit_high, errors="coerce"), "suppressed": m.data_value_footnote.eq("Value suppressed")})
    assert a[["topic", "age_band", "sex"]].notna().all().all() and not a.duplicated(["fips", "year", "topic", "age_band", "sex"]).any()
    assert (a.rate.isna() == a.suppressed).all()
    a = a.sort_values(["fips", "topic", "age_band", "sex", "year"]).reset_index(drop=True)
    wide = []
    for v, (per, yrs, mid) in PERIODS.items():
        x = a[a.year.isin(yrs)]; g = x.groupby(["fips", "topic", "age_band", "sex"])
        r = g.rate.agg(["mean", "count"]).reset_index(); r["mean"] = r["mean"].where(r["count"] == len(yrs))
        y = a[a.year == mid][["fips", "topic", "age_band", "sex", "rate", "ci_low", "ci_high"]]
        r = r.merge(y, on=["fips", "topic", "age_band", "sex"], how="left", validate="1:1")
        r["base"] = "mort_" + r.topic + "_" + r.age_band + np.where(r.sex == "all", "", "_" + r.sex)
        parts = {"": "mean", "_midyear": "rate"}
        w = pd.concat([r.pivot(index="fips", columns="base", values=col).add_suffix(sfx) for sfx, col in parts.items()], axis=1)
        ra = r[r.sex == "all"]
        w = pd.concat([w] + [ra.pivot(index="fips", columns="base", values=col).add_suffix(sfx) for sfx, col in {"_n_years": "count", "_midyear_lo": "ci_low", "_midyear_hi": "ci_high"}.items()], axis=1)
        w["acs_vintage"] = v; w["mort_mid_year"] = mid; wide.append(w.reset_index())
    return a, pd.concat(wide, ignore_index=True)

# ----------------------------------------------------------------------------------------------- reference data
def gazetteer():
    out = []
    for v, f in ((2010, "2010_Gaz_counties_national.zip"), (2014, "2014_Gaz_counties_national.zip"), (2019, "2019_Gaz_counties_national.zip")):
        z = zipfile.ZipFile("raw/ref_nat/" + f); g = pd.read_csv(z.open(z.namelist()[0]), sep="\t", dtype=str, encoding="latin-1"); g.columns = [c.strip() for c in g.columns]
        g = g[~g.USPS.isin(["PR"])].copy(); g["fips"] = unit(g.GEOID.str.zfill(5))
        for c in ("ALAND_SQMI", "INTPTLAT", "INTPTLONG"): g[c] = pd.to_numeric(g[c])
        big = g.sort_values("ALAND_SQMI", ascending=False).drop_duplicates("fips").set_index("fips")
        x = g.groupby("fips").agg(land_area_sqmi=("ALAND_SQMI", "sum"), state_abbr=("USPS", "first"), gaz_n=("GEOID", "size")).reset_index()
        x["intpt_lat"] = x.fips.map(big.INTPTLAT); x["intpt_lon"] = x.fips.map(big.INTPTLONG); x["acs_vintage"] = v; out.append(x)
    return pd.concat(out, ignore_index=True)

def static_refs(pop_w):
    """Time-invariant county attributes. pop_w: Series geoid -> population (2015-2019 ACS) used to choose the largest
    component of a combined unit (categorical attributes) and to weight PLACES prevalences."""
    def largest(df, col="geoid"):
        d = df.copy(); d["fips"] = unit(d[col]); d["w"] = d[col].map(pop_w).fillna(0)
        return d.sort_values("w", ascending=False).drop_duplicates("fips").set_index("fips")
    n = pd.read_excel("raw/ref_nat/NCHSURCodes2013-Past-Version.xlsx", dtype=str); n["geoid"] = n["FIPS code"].str.zfill(5)
    n = largest(n); lab6 = {1: "Large central metro", 2: "Large fringe metro", 3: "Medium metro", 4: "Small metro", 5: "Micropolitan", 6: "Noncore"}
    ref = pd.DataFrame({"nchs_ur_2013": pd.to_numeric(n["2013 code"], errors="coerce"), "nchs_ur_2006": pd.to_numeric(n["2006 code"], errors="coerce")})
    ref["nchs_ur_2013_label"] = ref.nchs_ur_2013.map(lab6); ref["metro_2013"] = ref.nchs_ur_2013 <= 4
    for tag, f in (("2013", "cbsa_list1_Feb_2013.xls"), ("2018", "cbsa_list1_Sep_2018.xls")):
        c = pd.read_excel("raw/ref_nat/" + f, header=2, dtype=str); c = c[c["FIPS State Code"].notna() & c["FIPS County Code"].notna()].copy()
        c["geoid"] = c["FIPS State Code"].str.zfill(2) + c["FIPS County Code"].str.zfill(3); c = c[~c.geoid.str.startswith("72")]
        c = largest(c); ty = c["Metropolitan/Micropolitan Statistical Area"].str.split().str[0]
        ref = ref.join(pd.DataFrame({f"cbsa_code_{tag}": c["CBSA Code"], f"cbsa_title_{tag}": c["CBSA Title"], f"cbsa_type_{tag}": ty,
                                     f"cbsa_central_outlying_{tag}": c["Central/Outlying County"], f"csa_code_{tag}": c["CSA Code"]}), how="left")
        ref[f"cbsa_type_{tag}"] = ref[f"cbsa_type_{tag}"].fillna("None")
    u = pd.read_excel("raw/ref_nat/PctUrbanRural_County_2010.xls", dtype=str); u["geoid"] = u.STATE.str.zfill(2) + u.COUNTY.str.zfill(3); u = u[~u.geoid.str.startswith("72")].copy()
    u["fips"] = unit(u.geoid); u[["POP_COU", "POP_URBAN"]] = u[["POP_COU", "POP_URBAN"]].apply(pd.to_numeric)
    g = u.groupby("fips")[["POP_COU", "POP_URBAN"]].sum(); ref = ref.join((100 * g.POP_URBAN / g.POP_COU).rename("pct_urban_2010"), how="outer").join(g.POP_COU.rename("pop_census_2010"))
    # PLACES 2020 release (wide)
    w = pd.read_parquet("raw/places_nat/places_county_2020release_wide.parquet"); w["geoid"] = w.countyfips.str.zfill(5); w["fips"] = unit(w.geoid)
    w["wt"] = pd.to_numeric(w.totalpopulation); meas = ["csmoking", "obesity", "diabetes", "lpa", "bphigh", "highchol", "binge", "sleep", "access2", "chd", "stroke"]
    cols = {}
    for m in meas:
        for src, sfx in (("adjprev", "aa"), ("crudeprev", "crude")):
            cols[f"places_r2020_{m}_{sfx}"] = pd.to_numeric(w[f"{m}_{src}"], errors="coerce")
        if m in ("csmoking", "obesity", "diabetes", "lpa"):
            ci = w[f"{m}_adj95ci"].str.extract(r"\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)").astype(float)
            cols[f"places_r2020_{m}_aa_lo"] = ci[0]; cols[f"places_r2020_{m}_aa_hi"] = ci[1]
    P = pd.DataFrame(cols); P["fips"] = w.fips.values; P["wt"] = w.wt.values
    wm = lambda d: pd.Series({c: np.average(d[c], weights=d.wt) if d[c].notna().all() else np.nan for c in cols})
    p20 = P.groupby("fips").apply(wm, include_groups=False); p20["places_r2020_n_components"] = P.groupby("fips").size()
    # PLACES 2021 release (long)
    l = pd.read_parquet("raw/places_nat/places_county_2021release_long.parquet"); l = l[l.locationid.str.len() == 5].copy()
    l["fips"] = unit(l.locationid); l["v"] = pd.to_numeric(l.data_value, errors="coerce"); l["wt"] = pd.to_numeric(l.totalpopulation)
    l["col"] = "places_r2021_" + l.measureid.str.lower() + np.where(l.datavaluetypeid == "AgeAdjPrv", "_aa", "_crude")
    l["vw"] = l.v * l.wt; g = l.groupby(["fips", "col"]); p21 = (g.vw.sum(min_count=1) / g.wt.sum()).unstack("col")
    ref = ref.join(p20, how="left").join(p21, how="left")
    ref["has_places_r2020"] = ref.places_r2020_csmoking_aa.notna(); ref["has_places_r2021"] = ref.places_r2021_csmoking_aa.notna()
    return ref.reset_index().rename(columns={"index": "fips"})

# ----------------------------------------------------------------------------------------------- assemble
CORE = ["car_hours_wk_per_adult16", "transit_hours_wk_per_adult16", "mort_cvd_35_64", "mort_cvd_65plus", "median_hh_income", "poverty_rate",
        "share_bachelors_plus", "share_nh_black", "share_hispanic", "unemployment_rate", "share_no_vehicle_hh", "pop_density", "share_age_65plus",
        "share_female", "nchs_ur_2013"]
PLACES_CORE = ["places_r2020_csmoking_aa", "places_r2020_obesity_aa", "places_r2020_diabetes_aa", "places_r2020_lpa_aa"]

def main():
    lab = labels(); parts = []; cals = []; comps = []
    for v in PERIODS:
        o, cal, comp = derive(v, lab); parts.append(o); cals.append(cal); comp["acs_vintage"] = v; comps.append(comp)
    acs = pd.concat(parts, ignore_index=True); comp = pd.concat(comps, ignore_index=True)
    ann, mw = mortality()
    gz = gazetteer()
    pop19 = pd.read_parquet(os.path.join(RAW, "acs5_2019_b01001.parquet")).set_index("geoid").B01001_E001
    pop10 = pd.read_parquet(os.path.join(RAW, "acs5_2010_b01001.parquet")).set_index("geoid").B01001_E001
    ref = static_refs(pop19.combine_first(pop10))
    d = acs.merge(mw, on=["fips", "acs_vintage"], how="outer", validate="1:1", indicator="_m_mort")
    d = d.merge(gz, on=["fips", "acs_vintage"], how="left", validate="1:1").merge(ref, on="fips", how="left", validate="m:1")
    d["in_acs"] = d._m_mort.isin(["both", "left_only"]); d["in_cdc_mortality"] = d._m_mort.isin(["both", "right_only"]); d = d.drop(columns="_m_mort")
    d["state_fips"] = d.fips.str[:2]
    reg = {s: (r, dv) for r, dd in REGION.items() for dv, ss in dd.items() for s in ss.split()}
    d["census_region"] = d.state_fips.map(lambda s: reg[s][0]); d["census_division"] = d.state_fips.map(lambda s: reg[s][1])
    cdc_names = ann.drop_duplicates("fips").set_index("fips").county_name_cdc
    d = d.rename(columns={"county_name_acs": "county_name"}); d["county_name_cdc"] = d.fips.map(cdc_names)
    d["pop_density"] = d.pop_total / d.land_area_sqmi
    d["fips_note"] = d.fips.map({u: "; ".join(sorted({f"{k}: {r}" for k, (uu, r) in XWALK.items() if uu == u})) for u in {x[0] for x in XWALK.values()}})
    d["complete_case_main"] = d[CORE].notna().all(axis=1)
    d["complete_case_main_places"] = d.complete_case_main & d[PLACES_CORE].notna().all(axis=1)
    first = ["fips", "period", "acs_vintage", "county_name", "state_fips", "state_abbr", "census_region", "census_division"]
    d = d[first + [c for c in d.columns if c not in first]].sort_values(["acs_vintage", "fips"]).reset_index(drop=True)
    assert not d.duplicated(["fips", "acs_vintage"]).any()
    d.to_parquet("national_county.parquet", index=False)
    ann.to_parquet("national_mortality_annual.parquet", index=False)
    os.makedirs("qc", exist_ok=True); pd.concat(cals, ignore_index=True).to_csv("qc/national_topbin_calibration.csv", index=False)
    xw = comp.rename(columns={"geoid": "acs_geoid", "name": "acs_name", "fips": "unit_fips"}); xw["changed"] = xw.acs_geoid != xw.unit_fips
    xw["reason"] = xw.acs_geoid.map(lambda g: XWALK.get(g, ("", ""))[1]); xw[["acs_vintage", "acs_geoid", "acs_name", "unit_fips", "changed", "reason"]].to_csv("national_county_crosswalk.csv", index=False)
    print(d.shape, ann.shape, d.groupby("period").size().to_dict(), flush=True)
    return d, ann

if __name__ == "__main__":
    main()
