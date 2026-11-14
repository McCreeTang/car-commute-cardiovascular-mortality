"""Writes methods_results_burden.md. Every number is read back from the saved result files; nothing is typed in.
Run: python burden/04_write_report.py   (after 01, 02, 03; optional burden/artifact_ids.json maps file name -> artifact version id)"""
import json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
rd = lambda fn: pd.read_csv(fn, keep_default_na=False, na_values=[''])
R = rd('burden_results.csv'); AN = rd('burden_anger_illustrative.csv'); EX = rd('exposure_distributions.csv')
SX = rd('burden_sensitivity.csv'); VC = rd('burden_validity_checks.csv'); AS = rd('burden_assumptions.csv')
PS = rd('burden_post2020_scenario.csv'); PM = json.load(open(os.path.join(HERE, 'post2020_meta.json')))
EM = json.load(open(os.path.join(HERE, 'exposure_meta.json'))); RM = json.load(open(os.path.join(HERE, 'run_meta.json')))
IDS = json.load(open(os.path.join(HERE, 'artifact_ids.json'))) if os.path.exists(os.path.join(HERE, 'artifact_ids.json')) else {}


def link(fn):
    vid = IDS.get(fn)
    return '[%s](%s)' % (fn, '{{' + 'artifact:' + vid + '}}') if vid else '`%s`' % fn


def row(scenario, cf, band='35plus', group='all14', fm=None, year=2019, T=R):
    fm = fm if fm is not None else ('U(0,1)' if scenario in 'ABCD' else 'not_applicable')
    r = T[(T.target_year == year) & (T.scenario == scenario) & (T.counterfactual == cf) & (T.age_band == band) & (T.county_group == group)
          & (T.net_sitting_fraction == fm)]
    assert len(r) == 1, (scenario, cf, band, group, fm, year, len(r))
    return r.iloc[0]


def ad(r, nd=1):
    f = '%%.%df' % nd
    return (f + ' (' + f + ' to ' + f + ')') % (r.attr_deaths_median, r.attr_deaths_lo95, r.attr_deaths_hi95)


def af(r, nd=3, pre='attributable_fraction'):
    f = '%%.%df' % nd
    return (f + ' (' + f + ' to ' + f + ')') % (100 * r[pre + '_median'], 100 * r[pre + '_lo95'], 100 * r[pre + '_hi95'])


def ex(year, band, metric, group='all14', mode='car', d=None, universe='all residents'):
    q = EX[(EX.year == year) & (EX.age_band == band) & (EX.metric == metric) & (EX.county_group == group) & (EX.universe == universe)]
    q = q[q.mode_def == mode] if metric not in ('population', 'share_worker_at_work', 'share_work_from_home') else q
    q = q[q.days_per_week == d] if d is not None else q[q.days_per_week.isna()]
    assert len(q) == 1, (year, band, metric, group, mode, d, universe, len(q))
    return q.iloc[0]


def sens(analysis, scenario, cf, band='35plus', group='all14', col='attributable_deaths'):
    q = SX[(SX.analysis == analysis) & (SX.scenario == scenario) & (SX.counterfactual == cf) & (SX.age_band == band) & (SX.county_group == group)]
    assert len(q) == 1, (analysis, scenario, cf, band, group, len(q))
    return float(q[col].iloc[0])


def table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '|'.join(['---'] * len(header)) + '|']
    out += ['| ' + ' | '.join(str(c).replace('|', '\\|') for c in r) + ' |' for r in rows]
    return '\n'.join(out)


CF = {'cf1_2010_distribution': '(1) 2010 distribution kept', 'cf1b_2010_duration_only': '(1b) 2010 durations, 2019 car-commuter share',
      'cf2_cap30': '(2) one-way car commute capped at 30 min', 'cf3_no_car': '(3) no car commuting (upper bound)'}
SC = {'A': 'A central sitting slope', 'B': 'B low sitting slope', 'C': 'C high sitting slope', 'D': 'D fatal + non-fatal slope',
      'E_both': 'E driving-specific HRs, both sexes', 'E_men': 'E driving-specific HRs, men only'}
BL = {'16_34': '16-34', '35_44': '35-44', '45_54': '45-54', '55_64': '55-64', '35_64': '35-64', '65plus': '65+', '35plus': '35+'}
GL = {'core9': 'Core nine counties', 'adjacent5': 'Five adjacent counties', 'all14': 'All 14 counties'}
L = []
w = L.append

# ------------------------------------------------------------------ headline numbers
hA = row('A', 'cf1_2010_distribution'); hA64 = row('A', 'cf1_2010_distribution', '35_64'); hA65 = row('A', 'cf1_2010_distribution', '65plus')
hB = row('B', 'cf1_2010_distribution'); hC = row('C', 'cf1_2010_distribution'); hD = row('D', 'cf1_2010_distribution')
hE = row('E_both', 'cf1_2010_distribution'); hEm = row('E_men', 'cf1_2010_distribution')
hA1b = row('A', 'cf1b_2010_duration_only'); hA2 = row('A', 'cf2_cap30'); hA3 = row('A', 'cf3_no_car'); hE3 = row('E_both', 'cf3_no_car')
e10 = ex(2010, '35_64', 'mean_weekly_hours', d=4.5); e19 = ex(2019, '35_64', 'mean_weekly_hours', d=4.5); e24 = ex(2024, '35_64', 'mean_weekly_hours', d=4.5)
m10 = ex(2010, '35_64', 'mean_oneway_min', universe='exposed commuters'); m19 = ex(2019, '35_64', 'mean_oneway_min', universe='exposed commuters')
main = R[(R.target_year == 2019) & R.attr_deaths_median.notna()]
nspan = main.groupby('scenario').ui_spans_zero.agg(['sum', 'size'])
_r = PS[(PS.scenario == 'A') & (PS.counterfactual == '2019_distribution_kept') & (PS.age_band == '35plus') & (PS.county_group == 'all14')].iloc[0]
rv0 = '%.0f (%.0f to %.0f)' % (100 * _r.reversal_fraction_median, 100 * _r.reversal_fraction_lo95, 100 * _r.reversal_fraction_hi95)

