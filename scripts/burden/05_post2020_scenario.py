"""Post-2020 SCENARIO (not a finding about observed mortality).
2024 car-commute exposure and 2024 PUMS populations combined with the 2019 county cardiovascular mortality rates (assumption: no
age-specific county mortality exists after 2019/2020), for scenario A and scenario E (both sexes, men only), under
(i) the 2010 distribution kept and (ii) the 2019 distribution kept. Same engine, inputs, seed and number of draws as 02_burden_mc.py.
Run: python burden/05_post2020_scenario.py   (after 01, 02, 03; ~10 min)
Outputs: burden_post2020_scenario.csv; appends rows P1-P5 to burden_validity_checks.csv; burden/post2020_meta.json"""
import importlib, json, math, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from burden_model import *
mc = importlib.import_module('02_burden_mc')

t0 = time.time()
SCEN = ['A', 'E_both', 'E_men']
FM = {'A': 'U(0,1)', 'E_both': 'not_applicable', 'E_men': 'not_applicable'}
SEX = {'A': 'both', 'E_both': 'both', 'E_men': 'men'}
KEPT = 'cf1_2010_distribution'          # engine label of the "baseline-year distribution kept" counterfactual (baseline year set per run)
DBANDS = ['35_64', '65plus', '35plus']   # bands with deaths
PBANDS = ['35_44', '45_54', '55_64', '35_64', '65plus']   # bands with pooled-person fractions
P = read_parameters(); df = load_pums(); cells = Cells(df)


def index(recs):
    out = {}
    for r in recs:
        if r['scenario'] in SCEN and r['net_sitting_fraction'] == FM[r['scenario']] and r['counterfactual'] == KEPT:
            out[(r['target_year'], r['scenario'], r['county_group'], r['age_band'], r['quantity'])] = r['v']
    return out


KW10 = dict(target_years=(2019, 2024), baseline_year=2010, deaths_years=(2019, 2024), f_modes=['U(0,1)'])
KW19 = dict(target_years=(2024,), baseline_year=2019, deaths_years=(2024,), f_modes=['U(0,1)'])


def run(seed):
    """Two passes over the SAME draws (make_draws is deterministic in the seed): baseline 2010, then baseline 2019."""
    a, _ = mc.run_mc(cells, P, seed=seed, **KW10); a = index(a)
    b, _ = mc.run_mc(cells, P, seed=seed, **KW19); b = index(b)
    return a, b


def derived(a, b, s, g, band):
    """Draw vectors for one stratum. a: baseline 2010 (targets 2019 and 2024); b: baseline 2019 (target 2024)."""
    o = {}
    with np.errstate(divide='ignore', invalid='ignore'):
        if band in DBANDS:
            ad10, ad19 = a[(2024, s, g, band, 'attributable_deaths')], b[(2024, s, g, band, 'attributable_deaths')]
            o['ad_2010_kept'], o['ad_2019_kept'] = ad10, ad19
            o['af_2010_kept'], o['af_2019_kept'] = a[(2024, s, g, band, 'af_death_weighted')], b[(2024, s, g, band, 'af_death_weighted')]
            o['baseline_deaths'] = a[(2024, s, g, band, 'baseline_deaths')]
            # burden of the 2010->2019 change evaluated on the 2024 population = ad10 - ad19; share of it reversed by 2019->2024
            o['reversal_same_population'] = -ad19 / (ad10 - ad19)
            # literal alternative: deaths averted in 2024 relative to the 2010-2019 burden as reported for 2019 (2019 population)
            o['reversal_vs_reported_2019_burden'] = -ad19 / a[(2019, s, g, band, 'attributable_deaths')]
            o['ad_2019_reported'] = a[(2019, s, g, band, 'attributable_deaths')]
        if band in PBANDS:
            p10, p19 = a[(2024, s, g, band, 'paf_pooled_persons')], b[(2024, s, g, band, 'paf_pooled_persons')]
            o['paf_pooled_2010_kept'], o['paf_pooled_2019_kept'] = p10, p19
            o['reversal_pooled_persons'] = -p19 / (p10 - p19)        # = (E2019[RR] - E2024[RR]) / (E2019[RR] - E2010[RR])
    return o


