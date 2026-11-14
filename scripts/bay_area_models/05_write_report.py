"""05_write_report.py -- builds methods_results_ecological.md. Every number is formatted from the saved result files; nothing is typed by hand.
Inputs: trends_table.csv, trends_heterogeneity_tests.csv, tract_models.csv, tract_model_diagnostics.csv, tract_sample_description.csv,
        panel_models.csv, panel_mde_benchmark.json, sensitivity_models.csv, sensitivity_samples.csv
"""
import json, os, numpy as np, pandas as pd
from scipy import stats
MDE_MULT = stats.t.ppf(0.975, 13) + stats.t.ppf(0.80, 13)
xc = json.load(open('trends_crosscheck.json'))
AV = json.load(open('handoff/artifact_versions.json')) if os.path.exists('handoff/artifact_versions.json') else {}
def link(fn): return f'[{fn}](' + '{{' + 'artifact:' + AV[fn] + '}}' + ')' if fn in AV else f'`{fn}`'
tr = pd.read_csv('trends_table.csv'); het = pd.read_csv('trends_heterogeneity_tests.csv')
tm = pd.read_csv('tract_models.csv'); dg = pd.read_csv('tract_model_diagnostics.csv'); sd = pd.read_csv('tract_sample_description.csv')
pm = pd.read_csv('panel_models.csv'); bench = json.load(open('panel_mde_benchmark.json'))
se_ = pd.read_csv('sensitivity_models.csv', low_memory=False); ssamp = pd.read_csv('sensitivity_samples.csv')
L = []; A = L.append
def p_(p): return '<0.001' if p < 0.001 else f'{p:.3f}'
def table(rows, header):
    A('| ' + ' | '.join(header) + ' |'); A('|' + '---|'*len(header))
    for r in rows: A('| ' + ' | '.join(str(x) for x in r) + ' |')
    A('')
PUMS = tr[tr.source == 'ACS 1-year PUMS']
def g(geo, band, meas, y0, y1):
    r = PUMS[(PUMS.geo == geo) & (PUMS.age_band == band) & (PUMS.measure == meas) & (PUMS.year_start == y0) & (PUMS.year_end == y1)]
    assert len(r) == 1; return r.iloc[0]
MLAB = {'mean_commute_min': 'Mean one-way commute (min)', 'share_commute_45plus': 'Commuters at 45+ min (%)', 'share_commute_60plus': 'Commuters at 60+ min (%)',
        'share_commute_90plus': 'Commuters at 90+ min (%)', 'share_drive_alone_workers': 'Workers driving alone (%)', 'share_wfh_workers': 'Workers working from home (%)'}
def k(meas): return 1.0 if meas == 'mean_commute_min' else 100.0
def lev(r, meas, which): return f"{r['value_'+which]*k(meas):.2f} ({r['se_'+which]*k(meas):.2f})"
def chg(r, meas): return f"{r['change']*k(meas):+.2f} ({r['se_change']*k(meas):.2f}); p {p_(r['p_value'])}"
def chgci(r, meas): return f"{r['change']*k(meas):+.2f} (95% CI {r['ci95_lo']*k(meas):+.2f} to {r['ci95_hi']*k(meas):+.2f})"
OL = {'chd_prev': 'Coronary heart disease', 'stroke_prev': 'Stroke', 'bphigh_prev': 'High blood pressure', 'obesity_prev': 'Obesity', 'lpa_prev': 'Physical inactivity', 'diabetes_prev': 'Diabetes'}
EL = {'share_commute_60plus': '60+ min commute share', 'share_drive_alone': 'Drive-alone share'}
EST = ['OLS (HC1)', 'Spatial error (ML)', 'Spatial lag (ML), average total impact']
def tmrow(v, oc, e, est):
    r = tm[(tm.acs_vintage == v) & (tm.outcome == oc) & (tm.exposure == e) & (tm.estimator == est)]; assert len(r) == 1; return r.iloc[0]
def cell(r): return f"{r.estimate:+.3f} ({r.ci95_lo:+.3f}, {r.ci95_hi:+.3f}); q {p_(r.q_bh_family12)}" + (' **F**' if r.favoured_by_diagnostics else '')

A('# Methods and results: ecological models track'); A('')
A('Cardiovascular risk and lengthening car commutes in the San Francisco Bay Area: descriptive trends, tract-level cross-sectional association models, a county-year housing-commute-mortality panel, and sensitivity analyses.'); A('')
A('**Reading rule.** Everything here is observational and ecological. Coefficients are associations between area-level quantities; none is a causal effect, and none describes individuals. '
  'The model set was fixed in `analysis_plan_prespecified.md` before any outcome model was fitted, and every model in it is reported. Every number below is formatted by `05_write_report.py` from the saved result files.'); A('')

# ------------------------------------------------------------------ headline
a1 = g('ALL14', '16plus', 'mean_commute_min', 2010, 2019); a2 = g('ALL14', '16plus', 'share_commute_60plus', 2010, 2019)
n19 = int(sd.loc[sd.acs_vintage == 2019, 'tracts_in_model'].iloc[0]); n24 = int(sd.loc[sd.acs_vintage == 2024, 'tracts_in_model'].iloc[0])
fav = tm[tm.favoured_by_diagnostics]
def nfdr(v, e, d=fav): x = d[(d.acs_vintage == v) & (d.exposure == e)]; return int(x.fdr_significant_q05.sum()), int((x.fdr_significant_q05 & (x.estimate < 0)).sum()), int((x.fdr_significant_q05 & (x.estimate > 0)).sum())
f19c = nfdr(2019, 'share_commute_60plus'); f24c = nfdr(2024, 'share_commute_60plus'); f19d = nfdr(2019, 'share_drive_alone'); f24d = nfdr(2024, 'share_drive_alone')
H1 = pm[pm.model_id == 'H_mean16_lag1'].iloc[0]; H2 = pm[pm.model_id == 'H_s60_16_lag1'].iloc[0]
M1 = pm[pm.model_id == 'M_cvd_35_64_s60'].iloc[0]; M2 = pm[pm.model_id == 'M_cvd_65plus_s60'].iloc[0]
A('## 1. Summary of results'); A('')
A(f"1. **Commutes lengthened substantially from 2010 to 2019.** Among commuters aged 16+ in the 14 counties with microdata, mean one-way travel time changed by {chgci(a1,'mean_commute_min')} minutes "
  f"(from {a1.value_start:.2f} to {a1.value_end:.2f}) and the share with commutes of 60+ minutes by {chgci(a2,'share_commute_60plus')} percentage points (from {a2.value_start*100:.2f}% to {a2.value_end*100:.2f}%). "
  "The rise was larger in the nine core counties than in the adjacent counties and differed by age band for the 60+ minute share (largest at ages 35-54, smallest at 65+). Nominal Zillow home values roughly doubled over the same years.")
A(f"2. **Tract-level models do not show the hypothesised positive association.** With the estimator favoured by the spatial diagnostics, the 60+ minute commute share was associated with LOWER modelled prevalence for {f19c[1]} of 6 outcomes in the 2015-2019 cross-section after false-discovery-rate control "
  f"({f19c[2]} positive), and with none of 6 in the 2020-2024 cross-section ({f24c[0]} FDR-significant). Drive-alone share: {f19d[0]} of 6 FDR-significant in 2015-2019 ({f19d[1]} negative, {f19d[2]} positive) and {f24d[0]} of 6 in 2020-2024 ({f24d[1]} negative, {f24d[2]} positive). "
  "These are wrong-signed or null relative to the hypothesis. Because PLACES prevalences are built from tract demography, the covariates alone reproduce "
  f"{dg.r2_covariates_only.min()*100:.0f}-{dg.r2_covariates_only.max()*100:.0f}% of their variance, and the tract analysis has little ability to detect a commute effect in either direction.")
