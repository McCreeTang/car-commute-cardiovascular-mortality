"""03_panel_models.py -- Step 3: county-year two-way fixed-effects models, 2010-2019, 14 counties.
Housing -> commute; commute -> age-specific cardiovascular mortality; product-of-coefficients decomposition.
NOT causal identification. Mortality rates are model-smoothed.
Inputs: handoff/input_paths.json (panel, zillow, dose). Outputs: panel_models.csv, panel_analysis_data.csv
"""
import json, itertools, numpy as np, pandas as pd
from scipy import stats
SEED = 20261113
P = json.load(open('handoff/input_paths.json'))
pan = pd.read_parquet(P['panel']); z = pd.read_parquet(P['zillow'])
zl = z[['county_fips','year','zhvi_mean']].copy()
for L in (0,1,2):
    t_ = zl.copy(); t_['year'] = t_['year'] + L; t_ = t_.rename(columns={'zhvi_mean': f'zhvi_l{L}'})
    pan = pan.merge(t_, on=['county_fips','year'], how='left')
assert np.allclose(pan['zhvi_l0'], pan['zhvi_mean'])   # panel and Zillow annual file agree
d = pan[(pan.year.between(2010,2019)) & pan.pums_available.astype(bool)].copy().sort_values(['county_fips','year']).reset_index(drop=True)
assert d.county_fips.nunique()==14 and len(d)==140
for L in (0,1,2): d[f'lzhvi_l{L}'] = np.log(d[f'zhvi_l{L}'])
d['mean16'] = d['pums_mean_commute_min_16plus']; d['s60_16'] = d['pums_share_commute_60plus_16plus']
d['mean3564'] = d['pums_mean_commute_min_35_64']; d['s60_3564'] = d['pums_share_commute_60plus_35_64']
SECOL = {'mean16': 'pums_mean_commute_min_se_16plus', 's60_16': 'pums_share_commute_60plus_se_16plus', 'mean3564': 'pums_mean_commute_min_se_35_64', 's60_3564': 'pums_share_commute_60plus_se_35_64'}
for c in ['cvd','chd','stroke']:
    for b in ['35_64','65plus']: d[f'lmort_{c}_{b}'] = np.log(d[f'mort_{c}_{b}'])
keep = ['county_fips','county_name','core9','year','zhvi_l0','zhvi_l1','zhvi_l2','lzhvi_l0','lzhvi_l1','lzhvi_l2','mean16','s60_16','mean3564','s60_3564',
        'pums_mean_commute_min_se_16plus','pums_share_commute_60plus_se_16plus'] + [c for c in d.columns if c.startswith('mort_c') or c.startswith('mort_stroke') or c.startswith('lmort_')]
d[[k for k in keep if k in d.columns]].to_csv('panel_analysis_data.csv', index=False)
G = 14; cl = d.county_fips.astype('category').cat.codes.to_numpy(); yr = d.year.astype('category').cat.codes.to_numpy()
Dc = np.eye(G)[cl]; Dy = np.eye(10)[yr][:, 1:]
FE = np.hstack([Dc, Dy])                      # county dummies + 9 year dummies (no constant)
SIGNS = np.array(list(itertools.product([-1.0, 1.0], repeat=G))).T   # G x 16384, full enumeration
TCRIT = stats.t.ppf(0.975, G-1); MDE_MULT = TCRIT + stats.t.ppf(0.80, G-1)

def twfe(y, X, cl=cl, FE=FE, G=G):
    """LSDV two-way FE. Returns coef (slopes), CR1 SE (Stata xtreg convention: absorbed county effects not counted in K), residuals."""
    Z = np.hstack([X, FE]); b = np.linalg.lstsq(Z, y, rcond=None)[0]; u = y - Z @ b
    N = len(y); k = X.shape[1] + 9
    ZtZi = np.linalg.pinv(Z.T @ Z); meat = np.zeros((Z.shape[1],)*2)
    for g in range(G):
        s = Z[cl==g].T @ u[cl==g]; meat += np.outer(s, s)
    V = ZtZi @ meat @ ZtZi * (G/(G-1)) * ((N-1)/(N-k))
    return b[:X.shape[1]], np.sqrt(np.diag(V))[:X.shape[1]], u

