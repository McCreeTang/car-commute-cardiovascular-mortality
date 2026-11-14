"""nat06_plot_tables.py -- plot-ready tables and the position of the 15 Bay Area study counties.
No models beyond those already pre-specified: residualised values are Frisch-Waugh partial residuals of the primary M3 model.
"""
import numpy as np, pandas as pd
import nat_common as nc
from nat_common import CAR, TRANSIT, Fit, design, pct

d = nc.load_county()
x = nc.cross_section(d, 2019)
x['bay_area'] = np.where(x.fips.isin(nc.BAY9), 'core 9', np.where(x.fips.isin(nc.BAY6), 'adjacent 6', ''))
x['car_q_within_class'] = x.groupby('nchs_ur_2013')[CAR].transform(lambda s: pd.qcut(s, 4, labels=False)) + 1

# 1. county-level table with residualised values behind the primary model (M3)
Xo = design(x, [TRANSIT], 3)            # all M3 regressors except car hours
chk = []
for wname, w35, w65 in (('w', x.pop_35_64.values.astype(float), x.pop_65plus.values.astype(float)), ('u', None, None)):
    for band, col, w in (('35_64', 'mort_cvd_35_64', w35), ('65plus', 'mort_cvd_65plus', w65)):
        ry = Fit(np.log(x[col].values), Xo, w).resid
        rx = Fit(x[CAR].values, Xo, w).resid
        x[f'resid_logmort_{band}_{wname}'] = ry; x[f'resid_car_{band}_{wname}'] = rx
        ww = np.ones(len(x)) if w is None else w
        chk.append((band, wname, (ww * rx * ry).sum() / (ww * rx * rx).sum()))
cols = ['fips', 'county_name', 'state_abbr', 'census_region', 'nchs_ur_2013', 'nchs_ur_2013_label', 'metro_2013', 'bay_area', 'pop_total', 'pop_35_64', 'pop_65plus',
        CAR, CAR + '_moe', TRANSIT, 'drivealone_hours_wk_per_adult16', 'mean_tt_car_mid', 'car_commuters_per_adult16', 'workers_per_adult16', 'car_q_within_class',
        'mort_cvd_35_64', 'mort_cvd_65plus', 'mort_chd_35_64', 'mort_stroke_35_64', 'mort_cvd_35_64_men', 'mort_cvd_35_64_women', 'intpt_lat', 'intpt_lon'] + [c for c in x.columns if c.startswith('resid_')]
pt = x[cols].copy()
pt['log_mort_cvd_35_64'] = np.log(pt.mort_cvd_35_64); pt['log_mort_cvd_65plus'] = np.log(pt.mort_cvd_65plus)
pt.to_parquet('national_plot_tables.parquet', index=False)
cs = pd.read_csv('national_cross_section_models.csv')
for band, wname, slope in chk:
    ref = cs[(cs.outcome == ('mort_cvd_35_64' if band == '35_64' else 'mort_cvd_65plus')) & (cs['sample'] == 'all') & (cs.model == 'M3') & (cs.weighting == ('pop_weighted' if wname == 'w' else 'unweighted')) & (cs.term == 'car')].b.iloc[0]
    assert abs(slope - ref) < 1e-8, (band, wname, slope, ref)

# 2. coefficient ladder; 3. falsification contrasts
lad = cs[(cs.cause == 'cvd') & (cs.sex == 'all')][['outcome', 'age_band', 'sample', 'model', 'weighting', 'term', 'n', 'pct', 'pct_lo', 'pct_hi', 'p_cluster', 'pct_lo_conley200', 'pct_hi_conley200', 'p_conley200', 'mde_pct', 'primary']]
lad.to_csv('national_plot_coefficient_ladder.csv', index=False)
con = pd.read_csv('national_falsification_contrasts.csv')
con[(con.cause == 'cvd')].to_csv('national_plot_falsification.csv', index=False)

# 4. change model: county-level changes with residualised values (weighted and unweighted)
c = pd.read_csv('national_change_analysis_data.csv', dtype={'fips': str})
DC = [k for k in c.columns if k.startswith('d_') and k not in ('d_car',)]
Xc = c[DC].astype(float).copy(); Xc.insert(0, 'const', 1.0)
Xc = pd.concat([Xc, pd.get_dummies(c.nchs_ur_2006, prefix='ur06', drop_first=True).astype(float), pd.get_dummies(c.state_abbr, prefix='st', drop_first=True).astype(float)], axis=1)
chm = pd.read_csv('national_change_models.csv')
for wname, w in (('w', c.w_35_64.values.astype(float)), ('u', None)):
    ry = Fit(c.dlog_mort_cvd_35_64.values, Xc, w).resid; rx = Fit(c.d_car.values, Xc, w).resid
    c[f'resid_dlogmort_35_64_{wname}'] = ry; c[f'resid_dcar_{wname}'] = rx
    ww = np.ones(len(c)) if w is None else w
    ref = chm[(chm.outcome == 'mort_cvd_35_64') & (chm['sample'] == 'all') & (chm.weighting == ('pop_weighted' if wname == 'w' else 'unweighted')) & (chm.term == 'change in car hours')].b.iloc[0]
    assert abs((ww * rx * ry).sum() / (ww * rx * rx).sum() - ref) < 1e-8