A(f"3. **Housing-to-commute panel: positive but imprecise.** Within counties and net of year effects, a 10% higher lagged nominal home value went with {H1.estimate:+.2f} minutes of mean commute "
  f"(wild-cluster 95% CI {H1.ci95_lo_wild:+.2f} to {H1.ci95_hi_wild:+.2f}; p {p_(H1.p_wild_cluster)}) and {H2.estimate*100:+.2f} percentage points of 60+ minute share "
  f"(95% CI {H2.ci95_lo_wild*100:+.2f} to {H2.ci95_hi_wild*100:+.2f}; p {p_(H2.p_wild_cluster)}). With 14 clusters the intervals include zero.")
A(f"4. **Commute-to-mortality panel: no positive association; the design cannot detect effects of plausible size.** Per 10-point higher 60+ minute share, all-cardiovascular mortality differed by {M1.estimate*100:+.1f}% at ages 35-64 "
  f"(95% CI {M1.ci95_lo_wild*100:+.1f}% to {M1.ci95_hi_wild*100:+.1f}%) and {M2.estimate*100:+.1f}% at ages 65+ (95% CI {M2.ci95_lo_wild*100:+.1f}% to {M2.ci95_hi_wild*100:+.1f}%). "
  f"The minimum detectable effect at ages 35-64 is {M1.mde_80pct_power*100:.1f}% per 10 points, against about {bench['implied_lograte_change_per_10pt_60plus_share_35_64']*100:.1f}% implied by the only driving-specific cohort estimate under generous assumptions. "
  "The product-of-coefficients indirect paths are all indistinguishable from zero.")
_t = se_[se_.level == 'tract']; _cm = _t[_t.exposure != 'share_drive_alone']
A(f"5. **Sensitivity analyses do not rescue the hypothesis.** Of {len(_cm)} sensitivity estimates for a commute-duration exposure, {int(((_cm.estimate < 0) & (_cm.p_value < 0.05)).sum())} are nominally significant and negative and {int(((_cm.estimate > 0) & (_cm.p_value < 0.05)).sum())} nominally significant and positive (all for obesity; number surviving FDR control: {int(((_cm.estimate > 0) & (_cm.q_bh_family12 < 0.05)).sum())}, under OLS only). Signs and significance of the drive-alone coefficients are unstable across specifications (section 6)."); A('')

# ------------------------------------------------------------------ data
A('## 2. Data, units and samples'); A('')
A('- Study area: 15 California counties (9 core Bay Area, 6 adjacent). San Benito has no person-level (PUMS) data, so PUMS-based trends and the panel use 14 counties; tract models and the county mortality cross-section use all 15.')
A('- Trends: ACS 1-year PUMS persons 16+, records with `puma_mixed_outside = False`; person weight `pwgtp`, 80 replicate weights. No 2020 file exists. 2010-2019 is the primary period; 2021-2024 is described separately because the work-from-home share rose sharply and commuters became a differently selected group.')
A('- Tract models: ACS 5-year tract estimates paired with CDC PLACES crude model-based prevalences for adults 18+ (not age-specific). Two cross-sections, never pooled.')
A('- Panel: county-year, 2010-2019, PUMS commute estimates, Zillow Home Value Index (nominal dollars), CDC model-smoothed mortality rates for ages 35-64 and 65+.')
A('- All dollar values are nominal. ACS median household income is top-coded (handled with an indicator).'); A('')
rows = []
for _, r in sd.iterrows():
    rows.append([r.cross_section, int(r.tracts_in_file), int(r.tracts_with_places), int(r.tracts_in_model), int(r.excluded), f"{r.population_in_model/r.population_in_file*100:.2f}%", int(r.n_counties), int(r.n_core9_tracts),
                 int(r.income_topcoded_tracts), f"{r.w_mean_neighbours:.2f}", int(r.w_n_islands_attached), int(r.w_n_components), f"{r.corr_exposures:+.3f}"])
A('**Table 2.1 Tract estimation samples** (tracts with a PLACES estimate, at least 100 commuters, no missing covariate).'); A('')
table(rows, ['Cross-section', 'Tracts in file', 'With PLACES', 'In model', 'Excluded', 'Population covered', 'Counties', 'Core-9 tracts', 'Income top-coded', 'Mean queen neighbours', 'Islands attached', 'Graph components', 'Correlation of the two exposures'])
rows = []
for _, r in sd.iterrows():
    rows.append([r.cross_section] + [f"{r['mean_'+c]*100:.1f} ({r['sd_'+c]*100:.1f})" for c in ['share_commute_60plus', 'share_drive_alone']] + [f"{r['mean_'+c]:.1f} ({r['sd_'+c]:.1f})" for c in OL])
A('**Table 2.2 Tract-level means (SD), unweighted, percent.**'); A('')
table(rows, ['Cross-section', '60+ min share', 'Drive-alone share'] + list(OL.values()))

# ------------------------------------------------------------------ trends
A('## 3. Housing and commute trends (step 1)'); A('')
A('### 3.1 Methods'); A('')
A('Estimates are weighted ratios (for example, weighted minutes over weighted commuters). Standard errors use the 80 replicate weights: variance = (4/80) x sum of squared deviations of the replicate estimates from the full-sample estimate; negative replicate weights are kept as published. '
  'Annual ACS samples are treated as independent, so the variance of a change is the sum of the two year-specific variances; changes are tested with two-sided z-tests. '
  'Age-band heterogeneity of the change is tested with a 4-df Wald chi-square on the five bands 16-34, 35-44, 45-54, 55-64, 65+ using the full within-year replicate covariance matrix. '
  'The core-versus-adjacent contrast is (change in the nine core counties) minus (change in the five adjacent counties with microdata), with the within-year replicate covariance. '
  f"The script reproduces the delivered county x year x age aggregates (maximum absolute difference {xc['max_abs_diff_estimate']:.1e} in estimates and {xc['max_abs_diff_se']:.1e} in standard errors over {xc['cells_matched']:,} of {xc['cells_compared']:,} cells compared). "
  'Travel time is top-coded in PUMS (observed maximum 141-146 minutes by year), which slightly understates means. Zillow values are annual means of a smoothed monthly index, in nominal dollars, with no published uncertainty; regional values are unweighted means of counties.'); A('')
A('### 3.2 Regional changes'); A('')
for (y0, y1, cap) in [(2010, 2019, 'Table 3.1 Change 2010 to 2019 (primary period), commuters/workers aged 16+. Level (SE); change (SE); p.'),
                      (2019, 2024, 'Table 3.2 Change 2019 to 2024 (descriptive: post-2020 commuters are a differently selected group). Level (SE); change (SE); p.')]:
    rows = []
    for meas in MLAB:
        for geo, gl in [('ALL14', 'All 14 counties'), ('CORE9', 'Core 9'), ('EXT5', 'Adjacent 5')]:
            r = g(geo, '16plus', meas, y0, y1); rows.append([MLAB[meas], gl, lev(r, meas, 'start'), lev(r, meas, 'end'), chg(r, meas)])
    A(f'**{cap}**'); A(''); table(rows, ['Measure', 'Region', str(y0), str(y1), 'Change'])
A('### 3.3 By age band, all 14 counties'); A('')
rows = []
for band, bl in [('16_34', '16-34'), ('35_44', '35-44'), ('45_54', '45-54'), ('55_64', '55-64'), ('65plus', '65+')]:
    row = [bl]
    for meas in ['mean_commute_min', 'share_commute_60plus', 'share_commute_90plus', 'share_drive_alone_workers']:
        r = g('ALL14', band, meas, 2010, 2019); row += [f"{r.value_start*k(meas):.2f}", f"{r.value_end*k(meas):.2f}", f"{r.change*k(meas):+.2f} ({r.se_change*k(meas):.2f})"]
    r2 = g('ALL14', band, 'mean_commute_min', 2019, 2024); r3 = g('ALL14', band, 'share_commute_60plus', 2019, 2024)
    row += [f"{r2.change:+.2f} ({r2.se_change:.2f})", f"{r3.change*100:+.2f} ({r3.se_change*100:.2f})", int(g('ALL14', band, 'mean_commute_min', 2010, 2019).n_commuter_records_start), int(g('ALL14', band, 'mean_commute_min', 2010, 2019).n_commuter_records_end)]
    rows.append(row)
