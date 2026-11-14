"""04_sensitivity.py -- Step 4: pre-specified sensitivity analyses S1-S8 (analysis_plan_prespecified.md, section D).
Outputs: sensitivity_models.csv, sensitivity_change_summary.csv, sensitivity_samples.csv
"""
import json, numpy as np, pandas as pd, statsmodels.api as sm, tract_common as tc
from scipy import stats
t = tc.load_tracts(); P = tc.P
prim = pd.read_csv('tract_models.csv')
rows, samples = [], []
def run(spec, spec_label, v, s, exposures, covars, estimators=('ols','error','lag'), weights=None, tiger=None, compare_exposure=None, compare_vintage=None):
    meta = tc.XS[v]
    if 'error' in estimators or 'lag' in estimators:
        w, eig, winfo = tc.build_w(s.tract_geoid, tiger or meta['tiger'])
    else: w, eig, winfo = None, None, {}
    samples.append(dict(spec=spec, spec_label=spec_label, acs_vintage=v, n_tracts=len(s), n_counties=int(s.county_fips.nunique()), **{f'w_{k}': x for k, x in winfo.items()}))
    for oc in tc.OUTCOMES:
        rr, dg = tc.fit_all(s, w, eig, oc, exposures, covars, estimators=estimators, weights=weights, perm=0)
        for r in rr:
            r.update(spec=spec, spec_label=spec_label, cross_section=meta['label'], acs_vintage=v, outcome_label=tc.OUTCOMES[oc],
                     compare_exposure=(compare_exposure or {}).get(r['exposure'], r['exposure']), compare_vintage=compare_vintage or v,
                     moran_I_ols_resid=dg.get('moran_I_ols_resid', np.nan), n_counties=int(s.county_fips.nunique()))
        rows.extend(rr)
for v in tc.XS:
    s = tc.base_sample(t, v)
    # S1 core9 only
    run('S1', 'nine core counties only', v, s[s.core9.astype(bool)].reset_index(drop=True), tc.EXPOSURES, tc.COVARS)
    # S2 exclude top decile of transit share
    thr = s.share_transit.quantile(0.90)
    run('S2', f'excluding top decile of transit share (share_transit > {thr:.4f})', v, s[s.share_transit <= thr].reset_index(drop=True), tc.EXPOSURES, tc.COVARS)
    # S3 alternative exposure definitions
    for alt, lab in [('mean_commute_min', 'mean commute minutes'), ('share_commute_45plus', '45+ minute share'), ('share_commute_90plus', '90+ minute share')]:
        sa = s[s[alt].notna()].reset_index(drop=True)
        run(f'S3_{alt}', f'alternative exposure: {lab} replaces 60+ share', v, sa, [alt, 'share_drive_alone'], tc.COVARS, compare_exposure={alt: 'share_commute_60plus'})
    # S4 add smoking
    run('S4', 'adding PLACES current smoking prevalence as covariate', v, s[s.csmoking_prev.notna()].reset_index(drop=True), tc.EXPOSURES, tc.COVARS + ['csmoking_prev'])
    # S5 population weighted
    run('S5', 'weighted by adult population (WLS) vs unweighted OLS', v, s, tc.EXPOSURES, tc.COVARS, estimators=('wls',), weights=s['adult_pop'].to_numpy(float))
    # S8 single exposure
    for e in tc.EXPOSURES:
        run(f'S8_{e}', f'single exposure: {e} without the other exposure', v, s, [e], tc.COVARS)
# S6 first difference on boundary-stable tracts
s19, s24 = tc.base_sample(t, 2019), tc.base_sample(t, 2024)
a = s19[s19.boundary_stable_99.fillna(False).astype(bool)].set_index('tract_geoid'); b = s24[s24.boundary_stable_99.fillna(False).astype(bool)].set_index('tract_geoid')
common = a.index.intersection(b.index)
dcols = list(tc.OUTCOMES) + tc.EXPOSURES + [c for c in tc.COVARS if c != 'income_topcoded']
fd = (b.loc[common, dcols] - a.loc[common, dcols])
fd['income_topcoded_2019'] = a.loc[common, 'income_topcoded']; fd['income_topcoded_2024'] = b.loc[common, 'income_topcoded']
fd['county_fips'] = b.loc[common, 'county_fips']; fd = fd.reset_index()
fd_cov = [c for c in tc.COVARS if c != 'income_topcoded'] + ['income_topcoded_2019', 'income_topcoded_2024']
run('S6', 'first difference 2015-2019 -> 2020-2024 on boundary-stable tracts (PLACES method changed between releases)', 2024, fd, tc.EXPOSURES, fd_cov,
    estimators=('ols', 'error'), tiger=2024, compare_vintage=2019)
