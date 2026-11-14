"""nat02_cross_section.py -- T1: 2015-2019 cross-sectional ladder, falsification contrasts, benchmarks, MDE.
Follows national_prespecified_plan.md sections 3-5. Run from the workspace root after nat_common.py is present.
"""
import numpy as np, pandas as pd
from scipy import stats
import nat_common as nc
from nat_common import CAR, TRANSIT, Fit, design, pct

d = nc.load_county()
x = nc.cross_section(d, 2019)
D = nc.haversine_matrix(x.intpt_lat, x.intpt_lon)

OUTCOMES = [  # (column, cause, band, sex, weight column)
    ('mort_cvd_35_64', 'cvd', '35_64', 'all', 'pop_35_64'), ('mort_cvd_65plus', 'cvd', '65plus', 'all', 'pop_65plus'),
    ('mort_chd_35_64', 'chd', '35_64', 'all', 'pop_35_64'), ('mort_chd_65plus', 'chd', '65plus', 'all', 'pop_65plus'),
    ('mort_stroke_35_64', 'stroke', '35_64', 'all', 'pop_35_64'), ('mort_stroke_65plus', 'stroke', '65plus', 'all', 'pop_65plus'),
    ('mort_cvd_35_64_men', 'cvd', '35_64', 'men', 'pop_35_64'), ('mort_cvd_35_64_women', 'cvd', '35_64', 'women', 'pop_35_64'),
]
SAMPLES = {'all': np.ones(len(x), bool), 'metro': x.nchs_ur_2013.between(1, 4).values, 'nonmetro': x.nchs_ur_2013.between(5, 6).values}

rows, fits = [], {}
for col, cause, band, sex, wcol in OUTCOMES:
    for sname, smask in SAMPLES.items():
        if sname != 'all' and not (cause == 'cvd' and sex == 'all'):
            continue
        m = smask & x[col].notna().values
        xs = x[m]; Ds = D[np.ix_(m, m)]
        y = np.log(xs[col].values)
        for rung in range(5):
            X = design(xs, [CAR, TRANSIT], rung)
            for wname, w in (('pop_weighted', xs[wcol].values.astype(float)), ('unweighted', None)):
                f = Fit(y, X, w, xs.state_abbr.values, Ds)
                fits[(col, sname, rung, wname)] = (f, m)
                Vc = {h: f.conley(h) for h in (100, 200, 500)}
                weq = f.diff(CAR, TRANSIT, df=f.G - 1); weq_c = f.diff(CAR, TRANSIT, V=Vc[200])
                for term, tname in ((CAR, 'car'), (TRANSIT, 'transit')):
                    c = f.coef(term, df=f.G - 1); cc = f.coef(term, V=Vc[200])
                    rows.append(dict(
                        outcome=col, cause=cause, age_band=band, sex=sex, sample=sname, model=f'M{rung}', weighting=wname, term=tname,
                        n=f.n, n_states=f.G, n_params=f.k, r2=f.r2, b=c['b'], se_cluster=c['se'], p_cluster=c['p'],
                        pct=pct(c['b']), pct_lo=pct(c['lo']), pct_hi=pct(c['hi']),
                        se_conley100=np.sqrt(Vc[100][f.i(term), f.i(term)]), se_conley200=cc['se'],
                        se_conley500=np.sqrt(Vc[500][f.i(term), f.i(term)]), p_conley200=cc['p'],
                        pct_lo_conley200=pct(cc['lo']), pct_hi_conley200=pct(cc['hi']),
                        mde_pct=pct(nc.MDE_MULT * c['se']),
                        car_minus_transit_b=weq['d'], car_eq_transit_p_cluster=weq['p'], car_eq_transit_p_conley200=weq_c['p'],
                        primary=bool(col == 'mort_cvd_35_64' and sname == 'all' and rung == 3 and wname == 'pop_weighted' and term == CAR)))
res = pd.DataFrame(rows)

