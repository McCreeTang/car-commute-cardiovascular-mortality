"""nat04_matched.py -- T3: matched high- versus low-driving counties, 2015-2019.
Follows national_prespecified_plan.md section 7.
"""
import numpy as np, pandas as pd, json
from scipy import stats
from scipy.optimize import linear_sum_assignment
import statsmodels.api as sm
import nat_common as nc
from nat_common import CAR, TRANSIT, Fit, pct

d = nc.load_county()
x = nc.cross_section(d, 2019)
MATCH = ['share_age_35_64', 'share_age_65plus', 'share_female', 'log_income', 'poverty_rate', 'share_bachelors_plus',
         'unemployment_rate', 'share_nh_black', 'share_hispanic', 'share_uninsured_18_64', 'log_density']
OTHER = ['share_less_than_hs', 'share_nh_asian', 'share_nh_aian', 'share_no_vehicle_hh', 'workers_per_adult16'] + nc.PLACES + ['intpt_lat', 'intpt_lon']

x['car_q'] = x.groupby('nchs_ur_2013')[CAR].transform(lambda s: pd.qcut(s, 4, labels=False))
g = x[x.car_q.isin([0, 3])].copy().reset_index(drop=True)
g['high'] = (g.car_q == 3).astype(int)

# propensity score
Xp = g[MATCH].astype(float)
Xp = pd.concat([Xp, pd.get_dummies(g.nchs_ur_2013.astype(int), prefix='ur', drop_first=True).astype(float),
                pd.get_dummies(g.census_region, prefix='reg', drop_first=True).astype(float)], axis=1)
Xp = sm.add_constant(Xp)
ps_fit = sm.Logit(g.high.values, Xp).fit(disp=0, maxiter=200)
g['logit_ps'] = ps_fit.fittedvalues if hasattr(ps_fit, 'fittedvalues') else Xp.values @ ps_fit.params.values
caliper = 0.2 * g.logit_ps.std(ddof=1)

Sinv = np.linalg.inv(np.cov(g[MATCH].astype(float).values, rowvar=False))
BIG = 1e6
pairs = []
for (ur, reg), s in g.groupby(['nchs_ur_2013', 'census_region']):
    T = s[s.high == 1]; C = s[s.high == 0]
    if len(T) == 0 or len(C) == 0:
        continue
    A = T[MATCH].astype(float).values; B = C[MATCH].astype(float).values
    diff = A[:, None, :] - B[None, :, :]
    M = np.sqrt(np.einsum('ijk,kl,ijl->ij', diff, Sinv, diff))
    bad = np.abs(T.logit_ps.values[:, None] - C.logit_ps.values[None, :]) > caliper
    cost = np.where(bad, BIG, M)
    r, cidx = linear_sum_assignment(cost)
    for i, j in zip(r, cidx):
        if cost[i, j] < BIG:
            pairs.append(dict(nchs_ur_2013=int(ur), census_region=reg, fips_high=T.fips.values[i], fips_low=C.fips.values[j], mahalanobis=M[i, j],
                              logit_ps_diff=T.logit_ps.values[i] - C.logit_ps.values[j]))
pairs = pd.DataFrame(pairs)
gi = g.set_index('fips')
H = gi.loc[pairs.fips_high]; L = gi.loc[pairs.fips_low]
keep = [CAR, TRANSIT, 'mort_cvd_35_64', 'mort_cvd_65plus', 'pop_total'] + MATCH + OTHER
for v in keep:
    pairs[v + '_high'] = H[v].values.astype(float); pairs[v + '_low'] = L[v].values.astype(float)
pairs['state_high'] = H.state_abbr.values; pairs['state_low'] = L.state_abbr.values
pairs['name_high'] = H.county_name.values; pairs['name_low'] = L.county_name.values
pairs['d_car'] = pairs[CAR + '_high'] - pairs[CAR + '_low']; pairs['d_transit'] = pairs[TRANSIT + '_high'] - pairs[TRANSIT + '_low']
pairs['dlog_mort_cvd_35_64'] = np.log(pairs.mort_cvd_35_64_high) - np.log(pairs.mort_cvd_35_64_low)
pairs['dlog_mort_cvd_65plus'] = np.log(pairs.mort_cvd_65plus_high) - np.log(pairs.mort_cvd_65plus_low)
pairs.to_csv('national_matched_pairs.csv', index=False)

# balance
def smd(a, b, sd):
    return (np.mean(a) - np.mean(b)) / sd
bal = []
for v in MATCH + OTHER + [CAR, TRANSIT, 'logit_ps']:
    t = g.loc[g.high == 1, v].astype(float); c0 = g.loc[g.high == 0, v].astype(float)
    sd = np.sqrt((t.var(ddof=1) + c0.var(ddof=1)) / 2)
    tm = gi.loc[pairs.fips_high, v].astype(float); cm = gi.loc[pairs.fips_low, v].astype(float)
    bal.append(dict(variable=v, role='matched on' if v in MATCH else ('exposure' if v in (CAR, TRANSIT) else ('propensity score' if v == 'logit_ps' else 'not matched on')),
                    mean_high_before=t.mean(), mean_low_before=c0.mean(), smd_before=smd(t, c0, sd),
                    mean_high_after=tm.mean(), mean_low_after=cm.mean(), smd_after=smd(tm, cm, sd), pooled_sd_before=sd))
bal = pd.DataFrame(bal)
bal.to_csv('national_matched_balance.csv', index=False)
balance_ok = bool((bal.loc[bal.role == 'matched on', 'smd_after'].abs() < 0.1).all())

