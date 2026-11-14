"""nat_common.py -- shared helpers for the national county models.
Input paths are read from handoff/national_input_paths.json (keys: county, annual, dose).
Specifications follow national_prespecified_plan.md.
"""
import json, numpy as np, pandas as pd
from scipy import stats

SEED = 20261113
PATHS = json.load(open('handoff/national_input_paths.json'))
T_DF = 50                                   # 51 state clusters - 1
MDE_MULT = stats.t.ppf(0.975, T_DF) + stats.t.ppf(0.80, T_DF)

AGE = ['share_age_18_34', 'share_age_35_64', 'share_age_65plus', 'share_female']
SES = ['log_income', 'poverty_rate', 'share_bachelors_plus', 'share_less_than_hs', 'unemployment_rate',
       'share_nh_black', 'share_hispanic', 'share_nh_asian', 'share_nh_aian', 'share_uninsured_18_64']
PLACES = ['places_r2020_csmoking_aa', 'places_r2020_obesity_aa', 'places_r2020_diabetes_aa', 'places_r2020_lpa_aa']
CAR, TRANSIT = 'car_hours_wk_per_adult16', 'transit_hours_wk_per_adult16'
BAY9 = ['06001', '06013', '06041', '06055', '06075', '06081', '06085', '06095', '06097']
BAY6 = ['06047', '06067', '06069', '06077', '06087', '06099']
NYC5 = ['36005', '36047', '36061', '36081', '36085']


def load_county():
    d = pd.read_parquet(PATHS['county'])
    d['fips'] = d['fips'].astype(str).str.zfill(5)
    d['log_income'] = np.log(d['median_hh_income'])
    d['log_density'] = np.log(d['pop_density'])
    return d


def cross_section(d, vintage=2019):
    x = d[(d.acs_vintage == vintage) & d.complete_case_main].copy().reset_index(drop=True)
    return x


def pct(b):
    return 100.0 * (np.exp(b) - 1.0)


def rung_terms(rung):
    """Covariate names (before fixed effects) for a ladder rung."""
    t = []
    if rung >= 1: t += AGE
    if rung >= 2: t += SES
    if rung >= 3: t += ['log_density']
    if rung >= 4: t += PLACES
    return t


def design(df, exposures, rung, extra=(), ur_col='nchs_ur_2013', fe=None, covs=None):
    """Design matrix: constant, exposures, rung covariates, extras; from rung 3: urban-rural and state indicators."""
    terms = list(exposures) + (rung_terms(rung) if covs is None else list(covs)) + list(extra)
    X = df[terms].astype(float).copy()
    X.insert(0, 'const', 1.0)
    if fe is None:
        fe = rung >= 3
    if fe:
        ur = pd.get_dummies(df[ur_col].astype(int), prefix='ur', drop_first=True).astype(float)
        st = pd.get_dummies(df['state_abbr'], prefix='st', drop_first=True).astype(float)
        X = pd.concat([X, ur, st], axis=1)
    # drop columns that are all zero in this sample (e.g. a class absent from a subsample)
    X = X.loc[:, (X.abs().sum(axis=0) > 0)]
    return X


def haversine_matrix(lat, lon):
    lat = np.radians(np.asarray(lat, float)); lon = np.radians(np.asarray(lon, float))
    dlat = lat[:, None] - lat[None, :]; dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlon / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


class Fit:
    """Weighted least squares with cluster-robust (CR1) and Conley covariance."""

    def __init__(self, y, X, w=None, cluster=None, dist=None):
        self.names = list(X.columns)
        Xv = np.asarray(X, float); yv = np.asarray(y, float)
        n, k = Xv.shape
        wv = np.ones(n) if w is None else np.asarray(w, float)
        self.n, self.w = n, wv
        XtWX = Xv.T @ (Xv * wv[:, None])
        self.rank = int(np.linalg.matrix_rank(XtWX))
        self.k = self.rank
        self.bread = np.linalg.pinv(XtWX)
        self.b = self.bread @ (Xv.T @ (wv * yv))
        self.resid = yv - Xv @ self.b
        self.scores = Xv * (wv * self.resid)[:, None]
        ybar = np.average(yv, weights=wv)
        self.r2 = 1 - (wv * self.resid ** 2).sum() / (wv * (yv - ybar) ** 2).sum()
        self.cluster = None if cluster is None else np.asarray(cluster)
        self.dist = dist
        self.V_cl = None
        if cluster is not None:
            self.Sg = pd.DataFrame(self.scores).groupby(self.cluster).sum()
            G = self.Sg.shape[0]; self.G = G
            self.c = G / (G - 1) * (n - 1) / (n - self.k)
            S = self.Sg.values
            self.V_cl = self.c * self.bread @ (S.T @ S) @ self.bread

    def conley(self, cutoff_km):
        K = np.clip(1 - self.dist / cutoff_km, 0, None)
        meat = self.scores.T @ K @ self.scores
        return self.n / (self.n - self.k) * self.bread @ meat @ self.bread

    def i(self, name):
        return self.names.index(name)

    def coef(self, name, V=None, df=None):
        V = self.V_cl if V is None else V
        j = self.i(name); b = self.b[j]; se = float(np.sqrt(V[j, j]))
        if df is None:
            crit = stats.norm.ppf(0.975); p = 2 * stats.norm.sf(abs(b / se))
        else:
            crit = stats.t.ppf(0.975, df); p = 2 * stats.t.sf(abs(b / se), df)
        return dict(b=b, se=se, lo=b - crit * se, hi=b + crit * se, p=p)

    def diff(self, n1, n2, V=None, df=None):
        V = self.V_cl if V is None else V
        i, j = self.i(n1), self.i(n2)
        d = self.b[i] - self.b[j]; se = float(np.sqrt(V[i, i] + V[j, j] - 2 * V[i, j]))
        if df is None:
            crit = stats.norm.ppf(0.975); p = 2 * stats.norm.sf(abs(d / se))
        else:
            crit = stats.t.ppf(0.975, df); p = 2 * stats.t.sf(abs(d / se), df)
        return dict(d=d, se=se, lo=d - crit * se, hi=d + crit * se, p=p)


