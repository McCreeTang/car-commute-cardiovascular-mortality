"""Build the road-rage / aggressive-driving proxy tabulation and assessment from the CCRS grouped counts
(raw/crash/ccrs_grouped_study.parquet, written by acquire_ccrs.py).

Indicator groups are an OPERATIONAL definition by the analyst (CCRS has no road-rage or aggressive-driving field).
Primary collision factor violation text is parsed to a California Vehicle Code section number; free-text entries
that carry no section number are matched by keyword. Section descriptions are the analyst's reading of the Vehicle
Code and were not retrieved from an official legal source.

Writes road_rage_proxy_counts.csv (county x year) and road_rage_proxy_assessment.md.
Usage: python build_road_rage_proxy.py
"""
import re, datetime, numpy as np, pandas as pd

SEC = {"unsafe_speed": {"22350", "22349", "22348"}, "following_too_closely": {"21703"}, "unsafe_lane_change": {"21658"},
       "unsafe_passing": {str(s) for s in range(21750, 21760)}, "reckless_or_speed_contest": {"23103", "23104", "23105", "23109"},
       "unsafe_turn_or_signal": {"22107", "22108"}, "signal_or_stop_sign": {"21453", "22450"}}
SEC_DESC = {"unsafe_speed": "22350 basic speed law (unsafe speed for conditions); 22349 maximum speed limit; 22348 excessive speed",
            "following_too_closely": "21703 following too closely", "unsafe_lane_change": "21658 lane straddling / unsafe lane change",
            "unsafe_passing": "21750-21759 overtaking and passing", "reckless_or_speed_contest": "23103-23105 reckless driving; 23109 speed contest / exhibition of speed",
            "unsafe_turn_or_signal": "22107 unsafe turning movement or lane move without signal; 22108 signal duration",
            "signal_or_stop_sign": "21453 red signal; 22450 stop sign"}
KW = [("following_too_closely", r"FOLLOW|TAILGAT"), ("reckless_or_speed_contest", r"RECKLESS|SPEED CONTEST|EXHIBITION|STREET RAC"), ("unsafe_passing", r"PASSING|OVERTAK"),
      ("unsafe_lane_change", r"LANE CHANGE|UNSAFE LANE|LANE STRADDL"), ("unsafe_speed", r"SPEED"), ("unsafe_turn_or_signal", r"UNSAFE TURN|TURNING"), ("signal_or_stop_sign", r"RED LIGHT|RED SIGNAL|STOP SIGN")]
NARROW = ["unsafe_speed", "following_too_closely", "unsafe_lane_change", "unsafe_passing", "reckless_or_speed_contest"]

def classify(G):
    G = G.rename(columns={"Primary Collision Factor Code": "pcf_code", "Primary Collision Factor Violation": "pcf_violation", "HitRun": "hitrun", "Is Preliminary": "is_prelim"}).copy()
    v = G.pcf_violation.astype(object).where(G.pcf_violation.notna(), "").astype(str).str.strip()
    G["section"] = v.str.extract(r"^\D{0,3}(\d{4,5})(?:\.(\d+))?")[0]
    G["viol_state"] = np.where(v.eq("") | v.str.lower().isin(["none", "null", "nan"]), "blank", np.where(G.section.notna(), "parsed", "unparsed"))
    sec2cat = {s: c for c, ss in SEC.items() for s in ss}
    G["indicator"] = G.section.map(sec2cat); G["matched_by"] = np.where(G.indicator.notna(), "section", None)
    vu = v.str.upper()
    for c, pat in KW:
        hit = (G.viol_state == "unparsed") & G.indicator.isna() & vu.str.contains(pat, regex=True)
        G.loc[hit, "indicator"] = c; G.loc[hit, "matched_by"] = "keyword"
    G["indicator"] = G.indicator.fillna("other_or_none")
    return G

