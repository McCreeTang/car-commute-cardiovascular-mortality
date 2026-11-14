
"""Comparative risk assessment engine: commute car time -> cardiovascular mortality.
One code path serves point estimates (K=1, central values, no perturbation), Monte Carlo and validity checks."""
import math, re
import numpy as np, pandas as pd
from scipy import sparse
from scipy.stats import norm
from burden_lib import *

FINE35 = ['35_44', '45_54', '55_64', '65plus']
MBANDS = ['35_64', '65plus']
MORT_AGE = {'35_64': '35-64', '65plus': '65+'}
LINEAR = ['A', 'B', 'C', 'D']
F_MODES = ['U(0,1)', '0.25', '0.5', '0.75', '1.0']
CFS = ['cf1_2010_distribution', 'cf1b_2010_duration_only', 'cf2_cap30', 'cf3_no_car']
NTERMS = 24


# ------------------------------------------------------------------ parameters (read from the CSV by row id)
def read_parameters():
    dr = pd.read_csv(PATHS['dr']).set_index('row_id')
    def row(rid, level=None):
        r = dr.loc[rid]
        lev = float(str(r.ci_level).strip('%')) / 100 if level is None else level
        return dict(row_id=rid, est=float(r.estimate), lo=float(r.ci_lower), hi=float(r.ci_upper), level=lev,
                    abstract_only=bool(r.abstract_only), source='%s %s' % (r.first_author, r.year), field='estimate/ci columns')
    def from_notes(rid, pattern):
        r = dr.loc[rid]; mm = re.search(pattern, str(r.notes))
        if mm is None: raise ValueError('pattern not found in notes of ' + rid)
        return dict(row_id=rid, est=float(mm.group(1)), lo=float(mm.group(2)), hi=float(mm.group(3)), level=0.95,
                    abstract_only=bool(r.abstract_only), source='%s %s' % (r.first_author, r.year), field='notes field: "%s"' % mm.group(0))
    num = r'(\d+\.\d+)\s*\((\d+\.\d+)\s*-\s*(\d+\.\d+)\)'
    P = {'A': row('DR027'),
         'B': from_notes('DR028', r'Below 6 h/day:\s*' + num),
         'C': row('DR028'),
         'D': from_notes('DR033', r'Per hour sedentary RR\s*' + num),
         'E1': row('DR001'), 'E2': row('DR002'), 'E3': row('DR003'),
         'anger_mi': row('DR047'), 'anger_stroke': row('DR050')}
    for k, p in P.items():
        p['se_log'] = float(lognormal_se(p['lo'], p['hi'], p['level']))
        p['se_log_max_halfwidth'] = float(max(math.log(p['est'] / p['lo']), math.log(p['hi'] / p['est'])) / norm.ppf(0.5 + p['level'] / 2))
    return P


ASSUMED = dict(days_lo=4.0, days_hi=5.0, f_lo=0.0, f_hi=1.0, cap_min=30.0, warren_rho=0.5, warren_noncommute_h=0.0,
               warren_gt10_strict=True, anger_lambda_lo=0.002, anger_lambda_hi=0.1, window_mi_h=2.0, window_stroke_h=1.0,
               days_in_week_for_daily_average=7.0)


