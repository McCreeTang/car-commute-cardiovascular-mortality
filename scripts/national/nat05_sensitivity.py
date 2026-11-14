"""nat05_sensitivity.py -- sensitivity family C (26 tests) and family A multiplicity.
Follows national_prespecified_plan.md sections 8-9. Needs national_cross_section_models.csv, national_change_models.csv,
national_matched_contrast.csv from the earlier scripts.
"""
import numpy as np, pandas as pd
import nat_common as nc
from nat_common import CAR, TRANSIT, Fit, design, pct

d = nc.load_county()
x = nc.cross_section(d, 2019)
x14 = nc.cross_section(d, 2014)
for df in (x, x14):
    df['mean_tt_car_per10'] = df.mean_tt_car_mid / 10.0
    df['car_commuters_per_adult16_per10pt'] = df.car_commuters_per_adult16 * 10.0
    df['share_car_60plus_per10pt'] = df.share_car_commuters_60plus * 10.0
    df['car_hours_5day'] = df.car_min_per_day_per_adult16 * 5 / 60.0
    df['transit_hours_5day'] = df.transit_min_per_day_per_adult16 * 5 / 60.0

OUT = 'mort_cvd_35_64'
cs = pd.read_csv('national_cross_section_models.csv')
prim = cs[cs.primary].iloc[0]
rows = []

def run(spec, label, df, driving, others=(TRANSIT,), rung=3, extra=(), outcome=OUT, weighted=True, unit='per hour a week', in_family=True, report_terms=(), compare_same_units=None):
    df = df[df[outcome].notna()].reset_index(drop=True)
    X = design(df, [driving] + list(others), rung, extra=extra)
    w = df.pop_35_64.values.astype(float) if weighted else None
    f = Fit(np.log(df[outcome].values), X, w, df.state_abbr.values)
    co = f.coef(driving, df=f.G - 1)
    row = dict(spec=spec, label=label, n=f.n, n_states=f.G, exposure=driving, unit=unit, weighting='pop_weighted' if weighted else 'unweighted',
               b=co['b'], se_cluster=co['se'], pct=pct(co['b']), pct_lo=pct(co['lo']), pct_hi=pct(co['hi']), p_cluster=co['p'], in_family_C=in_family)
    if TRANSIT in f.names or 'transit_hours_wk_per_adult16_pub' in f.names or 'transit_hours_5day' in f.names:
        tn = [t for t in f.names if t.startswith('transit_hours')][0]
        ct = f.coef(tn, df=f.G - 1)
        row.update(transit_pct=pct(ct['b']), transit_pct_lo=pct(ct['lo']), transit_pct_hi=pct(ct['hi']), transit_p=ct['p'])
    for t in report_terms:
        c2 = f.coef(t, df=f.G - 1)
        row.update(other_term=t, other_pct=pct(c2['b']), other_pct_lo=pct(c2['lo']), other_pct_hi=pct(c2['hi']), other_p=c2['p'])
    if compare_same_units is not None:
        row.update(same_units_primary_measure_pct=compare_same_units)
    rows.append(row)
    return f

# ladder variants (taken from the cross-section file so the two tables agree exactly)
def from_cs(spec, label, model, weighting, sample='all', outcome=OUT):
    r = cs[(cs.outcome == outcome) & (cs['sample'] == sample) & (cs.model == model) & (cs.weighting == weighting) & (cs.term == 'car')].iloc[0]
    t = cs[(cs.outcome == outcome) & (cs['sample'] == sample) & (cs.model == model) & (cs.weighting == weighting) & (cs.term == 'transit')].iloc[0]
    rows.append(dict(spec=spec, label=label, n=int(r.n), n_states=int(r.n_states), exposure=CAR, unit='per hour a week', weighting=weighting, b=r.b, se_cluster=r.se_cluster,
                     pct=r.pct, pct_lo=r.pct_lo, pct_hi=r.pct_hi, p_cluster=r.p_cluster, in_family_C=True,
                     transit_pct=t.pct, transit_pct_lo=t.pct_lo, transit_pct_hi=t.pct_hi, transit_p=t.p_cluster))
for m in ('M0', 'M1', 'M2', 'M4'):
    from_cs(f'L-{m}-w', f'{m}, population-weighted', m, 'pop_weighted')
for m in ('M0', 'M1', 'M2', 'M3', 'M4'):
    from_cs(f'L-{m}-u', f'{m}, unweighted', m, 'unweighted')
from_cs('F-metro', 'M3, metropolitan counties only', 'M3', 'pop_weighted', sample='metro')

run('S1', 'Drive-alone hours in place of car hours', x, 'drivealone_hours_wk_per_adult16')
run('S2', 'Mean one-way car travel time (per 10 min), with car commuters per adult', x, 'mean_tt_car_per10', others=('car_commuters_per_adult16_per10pt', TRANSIT),
    unit='per 10 minutes one way', report_terms=('car_commuters_per_adult16_per10pt',))