def county_year(G):
    CY = G.groupby(["county_fips", "county_name", "core9", "year", "indicator"]).n.sum().unstack().fillna(0).astype(int).reset_index()
    CY["all_crashes"] = CY[list(SEC) + ["other_or_none"]].sum(axis=1); CY["narrow_composite"] = CY[NARROW].sum(axis=1)
    hr = G[G.hitrun.notna()].groupby(["county_fips", "year"]).n.sum().rename("hit_and_run").reset_index()
    CY = CY.merge(hr, on=["county_fips", "year"], how="left"); CY["hit_and_run"] = CY.hit_and_run.fillna(0).astype(int)
    assert int(CY.all_crashes.sum()) == int(G.n.sum()) and not CY.duplicated(["county_fips", "year"]).any()
    return CY

def add_population(CY):
    """Approximate denominators: ACS 5-year county population, 2015-2019 for crash years <= 2019, 2020-2024 afterwards."""
    pop = {}
    for vint in (2019, 2024):
        d = pd.read_parquet(f"raw/acs/acs5_{vint}_b01001.parquet", columns=["GEO_ID", "sumlevel", "B01001_E001"])
        d = d[d.sumlevel == "050"]; pop[vint] = dict(zip(d.GEO_ID.str[-3:], d.B01001_E001))
    CY["pop_vintage"] = np.where(CY.year <= 2019, "ACS 2015-2019", "ACS 2020-2024")
    CY["population"] = [pop[2019 if y <= 2019 else 2024][f] for f, y in zip(CY.county_fips, CY.year)]
    CY["narrow_pct_of_crashes"] = (CY.narrow_composite / CY.all_crashes * 100).round(2)
    CY["narrow_per_100k_pop"] = (CY.narrow_composite / CY.population * 1e5).round(1)
    CY["crashes_per_100k_pop"] = (CY.all_crashes / CY.population * 1e5).round(1)
    return CY

def md_table(df):
    """Markdown table; formatting is decided per column dtype (row-wise iteration would upcast integers to floats)."""
    cols = list(df.columns)
    def fmt(c):
        s = df[c]
        if c == "year" or s.dtype == object: return s.astype(str).tolist()
        if pd.api.types.is_integer_dtype(s): return [f"{int(v):,}" for v in s]
        return [str(v) for v in s]
    cells = [fmt(c) for c in cols]
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    out += ["| " + " | ".join(col[i] for col in cells) + " |" for i in range(len(df))]
    return "\n".join(out)

