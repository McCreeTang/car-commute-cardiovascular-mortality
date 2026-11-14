
"""Steps 2-3. Attributable cardiovascular deaths with Monte Carlo uncertainty.
Run: python burden/02_burden_mc.py   (from the workspace root; ~3 min)
Outputs: burden_results.csv, burden_anger_illustrative.csv, burden_assumptions.csv, burden_draws_headline.csv, burden/run_meta.json"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from burden_model import *

SEED = 20261113
K = 40000
CHUNK = 2500


def slice_draws(D, sl):
    out = {}
    for k, v in D.items():
        if k == 'K': continue
        if k == 'z': out[k] = {y: a[sl] for y, a in v.items()}
        else: out[k] = v[sl]
    out['K'] = len(out['f'])
    return out


def run_mc(cells, P, K=K, seed=SEED, A=ASSUMED, se_rule='se_log', overrides=None, **kw):
    D = make_draws(K, seed, P, A=A, se_rule=se_rule, overrides=overrides)
    parts = [simulate(cells, slice_draws(D, slice(i, min(i + CHUNK, K))), A=A, **kw) for i in range(0, K, CHUNK)]
    recs = parts[0]
    for j, r in enumerate(recs):
        r['v'] = np.concatenate([p[j]['v'] for p in parts])
    return recs, D


if __name__ == '__main__':
    t0 = time.time()
    P = read_parameters()
    df = load_pums()
    cells = Cells(df)
    central = simulate(cells, make_draws(1, 0, P, central=True))
    recs, D = run_mc(cells, P)
    S = summarise(recs, central)
    print('MC done', round(time.time() - t0, 1), 's', S.shape)

    # ---------------- tidy results table: one row per stratum x scenario x counterfactual
    idx = ['target_year', 'scenario', 'sex', 'net_sitting_fraction', 'counterfactual', 'county_group', 'age_band']
    def wide(q, pre):
        t = S[S.quantity == q].set_index(idx)[['median', 'lo95', 'hi95', 'central', 'prob_gt0']]
        t.columns = [pre + '_' + c for c in ['median', 'lo95', 'hi95', 'central', 'prob_gt0']]
        return t
    R = wide('paf_pooled_persons', 'paf_pooled').join(wide('af_death_weighted', 'af_dw'), how='outer') \
        .join(wide('attributable_deaths', 'attr_deaths'), how='outer').join(wide('baseline_deaths', 'baseline_deaths').drop(columns='baseline_deaths_prob_gt0'), how='outer').reset_index()
    has_d = R.attr_deaths_median.notna()
    R['af_definition'] = np.where(has_d, 'death-weighted mean of county PAFs (= attributable deaths / baseline deaths)', 'pooled-person PAF for the stratum')
    for c in ['median', 'lo95', 'hi95', 'central']:
        R['attributable_fraction_' + c] = np.where(has_d, R['af_dw_' + c], R['paf_pooled_' + c])
    R['ui_spans_zero'] = (R.attributable_fraction_lo95 <= 0) & (R.attributable_fraction_hi95 >= 0)
    is_anger = R.scenario.str.startswith('anger')
    R['period'] = np.where(R.target_year == 2019, 'primary (2010-2019)', 'descriptive (2024; fractions only, no mortality data after 2019/2020)')
    desc = {'A': 'A central: generic sitting, CVD mortality, RR per h/day linear (DR027)',
            'B': 'B low: generic sitting, slope below 6 h/day total sitting (DR028 notes)',
            'C': 'C high: generic sitting, slope above 6 h/day total sitting (DR028)',
            'D': 'D fatal+non-fatal CVD slope per h/day applied to mortality (DR033 notes)',
            'E_both': 'E driving-specific categorical HRs (DR001-DR003), men-only HRs applied to both sexes',
            'E_men': 'E driving-specific categorical HRs (DR001-DR003), men only',
            'anger_mi': 'ILLUSTRATIVE anger trigger: MI onset IRR (DR047) x assumed driving-anger frequency, applied to CHD deaths',
            'anger_stroke': 'ILLUSTRATIVE anger trigger: stroke onset OR (DR050) x assumed driving-anger frequency, applied to stroke deaths'}
    R['scenario_description'] = R.scenario.map(desc)
    R['note'] = ''
    R.loc[R.target_year == 2024, 'note'] = 'attributable deaths not computed: county age-specific mortality ends 2019/2020'
    R.loc[R.age_band.isin(['35_44', '45_54', '55_64']), 'note'] = 'fraction only: mortality rates exist only for 35-64 and 65+'
    cols = idx + ['scenario_description', 'period', 'af_definition', 'attributable_fraction_median', 'attributable_fraction_lo95', 'attributable_fraction_hi95',
                  'attributable_fraction_central', 'attr_deaths_median', 'attr_deaths_lo95', 'attr_deaths_hi95', 'attr_deaths_central', 'attr_deaths_prob_gt0',
                  'ui_spans_zero', 'baseline_deaths_median', 'baseline_deaths_lo95', 'baseline_deaths_hi95', 'baseline_deaths_central',
                  'paf_pooled_median', 'paf_pooled_lo95', 'paf_pooled_hi95', 'paf_pooled_central', 'note']
    main = R.loc[~is_anger, cols].copy()
    # explicit not-assessed rows for ages under 35
    na = pd.DataFrame([dict(target_year=y, scenario='not assessed', sex='both', net_sitting_fraction='not_applicable', counterfactual='not_applicable', county_group=g, age_band='16_34',
                            scenario_description='burden not assessed', period='', af_definition='',
                            note='burden not assessed under age 35: no baseline cardiovascular mortality rates are available and none were imputed; exposure is in exposure_distributions.csv')
                       for y in (2019, 2024) for g in GROUPS])
    main = pd.concat([main, na], ignore_index=True)
    main.to_csv('burden_results.csv', index=False)
    ang = R.loc[is_anger, cols].copy()
    ang.insert(0, 'ILLUSTRATIVE_ONLY', True)
    ang['note'] = 'illustrative scenario; rests on an assumed frequency of driving-anger episodes that no dataset supplies; excluded from all headline totals'
    ang.to_csv('burden_anger_illustrative.csv', index=False)

    # ---------------- draws for the headline quantities (plot-ready)
    keep = []
    for r in recs:
        if r['target_year'] == 2019 and r['county_group'] == 'all14' and r['age_band'] == '35plus' and r['quantity'] == 'attributable_deaths' \
                and r['net_sitting_fraction'] in ('U(0,1)', 'not_applicable') and not r['scenario'].startswith('anger'):
            keep.append(pd.Series(r['v'], name='%s|%s' % (r['scenario'], r['counterfactual'])))
    dd = pd.concat(keep, axis=1); dd.insert(0, 'draw', np.arange(len(dd))); dd.insert(1, 'net_sitting_fraction_f', D['f']); dd.insert(2, 'days_per_week_d', D['d'])
    dd.round(4).to_csv('burden_draws_headline.csv', index=False)

    # ---------------- assumptions table
    A = ASSUMED; rows = []
    def addp(name, value, rng, dist, src, abs_only, note):
        rows.append(dict(parameter=name, value=value, range_or_ci=rng, distribution_in_monte_carlo=dist, source_row_id=src, abstract_only=abs_only, note=note))
    lab = {'A': 'RR of CVD mortality per additional h/day sitting, scenario A (central)', 'B': 'RR per h/day, scenario B (below 6 h/day total sitting)',
           'C': 'RR per h/day, scenario C (above 6 h/day total sitting)', 'D': 'RR of fatal+non-fatal CVD per h/day sedentary, scenario D',
           'E1': 'HR CVD mortality, 4-7 vs <4 h/week in a car, scenario E', 'E2': 'HR CVD mortality, 7-10 vs <4 h/week in a car, scenario E',
           'E3': 'HR CVD mortality, >10 vs <4 h/week in a car, scenario E', 'anger_mi': 'ILLUSTRATIVE: IRR of MI onset within 2 h of an anger outburst',
           'anger_stroke': 'ILLUSTRATIVE: OR of acute stroke within 1 h of anger or emotional upset'}
    for k, p in P.items():
        addp(lab[k], p['est'], '%g-%g (%d%% CI)' % (p['lo'], p['hi'], round(p['level'] * 100)), 'log-normal, SE(log)=%.5f from the published CI' % p['se_log'],
             p['row_id'], p['abstract_only'], '%s; read from %s' % (p['source'], p['field']))
    addp('Commute days per week (d)', 4.5, '%g-%g' % (A['days_lo'], A['days_hi']), 'uniform', 'assumed', 'not_applicable',
         'ACS does not record commute days; 5 days x mean weeks worked/52 among 2019 car commuters gives the value in burden/exposure_meta.json; 3 and 5 days shown as sensitivities')
    addp('Fraction of car commute time that is net additional sitting (f), scenarios A-D', 0.5, '%g-%g' % (A['f_lo'], A['f_hi']), 'uniform; fixed values 0.25, 0.5, 0.75, 1.0 also reported',
         'assumed', 'not_applicable', 'no direct estimate exists; DR005-DR008 source (Ding 2014) suggests displacement of other sitting')
    addp('Fraction f for scenario E', 1.0, 'fixed', 'not varied', 'assumed', 'not_applicable', 'Warren 2010 exposure is car time itself, so no displacement factor is applied')
    addp('Daily averaging of weekly commute hours', A['days_in_week_for_daily_average'], 'fixed', 'not varied', 'assumed', 'not_applicable',
         'h/day = weekly hours / 7; workday-only averaging shown as a sensitivity')
    addp('Car modes (primary)', 'car_alone + carpool', 'sensitivity: + taxi, motorcycle, bus, rail, ferry', 'not varied', 'assumed', 'not_applicable', 'ACS travel time is door-to-door and is treated as in-vehicle time')
    addp('Travel-time top-code', 'published replacement value (141/142/141 min in 2010/2019/2024)', 'sensitivity: largest uncensored value (100/115/115 min) and 180 min', 'not varied', 'data dictionary', 'not_applicable',
         'Census replaces all values above a threshold by one value; the threshold differs between 2010 and 2019')
    addp('Counterfactual 2 cap on one-way car commute', A['cap_min'], 'fixed', 'not varied', 'assumed', 'not_applicable', 'minutes')
    addp('Counterfactual 1 baseline year', 2010, 'fixed', 'sampling error of the 2010 sample propagated', 'assumed', 'not_applicable', '2010 followed a recession; cf1b holds the 2019 car-commuter share fixed and changes only durations')
    addp('Warren categories applied to commute car hours only (non-commute car time)', A['warren_noncommute_h'], 'sensitivity: 2 and 3.9 h/week', 'not varied', 'assumed', 'not_applicable', 'Warren 2010 measured all car time')
    addp('Warren category boundaries', '<4; 4 to <7; 7 to 10; >10 h/week', 'sensitivity: >=10', 'not varied', 'assumed', 'not_applicable', 'published labels do not state boundary inclusion')
    addp('Correlation between the three Warren log-HRs', A['warren_rho'], 'sensitivity: 0 and 1', 'multivariate normal', 'assumed', 'not_applicable', 'the three HRs share a reference group; covariance not published')
    addp('Warren men-only HRs applied to women', 'yes in E_both; no in E_men', '', '', 'assumed', 'not_applicable', 'no driving-specific estimate exists for women')
    addp('Relative risks constant across age bands', 'yes', '', '', 'assumed', 'not_applicable', 'no usable age-stratified estimates in the parameter table')
    addp('Sampling error', '80 ACS replicate weights', '', 'normal random combination of replicate deviations (variance = 4/80 x sum of squared deviations); independent between survey years', 'PUMS', 'not_applicable', '')
    addp('Baseline mortality rate uncertainty', 'county x age band smoothed rate, 2019', 'published interval, treated as 95%', 'log-normal, independent across counties and bands', 'mortality_long.parquet (topic cvd)', 'not_applicable',
         'rates are age-standardised within band and model-smoothed; deaths = rate x PUMS population')
    addp('ILLUSTRATIVE: driving-anger outbursts per hour of car commuting', float(np.sqrt(A['anger_lambda_lo'] * A['anger_lambda_hi'])), '%g-%g' % (A['anger_lambda_lo'], A['anger_lambda_hi']),
         'log-uniform', 'assumed', 'not_applicable', 'NO DATASET SUPPLIES THIS; range spans one episode per 500 to one per 10 hours of driving')
    addp('ILLUSTRATIVE: hazard window after an episode', '2 h (MI), 1 h (stroke)', 'fixed', 'not varied', 'DR047; DR050', False, 'as defined in the source studies')
    addp('ILLUSTRATIVE: trigger RR for event onset applies equally to CHD / stroke deaths', 'yes', '', '', 'assumed', 'not_applicable', 'source studies measured onset of mostly non-fatal events')
    addp('Monte Carlo', '%d draws, seed %d' % (K, SEED), '', '', 'not_applicable', 'not_applicable', 'numpy default_rng (PCG64)')
    pd.DataFrame(rows).to_csv('burden_assumptions.csv', index=False)
    dr = pd.read_csv(PATHS['dr'])
    meta = dict(seed=SEED, K=K, n_parameter_rows=int(len(dr)), n_abstract_only_rows=int(dr.abstract_only.sum()),
                rows_used=sorted({p['row_id'] for p in P.values()}), abstract_only_rows_used=sorted({p['row_id'] for p in P.values() if p['abstract_only']}),
                runtime_s=round(time.time() - t0, 1), n_persons_35plus={int(y): int(cells.Y[y]['n']) for y in YEARS},
                n_exposed_35plus={int(y): int(cells.Y[y]['n_exposed']) for y in YEARS})
    json.dump(meta, open('burden/run_meta.json', 'w'), indent=1)
    print(json.dumps(meta, indent=1)); print(main.shape, ang.shape, dd.shape)