# ------------------------------------------------------------------ data structures
class Cells:
    """Weighted sums by county x age band (35-44,45-54,55-64,65+) x sex, for each year and each of the 81 weights."""
    def __init__(self, df, modeset='car', topcode='as_published', cap_min=30.0, exposure_scale=1.0, years=YEARS):
        jw_all = hours_per_commute_day(df, modeset, topcode) * 30.0 * exposure_scale     # one-way minutes, 0 if unexposed
        keep = (df.agep >= 35).to_numpy()
        self.counties = sorted(df.county_fips.unique())
        cmeta = df[['county_fips', 'county_name', 'core9']].drop_duplicates().set_index('county_fips')
        meta = [(c, b, s) for c in self.counties for b in FINE35 for s in (1, 2)]
        self.meta = pd.DataFrame(meta, columns=['county', 'band', 'sex'])
        self.meta['core9'] = self.meta.county.map(cmeta.core9).astype(bool)
        self.meta['county_name'] = self.meta.county.map(cmeta.county_name)
        self.ncell = len(self.meta)
        key = {k: i for i, k in enumerate(meta)}
        self.cap_h = 2.0 * cap_min / 60.0
        self.cap_min = cap_min
        self.Y = {}
        for y in years:
            m = keep & (df.year == y).to_numpy()
            sub = df.loc[m, ['county_fips', 'band', 'sex']]
            cid = np.array([key[k] for k in zip(sub.county_fips, sub.band, sub.sex)])
            W = df.loc[m, WCOLS].to_numpy('float64'); jw = jw_all[m]
            n = len(cid)
            C = sparse.csr_matrix((np.ones(n), (cid, np.arange(n))), shape=(self.ncell, n))
            a = 2.0 * jw / 60.0; acap = np.minimum(a, self.cap_h); ex = a > 0
            Wtot = C @ W; Wcar = C @ (W * ex[:, None])
            mom = np.zeros((self.ncell, 81, NTERMS + 1)); momc = np.zeros_like(mom)
            p = np.ones(n); pc = np.ones(n)
            for k in range(1, NTERMS + 1):
                p = p * a; pc = pc * acap
                mom[:, :, k] = C @ (W * p[:, None]); momc[:, :, k] = C @ (W * pc[:, None])
            # sorted structures for categorical (threshold) exposure
            srt = []
            for c in range(self.ncell):
                i = np.where((cid == c) & ex)[0]; o = i[np.argsort(jw[i], kind='stable')]
                cum = np.vstack([np.zeros((1, 81)), np.cumsum(W[o], axis=0)])
                srt.append((jw[o], np.minimum(jw[o], cap_min), cum))
            self.Y[y] = dict(Wtot=Wtot, Wcar=Wcar, mom=mom, momc=momc, srt=srt, n=n, n_exposed=int(ex.sum()),
                             a=a, W=W, cid=cid)


def perturb(S, z):
    """S[..., 81] -> [..., K]: full-sample value plus a random combination of the 80 replicate deviations.
    With z ~ N(0, I_80) the result has mean S0 and variance equal to the ACS replicate variance (4/80 x sum of squares)."""
    S0 = S[..., 0]
    if z is None:
        return S0[..., None]
    dev = S[..., 1:] - S0[..., None]
    return S0[..., None] + math.sqrt(SDR) * (dev @ z.T)


def load_rates(topic='cvd', year=2019):
    mort = pd.read_parquet(PATHS['mort'])
    if topic == 'majorcvd':
        m = mort[(mort.series == 'major_cvd_age_2010_2020') & (mort.year == year) & (mort.value_type == 'Age-Standardized, Spatially Smoothed Rate')
                 & (mort.sex == 'Overall') & (mort.race == 'Overall')]
    else:
        m = mort[(mort.series == 'age_stratified_1999_2019') & (mort.year == year) & (mort.race == 'Overall') & (mort.topic == topic)
                 & mort.value_type.str.contains('Smoothed Rate')]
    m = m[['county_fips', 'age_group', 'sex', 'value', 'ci_low', 'ci_high']].copy()
    assert m.value.notna().all() and not m.duplicated(['county_fips', 'age_group', 'sex']).any()
    return m.set_index(['county_fips', 'age_group', 'sex'])