w('# Cardiovascular mortality attributable to car-commute sitting time: methods and results of the burden model')
w('')
w('Under the central generic-sitting assumption (scenario A), the lengthening of car commutes between 2010 and 2019 is associated with a median of %s cardiovascular deaths per year among residents aged 35 and over in the 14 study counties, which is %s%% of an estimated %s baseline cardiovascular deaths. '
  'The burden is small in absolute and relative terms, and its lower bound is close to zero because the share of car time that adds to total sitting is unknown and was allowed to range from 0 to 1. '
  'The low-slope scenario (B) gives %s deaths per year and its interval spans zero. '
  'The driving-specific hazard ratios from the single available cohort of US men (scenario E) give a much larger median, %s deaths per year, and that interval also spans zero. '
  'The two approaches therefore differ by a factor of about %.0f at the median, and the data cannot say which is closer to the truth. '
  'These are model-based associations under declared assumptions, not causal effects; no cardiovascular outcome was observed in any commuter. '
  'A separately labelled post-2020 scenario (section 7) applies 2019 mortality rates to 2024 commuting; under scenario A it implies that %s%% of the burden of the 2010-2019 lengthening had been reversed by 2024. That scenario is not an estimate of observed mortality.'
  % (ad(hA), af(hA), '{:,.0f}'.format(hA.baseline_deaths_median), ad(hB), ad(hE, 0), hE.attr_deaths_median / hA.attr_deaths_median, rv0))
w('')
w('## 1. Data and population')
w('')
w('Exposure comes from the 1-year ACS Public Use Microdata Sample person file for 2010 and 2019 (primary period) and 2021 to 2024 (post-2020, descriptive only; no 2020 file exists). '
  'All persons aged 16 or older living in the 14 counties with person-level data were used: %s records in 2010, %s in 2019, and %s, %s, %s and %s in 2021, 2022, 2023 and 2024. The burden engine uses 2010, 2019 and 2024; 2021 to 2023 enter the exposure tables only. '
  'The %s records in these six years from the PUMA that combines San Benito with part of Monterey County were excluded, so San Benito is not in the burden model. '
  'Non-workers, people working from home and commuters by non-car modes are kept in every denominator with zero exposure. '
  'Weighted population totals and their replicate-weight standard errors by county, region, year and age band were compared with `pums_county_year_age.parquet` over %d rows; the maximum absolute difference was %g persons.'
  % (*['{:,}'.format(EM['n_persons_used'][str(y)]) for y in (2010, 2019, 2021, 2022, 2023, 2024)],
     '{:,}'.format(EM['n_excluded_mixed_puma_records']), EM['reconciliation_rows'], EM['reconciliation_max_abs_diff_pop']))
w('')
w('Baseline mortality is the 2019 county cardiovascular disease death rate for ages 35-64 and 65+ (CDC, model-smoothed, age-standardised within band) from `mortality_long.parquet`. '
  'Age bands: 16-34, 35-44, 45-54, 55-64, 65+, and the aggregates 35-64 and 65+ that match the mortality data. County groups: core nine, five adjacent, all 14.')
w('')
w('## 2. Exposure')
w('')
w('For person *i* with one-way travel time *t_i* (minutes) by car alone or carpool:')
w('')
w('- hours in the car on a commuting day: *a_i* = 2 x *t_i* / 60 (zero for everyone else);')
w('- weekly car-commute hours: *h_i* = *d* x *a_i*, where *d* is commute days per week;')
w('- net additional daily sitting: *x_i* = *f* x *h_i* / 7, where *f* is the fraction of car time that is additional to, rather than a replacement for, other sitting.')
w('')
w('**Commute days per week (assumed).** The ACS does not ask how many days a week a person commutes. The model uses *d* = 4.5 as the central value with a uniform range of 4 to 5, and 3 and 5 as fixed sensitivity values. '
  'As a plausibility check only, five days a week multiplied by the mean weeks worked in the past year among 2019 car commuters (%.1f of 52) gives %.2f days per week averaged over the year.'
  % (EM['mean_weeks_worked_car_commuters_2019'], EM['annualised_days_per_week_if_5_day_week_2019']))
w('')
w('**Travel-time top-code.** The Census Bureau replaces every travel time above a threshold with a single value. In this file the replacement value is %.0f, %.0f and %.0f minutes in 2010, 2019 and 2024, and the largest uncensored value is %.0f, %.0f and %.0f minutes. '
  'In 2021, 2022 and 2023 the replacement value is %.0f, %.0f and %.0f minutes and the largest uncensored value is %.0f, %.0f and %.0f minutes. '
  'The threshold therefore differs between 2010 and 2019. The published replacement value was kept in the main analysis. '
  'Two sensitivity analyses replace it with the largest uncensored value of the year (a lower bound) and with 180 minutes. '
  'Every top-coded commuter exceeds 10 hours a week and 30 minutes one way under any value of *d* used here, so the categorical scenario and the 30-minute cap are unaffected by the top-code.'
  % (EM['topcode']['2010']['topcode_value'], EM['topcode']['2019']['topcode_value'], EM['topcode']['2024']['topcode_value'],
     EM['topcode']['2010']['max_uncensored_value'], EM['topcode']['2019']['max_uncensored_value'], EM['topcode']['2024']['max_uncensored_value'],
     *[EM['topcode'][str(y)]['topcode_value'] for y in (2021, 2022, 2023)], *[EM['topcode'][str(y)]['max_uncensored_value'] for y in (2021, 2022, 2023)]))
w('')
w('**Travel time is door-to-door.** It is treated as in-vehicle time, which overstates sitting slightly for car modes and more for transit; the all-seated-motorised sensitivity (car, taxi, motorcycle, bus, rail, ferry) should be read with that in mind.')
w('')
w('### Exposure results')
w('')
w('Table 1. Car-commute exposure among all residents, all 14 counties (car alone or carpool; weekly hours at *d* = 4.5). Standard errors from the 80 replicate weights in parentheses.')
w('')
rows = []
for b in ['16_34', '35_44', '45_54', '55_64', '35_64', '65plus']:
    for y in (2010, 2019, 2024):
        p = ex(y, b, 'population'); s = ex(y, b, 'share_exposed_commuter'); m = ex(y, b, 'mean_oneway_min', universe='exposed commuters')
        a6 = ex(y, b, 'share_oneway_60_89_min'); a9 = ex(y, b, 'share_oneway_90_plus_min'); h = ex(y, b, 'mean_weekly_hours', d=4.5); g = ex(y, b, 'share_weekly_hours_gt10', d=4.5)
        rows.append([BL[b], y, '{:,.0f}'.format(p.value), '%.1f (%.1f)' % (100 * s.value, 100 * s.se), '%.1f (%.1f)' % (m.value, m.se), '%.1f' % (100 * a6.value), '%.1f' % (100 * a9.value),
                     '%.2f (%.2f)' % (h.value, h.se), '%.1f (%.1f)' % (100 * g.value, 100 * g.se)])