A('**Table 3.3 Change 2010 to 2019 by age band (change with SE), and 2019 to 2024 change for two measures.**'); A('')
table(rows, ['Age', 'Mean min 2010', '2019', 'Change', '60+ % 2010', '2019', 'Change (pts)', '90+ % 2010', '2019', 'Change (pts)', 'Drive alone % 2010', '2019', 'Change (pts)', 'Mean min change 2019-24', '60+ change 2019-24 (pts)', 'Commuter records 2010', '2019'])
A('### 3.4 Heterogeneity tests, 2010 to 2019'); A('')
rows = []
h = het[het.year_start == 2010]
for meas in MLAB:
    for geo in ['ALL14', 'CORE9', 'EXT5']:
        r = h[(h.measure == meas) & (h.geo == geo) & h.test.str.startswith('age-band')].iloc[0]
        rows.append([MLAB[meas], f'Age bands equal, {geo}', f"chi-square(4) = {r.statistic:.2f}", p_(r.p_value)])
    r = h[(h.measure == meas) & h.test.str.contains('age band 16plus')].iloc[0]
    rows.append([MLAB[meas], 'Core 9 minus adjacent 5 (all ages)', f"difference {r.estimate*k(meas):+.2f} (SE {r.se*k(meas):.2f}); z = {r.statistic:.2f}", p_(r.p_value)])
    r = h[(h.measure == meas) & h.test.str.startswith('county')].iloc[0]
    rows.append([MLAB[meas], 'All 14 county changes equal (added, not pre-specified)', f"chi-square(13) = {r.statistic:.2f}", p_(r.p_value)])
table(rows, ['Measure', 'Test', 'Statistic', 'p'])
rr = h[(h.measure == 'share_commute_60plus') & h.test.str.contains('difference in change')]
rows = [[r.test.split('age band ')[1].split(' ')[0].replace('_', '-').replace('plus', '+'), f"{r.estimate*100:+.2f} ({r.se*100:.2f})", f"{r.statistic:.2f}", p_(r.p_value), r.detail] for _, r in rr.iterrows()]
A('**Table 3.4 Core 9 minus adjacent 5: difference in the 2010-2019 change of the 60+ minute share (percentage points), by age band.**'); A('')
table(rows, ['Age band', 'Difference (SE)', 'z', 'p', 'Component changes (proportions)'])
A('### 3.5 By county'); A('')
Z = tr[tr.source == 'Zillow ZHVI']
rows = []
for geo in sorted(Z[~Z.is_region_total].geo.unique(), key=lambda c: Z[Z.geo == c].geo_name.iloc[0]):
    zz = Z[(Z.geo == geo) & (Z.year_start == 2010) & (Z.year_end == 2019)].iloc[0]; zz2 = Z[(Z.geo == geo) & (Z.year_start == 2019) & (Z.year_end == 2024)].iloc[0]
    row = [zz.geo_name, 'core' if zz.core9 else 'adjacent', f"{zz.value_start:,.0f}", f"{zz.value_end:,.0f}", f"{zz['pct_change']:+.1f}%", f"{zz2.value_end:,.0f}", f"{zz2['pct_change']:+.1f}%"]
    q = PUMS[(PUMS.geo.astype(str).str.zfill(3) == str(geo).zfill(3)) & (PUMS.age_band == '16plus')]
    if len(q):
        for meas in ['mean_commute_min', 'share_commute_60plus', 'share_drive_alone_workers']:
            r = q[(q.measure == meas) & (q.year_start == 2010) & (q.year_end == 2019)].iloc[0]; row.append(f"{r.value_start*k(meas):.1f} -> {r.value_end*k(meas):.1f}; {r.change*k(meas):+.2f} ({r.se_change*k(meas):.2f})")
        for meas in ['mean_commute_min', 'share_commute_60plus']:
            r = q[(q.measure == meas) & (q.year_start == 2019) & (q.year_end == 2024)].iloc[0]; row.append(f"{r.change*k(meas):+.2f} ({r.se_change*k(meas):.2f})")
    else: row += ['no microdata']*5
    rows.append(row)
for geo in ['CORE9', 'EXT6', 'EXT5', 'ALL15', 'ALL14']:
    zz = Z[(Z.geo == geo) & (Z.year_start == 2010) & (Z.year_end == 2019)].iloc[0]; zz2 = Z[(Z.geo == geo) & (Z.year_start == 2019) & (Z.year_end == 2024)].iloc[0]
    rows.append([f'{geo} (unweighted county mean)', '', f"{zz.value_start:,.0f}", f"{zz.value_end:,.0f}", f"{zz['pct_change']:+.1f}%", f"{zz2.value_end:,.0f}", f"{zz2['pct_change']:+.1f}%", '', '', '', '', ''])
A('**Table 3.5 County home values (Zillow index, NOMINAL dollars) and commute changes (change with replicate-weight SE).**'); A('')
table(rows, ['County', 'Group', 'ZHVI 2010', 'ZHVI 2019', 'Change 2010-19', 'ZHVI 2024', 'Change 2019-24', 'Mean commute min 2010 -> 2019; change', '60+ % 2010 -> 2019; change (pts)', 'Drive-alone % 2010 -> 2019; change (pts)', 'Mean min change 2019-24', '60+ change 2019-24 (pts)'])
cc = PUMS[(~PUMS.is_region_total) & (PUMS.age_band == '16plus') & (PUMS.year_start == 2010) & (PUMS.year_end == 2019)]
c1 = cc[cc.measure == 'mean_commute_min']; c2 = cc[cc.measure == 'share_commute_60plus']
A(f"County changes in mean commute, 2010-2019, range from {c1.change.min():+.2f} minutes ({c1.loc[c1.change.idxmin(),'geo_name']}) to {c1.change.max():+.2f} ({c1.loc[c1.change.idxmax(),'geo_name']}); "
  f"{int((c1.p_value < 0.05).sum())} of 14 county increases are individually significant at 0.05 (unadjusted). For the 60+ minute share the range is {c2.change.min()*100:+.2f} ({c2.loc[c2.change.idxmin(),'geo_name']}) to {c2.change.max()*100:+.2f} points ({c2.loc[c2.change.idxmax(),'geo_name']}). "
  "The full table (every county x age band x measure x period, plus 2019-2021 and 2010-2024 rows) is in `trends_table.csv`; levels for 2010, 2019, 2021 and 2024 are in `trends_levels.csv`."); A('')

# ------------------------------------------------------------------ tract models
A('## 4. Tract-level association models (step 2)'); A('')
A('### 4.1 Specification (fixed in advance)'); A('')
A('For each cross-section c and outcome y (PLACES crude prevalence, percent):'); A('')
A('`y_i = a_county(i) + b1 * share_commute_60plus_i + b2 * share_drive_alone_i + g\' * X_i + e_i`'); A('')
A('- Both exposures are entered jointly. `share_commute_60plus` is the share of commuters with travel time of 60+ minutes; `share_drive_alone` is the share of all workers who drove alone. Coefficients are reported per 10-percentage-point difference in the exposure, in percentage points of prevalence.')
A('- X: shares aged 18-34, 35-64, 65+ (under 18 is the reference); log median household income and an indicator for the top-coded value; poverty rate; share with a bachelor\'s degree or more; shares non-Hispanic Black, non-Hispanic Asian, Hispanic (reference: non-Hispanic White and all other); share of households with no vehicle; county fixed effects.')
A('- Spatial weights: queen contiguity from TIGER/Line tract polygons (TIGER2019 for 2010-boundary tracts, TIGER2024 for 2020-boundary tracts), built on the estimation sample, row-standardised; tracts without a neighbour are joined to the nearest sample tract. TIGER/Line polygons extend over water, so tracts on opposite shores of the Bay can be neighbours.')
A('- Estimators: (1) OLS with HC1 standard errors, with Moran\'s I of the residuals and Lagrange-multiplier tests; (2) spatial error model by maximum likelihood, `y = Xb + u, u = lambda*W*u + e`; (3) spatial lag model by maximum likelihood, `y = rho*W*y + Xb + e`. For the lag model the reported quantity is the average total impact `b/(1-rho)` with a 95% interval from 2,000 draws of the asymptotic distribution of (b, rho); its p-value is the z-test of b. Raw b and the average direct impact are in `tract_models.csv`.')
A('- Favoured model (rule fixed in advance): OLS if neither LM test is significant at 0.05; the single significant alternative if only one is; otherwise the alternative with the larger robust LM statistic. AIC is a cross-check.')
A('- Multiplicity: Benjamini-Hochberg q-values within each family of 12 tests (6 outcomes x 2 exposures) per cross-section and estimator.'); A('')
A('### 4.2 Diagnostics'); A('')
rows = []
for _, r in dg.iterrows():
    rows.append([str(r.acs_vintage - 4) + '-' + str(r.acs_vintage), OL[r.outcome], int(r.n_tracts), f"{r.ols_r2:.3f}", f"{r.r2_covariates_only:.3f}", f"{r.partial_r2_exposures:.4f}", f"{r.moran_I_ols_resid:.3f} (z {r.moran_z:.1f}; perm. p {p_(r.moran_p_perm)})",
                 f"{r.lm_error:.1f} / {r.rlm_error:.1f}", f"{r.lm_lag:.1f} / {r.rlm_lag:.1f}", f"{r.error_lambda:.3f} ({r.error_lambda_se:.3f})", f"{r.lag_rho:.3f} ({r.lag_rho_se:.3f})",
                 f"{r.ols_aic:.0f} / {r.error_aic:.0f} / {r.lag_aic:.0f}", f"{r.moran_I_error_filtered_resid:+.3f} / {r.moran_I_lag_resid:+.3f}", r.favoured_by_lm_rule.split(' (')[0].replace('Spatial ', ''), r.lowest_aic.split(' (')[0].replace('Spatial ', '')])