# multiplicity family B: car, M3, weighted, secondary outcomes
fb = (res.term == 'car') & (res.model == 'M3') & (res.weighting == 'pop_weighted') & (res['sample'] == 'all') & (res.outcome != 'mort_cvd_35_64')
res['family'] = np.where(res.primary, 'A (T1)', np.where(fb, 'B', ''))
res['q_family_B'] = np.nan
res.loc[fb, 'q_family_B'] = nc.bh(res.loc[fb, 'p_cluster'].values)
res.to_csv('national_cross_section_models.csv', index=False)

# ---- falsification contrasts: 35-64 minus 65+ (same units), every rung and weighting; causes cvd, chd, stroke
crow = []
for cause in ('cvd', 'chd', 'stroke'):
    for sname in SAMPLES:
        if sname != 'all' and cause != 'cvd':
            continue
        for rung in range(5):
            for wname in ('pop_weighted', 'unweighted'):
                f1, m1 = fits[(f'mort_{cause}_35_64', sname, rung, wname)]; f2, m2 = fits[(f'mort_{cause}_65plus', sname, rung, wname)]
                assert (m1 == m2).all()
                C = nc.cross_cov(f1, f2)
                for term, tname in ((CAR, 'car'), (TRANSIT, 'transit')):
                    j = f1.i(term)
                    b1, b2 = f1.b[j], f2.b[j]
                    se = np.sqrt(f1.V_cl[j, j] + f2.V_cl[j, j] - 2 * C[j, j])
                    dd = b1 - b2; crit = stats.t.ppf(0.975, f1.G - 1)
                    crow.append(dict(contrast='35_64 minus 65plus', cause=cause, sample=sname, model=f'M{rung}', weighting=wname, term=tname, n=f1.n,
                                     b_35_64=b1, b_65plus=b2, pct_35_64=pct(b1), pct_65plus=pct(b2), diff_b=dd, diff_se=se,
                                     diff_lo=dd - crit * se, diff_hi=dd + crit * se, diff_p=2 * stats.t.sf(abs(dd / se), f1.G - 1),
                                     ratio_65plus_to_35_64=b2 / b1, corr_between_equations=C[j, j] / np.sqrt(f1.V_cl[j, j] * f2.V_cl[j, j])))
con = pd.DataFrame(crow)
con.to_csv('national_falsification_contrasts.csv', index=False)

# ---- diagnostics: Moran's I of M3 residuals; quintile dose-response
diag = []
for col in ('mort_cvd_35_64', 'mort_cvd_65plus'):
    for wname in ('pop_weighted', 'unweighted'):
        f, m = fits[(col, 'all', 3, wname)]
        mi = nc.morans_i_knn(f.resid, None, None, dist=D[np.ix_(m, m)])
        diag.append(dict(kind='moran_M3_residuals', outcome=col, weighting=wname, level='', n=f.n, estimate=mi['I'], lo=np.nan, hi=np.nan, p=mi['p_perm'], note=f"z={mi['z']:.1f}; 8 nearest neighbours; 999 permutations"))
def wquantile(v, w, qs):
    o = np.argsort(v); cw = np.cumsum(w[o]) / w.sum()
    return np.interp(qs, cw, v[o])
cuts = wquantile(x[CAR].values, x.pop_35_64.values.astype(float), [0.2, 0.4, 0.6, 0.8])
x['car_q5'] = np.digitize(x[CAR].values, cuts) + 1
for col, wcol in (('mort_cvd_35_64', 'pop_35_64'), ('mort_cvd_65plus', 'pop_65plus')):
    dq = pd.get_dummies(x.car_q5, prefix='carq', drop_first=True).astype(float)
    X = pd.concat([design(x, [TRANSIT], 3), dq], axis=1)
    for wname, w in (('pop_weighted', x[wcol].values.astype(float)), ('unweighted', None)):
        f = Fit(np.log(x[col].values), X, w, x.state_abbr.values)
        for q in range(2, 6):
            c = f.coef(f'carq_{q}', df=f.G - 1)
            wq = x.pop_35_64.values
            diag.append(dict(kind='quintile_M3', outcome=col, weighting=wname, level=f'Q{q} vs Q1', n=int((x.car_q5 == q).sum()),
                             estimate=pct(c['b']), lo=pct(c['lo']), hi=pct(c['hi']), p=c['p'],
                             note=f"mean car hours Q{q} {np.average(x[CAR][x.car_q5 == q], weights=wq[x.car_q5 == q]):.3f}; Q1 {np.average(x[CAR][x.car_q5 == 1], weights=wq[x.car_q5 == 1]):.3f}; cuts {np.round(cuts, 3).tolist()}; n Q1 {int((x.car_q5 == 1).sum())}"))