w(table(['Age', 'Year', 'Residents', 'Car commuters, % of residents', 'Mean one-way minutes, car commuters', 'One-way 60-89 min, % of residents', 'One-way 90+ min, % of residents',
         'Mean weekly car-commute hours per resident', 'More than 10 h/week, % of residents'], rows))
w('')
w('Among residents aged 35-64, mean weekly car-commute hours per resident rose from %.2f (SE %.2f) in 2010 to %.2f (SE %.2f) in 2019 and stood at %.2f (SE %.2f) in 2024. '
  'Mean one-way travel time among car commuters aged 35-64 rose from %.1f to %.1f minutes between 2010 and 2019. '
  'Part of the rise in hours per resident reflects a larger share of residents commuting by car (%.1f%% in 2010, %.1f%% in 2019), which is why counterfactual 1b below separates duration from participation. '
  'The 2024 values describe a differently selected group of commuters because working from home rose from %.1f%% to %.1f%% of residents aged 35-64 between 2019 and 2024.'
  % (e10.value, e10.se, e19.value, e19.se, e24.value, e24.se, m10.value, m19.value,
     100 * ex(2010, '35_64', 'share_exposed_commuter').value, 100 * ex(2019, '35_64', 'share_exposed_commuter').value,
     100 * ex(2019, '35_64', 'share_work_from_home').value, 100 * ex(2024, '35_64', 'share_work_from_home').value))
w('')
w('Table 2. Mean weekly car-commute hours per resident by county group (*d* = 4.5; SE in parentheses).')
w('')
rows = []
for b in ['16_34', '35_64', '65plus']:
    for g in ['core9', 'adjacent5']:
        rows.append([BL[b], GL[g]] + ['%.2f (%.2f)' % (ex(y, b, 'mean_weekly_hours', group=g, d=4.5).value, ex(y, b, 'mean_weekly_hours', group=g, d=4.5).se) for y in (2010, 2019, 2024)]
                    + ['%.1f' % ex(y, b, 'mean_oneway_min', group=g, universe='exposed commuters').value for y in (2010, 2019, 2024)])
w(table(['Age', 'County group', 'Hours 2010', 'Hours 2019', 'Hours 2024', 'One-way min 2010', 'One-way min 2019', 'One-way min 2024'], rows))
w('')
w('The year-by-year path for 2021 to 2024 is in section 7 (Table 9).')
w('')
w('Ages 16-34: exposure is reported in Table 1 and in %s. **Burden was not assessed under age 35 because no baseline cardiovascular mortality rates are available for that age range; none were imputed.**' % link('exposure_distributions.csv'))
w('')
w('## 3. Risk functions')
w('')
w('Every relative risk was read by row id from `dose_response_parameters.csv` at run time. Of the %d rows in that table, %d are flagged abstract_only; the %d rows used here (%s) are all full-text rows, so **no abstract-only or press-release estimate enters the model** (abstract-only rows used: %s).'
  % (RM['n_parameter_rows'], RM['n_abstract_only_rows'], len(RM['rows_used']), ', '.join(RM['rows_used']), ', '.join(RM['abstract_only_rows_used']) or 'none'))
w('')
w('Table 3. Risk parameters.')
w('')
rr = AS[AS.source_row_id.astype(str).str.fullmatch(r'DR\d+')]
w(table(['Parameter', 'Estimate', 'Interval', 'Row id', 'Abstract only', 'Source and field', 'Monte Carlo distribution'],
        [[r.parameter, r.value, r.range_or_ci, r.source_row_id, r.abstract_only, r.note, r.distribution_in_monte_carlo] for r in rr.itertuples()]))
