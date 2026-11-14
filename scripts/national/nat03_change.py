"""nat03_change.py -- T2: change in log mortality (2015-2019 minus 2006-2010) on change in car and transit hours.
Follows national_prespecified_plan.md section 6.
"""
import numpy as np, pandas as pd, json
from scipy import stats
import nat_common as nc
from nat_common import CAR, TRANSIT, Fit, pct

d = nc.load_county()
a = d[(d.acs_vintage == 2010) & d.complete_case_main].set_index('fips')
b = d[(d.acs_vintage == 2019) & d.complete_case_main].set_index('fips')
ix = a.index.intersection(b.index)
a, b = a.loc[ix], b.loc[ix]

DCOV = ['share_age_18_34', 'share_age_35_64', 'share_age_65plus', 'share_female', 'log_income', 'poverty_rate', 'share_bachelors_plus',
        'share_less_than_hs', 'unemployment_rate', 'share_nh_black', 'share_hispanic', 'share_nh_asian', 'share_nh_aian', 'log_density']
c = pd.DataFrame(index=ix)
c['state_abbr'] = b.state_abbr; c['nchs_ur_2006'] = b.nchs_ur_2006.astype(int); c['nchs_ur_2013'] = b.nchs_ur_2013.astype(int)
c['intpt_lat'] = b.intpt_lat; c['intpt_lon'] = b.intpt_lon; c['county_name'] = b.county_name
c['d_car'] = b[CAR] - a[CAR]; c['d_transit'] = b[TRANSIT] - a[TRANSIT]
c['car_2010'] = a[CAR]; c['car_2019'] = b[CAR]; c['transit_2010'] = a[TRANSIT]; c['transit_2019'] = b[TRANSIT]
for v in DCOV:
    c['d_' + v] = b[v] - a[v]
for o in ('mort_cvd_35_64', 'mort_cvd_65plus', 'mort_chd_35_64', 'mort_stroke_35_64'):
    c['dlog_' + o] = np.log(b[o]) - np.log(a[o]); c[o + '_2010'] = a[o]; c[o + '_2019'] = b[o]
c['w_35_64'] = (a.pop_35_64 + b.pop_35_64) / 2.0; c['w_65plus'] = (a.pop_65plus + b.pop_65plus) / 2.0
c['pop_2010'] = a.pop_total; c['pop_2019'] = b.pop_total
c['sv_car'] = (a[CAR + '_moe'] / 1.645) ** 2 + (b[CAR + '_moe'] / 1.645) ** 2          # sampling variance of the change
c['sv_transit'] = (a[TRANSIT + '_moe'] / 1.645) ** 2 + (b[TRANSIT + '_moe'] / 1.645) ** 2
c['large65k'] = (c.pop_2010 >= 65000) & (c.pop_2019 >= 65000)
c = c.reset_index()
c.to_csv('national_change_analysis_data.csv', index=False)

def dmat(df, drop=None):
    terms = ['d_car', 'd_transit'] + ['d_' + v for v in DCOV]
    if drop: terms = [t for t in terms if t != drop]
    X = df[terms].astype(float).copy(); X.insert(0, 'const', 1.0)
    ur = pd.get_dummies(df.nchs_ur_2006, prefix='ur06', drop_first=True).astype(float)
    st = pd.get_dummies(df.state_abbr, prefix='st', drop_first=True).astype(float)
    X = pd.concat([X, ur, st], axis=1)
    return X.loc[:, X.abs().sum(axis=0) > 0]

rows = []
OUT = [('mort_cvd_35_64', 'w_35_64', 'primary (T2)'), ('mort_cvd_65plus', 'w_65plus', 'falsification'),
       ('mort_chd_35_64', 'w_35_64', 'secondary'), ('mort_stroke_35_64', 'w_35_64', 'secondary')]
