"""tract_common.py -- shared functions for the tract-level models (steps 2 and 4).
Requires geopandas, libpysal, spreg, esda, statsmodels. Seed 20261113.
"""
import json, warnings, numpy as np, pandas as pd, geopandas as gpd, libpysal, spreg, esda
import statsmodels.api as sm
from scipy import stats
from scipy.sparse.csgraph import connected_components
SEED = 20261113
P = json.load(open('handoff/input_paths.json'))
OUTCOMES = {'chd_prev': 'Coronary heart disease', 'stroke_prev': 'Stroke', 'bphigh_prev': 'High blood pressure',
            'obesity_prev': 'Obesity', 'lpa_prev': 'No leisure-time physical activity', 'diabetes_prev': 'Diagnosed diabetes'}
EXPOSURES = ['share_commute_60plus', 'share_drive_alone']
COVARS = ['share_age_18_34', 'share_age_35_64', 'share_age_65plus', 'log_median_hh_income', 'income_topcoded', 'poverty_rate', 'share_bachelors_plus',
          'share_nh_black', 'share_nh_asian', 'share_hispanic', 'share_no_vehicle_hh']
SCALE = {'share_commute_60plus': 0.10, 'share_drive_alone': 0.10, 'share_commute_45plus': 0.10, 'share_commute_90plus': 0.10, 'mean_commute_min': 5.0}
UNIT = {k: ('per 5 minutes' if k == 'mean_commute_min' else 'per 10 percentage points') for k in SCALE}
XS = {2019: dict(label='ACS 2015-2019 / PLACES 2021 release (BRFSS 2019)', tiger=2019, tract_vintage=2010),
      2024: dict(label='ACS 2020-2024 / PLACES 2025 release (BRFSS 2023)', tiger=2024, tract_vintage=2020)}
_geo_cache = {}

def load_tracts():
    t = pd.read_parquet(P['tract'])
    t['log_median_hh_income'] = np.log(t['median_hh_income'])
    t['income_topcoded'] = t['median_hh_income_topcoded'].fillna(False).astype(float)
    t['adult_pop'] = t['pop_total'] * (1 - t['share_age_under18'])
    return t

def base_sample(t, vintage, extra_required=()):
    s = t[t.acs_vintage == vintage].copy()
    need = list(OUTCOMES) + EXPOSURES + COVARS + list(extra_required)
    ok = s['has_places'].astype(bool) & (s['commuters_total'] >= 100) & s[need].notna().all(axis=1)
    return s[ok].sort_values('tract_geoid').reset_index(drop=True)

def geometries(tiger_year):
    if tiger_year not in _geo_cache:
        g = gpd.read_file(f'tiger/tl_{tiger_year}_06_tract.zip')[['GEOID', 'COUNTYFP', 'ALAND', 'AWATER', 'geometry']]
        _geo_cache[tiger_year] = g.to_crs(3310)      # California Albers (metres)
    return _geo_cache[tiger_year]

def build_w(geoids, tiger_year):
    """Queen contiguity on the given tracts (order preserved), nearest-neighbour fix for islands, row-standardised."""
    g = geometries(tiger_year).set_index('GEOID')
    missing = [x for x in geoids if x not in g.index]
    if missing: raise ValueError(f'{len(missing)} tracts not in TIGER {tiger_year}: {missing[:5]}')
    gs = g.loc[list(geoids)].reset_index()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        w = libpysal.weights.Queen.from_dataframe(gs, use_index=False, silence_warnings=True)
    nb = {i: list(w.neighbors[i]) for i in range(len(gs))}
    islands = [i for i, v in nb.items() if len(v) == 0]
    if islands:
        cen = np.column_stack([gs.geometry.centroid.x, gs.geometry.centroid.y])
        for i in islands:
            dist = np.hypot(*(cen - cen[i]).T); dist[i] = np.inf; j = int(np.argmin(dist))
            if j not in nb[i]: nb[i].append(j)
            if i not in nb[j]: nb[j].append(i)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        w2 = libpysal.weights.W(nb, silence_warnings=True)
    A = w2.sparse.copy()
    ncomp = connected_components(A, directed=False)[0]
    deg = np.asarray(A.sum(1)).ravel()
    Dm = 1/np.sqrt(deg); S = (A.multiply(Dm[:, None]).multiply(Dm[None, :])).toarray()
    eig = np.linalg.eigvalsh(S)                      # eigenvalues of the row-standardised W (similar matrix)
    w2.transform = 'r'
    info = dict(n=len(gs), n_islands_attached=len(islands), mean_neighbours=float(deg.mean()), min_neighbours=int(deg.min()), max_neighbours=int(deg.max()), n_components=int(ncomp))
    return w2, eig, info