if __name__ == "__main__":
    G = classify(pd.read_parquet("raw/crash/ccrs_grouped_study.parquet")); CY = add_population(county_year(G))
    CY.to_csv("road_rage_proxy_counts.csv", index=False)
    log = pd.read_csv("raw/crash/ccrs_query_log.csv"); tot = G.groupby("year").n.sum()
    Y = G.groupby(["year", "indicator"]).n.sum().unstack().fillna(0).astype(int)
    T = pd.DataFrame({"year": Y.index, "all crashes": tot.values, **{c.replace("_", " "): Y[c].values for c in NARROW}})
    T["narrow composite"] = Y[NARROW].sum(axis=1).values
    T = T.astype({c: int for c in T.columns})
    T["composite % of crashes"] = (T["narrow composite"] / T["all crashes"] * 100).round(1)
    T["unsafe speed % of composite"] = (Y["unsafe_speed"].values / T["narrow composite"] * 100).round(1)
    T["hit-and-run % of crashes"] = (G[G.hitrun.notna()].groupby("year").n.sum().reindex(Y.index).values / tot.values * 100).round(1)
    T["with latitude %"] = (log.set_index("year").with_latitude.reindex(Y.index).values / tot.values * 100).round(1)
    vs = (G.groupby(["year", "viol_state"]).n.sum().unstack().fillna(0).div(tot, axis=0) * 100).round(1)
    sp = G[G.indicator == "unsafe_speed"].groupby(G.section.fillna("keyword")).n.sum()
    kw = G[G.indicator != "other_or_none"].groupby(["year", "matched_by"]).n.sum().unstack().fillna(0); kwp = (kw["keyword"] / kw.sum(axis=1) * 100).round(1)
    rk = Y["reckless_or_speed_contest"]; small = CY.sort_values("all_crashes").iloc[0]
    # the flag is stored as the strings "True"/"False", so compare as text
    prelim = G[G.is_prelim.astype(str).str.lower() == "true"].groupby("year").n.sum().reindex(tot.index).fillna(0)
    cz = CY[CY.reckless_or_speed_contest == 0]
    C = CY[CY.year.isin([2019, 2024])].pivot(index="county_name", columns="year", values=["all_crashes", "narrow_pct_of_crashes", "narrow_per_100k_pop"])
    C.columns = [f"{a.replace('_', ' ')} {b}" for a, b in C.columns]; C = C.reset_index().rename(columns={"county_name": "county"})
    for c in C.columns:
        if c.startswith("all crashes"): C[c] = C[c].astype(int)
    state = __import__("json").load(open("raw/crash/ccrs_package_state.json"))
    missing_parties = sorted(set(range(2016, 2027)) - {int(m.group(1)) for n in state["resource_names"] for m in [re.match(r"^Parties_(\d{4})$", n)] if m})
    md = f"""# Road rage proxy assessment: California Crash Reporting System (CCRS)

Generated {datetime.date.today().isoformat()} by `build_road_rage_proxy.py`. Every number below is computed from the CCRS tables queried on data.ca.gov (package last modified {state['package_modified'][:10]}).

## Verdict

**Descriptive context only.** The CCRS data are not adequate as a road-rage exposure or outcome variable in the association models or the attributable-burden model. They can support a descriptive paragraph or supplementary figure on crash patterns in the study counties from 2016 onward, with the caveats below stated alongside.

## What was examined

- Source: California Highway Patrol, California Crash Reporting System, package `ccrs` on data.ca.gov. Three tables per year (Crashes, Parties, InjuredWitnessPassengers), years {int(tot.index.min())}-{int(tot.index.max())}. Only the Crashes tables were tabulated here.
- Field definitions: the publisher's "Raw Data Template" (CCRS raw data export layout, dated 9/27/2024).
- Geography: County Code is the county in which the crash occurred (publisher's definition); it is the alphabetical index of the 58 counties, verified against the recorded city names for all 15 study counties.
- Not examined: the Parties and InjuredWitnessPassengers tables (so no tabulation by driver age or at-fault party), and the four Caltrans "Crash Data on State Highway System" packages (2021-2024, state highways only), which were listed in the catalog but not opened.

## Is there a road-rage flag?

No. Neither the three CCRS tables (75, 49 and 22 fields in the 2019 tables) nor the publisher's layout document contains any field or value for road rage or aggressive driving. The closest fields are:

- `Primary Collision Factor Code`: A vehicle code violation, B other improper driving, C other than driver, D unknown, E fell asleep, dash not stated (publisher's definitions). Category A is {G[G.pcf_code == 'A'].n.sum() / G.n.sum() * 100:.1f}% of study-county crashes across all years.
- `Primary Collision Factor Violation`: free text holding the Vehicle Code section. It has {G.pcf_violation.nunique():,} distinct raw strings in the study counties; {vs['parsed'].min()}-{vs['parsed'].max()}% of crashes per year parse to a section number, {vs['blank'].min()}-{vs['blank'].max()}% are blank and {vs['unparsed'].min()}-{vs['unparsed'].max()}% are words without a section number (rising over time).
- `HitRun` (felony or misdemeanor), and in the Parties table `Other Associate Factor`, `Inattention` and `StatedAge`.

Any aggressive-driving indicator therefore has to be constructed by the analyst from violation sections. The grouping used here:

{chr(10).join(f"- `{k}`: {v}" for k, v in SEC_DESC.items())}

The "narrow composite" is the sum of the first five groups. Free-text entries without a section number were assigned by keyword; they are {kwp.min()}-{kwp.max()}% of indicator crashes per year. The section descriptions are the analyst's reading of the California Vehicle Code and were not retrieved from an official legal source in this work; they should be checked before publication.

## Counts, 15 study counties combined

{md_table(T)}

County-by-year counts for every indicator are in `road_rage_proxy_counts.csv` ({len(CY)} rows: {CY.county_fips.nunique()} counties x {CY.year.nunique()} years).

## Selected county values

Population denominators are approximate: ACS 5-year county population, 2015-2019 for crash years up to 2019 and 2020-2024 afterwards.

{md_table(C)}

## Why this is not adequate for modelling

1. **Definition.** There is no road-rage variable. The composite measures what an officer recorded as the primary cause of a crash that happened, not driver anger or hostile behaviour, and road-rage incidents that do not end in a reported crash are not in the data at all.
2. **Specificity.** Unsafe speed makes up {T['unsafe speed % of composite'].min()}-{T['unsafe speed % of composite'].max()}% of the narrow composite each year, and it is almost entirely section 22350, the basic speed law ({int(sp.get('22350', 0)):,} crashes over all years, against {int(sp.get('22349', 0) + sp.get('22348', 0)):,} for the maximum-speed sections). That citation is commonly the recorded primary factor for rear-end crashes in dense traffic, so the composite largely tracks congestion, which is the study's exposure. Using it as a mediator or outcome of long commutes would be close to circular.
3. **Sparse specific indicators.** The most specific group, reckless driving or speed contest, has {int(rk.min())}-{int(rk.max())} crashes per year across all 15 counties, and {len(cz)} of {len(CY)} county-years have none. The smallest county-year ({small.county_name}, {int(small.year)}) has {int(small.all_crashes):,} crashes in total.
4. **Coverage years.** CCRS on data.ca.gov starts in {int(tot.index.min())}; nothing is available for 2010-{int(tot.index.min()) - 1}, so the first part of the study window is uncovered. {int(tot.index.max())} is a partial year ({int(tot.loc[tot.index.max()]):,} crashes so far). The tables are still being updated, and the `Is Preliminary` flag is set on at most {prelim.max() / 1:,.0f} records in any year ({(prelim / tot * 100).max():.1f}% of that year's crashes, in {int((prelim / tot).idxmax())}), so it does not show how incomplete recent years are. The Parties table is missing for {', '.join(map(str, missing_parties)) or 'no year'}.
5. **Denominator.** No vehicle-miles-travelled or trip denominator was acquired, and crash counts depend on traffic volume, through traffic and reporting practice. County is the place of occurrence, not the driver's county of residence, so a commuter from an outer county who crashes in the core is counted in the core. Per-resident rates are therefore only a rough scale adjustment.
6. **Spatial resolution.** A latitude is recorded for {T['with latitude %'].min()}-{T['with latitude %'].max()}% of crashes per year, so tract-level assignment would be incomplete and probably not at random.
7. **Period effects.** Crash counts fell from {int(tot.loc[2019]):,} in 2019 to {int(tot.loc[2020]):,} in 2020, and the composite's share of crashes shifted from {T.set_index('year').loc[2019, 'composite % of crashes']}% to {T.set_index('year').loc[2020, 'composite % of crashes']}%, consistent with a change in traffic conditions and not obviously in driver behaviour.

## What it can support

- A descriptive statement of crash volume and the mix of recorded primary factors in the study counties, {int(tot.index.min())} onward, clearly labelled as crash-causation attributions.
- The hit-and-run share ({T['hit-and-run % of crashes'].min()}-{T['hit-and-run % of crashes'].max()}% of crashes per year) as a separate descriptive series.
- If age-specific context is wanted, the Parties table carries `StatedAge` and `IsAtFault`; that tabulation was not done here.

For the manuscript, driving stress and road rage are better treated as a mechanism discussed from the literature than as a measured variable.
"""
    open("road_rage_proxy_assessment.md", "w", encoding="utf-8").write(md)
    print("rows", len(CY), "| md chars", len(md))
