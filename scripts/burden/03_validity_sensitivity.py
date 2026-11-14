
"""Validity checks and sensitivity analyses for the burden model (same engine as the main run).
Run: python burden/03_validity_sensitivity.py   (after 01 and 02)
Outputs: burden_validity_checks.csv, burden_sensitivity.csv"""
import copy, importlib, json, math, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from burden_model import *
mc = importlib.import_module('02_burden_mc')

t0 = time.time()
P = read_parameters(); df = load_pums(); cells = Cells(df)
checks = []
def chk(cid, desc, value, tol, passed, detail=''):
    checks.append(dict(check_id=cid, description=desc, value=value, tolerance=tol, passed=bool(passed), detail=detail))
    print(cid, bool(passed), value, detail)

def tab(recs):
    return summarise(recs)
def get(T, scenario, cf, q='attributable_deaths', group='all14', band='35plus', fm=None, year=2019, col='median'):
    fm = fm if fm is not None else ('U(0,1)' if scenario in LINEAR else 'not_applicable')
    r = T[(T.target_year == year) & (T.scenario == scenario) & (T.counterfactual == cf) & (T.quantity == q) & (T.county_group == group)
          & (T.age_band == band) & (T.net_sitting_fraction == fm)]
    assert len(r) == 1, (scenario, cf, q, group, band, fm, len(r))
    return float(r[col].iloc[0])

central = simulate(cells, make_draws(1, 0, P, central=True)); C0 = tab(central)

# ---- V1: relative risk of 1 gives zero burden (full Monte Carlo path, all other inputs random)
ov = {'beta_A': 0, 'beta_B': 0, 'beta_C': 0, 'beta_D': 0, 'lnhr': 0, 'ln_irr_mi': 0, 'ln_or_stroke': 0}
r1, _ = mc.run_mc(cells, P, K=2000, overrides=ov)
mx = max(np.abs(r['v']).max() for r in r1 if r['quantity'] != 'baseline_deaths')
chk('V1_rr_equals_1', 'All relative risks set to 1 (2,000 draws, sampling/assumption draws left random): max |PAF or attributable deaths| over all strata, scenarios, counterfactuals', mx, 1e-9, mx < 1e-9)

# ---- V2: counterfactual equal to observed gives zero
cells_nocap = Cells(df, cap_min=1e9)
r2, _ = mc.run_mc(cells_nocap, P, K=2000)
mx = max(np.abs(r['v']).max() for r in r2 if r['counterfactual'] == 'cf2_cap30' and r['quantity'] != 'baseline_deaths')
chk('V2a_cap_not_binding', 'Cap counterfactual with a cap above every travel time (counterfactual = observed): max |PAF or deaths|', mx, 1e-9, mx < 1e-9)
r2b, _ = mc.run_mc(cells, P, K=2000, baseline_year=2019, target_years=(2019,))
mx = max(np.abs(r['v']).max() for r in r2b if r['counterfactual'].startswith('cf1') and r['quantity'] != 'baseline_deaths')
chk('V2b_baseline_equals_target', 'Baseline-year counterfactuals with baseline year = 2019 (counterfactual = observed): max |PAF or deaths|', mx, 1e-9, mx < 1e-9)

# ---- V3: monotonicity in exposure, f, d, cap
scales = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]; vals = {s: [] for s in ['A', 'B', 'C', 'D', 'E_both']}
for sc in scales:
    cs = Cells(df, exposure_scale=sc, years=[2010, 2019])
    T = tab(simulate(cs, make_draws(1, 0, P, central=True), target_years=(2019,)))
    for s in vals: vals[s].append(get(T, s, 'cf3_no_car', fm='0.5' if s in LINEAR else None))
for s, v in vals.items():
    chk('V3a_monotone_exposure_' + s, 'Attributable deaths (no-car counterfactual, all 14 counties, 35+, central) increase with travel time scaled by %s' % scales,
        float(np.diff(v).min()), 0, np.all(np.diff(v) > 0), detail='; '.join('%.2f' % x for x in v))
v = [get(C0, 'A', 'cf3_no_car', fm=f) for f in ['0.25', '0.5', '0.75', '1.0']]
chk('V3b_monotone_f', 'Scenario A deaths (no-car) increase with net-sitting fraction f = 0.25, 0.5, 0.75, 1.0', float(np.diff(v).min()), 0, np.all(np.diff(v) > 0), detail='; '.join('%.2f' % x for x in v))
v = []
for dd in [3, 4, 5]:
    Dd = make_draws(1, 0, P, central=True, overrides={'d': dd}); v.append(get(tab(simulate(cells, Dd, target_years=(2019,))), 'A', 'cf3_no_car', fm='0.5'))