def wcr(y, X, j, beta0=0.0):
    """Wild cluster restricted bootstrap-t p-value for H0: beta_j = beta0, all 2^14 Rademacher sign vectors."""
    others = np.hstack([np.delete(X, j, axis=1), FE]); xj = X[:, j]
    M = np.eye(len(y)) - others @ np.linalg.pinv(others)
    xt = M @ xj; sxx = xt @ xt
    yr_ = y - beta0*xj; ur = M @ yr_; fit = yr_ - ur            # restricted fit and residuals
    bhat = xt @ y / sxx; Zf = np.hstack([X, FE]); Mf = np.eye(len(y)) - Zf @ np.linalg.pinv(Zf)
    def tstat(Y):                                               # Y: N x B
        bb = xt @ Y / sxx; U = Mf @ Y
        S = np.vstack([(xt[cl==g, None] * U[cl==g]).sum(0) for g in range(G)])
        return (bb - beta0) / np.sqrt((S**2).sum(0)) * sxx      # scalar corrections cancel in the comparison
    t0 = tstat(y[:, None])[0]
    Ystar = (fit + beta0*xj)[:, None] + ur[:, None] * SIGNS[cl]
    ts = tstat(Ystar)
    return float(np.mean(np.abs(ts) >= abs(t0) - 1e-10)), bhat

def wcr_ci(y, X, j, bhat, se, level=0.05):
    f = lambda b0: wcr(y, X, j, b0)[0] - level
    out = []
    for sgn in (-1, 1):
        lo, hi = bhat, bhat + sgn*1.0*se
        k = 0
        while f(hi) > 0 and k < 12: hi = bhat + sgn*(2.0**(k+1))*se; k += 1
        if f(hi) > 0: out.append(np.nan); continue
        for _ in range(40):
            mid = 0.5*(lo+hi)
            if f(mid) > 0: lo = mid
            else: hi = mid
        out.append(0.5*(lo+hi))
    return out

def within_sd(x):
    r = x - FE @ np.linalg.lstsq(FE, x, rcond=None)[0]; return float(r.std(ddof=0))
def noise_share(name):
    """Approximate share of the within (two-way demeaned) variance of a PUMS commute measure that is sampling variance:
    mean(SE^2) x (1-1/T)(1-1/G) / within variance. 1 - this = approximate reliability of the measure in the fixed-effects model."""
    if name not in SECOL: return np.nan
    return float((d[SECOL[name]]**2).mean() * (1-1/10) * (1-1/G) / within_sd(d[name].to_numpy(float))**2)

rows = []
def run(block, model_id, yname, ylab, xname, xlab, xscale, xunit, controls=(), role='', note=''):
    y = d[yname].to_numpy(float); X = d[[xname, *controls]].to_numpy(float)
    b, se, u = twfe(y, X); p_w, _ = wcr(y, X, 0, 0.0); lo, hi = wcr_ci(y, X, 0, b[0], se[0])
    t = b[0]/se[0]
    rows.append(dict(block=block, model_id=model_id, role=role, outcome=yname, outcome_label=ylab, regressor=xname, regressor_label=xlab, unit_of_coefficient=xunit,
                     controls='; '.join(controls) if controls else 'none', fixed_effects='county + year', n_obs=len(y), n_clusters=G, years='2010-2019',
                     estimate=b[0]*xscale, se_cr1=se[0]*xscale, ci95_lo_cr1_t13=(b[0]-TCRIT*se[0])*xscale, ci95_hi_cr1_t13=(b[0]+TCRIT*se[0])*xscale,
                     p_cr1_t13=2*stats.t.sf(abs(t), G-1), p_wild_cluster=p_w, ci95_lo_wild=lo*xscale, ci95_hi_wild=hi*xscale,
                     ci_width_wild=(hi-lo)*xscale, mde_80pct_power=MDE_MULT*se[0]*abs(xscale),
                     within_sd_regressor=within_sd(d[xname].to_numpy(float)), within_sd_outcome=within_sd(y),
                     sampling_noise_share_of_within_var_regressor=noise_share(xname), sampling_noise_share_of_within_var_outcome=noise_share(yname),
                     inference='CR1 by county with t(13); wild cluster restricted bootstrap-t, Rademacher, 16,384 enumerated sign vectors; CI by test inversion',
                     note=note))
    return b, se