# ------------------------------------------------------------------ draws
def make_draws(K, seed, P, A=ASSUMED, central=False, se_rule='se_log', overrides=None):
    """All random inputs. central=True returns the single deterministic central configuration (K=1)."""
    rng = np.random.default_rng(seed)
    D = {}
    if central:
        K = 1
        for s in LINEAR: D['beta_' + s] = np.array([math.log(P[s]['est'])])
        D['lnhr'] = np.log(np.array([[P['E1']['est'], P['E2']['est'], P['E3']['est']]]))
        D['f'] = np.array([(A['f_lo'] + A['f_hi']) / 2]); D['d'] = np.array([(A['days_lo'] + A['days_hi']) / 2])
        D['z'] = {y: None for y in YEARS}
        D['rate_z'] = None
        D['ln_irr_mi'] = np.array([math.log(P['anger_mi']['est'])]); D['ln_or_stroke'] = np.array([math.log(P['anger_stroke']['est'])])
        D['lam'] = np.array([math.sqrt(A['anger_lambda_lo'] * A['anger_lambda_hi'])])
    else:
        for s in LINEAR: D['beta_' + s] = math.log(P[s]['est']) + P[s][se_rule] * rng.standard_normal(K)
        rho = A['warren_rho']                                 # equicorrelated normals via a common factor (valid for 0 <= rho <= 1)
        zz = math.sqrt(rho) * rng.standard_normal((K, 1)) + math.sqrt(1 - rho) * rng.standard_normal((K, 3))
        D['lnhr'] = np.log([P['E1']['est'], P['E2']['est'], P['E3']['est']]) + zz * np.array([P['E1'][se_rule], P['E2'][se_rule], P['E3'][se_rule]])
        D['f'] = rng.uniform(A['f_lo'], A['f_hi'], K); D['d'] = rng.uniform(A['days_lo'], A['days_hi'], K)
        D['z'] = {y: rng.standard_normal((K, 80)) for y in YEARS}
        D['rate_z'] = rng.standard_normal((K, 400))          # one column per mortality-rate cell (assigned in order)
        D['ln_irr_mi'] = math.log(P['anger_mi']['est']) + P['anger_mi'][se_rule] * rng.standard_normal(K)
        D['ln_or_stroke'] = math.log(P['anger_stroke']['est']) + P['anger_stroke'][se_rule] * rng.standard_normal(K)
        D['lam'] = np.exp(rng.uniform(math.log(A['anger_lambda_lo']), math.log(A['anger_lambda_hi']), K))
    D['K'] = K
    if overrides:
        for k, v in overrides.items():
            D[k] = np.broadcast_to(np.asarray(v, float), D[k].shape).copy()
    return D


# ------------------------------------------------------------------ engine
def taylor_excess(mom_s, c):
    """sum_i w_i (exp(c a_i) - 1) from perturbed weighted moments mom_s[cell, m, K] (m = 0..NTERMS; m=0 unused)."""
    out = np.zeros((mom_s.shape[0], len(c))); term = np.ones_like(c)
    for k in range(1, NTERMS + 1):
        term = term * c / k
        out += mom_s[:, k, :] * term
    return out


def cat_counts(srt, z, thr_min, strict, use_cap, K):
    """Perturbed weighted number of exposed persons with one-way minutes >= thr (or > thr if strict); returns [cell, K]."""
    out = np.zeros((len(srt), K))
    for c, (jw, jwc, cum) in enumerate(srt):
        x = jwc if use_cap else jw
        idx = np.searchsorted(x, thr_min, 'right' if strict else 'left')
        S = cum[-1][None, :] - cum[idx]                     # [K, 81]
        if z is None: out[c] = S[:, 0]
        else: out[c] = S[:, 0] + math.sqrt(SDR) * np.einsum('kr,kr->k', S[:, 1:] - S[:, :1], z)
    return out