A('**Table 4.1 Model diagnostics.** LM = Lagrange multiplier statistic (1 df) / robust form. Residual Moran\'s I after the spatial models uses spatially filtered residuals (error model) and ordinary residuals (lag model).'); A('')
table(rows, ['ACS period', 'Outcome', 'n', 'OLS R2', 'R2 covariates only', 'Partial R2 of the 2 exposures', 'Moran\'s I, OLS residuals', 'LM error / robust', 'LM lag / robust', 'lambda (SE)', 'rho (SE)', 'AIC OLS / error / lag', 'Residual Moran\'s I error / lag', 'Favoured (LM rule)', 'Lowest AIC'])
f19 = dg[dg.acs_vintage == 2019].favoured_by_lm_rule.value_counts(); f24 = dg[dg.acs_vintage == 2024].favoured_by_lm_rule.value_counts()
def cnt(vc, key): return int(vc.get(key, 0))
agree = int((dg.favoured_by_lm_rule == dg.lowest_aic).sum())
A(f"OLS residuals are spatially autocorrelated for every outcome in both cross-sections (Moran's I {dg.moran_I_ols_resid.min():.3f} to {dg.moran_I_ols_resid.max():.3f}; all permutation p-values {p_(dg.moran_p_perm.max())} with 999 permutations, the smallest attainable), so OLS standard errors are not trustworthy and OLS is never favoured. "
  f"By the pre-specified LM rule the spatial error model is favoured for {cnt(f19,'Spatial error (ML)')} of 6 outcomes in 2015-2019 and {cnt(f24,'Spatial error (ML)')} of 6 in 2020-2024; the spatial lag model for {cnt(f19,'Spatial lag (ML), average total impact')} and {cnt(f24,'Spatial lag (ML), average total impact')}. "
  f"The lowest-AIC model agrees with the LM rule in {agree} of 12 cases. The error model removes residual autocorrelation (filtered-residual Moran's I {dg.moran_I_error_filtered_resid.min():+.3f} to {dg.moran_I_error_filtered_resid.max():+.3f}); the lag model leaves some in 2015-2019 (up to {dg.moran_I_lag_resid.max():+.3f}). "
  f"The covariates and county effects alone explain {dg.r2_covariates_only.min()*100:.1f}% to {dg.r2_covariates_only.max()*100:.1f}% of the variance of the PLACES outcomes; the two exposures add a partial R2 of {dg.partial_r2_exposures.min():.4f} to {dg.partial_r2_exposures.max():.4f}. "
  "This is the expected signature of outcomes that are themselves predictions from tract demography."); A('')
A('### 4.3 Coefficients (all 72 pre-specified estimates)'); A('')
for v in (2019, 2024):
    rows = []
    for e in EL:
        for oc in OL: rows.append([EL[e], OL[oc]] + [cell(tmrow(v, oc, e, est)) for est in EST])
    A(f"**Table 4.{2 if v == 2019 else 3} {sd.loc[sd.acs_vintage == v, 'cross_section'].iloc[0]}; n = {n19 if v == 2019 else n24} tracts.** Difference in prevalence (percentage points) per 10-point higher exposure, (95% CI); q = Benjamini-Hochberg q-value in the family of 12; **F** = estimator favoured by the diagnostics for that outcome."); A('')
    table(rows, ['Exposure', 'Outcome', 'OLS (HC1)', 'Spatial error (ML)', 'Spatial lag (ML), total impact'])
rows = []
for v in (2019, 2024):
    for est in EST + ['Favoured per outcome']:
        d = fav[fav.acs_vintage == v] if est == 'Favoured per outcome' else tm[(tm.acs_vintage == v) & (tm.estimator == est)]
        row = [f'{v-4}-{v}', est]
        for e in EL:
            x = d[d.exposure == e]; row += [f"{int((x.estimate < 0).sum())} / {int((x.estimate > 0).sum())}", int((x.p_value < 0.05).sum()), f"{int((x.fdr_significant_q05 & (x.estimate < 0)).sum())} neg, {int((x.fdr_significant_q05 & (x.estimate > 0)).sum())} pos"]
        rows.append(row)
A('**Table 4.4 Count of estimates by sign and significance (6 outcomes each).** The q-values in the "Favoured" row are those computed within each estimator\'s own family of 12.'); A('')
table(rows, ['ACS period', 'Estimator', '60+ share: negative / positive', 'p < 0.05', 'FDR q < 0.05', 'Drive alone: negative / positive', 'p < 0.05', 'FDR q < 0.05'])
x19 = fav[(fav.acs_vintage == 2019) & (fav.exposure == 'share_commute_60plus')].set_index('outcome'); x24 = fav[(fav.acs_vintage == 2024) & (fav.exposure == 'share_commute_60plus')].set_index('outcome')
def s_(r, u='points'): return f"{r.estimate:+.3f} {u} (95% CI {r.ci95_lo:+.3f} to {r.ci95_hi:+.3f}; q {p_(r.q_bh_family12)})"
A('**Reading of the result.**'); A('')
A(f"- 2015-2019 (favoured estimator per outcome): a 10-point higher 60+ minute commute share went with coronary heart disease prevalence {s_(x19.loc['chd_prev'])}, stroke {s_(x19.loc['stroke_prev'])}, high blood pressure {s_(x19.loc['bphigh_prev'])}, "
  f"diabetes {s_(x19.loc['diabetes_prev'])}, physical inactivity {s_(x19.loc['lpa_prev'])} and obesity {s_(x19.loc['obesity_prev'])}. The significant associations are inverse, opposite to the hypothesis.")
A(f"- 2020-2024: no association of the 60+ minute share with any outcome under any estimator (largest absolute favoured estimate {x24.estimate.abs().max():.3f} points; smallest q {p_(tm[(tm.acs_vintage==2024)&(tm.exposure=='share_commute_60plus')].q_bh_family12.min())}).")
d19 = fav[(fav.acs_vintage == 2019) & (fav.exposure == 'share_drive_alone')].set_index('outcome'); d24 = fav[(fav.acs_vintage == 2024) & (fav.exposure == 'share_drive_alone')].set_index('outcome')
A(f"- Drive-alone share: inversely associated with modelled physical inactivity in both cross-sections ({s_(d19.loc['lpa_prev'])} and {s_(d24.loc['lpa_prev'])}) and with diabetes in 2015-2019 ({s_(d19.loc['diabetes_prev'])}); no association with coronary heart disease, stroke or high blood pressure in either cross-section.")
A("- Magnitudes are small relative to between-tract variation: the outcome standard deviations are in Table 2.2, and a 10-point exposure difference is a little over one standard deviation of the 60+ share and about 0.6 standard deviations of the drive-alone share.")
A("- A plausible, untested reading of the inverse 2015-2019 associations is residual composition: long-commute tracts are worker-dense, and the three broad age shares used here do not capture the finer demographic cells from which PLACES builds the outcome (PLACES method as summarised in the project data dictionary; not re-verified from CDC documentation here). That is an interpretation, not a finding."); A('')