fd.to_csv('first_difference_tract_data.csv', index=False)
sens = pd.DataFrame(rows)
sens['q_bh_family12'] = sens.groupby(['spec', 'acs_vintage', 'estimator'])['p_value'].transform(tc.bh)
# ---- comparison with the primary estimates
key_est = {'WLS adult-population weights (HC1)': 'OLS (HC1)'}
sens['primary_estimator'] = sens['estimator'].replace(key_est)
pm = prim[['acs_vintage', 'outcome', 'exposure', 'estimator', 'estimate', 'p_value', 'ci95_lo', 'ci95_hi']].rename(
    columns={'acs_vintage': 'compare_vintage', 'exposure': 'compare_exposure', 'estimator': 'primary_estimator', 'estimate': 'primary_estimate', 'p_value': 'primary_p',
             'ci95_lo': 'primary_ci95_lo', 'ci95_hi': 'primary_ci95_hi'})
sens = sens.merge(pm, on=['compare_vintage', 'outcome', 'compare_exposure', 'primary_estimator'], how='left')
sens['sign_differs'] = np.sign(sens.estimate) != np.sign(sens.primary_estimate)
sens['nominal_sig'] = sens.p_value < 0.05; sens['primary_nominal_sig'] = sens.primary_p < 0.05
sens['significance_changes'] = sens.nominal_sig != sens.primary_nominal_sig
same_unit = sens.exposure == sens.compare_exposure
sens['ratio_to_primary'] = np.where(same_unit, sens.estimate / sens.primary_estimate, np.nan)
sens['outside_primary_ci'] = np.where(same_unit, (sens.estimate < sens.primary_ci95_lo) | (sens.estimate > sens.primary_ci95_hi), np.nan)
sens['sign_reversal_both_significant'] = sens.sign_differs & sens.nominal_sig & sens.primary_nominal_sig
sens['level'] = 'tract'

# ---- S7 county mortality in place of model-based prevalence (n = 15)
pan = pd.read_parquet(P['panel'])
def county_rows(v, ydf, ylab, ycol):
    x = pan[pan.year == v].set_index('county_fips')[['acs5_share_commute_60plus', 'acs5_share_drive_alone', 'acs5_median_hh_income', 'core9']].join(ydf)
    out = []
    for e, ee in [('acs5_share_commute_60plus', 'share_commute_60plus'), ('acs5_share_drive_alone', 'share_drive_alone')]:
        ly = np.log(x[ycol].astype(float))
        for adj, lab in [([], 'County OLS (HC3), unadjusted'), (['acs5_median_hh_income'], 'County OLS (HC3), adjusted for log median household income')]:
            X = pd.DataFrame({'x': x[e].astype(float)}); 
            for a_ in adj: X[a_] = np.log(x[a_].astype(float))
            m = sm.OLS(ly, sm.add_constant(X)).fit(cov_type='HC3', use_t=True)
            ci = m.conf_int().loc['x']
            mc = sm.OLS(ly, sm.add_constant(X)).fit()            # classical SE, reported alongside (added after seeing that one county has leverage > 0.7)
            lev = mc.get_influence().hat_matrix_diag
            out.append(dict(spec='S7', spec_label='county cardiovascular mortality (model-smoothed) in place of PLACES prevalence', level='county', acs_vintage=v, cross_section=tc.XS[v]['label'],
                            outcome=ycol, outcome_label=ylab, exposure=ee, exposure_unit='per 10 percentage points; outcome is log rate (x100 = approx % difference)', estimator=lab,
                            estimate=m.params['x']*0.10, se=m.bse['x']*0.10, ci95_lo=ci[0]*0.10, ci95_hi=ci[1]*0.10, z=m.tvalues['x'], p_value=m.pvalues['x'], n_tracts=np.nan, n_counties=int(m.nobs),
                            se_classical=mc.bse['x']*0.10, p_value_classical=mc.pvalues['x'], max_leverage=float(lev.max()), max_leverage_county=str(x.index[int(np.argmax(lev))])))
        rho, p = stats.spearmanr(x[e], x[ycol])
        out.append(dict(spec='S7', spec_label='county cardiovascular mortality (model-smoothed) in place of PLACES prevalence', level='county', acs_vintage=v, cross_section=tc.XS[v]['label'],
                        outcome=ycol, outcome_label=ylab, exposure=ee, exposure_unit='Spearman rank correlation (unitless)', estimator='Spearman correlation', estimate=rho, se=np.nan,
                        ci95_lo=np.nan, ci95_hi=np.nan, z=np.nan, p_value=p, n_tracts=np.nan, n_counties=int(len(x))))
    return out