def stats(v, c=None):
    q = np.nanpercentile(v, [2.5, 50, 97.5])
    return dict(median=q[1], lo95=q[0], hi95=q[2], central=(np.nan if c is None else float(c[0])), prob_gt0=float(np.mean(v > 0)))


# ------------------------------------------------------------------ main run and deterministic central
A, B = run(mc.SEED)
Dc = make_draws(1, 0, P, central=True)
CA, CB = index(simulate(cells, Dc, **KW10)), index(simulate(cells, Dc, **KW19))
rows = []
for s in SCEN:
    for g in GROUPS:
        for band in ['35_44', '45_54', '55_64', '35_64', '65plus', '35plus']:
            d, c = derived(A, B, s, g, band), derived(CA, CB, s, g, band)
            for cf, tag in (('2010_distribution_kept', '2010_kept'), ('2019_distribution_kept', '2019_kept')):
                r = dict(LABEL='SCENARIO - 2024 exposure and population with 2019 mortality rates; NOT an estimate of observed post-2020 mortality',
                         exposure_year=2024, population_year=2024, mortality_rate_year=2019, scenario=s, sex=SEX[s], net_sitting_fraction=FM[s],
                         counterfactual=cf, county_group=g, age_band=band)
                def put(prefix, key, with_prob=False):
                    st = stats(d[key], c[key])
                    for k in ('median', 'lo95', 'hi95', 'central'): r['%s_%s' % (prefix, k)] = st[k]
                    if with_prob: r[prefix + '_prob_gt0'] = st['prob_gt0']
                    return st
                if band in DBANDS:
                    st = put('attr_deaths', 'ad_' + tag, True); put('attributable_fraction', 'af_' + tag); put('baseline_deaths_2024pop_2019rates', 'baseline_deaths')
                    r['af_definition'] = 'death-weighted mean of county fractions (= attributable deaths / baseline deaths)'
                    r['ui_spans_zero'] = bool(st['lo95'] <= 0 <= st['hi95'])
                else:
                    st = put('attributable_fraction', 'paf_pooled_' + tag); r['af_definition'] = 'pooled-person fraction for the stratum (no mortality rates for 10-year bands)'
                    r['ui_spans_zero'] = bool(st['lo95'] <= 0 <= st['hi95'])
                if band in PBANDS: put('paf_pooled', 'paf_pooled_' + tag)
                if cf == '2019_distribution_kept':
                    if band in DBANDS:
                        put('reversal_fraction', 'reversal_same_population'); put('reversal_vs_reported_2019_burden', 'reversal_vs_reported_2019_burden')
                        r['reversal_definition'] = '-(deaths under 2019 kept) / (deaths under 2010 kept - deaths under 2019 kept), all on the 2024 population with 2019 rates'
                    else:
                        put('reversal_fraction', 'reversal_pooled_persons')
                        r['reversal_definition'] = 'pooled persons: (E2019[RR] - E2024[RR]) / (E2019[RR] - E2010[RR])'
                    if band in DBANDS:
                        st = stats(d['ad_2019_reported'], c['ad_2019_reported'])
                        for k in ('median', 'lo95', 'hi95'): r['attr_deaths_2019_vs_2010_as_reported_%s' % k] = st[k]
                rows.append(r)
out = pd.DataFrame(rows)
out['note'] = ('Post-2020 commuters are a differently selected group (work from home rose). Deaths use 2019 county rates as an assumption. '
               'Negative values under the 2019-kept counterfactual mean fewer modelled deaths than if the 2019 commute distribution had persisted.')
out.to_csv('burden_post2020_scenario.csv', index=False)
print('main run done', round(time.time() - t0), 's', out.shape)

# ------------------------------------------------------------------ validity checks (appended as P-rows)
checks = []
def chk(cid, desc, value, tol, passed, detail=''):
    checks.append(dict(check_id=cid, description=desc, value=value, tolerance=tol, passed=bool(passed), detail=detail))
    print(cid, bool(passed), value, detail)