chk('V3c_monotone_days', 'Scenario A deaths (no-car) increase with commute days per week = 3, 4, 5', float(np.diff(v).min()), 0, np.all(np.diff(v) > 0), detail='; '.join('%.2f' % x for x in v))
v = []
for cap in [15, 30, 45, 60, 90]:
    cs = Cells(df, cap_min=cap, years=[2010, 2019]); v.append(get(tab(simulate(cs, make_draws(1, 0, P, central=True), target_years=(2019,))), 'A', 'cf2_cap30', fm='0.5'))
chk('V3d_monotone_cap', 'Scenario A deaths under a travel-time cap decrease as the cap rises (15, 30, 45, 60, 90 min)', float(np.diff(v).max()), 0, np.all(np.diff(v) < 0), detail='; '.join('%.2f' % x for x in v))
ordv = [get(C0, 'A', c, fm='0.5') for c in ['cf2_cap30', 'cf3_no_car']]
chk('V3e_cap_below_nocar', 'Cap-30 burden is smaller than the no-car burden (scenario A, central)', ordv[1] - ordv[0], 0, ordv[0] < ordv[1])

# ---- V4: stability to the seed (mc.K draws each)
ra, _ = mc.run_mc(cells, P, seed=mc.SEED); rb, _ = mc.run_mc(cells, P, seed=777)
Ta, Tb = tab(ra), tab(rb)
k = (Ta.target_year == 2019) & (Ta.county_group == 'all14') & (Ta.age_band == '35plus') & (Ta.quantity == 'attributable_deaths') & ~Ta.scenario.str.startswith('anger')
a, b = Ta[k].reset_index(drop=True), Tb[k].reset_index(drop=True)
assert (a[KEYS].values == b[KEYS].values).all()
rel_med = ((a['median'] - b['median']).abs() / a['median'].abs()).max()
im = ((a['median'] - b['median']).abs() / a['median'].abs()).idxmax(); worst_row = '%s | %s | f=%s: %.3f vs %.3f' % (a.scenario[im], a.counterfactual[im], a.net_sitting_fraction[im], a['median'][im], b['median'][im])
width = a.hi95 - a.lo95
rel_bnd = max(((a.lo95 - b.lo95).abs() / width).max(), ((a.hi95 - b.hi95).abs() / width).max())
chk('V4a_seed_median', 'Seed %d vs 777, 40,000 draws each: max relative difference in median attributable deaths (all 14 counties, 35+, every scenario x counterfactual x f setting; %d rows)' % (mc.SEED, k.sum()), float(rel_med), 0.03, rel_med < 0.03, detail='largest: ' + worst_row)
chk('V4b_seed_bounds', 'Seed %d vs 777: max |difference in a 95%% bound| / interval width, same rows' % mc.SEED, float(rel_bnd), 0.03, rel_bnd < 0.03)
# Monte Carlo error of the headline median from 20 batches of 500 draws
hv = [r['v'] for r in ra if r['target_year'] == 2019 and r['scenario'] == 'A' and r['counterfactual'] == 'cf1_2010_distribution' and r['county_group'] == 'all14'
      and r['age_band'] == '35plus' and r['quantity'] == 'attributable_deaths' and r['net_sitting_fraction'] == 'U(0,1)'][0]
bm = np.median(hv.reshape(20, -1), axis=1)
chk('V4c_mc_error', 'Scenario A, 2010-distribution counterfactual: SD of the median across 20 batches of 2,000 draws / sqrt(20), relative to the median', float(bm.std(ddof=1) / math.sqrt(20) / np.median(hv)), 0.03,
    bm.std(ddof=1) / math.sqrt(20) / np.median(hv) < 0.03)

# ---- V5: series evaluation of sum w (exp(c a) - 1) against direct evaluation
Y = cells.Y[2019]; worst = 0.0
for c in [1e-4, math.log(1.02) * 0.5 * 4.5 / 7, math.log(1.07) * 5 / 7, 0.2]:
    direct = np.zeros((cells.ncell, 81)); g = np.expm1(c * Y['a'])
    for j in range(81): direct[:, j] = np.bincount(Y['cid'], weights=Y['W'][:, j] * g, minlength=cells.ncell)
    ser_all = np.stack([taylor_excess(np.swapaxes(Y['mom'], 1, 2)[:, :, [j]], np.full(1, c))[:, 0] for j in range(81)], axis=1)
    worst = max(worst, np.abs(ser_all - direct).max() / np.abs(direct).max())
