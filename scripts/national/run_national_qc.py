"""QC of the national county dataset. Writes national_data_qc_report.md and qc/*.csv.
Usage: python run_national_qc.py [path to the earlier Bay Area county_year_panel.parquet]"""
import os, sys, json, zipfile, datetime, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))      # the build script sits next to this one
import build_national_dataset as B

OUT = []
def P(*a): OUT.append(" ".join(str(x) for x in a))
def table(df, index=False, floatfmt=None):
    d = df.reset_index() if index else df.copy()
    if floatfmt:
        for c in d.select_dtypes("float").columns: d[c] = d[c].map(lambda x: "" if pd.isna(x) else format(x, floatfmt))
    P("| " + " | ".join(map(str, d.columns)) + " |"); P("|" + "---|" * len(d.columns))
    for r in d.itertuples(index=False): P("| " + " | ".join("" if (isinstance(x, float) and np.isnan(x)) else str(x) for x in r) + " |")
    P("")

def main(bay_path=None):
    os.makedirs("qc", exist_ok=True)
    d = pd.read_parquet("national_county.parquet"); a = pd.read_parquet("national_mortality_annual.parquet")
    xw = pd.read_csv("national_county_crosswalk.csv", dtype=str); cal = pd.read_csv("qc/national_topbin_calibration.csv")
    P("# National county dataset: QC report"); P("")
    P(f"Generated {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC by `run_national_qc.py`. Every number below was computed by that script from the saved files.")
    P(""); P(f"`national_county.parquet`: {len(d):,} rows x {d.shape[1]} columns. `national_mortality_annual.parquet`: {len(a):,} rows x {a.shape[1]} columns.")
    P("")
    # ------------------------------------------------------------------ 1 counts
    P("## 1. Row counts and keys"); P("")
    raw = xw.groupby("acs_vintage").agg(acs_counties=("acs_geoid", "nunique"), analysis_units=("unit_fips", "nunique")).reset_index()
    gz = {}
    for v, f in ((2010, "2010_Gaz_counties_national.zip"), (2014, "2014_Gaz_counties_national.zip"), (2019, "2019_Gaz_counties_national.zip")):
        z = zipfile.ZipFile("raw/ref_nat/" + f); g = pd.read_csv(z.open(z.namelist()[0]), sep="\t", dtype=str, encoding="latin-1"); g.columns = [c.strip() for c in g.columns]
        gz[v] = g[g.USPS != "PR"].assign(geoid=lambda x: x.GEOID.str.zfill(5))
    raw["gazetteer_counties"] = [len(gz[int(v)]) for v in raw.acs_vintage]
    raw["acs_not_in_gazetteer"] = [len(set(xw[xw.acs_vintage == v].acs_geoid) - set(gz[int(v)].geoid)) for v in raw.acs_vintage]
    raw["gazetteer_not_in_acs"] = [len(set(gz[int(v)].geoid) - set(xw[xw.acs_vintage == v].acs_geoid)) for v in raw.acs_vintage]
    raw["rows_in_dataset"] = [int((d.acs_vintage == int(v)).sum()) for v in raw.acs_vintage]
    raw["rows_with_acs"] = [int(((d.acs_vintage == int(v)) & d.in_acs).sum()) for v in raw.acs_vintage]
    raw["rows_with_cdc_mortality_unit"] = [int(((d.acs_vintage == int(v)) & d.in_cdc_mortality).sum()) for v in raw.acs_vintage]
    P("Expected number of counties = the count in the Census Gazetteer county file of the same vintage (50 states + DC), an independent file. The 2010 Gazetteer and the 2006-2010 ACS both carry Bedford city VA (3,143 counties); later vintages have 3,142. After mapping to the CDC mortality units there are 3,136 units in every period.")
    P(""); table(raw)
    st = d.groupby(["state_abbr", "period"]).size().unstack("period")
    exp = pd.concat({B.PERIODS[v][0]: gz[v].assign(u=B.unit(gz[v].geoid)).groupby("USPS").u.nunique() for v in gz}, axis=1)
    cmpst = st.join(exp, rsuffix="_expected"); cmpst.to_csv("qc/national_counts_by_state_period.csv")
    bad = int((st.reindex(exp.index).fillna(-1).to_numpy() != exp.to_numpy()).sum())
    P(f"Counts by state and period (51 states x 3 periods) against the Gazetteer-based expected number of units: **{bad} mismatches** (full table: `qc/national_counts_by_state_period.csv`). States: {d.state_abbr.nunique()}; missing state_abbr: {int(d.state_abbr.isna().sum())}.")
    P(""); P(f"Duplicate keys (fips + acs_vintage): **{int(d.duplicated(['fips', 'acs_vintage']).sum())}**. Duplicate keys in the annual mortality file (fips + year + topic + age_band + sex): **{int(a.duplicated(['fips', 'year', 'topic', 'age_band', 'sex']).sum())}**.")
    P(f"Units present in all three periods: {int((d.groupby('fips').size() == 3).sum()):,} of {d.fips.nunique():,}. Rows without ACS data: {int((~d.in_acs).sum())}; rows without a CDC mortality unit: {int((~d.in_cdc_mortality).sum())}.")
    P("")
    # ------------------------------------------------------------------ 2 county changes
    P("## 2. County changes (crosswalk)"); P("")
    P("ACS county codes that were mapped to a different analysis unit (`national_county_crosswalk.csv` lists every county). Counts were summed over components; medians of multi-county units are household-weighted means (flag `median_approx`); categorical attributes (rural-urban code, CBSA) come from the most populous component; PLACES prevalences are population-weighted means.")
    P(""); ch = xw[xw.changed == "True"].groupby(["acs_geoid", "acs_name", "unit_fips", "reason"]).acs_vintage.agg(lambda s: ", ".join(sorted(s))).reset_index().rename(columns={"acs_vintage": "acs_vintages"})
    table(ch[["acs_geoid", "acs_name", "unit_fips", "acs_vintages", "reason"]])
    P("Not affected in these vintages (checked against the ACS geography files): Broomfield County CO (08014, created 2001) is present in all three vintages and in the CDC series; Connecticut still has its eight counties (planning regions replace them only from the 2022 ACS); Valdez-Cordova Census Area AK (02261) was split in 2019 but the 2015-2019 ACS and the CDC series both still use 02261.")
    P(f"Checks: 08014 rows = {int((d.fips == '08014').sum())}; Connecticut units per period = {sorted(d[d.state_abbr == 'CT'].groupby('period').size().unique().tolist())}; 02261 rows = {int((d.fips == '02261').sum())}; 02063/02066 rows = {int(d.fips.isin(['02063', '02066']).sum())}.")
    P("")
    # ------------------------------------------------------------------ 3 mortality
    P("## 3. Mortality coverage"); P("")
    P(f"Annual file: {a.fips.nunique():,} units x {a.year.nunique()} years ({a.year.min()}-{a.year.max()}) x {a.topic.nunique()} causes x {a.age_band.nunique()} age bands x {a.sex.nunique()} sex strata = {len(a):,} rows. The download (race = Overall) was checked against the server-side row count.")
    sup = a.groupby(["sex", "age_band"]).agg(rows=("rate", "size"), suppressed=("suppressed", "sum"), units_ever_suppressed=("fips", lambda s: s[a.loc[s.index, "suppressed"]].nunique())).reset_index()
    sup["pct_suppressed"] = (100 * sup.suppressed / sup.rows).round(2); P(""); P("Suppressed values ('Value suppressed' in the source) by stratum, all causes and years:"); P(""); table(sup)
    ny = d.groupby("period")[["mort_cvd_35_64_n_years", "mort_cvd_65plus_n_years"]].agg(lambda s: ", ".join(f"{int(k)} years: {int(n)} units" for k, n in s.value_counts().sort_index().items()))
    P("Number of non-suppressed annual values behind each five-year mean (the mean is set to missing unless all five are present):"); P("")
    table(ny.reset_index().astype(str))
    inci = ((a.rate >= a.ci_low) & (a.rate <= a.ci_high)) | a.rate.isna()
    P(f"Rate inside its published confidence limits: {int(inci.sum()):,} of {len(a):,} rows ({int((~inci).sum())} outside). Rate range: {a.rate.min()} to {a.rate.max()} per 100,000.")
    P("")
    # ------------------------------------------------------------------ 4 missingness
    P("## 4. Missingness per variable"); P("")
    miss = d.drop(columns=["fips"]).isna().groupby(d.period).sum().T; miss["n_rows_per_period"] = int(len(d) / 3); miss.to_csv("qc/national_missingness_by_variable_period.csv")
    P(f"Full table for all {d.shape[1]} columns: `qc/national_missingness_by_variable_period.csv`. Columns with any missing value, grouped by pattern (number missing in 2006-2010 / 2010-2014 / 2015-2019, out of {int(len(d) / 3):,} units each):"); P("")
    m = miss[miss.drop(columns="n_rows_per_period").sum(axis=1) > 0].drop(columns="n_rows_per_period")
    m["pattern"] = m.astype(int).astype(str).agg(" / ".join, axis=1)
    grp = m.reset_index().groupby("pattern")["index"].agg(lambda s: ", ".join(f"`{x}`" for x in s)).reset_index().rename(columns={"index": "columns", "pattern": "missing (2006-10 / 2010-14 / 2015-19)"})
    grp["n_columns"] = grp["columns"].str.count("`") // 2; grp["columns"] = grp["columns"].map(lambda t: t if len(t) < 900 else t[:900] + " ... (see CSV)")
    table(grp[["missing (2006-10 / 2010-14 / 2015-19)", "n_columns", "columns"]])
    # ------------------------------------------------------------------ 5 range checks
    P("## 5. Range checks"); P("")
    share_cols = [c for c in d.columns if (c.startswith("share_") or c in ("poverty_rate", "unemployment_rate", "labor_force_participation", "unemployment_rate_b23025")) and not c.endswith("_moe")]
    checks = [("all share/rate columns in [0, 1] (%d columns)" % len(share_cols), int(((d[share_cols] < 0) | (d[share_cols] > 1)).sum().sum())),
              ("pop_18plus <= pop_16plus <= pop_total", int(((d.pop_18plus > d.pop_16plus) | (d.pop_16plus > d.pop_total)).sum())),
              ("workers_total <= pop_16plus", int((d.workers_total > d.pop_16plus).sum())),
              ("commuters_total <= workers_total", int((d.commuters_total > d.workers_total).sum())),
              ("car_commuters + transit_commuters <= commuters_total", int((d.car_commuters + d.transit_commuters > d.commuters_total).sum())),
              ("drivealone_commuters <= car_commuters", int((d.drivealone_commuters > d.car_commuters).sum())),
              ("car_agg_min_mid + transit_agg_min_mid <= all_agg_min_pub (tolerance 1e-6)", int((d.car_agg_min_mid + d.transit_agg_min_mid > d.all_agg_min_pub * (1 + 1e-6)).sum())),
              ("hours and minutes columns >= 0", int((d[[c for c in d.columns if ("hours_wk" in c or "min_per_day" in c or "agg_min" in c) and not c.endswith("_moe")]] < 0).sum().sum())),
              ("mean_tt_all_pub between 2 and 80 minutes", int(((d.mean_tt_all_pub < 2) | (d.mean_tt_all_pub > 80)).sum())),
              ("car_hours_wk_per_adult16 below 10", int((d.car_hours_wk_per_adult16 >= 10).sum())),
              ("mortality means > 0", int((d[[c for c in d.columns if c.startswith("mort_") and not c.endswith(("_n_years", "mid_year"))]] <= 0).sum().sum())),
              ("mid-year mortality inside its confidence limits", int(sum(((d[c] < d[c + "_lo"]) | (d[c] > d[c + "_hi"])).sum() for c in d.columns if c.endswith("_midyear") and c + "_lo" in d.columns))),
              ("65+ CVD rate > 35-64 CVD rate", int((d.mort_cvd_65plus <= d.mort_cvd_35_64).sum())),
              ("heart disease <= all CVD; CHD <= heart disease (both age bands, means)", int(sum(((d[f"mort_hd_{g}"] > d[f"mort_cvd_{g}"]) | (d[f"mort_chd_{g}"] > d[f"mort_hd_{g}"])).sum() for g in ("35_64", "65plus")))),
              ("nchs_ur_2013 in 1..6", int((~d.nchs_ur_2013.isin([1, 2, 3, 4, 5, 6])).sum())),
              ("PLACES prevalences in (0, 100)", int(((d[[c for c in d.columns if c.startswith("places_r") and not c.endswith("n_components")]] <= 0) | (d[[c for c in d.columns if c.startswith("places_r") and not c.endswith("n_components")]] >= 100)).sum().sum())),
              ("land_area_sqmi > 0 and pop_density > 0", int(((d.land_area_sqmi <= 0) | (d.pop_density <= 0)).sum())),
              ("pct_urban_2010 in [0, 100]", int(((d.pct_urban_2010 < 0) | (d.pct_urban_2010 > 100)).sum()))]
    table(pd.DataFrame(checks, columns=["check", "rows violating"]))
    nest = d[(d.mort_hd_35_64 > d.mort_cvd_35_64) | (d.mort_chd_35_64 > d.mort_hd_35_64)]
    P(f"Note on the nested-cause check: all {len(nest)} violating rows are in the 35-64 band and in very small units (median population {int(nest.pop_total.median()):,}); largest excess {float(max((nest.mort_hd_35_64 - nest.mort_cvd_35_64).max(), (nest.mort_chd_35_64 - nest.mort_hd_35_64).max())):.1f} per 100,000. The published values are model-smoothed estimates, not counts, so a sub-cause can exceed its parent where data are sparse. Values were left as published.")
    P("")
    u = d[d.unemployment_rate_b23025.notna()]
    P(f"Unemployment rate summed from B23001 against the published B23025 cells (2010-2014 and 2015-2019, {len(u):,} rows): maximum absolute difference {float((u.unemployment_rate - u.unemployment_rate_b23025).abs().max()):.2e}.")
    rng = d[["car_hours_wk_per_adult16", "drivealone_hours_wk_per_adult16", "transit_hours_wk_per_adult16", "all_hours_wk_per_adult16", "mean_tt_all_pub", "mean_tt_car_mid", "share_drive_alone", "share_wfh", "share_commute_45plus", "share_commute_60plus", "rake_factor",
             "mort_cvd_35_64", "mort_cvd_65plus", "median_hh_income", "median_home_value", "poverty_rate", "unemployment_rate", "share_uninsured", "pop_density", "pop_total"]]
    q = rng.groupby(d.period).describe(percentiles=[.01, .5, .99]).stack(0, future_stack=True)[["count", "min", "1%", "50%", "99%", "max"]].reset_index().rename(columns={"level_1": "variable"})
    q.to_csv("qc/national_range_summary.csv", index=False)
    P(""); P("Distribution of key variables by period (unweighted across units; full table `qc/national_range_summary.csv`):"); P("")
    table(q[q.variable.isin(["car_hours_wk_per_adult16", "transit_hours_wk_per_adult16", "mean_tt_all_pub", "share_drive_alone", "share_wfh", "rake_factor", "mort_cvd_35_64", "mort_cvd_65plus"])].sort_values(["variable", "period"]), floatfmt=".3f")
    top = d[d.median_home_value_topcoded.fillna(False)][["fips", "county_name", "period"]]
    P(f"Top-coded median home value rows: {len(top)}. Rows with `median_approx` (multi-county unit): {int(d.median_approx.sum())}.")
    P("")
    # ------------------------------------------------------------------ 6 exposure construction
    P("## 6. Exposure construction: suppression of published aggregates and validation of the estimate used"); P("")
    s = d.groupby("period")[["all_agg_pub_suppressed", "car_agg_pub_suppressed", "drivealone_agg_pub_suppressed", "transit_agg_pub_suppressed"]].agg(["sum", "mean"])
    s = pd.DataFrame({f"{c[0].replace('_agg_pub_suppressed', '')} ({'n' if c[1] == 'sum' else '%'})": (s[c].astype(int) if c[1] == "sum" else (100 * s[c]).round(1)) for c in s.columns}).reset_index()
    P("Units whose published aggregate travel time is suppressed (B08013 for all modes; B08136, or C08136 in 2006-2010, by mode). For multi-county units the published aggregate is missing if any component is suppressed."); P(""); table(s)
    popsup = d.assign(p=d.pop_total.where(d.car_agg_pub_suppressed, 0)).groupby("period").agg(p=("p", "sum"), t=("pop_total", "sum"))
    P("Share of population living in units with a suppressed car aggregate: " + "; ".join(f"{k} {100 * r.p / r.t:.2f}%" for k, r in popsup.iterrows()) + ".")
    P(""); P("Primary estimate (`*_agg_min_mid`: bin midpoints scaled to the county's published all-mode aggregate) against the published by-mode aggregate, in units where the latter exists and is positive. Compared as weekly hours per adult resident:"); P("")
    rows = []
    for per, x in d.groupby("period"):
        for k in ("car", "drivealone", "transit"):
            y = x[[f"{k}_hours_wk_per_adult16", f"{k}_hours_wk_per_adult16_pub", f"{k}_agg_min_midraw", f"{k}_agg_min_pub", "pop_16plus"]].dropna(); y = y[(y.iloc[:, 1] > 0) & (y.iloc[:, 0] > 0)]
            e, p_ = y.iloc[:, 0], y.iloc[:, 1]; rawh = y.iloc[:, 2] / y.pop_16plus * 2 * B.DAYS / 60; pe = 100 * (e / p_ - 1).abs()
            rows.append({"period": per, "mode": k, "units_compared": len(y), "pearson_r": round(e.corr(p_), 4), "slope (estimate on published)": round(np.polyfit(p_, e, 1)[0], 3),
                         "total estimate / total published": round(y.iloc[:, 0].mul(y.pop_16plus).sum() / y.iloc[:, 1].mul(y.pop_16plus).sum(), 4),
                         "median abs % diff": round(pe.median(), 2), "95th pct abs % diff": round(pe.quantile(.95), 2), "pearson_r unscaled midpoints": round(rawh.corr(p_), 4),
                         "slope unscaled midpoints": round(np.polyfit(p_, rawh, 1)[0], 3)})
    v = pd.DataFrame(rows); v.to_csv("qc/national_exposure_validation.csv", index=False); table(v)
    rows = []
    for vv, (per, _, _) in B.PERIODS.items():
        _, _, sE, _ = B.load_cells(vv); tt, blocks, ta, aggs = B.mode_blocks(vv); x = d[d.acs_vintage == vv]
        for k in ("car", "transit"):
            pub = sum(sE[B.cell(ta, c)] for c in aggs[k]).dropna(); est = x.groupby("state_fips")[f"{k}_agg_min_mid"].sum().reindex(pub.index); r = est / pub
            rows.append({"period": per, "mode": k, "states compared": len(pub), "sum of county estimates / published state aggregates": round(est.sum() / pub.sum(), 4), "lowest state ratio": round(r.min(), 3), "highest state ratio": round(r.max(), 3),
                         "share of state minutes in counties with suppressed aggregate (%)": round(100 * x[x[f"{k}_agg_pub_suppressed"] & x.state_fips.isin(pub.index)][f"{k}_agg_min_mid"].sum() / est.sum(), 1)})
    P("Second check, which also covers the counties whose own aggregate is suppressed: county estimates summed to states against the published STATE aggregates by mode (state aggregates are published for all states except Wyoming in 2010-2014 and 2015-2019):"); P("")
    table(pd.DataFrame(rows))
    rel = d.assign(cv=d.car_hours_wk_per_adult16_moe / 1.645 / d.car_hours_wk_per_adult16, size=pd.cut(d.pop_total, [0, 5000, 20000, 100000, 1e9], labels=["< 5,000", "5,000-19,999", "20,000-99,999", "100,000+"]))
    rt = rel.groupby(["period", "size"], observed=True).agg(units=("cv", "size"), median_cv_pct=("cv", lambda s: round(100 * s.median(), 1)), units_cv_over_30pct=("cv", lambda s: int((s > 0.30).sum()))).reset_index().rename(columns={"size": "population"})
    P("Sampling error of the primary exposure (`car_hours_wk_per_adult16`): approximate coefficient of variation = (margin of error / 1.645) / estimate, by population size. The margin of error uses Census approximation formulas and is conservative (bin margins treated as independent)."); P(""); table(rt)
    zm = {}
    for vv, tb in ((2010, "c08134"), (2014, "b08134"), (2019, "b08134")):
        t = pd.read_parquet(f"raw/acs_nat/acs5_{vv}_{tb}.parquet"); t = t[t.sumlevel == "050"]; zm[vv] = float(np.median(t.filter(regex="_M").to_numpy()[t.filter(regex="_E").to_numpy() == 0]))
    P(f"The larger values for small units in 2006-2010 reflect the published margins of zero-estimate cells, which are much larger in that file (median {zm[2010]:.0f}) than in 2010-2014 ({zm[2014]:.0f}) or 2015-2019 ({zm[2019]:.0f}); they do not indicate a smaller sample."); P("")
    P("Diagnostics behind the open-ended 60+ bin assumption (75 minutes for car, 80 for transit; `qc/national_topbin_calibration.csv`). `top_bin_mean_matching_state_totals` is the 60+ mean that would be needed if the closed-bin midpoints were exact; values below 60 show that the midpoints overstate (reported times heap at 10, 15, 20, 30, 45), which is why the midpoint minutes are scaled to the published county total rather than used directly. `bounded_ls_top_bin_*` is the 60+ coefficient of a bounded least-squares fit of the published aggregates on the nine bin counts."); P("")
    table(cal, floatfmt=".2f")
    # ------------------------------------------------------------------ 7 mean travel time
    P("## 7. Derived mean travel time against the published ACS mean"); P("")
    P("Published mean = published aggregate travel time (B08013) / workers who did not work at home (B08303), the definition of the ACS mean travel time to work. The ACS data-profile table itself (DP03) could not be queried because the Census API needs a key. Derived mean = unscaled bin midpoints from the mode-by-travel-time table (`mean_tt_all_midraw`, 60+ bin at 75 or 80 minutes); it is an independent calculation from different table cells. The primary exposure does not use the unscaled value.")
    P(""); x = d[d.acs_vintage == 2019]; big = x.nlargest(8, "pop_total"); small = x[(x.pop_total > 20000) & (x.pop_total < 60000)].sort_values("fips").iloc[::150].head(6)
    t7 = pd.concat([big, small])[["fips", "county_name", "pop_total", "mean_tt_all_pub", "mean_tt_all_pub_moe", "mean_tt_all_midraw", "rake_factor"]].copy()
    t7["difference (derived - published)"] = t7.mean_tt_all_midraw - t7.mean_tt_all_pub; t7["pop_total"] = t7.pop_total.astype(int)
    P(f"2015-2019, {len(t7)} counties (the eight most populous and six mid-sized counties taken at fixed intervals of the FIPS-sorted list):"); P(""); table(t7, floatfmt=".2f")
    rows = []
    for per, x in d.groupby("period"):
        df = (x.mean_tt_all_midraw - x.mean_tt_all_pub).dropna()
        rows.append({"period": per, "units": len(df), "pearson_r": round(x.mean_tt_all_midraw.corr(x.mean_tt_all_pub), 4), "mean difference (min)": round(df.mean(), 2), "median abs difference (min)": round(df.abs().median(), 2),
                     "95th pct abs difference (min)": round(df.abs().quantile(.95), 2), "within published MOE (%)": round(100 * (df.abs() <= x.mean_tt_all_pub_moe.reindex(df.index)).mean(), 1)})
    P("All units:"); P(""); table(pd.DataFrame(rows))
    # ------------------------------------------------------------------ 8 Bay Area
    P("## 8. Bay Area counties against the earlier Bay Area county panel"); P("")
    if bay_path and os.path.exists(bay_path):
        bay = pd.read_parquet(bay_path); bay["fips"] = "06" + bay.county_fips.astype(str).str.zfill(3)
        pairs = {"acs5_pop_total": "pop_total", "acs5_commuters_total": "commuters_total", "acs5_mean_commute_min": "mean_tt_all_pub", "acs5_share_drive_alone": "share_drive_alone", "acs5_share_wfh": "share_wfh",
                 "acs5_share_commute_60plus": "share_commute_60plus", "acs5_share_commute_90plus": "share_commute_90plus", "acs5_median_hh_income": "median_hh_income", "acs5_median_home_value": "median_home_value"}
        b = bay[bay.year.isin([2014, 2019])].merge(d, left_on=["fips", "year"], right_on=["fips", "acs_vintage"], how="left", validate="1:1"); rows = []
        for bc, nc in pairs.items():
            df = (b[bc] - b[nc]).abs(); moe = b.get(bc + "_moe")
            rows.append({"bay_area_panel_column": bc, "national_column": nc, "county-periods compared": int(df.notna().sum()), "max abs difference": float(df.max()),
                         "max abs relative difference": float((df / b[bc].abs()).max()), "within Bay Area panel MOE": "n/a" if moe is None else f"{int((df <= moe).sum())} of {int(df.notna().sum())}"})
        P(f"The earlier panel (`county_year_panel.parquet`) holds ACS 5-year county estimates for {bay.fips.nunique()} California counties (9 Bay Area + 6 adjacent) at 2014 and 2019, built from the same Census summary files through a different script. Matched county-periods: {int(b.pop_total.notna().sum())} of {len(b)}."); P("")
        table(pd.DataFrame(rows))
        mc = [c for c in bay.columns if c.startswith("mort_") and "majorcvd" not in c]; bl = bay[["fips", "year"] + mc].melt(["fips", "year"], var_name="col", value_name="bay").dropna()
        bl[["topic", "age_band"]] = bl.col.str.extract(r"mort_([a-z]+)_(35_64|65plus)")
        j = bl.merge(a[a.sex == "all"], on=["fips", "year", "topic", "age_band"], how="left", validate="1:1")
        P(f"Annual mortality (5 causes x 2 age bands, {int(j.year.min())}-{int(j.year.max())}): {len(j):,} county-year values in the Bay Area panel, {int(j.rate.notna().sum()):,} matched in the national annual file, maximum absolute difference {float((j.bay - j.rate).abs().max())}.")
        core9 = bay[bay.core9].fips.unique() if "core9" in bay.columns else []
        t8 = d[d.fips.isin(core9)].pivot(index=["fips", "county_name"], columns="period", values="car_hours_wk_per_adult16").round(3).reset_index()
        P(""); P("For reference, the primary exposure (`car_hours_wk_per_adult16`) of the nine Bay Area counties:"); P(""); table(t8)
    else:
        P("Bay Area panel not supplied to the QC script; check NOT run."); P("")
    # ------------------------------------------------------------------ 9 coverage
    P("## 9. Population coverage"); P("")
    stt = {}
    for v in B.PERIODS:
        t = pd.read_parquet(f"raw/acs_nat/acs5_{v}_b01001.parquet"); stt[B.PERIODS[v][0]] = (float(t[t.sumlevel == "040"].B01001_E001.sum()), float(t[t.sumlevel == "050"].B01001_E001.sum()))
    rows = []
    for per, x in d.groupby("period"):
        tot = x.pop_total.sum()
        rows.append({"period": per, "units": len(x), "US population, sum of state estimates": int(stt[per][0]), "sum of county estimates": int(stt[per][1]), "sum over dataset rows": int(tot),
                     "complete_case_main rows": int(x.complete_case_main.sum()), "population share (%)": round(100 * x.pop_total[x.complete_case_main].sum() / tot, 3),
                     "complete_case_main_places rows": int(x.complete_case_main_places.sum()), "population share with PLACES (%)": round(100 * x.pop_total[x.complete_case_main_places].sum() / tot, 3)})
    P("`complete_case_main` requires: " + ", ".join(f"`{c}`" for c in B.CORE) + ". `complete_case_main_places` adds " + ", ".join(f"`{c}`" for c in B.PLACES_CORE) + " (PLACES 2020 release, BRFSS 2018; contemporaneous with 2015-2019 only)."); P("")
    table(pd.DataFrame(rows))
    inc = d[~d.complete_case_main]; why = {c: int(inc[c].isna().sum()) for c in B.CORE if inc[c].isna().any()}
    P(f"Rows that are not complete cases: {len(inc)}; missing variable counts among them: {why}.")
    P("Units never complete: " + ", ".join(f"{f} {n}" for f, n in d[~d.complete_case_main].drop_duplicates("fips")[["fips", "county_name"]].head(60).itertuples(index=False)) + ("." if d[~d.complete_case_main].fips.nunique() <= 60 else f" ... ({d[~d.complete_case_main].fips.nunique()} units in total)."))
    P("")
    # ------------------------------------------------------------------ 10 classification coverage
    P("## 10. Rural-urban classification, CBSA and PLACES coverage"); P("")
    x = d[d.acs_vintage == 2019]
    n = x.groupby(["nchs_ur_2013", "nchs_ur_2013_label"]).agg(units=("fips", "size"), population=("pop_total", "sum"), car_hours_median=("car_hours_wk_per_adult16", "median"), transit_hours_median=("transit_hours_wk_per_adult16", "median")).reset_index()
    n["population"] = n.population.astype(int); n["nchs_ur_2013"] = n.nchs_ur_2013.astype(int)
    P("NCHS 2013 Urban-Rural Classification (2015-2019 rows; exposure medians are descriptive only):"); P(""); table(n, floatfmt=".3f")
    P(f"CBSA membership (2015-2019 rows): February 2013 delineation: { {k: int(n) for k, n in x.cbsa_type_2013.value_counts().items()} }; September 2018 delineation: { {k: int(n) for k, n in x.cbsa_type_2018.value_counts().items()} }.")
    P(f"PLACES 2020 release (BRFSS 2018): {int(x.has_places_r2020.sum()):,} of {len(x):,} units. PLACES 2021 release (BRFSS 2019): {int(x.has_places_r2021.sum()):,} of {len(x):,} units; missing by state: { {k: int(n) for k, n in x[~x.has_places_r2021].state_abbr.value_counts().items()} }.")
    P("")
    # ------------------------------------------------------------------ 0 coverage shortfalls (placed first)
    x19 = d[d.acs_vintage == 2019]; sup = d.groupby("period")[["car_agg_pub_suppressed", "transit_agg_pub_suppressed"]].mean().mul(100).round(1)
    fb = pd.read_csv("raw/acs_nat/acs5_nat_bundle_fallbacks_2014.csv") if os.path.exists("raw/acs_nat/acs5_nat_bundle_fallbacks_2014.csv") else pd.DataFrame()
    S = ["## 0. Where coverage is less than, or different from, what was requested", "",
         f"1. **Analysis units, not raw counties.** The CDC mortality series has {a.fips.nunique():,} county units. The 3,143 (2006-2010) or 3,142 (later) ACS counties of the 50 states and DC were mapped onto them: Bedford city VA is merged into Bedford County, and eight south-east Alaska boroughs/census areas form two combined units (02901, 02902). No county was dropped. Puerto Rico and the territories are not included (not requested).",
         "2. **Tables B08134 and B08136 do not exist for 2006-2010.** The collapsed tables C08134 and C08136 were used instead (total, drove alone, carpooled, public transit, other). Car and transit measures are unaffected; no finer sub-modes exist for that period.",
         "3. **Published aggregate travel time by mode is suppressed for many units**: car " + ", ".join(f"{sup.car_agg_pub_suppressed[p]}% ({p})" for p in sup.index) + "; transit " + ", ".join(f"{sup.transit_agg_pub_suppressed[p]}% ({p})" for p in sup.index) + ". The primary exposure therefore uses bin-midpoint minutes scaled to each county's published all-mode aggregate (section 6), which exists for all but one unit-period (next item).",
         f"4. **One unit lacks the all-mode aggregate too**: " + "; ".join(f"{r.county_name} ({r.fips}), {r.period}, population {int(r.pop_total)}" for r in d[d.agg_scaled_with_median_factor].itertuples()) + ". Its midpoint minutes were scaled by the median factor of the period (flag `agg_scaled_with_median_factor`).",
         "5. **Health-insurance coverage is missing for 2006-2010** (table B27001 is not in that file; the question began in 2008). `share_uninsured` and `share_uninsured_18_64` are available for 2010-2014 and 2015-2019 only, and the adult band is 18-64 in 2010-2014 but 19-64 in 2015-2019.",
         f"6. **Mortality is suppressed in the source for small units in every year**: {int(x19.mort_cvd_35_64.isna().sum())} units for ages 35-64 and {int(x19.mort_cvd_65plus.isna().sum())} units for ages 65+ (both sexes); by sex {int(x19.mort_cvd_35_64_men.isna().sum())}/{int(x19.mort_cvd_35_64_women.isna().sum())} units (men/women, 35-64) and {int(x19.mort_cvd_65plus_men.isna().sum())}/{int(x19.mort_cvd_65plus_women.isna().sum())} units (65+). The units without a 65+ rate have 2015-2019 populations between {int(x19[x19.mort_cvd_65plus.isna()].pop_total.min()):,} and {int(x19[x19.mort_cvd_65plus.isna()].pop_total.max()):,} (median {int(x19[x19.mort_cvd_65plus.isna()].pop_total.median()):,}). Complete-case rows cover {100 * x19.pop_total[x19.complete_case_main].sum() / x19.pop_total.sum():.2f}% of the 2015-2019 population (section 9).",
         "7. **Mortality scope.** Only all-races rows (both sexes, men, women) were downloaded; the race-specific strata of the source were not. The annual file also carries 1999 (published in the same series) in addition to the requested 2000-2019. Rates are model-smoothed and age-standardized within band; there are no counts and no other age bands.",
         f"8. **PLACES is not period-matched.** County PLACES starts with the 2020 release (BRFSS 2018; 2017 for high blood pressure and cholesterol). The same values are attached to all three period rows; they are contemporaneous with 2015-2019 only. The 2020 release is the main set ({int(x19.has_places_r2020.sum()):,} of {len(x19):,} units); the 2021 release (BRFSS 2019) is also included but lacks the {int((~x19.has_places_r2021).sum())} New Jersey counties. PLACES values are model-based.",
         "9. **Rural-urban classification**: NCHS 2013 (and 2006) codes for every unit, obtained from ftp.cdc.gov after access to www.cdc.gov and ftp.cdc.gov was granted (the files have moved from www.cdc.gov to ftp.cdc.gov). The USDA Rural-Urban Continuum Codes were not downloaded (www.ers.usda.gov is not reachable and was not needed). Census 2010 percent urban and population density are included as well. All are time-invariant in the file.",
         "10. **CBSA membership**: February 2013 and September 2018 delineations. No delineation contemporaneous with 2006-2010 (December 2009) was added.",
         "11. **Published mean travel time**: taken as published aggregate / published universe (B08013 / B08303). The data-profile table (DP03) could not be queried because the Census API requires a key.",
         ("12. **One source file came from a different Census file on the same host.** " + "; ".join(f"{r.state} {r.vintage} sequence {r.sequence}" for r in fb.itertuples()) + ": the per-sequence zip is rejected by the www2.census.gov firewall, so its two members were read from the Census Bureau's whole-state bundle (`5_year_by_state/<State>_All_Geographies_Not_Tracts_Block_Groups.zip`). This sequence holds B25077 (median home value).") if len(fb) else "12. No source-file fallback was needed.",
         "13. **Dollar amounts are nominal** (2010, 2014 and 2019 dollars); no price index was applied.",
         "14. **The exposure measures commuting only.** The ACS asks about the usual journey to work; non-commute driving, commute days per week (assumed 4.5) and time as a car passenger versus driver (other than drove-alone versus carpool) are not observed.", ""]
    head, rest = OUT[:6], OUT[6:]
    links = json.load(open("artifact_links.json")) if os.path.exists("artifact_links.json") else {}     # filename -> artifact link marker
    F = ["## Files", ""] + [f"- [{k}]({v})" for k, v in links.items()] + [""] if links else []
    open("national_data_qc_report.md", "w", encoding="utf-8").write("\n".join(head + S + rest + F))
    return d, a

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