c['bay_area'] = np.where(c.fips.isin(nc.BAY9), 'core 9', np.where(c.fips.isin(nc.BAY6), 'adjacent 6', ''))
c[['fips', 'county_name', 'state_abbr', 'nchs_ur_2006', 'bay_area', 'w_35_64', 'pop_2010', 'pop_2019', 'large65k', 'car_2010', 'car_2019', 'd_car', 'sv_car', 'transit_2010', 'transit_2019', 'd_transit',
   'mort_cvd_35_64_2010', 'mort_cvd_35_64_2019', 'dlog_mort_cvd_35_64', 'mort_cvd_65plus_2010', 'mort_cvd_65plus_2019', 'dlog_mort_cvd_65plus',
   'resid_dlogmort_35_64_w', 'resid_dcar_w', 'resid_dlogmort_35_64_u', 'resid_dcar_u']].to_csv('national_plot_change.csv', index=False)

# 5. matched-pair differences
mp = pd.read_csv('national_matched_pairs.csv', dtype={'fips_high': str, 'fips_low': str})
mp[['nchs_ur_2013', 'census_region', 'fips_high', 'name_high', 'state_high', 'fips_low', 'name_low', 'state_low', 'mahalanobis', 'logit_ps_diff', CAR + '_high', CAR + '_low', 'd_car', 'd_transit',
    'mort_cvd_35_64_high', 'mort_cvd_35_64_low', 'dlog_mort_cvd_35_64', 'mort_cvd_65plus_high', 'mort_cvd_65plus_low', 'dlog_mort_cvd_65plus']].to_csv('national_plot_matched_pairs.csv', index=False)

# 6. Bay Area position (descriptive percentiles among national units, 2015-2019)
a = d[d.acs_vintage == 2019].set_index('fips'); a0 = d[d.acs_vintage == 2010].set_index('fips')
def pctile(series, w=None):
    s = series.dropna()
    if w is None:
        return series.apply(lambda v: 100.0 * (s <= v).mean() if pd.notna(v) else np.nan)
    ww = w.loc[s.index].astype(float)
    return series.apply(lambda v: 100.0 * ww[s <= v].sum() / ww.sum() if pd.notna(v) else np.nan)
a['d_car'] = a[CAR] - a0[CAR]; a['d_transit'] = a[TRANSIT] - a0[TRANSIT]
a['dlog_mort_cvd_35_64'] = np.log(a.mort_cvd_35_64) - np.log(a0.mort_cvd_35_64); a['dlog_mort_cvd_65plus'] = np.log(a.mort_cvd_65plus) - np.log(a0.mort_cvd_65plus)
out = pd.DataFrame(index=nc.BAY9 + nc.BAY6)
out['county_name'] = a.county_name; out['group'] = ['core 9'] * 9 + ['adjacent 6'] * 6
out['nchs_ur_2013_label'] = a.nchs_ur_2013_label; out['pop_total_2015_2019'] = a.pop_total
for v, lab in ((CAR, 'car_hours'), (TRANSIT, 'transit_hours'), ('mort_cvd_35_64', 'mort_cvd_35_64'), ('mort_cvd_65plus', 'mort_cvd_65plus'), ('median_hh_income', 'median_hh_income'), ('share_bachelors_plus', 'share_bachelors_plus'),
               ('d_car', 'change_car_hours_2006_10_to_2015_19'), ('dlog_mort_cvd_35_64', 'dlog_mort_cvd_35_64'), ('dlog_mort_cvd_65plus', 'dlog_mort_cvd_65plus')):
    out[lab] = a[v]; out[lab + '_pctile_units'] = pctile(a[v]); out[lab + '_pctile_popweighted'] = pctile(a[v], a.pop_total)
xi = x.set_index('fips')
out['car_quartile_within_urban_rural_class'] = xi.car_q_within_class.reindex(out.index)
out['resid_logmort_35_64_M3_weighted'] = xi.resid_logmort_35_64_w.reindex(out.index)
out['matched_role'] = ''
out.loc[out.index.isin(mp.fips_high), 'matched_role'] = 'matched, high-driving'
out.loc[out.index.isin(mp.fips_low), 'matched_role'] = 'matched, low-driving'
out['n_units_exposure'] = int(a[CAR].notna().sum()); out['n_units_mort_35_64'] = int(a.mort_cvd_35_64.notna().sum()); out['n_units_mort_65plus'] = int(a.mort_cvd_65plus.notna().sum())
out.index.name = 'fips'
out.reset_index().to_csv('national_bay_area_position.csv', index=False)
print('done')
