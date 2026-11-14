"""02_tract_models.py -- Step 2: pre-specified primary tract-level models (see analysis_plan_prespecified.md, section B).
6 outcomes x 2 jointly-entered exposures x 2 cross-sections x 3 estimators = 72 rows.
Outputs: tract_models.csv, tract_model_diagnostics.csv, tract_sample_description.csv
"""
import numpy as np, pandas as pd, tract_common as tc
t = tc.load_tracts()
allrows, alldiag, desc = [], [], []
for v, meta in tc.XS.items():
    s = tc.base_sample(t, v)
    w, eig, winfo = tc.build_w(s.tract_geoid, meta['tiger'])
    full = t[t.acs_vintage == v]
    desc.append(dict(cross_section=meta['label'], acs_vintage=v, tracts_in_file=len(full), tracts_with_places=int(full.has_places.sum()),
                     tracts_in_model=len(s), excluded=len(full)-len(s), population_in_model=float(s.pop_total.sum()), population_in_file=float(full.pop_total.sum()),
                     n_counties=int(s.county_fips.nunique()), n_core9_tracts=int(s.core9.sum()), income_topcoded_tracts=int(s.income_topcoded.sum()),
                     **{f'w_{k}': x for k, x in winfo.items()},
                     **{f'mean_{c}': float(s[c].mean()) for c in tc.EXPOSURES + list(tc.OUTCOMES)}, **{f'sd_{c}': float(s[c].std(ddof=1)) for c in tc.EXPOSURES + list(tc.OUTCOMES)},
                     corr_exposures=float(s[tc.EXPOSURES].corr().iloc[0, 1])))
    for oc in tc.OUTCOMES:
        rows, dg = tc.fit_all(s, w, eig, oc, tc.EXPOSURES, tc.COVARS)
        for r in rows: r.update(cross_section=meta['label'], acs_vintage=v, outcome_label=tc.OUTCOMES[oc], favoured_by_diagnostics=(r['estimator'] == dg['favoured_by_lm_rule']))
        dg.update(cross_section=meta['label'], acs_vintage=v, outcome_label=tc.OUTCOMES[oc], **{f'w_{k}': x for k, x in winfo.items()})
        allrows += rows; alldiag.append(dg)
res = pd.DataFrame(allrows)
res['q_bh_family12'] = res.groupby(['acs_vintage', 'estimator'])['p_value'].transform(tc.bh)
res['fdr_significant_q05'] = res['q_bh_family12'] < 0.05
res['outcome_unit'] = 'percentage points of crude prevalence, adults 18+ (PLACES model-based)'
res['model'] = 'both exposures entered jointly; covariates: age shares, log median household income (+top-code flag), poverty, bachelor+, NH Black, NH Asian, Hispanic, no-vehicle households; county fixed effects'
first = ['cross_section', 'acs_vintage', 'outcome', 'outcome_label', 'exposure', 'exposure_unit', 'estimator', 'estimate', 'se', 'ci95_lo', 'ci95_hi', 'z', 'p_value',
         'q_bh_family12', 'fdr_significant_q05', 'favoured_by_diagnostics', 'n_tracts']
res = res[first + [c for c in res.columns if c not in first]]
res.to_csv('tract_models.csv', index=False)
dg = pd.DataFrame(alldiag); firstd = ['cross_section', 'acs_vintage', 'outcome', 'outcome_label', 'n_tracts']
dg[firstd + [c for c in dg.columns if c not in firstd]].to_csv('tract_model_diagnostics.csv', index=False)
pd.DataFrame(desc).to_csv('tract_sample_description.csv', index=False)
print(res.shape, dg.shape)