w('')
w('- Scenarios A to D (generic sitting): RR_i = exp(beta x *x_i*), beta = ln(RR per hour per day). A is the linear slope; B and C are the slopes below and above 6 hours of total daily sitting, used as low and high variants because individual total sitting is unknown; D is the per-hour slope for fatal plus non-fatal cardiovascular disease, applied to mortality as an upper alternative.')
w('- Scenario E (driving-specific): RR_i = 1 for *h_i* < 4, HR_1 for 4 <= *h_i* < 7, HR_2 for 7 <= *h_i* <= 10, HR_3 for *h_i* > 10 hours per week in a car. The hazard ratios come from men only. E_both applies them to both sexes, which is an assumption; E_men restricts exposure, population and mortality rates to men. No displacement factor *f* is applied because the exposure in the source study is car time itself. The source measured all car time, whereas only commute car time is available here.')
w('- The same relative risks are applied in every age band, because the parameter table holds no usable age-specific estimate.')
w('')
w('## 4. Counterfactuals and attributable burden')
w('')
w('For a stratum with person weights *w_i*, the potential impact fraction is')
w('')
w('PIF = [ sum_i *w_i* RR(*x_i*) - sum_i *w_i* RR(*x_i*\') ] / sum_i *w_i* RR(*x_i*),')
w('')
w('where *x_i*\' is the counterfactual exposure:')
w('')
w('1. **2010 distribution kept.** PIF = 1 - E_2010[RR] / E_2019[RR], with each expectation taken over all residents of the stratum in that survey year.')
w('2. **(1b, added) 2010 durations with the 2019 car-commuter share.** E_cf[RR] = 1 + s_2019 x (E_2010[RR | car commuter] - 1), where s_2019 is the 2019 share of residents commuting by car. This removes the part of counterfactual 1 that is due to more residents commuting by car in 2019 than in the post-recession year 2010.')
w('3. **Cap.** One-way car travel time capped at %.0f minutes.' % float(AS[AS.parameter.str.startswith('Counterfactual 2')].value.iloc[0]))
w('4. **No car commuting.** *x_i*\' = 0 for everyone; a theoretical upper bound, not a feasible scenario.')
w('')
w('Attributable deaths per year in county group *g* and mortality age band *b* are the sum over counties of county-specific fractions times county baseline deaths:')
w('')
w('AD_gb = sum over counties c in g of PIF_cb x (rate_cb / 100,000) x N_cb,')
w('')
w('with rate_cb the 2019 county cardiovascular death rate and N_cb the 2019 weighted PUMS population. The reported attributable fraction for 35-64, 65+ and 35+ is AD_gb divided by baseline deaths (a death-weighted mean of county fractions). For the 10-year bands, which have no mortality rates, the fraction is the pooled-person PIF of the stratum and no deaths are computed.')
w('')
w('## 5. Uncertainty')
w('')
w('Monte Carlo simulation with %s draws and seed %d propagates jointly:' % ('{:,}'.format(RM['K']), RM['seed']))
w('')
w('- relative risks: log-normal, SE(log) = (ln upper - ln lower) / (2 x z) from the published interval; the three scenario-E hazard ratios share a reference group and are drawn with an assumed correlation of %s;' % AS[AS.parameter.str.startswith('Correlation')].value.iloc[0])
w('- survey sampling error: each draw adds to every full-sample weighted sum a random combination of its 80 replicate deviations, theta* = theta_0 + sqrt(4/80) x sum_r z_r (theta_r - theta_0) with z_r standard normal, which reproduces the ACS replicate variance and keeps all strata of a survey year correlated; the 2010, 2019 and 2024 samples are perturbed independently;')
w('- assumed parameters: *d* uniform on 4 to 5; *f* uniform on 0 to 1 for scenarios A to D (results at fixed *f* = 0.25, 0.5, 0.75 and 1.0 are also reported);')
w('- baseline mortality rates: log-normal from the published interval of each county rate (treated as a 95% interval; an addition to the three sources named in the task).')
w('')
w('Results are medians with 2.5th and 97.5th percentiles (95%% uncertainty interval, UI). "Central" values in the result files are deterministic evaluations at *d* = 4.5, *f* = 0.5 and the point estimates. The full list of parameters and assumptions is in %s.' % link('burden_assumptions.csv'))
w('')
w('## 6. Results')
w('')
w('Table 4. Attributable cardiovascular deaths per year and attributable fraction, ages 35 and over, all 14 counties, 2019 (median and 95%% UI; *f* uniform on 0 to 1 for A to D). Baseline deaths: %s (95%% UI %s to %s) for both sexes and %s for men.'
  % tuple('{:,.0f}'.format(v) for v in (hA.baseline_deaths_median, hA.baseline_deaths_lo95, hA.baseline_deaths_hi95, hEm.baseline_deaths_median)))
w('')
rows = []
for s in SC:
    for c in CF:
        r = row(s, c)
        rows.append([SC[s], CF[c], ad(r), af(r), '%.3f' % r.attr_deaths_prob_gt0, 'yes' if r.ui_spans_zero else 'no'])
w(table(['Scenario', 'Counterfactual', 'Attributable deaths per year', 'Attributable fraction, %', 'Share of draws above zero', 'UI spans zero'], rows))
w('')
w('Reading Table 4:')
w('')
w('- **Scenario A, 2010 to 2019 lengthening:** %s deaths per year, %s%% of baseline deaths. Holding the 2019 car-commuter share fixed and changing durations only (1b) gives %s. Capping one-way car commutes at 30 minutes gives %s, and removing all car commuting gives %s.' % (ad(hA), af(hA), ad(hA1b), ad(hA2), ad(hA3)))
w('- **Scenarios B, C and D** scale the same exposure contrast by their slopes: %s (B), %s (C) and %s (D) deaths per year for counterfactual 1. The interval for B spans zero in %d of its %d rows with deaths (strata x counterfactuals x settings of *f*) because the published lower confidence limit of that slope is below 1.' % (ad(hB), ad(hC), ad(hD), int(nspan.loc['B', 'sum']), int(nspan.loc['B', 'size'])))
w('- **Scenario E** gives %s deaths per year for both sexes and %s for men only under counterfactual 1, and %s under the no-car bound. The interval spans zero in %d of %d E_both rows and %d of %d E_men rows, because the confidence intervals of the two lower hazard ratios include 1.' % (ad(hE, 0), ad(hEm, 0), ad(hE3, 0), int(nspan.loc['E_both', 'sum']), int(nspan.loc['E_both', 'size']), int(nspan.loc['E_men', 'sum']), int(nspan.loc['E_men', 'size'])))
w('- The intervals for A, C and D exclude zero only because their slope confidence intervals exclude 1 and *f* is assumed positive; with *f* = 0 the burden is zero by construction, and the lower bounds sit close to zero.')
w('')
w('Table 5. Attributable deaths per year by mortality age band, all 14 counties, 2019 (median and 95% UI).')
w('')
rows = []
for b in ['35_64', '65plus']:
    for s in SC:
        rows.append([BL[b], SC[s]] + [ad(row(s, c, b)) for c in CF] + ['%.0f' % row(s, 'cf3_no_car', b).baseline_deaths_median])
w(table(['Age', 'Scenario'] + [CF[c] for c in CF] + ['Baseline deaths'], rows))
w('')
w('For scenario A and counterfactual 1 the attributable fraction is %s%% at ages 35-64 and %s%% at 65+. More of the attributable deaths fall in the 65+ band (%s against %s) only because baseline deaths there are far higher; see the limitation on within-band age below, which makes the 65+ figure the less reliable of the two.'
  % (af(hA64), af(hA65), ad(hA65), ad(hA64)))
w('')
w('Table 6. Attributable deaths per year by county group, counterfactual 1 (2010 distribution kept), 2019 (median and 95% UI; attributable fraction in % in brackets).')
w('')
rows = []
for s in ['A', 'E_both']:
    for g in ['core9', 'adjacent5', 'all14']:
        rows.append([SC[s], GL[g]] + ['%s [%.3f]' % (ad(row(s, 'cf1_2010_distribution', b, g)), 100 * row(s, 'cf1_2010_distribution', b, g).attributable_fraction_median) for b in ['35_64', '65plus', '35plus']])