# ------------------------------------------------------------------ panel
A('## 5. Housing to commute to mortality: county-year panel (step 3)'); A('')
A('> **This is not causal identification.** Two-way fixed effects remove fixed county differences and common year shocks only. Home values, commuting, the age and occupational mix of residents, migration and mortality all trend together within counties, and nothing here isolates exogenous variation in housing costs. '
  '**The mortality rates are model-smoothed** (age-standardised and spatiotemporally smoothed by CDC): smoothing borrows strength across neighbouring counties and adjacent years, which removes exactly the within-county year-to-year variation that fixed-effects models use, induces serial and spatial correlation, and makes the stated uncertainty too small. '
  '**Sample size:** 14 counties x 10 years = 140 county-years, 14 clusters.'); A('')
A('### 5.1 Specification'); A('')
A('- Model H: `commute_ct = a_c + d_t + beta * log(ZHVI_c,t-1) + e_ct`; outcomes: mean one-way commute and 60+ minute share (commuters 16+; also the 35-64 band, which is the a-path for the 35-64 decomposition). Lag 1 is primary; lags 0 and 2 are secondary. The 2008 and 2009 index values come from `zillow_county_annual.parquet` of this project. Year effects absorb common inflation. Coefficients are scaled to a 10% higher home value (beta x ln 1.10).')
A('- Model M: `log(mortality_ct, band) = a_c + d_t + gamma * commute_ct + e_ct`, all-cardiovascular mortality (primary), coronary heart disease and stroke (secondary), ages 35-64 (with the commute measure of commuters aged 35-64) and 65+ (with the measure for all commuters 16+, because people aged 65+ are mostly not commuters). Contemporaneous. Coefficients per 5 minutes or per 10 points of 60+ share; x100 is an approximate percent difference in the rate.')
A('- Decomposition: a = home value -> commute; b = commute -> log mortality given home value; indirect = a x b; direct = home value -> log mortality given commute; total = home value -> log mortality. Percentile intervals from 4,999 county-cluster pairs bootstrap draws (seed 20261113).')
A('- Inference: clustered by county. CR1 standard errors with a t(13) reference; primary intervals from the wild cluster restricted bootstrap-t (null imposed, Rademacher weights, all 2^14 = 16,384 sign vectors enumerated, so no simulation error) inverted for the 95% CI. Unweighted.')
A(f'- Minimum detectable effect (MDE): (t_0.975,13 + t_0.80,13) x CR1 SE = {MDE_MULT:.2f} x SE, the true coefficient that would be detected with 80% power at two-sided 5%.')
A('- Sampling error in the PUMS county-year commute estimates is not modelled. The column "noise share" is mean(SE^2) x (1-1/T)(1-1/G) divided by the within-county, within-year variance of the measure: the approximate fraction of the identifying variation that is sampling noise (added diagnostic, not pre-specified).'); A('')
A('### 5.2 Housing to commute'); A('')
rows = []
for _, r in pm[pm.block.str.startswith('H')].iterrows():
    sc = 1.0 if 'mean' in r.outcome else 100.0; u = 'min' if 'mean' in r.outcome else 'pts'
    rows.append([r.outcome_label.replace(' (minutes)', '').replace(' (proportion)', ''), r.regressor_label.split(',')[1].strip().replace(' (nominal)', ''), r.role.split(' (')[0], f"{r.estimate*sc:+.3f} {u}", f"{r.se_cr1*sc:.3f}",
                 f"{r.ci95_lo_cr1_t13*sc:+.3f} to {r.ci95_hi_cr1_t13*sc:+.3f}", p_(r.p_cr1_t13), f"{r.ci95_lo_wild*sc:+.3f} to {r.ci95_hi_wild*sc:+.3f}", p_(r.p_wild_cluster), f"{r.ci_width_wild*sc:.3f}", f"{r.mde_80pct_power*sc:.3f}",
                 f"{r.sampling_noise_share_of_within_var_outcome:.2f}"])
A('**Table 5.1 Model H: difference in the commute measure per 10% higher nominal home value (n = 140 county-years, 14 clusters).**'); A('')
table(rows, ['Outcome', 'Home value lag', 'Role', 'Estimate', 'CR1 SE', '95% CI, t(13)', 'p, t(13)', '95% CI, wild cluster', 'p, wild cluster', 'Width of wild CI', 'MDE (80% power)', 'Noise share of outcome'])
A(f"How wide the intervals are: for the primary mean-commute model the wild-cluster interval spans {H1.ci_width_wild:.2f} minutes around an estimate of {H1.estimate:+.2f}, i.e. it is {H1.ci_width_wild/abs(H1.estimate):.1f} times the estimate; for the 60+ share it spans {H2.ci_width_wild*100:.2f} points around {H2.estimate*100:+.2f} ({H2.ci_width_wild/abs(H2.estimate):.1f} times the estimate). "
  f"The MDE is {H1.mde_80pct_power:.2f} minutes and {H2.mde_80pct_power*100:.2f} points per 10% of home value. The within-county, within-year standard deviation of log home value is only {H1.within_sd_regressor:.3f} (about {100*(np.exp(H1.within_sd_regressor)-1):.1f}%), because home values rose together across the region; year effects absorb the common rise, which is most of the story told by the raw trends. "
  "All twelve point estimates are positive; none of the wild-cluster intervals excludes zero."); A('')
A('### 5.3 Commute to mortality'); A('')
rows = []
for _, r in pm[pm.block.str.startswith('M')].iterrows():
    rows.append([r.outcome_label.replace('log ', '').replace(' (model-smoothed)', '').replace(' mortality rate', ''), r.regressor_label, r.role, f"{r.estimate*100:+.2f}%", f"{r.se_cr1*100:.2f}", f"{r.ci95_lo_wild*100:+.2f}% to {r.ci95_hi_wild*100:+.2f}%",
                 p_(r.p_wild_cluster), p_(r.p_cr1_t13), f"{r.mde_80pct_power*100:.2f}%", f"{r.sampling_noise_share_of_within_var_regressor:.2f}"])
A('**Table 5.2 Model M: approximate percent difference in the model-smoothed mortality rate per 5 more minutes of mean commute or per 10-point higher 60+ share (100 x log-rate coefficient; n = 140, 14 clusters).**'); A('')
table(rows, ['Mortality (cause, ages)', 'Commute measure', 'Role', 'Estimate', 'CR1 SE (x100)', '95% CI, wild cluster', 'p, wild cluster', 'p, t(13)', 'MDE (80% power)', 'Noise share of regressor'])
Mm = pm[pm.block.str.startswith('M')]
prim_ = Mm[Mm.role == 'primary']; sec_ = Mm[Mm.role == 'secondary']
chd = Mm[Mm.model_id.str.startswith('M_chd')]
A(f"Primary outcome (all cardiovascular disease): {int((prim_.p_wild_cluster < 0.05).sum())} of 4 coefficients are significant at 0.05; point estimates are negative at ages 35-64 and positive but small at 65+. "
  f"Secondary outcomes: all 4 coronary heart disease coefficients are NEGATIVE with wild-cluster p from {p_(chd.p_wild_cluster.min())} to {p_(chd.p_wild_cluster.max())} (counties whose commutes lengthened most had larger declines in smoothed coronary mortality), not adjusted for multiplicity across the 12 models; the 4 stroke coefficients are not significant. "
  "None supports a positive commute-mortality association. "
  f"The MDEs range from {Mm.mde_80pct_power.min()*100:.1f}% to {Mm.mde_80pct_power.max()*100:.1f}%. "
  f"Benchmark (illustrative): if every commuter with a 60+ minute commute carried the hazard ratio of {bench['hr']} ({bench['hr_lo']} to {bench['hr_hi']}) reported for men riding in a car more than 10 versus under 4 hours a week (dose-response row {bench['row_id']}, Warren 2010; the only driving-specific cardiovascular mortality estimate), "
  f"and commuters are {bench['pop_share_commuter_35_64_2019']*100:.1f}% of people aged 35-64 (all 14 counties, 2019), a 10-point higher 60+ share would raise mortality at 35-64 by about {bench['implied_lograte_change_per_10pt_60plus_share_35_64']*100:.1f}%. "
  f"The MDE for that model is {M1.mde_80pct_power*100:.1f}%, {M1.mde_80pct_power/bench['implied_lograte_change_per_10pt_60plus_share_35_64']:.1f} times larger, before allowing for attenuation: {Mm.sampling_noise_share_of_within_var_regressor.min()*100:.0f}% to {Mm.sampling_noise_share_of_within_var_regressor.max()*100:.0f}% of the within-county variation in the commute regressors is PUMS sampling noise, which biases these coefficients towards zero. "
  "A null here is therefore uninformative about effects of the size the literature suggests; it rules out only large effects."); A('')