m1519 = pan[pan.year.between(2015, 2019)].groupby('county_fips')[['mort_cvd_35_64', 'mort_cvd_65plus', 'mort_chd_35_64', 'mort_chd_65plus']].mean()
c7 = []
for col, lab in [('mort_cvd_35_64', 'All CVD mortality 35-64, mean 2015-2019'), ('mort_cvd_65plus', 'All CVD mortality 65+, mean 2015-2019'),
                 ('mort_chd_35_64', 'CHD mortality 35-64, mean 2015-2019'), ('mort_chd_65plus', 'CHD mortality 65+, mean 2015-2019')]:
    c7 += county_rows(2019, m1519[[col]], lab, col)
p2223 = pan[pan.year.isin([2022, 2023])].groupby('county_fips')[['pooled3yr_hd_35plus', 'pooled3yr_stroke_35plus']].mean()
for col, lab in [('pooled3yr_hd_35plus', 'Heart disease mortality 35+, pooled 3-year rates (midpoints 2022, 2023 averaged)'),
                 ('pooled3yr_stroke_35plus', 'Stroke mortality 35+, pooled 3-year rates (midpoints 2022, 2023 averaged)')]:
    c7 += county_rows(2024, p2223[[col]], lab, col)
c7 = pd.DataFrame(c7); c7['nominal_sig'] = c7.p_value < 0.05
allsens = pd.concat([sens, c7], ignore_index=True, sort=False)
first = ['spec', 'spec_label', 'level', 'cross_section', 'acs_vintage', 'outcome', 'outcome_label', 'exposure', 'exposure_unit', 'estimator', 'estimate', 'se', 'ci95_lo', 'ci95_hi', 'p_value',
         'q_bh_family12', 'n_tracts', 'n_counties', 'primary_estimate', 'primary_p', 'ratio_to_primary', 'sign_differs', 'nominal_sig', 'primary_nominal_sig', 'significance_changes',
         'sign_reversal_both_significant', 'outside_primary_ci']
allsens = allsens[first + [c for c in allsens.columns if c not in first]]
allsens.to_csv('sensitivity_models.csv', index=False)
pd.DataFrame(samples).to_csv('sensitivity_samples.csv', index=False)
# ---- summary of changes
g = sens.groupby(['spec', 'spec_label', 'acs_vintage', 'exposure', 'estimator'])
summ = g.agg(n_models=('estimate', 'size'), n_sign_differs=('sign_differs', 'sum'), n_significance_changes=('significance_changes', 'sum'),
             n_sign_reversal_both_significant=('sign_reversal_both_significant', 'sum'), n_nominal_sig=('nominal_sig', 'sum'), n_primary_nominal_sig=('primary_nominal_sig', 'sum'),
             n_fdr_sig=('q_bh_family12', lambda q: int((q < 0.05).sum())), n_outside_primary_ci=('outside_primary_ci', 'sum'),
             median_ratio_to_primary=('ratio_to_primary', 'median')).reset_index()
summ.to_csv('sensitivity_change_summary.csv', index=False)
print(allsens.shape, summ.shape, len(common))