w(table(['Scenario', 'County group', '35-64', '65+', '35+'], rows))
w('')
w('Table 7. Scenarios A to D at fixed values of the net-sitting fraction *f*: attributable deaths per year, ages 35+, all 14 counties, counterfactual 1 (median and 95% UI over the remaining uncertainty).')
w('')
rows = [[SC[s]] + [ad(row(s, 'cf1_2010_distribution', fm=fm)) for fm in ['0.25', '0.5', '0.75', '1.0', 'U(0,1)']] for s in 'ABCD']
w(table(['Scenario', 'f = 0.25', 'f = 0.5', 'f = 0.75', 'f = 1.0', 'f uniform 0 to 1'], rows))
w('')
w('Table 8. Pooled-person attributable fraction (%) by 10-year age band, scenario A, all 14 counties (median and 95% UI; *f* uniform 0 to 1). The 2024 column is descriptive: fractions only, because county age-specific mortality ends in 2019/2020, and 2024 commuters are a differently selected group.')
w('')
rows = []
for b in ['35_44', '45_54', '55_64', '35_64', '65plus']:
    for y in (2019, 2024):
        rows.append([BL[b], y] + [af(row('A', c, b, year=y), 3, 'paf_pooled') for c in CF])
w(table(['Age', 'Year'] + [CF[c] for c in CF], rows))
w('')
# ------------------------------------------------------------------ post-2020 scenario (labelled; not observed mortality)
def ps(scenario, cf, band='35plus', group='all14'):
    r = PS[(PS.scenario == scenario) & (PS.counterfactual == cf) & (PS.age_band == band) & (PS.county_group == group)]
    assert len(r) == 1, (scenario, cf, band, group, len(r))
    return r.iloc[0]
def rv(r, pre='reversal_fraction', nd=0):
    f = '%%.%df' % nd
    return (f + '%% (' + f + ' to ' + f + ')') % (100 * r[pre + '_median'], 100 * r[pre + '_lo95'], 100 * r[pre + '_hi95'])
K10, K19 = '2010_distribution_kept', '2019_distribution_kept'
PY = EM['exposure_years']; POST = [y for y in PY if y > 2019]
span = lambda r: 'spans zero' if r.ui_spans_zero else 'excludes zero'
wfh = {y: 100 * ex(y, '35_64', 'share_work_from_home').value for y in PY}
hrs = {y: ex(y, '35_64', 'mean_weekly_hours', d=4.5).value for y in PY}
vc = lambda cid: VC[VC.check_id == cid].iloc[0]
w('## 7. Post-2020 scenario: 2024 commuting with 2019 mortality rates (a scenario, not observed mortality)')
w('')
w('**This section is a labelled scenario, not a finding about observed mortality.** It is kept out of the primary 2010-2019 results and out of every association analysis. Three points govern how to read it:')
w('')
w('- **Assumption: 2019 mortality rates are applied to 2024.** No county cardiovascular mortality by age band exists after 2019/2020, so the 2019 county rates are multiplied by 2024 PUMS populations. Cardiovascular mortality changed during and after the pandemic for reasons unrelated to commuting, and none of that is represented here.')
w('- **Post-2020 commuters are a differently selected group.** Working from home rose from %.1f%% of residents aged 35-64 in 2019 to %.1f%% in 2021 and was %.1f%% in 2024, so who commutes by car, and how far, changed for reasons other than housing costs and congestion.' % (wfh[2019], wfh[2021], wfh[2024]))
w('- **It is not an estimate of post-pandemic mortality.** The numbers are what the risk functions of section 3 imply for the change in car-commute time alone, with everything else held at 2019.')
w('')
w('### Exposure after 2020')
w('')
w('Table 9. Mean weekly car-commute hours per resident, %s (car alone or carpool; *d* = 4.5; SE in parentheses). There is no 2020 column because no standard 2020 ACS 1-year PUMS file exists. Years after 2019 are descriptive only.' % ', '.join(str(y) for y in PY))
w('')
rows = []
for g, bands_ in (('all14', ['16_34', '35_44', '45_54', '55_64', '35_64', '65plus']), ('core9', ['16_34', '35_64', '65plus']), ('adjacent5', ['16_34', '35_64', '65plus'])):
    for b in bands_:
        rows.append([GL[g], BL[b]] + ['%.2f (%.2f)' % (ex(y, b, 'mean_weekly_hours', group=g, d=4.5).value, ex(y, b, 'mean_weekly_hours', group=g, d=4.5).se) for y in PY])
w(table(['County group', 'Age'] + [str(y) for y in PY], rows))
w('')
w('Among residents aged 35-64 in all 14 counties, weekly car-commute hours per resident went from %.2f in 2019 to %.2f in 2021, which is %s the 2010 value of %.2f, and then to %.2f in 2022, %.2f in 2023 and %.2f in 2024. '
  'The share of residents aged 35-64 commuting by car was %.1f%% in 2019, %.1f%% in 2021 and %.1f%% in 2024. All mode definitions, days-per-week values and the remaining metrics for these years are in %s.'
  % (hrs[2019], hrs[2021], 'below' if hrs[2021] < hrs[2010] else 'above', hrs[2010], hrs[2022], hrs[2023], hrs[2024],
     100 * ex(2019, '35_64', 'share_exposed_commuter').value, 100 * ex(2021, '35_64', 'share_exposed_commuter').value, 100 * ex(2024, '35_64', 'share_exposed_commuter').value, link('exposure_distributions.csv')))
w('')
w('### Scenario definition')
w('')
w('For target year 2024 and a kept distribution of year *y* (2010 or 2019), in county group *g* and mortality age band *b*:')
w('')
w('AD_gb(y) = sum over counties c in g of [ 1 - E_y[RR] / E_2024[RR] ] x (rate_cb,2019 / 100,000) x N_cb,2024.')
w('')
w('Counterfactual (i) keeps the 2010 distribution and counterfactual (ii) keeps the 2019 distribution. A negative AD(2019) means fewer modelled deaths than if the 2019 commute distribution had persisted. '
  'The share of the 2010-2019 burden reversed by the 2019-2024 change is')
w('')
w('R_gb = -AD_gb(2019) / [ AD_gb(2010) - AD_gb(2019) ].')
w('')
w('The denominator is the burden of the 2010-to-2019 change evaluated on the same 2024 population and 2019 rates, so R is not moved by population growth or ageing between 2019 and 2024. '
  'A second version divides the same numerator by the 2010-2019 burden as reported for 2019 in section 6 (2019 population). For the 10-year bands, which have no deaths, R is the pooled-person ratio (E_2019[RR] - E_2024[RR]) / (E_2019[RR] - E_2010[RR]). '
  'Uncertainty is propagated exactly as in section 5, with the same seed and the same %s draws as the main run; the 2019 results recomputed inside this run differ from %s by at most %.1e deaths.'
  % ('{:,}'.format(PM['K']), link('burden_results.csv'), float(vc('P4_reproduces_main_2019_results').value)))