# P1: counterfactual equal to observed (baseline year = target year = 2024) gives zero
r1, _ = mc.run_mc(cells, P, K=2000, target_years=(2024,), baseline_year=2024, deaths_years=(2024,))
mx = max(np.abs(r['v']).max() for r in r1 if r['counterfactual'].startswith('cf1') and r['quantity'] != 'baseline_deaths')
chk('P1_post2020_counterfactual_equals_observed', 'Post-2020 scenario with the 2024 distribution kept (counterfactual = observed), 2,000 draws, every scenario and stratum: max |fraction or deaths|', mx, 1e-9, mx < 1e-9)

# P2: sign of the 2019-kept result agrees with the sign of the exposure change 2019 -> 2024 in each stratum (deterministic central)
meta = cells.meta
def mean_hours(year, m):                      # mean round-trip car hours per commuting day per resident (full-sample weight)
    Y = cells.Y[year]; return Y['mom'][m, 0, 1].sum() / Y['Wtot'][m, 0].sum()
def mask(counties, bands, sex=None):
    m = meta.county.isin(counties).to_numpy() & meta.band.isin(bands).to_numpy()
    return m & (meta.sex == sex).to_numpy() if sex else m
grp = {'core9': list(meta[meta.core9].county.unique()), 'adjacent5': list(meta[~meta.core9].county.unique()), 'all14': list(meta.county.unique())}
bset = {'35_44': ['35_44'], '45_54': ['45_54'], '55_64': ['55_64'], '35_64': MORT_BANDS['35_64'], '65plus': ['65plus'], '35plus': FINE35}
res = {s: [0, 0, []] for s in SCEN}
for s in SCEN:
    for g in GROUPS:
        for band in bset:
            m = mask(grp[g], bset[band], 1 if s == 'E_men' else None)
            dexp = mean_hours(2024, m) - mean_hours(2019, m)
            c = derived(CA, CB, s, g, band)
            for key in ('ad_2019_kept', 'paf_pooled_2019_kept'):
                if key in c:
                    ok = np.sign(c[key][0]) == np.sign(dexp); res[s][1] += 1; res[s][0] += int(ok)
                    if not ok: res[s][2].append('%s/%s/%s: result %.4g, exposure change %.4g h/day' % (g, band, key, c[key][0], dexp))
for s in SCEN:
    chk('P2_sign_agrees_group_strata_' + s, 'Scenario %s, central: sign of the 2019-kept deaths / pooled fraction equals the sign of the 2019-to-2024 change in mean car-commute hours per resident, county group x age band strata (share agreeing)' % s,
        res[s][0] / res[s][1], 1.0, res[s][0] == res[s][1], detail='%d of %d agree%s' % (res[s][0], res[s][1], ('; disagree: ' + ' | '.join(res[s][2])) if res[s][2] else ''))
# county x mortality band, scenario A (county-specific fractions are what the deaths are built from)
cc = math.log(P['A']['est']) * 0.5 * 4.5 / 7
def cell_excess(year):
    return taylor_excess(np.swapaxes(cells.Y[year]['mom'], 1, 2)[:, :, [0]], np.array([cc]))[:, 0]
x19, x24 = cell_excess(2019), cell_excess(2024); n_ok = n_all = 0; bad = []
for cty in cells.counties:
    for mb in MBANDS:
        m = mask([cty], MORT_BANDS[mb])
        pif = 1 - (1 + x19[m].sum() / cells.Y[2019]['Wtot'][m, 0].sum()) / (1 + x24[m].sum() / cells.Y[2024]['Wtot'][m, 0].sum())
        dexp = mean_hours(2024, m) - mean_hours(2019, m); n_all += 1; ok = np.sign(pif) == np.sign(dexp); n_ok += int(ok)
        if not ok: bad.append('%s/%s' % (cty, mb))
chk('P2_sign_agrees_county_strata_A', 'Scenario A, central: sign of the county-specific 2019-kept fraction equals the sign of the change in mean car-commute hours per resident, 14 counties x 2 mortality age bands (share agreeing)',
    n_ok / n_all, 1.0, n_ok == n_all, detail='%d of %d agree%s' % (n_ok, n_all, ('; disagree: ' + ', '.join(bad)) if bad else ''))