def cross_cov(f1, f2):
    """State-clustered covariance between coefficient vectors of two fits on the same units and clusters."""
    S1 = f1.Sg.values; S2 = f2.Sg.reindex(f1.Sg.index).values
    c = np.sqrt(f1.c * f2.c)
    return c * f1.bread @ (S1.T @ S2) @ f2.bread


def bh(p):
    """Benjamini-Hochberg q-values."""
    p = np.asarray(p, float); n = len(p); o = np.argsort(p)
    q = np.empty(n); prev = 1.0
    for rank, idx in zip(range(n, 0, -1), o[::-1]):
        prev = min(prev, p[idx] * n / rank); q[idx] = prev
    return q


def holm(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p)
    adj = np.empty(n); prev = 0.0
    for rank, idx in enumerate(o):
        prev = max(prev, min(1.0, (n - rank) * p[idx])); adj[idx] = prev
    return adj


def morans_i_knn(resid, lat, lon, k=8, nperm=999, seed=SEED, dist=None):
    D = haversine_matrix(lat, lon) if dist is None else dist
    n = len(resid)
    idx = np.argsort(D, axis=1)[:, 1:k + 1]
    z = np.asarray(resid, float) - np.mean(resid)
    def stat(zz):
        return (zz * zz[idx].mean(axis=1)).sum() / (zz ** 2).sum()
    I = stat(z)
    rng = np.random.default_rng(seed)
    sims = np.array([stat(rng.permutation(z)) for _ in range(nperm)])
    p = (1 + (sims >= I).sum()) / (nperm + 1)
    return dict(I=I, p_perm=p, z=(I - sims.mean()) / sims.std(ddof=1), k=k, nperm=nperm)


def benchmarks():
    """Literature conversions fixed in the plan (percent difference per additional commute hour a week)."""
    dr = pd.read_csv(PATHS['dose']).set_index('row_id')
    rows = []
    s = dr.loc['DR027', ['estimate', 'ci_lower', 'ci_upper']].astype(float).values
    for f in (0.5, 1.0):
        v = [pct(np.log(x) * f / 7) for x in s]
        rows.append(dict(benchmark=f'sitting_DR027_f{f}', source='DR027', pct=v[0], pct_lo=v[1], pct_hi=v[2],
                         conversion=f'100*(RR^({f}/7)-1)'))
    for tm in (12.0, 15.0):
        ref = 2.0; xs, ys, ses = [], [], []
        for rid, m in (('DR001', 5.5), ('DR002', 8.5), ('DR003', tm)):
            e, lo, hi = dr.loc[rid, ['estimate', 'ci_lower', 'ci_upper']].astype(float)
            xs.append(m - ref); ys.append(np.log(e)); ses.append((np.log(hi) - np.log(lo)) / (2 * stats.norm.ppf(0.975)))
        x, y, se = map(np.array, (xs, ys, ses)); w = 1 / se ** 2
        sl = (w * x * y).sum() / (w * x * x).sum(); sse = np.sqrt(1 / (w * x * x).sum())
        rows.append(dict(benchmark=f'driving_DR001-003_wls_top{int(tm)}', source='DR001-DR003', pct=pct(sl),
                         pct_lo=pct(sl - 1.959964 * sse), pct_hi=pct(sl + 1.959964 * sse),
                         conversion=f'inverse-variance slope through reference; midpoints 2, 5.5, 8.5, {tm:g} h/week'))
        e, lo, hi = dr.loc['DR003', ['estimate', 'ci_lower', 'ci_upper']].astype(float)
        rows.append(dict(benchmark=f'driving_DR003_top{int(tm)}', source='DR003', pct=pct(np.log(e) / (tm - ref)),
                         pct_lo=pct(np.log(lo) / (tm - ref)), pct_hi=pct(np.log(hi) / (tm - ref)),
                         conversion=f'ln(HR)/({tm:g}-2) h/week'))
    return pd.DataFrame(rows)