run('S3', 'Share of car commuters at 60+ min (per 10 points), with car commuters per adult', x, 'share_car_60plus_per10pt', others=('car_commuters_per_adult16_per10pt', TRANSIT),
    unit='per 10 percentage points', report_terms=('car_commuters_per_adult16_per10pt',))
# S4: published aggregates; compare with the primary measure on the same units
xa = x[x.car_hours_wk_per_adult16_pub.notna()].reset_index(drop=True)
fa0 = Fit(np.log(xa[OUT].values), design(xa, [CAR, TRANSIT], 3), xa.pop_35_64.values.astype(float), xa.state_abbr.values)
run('S4a', 'Published car aggregate (units where published)', xa, 'car_hours_wk_per_adult16_pub', compare_same_units=pct(fa0.b[fa0.i(CAR)]))
xb = x[x.car_hours_wk_per_adult16_pub.notna() & x.transit_hours_wk_per_adult16_pub.notna()].reset_index(drop=True)
fb0 = Fit(np.log(xb[OUT].values), design(xb, [CAR, TRANSIT], 3), xb.pop_35_64.values.astype(float), xb.state_abbr.values)
run('S4b', 'Published car and transit aggregates (units where both published)', xb, 'car_hours_wk_per_adult16_pub', others=('transit_hours_wk_per_adult16_pub',),
    compare_same_units=pct(fb0.b[fb0.i(CAR)]))
run('S5', 'Excluding counties under 20,000 population', x[x.pop_total >= 20000], CAR)
run('S6', '2010-2014 cross-section', x14, CAR)
run('S7-men', 'Men, ages 35-64', x, CAR, outcome='mort_cvd_35_64_men')
run('S7-women', 'Women, ages 35-64', x, CAR, outcome='mort_cvd_35_64_women')
run('S8', 'Five commute days a week (rescaling; not a separate test)', x, 'car_hours_5day', others=('transit_hours_5day',), in_family=False)
for reg in ('Northeast', 'Midwest', 'South', 'West'):
    run(f'S9-{reg}', f'Leaving out the {reg}', x[x.census_region != reg], CAR)
run('S10', 'M3 + workers per adult 16+', x, CAR, extra=('workers_per_adult16',), report_terms=('workers_per_adult16',))
run('S11', 'Excluding the five New York City counties', x[~x.fips.isin(nc.NYC5)], CAR)
run('S12', 'Car hours without the transit term', x, CAR, others=())

s = pd.DataFrame(rows)
fam = s.in_family_C
assert fam.sum() == 26, fam.sum()
s['q_family_C'] = np.nan
s.loc[fam, 'q_family_C'] = nc.bh(s.loc[fam, 'p_cluster'].values)
s['primary_pct'] = prim.pct; s['primary_p'] = prim.p_cluster
s['sign_differs_from_primary'] = np.sign(s.b) != np.sign(prim.b)
s['significance_changes'] = (s.p_cluster < 0.05) != (prim.p_cluster < 0.05)
same = s.unit == 'per hour a week'
s['ratio_to_primary'] = np.where(same, s.b / prim.b, np.nan)
s['direction'] = np.where(s.p_cluster < 0.05, np.where(s.b > 0, 'positive, p<0.05', 'negative, p<0.05'), np.where(s.b > 0, 'positive, n.s.', 'negative, n.s.'))
s.to_csv('national_sensitivity.csv', index=False)

# family A
ch = pd.read_csv('national_change_models.csv'); mc = pd.read_csv('national_matched_contrast.csv')
t2 = ch[(ch.outcome == OUT) & (ch['sample'] == 'all') & (ch.weighting == 'pop_weighted') & (ch.term == 'change in car hours')].iloc[0]
t3 = mc[(mc.outcome == OUT) & mc.estimate_to_interpret].iloc[0]
A = pd.DataFrame([
    dict(test='T1 cross-section (M3, weighted)', n=int(prim.n), unit='per hour a week', pct=prim.pct, pct_lo=prim.pct_lo, pct_hi=prim.pct_hi, p=prim.p_cluster, mde_pct=prim.mde_pct),
    dict(test='T2 change 2006-2010 to 2015-2019 (weighted)', n=int(t2.n), unit='per hour a week', pct=t2.pct, pct_lo=t2.pct_lo, pct_hi=t2.pct_hi, p=t2.p_cluster, mde_pct=t2.mde_pct),
    dict(test=f'T3 matched high vs low ({t3.estimator})', n=int(t3.n_pairs), unit='high vs low driving', pct=t3.pct, pct_lo=t3.pct_lo, pct_hi=t3.pct_hi, p=t3.p_cluster, mde_pct=t3.mde_pct)])
A['q_bh_family_A'] = nc.bh(A.p.values); A['p_holm_family_A'] = nc.holm(A.p.values)
A.to_csv('national_family_A.csv', index=False)
print('done', len(s))