LN11 = np.log(1.10)
# ---- Model H: housing -> commute
for L, tag in [(1,'primary'), (0,'secondary'), (2,'secondary')]:
    for yv, yl in [('mean16','Mean one-way commute, commuters 16+ (minutes)'), ('s60_16','Share of commuters 16+ with 60+ min commute (proportion)'),
                   ('mean3564','Mean one-way commute, commuters 35-64 (minutes)'), ('s60_3564','Share of commuters 35-64 with 60+ min commute (proportion)')]:
        run('H: housing -> commute', f'H_{yv}_lag{L}', yv, yl, f'lzhvi_l{L}', f'log Zillow home value index, lag {L} y (nominal)', LN11,
            'change in outcome per 10% higher home value', role=tag + (' (a-path for 35-64 decomposition)' if '3564' in yv and L==1 else ''),
            note='year effects absorb common inflation; PUMS sampling error in the outcome adds noise only')
# ---- Model M: commute -> log mortality
for cause, cl_ in [('cvd','all cardiovascular disease'), ('chd','coronary heart disease'), ('stroke','stroke')]:
    for band, mx, sx in [('35_64','mean3564','s60_3564'), ('65plus','mean16','s60_16')]:
        ylab = f'log {cl_} mortality rate, ages {band.replace("_","-").replace("plus","+")} (model-smoothed)'
        tag = 'primary' if cause=='cvd' else 'secondary'
        run('M: commute -> mortality', f'M_{cause}_{band}_mean', f'lmort_{cause}_{band}', ylab, mx, f'mean commute minutes ({ "35-64" if band=="35_64" else "16+"} commuters)', 5.0,
            'log-rate change per 5 more minutes (x100 = approx % change)', role=tag, note='smoothed outcome; sampling error in the PUMS regressor attenuates towards zero')
        run('M: commute -> mortality', f'M_{cause}_{band}_s60', f'lmort_{cause}_{band}', ylab, sx, f'60+ min share ({ "35-64" if band=="35_64" else "16+"} commuters)', 0.10,
            'log-rate change per 10-point higher share (x100 = approx % change)', role=tag, note='smoothed outcome; sampling error in the PUMS regressor attenuates towards zero')
# ---- Pathway decomposition (product of coefficients), cvd mortality
rng = np.random.default_rng(SEED); B = 4999
def decomp(dd, cl_b, FE_b, Gb, yname, mname):
    y = dd[yname].to_numpy(float); m = dd[mname].to_numpy(float); h = dd['lzhvi_l1'].to_numpy(float)
    def coef(yv, X): return np.linalg.lstsq(np.hstack([X, FE_b]), yv, rcond=None)[0][:X.shape[1]]
    a = coef(m, h[:, None])[0]; bb = coef(y, np.column_stack([m, h])); c = coef(y, h[:, None])[0]
    return np.array([a, bb[0], a*bb[0], bb[1], c])