# counts
cnt = g.groupby(['nchs_ur_2013', 'census_region', 'high']).size().unstack('high', fill_value=0).rename(columns={0: 'low_available', 1: 'high_available'})
cnt['pairs'] = pairs.groupby(['nchs_ur_2013', 'census_region']).size().reindex(cnt.index).fillna(0).astype(int)
cnt = cnt.reset_index(); cnt.to_csv('national_matched_counts.csv', index=False)

def evalue(rr):
    rr = rr if rr >= 1 else 1 / rr
    return rr + np.sqrt(rr * (rr - 1))

def rosenbaum(dv):
    dv = dv[dv != 0]; n = len(dv)
    sgn = np.sign(np.mean(dv)) if np.mean(dv) != 0 else 1.0
    dd = dv * sgn                                   # test in the direction of the observed mean difference
    rk = stats.rankdata(np.abs(dd)); Tplus = rk[dd > 0].sum()
    out = []
    for G in np.round(np.arange(1.0, 3.0001, 0.05), 2):
        p = G / (1 + G)
        mu = p * n * (n + 1) / 2; var = p * (1 - p) * n * (n + 1) * (2 * n + 1) / 6
        out.append((G, stats.norm.sf((Tplus - mu) / np.sqrt(var))))
    out = pd.DataFrame(out, columns=['gamma', 'p_upper_one_sided'])
    sig = out[out.p_upper_one_sided < 0.025]
    return out, (float(sig.gamma.max()) if len(sig) else np.nan), float(out.p_upper_one_sided.iloc[0])

rows = []; ros_all = []
dX = pd.DataFrame({v: pairs[v + '_high'] - pairs[v + '_low'] for v in MATCH}); dX.insert(0, 'const', 1.0)
ones = pd.DataFrame({'const': np.ones(len(pairs))})
for o, role in (('mort_cvd_35_64', 'primary (T3)'), ('mort_cvd_65plus', 'falsification')):
    y = pairs['dlog_' + o].values; n = len(y)
    ros, gmax, p1 = rosenbaum(y); ros['outcome'] = o; ros_all.append(ros)
    wil = stats.wilcoxon(y)
    for est, X in (('unadjusted pair difference', ones), ('regression-adjusted for covariate differences', dX)):
        f = Fit(y, X, None, pairs.state_high.values)
        co = f.coef('const', df=f.G - 1)
        rr, lo, hi = np.exp(co['b']), np.exp(co['lo']), np.exp(co['hi'])
        near = hi if co['b'] < 0 else lo
        ev_ci = 1.0 if (lo <= 1 <= hi) else evalue(near)
        row = dict(outcome=o, role=role, estimator=est, n_pairs=n, n_state_clusters=f.G, mean_dlog=co['b'], se_cluster=co['se'], p_cluster=co['p'],
                   pct=pct(co['b']), pct_lo=pct(co['lo']), pct_hi=pct(co['hi']), rate_ratio=rr, e_value_point=evalue(rr), e_value_ci=ev_ci,
                   mean_d_car_hours=pairs.d_car.mean(), pct_per_hour=pct(co['b'] / pairs.d_car.mean()),
                   pct_per_hour_lo=pct(co['lo'] / pairs.d_car.mean()), pct_per_hour_hi=pct(co['hi'] / pairs.d_car.mean()),
                   mde_pct=pct((stats.t.ppf(0.975, f.G - 1) + stats.t.ppf(0.8, f.G - 1)) * co['se']))
        if est.startswith('unadjusted'):
            se_t = y.std(ddof=1) / np.sqrt(n); tc = stats.t.ppf(0.975, n - 1)
            row.update(pct_lo_paired_t=pct(y.mean() - tc * se_t), pct_hi_paired_t=pct(y.mean() + tc * se_t), p_paired_t=2 * stats.t.sf(abs(y.mean() / se_t), n - 1),
                       wilcoxon_p=wil.pvalue, share_pairs_high_higher=float((y > 0).mean()), rosenbaum_p_gamma1_one_sided=p1,
                       rosenbaum_gamma_max=gmax, sd_pair_diff=y.std(ddof=1))
        rows.append(row)
res = pd.DataFrame(rows)
res['balance_target_met'] = balance_ok
res['estimate_to_interpret'] = np.where(res.estimator.str.startswith('unadjusted') == balance_ok, True, False)
res.to_csv('national_matched_contrast.csv', index=False)
pd.concat(ros_all).to_csv('national_matched_rosenbaum.csv', index=False)
meta = dict(n_sample=len(x), n_high=int(g.high.sum()), n_low=int((1 - g.high).sum()), n_pairs=len(pairs), n_high_discarded=int(g.high.sum() - len(pairs)),
            n_low_discarded=int((1 - g.high).sum() - len(pairs)), caliper_logit=float(caliper), sd_logit_ps=float(g.logit_ps.std(ddof=1)),
            ps_converged=bool(ps_fit.mle_retvals['converged']), balance_target_met=balance_ok,
            max_abs_smd_matched_before=float(bal.loc[bal.role == 'matched on', 'smd_before'].abs().max()),
            max_abs_smd_matched_after=float(bal.loc[bal.role == 'matched on', 'smd_after'].abs().max()),
            max_abs_smd_unmatched_after=float(bal.loc[bal.role == 'not matched on', 'smd_after'].abs().max()),
            mean_car_high=float(pairs[CAR + '_high'].mean()), mean_car_low=float(pairs[CAR + '_low'].mean()),
            pairs_same_state=int((pairs.state_high == pairs.state_low).sum()), median_mahalanobis=float(pairs.mahalanobis.median()))
json.dump(meta, open('national_matched_meta.json', 'w'), indent=1)
print(meta)