chk('V5_series_vs_direct', 'Power-series evaluation of the exposure-weighted excess risk vs direct exponentials, all cells x 81 weights, four slopes up to 0.2 per commuting-day hour: max abs difference / max value', float(worst), 1e-10, worst < 1e-10)

# ---- V6: independent recomputation of a headline fraction straight from the person file (no Cells object)
beta = math.log(P['A']['est']); f = 0.5; d = 4.5
def pooled_E(year, lo, hi):
    s = df[(df.year == year) & (df.agep >= lo) & (df.agep <= hi)]
    a = np.where(s.mode_cat.isin(['car_alone', 'carpool']), 2 * s.jw.fillna(0) / 60, 0.0)
    return float(np.average(np.exp(beta * f * d * a / 7), weights=s.pwgtp))
indep = 1 - pooled_E(2010, 35, 64) / pooled_E(2019, 35, 64)
eng = get(C0, 'A', 'cf1_2010_distribution', q='paf_pooled_persons', band='35_64', fm='0.5')
chk('V6_independent_paf', 'Scenario A central pooled PAF, 35-64, all 14 counties, 2010-distribution counterfactual: engine vs direct pandas computation (abs difference)', abs(indep - eng), 1e-12, abs(indep - eng) < 1e-12,
    detail='engine %.8f direct %.8f' % (eng, indep))

# ---- V7: baseline deaths recomputed from the county aggregate file and the mortality table
pc = pd.read_parquet(PATHS['pcya']); rt = load_rates('cvd')
tot = 0.0
for cty in cells.counties:
    for b, lab in (('35_64', '35-64'), ('65plus', '65+')):
        tot += float(pc[(pc.year == 2019) & (pc.county_fips == cty) & (pc.age_band == b)]['pop'].iloc[0]) * rt.loc[(cty, lab, 'Overall')].value / 1e5
eng = get(C0, 'A', 'cf3_no_car', q='baseline_deaths', fm='0.5')
chk('V7_baseline_deaths', 'Baseline CVD deaths 35+, 14 counties, 2019: engine vs rate x population from pums_county_year_age.parquet (abs difference)', abs(tot - eng), 1e-6, abs(tot - eng) < 1e-6, detail='engine %.3f independent %.3f' % (eng, tot))

# ---- V11: independent recomputation of the categorical (Warren) fractions straight from the person file
hrs = [P['E1']['est'], P['E2']['est'], P['E3']['est']]
def E_warren(year, lo, hi, sex=None, cap=None):
    s = df[(df.year == year) & (df.agep >= lo) & (df.agep <= hi)]
    if sex: s = s[s.sex == sex]
    t = np.where(s.mode_cat.isin(['car_alone', 'carpool']), s.jw.fillna(0), 0.0)
    if cap: t = np.minimum(t, cap)
    h = 4.5 * 2 * t / 60
    return float(np.average(np.where(h > 10, hrs[2], np.where(h >= 7, hrs[1], np.where(h >= 4, hrs[0], 1.0))), weights=s.pwgtp))
pairs = [(1 - E_warren(2010, 35, 64) / E_warren(2019, 35, 64), get(C0, 'E_both', 'cf1_2010_distribution', q='paf_pooled_persons', band='35_64')),
         (1 - E_warren(2019, 35, 64, cap=30) / E_warren(2019, 35, 64), get(C0, 'E_both', 'cf2_cap30', q='paf_pooled_persons', band='35_64')),
         (1 - 1 / E_warren(2019, 35, 64), get(C0, 'E_both', 'cf3_no_car', q='paf_pooled_persons', band='35_64')),
         (1 - E_warren(2010, 65, 200, sex=1) / E_warren(2019, 65, 200, sex=1), get(C0, 'E_men', 'cf1_2010_distribution', q='paf_pooled_persons', band='65plus'))]
mx = max(abs(a - b) for a, b in pairs)
chk('V11_independent_categorical_paf', 'Scenario E central pooled PAFs (35-64 three counterfactuals; men 65+ 2010-distribution): engine vs direct pandas computation, max abs difference', mx, 1e-12, mx < 1e-12,
    detail='; '.join('%.6f/%.6f' % p for p in pairs))