for sname, mask in (('all', np.ones(len(c), bool)), ('pop>=65,000 both periods', c.large65k.values)):
    cs = c[mask].reset_index(drop=True)
    Dm = nc.haversine_matrix(cs.intpt_lat, cs.intpt_lon)
    X = dmat(cs)
    for o, wcol, role in OUT:
        y = cs['dlog_' + o].values
        for wname, w in (('pop_weighted', cs[wcol].values.astype(float)), ('unweighted', np.ones(len(cs)))):
            f = Fit(y, X, w, cs.state_abbr.values, Dm)
            Vc = f.conley(200)
            weq = f.diff('d_car', 'd_transit', df=f.G - 1)
            for term, sv in (('d_car', 'sv_car'), ('d_transit', 'sv_transit')):
                co = f.coef(term, df=f.G - 1); cc = f.coef(term, V=Vc)
                # reliability of the exposure change
                xv = cs[term].values; mu = np.average(xv, weights=w)
                var_raw = np.average((xv - mu) ** 2, weights=w); noise = np.average(cs[sv].values, weights=w)
                Xo = dmat(cs, drop=term)
                fx = Fit(xv, Xo, w)                                   # partial out all other regressors and fixed effects
                var_cond = np.average(fx.resid ** 2, weights=w) * f.n / (f.n - fx.k)
                rel_raw = 1 - noise / var_raw; rel_cond = 1 - noise / var_cond
                rows.append(dict(outcome=o, role=role, sample=sname, weighting=wname, term=term.replace('d_', 'change in ') + ' hours',
                                 n=f.n, n_states=f.G, r2=f.r2, b=co['b'], se_cluster=co['se'], p_cluster=co['p'],
                                 pct=pct(co['b']), pct_lo=pct(co['lo']), pct_hi=pct(co['hi']),
                                 se_conley200=cc['se'], p_conley200=cc['p'], pct_lo_conley200=pct(cc['lo']), pct_hi_conley200=pct(cc['hi']),
                                 mde_pct=pct(nc.MDE_MULT * co['se']), car_eq_transit_p_cluster=weq['p'],
                                 sd_exposure_change=np.sqrt(var_raw), mean_exposure_change=mu, sd_exposure_change_conditional=np.sqrt(var_cond),
                                 mean_sampling_sd=np.sqrt(noise), reliability_raw=rel_raw, reliability_conditional=rel_cond,
                                 pct_corrected_for_attenuation=pct(co['b'] / rel_cond) if rel_cond > 0 else np.nan,
                                 mde_pct_true_scale=pct(nc.MDE_MULT * co['se'] / rel_cond) if rel_cond > 0 else np.nan,
                                 mean_dlog_outcome=np.average(y, weights=w), sd_dlog_outcome=np.sqrt(np.average((y - np.average(y, weights=w)) ** 2, weights=w))))
res = pd.DataFrame(rows)
res.to_csv('national_change_models.csv', index=False)
desc = dict(n_units=len(c), n_large=int(c.large65k.sum()), n_states=int(c.state_abbr.nunique()),
            share_units_car_increase=float((c.d_car > 0).mean()),
            wmean_car_2010=float(np.average(c.car_2010, weights=c.w_35_64)), wmean_car_2019=float(np.average(c.car_2019, weights=c.w_35_64)),
            mean_car_2010=float(c.car_2010.mean()), mean_car_2019=float(c.car_2019.mean()),
            wmean_mort35_64_2010=float(np.average(c.mort_cvd_35_64_2010, weights=c.w_35_64)), wmean_mort35_64_2019=float(np.average(c.mort_cvd_35_64_2019, weights=c.w_35_64)),
            wmean_mort65_2010=float(np.average(c.mort_cvd_65plus_2010, weights=c.w_65plus)), wmean_mort65_2019=float(np.average(c.mort_cvd_65plus_2019, weights=c.w_65plus)),
            pop_share_large=float(c.pop_2019[c.large65k].sum() / c.pop_2019.sum()))
json.dump(desc, open('national_change_sample.json', 'w'), indent=1)
print('done', len(res))