pd.DataFrame(diag).to_csv('national_cross_section_diagnostics.csv', index=False)

# ---- sample description (exposures and covariates; weighted and unweighted)
desc = []
for v in [CAR, TRANSIT, 'mort_cvd_35_64', 'mort_cvd_65plus', 'pop_total'] + nc.AGE + nc.SES + ['log_density'] + nc.PLACES:
    s = x[v].astype(float); w = x.pop_35_64.astype(float)
    mu = np.average(s, weights=w)
    desc.append(dict(variable=v, n=int(s.notna().sum()), mean=s.mean(), sd=s.std(), p10=s.quantile(.1), median=s.median(), p90=s.quantile(.9),
                     wmean_pop35_64=mu, wsd_pop35_64=np.sqrt(np.average((s - mu) ** 2, weights=w))))
desc = pd.DataFrame(desc)
extra = dict(n_units=len(x), n_states=x.state_abbr.nunique(), pop_total=int(x.pop_total.sum()), n_metro=int(SAMPLES['metro'].sum()), n_nonmetro=int(SAMPLES['nonmetro'].sum()),
             corr_car_transit_unweighted=float(np.corrcoef(x[CAR], x[TRANSIT])[0, 1]),
             n_transit_ge_025=int((x[TRANSIT] >= 0.25).sum()),
             n_men=int(x.mort_cvd_35_64_men.notna().sum()), n_women=int(x.mort_cvd_35_64_women.notna().sum()))
a = d[d.acs_vintage == 2019]
extra['car_commuter_prev_16plus'] = float(a.car_commuters.sum() / a.pop_16plus.sum())
extra['car_commuter_prev_45_64'] = float(a.car_workers_45_64.sum() / a.pop_45_64.sum())
extra['car_commuter_prev_65plus'] = float(a.car_workers_65plus.sum() / a.pop_65plus.sum())
extra['k_45_64'] = extra['car_commuter_prev_45_64'] / extra['car_commuter_prev_16plus']
extra['k_65plus'] = extra['car_commuter_prev_65plus'] / extra['car_commuter_prev_16plus']
extra['ratio_65plus_to_45_64_prev'] = extra['car_commuter_prev_65plus'] / extra['car_commuter_prev_45_64']
desc.to_csv('national_cross_section_sample.csv', index=False)
import json; json.dump(extra, open('national_cross_section_sample_extra.json', 'w'), indent=1)

# ---- benchmarks against the primary estimate and its MDE
bm = nc.benchmarks()
k = extra['k_45_64']
bm['pct_x_age_concentration'] = pct(np.log1p(bm.pct / 100) * k); bm['age_concentration_factor'] = k
prim = res[res.primary].iloc[0]
for wname in ('pop_weighted', 'unweighted'):
    r = res[(res.outcome == 'mort_cvd_35_64') & (res['sample'] == 'all') & (res.model == 'M3') & (res.weighting == wname) & (res.term == 'car')].iloc[0]
    bm[f'M3_{wname}_pct'] = r.pct; bm[f'M3_{wname}_pct_lo'] = r.pct_lo; bm[f'M3_{wname}_pct_hi'] = r.pct_hi; bm[f'M3_{wname}_mde_pct'] = r.mde_pct
    bm[f'M3_{wname}_mde_over_benchmark'] = r.mde_pct / bm.pct
    bm[f'M3_{wname}_benchmark_inside_ci'] = (bm.pct >= r.pct_lo) & (bm.pct <= r.pct_hi)
bm.to_csv('national_benchmarks.csv', index=False)
print('done', len(res), len(con))