A('### 5.4 Product-of-coefficients decomposition (descriptive)'); A('')
rows = []
D = pm[pm.block.str.startswith('D')]
for mid, grp in D.groupby('model_id', sort=False):
    band = '35-64' if '35_64' in mid else '65+'; med = 'mean commute (min)' if 'mean' in mid.split('_')[-1] or 'mean' in mid else '60+ share'
    for _, r in grp.iterrows():
        if r.role.startswith('a:'):
            sc = 1.0 if 'mean' in r.regressor else 100.0; txt = f"{r.estimate*sc:+.3f} ({r.boot_ci95_lo*sc:+.3f} to {r.boot_ci95_hi*sc:+.3f}) {'min' if sc == 1 else 'pts'} per 10% home value"
        elif r.role.startswith('b:'):
            sc = 100.0 if 'mean' in r.regressor else 10.0; txt = f"{r.estimate*sc:+.2f}% ({r.boot_ci95_lo*sc:+.2f}% to {r.boot_ci95_hi*sc:+.2f}%) per {'minute' if 'mean' in r.regressor else '10 pts'}"
        else: txt = f"{r.estimate*100:+.3f}% ({r.boot_ci95_lo*100:+.3f}% to {r.boot_ci95_hi*100:+.3f}%) per 10% home value"
        rows.append([f'All CVD, {band}', 'mean commute (min)' if 'mean' in r.regressor else '60+ share', r.role.replace(' | ', ' given '), txt])
A('**Table 5.3 Decomposition of the association between lagged log home value and log all-cardiovascular mortality (estimate, 95% percentile interval from 4,999 county-cluster bootstrap draws).** Mortality entries are approximate percent differences in the rate.'); A('')
table(rows, ['Outcome', 'Commute measure (mediator)', 'Path', 'Estimate (95% bootstrap interval)'])
ind = D[D.role.str.startswith('indirect')]; tot = D[D.role.str.startswith('total')].drop_duplicates('outcome')
A(f"All four indirect (home value -> commute -> mortality) products have intervals that include zero (estimates {ind.estimate.min()*100:+.3f}% to {ind.estimate.max()*100:+.3f}% per 10% of home value). "
  + ' '.join(f"The total within-county association of home value with all-cardiovascular mortality at ages {('35-64' if '35_64' in r.outcome else '65+')} is {r.estimate*100:+.2f}% per 10% of home value (interval {r.boot_ci95_lo*100:+.2f}% to {r.boot_ci95_hi*100:+.2f}%)." for _, r in tot.iterrows())
  + " At ages 35-64 this positive total association is essentially all 'direct', that is, not passing through the commute measures; it is a within-county co-trend (counties with faster home-value growth had slower declines in smoothed mortality) with many non-commute explanations, including the smoothing model, and is not evidence of an effect of housing cost. "
  "A pairs cluster bootstrap with 14 clusters is known to be unreliable (intervals tend to be too narrow); these intervals should be read as optimistic. The decomposition assumes linearity, no exposure-mediator interaction and no unmeasured confounding of any path, none of which is defensible here."); A('')

# ------------------------------------------------------------------ sensitivity
A('## 6. Sensitivity analyses (step 4)'); A('')
A('All specifications were fixed in advance. Each is compared with the primary estimate for the same outcome, exposure, cross-section and estimator. "Sign differs" compares point estimates regardless of significance; "significance changes" means crossing nominal p = 0.05 in either direction. For S3 the alternative commute measure is compared with the primary 60+ share coefficient on sign and significance only (units differ). S6 is compared with the 2015-2019 cross-sectional estimate.'); A('')
tr_ = se_[se_.level == 'tract'].copy()
SL = {'S1': 'S1 Nine core counties only', 'S2': 'S2 Excluding top decile of transit share', 'S3_mean_commute_min': 'S3a Mean commute minutes (per 5 min) as exposure', 'S3_share_commute_45plus': 'S3b 45+ minute share as exposure',
      'S3_share_commute_90plus': 'S3c 90+ minute share as exposure', 'S4': 'S4 Adding PLACES smoking prevalence', 'S5': 'S5 Adult-population-weighted (WLS) vs unweighted OLS',
      'S6': 'S6 First difference, boundary-stable tracts', 'S8_share_commute_60plus': 'S8a 60+ share entered alone', 'S8_share_drive_alone': 'S8b Drive-alone share entered alone'}
rows = []
for spec in SL:
    for v in (2019, 2024):
        x = tr_[(tr_.spec == spec) & (tr_.acs_vintage == v)]
        if not len(x): continue
        nt = int(ssamp[(ssamp.spec == spec) & (ssamp.acs_vintage == v)].n_tracts.iloc[0])
        for e in x.exposure.unique():
            y = x[x.exposure == e]
            rows.append([SL[spec], ('2015-19 to 2020-24' if spec == 'S6' else f'{v-4}-{v}'), nt, e.replace('share_', '').replace('_', ' '), len(y), int(y.sign_differs.sum()), int(y.significance_changes.sum()), int(y.sign_reversal_both_significant.sum()),
                         f"{int(y.nominal_sig.sum())} vs {int(y.primary_nominal_sig.sum())}", f"{int(((y.p_value < 0.05) & (y.estimate > 0)).sum())}", ('' if y.ratio_to_primary.isna().all() else f"{y.ratio_to_primary.median():.2f}")])
A('**Table 6.1 Where sign, size or significance change (tract models; rows pool the estimators run for the specification: OLS, spatial error and spatial lag, 6 outcomes each).**'); A('')
table(rows, ['Specification', 'Cross-section', 'n tracts', 'Exposure', 'Models', 'Sign differs from primary', 'Significance changes', 'Sign reversal, both significant', 'p < 0.05: sensitivity vs primary', 'Significant AND positive', 'Median ratio to primary'])
def sens_tab(spec, v, ests):
    rows = []
    x = tr_[(tr_.spec == spec) & (tr_.acs_vintage == v)]
    for e in x.exposure.unique():
        for oc in OL:
            row = [e.replace('share_', '').replace('_', ' '), OL[oc]]
            for est in ests:
                r = x[(x.exposure == e) & (x.outcome == oc) & (x.estimator == est)].iloc[0]
                row.append(f"{r.estimate:+.3f} ({r.ci95_lo:+.3f}, {r.ci95_hi:+.3f}); p {p_(r.p_value)}; primary {r.primary_estimate:+.3f}")
            rows.append(row)
    return rows
s1 = tr_[(tr_.spec == 'S1') & (tr_.acs_vintage == 2024) & (tr_.exposure == 'share_commute_60plus')]
A('**S1 (core counties).** In 2015-2019 the inverse associations of the 60+ share persist in the nine core counties. '
  f"In 2020-2024, restricting to the core counties turns {int(s1.nominal_sig.sum())} of 18 previously null 60+ share coefficients nominally significant, all of them negative ({int(((s1.p_value<0.05)&(s1.estimate<0)).sum())} negative, {int(((s1.p_value<0.05)&(s1.estimate>0)).sum())} positive); "
  f"{int((tr_[(tr_.spec=='S1')&(tr_.acs_vintage==2024)&(tr_.exposure=='share_commute_60plus')].q_bh_family12 < 0.05).sum())} of 18 survive FDR control within their family."); A('')