w('')
w('### Scenario results')
w('')
w('Table 10. SCENARIO. Attributable cardiovascular deaths per year for 2024 commuting and population with 2019 mortality rates, all 14 counties (median and 95% UI; *f* uniform on 0 to 1 for scenario A).')
w('')
rows = []
for s_ in ['A', 'E_both', 'E_men']:
    for b in ['35_64', '65plus', '35plus']:
        r10, r19 = ps(s_, K10, b), ps(s_, K19, b)
        nd_ = 2 if s_ == 'A' else 1
        rows.append([SC[s_], BL[b], ad(r10, nd_), ad(r19, nd_), '%.3f' % (1 - r19.attr_deaths_prob_gt0), 'yes' if r19.ui_spans_zero else 'no', '{:,.0f}'.format(r10.baseline_deaths_2024pop_2019rates_median)])
w(table(['Scenario', 'Age', '(i) 2010 distribution kept', '(ii) 2019 distribution kept', 'Share of draws at or below zero, (ii)', 'UI spans zero, (ii)', 'Baseline deaths (2024 population x 2019 rates)'], rows))
w('')
w('Table 11. SCENARIO. Share of the 2010-2019 attributable burden reversed by the 2019-2024 change, all 14 counties (median and 95% UI, in %).')
w('')
rows = []
for s_ in ['A', 'E_both', 'E_men']:
    for b in ['35_64', '65plus', '35plus']:
        r19 = ps(s_, K19, b)
        rows.append([SC[s_], BL[b], rv(r19), rv(r19, 'reversal_vs_reported_2019_burden'), 'deaths, county-weighted'])
for b in ['35_44', '45_54', '55_64']:
    rows.append([SC['A'], BL[b], rv(ps('A', K19, b)), 'not available (no deaths)', 'pooled persons'])
w(table(['Scenario', 'Age', 'R on the 2024 population', 'R against the 2019 burden as reported', 'Basis'], rows))
w('')
w('Table 12. SCENARIO. Ages 35+, by county group (median and 95% UI).')
w('')
rows = []
for s_ in ['A', 'E_both']:
    for g in ['core9', 'adjacent5', 'all14']:
        nd_ = 2 if s_ == 'A' else 1
        rows.append([SC[s_], GL[g], ad(ps(s_, K10, group=g), nd_), ad(ps(s_, K19, group=g), nd_), rv(ps(s_, K19, group=g))])
w(table(['Scenario', 'County group', '(i) 2010 distribution kept', '(ii) 2019 distribution kept', 'Reversed share R'], rows))
w('')
pA10, pA19, pE10, pE19, pM19 = ps('A', K10), ps('A', K19), ps('E_both', K10), ps('E_both', K19), ps('E_men', K19)
w('Reading Tables 10 to 12:')
w('')
w('- **Scenario A, ages 35+.** With the 2010 distribution kept, the 2024 scenario gives %s deaths per year, against %s for 2019 in section 6. With the 2019 distribution kept it gives %s, and the interval %s. '
  'On the same population, %s of the burden of the 2010-2019 lengthening is reversed; by age band the share is %s at 35-64 and %s at 65+.'
  % (ad(pA10, 2), ad(hA, 2), ad(pA19, 2), span(pA19), rv(pA19), rv(ps('A', K19, '35_64')), rv(ps('A', K19, '65plus'))))
w('- **Scenario E.** With the 2019 distribution kept the scenario gives %s deaths per year for both sexes (interval %s) and %s for men only (interval %s); the reversed share is %s and %s, with wide intervals because the hazard ratios are imprecise.'
  % (ad(pE19, 0), span(pE19), ad(pM19, 0), span(pM19), rv(pE19), rv(pM19)))
w('- For scenario A the reversed share depends almost only on the change in mean car-commute hours, because the unknown slope and net-sitting fraction scale numerator and denominator alike; its interval therefore reflects survey sampling error and county weighting rather than the uncertainty of the risk function.')
w('- Checks specific to this scenario (rows P1 to P5 of %s): keeping the 2024 distribution gives zero (max %.1e); the sign of (ii) agrees with the sign of the 2019-2024 change in mean car-commute hours per resident in %s comparisons for scenario A (county group by age band; deaths and pooled fractions), %s for E both sexes, %s for E men, and in %s county-by-mortality-age-band strata for scenario A; a second seed moves median deaths by at most %.1f%%, interval bounds by at most %.1f%% of the interval width and the median reversed share by at most %.4f.'
  % (link('burden_validity_checks.csv'), float(vc('P1_post2020_counterfactual_equals_observed').value), *[str(vc(c_).detail).split(' agree')[0] for c_ in ('P2_sign_agrees_group_strata_A', 'P2_sign_agrees_group_strata_E_both', 'P2_sign_agrees_group_strata_E_men', 'P2_sign_agrees_county_strata_A')], 100 * float(vc('P3a_post2020_seed_median').value), 100 * float(vc('P3b_post2020_seed_bounds').value),
     float(vc('P3c_post2020_seed_reversal').value)))
w('')
w('## 8. Illustrative scenario: anger while driving as a trigger (not part of any total)')
w('')
aM = row('anger_mi', 'cf1_2010_distribution', T=AN); aS = row('anger_stroke', 'cf1_2010_distribution', T=AN); aM3 = row('anger_mi', 'cf3_no_car', T=AN); aS3 = row('anger_stroke', 'cf3_no_car', T=AN)
lam = AS[AS.parameter.str.contains('outbursts per hour')].iloc[0]
w('**This scenario is illustrative only and is excluded from every total above.** No study has measured road rage or driving anger against a cardiovascular event, and no dataset supplies the frequency of anger outbursts while driving. '
  'The scenario combines primary-study trigger estimates (myocardial infarction within 2 hours of an anger outburst, row DR047; acute stroke within 1 hour of anger or emotional upset, row DR050, published with a 99%% interval; the press-release row DR054 is not used) with an assumed rate of driving-anger outbursts per hour of car commuting, drawn log-uniformly from %s (central %.4f). '
  'For person *i*, RR_i = 1 + (RR_trigger - 1) x lambda x *h_i* x W / 168, where W is the hazard window in hours. It further assumes that a trigger estimate for event onset applies equally to coronary heart disease deaths and stroke deaths. Survey data on road-rage behaviour cited in the literature review describe how many drivers report such behaviour in a year, not outbursts per hour of driving, and were not used to set the rate.'
  % (lam.range_or_ci, float(lam.value)))