# P3: stability to the seed (same number of draws)
A2, B2 = run(777)
dm = db = dr = 0.0; worst = ''
for s in SCEN:
    for band in DBANDS:
        d1, d2 = derived(A, B, s, 'all14', band), derived(A2, B2, s, 'all14', band)
        for key in ('ad_2010_kept', 'ad_2019_kept'):
            q1, q2 = np.percentile(d1[key], [2.5, 50, 97.5]), np.percentile(d2[key], [2.5, 50, 97.5])
            rel = abs(q1[1] - q2[1]) / abs(q1[1])
            if rel > dm: dm, worst = rel, '%s | %s | %s: %.3f vs %.3f' % (s, band, key, q1[1], q2[1])
            db = max(db, abs(q1[0] - q2[0]) / (q1[2] - q1[0]), abs(q1[2] - q2[2]) / (q1[2] - q1[0]))
        dr = max(dr, abs(np.nanmedian(d1['reversal_same_population']) - np.nanmedian(d2['reversal_same_population'])))
chk('P3a_post2020_seed_median', 'Post-2020 scenario, seed %d vs 777, %d draws each: max relative difference in median deaths (all 14 counties; 35-64, 65+, 35+; A, E both sexes, E men; both counterfactuals)' % (mc.SEED, mc.K),
    float(dm), 0.03, dm < 0.03, detail='largest: ' + worst)
chk('P3b_post2020_seed_bounds', 'Same rows: max |difference in a 95% bound| / interval width', float(db), 0.03, db < 0.03)
chk('P3c_post2020_seed_reversal', 'Same strata: max absolute difference in the median reversal fraction', float(dr), 0.01, dr < 0.01)

# P4: the 2019 results recomputed inside this run reproduce burden_results.csv (same engine, seed and draws)
R = pd.read_csv('burden_results.csv', keep_default_na=False, na_values=[''])
mx = 0.0; n = 0
for s in SCEN:
    for g in GROUPS:
        for band in DBANDS:
            r = R[(R.target_year == 2019) & (R.scenario == s) & (R.net_sitting_fraction == FM[s]) & (R.counterfactual == KEPT) & (R.county_group == g) & (R.age_band == band)].iloc[0]
            q = np.percentile(A[(2019, s, g, band, 'attributable_deaths')], [2.5, 50, 97.5]); n += 1
            mx = max(mx, abs(q[0] - r.attr_deaths_lo95), abs(q[1] - r.attr_deaths_median), abs(q[2] - r.attr_deaths_hi95))
chk('P4_reproduces_main_2019_results', 'Median and 95%% bounds of 2019 attributable deaths (2010 kept) recomputed in the post-2020 run vs burden_results.csv, %d rows: max abs difference' % n, mx, 1e-8, mx < 1e-8)

# P5: independent recomputation of a pooled reversal fraction straight from the person file
beta, f, d = math.log(P['A']['est']), 0.5, 4.5
def E(year):
    s_ = df[(df.year == year) & (df.agep >= 35) & (df.agep <= 64)]
    a_ = np.where(s_.mode_cat.isin(['car_alone', 'carpool']), 2 * s_.jw.fillna(0) / 60, 0.0)
    return float(np.average(np.exp(beta * f * d * a_ / 7), weights=s_.pwgtp))
ind = (E(2019) - E(2024)) / (E(2019) - E(2010)); eng = float(derived(CA, CB, 'A', 'all14', '35_64')['reversal_pooled_persons'][0])
chk('P5_independent_reversal_fraction', 'Scenario A central pooled reversal fraction, 35-64, all 14 counties: engine vs direct pandas computation (abs difference)', abs(ind - eng), 1e-9, abs(ind - eng) < 1e-9,
    detail='engine %.6f direct %.6f' % (eng, ind))

V = pd.read_csv('burden_validity_checks.csv')
V = pd.concat([V[~V.check_id.astype(str).str.startswith('P')], pd.DataFrame(checks)], ignore_index=True)
V.to_csv('burden_validity_checks.csv', index=False)
json.dump(dict(seed=mc.SEED, K=mc.K, scenarios=SCEN, runtime_s=round(time.time() - t0, 1),
               n_persons_35plus={int(y): int(cells.Y[y]['n']) for y in YEARS}), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'post2020_meta.json'), 'w'), indent=1)
print('done', round(time.time() - t0), 's', len(V))