def simulate(cells, D, A=ASSUMED, target_years=(2019, 2024), rates_topic='cvd', f_modes=F_MODES, with_anger=True,
             pooled_death_paf=False, baseline_year=2010, deaths_years=(2019,)):
    """Returns a list of records: dict(keys..., paf=array[K], ad=array[K] or None, deaths=array[K] or None)."""
    K = D['K']; meta = cells.meta
    S = {}
    for y in set(target_years) | {baseline_year}:
        Yd = cells.Y[y]; z = D['z'][y]
        S[y] = dict(Wtot=perturb(Yd['Wtot'], z), Wcar=perturb(Yd['Wcar'], z),
                    mom=perturb(np.swapaxes(Yd['mom'], 1, 2), z), momc=perturb(np.swapaxes(Yd['momc'], 1, 2), z))
    X = {}                                                   # (scenario, fmode, year) -> (X_obs, X_cap) [cell, K]
    d = D['d']; days7 = A['days_in_week_for_daily_average']
    for s in LINEAR:
        for fm in f_modes:
            f = D['f'] if fm == 'U(0,1)' else np.full(K, float(fm))
            c = D['beta_' + s] * f * d / days7             # log-RR per hour of round-trip car time on a commuting day
            for y in S:
                X[(s, fm, y)] = (taylor_excess(S[y]['mom'], c), taylor_excess(S[y]['momc'], c))
    hr = np.exp(D['lnhr']); u = A['warren_noncommute_h']
    t1, t2, t3 = 30 * (4 - u) / d, 30 * (7 - u) / d, 30 * (10 - u) / d     # thresholds in one-way minutes
    for y in S:
        z = D['z'][y]; res = []
        for cap in (False, True):
            n1 = cat_counts(cells.Y[y]['srt'], z, t1, False, cap, K); n2 = cat_counts(cells.Y[y]['srt'], z, t2, False, cap, K)
            n3 = cat_counts(cells.Y[y]['srt'], z, t3, A['warren_gt10_strict'], cap, K)
            res.append((n1 - n2) * (hr[:, 0] - 1) + (n2 - n3) * (hr[:, 1] - 1) + n3 * (hr[:, 2] - 1))
        X[('E', 'not_applicable', y)] = tuple(res)
    if with_anger:
        for nm, lnrr, win in (('anger_mi', D['ln_irr_mi'], A['window_mi_h']), ('anger_stroke', D['ln_or_stroke'], A['window_stroke_h'])):
            c = (np.exp(lnrr) - 1) * D['lam'] * win * d / 168.0   # excess RR per hour of car time on a commuting day
            for y in S:
                X[(nm, 'not_applicable', y)] = (S[y]['mom'][:, 1, :] * c, S[y]['momc'][:, 1, :] * c)

    def unit_mask(counties=None, bands=None, sex=None):
        m = np.ones(len(meta), bool)
        if counties is not None: m &= meta.county.isin(counties).to_numpy()
        if bands is not None: m &= meta.band.isin(bands).to_numpy()
        if sex is not None: m &= (meta.sex == sex).to_numpy()
        return m

    def pafs(key, ty, m):
        s, fm = key
        xo, xc = X[(s, fm, ty)]; xb = X[(s, fm, baseline_year)][0]
        Xo, Xc, Xb = xo[m].sum(0), xc[m].sum(0), xb[m].sum(0)
        Wt, Wb = S[ty]['Wtot'][m].sum(0), S[baseline_year]['Wtot'][m].sum(0)
        Ct, Cb = S[ty]['Wcar'][m].sum(0), S[baseline_year]['Wcar'][m].sum(0)
        Eo = 1 + Xo / Wt
        with np.errstate(divide='ignore', invalid='ignore'):
            dur = np.where(Cb > 0, Xb / Cb, 0.0)
        return {'cf1_2010_distribution': 1 - (1 + Xb / Wb) / Eo,
                'cf1b_2010_duration_only': 1 - (1 + (Ct / Wt) * dur) / Eo,
                'cf2_cap30': (Xo - Xc) / (Wt + Xo),
                'cf3_no_car': Xo / (Wt + Xo)}

    groups = {'core9': list(meta[meta.core9].county.unique()), 'adjacent5': list(meta[~meta.core9].county.unique()),
              'all14': list(meta.county.unique())}
    band_sets = {'35_44': ['35_44'], '45_54': ['45_54'], '55_64': ['55_64'], '35_64': MORT_BANDS['35_64'], '65plus': ['65plus']}
    rates = {t: load_rates(t) for t in ({rates_topic, 'chd', 'stroke'} if with_anger else {rates_topic})}
    rz = [0]
    def rate_draw(topic, county, mband, sexlab):
        r = rates[topic].loc[(county, MORT_AGE[mband], sexlab)]
        if D['rate_z'] is None: return np.full(K, r.value)
        j = rz[0]; rz[0] += 1
        return np.exp(math.log(r.value) + lognormal_se(r.ci_low, r.ci_high) * D['rate_z'][:, j])

    scen = [(s, fm, s, 'both') for s in LINEAR for fm in f_modes] + [('E', 'not_applicable', 'E_both', 'both'), ('E', 'not_applicable', 'E_men', 'men')]
    if with_anger: scen += [('anger_mi', 'not_applicable', 'anger_mi', 'both'), ('anger_stroke', 'not_applicable', 'anger_stroke', 'both')]
    topic_of = {'anger_mi': 'chd', 'anger_stroke': 'stroke'}
    sexcode = {'both': None, 'men': 1}; sexlab = {'both': 'Overall', 'men': 'Men'}
    # baseline deaths by county x mortality band x sex x topic. Rates are always the 2019 county rates (no later age-specific
    # mortality exists); populations are those of each year in deaths_years (default 2019 only; 2024 = labelled scenario).
    deaths = {}
    need = {(rates_topic, 'both'), (rates_topic, 'men')} | ({('chd', 'both'), ('stroke', 'both')} if with_anger else set())
    if rates_topic == 'majorcvd': need.discard(('majorcvd', 'men'))
    for topic, sx in sorted(need):
        for cty in groups['all14']:
            for mb in MBANDS:
                rate = rate_draw(topic, cty, mb, sexlab[sx])
                for dy in deaths_years:
                    if dy in S: deaths[(topic, sx, cty, mb, dy)] = rate * S[dy]['Wtot'][unit_mask([cty], MORT_BANDS[mb], sexcode[sx])].sum(0) / 1e5
    out = []
    for s, fm, label, sx in scen:
        topic = topic_of.get(s, rates_topic)
        for ty in target_years:
            # pooled-person PAFs for every age band
            for g, cl in groups.items():
                for b, bs in band_sets.items():
                    for cf, v in pafs((s, fm), ty, unit_mask(cl, bs, sexcode[sx])).items():
                        out.append(dict(target_year=ty, scenario=label, sex=sx, net_sitting_fraction=fm, counterfactual=cf, county_group=g,
                                        age_band=b, quantity='paf_pooled_persons', v=v))
            if (topic, sx, groups['all14'][0], '35_64', ty) not in deaths: continue
            # county-specific PAFs x county deaths
            ad = {(g, mb, cf): np.zeros(K) for g in groups for mb in MBANDS for cf in CFS}
            dd = {(g, mb): np.zeros(K) for g in groups for mb in MBANDS}
            for g, cl in groups.items():
                for mb in MBANDS:
                    if pooled_death_paf:
                        pg = pafs((s, fm), ty, unit_mask(cl, MORT_BANDS[mb], sexcode[sx]))
                    for cty in cl:
                        Dc = deaths[(topic, sx, cty, mb, ty)]; dd[(g, mb)] += Dc
                        pc = pg if pooled_death_paf else pafs((s, fm), ty, unit_mask([cty], MORT_BANDS[mb], sexcode[sx]))
                        for cf in CFS: ad[(g, mb, cf)] += pc[cf] * Dc
            for g in groups:
                for cf in CFS:
                    tot_ad = np.zeros(K); tot_d = np.zeros(K)
                    for mb in MBANDS:
                        tot_ad += ad[(g, mb, cf)]; tot_d += dd[(g, mb)]
                        for q, v in (('attributable_deaths', ad[(g, mb, cf)]), ('af_death_weighted', ad[(g, mb, cf)] / dd[(g, mb)]), ('baseline_deaths', dd[(g, mb)])):
                            out.append(dict(target_year=ty, scenario=label, sex=sx, net_sitting_fraction=fm, counterfactual=cf, county_group=g, age_band=mb, quantity=q, v=v))
                    for q, v in (('attributable_deaths', tot_ad), ('af_death_weighted', tot_ad / tot_d), ('baseline_deaths', tot_d)):
                        out.append(dict(target_year=ty, scenario=label, sex=sx, net_sitting_fraction=fm, counterfactual=cf, county_group=g, age_band='35plus', quantity=q, v=v))
    return out


def summarise(records, central_records=None):
    rows = []
    cen = {}
    if central_records is not None:
        for r in central_records:
            cen[tuple(r[k] for k in KEYS)] = float(r['v'][0])
    for r in records:
        v = r['v']; k = tuple(r[k] for k in KEYS)
        q = np.percentile(v, [2.5, 50, 97.5])
        rows.append(dict(zip(KEYS, k), central=cen.get(k, np.nan), median=q[1], lo95=q[0], hi95=q[2], mean=v.mean(), sd=v.std(ddof=1) if len(v) > 1 else 0.0,
                         prob_gt0=float((v > 0).mean()), n_draws=len(v)))
    return pd.DataFrame(rows)


KEYS = ['target_year', 'scenario', 'sex', 'net_sitting_fraction', 'counterfactual', 'county_group', 'age_band', 'quantity']