w('')
w('Table 13. Illustrative anger-trigger scenario, ages 35+, all 14 counties, 2019 (median and 95% UI).')
w('')
rows = []
for s, lab in (('anger_mi', 'MI trigger applied to CHD deaths'), ('anger_stroke', 'Stroke trigger applied to stroke deaths')):
    for c in CF:
        r = row(s, c, T=AN)
        rows.append([lab, CF[c], ad(r, 2), af(r, 4), '%.0f' % r.baseline_deaths_median])
w(table(['Pathway', 'Counterfactual', 'Deaths per year', 'Fraction, %', 'Baseline deaths (CHD or stroke)'], rows))
w('')
w('Under these assumptions the pathway is very small: %s coronary deaths and %s stroke deaths per year for the 2010 to 2019 lengthening, and %s and %s under the no-car bound. The result is driven almost entirely by the assumed outburst rate and should not be cited as an estimate.' % (ad(aM, 2), ad(aS, 2), ad(aM3, 2), ad(aS3, 2)))
w('')
w('## 9. Sensitivity analyses')
w('')
w('Table 14. Attributable deaths per year, ages 35+, all 14 counties. Deterministic rows use central values (*d* = 4.5, *f* = 0.5, point relative risks); Monte Carlo rows give the median and 95% UI.')
w('')
order = [('base', 'Base (deterministic central)'), ('modes_all_seated_motorized', 'All seated motorised modes'), ('topcode_largest_uncensored_value', 'Top-code replaced by largest uncensored value'),
         ('topcode_180_min', 'Top-code replaced by 180 min'), ('days_per_week_3', 'Commute days per week = 3'), ('days_per_week_5', 'Commute days per week = 5'),
         ('daily_average_over_workdays_only', 'Daily sitting averaged over workdays only'), ('mortality_major_cvd_series_2019', 'Major cardiovascular disease rate series'),
         ('pooled_group_paf_times_group_deaths', 'Group-level pooled fraction x group deaths'), ('warren_boundary_ge10', 'E: top category >= 10 h/week (d = 4.5)'),
         ('warren_boundary_ge10_with_days_per_week_5', 'E: top category >= 10 h/week with d = 5'), ('warren_noncommute_car_2h', 'E: plus 2 h/week non-commute car time'),
         ('warren_noncommute_car_3.9h', 'E: plus 3.9 h/week non-commute car time')]
def sv(a, s, c):
    q = SX[(SX.analysis == a) & (SX.scenario == s) & (SX.counterfactual == c) & (SX.age_band == '35plus') & (SX.county_group == 'all14')]
    return '%.1f' % q.attributable_deaths.iloc[0] if len(q) else 'n/a'
rows = [[lab] + [sv(a, s, c) for s in ('A', 'E_both') for c in ('cf1_2010_distribution', 'cf3_no_car')] for a, lab in order]
def mv(a, s, c):
    q = SX[(SX.analysis == a) & (SX.scenario == s) & (SX.counterfactual == c) & (SX.age_band == '35plus') & (SX.county_group == 'all14')]
    return '%.1f (%.1f to %.1f)' % (q.attributable_deaths.iloc[0], q.lo95.iloc[0], q.hi95.iloc[0]) if len(q) else 'n/a'
for a, lab in [('mc_base', 'Monte Carlo base'), ('mc_days_uniform_3_to_5', 'Monte Carlo, d uniform 3 to 5'), ('mc_se_from_wider_ci_halfwidth', 'Monte Carlo, SE from the wider CI half-width'),
               ('mc_warren_rho_0', 'Monte Carlo, E hazard ratios uncorrelated'), ('mc_warren_rho_1', 'Monte Carlo, E hazard ratios perfectly correlated')]:
    rows.append([lab] + [mv(a, s, c) for s in ('A', 'E_both') for c in ('cf1_2010_distribution', 'cf3_no_car')])
w(table(['Analysis', 'A, counterfactual 1', 'A, no car', 'E both sexes, counterfactual 1', 'E both sexes, no car'], rows))
w('')
b64 = sens('base', 'A', 'cf1_2010_distribution', '35_64')
w('- **Within-band age gradient (35-64).** Deaths in this band are concentrated at its older end, where car commuting is less common. Applying the pooled fraction of 55-64-year-olds to all 35-64 deaths gives %.2f deaths per year for scenario A, counterfactual 1, and applying that of 35-44-year-olds gives %.2f, against %.2f with the pooled 35-64 fraction and %.2f in the base calculation (county-specific fractions); for scenario E the same four values are %.1f, %.1f, %.1f and %.1f.'
  % (sens('deaths_35_64_using_pooled_paf_of_55_64', 'A', 'cf1_2010_distribution', '35_64'), sens('deaths_35_64_using_pooled_paf_of_35_44', 'A', 'cf1_2010_distribution', '35_64'), sens('pooled_group_paf_times_group_deaths', 'A', 'cf1_2010_distribution', '35_64'), b64,
     sens('deaths_35_64_using_pooled_paf_of_55_64', 'E_both', 'cf1_2010_distribution', '35_64'), sens('deaths_35_64_using_pooled_paf_of_35_44', 'E_both', 'cf1_2010_distribution', '35_64'),
     sens('pooled_group_paf_times_group_deaths', 'E_both', 'cf1_2010_distribution', '35_64'), sens('base', 'E_both', 'cf1_2010_distribution', '35_64')))
w('- **Scenario E is sensitive to choices the data cannot settle.** Adding non-commute car time moves commuters into higher categories and raises the estimate, and at five commute days a week the many reports of exactly 60 minutes sit on the 10-hour boundary. '
  'The assumed correlation between the three hazard ratios changes the interval: for counterfactual 1 it is %s with uncorrelated hazard ratios, %s at the assumed 0.5 and %s with perfect correlation, so whether the interval spans zero depends on an assumption.'
  % (mv('mc_warren_rho_0', 'E_both', 'cf1_2010_distribution'), mv('mc_base', 'E_both', 'cf1_2010_distribution'), mv('mc_warren_rho_1', 'E_both', 'cf1_2010_distribution')))