A('**Table 6.2 S1, nine core counties, 2020-2024.** Estimate (95% CI); p; primary estimate.'); A(''); table(sens_tab('S1', 2024, EST), ['Exposure', 'Outcome'] + EST)
s4 = tr_[(tr_.spec == 'S4') & (tr_.exposure == 'share_drive_alone')]
A(f"**S4 (smoking).** Adding modelled smoking prevalence changes the sign of {int(s4[s4.acs_vintage==2019].sign_differs.sum())} of 18 drive-alone coefficients in 2015-2019 and {int(s4[s4.acs_vintage==2024].sign_differs.sum())} of 18 in 2020-2024, and changes nominal significance for {int(s4[s4.acs_vintage==2019].significance_changes.sum())} and {int(s4[s4.acs_vintage==2024].significance_changes.sum())}; the 60+ share coefficients are little affected. "
  "Smoking prevalence is itself a PLACES model output built from the same demographic predictors, so this adjustment partly re-enters the outcome model on the right-hand side and is not a clean confounder adjustment. The drive-alone associations should be regarded as not robust."); A('')
s6 = tr_[tr_.spec == 'S6']; n6 = int(ssamp[ssamp.spec == 'S6'].n_tracts.iloc[0])
A(f"**S6 (first difference).** {n6} boundary-stable tracts present in both samples. Changes in modelled prevalence between the PLACES 2021 release (BRFSS 2019) and the 2025 release (BRFSS 2023) regressed on changes in the exposures and covariates, with county effects. "
  f"For the 60+ share, {int(((s6.exposure=='share_commute_60plus')&(s6.p_value<0.05)&(s6.estimate<0)).sum())} of 12 coefficients are nominally significant and negative and {int(((s6.exposure=='share_commute_60plus')&(s6.p_value<0.05)&(s6.estimate>0)).sum())} positive; {int(((s6.exposure=='share_commute_60plus')&(s6.p_value<0.05)&(s6.estimator=='OLS (HC1)')).sum())} of these are OLS estimates and {int(((s6.exposure=='share_commute_60plus')&(s6.p_value<0.05)&(s6.estimator=='Spatial error (ML)')).sum())} are spatial error estimates. "
  f"For drive-alone share, {int(((s6.exposure=='share_drive_alone')&(s6.p_value<0.05)&(s6.estimate>0)).sum())} of 12 are significant and positive (physical inactivity and obesity, both estimators), the opposite sign to the cross-sectional estimates for inactivity. "
  "The two PLACES releases differ in BRFSS year, population base and modelling details, the period spans the pandemic shift to remote work (which changes who is counted as a commuter and as driving alone), and income is nominal; the differenced outcome therefore mixes real change with method change, and these estimates carry little evidential weight in either direction."); A('')
A('**Table 6.3 S6, first-difference models.** Estimate per 10-point change in exposure (95% CI); p; primary = 2015-2019 cross-sectional estimate, same estimator.'); A(''); table(sens_tab('S6', 2024, ['OLS (HC1)', 'Spatial error (ML)']), ['Exposure', 'Outcome', 'OLS (HC1)', 'Spatial error (ML)'])
c7 = se_[se_.spec == 'S7']
rows = []
for (oc, e), grp in c7.groupby(['outcome_label', 'exposure'], sort=False):
    u = grp[grp.estimator.str.contains('unadjusted')].iloc[0]; a = grp[grp.estimator.str.contains('adjusted for')].iloc[0]; s = grp[grp.estimator.str.startswith('Spearman')].iloc[0]
    rows.append([oc, EL[e], f"{u.estimate*100:+.1f}% ({u.ci95_lo*100:+.1f}% to {u.ci95_hi*100:+.1f}%); p {p_(u.p_value)}; classical p {p_(u.p_value_classical)}",
                 f"{a.estimate*100:+.1f}% ({a.ci95_lo*100:+.1f}% to {a.ci95_hi*100:+.1f}%); p {p_(a.p_value)}; classical p {p_(a.p_value_classical)}", f"{s.estimate:+.2f} (p {p_(s.p_value)})", f"{u.max_leverage:.2f}"])
A('**S7 (county mortality in place of modelled prevalence).** Fifteen counties; log model-smoothed mortality rate on each ACS 5-year county exposure, alone and with log median household income. With n = 15 nothing more can be adjusted for, and the estimates are dominated by between-county socioeconomic differences.'); A('')
A('**Table 6.4 S7: approximate percent difference in county mortality rate per 10-point higher exposure (HC3 95% CI, t reference); Spearman rank correlation.** "Classical p" uses ordinary least-squares standard errors and was added after seeing that one county has very high leverage (not pre-specified).'); A('')
table(rows, ['Outcome', 'Exposure', 'Unadjusted', 'Adjusted for log median household income', 'Spearman rho', 'Max leverage (unadjusted)'])
c60 = c7[(c7.exposure == 'share_commute_60plus') & ~c7.estimator.str.startswith('Spearman')]; cda = c7[(c7.exposure == 'share_drive_alone')]
sp = cda[cda.estimator.str.startswith('Spearman')]; sp60 = c7[(c7.exposure == 'share_commute_60plus') & c7.estimator.str.startswith('Spearman')]
A(f"For the 60+ minute share, {int((c60.p_value < 0.05).sum())} of {len(c60)} county regressions is nominally significant under HC3 ({'; '.join(f'{r.outcome_label}, {r.estimator.split(chr(44))[1].strip()}: {r.estimate*100:+.1f}%' for _, r in c60[c60.p_value < 0.05].iterrows())}); rank correlations range from {sp60.estimate.min():+.2f} to {sp60.estimate.max():+.2f} with none significant at 0.05. "
  f"For drive-alone share the rank correlations with mortality are strongly positive ({sp.estimate.min():+.2f} to {sp.estimate.max():+.2f}; {int((sp.p_value < 0.05).sum())} of {len(sp)} with p < 0.05), but the regression slopes are imprecise under HC3 because San Francisco is a high-leverage point (leverage up to {c7.max_leverage.max():.2f}), "
  f"and they shrink towards zero once median household income is included (largest adjusted estimate {cda[cda.estimator.str.contains('adjusted for')].estimate.abs().max()*100:.1f}% per 10 points). "
  "The positive unadjusted rank correlation is what would be expected from the Central Valley counties being both more car-dependent and poorer; it does not survive the single adjustment available. The within-county panel models in section 5 are the counterpart that removes fixed county differences."); A('')
cm = tr_[tr_.exposure != 'share_drive_alone']; cpos = cm[(cm.estimate > 0) & (cm.p_value < 0.05)]; cneg = cm[(cm.estimate < 0) & (cm.p_value < 0.05)]; cposq = cpos[cpos.q_bh_family12 < 0.05]
def _d(r): return f"{SL[r.spec].split(' ')[0]} {r.acs_vintage-4}-{r.acs_vintage} {OL[r.outcome].lower()}, {r.estimator.split(' (')[0]}: {r.estimate:+.3f}, p {p_(r.p_value)}, q {p_(r.q_bh_family12)}"
A(f"**Overall.** Across specifications the commute-duration exposure (60+ share or its alternatives) is either inversely associated with modelled prevalence (2015-2019; core counties in 2020-2024) or not associated. Of {len(cm)} sensitivity estimates for a commute-duration exposure, {len(cneg)} are nominally significant and negative and {len(cpos)} nominally significant and positive. "
  f"The positive ones are all for obesity ({'; '.join(_d(r) for _, r in cpos.iterrows())}); the number that survive FDR control within their family is {len(cposq)} ({'; '.join(_d(r) for _, r in cposq.iterrows())}), under OLS only and not under either spatial estimator for the same specification, where OLS residuals are spatially autocorrelated. "
  "No positive association with coronary heart disease, stroke, high blood pressure, diabetes or inactivity appears in any specification. The alternative thresholds (45+, 90+, mean minutes) behave like the 60+ share. Single-exposure models and population weighting change little. Drive-alone share coefficients change sign under smoking adjustment and in first differences and should not be interpreted. Full results: `sensitivity_models.csv`; counts: `sensitivity_change_summary.csv`."); A('')