# ---- V12: independent recomputation of county-weighted attributable deaths (scenario A, cap 30, 35-64)
ad = 0.0
for cty in cells.counties:
    s = df[(df.year == 2019) & (df.agep >= 35) & (df.agep <= 64) & (df.county_fips == cty)]
    t = np.where(s.mode_cat.isin(['car_alone', 'carpool']), s.jw.fillna(0), 0.0)
    eo = np.average(np.exp(beta * f * d * (2 * t / 60) / 7), weights=s.pwgtp); ec = np.average(np.exp(beta * f * d * (2 * np.minimum(t, 30) / 60) / 7), weights=s.pwgtp)
    ad += (1 - ec / eo) * rt.loc[(cty, '35-64', 'Overall')].value * s.pwgtp.sum() / 1e5
eng = get(C0, 'A', 'cf2_cap30', band='35_64', fm='0.5')
chk('V12_independent_county_deaths', 'Scenario A central attributable deaths, 35-64, cap-30 counterfactual, summed over 14 county-specific PAFs: engine vs direct pandas computation (abs difference)', abs(ad - eng), 1e-9, abs(ad - eng) < 1e-9,
    detail='engine %.6f direct %.6f' % (eng, ad))

# ---- V8: Monte Carlo sampling draws reproduce the replicate-weight SE of a population total
pop_draw = None
D = make_draws(4000, 99, P)
pd_ = perturb(cells.Y[2019]['Wtot'], D['z'][2019])
m = cells.meta.band.isin(MORT_BANDS['35_64']).to_numpy()
sd = pd_[m].sum(0).std(ddof=1); ref = float(pc[(pc.year == 2019) & (pc.county_fips == 'ALL14') & (pc.age_band == '35_64')].pop_se.iloc[0])
chk('V8_sampling_draws', 'SD of the simulated 2019 population 35-64 (4,000 draws) / replicate-weight SE in pums_county_year_age.parquet', float(sd / ref), '0.95-1.05', 0.95 < sd / ref < 1.05, detail='sd %.1f se %.1f' % (sd, ref))

# ---- V9: Monte Carlo median close to the deterministic central value (informational; not expected to be equal)
S = pd.read_csv('burden_results.csv')
h = S[(S.target_year == 2019) & (S.county_group == 'all14') & (S.age_band == '35plus') & (S.scenario == 'A') & (S.net_sitting_fraction == '0.5') & (S.counterfactual == 'cf1_2010_distribution')].iloc[0]
chk('V9_median_vs_central', 'Scenario A, f fixed at 0.5: Monte Carlo median / deterministic central attributable deaths (informational)', float(h.attr_deaths_median / h.attr_deaths_central), '0.9-1.1', 0.9 < h.attr_deaths_median / h.attr_deaths_central < 1.1)

# ---- V10: population reconciliation from step 1
em = json.load(open('burden/exposure_meta.json'))
chk('V10_population_reconciliation', 'Max abs difference in weighted population (and its SE) vs pums_county_year_age.parquet over %d county/region x year x age-band rows' % em['reconciliation_rows'],
    max(em['reconciliation_max_abs_diff_pop'], em['reconciliation_max_abs_diff_se']), 1e-6, max(em['reconciliation_max_abs_diff_pop'], em['reconciliation_max_abs_diff_se']) < 1e-6)
pd.DataFrame(checks).to_csv('burden_validity_checks.csv', index=False)

# ======================================================================= sensitivity analyses
sens = []
def record(name, kind, T, scen=('A', 'B', 'C', 'D', 'E_both', 'E_men'), col='median', extra=None):
    for s in scen:
        for cf in CFS:
            for g in GROUPS:
                for b in ['35_64', '65plus', '35plus']:
                    try:
                        row = dict(analysis=name, kind=kind, scenario=s, counterfactual=cf, county_group=g, age_band=b,
                                   attributable_deaths=get(T, s, cf, group=g, band=b, fm='0.5' if s in LINEAR else None, col=col),
                                   baseline_deaths=get(T, s, cf, q='baseline_deaths', group=g, band=b, fm='0.5' if s in LINEAR else None, col=col))
                    except AssertionError:
                        continue
                    if extra: row.update(extra(T, s, cf, g, b))
                    sens.append(row)