mxd = max(abs(sens(a, 'A', c) - sens('base', 'A', c)) for a in ('topcode_largest_uncensored_value', 'topcode_180_min', 'mortality_major_cvd_series_2019', 'pooled_group_paf_times_group_deaths')
          for c in ('cf1_2010_distribution', 'cf3_no_car'))
w('- The top-code treatment, the mortality series and the level at which fractions are pooled change the scenario A results in Table 14 by at most %.2f deaths per year.' % mxd)
w('')
w('## 10. Validity checks')
w('')
w('All %d checks passed (%d failed). Full detail is in %s.' % (int(VC.passed.sum()), int((~VC.passed).sum()), link('burden_validity_checks.csv')))
w('')
def fmtv(v):
    try: return '%.3g' % float(v)
    except Exception: return str(v)
w(table(['Check', 'What was tested', 'Value', 'Tolerance', 'Passed'], [[r.check_id, r.description, fmtv(r.value), r.tolerance, 'yes' if r.passed else 'NO'] for r in VC.itertuples()]))
w('')
w('## 11. Limitations')
w('')
c = EM['within_band_composition_all14']
w('This is a modelling exercise on observational, cross-sectional survey data; it reports associations implied by borrowed relative risks and cannot show that commuting caused any death. '
  'The central scenarios transfer a generic total-sitting dose-response to car-commute time, which assumes car sitting is exchangeable with other sitting; the only driving-specific cardiovascular mortality estimate comes from one cohort of US men with exposure measured once in 1982, and two other cohorts found no mortality association with driving or transport sitting. '
  'The fraction of commute time that is net additional sitting has no direct estimate and one cohort found long drivers slightly less likely to report high total sitting, so *f* was treated as unknown between 0 and 1 and dominates the uncertainty of scenarios A to D. '
  'Commute days per week are not recorded in the ACS and were assumed. Individual total sitting and physical activity are unknown, so the sitting slope could not be restricted to inactive commuters even though activity strongly modifies the association in the source literature. '
  'The same relative risk was applied at every age. Mortality rates exist only for 35-64 and 65+, are model-smoothed and age-standardised within band, and were multiplied by survey population counts, so "deaths" are rate-equivalent estimates rather than counts from death certificates. '
  'Within each band, commuters are younger than the people who die: in 2019, ages 65-69 held %.0f%% of the 65+ population but %.0f%% of its car-commute hours, and ages 75 and over held %.0f%% of the population but %.0f%% of the hours, so applying the band-wide 65+ death rate to commuters probably overstates attributable deaths at 65+ by an amount that cannot be quantified without finer mortality data; the same issue in the 35-64 band was bounded in section 9. '
  'Working commuters are also likely to be healthier than non-working residents of the same age, which works in the same direction. '
  'Burden was not assessed under age 35. The 2010 baseline followed a recession, so counterfactual 1 mixes longer commutes with higher employment; counterfactual 1b separates them. '
  'Travel time is top-coded with a threshold that changed between 2010 and 2019, is self-reported with heaping at round values, and is door-to-door rather than in-vehicle. San Benito County has no person-level data and is excluded. '
  'The 2021-2024 figures describe commuters selected differently after the rise in working from home, and no mortality data exist for those years; the post-2020 scenario in section 7 applies 2019 mortality rates to 2024 as an assumption and is not an estimate of deaths that occurred. The anger-trigger scenario rests on an assumed outburst frequency and is illustrative only. '
  'Several further choices are assumptions rather than estimates: the correlation between the three driving-specific hazard ratios, the category boundaries, the treatment of the mortality-rate interval as a 95%% interval, and independence of rate uncertainty across counties.'
  % (100 * c['2019|65plus|age_65_69']['share_of_band_population'], 100 * c['2019|65plus|age_65_69']['share_of_band_car_commute_hours'],
     100 * c['2019|65plus|age_75_plus']['share_of_band_population'], 100 * c['2019|65plus|age_75_plus']['share_of_band_car_commute_hours']))
w('')
w('## 12. Files')
w('')
files = [('exposure_distributions.csv', 'weighted exposure distributions by year, county group, age band, mode definition and days per week, with replicate-weight SEs'),
         ('burden_results.csv', 'attributable fraction and deaths per year by age band, county group, scenario, counterfactual and net-sitting fraction, with 95% UIs'),
         ('burden_assumptions.csv', 'every parameter and assumption with value, range, source row id and abstract_only flag'),
         ('burden_validity_checks.csv', 'validity checks'), ('burden_sensitivity.csv', 'sensitivity analyses'),
         ('burden_anger_illustrative.csv', 'illustrative anger-trigger scenario (excluded from totals)'),
         ('burden_post2020_scenario.csv', 'SCENARIO: 2024 commuting and population with 2019 mortality rates, 2010-kept and 2019-kept counterfactuals, reversed share (not observed mortality)'),
         ('burden_draws_headline.csv', 'Monte Carlo draws of attributable deaths, ages 35+, all 14 counties, for plotting'),
         ('exposure_reconciliation.csv', 'population reconciliation against pums_county_year_age.parquet'),
         ('burden_lib.py', 'data loading and helpers'), ('burden_model.py', 'comparative risk assessment engine'), ('01_exposure.py', 'step 1'),
         ('02_burden_mc.py', 'steps 2 and 3'), ('03_validity_sensitivity.py', 'validity checks and sensitivity analyses'), ('05_post2020_scenario.py', 'post-2020 scenario and its validity checks'),
         ('04_write_report.py', 'writes this document from the result files')]
for fn, d in files:
    w('- %s: %s' % (link(fn), d))
w('')
w('The scripts read input locations from `burden/paths.json` (keys `pums`, `pcya`, `mort`, `dr` pointing to pums_commuters.parquet, pums_county_year_age.parquet, mortality_long.parquet and dose_response_parameters.csv) and are run from the workspace root in the order 01, 02, 03, 05, 04.')
open('methods_results_burden.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('written', len('\n'.join(L)))