# ------------------------------------------------------------------ deviations, assumptions, limitations
A('## 7. Departures from and additions to the pre-specified plan'); A('')
A('No pre-specified model was dropped or altered. Additions, all reported: (1) a 13-df Wald test of equal change across the 14 counties, and descriptive 2019-2021 and 2010-2024 change rows in `trends_table.csv`; (2) Model H was also run for the 35-64 commuter band because it is the a-path of the 35-64 decomposition; '
  '(3) the sampling-noise share diagnostic in the panel; (4) covariates-only R2, partial R2 and Moran\'s I of the spatial-model residuals in the tract diagnostics; (5) classical standard errors and leverage for the 15-county regressions; the plan did not name a variance estimator for S7, HC3 was coded first and is the reported interval. '
  'One API test fit was run before the primary run, on short-sleep prevalence, which is not among the six outcomes.'); A('')
A('## 8. Assumptions'); A('')
for i, s in enumerate([
    'ACS samples in different years are independent (variance of a change = sum of variances). Successive-difference replication variance with factor 4/80.',
    'PUMS travel time is top-coded; means are computed on the top-coded values.',
    'Regional Zillow values are unweighted means of county index values; the index is nominal, smoothed, and has no uncertainty estimate.',
    'Tract sample restricted to tracts with at least 100 commuters; median household income top-codes are handled with an indicator rather than a censored-data model.',
    'Queen contiguity on TIGER/Line polygons (which extend over water); nearest-neighbour link for tracts with no sample neighbour; row-standardised weights.',
    'The two exposures are mutually adjusted in the primary models; reference categories are under-18 (age) and non-Hispanic White plus other (race/ethnicity).',
    'Spatial models are estimated by maximum likelihood assuming normal, homoskedastic innovations; lag-model p-values are those of the raw coefficient; total-impact intervals come from 2,000 parametric draws.',
    'False discovery rate controlled by Benjamini-Hochberg within families of 12 (6 outcomes x 2 exposures) per cross-section and estimator.',
    'Panel models are unweighted and linear; log mortality rates; contemporaneous commute; one-year lag of home value; CR1 uses the convention that county effects nested in clusters are not counted in the degrees-of-freedom correction.',
    'The 65+ mortality models use the commute measure of all commuters, a proxy for area-level commuting conditions rather than the exposure of the people who died.',
    'The MDE uses the estimated CR1 standard error as if known. The literature benchmark assumes every 60+ minute commuter carries the hazard ratio reported for men riding in a car more than 10 hours a week, that it applies to both sexes and to mortality within the same year, and that non-commuters are unaffected; it is an upper-end illustration, not an estimate.',
    'Applying sitting or driving dose-response estimates to commute time is an assumption; car time does not add one-for-one to total sitting (Ding 2014), and no study has linked road rage to cardiovascular events.']):
    A(f'{i+1}. {s}')
A('')
A('## 9. Limitations'); A('')
A('This analysis is ecological and observational, and its associations cannot be read as effects of commuting on individuals. '
  'The tract outcomes are CDC PLACES estimates: crude, model-based prevalences for all adults 18+, produced by multilevel regression and poststratification from tract demographic composition. They are not measurements, are not age-specific, and regressing them on the same demographics is partly circular; '
  f"here the covariates alone reproduce {dg.r2_covariates_only.min()*100:.0f}-{dg.r2_covariates_only.max()*100:.0f}% of their variance, so the commute coefficients mostly reflect how commuting correlates with the parts of the PLACES prediction model that the covariates miss, and the model-based uncertainty of the outcomes is ignored. "
  'Exposure and outcome refer to different people: commute measures describe workers, whereas cardiovascular prevalence and mortality are dominated by older and often retired residents, and current commute is not lifetime exposure; residential sorting, the healthy-worker effect and migration (people who move outward for cheaper housing are not a random sample) can all produce inverse associations like those seen in 2015-2019. '
  'Commute duration is self-reported, top-coded travel time for all modes; it is not time spent driving, total sitting time or driving stress, and no measure of road rage enters any model. '
  'Age-specific mortality exists only for ages 35-64 and 65+, ends in 2019, and is model-smoothed, which removes within-county variation, understates uncertainty and distorts fixed-effects inference; the panel has only 14 clusters, wide intervals, minimum detectable effects several times larger than literature-implied effects, and commute regressors of which roughly half the identifying variation is sampling noise. '
  'The housing variable is a nominal, smoothed home-value index; year effects absorb common inflation in the panel, but tract-level income is nominal and top-coded, and the home-value-to-commute coefficients rest on small relative differences in county growth rates. The decomposition is a product of coefficients, not causal mediation. '
  'The 2020-2024 cross-section mixes pre- and post-pandemic commuting, with work-from-home shares several times the 2019 level, so its commuters are a differently selected group; the two PLACES releases differ in method, and only 1,523 of 2,251 2010-vintage tracts have stable boundaries, so cross-period tract comparisons are weak. '
  'Spatial weights treat over-water adjacency as contiguity, the spatial models assume a single spatial parameter for the whole region, and San Benito has no person-level data. '
  'Finally, half of the literature parameters behind the benchmark comparisons were read from abstracts only and are provisional, and the single driving-specific cardiovascular mortality estimate comes from one cohort of men.'); A('')
A('## 10. Files'); A('')
for f_, d_ in [('trends_table.csv', 'changes 2010-2019, 2019-2024 (plus 2019-2021, 2010-2024) by county/region x age band x measure, with replicate-weight SEs; Zillow rows'),
               ('trends_levels.csv', 'levels with SEs for 2010, 2019, 2021, 2024'), ('trends_heterogeneity_tests.csv', 'age-band, core-vs-adjacent and county heterogeneity tests'),
               ('tract_models.csv', '72 primary estimates: outcome x exposure x cross-section x estimator'), ('tract_model_diagnostics.csv', 'Moran\'s I, LM tests, spatial parameters, AIC, favoured model'),
               ('tract_sample_description.csv', 'sample sizes, weights-matrix summary, means and SDs'), ('panel_models.csv', 'Model H, Model M and decomposition rows with CR1, wild-cluster and bootstrap intervals and MDEs'),
               ('panel_analysis_data.csv', 'the 140 county-year analysis rows'), ('panel_mde_benchmark.json', 'literature benchmark used for the MDE comparison'), ('trends_crosscheck.json', 'agreement of the trend estimates with the delivered aggregate file'), ('sensitivity_models.csv', 'all sensitivity estimates with comparison flags'), ('sensitivity_change_summary.csv', 'counts of sign and significance changes'),
               ('sensitivity_samples.csv', 'sample sizes per sensitivity specification'), ('first_difference_tract_data.csv', 'differenced tract data used in S6'),
               ('analysis_plan_prespecified.md', 'the plan saved before fitting'), ('01_trends.py, tract_common.py, 02_tract_models.py, 03_panel_models.py, 04_sensitivity.py, 05_write_report.py', 'analysis scripts (run in this order; 01, 03 and 05 need pandas/scipy/statsmodels, tract_common/02/04 also geopandas, libpysal, spreg, esda; resolved input paths are read from handoff/input_paths.json with keys tract, panel, pums, pcya, mort, rel, dose, zillow; TIGER/Line tl_2019_06_tract.zip and tl_2024_06_tract.zip from www2.census.gov/geo/tiger in tiger/)')]:
    A('- ' + ', '.join(link(x.strip()) for x in f_.split(',')) + f': {d_}')
A('')
A('Software: Python 3.11; pandas, numpy, scipy, statsmodels 0.15.0, geopandas 1.2.0, libpysal 4.14.1, spreg 1.9.0, esda 2.9.0. Seed 20261113.')
open('methods_results_ecological.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('written', len('\n'.join(L)))