def design(s, exposures, covars, county_fe=True):
    X = s[list(exposures) + list(covars)].astype(float).copy()
    if county_fe:
        dm = pd.get_dummies(s['county_fips'], prefix='cty', drop_first=True).astype(float)
        X = pd.concat([X, dm], axis=1)
    X = X.loc[:, X.std(ddof=0) > 0]                   # drops e.g. a top-code dummy that is constant in a subsample
    return X

def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); q = np.empty(n)
    q[o] = np.minimum.accumulate((p[o] * n / np.arange(1, n+1))[::-1])[::-1]
    return np.minimum(q, 1.0)

def fit_all(s, w, eig, outcome, exposures, covars, estimators=('ols', 'error', 'lag'), county_fe=True, weights=None, perm=999, method='full'):
    """Fit the requested estimators for one outcome. Returns (rows: list of dict per exposure x estimator, diag: dict)."""
    X = design(s, exposures, covars, county_fe); names = list(X.columns)
    y = s[outcome].to_numpy(float); Xa = X.to_numpy(float); n, k = Xa.shape
    rows, diag = [], dict(outcome=outcome, n_tracts=n, n_regressors_incl_const=k+1, n_counties=int(s.county_fips.nunique()))
    def add(est, e, coef, se, pval, extra):
        sc = SCALE[e]
        r = dict(outcome=outcome, exposure=e, estimator=est, exposure_unit=UNIT[e], estimate=coef*sc, se=se*sc, ci95_lo=(coef-1.96*se)*sc, ci95_hi=(coef+1.96*se)*sc,
                 z=coef/se, p_value=pval, n_tracts=n)
        r.update(extra); rows.append(r)
    Xc = sm.add_constant(Xa, has_constant='add')
    if 'ols' in estimators or 'wls' in estimators:
        if weights is None:
            m = sm.OLS(y, Xc).fit(cov_type='HC1'); est = 'OLS (HC1)'
        else:
            m = sm.WLS(y, Xc, weights=weights).fit(cov_type='HC1'); est = 'WLS adult-population weights (HC1)'
        diag.update(ols_r2=m.rsquared, ols_adj_r2=m.rsquared_adj, ols_aic=float(-2*m.llf + 2*(k+1)), ols_loglik=float(m.llf))
        for e in exposures:
            j = names.index(e) + 1
            add(est, e, m.params[j], m.bse[j], m.pvalues[j], dict(aic=diag['ols_aic'], loglik=float(m.llf)))
        if weights is None and w is not None:
            # covariates-only R2 (how much of the modelled outcome the demographics reproduce) and partial R2 of the exposures
            Xn = sm.add_constant(X.drop(columns=list(exposures)).to_numpy(float), has_constant='add'); m0 = sm.OLS(y, Xn).fit()
            diag.update(r2_covariates_only=m0.rsquared, partial_r2_exposures=float((m0.ssr - m.ssr)/m0.ssr))
            o = spreg.OLS(y[:, None], Xa, w=w, spat_diag=True, moran=True, name_x=names)
            assert np.allclose(o.betas.ravel(), m.params, rtol=1e-6, atol=1e-8)
            diag.update(moran_I_ols_resid=o.moran_res[0], moran_z=o.moran_res[1], moran_p_normal=o.moran_res[2],
                        lm_error=o.lm_error[0], lm_error_p=o.lm_error[1], lm_lag=o.lm_lag[0], lm_lag_p=o.lm_lag[1],
                        rlm_error=o.rlm_error[0], rlm_error_p=o.rlm_error[1], rlm_lag=o.rlm_lag[0], rlm_lag_p=o.rlm_lag[1])
            if perm:
                np.random.seed(SEED); mi = esda.Moran(o.u.ravel(), w, permutations=perm)
                diag.update(moran_I_esda=mi.I, moran_p_perm=mi.p_sim, moran_permutations=perm)
    if 'error' in estimators:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            me = spreg.ML_Error(y[:, None], Xa, w=w, method=method, name_x=names)
        b = me.betas.ravel(); se = np.asarray(me.std_err).ravel(); lam, lam_se = b[-1], se[-1]
        diag.update(error_lambda=lam, error_lambda_se=lam_se, error_aic=me.aic, error_loglik=me.logll)
        try:
            np.random.seed(SEED); mi = esda.Moran(me.e_filtered.ravel(), w, permutations=0); diag.update(moran_I_error_filtered_resid=mi.I, moran_p_error_filtered_resid=mi.p_norm)
        except Exception as ex: diag.update(moran_I_error_filtered_resid=np.nan)
        for e in exposures:
            j = names.index(e) + 1
            add('Spatial error (ML)', e, b[j], se[j], 2*stats.norm.sf(abs(b[j]/se[j])), dict(spatial_param=lam, spatial_param_se=lam_se, aic=me.aic, loglik=me.logll))
    if 'lag' in estimators:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            ml = spreg.ML_Lag(y[:, None], Xa, w=w, method=method, name_x=names, spat_diag=False, spat_impacts=None)
        b = ml.betas.ravel(); V = np.asarray(ml.vm); se = np.sqrt(np.diag(V)); rho, rho_se = b[-1], se[-1]
        diag.update(lag_rho=rho, lag_rho_se=rho_se, lag_aic=ml.aic, lag_loglik=ml.logll)
        try:
            mi = esda.Moran(ml.u.ravel(), w, permutations=0); diag.update(moran_I_lag_resid=mi.I, moran_p_lag_resid=mi.p_norm)
        except Exception as ex: diag.update(moran_I_lag_resid=np.nan)
        rng = np.random.default_rng(SEED)
        for e in exposures:
            j = names.index(e) + 1; sc = SCALE[e]
            idx = [j, len(b)-1]; dr = rng.multivariate_normal(b[idx], V[np.ix_(idx, idx)], size=2000)
            rr = np.clip(dr[:, 1], -0.999, 0.999)
            tot = dr[:, 0]/(1-rr); dirm = np.array([np.mean(1/(1-r_*eig)) for r_ in rr]) * dr[:, 0]
            tot0 = b[j]/(1-rho); dir0 = b[j]*np.mean(1/(1-rho*eig))
            lo, hi = np.percentile(tot, [2.5, 97.5]); dlo, dhi = np.percentile(dirm, [2.5, 97.5])
            rows.append(dict(outcome=outcome, exposure=e, estimator='Spatial lag (ML), average total impact', exposure_unit=UNIT[e], estimate=tot0*sc, se=float(tot.std(ddof=1))*sc,
                             ci95_lo=lo*sc, ci95_hi=hi*sc, z=b[j]/se[j], p_value=2*stats.norm.sf(abs(b[j]/se[j])), n_tracts=n, spatial_param=rho, spatial_param_se=rho_se,
                             aic=ml.aic, loglik=ml.logll, lag_raw_beta=b[j]*sc, lag_raw_beta_se=se[j]*sc, lag_direct_impact=dir0*sc, lag_direct_ci95_lo=dlo*sc, lag_direct_ci95_hi=dhi*sc))
    if 'lm_error_p' in diag:
        pe, pl = diag['lm_error_p'], diag['lm_lag_p']
        if pe >= 0.05 and pl >= 0.05: fav = 'OLS (HC1)'
        elif pe < 0.05 and pl >= 0.05: fav = 'Spatial error (ML)'
        elif pl < 0.05 and pe >= 0.05: fav = 'Spatial lag (ML), average total impact'
        else: fav = 'Spatial error (ML)' if diag['rlm_error'] >= diag['rlm_lag'] else 'Spatial lag (ML), average total impact'
        diag['favoured_by_lm_rule'] = fav
        if 'error_aic' in diag and 'lag_aic' in diag:
            aics = {'OLS (HC1)': diag['ols_aic'], 'Spatial error (ML)': diag['error_aic'], 'Spatial lag (ML), average total impact': diag['lag_aic']}
            diag['lowest_aic'] = min(aics, key=aics.get)
    diag.update(outcome_mean=float(y.mean()), outcome_sd=float(y.std(ddof=1)))
    for e in exposures: diag[f'sd_{e}'] = float(s[e].std(ddof=1)); diag[f'mean_{e}'] = float(s[e].mean())
    return rows, diag
