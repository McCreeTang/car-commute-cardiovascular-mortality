
"""Step 1. Age-stratified distributions of weekly in-vehicle commute hours among ALL residents.
Run: python burden/01_exposure.py   (from the workspace root)
Outputs: exposure_distributions.csv, burden/exposure_reconciliation.csv, burden/exposure_meta.json"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from burden_lib import *

DAYS = [5.0, 4.5, 4.0, 3.0]            # assumed commute days per week (declared assumption; ACS has no such item)
ONEWAY_BINS = [(1, 14), (15, 29), (30, 44), (45, 59), (60, 89), (90, 1e9)]

df = load_pums(EXPOSURE_YEARS)
W = df[WCOLS].to_numpy(dtype='float64')
bands = {b: (df.band == b).to_numpy() for b in FINE_BANDS}
bands['35_64'] = np.isin(df.band, MORT_BANDS['35_64'])
groups = {'core9': df.core9.to_numpy(), 'adjacent5': ~df.core9.to_numpy(), 'all14': np.ones(len(df), bool)}


def wq(x, w, qs):
    """Weighted quantiles (lower inverse-CDF definition)."""
    o = np.argsort(x, kind='stable'); x = x[o]; cw = np.cumsum(w[o]); tot = cw[-1]
    return [x[min(np.searchsorted(cw, q * tot, 'left'), len(x) - 1)] for q in qs]


rows = []
def add(year, grp, band, modeset, d, metric, vec, n_unw, universe):
    vec = np.asarray(vec, float)
    rows.append(dict(year=year, county_group=grp, age_band=band, mode_def=modeset, days_per_week=d, metric=metric,
                     universe=universe, value=vec[0], se=float(sdr_se(vec[0], vec[1:])), n_unweighted=int(n_unw)))

for year in EXPOSURE_YEARS:
    my = (df.year == year).to_numpy()
    for gname, gm in groups.items():
        for bname, bm in bands.items():
            m = my & gm & bm
            Wm = W[m]; tot = Wm.sum(0); n = int(m.sum()); sub = df[m]
            add(year, gname, bname, 'na', np.nan, 'population', tot, n, 'all residents')
            add(year, gname, bname, 'na', np.nan, 'share_worker_at_work', Wm[sub.worker_at_work.to_numpy()].sum(0) / tot, n, 'all residents')
            add(year, gname, bname, 'na', np.nan, 'share_work_from_home', Wm[sub.wfh.to_numpy()].sum(0) / tot, n, 'all residents')
            for ms in MODESETS:
                a = hours_per_commute_day(sub, ms)           # hours per commuting day, 0 if not exposed
                # hours_per_commute_day reads attrs from the parent frame
                jw1 = a * 30.0                                # one-way minutes for exposed, 0 otherwise
                ex = a > 0; nex = int(ex.sum()); Wex = Wm[ex]; totex = Wex.sum(0)
                add(year, gname, bname, ms, np.nan, 'share_exposed_commuter', totex / tot, n, 'all residents')
                add(year, gname, bname, ms, np.nan, 'share_oneway_0_not_exposed', 1 - totex / tot, n, 'all residents')
                for lo, hi in ONEWAY_BINS:
                    k = (jw1 >= lo) & (jw1 <= hi)
                    lab = 'share_oneway_%d_%s_min' % (lo, 'plus' if hi > 1e6 else str(hi))
                    add(year, gname, bname, ms, np.nan, lab, Wm[k].sum(0) / tot, n, 'all residents')
                add(year, gname, bname, ms, np.nan, 'mean_oneway_min', (Wex * jw1[ex][:, None]).sum(0) / totex, nex, 'exposed commuters')
                tc = sub.topcoded.to_numpy() & ex
                add(year, gname, bname, ms, np.nan, 'share_topcoded_travel_time', Wm[tc].sum(0) / totex, nex, 'exposed commuters')
                sa = (Wm * a[:, None]).sum(0)
                for d in DAYS:
                    h = d * a
                    add(year, gname, bname, ms, d, 'mean_weekly_hours', d * sa / tot, n, 'all residents')
                    add(year, gname, bname, ms, d, 'mean_weekly_hours', d * sa / totex, nex, 'exposed commuters')
                    add(year, gname, bname, ms, d, 'share_weekly_hours_lt4', Wm[h < 4].sum(0) / tot, n, 'all residents')
                    add(year, gname, bname, ms, d, 'share_weekly_hours_4_to_lt7', Wm[(h >= 4) & (h < 7)].sum(0) / tot, n, 'all residents')
                    add(year, gname, bname, ms, d, 'share_weekly_hours_7_to_10', Wm[(h >= 7) & (h <= 10)].sum(0) / tot, n, 'all residents')
                    add(year, gname, bname, ms, d, 'share_weekly_hours_gt10', Wm[h > 10].sum(0) / tot, n, 'all residents')
                    qs = [0.5, 0.75, 0.9, 0.95]
                    Q = np.array([wq(h[ex], Wex[:, j], qs) for j in range(Wex.shape[1])])   # 81 x 4
                    for qi, q in enumerate(qs):
                        add(year, gname, bname, ms, d, 'p%d_weekly_hours' % int(q * 100), Q[:, qi], nex, 'exposed commuters')

out = pd.DataFrame(rows)
out['primary_period'] = out.year.isin([2010, 2019])
out['period'] = np.where(out.year.isin([2010, 2019]), 'primary (2010, 2019)', 'post-2020, descriptive only (2021-2024)')
out['note'] = np.where(out.year >= 2021, 'Post-2020 commuters are a differently selected group (work from home rose); descriptive only, excluded from all association analyses. ', '') + \
    'No 2020 row: the Census Bureau released no standard 2020 ACS 1-year PUMS file. Travel time is top-coded (replacement value and largest uncensored value by year are in exposure_meta.json).'
out.to_csv('exposure_distributions.csv', index=False)

# ---- reconciliation of population totals against pums_county_year_age.parquet
pc = pd.read_parquet(PATHS['pcya'])
pc = pc[pc.year.isin(EXPOSURE_YEARS)]
df['cf'] = df.county_fips
rec = []
for year in EXPOSURE_YEARS:
    for bname, bm in bands.items():
        if bname == '65plus' or bname in ('35_44', '45_54', '55_64', '16_34', '35_64'):
            for key, mask in list({c: (df.cf == c).to_numpy() for c in sorted(df.cf.unique())}.items()) + \
                             [('CORE9', groups['core9']), ('EXT5', groups['adjacent5']), ('ALL14', groups['all14'])]:
                m = (df.year == year).to_numpy() & bm & mask
                tot = W[m].sum(0)
                ref = pc[(pc.year == year) & (pc.county_fips == key) & (pc.age_band == bname)]
                rec.append(dict(year=year, unit=key, age_band=bname, pop_this_work=tot[0], pop_se_this_work=float(sdr_se(tot[0], tot[1:])),
                                pop_reference=float(ref['pop'].iloc[0]), pop_se_reference=float(ref.pop_se.iloc[0]),
                                n_this_work=int(m.sum()), n_reference=int(ref.n_persons.iloc[0])))
rec = pd.DataFrame(rec)
rec['abs_diff_pop'] = (rec.pop_this_work - rec.pop_reference).abs()
rec['abs_diff_se'] = (rec.pop_se_this_work - rec.pop_se_reference).abs()
rec.to_csv('burden/exposure_reconciliation.csv', index=False)

# weeks worked among car commuters, 2019 (WKWN = number of weeks) -> empirical support for the days-per-week range
meta = {'n_excluded_mixed_puma_records': int(df.attrs['n_excluded_mixed']), 'topcode': df.attrs['topcode'],
        'n_persons_used': {int(y): int((df.year == y).sum()) for y in EXPOSURE_YEARS},
        'exposure_years': EXPOSURE_YEARS, 'n_excluded_mixed_by_year': df.attrs['n_excluded_mixed_by_year']}
for y in (2019, 2024):
    s = df[(df.year == y) & df.mode_cat.isin(MODESETS['car'])]
    mw = float(np.average(s.wk_raw.astype(float), weights=s.pwgtp))
    meta['mean_weeks_worked_car_commuters_%d' % y] = mw
    meta['annualised_days_per_week_if_5_day_week_%d' % y] = 5 * mw / 52
# within-band age composition of car-commute hours (context for applying one band-wide mortality rate)
a_all = hours_per_commute_day(df, 'car')
comp = {}
for y in (2010, 2019):
    for lab, edges in (('65plus', [(65, 69), (70, 74), (75, 200)]), ('35_64', [(35, 44), (45, 54), (55, 64)])):
        m = (df.year == y).to_numpy() & (bands[lab])
        tot_h = (df.pwgtp.to_numpy()[m] * a_all[m]).sum(); tot_p = df.pwgtp.to_numpy()[m].sum()
        for lo, hi in edges:
            k = m & (df.agep >= lo).to_numpy() & (df.agep <= hi).to_numpy()
            comp['%d|%s|age_%d_%s' % (y, lab, lo, 'plus' if hi > 150 else hi)] = dict(
                share_of_band_car_commute_hours=float((df.pwgtp.to_numpy()[k] * a_all[k]).sum() / tot_h),
                share_of_band_population=float(df.pwgtp.to_numpy()[k].sum() / tot_p))
meta['within_band_composition_all14'] = comp
meta['reconciliation_max_abs_diff_pop'] = float(rec.abs_diff_pop.max())
meta['reconciliation_max_abs_diff_se'] = float(rec.abs_diff_se.max())
meta['reconciliation_rows'] = int(len(rec))
json.dump(meta, open('burden/exposure_meta.json', 'w'), indent=1)
print(json.dumps(meta, indent=1)); print(out.shape)