def central_run(cs=cells, A=ASSUMED, ov=None, **kw):
    return tab(simulate(cs, make_draws(1, 0, P, A=A, central=True, overrides=ov), A=A, target_years=(2019,), with_anger=False, **kw))
det = 'deterministic central (f=0.5 for A-D, d=4.5, point RRs, no sampling draw)'
record('base', det, central_run())
record('modes_all_seated_motorized', det, central_run(Cells(df, modeset='seated_motorized', years=[2010, 2019])))
record('topcode_largest_uncensored_value', det, central_run(Cells(df, topcode='floor', years=[2010, 2019])))
record('topcode_180_min', det, central_run(Cells(df, topcode='min180', years=[2010, 2019])))
record('days_per_week_3', det, central_run(ov={'d': 3}))
record('days_per_week_5', det, central_run(ov={'d': 5}))
A2 = dict(ASSUMED); A2['days_in_week_for_daily_average'] = 4.5
record('daily_average_over_workdays_only', det, central_run(A=A2), scen=('A', 'B', 'C', 'D'))
record('mortality_major_cvd_series_2019', det, central_run(rates_topic='majorcvd'))
record('pooled_group_paf_times_group_deaths', det, central_run(pooled_death_paf=True))
for nm, u, strict in (('warren_boundary_ge10', 0.0, False), ('warren_noncommute_car_2h', 2.0, True), ('warren_noncommute_car_3.9h', 3.9, True)):
    A3 = dict(ASSUMED); A3['warren_noncommute_h'] = u; A3['warren_gt10_strict'] = strict
    record(nm, det, central_run(A=A3), scen=('E_both', 'E_men'))
A6 = dict(ASSUMED); A6['warren_gt10_strict'] = False
record('warren_boundary_ge10_with_days_per_week_5', det, central_run(A=A6, ov={'d': 5}), scen=('E_both', 'E_men'))
# within-band age gradient bound for 35-64: apply the 55-64 (or 35-44) pooled PAF to all 35-64 deaths
B = central_run()
for src in ('55_64', '35_44'):
    for s in ('A', 'B', 'C', 'D', 'E_both'):
        for cf in CFS:
            for g in GROUPS:
                fm = '0.5' if s in LINEAR else None
                sens.append(dict(analysis='deaths_35_64_using_pooled_paf_of_%s' % src, kind=det, scenario=s, counterfactual=cf, county_group=g, age_band='35_64',
                                 attributable_deaths=get(B, s, cf, q='paf_pooled_persons', group=g, band=src, fm=fm) * get(B, s, cf, q='baseline_deaths', group=g, band='35_64', fm=fm),
                                 baseline_deaths=get(B, s, cf, q='baseline_deaths', group=g, band='35_64', fm=fm)))
# Monte Carlo variants (mc.K draws, same seed)
def mc_extra(T, s, cf, g, b):
    fm = 'U(0,1)' if s in LINEAR else None
    return dict(lo95=get(T, s, cf, group=g, band=b, fm=fm, col='lo95'), hi95=get(T, s, cf, group=g, band=b, fm=fm, col='hi95'),
                attributable_deaths=get(T, s, cf, group=g, band=b, fm=fm, col='median'))
mck = 'Monte Carlo median and 95%% UI (%d draws; f ~ U(0,1) for A-D)' % mc.K
record('mc_base', mck, Ta, extra=mc_extra)
for rho in (0.0, 1.0):
    A4 = dict(ASSUMED); A4['warren_rho'] = rho
    rr, _ = mc.run_mc(cells, P, A=A4, target_years=(2019,), with_anger=False)
    record('mc_warren_rho_%g' % rho, mck, tab(rr), scen=('E_both', 'E_men'), extra=mc_extra)
rr, _ = mc.run_mc(cells, P, se_rule='se_log_max_halfwidth', target_years=(2019,), with_anger=False)
record('mc_se_from_wider_ci_halfwidth', mck, tab(rr), extra=mc_extra)
A5 = dict(ASSUMED); A5['days_lo'] = 3.0
rr, _ = mc.run_mc(cells, P, A=A5, target_years=(2019,), with_anger=False)
record('mc_days_uniform_3_to_5', mck, tab(rr), extra=mc_extra)
pd.DataFrame(sens).to_csv('burden_sensitivity.csv', index=False)
print('done', round(time.time() - t0, 1), 's', len(checks), len(sens))