counties = sorted(d.county_fips.unique()); idx_by = {c: np.where(d.county_fips.to_numpy()==c)[0] for c in counties}
draws_idx = rng.integers(0, G, size=(B, G))
for band, mx, sx in [('35_64','mean3564','s60_3564'), ('65plus','mean16','s60_16')]:
    for mname, mlab, mscale in [(mx,'mean commute minutes',1.0), (sx,'60+ min share',1.0)]:
        yname = f'lmort_cvd_{band}'
        pt = decomp(d, cl, FE, G, yname, mname)
        bs = np.empty((B,5))
        for r in range(B):
            ii = np.concatenate([idx_by[counties[k]] for k in draws_idx[r]])
            dd = d.iloc[ii]; clb = np.repeat(np.arange(G), 10); FEb = np.hstack([np.eye(G)[clb], np.eye(10)[dd.year.astype('category').cat.codes.to_numpy()][:,1:]])
            bs[r] = decomp(dd, clb, FEb, G, yname, mname)
        # scale: a per 10% higher home value; b per unit mediator; indirect/direct/total per 10% higher home value on log mortality
        sc = np.array([LN11, 1.0, LN11, LN11, LN11])
        labs = [('a: log home value (lag 1) -> commute', f'change in {mlab} per 10% higher home value'),
                ('b: commute -> log mortality | home value', f'log-rate change per unit of {mlab} (1 minute, or share 0->1)'),
                ('indirect a x b', 'log-rate change per 10% higher home value via commute'),
                ('direct: home value -> log mortality | commute', 'log-rate change per 10% higher home value'),
                ('total: home value -> log mortality', 'log-rate change per 10% higher home value')]
        for k,(lab,unit) in enumerate(labs):
            lo, hi = np.percentile(bs[:,k]*sc[k], [2.5, 97.5])
            rows.append(dict(block='D: pathway decomposition (descriptive, not causal)', model_id=f'D_cvd_{band}_{mname}', role=lab, outcome=yname,
                             outcome_label=f'log all-CVD mortality, ages {band}', regressor=mname, regressor_label=mlab, unit_of_coefficient=unit,
                             controls='see role', fixed_effects='county + year', n_obs=140, n_clusters=G, years='2010-2019',
                             estimate=pt[k]*sc[k], se_cr1=np.nan, ci95_lo_cr1_t13=np.nan, ci95_hi_cr1_t13=np.nan, p_cr1_t13=np.nan, p_wild_cluster=np.nan,
                             ci95_lo_wild=np.nan, ci95_hi_wild=np.nan, ci_width_wild=np.nan, mde_80pct_power=np.nan,
                             within_sd_regressor=np.nan, within_sd_outcome=np.nan,
                             sampling_noise_share_of_within_var_regressor=np.nan, sampling_noise_share_of_within_var_outcome=np.nan,
                             inference=f'county-cluster pairs bootstrap, {B} draws, percentile, seed {SEED}; unreliable with 14 clusters',
                             note='product of coefficients; not causal mediation', boot_ci95_lo=lo, boot_ci95_hi=hi, boot_se=float((bs[:,k]*sc[k]).std(ddof=1))))
res = pd.DataFrame(rows)
# ---- literature benchmark for the MDE: Warren 2010 (row DR003), the only driving-specific CVD-mortality estimate
dose = pd.read_csv(P['dose']); w = dose[dose.row_id=='DR003'].iloc[0]
res.attrs = {}
bench = dict(row_id='DR003', hr=float(w['estimate']), hr_lo=float(w['ci_lower']), hr_hi=float(w['ci_upper']), abstract_only=bool(w['abstract_only']))
# Illustrative expectation: a 10-point higher 60+ share among commuters, if every such commuter carried HR = DR003 and commuters are a fraction f of the age band,
# raises the band's log mortality by about f * 0.10 * (HR - 1). f for 35-64 from the PUMS aggregate (ALL14, 2019).
pc = pd.read_parquet(P['pcya']); f3564 = float(pc[(pc.county_fips=='ALL14')&(pc.year==2019)&(pc.age_band=='35_64')]['pop_share_commuter'].iloc[0])
bench['pop_share_commuter_35_64_2019'] = f3564
bench['implied_lograte_change_per_10pt_60plus_share_35_64'] = float(np.log(1 + f3564*0.10*(bench['hr']-1)))
json.dump(bench, open('panel_mde_benchmark.json','w'), indent=1)
res['literature_benchmark'] = ''
m_ = res.model_id=='M_cvd_35_64_s60'
res.loc[m_, 'literature_benchmark'] = (f"illustrative: if every 60+ min commuter carried HR {bench['hr']} (DR003, Warren 2010, >10 vs <4 h/wk in a car, men) and commuters are "
                                      f"{f3564:.3f} of persons 35-64, a 10-point higher share implies log-rate change {bench['implied_lograte_change_per_10pt_60plus_share_35_64']:.4f}")
res.to_csv('panel_models.csv', index=False)
print(res.shape)
