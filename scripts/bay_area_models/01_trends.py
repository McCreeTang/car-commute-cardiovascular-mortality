"""01_trends.py -- Step 1: housing and commute trends with replicate-weight uncertainty.
Inputs: handoff/input_paths.json (resolved artifact paths: pums, panel, pcya).
Outputs: trends_table.csv, trends_levels.csv, trends_heterogeneity_tests.csv
"""
import json, numpy as np, pandas as pd, pyarrow.parquet as pq
from scipy import stats
P = json.load(open('handoff/input_paths.json'))
REPS = ['pwgtp'] + [f'pwgtp{i}' for i in range(1, 81)]
cols = ['year','county_fips','county_name','core9','puma_mixed_outside','agep','jwmnp','mode_cat','worker_at_work','wfh','commuter'] + REPS
YEARS = [2010, 2019, 2021, 2024]
BANDS = {'16plus':(16,200),'16_34':(16,34),'35_44':(35,44),'45_54':(45,54),'55_64':(55,64),'65plus':(65,200),
         '16_24':(16,24),'25_34':(25,34),'35_64':(35,64)}
MEAS = ['mean_commute_min','share_commute_45plus','share_commute_60plus','share_commute_90plus','share_drive_alone_workers','share_wfh_workers']
df = pq.read_table(P['pums'], columns=cols, filters=[('year','in',YEARS)]).to_pandas()
df = df[~df['puma_mixed_outside']].copy()
names = df.drop_duplicates('county_fips').set_index('county_fips')['county_name'].to_dict()
core = df.drop_duplicates('county_fips').set_index('county_fips')['core9'].astype(bool).to_dict()
est = {}   # (year, geo, band, measure) -> array[81]
nrec = {}
for y in YEARS:
    d = df[df.year == y]
    W = d[REPS].to_numpy(dtype='float64')
    com = d['commuter'].to_numpy(bool); wk = d['worker_at_work'].to_numpy(bool)
    tt = d['jwmnp'].to_numpy(dtype='float64'); tt0 = np.where(com, np.nan_to_num(tt), 0.0)
    ind = {'com': com.astype(float), 'tt': tt0,
           'c45': (com & (tt >= 45)).astype(float), 'c60': (com & (tt >= 60)).astype(float), 'c90': (com & (tt >= 90)).astype(float),
           'wk': wk.astype(float), 'da': (wk & (d['mode_cat'].to_numpy() == 'car_alone')).astype(float),
           'wfh': (wk & d['wfh'].to_numpy(bool)).astype(float)}
    age = d['agep'].to_numpy(); cf = d['county_fips'].to_numpy(); c9 = d['core9'].to_numpy(bool)
    geos = {c: cf == c for c in sorted(names)}
    geos.update({'CORE9': c9, 'EXT5': ~c9, 'ALL14': np.ones(len(d), bool)})
    for g, gm in geos.items():
        for b, (lo, hi) in BANDS.items():
            m = gm & (age >= lo) & (age <= hi)
            Wm = W[m]
            S = {k: Wm.T @ v[m] for k, v in ind.items()}
            est[(y,g,b,'mean_commute_min')] = S['tt'] / S['com']
            est[(y,g,b,'share_commute_45plus')] = S['c45'] / S['com']
            est[(y,g,b,'share_commute_60plus')] = S['c60'] / S['com']
            est[(y,g,b,'share_commute_90plus')] = S['c90'] / S['com']
            est[(y,g,b,'share_drive_alone_workers')] = S['da'] / S['wk']
            est[(y,g,b,'share_wfh_workers')] = S['wfh'] / S['wk']
            nrec[(y,g,b)] = (int(com[m].sum()), int(wk[m].sum()))
def var(a): return 4.0/80.0 * np.sum((a[1:] - a[0])**2)
def cov(A):  # A: k x 81
    D = A[:, 1:] - A[:, [0]]
    return 4.0/80.0 * D @ D.T
def gname(g): return names.get(g, g)
def gcore(g): return {'CORE9': True, 'EXT5': False, 'ALL14': None}.get(g, core.get(g))
# ---- levels
rows = []
for (y,g,b,m), a in est.items():
    rows.append(dict(year=y, geo=g, geo_name=gname(g), core9=gcore(g), is_region_total=g in ('CORE9','EXT5','ALL14'), age_band=b, measure=m,
                     estimate=a[0], se=np.sqrt(var(a)), n_commuter_records=nrec[(y,g,b)][0], n_worker_records=nrec[(y,g,b)][1]))
lev = pd.DataFrame(rows); lev.to_csv('trends_levels.csv', index=False)
# ---- changes
rows = []
geos_all = sorted(names) + ['CORE9','EXT5','ALL14']
for (y0, y1, lab) in [(2010,2019,'2010-2019 (primary)'), (2019,2024,'2019-2024 (descriptive; post-2020 commuters differently selected)'), (2019,2021,'2019-2021 (descriptive)'), (2010,2024,'2010-2024 (descriptive)')]:
    for g in geos_all:
        for b in BANDS:
            for m in MEAS:
                a0, a1 = est[(y0,g,b,m)], est[(y1,g,b,m)]
                ch = a1[0]-a0[0]; se = np.sqrt(var(a0)+var(a1)); zval = ch/se
                unit = 'minutes' if m == 'mean_commute_min' else 'proportion (0-1)'
                rows.append(dict(source='ACS 1-year PUMS', period=lab, year_start=y0, year_end=y1, geo=g, geo_name=gname(g), core9=gcore(g),
                                 is_region_total=g in ('CORE9','EXT5','ALL14'), age_band=b, measure=m, unit=unit,
                                 value_start=a0[0], se_start=np.sqrt(var(a0)), value_end=a1[0], se_end=np.sqrt(var(a1)),
                                 change=ch, se_change=se, ci95_lo=ch-1.96*se, ci95_hi=ch+1.96*se, z=zval, p_value=2*stats.norm.sf(abs(zval)),
                                 pct_change=np.nan, n_commuter_records_start=nrec[(y0,g,b)][0], n_commuter_records_end=nrec[(y1,g,b)][0],
                                 note='replicate-weight SE; years treated as independent samples'))
# ---- Zillow (nominal)
pan = pd.read_parquet(P['panel'])
zp = pan.pivot(index='county_fips', columns='year', values='zhvi_mean')
meta = pan.drop_duplicates('county_fips').set_index('county_fips')[['county_name','core9']]
def zrow(g, gn, c9, tot, v0, v1, y0, y1, lab, note):
    return dict(source='Zillow ZHVI', period=lab, year_start=y0, year_end=y1, geo=g, geo_name=gn, core9=c9, is_region_total=tot, age_band='not applicable',
                measure='zhvi_mean_nominal_usd', unit='nominal US dollars', value_start=v0, se_start=np.nan, value_end=v1, se_end=np.nan, change=v1-v0,
                se_change=np.nan, ci95_lo=np.nan, ci95_hi=np.nan, z=np.nan, p_value=np.nan, pct_change=100*(v1/v0-1),
                n_commuter_records_start=np.nan, n_commuter_records_end=np.nan, note=note)
for (y0,y1,lab) in [(2010,2019,'2010-2019 (primary)'),(2019,2024,'2019-2024 (descriptive; post-2020 commuters differently selected)'),(2019,2021,'2019-2021 (descriptive)'),(2010,2024,'2010-2024 (descriptive)')]:
    for c in zp.index:
        rows.append(zrow(c, meta.loc[c,'county_name'], bool(meta.loc[c,'core9']), False, zp.loc[c,y0], zp.loc[c,y1], y0, y1, lab,
                         'nominal dollars; smoothed index; no published uncertainty' + ('; county has no PUMS commute data' if c not in names else '')))
    for g, sel, c9 in [('CORE9', meta.core9.astype(bool), True), ('EXT6', ~meta.core9.astype(bool), False), ('EXT5', (~meta.core9.astype(bool)) & meta.index.isin(list(names)), False),
                       ('ALL15', meta.core9.notna(), None), ('ALL14', meta.index.isin(list(names)), None)]:
        idx = meta.index[np.asarray(sel)]
        r = zrow(g, g, c9, True, zp.loc[idx,y0].mean(), zp.loc[idx,y1].mean(), y0, y1, lab,
                 f'unweighted mean of {len(idx)} county index values; pct_change is the mean of county percent changes; nominal dollars')
        r['pct_change'] = float((100*(zp.loc[idx,y1]/zp.loc[idx,y0]-1)).mean())
        rows.append(r)
tr = pd.DataFrame(rows); tr.to_csv('trends_table.csv', index=False)
# ---- heterogeneity tests 2010->2019 (and 2019->2024 for description)
AB = ['16_34','35_44','45_54','55_64','65plus']
C = np.zeros((4,5)); C[:,0] = -1; C[np.arange(4), np.arange(1,5)] = 1
rows = []
for (y0,y1) in [(2010,2019),(2019,2024)]:
    for m in MEAS:
        for g in ['ALL14','CORE9','EXT5']:
            A0 = np.vstack([est[(y0,g,b,m)] for b in AB]); A1 = np.vstack([est[(y1,g,b,m)] for b in AB])
            dvec = A1[:,0]-A0[:,0]; V = cov(A0)+cov(A1)
            cd = C @ dvec; Wst = float(cd @ np.linalg.solve(C @ V @ C.T, cd))
            rows.append(dict(test='age-band heterogeneity of change (Wald, 4 df)', year_start=y0, year_end=y1, measure=m, geo=g, statistic=Wst, df=4,
                             p_value=stats.chi2.sf(Wst,4), estimate=np.nan, se=np.nan,
                             detail='; '.join(f'{b}: {dv:.4f} (SE {np.sqrt(V[i,i]):.4f})' for i,(b,dv) in enumerate(zip(AB,dvec)))))
        for b in ['16plus'] + AB:
            A0 = np.vstack([est[(y0,'CORE9',b,m)], est[(y0,'EXT5',b,m)]]); A1 = np.vstack([est[(y1,'CORE9',b,m)], est[(y1,'EXT5',b,m)]])
            c = np.array([1.,-1.]); dd = c @ (A1[:,0]-A0[:,0]); se = np.sqrt(c @ (cov(A0)+cov(A1)) @ c)
            rows.append(dict(test=f'core9 minus adjacent(EXT5) difference in change, age band {b} (z)', year_start=y0, year_end=y1, measure=m, geo='CORE9-EXT5',
                             statistic=dd/se, df=np.nan, p_value=2*stats.norm.sf(abs(dd/se)), estimate=dd, se=se,
                             detail=f'core9 change {A1[0,0]-A0[0,0]:.4f}; adjacent change {A1[1,0]-A0[1,0]:.4f}'))
        # county heterogeneity: Wald that all 14 county changes are equal (13 df); counties are disjoint domains, covariance from replicates
        cs = sorted(names)
        A0 = np.vstack([est[(y0,c_,'16plus',m)] for c_ in cs]); A1 = np.vstack([est[(y1,c_,'16plus',m)] for c_ in cs])
        dvec = A1[:,0]-A0[:,0]; V = cov(A0)+cov(A1); Cc = np.zeros((13,14)); Cc[:,0] = -1; Cc[np.arange(13), np.arange(1,14)] = 1
        cd = Cc @ dvec; Wst = float(cd @ np.linalg.solve(Cc @ V @ Cc.T, cd))
        rows.append(dict(test='county heterogeneity of change, 16+ (Wald, 13 df)', year_start=y0, year_end=y1, measure=m, geo='14 counties', statistic=Wst, df=13,
                         p_value=stats.chi2.sf(Wst,13), estimate=np.nan, se=np.nan, detail=f'range of county changes {dvec.min():.4f} to {dvec.max():.4f}'))
het = pd.DataFrame(rows); het.to_csv('trends_heterogeneity_tests.csv', index=False)
# ---- cross-check against the delivered aggregate file
pc = pd.read_parquet(P['pcya'])
chk = lev.merge(pc.melt(id_vars=['year','county_fips','age_band'], value_vars=MEAS, var_name='measure', value_name='ref'),
                left_on=['year','geo','age_band','measure'], right_on=['year','county_fips','age_band','measure'], how='left')
chk2 = lev.merge(pc.melt(id_vars=['year','county_fips','age_band'], value_vars=[m+'_se' for m in MEAS], var_name='measure', value_name='ref_se').assign(measure=lambda x: x.measure.str[:-3]),
                 left_on=['year','geo','age_band','measure'], right_on=['year','county_fips','age_band','measure'], how='left')
json.dump(dict(cells_compared=int(len(chk)), cells_matched=int(chk.ref.notna().sum()), max_abs_diff_estimate=float((chk.estimate-chk.ref).abs().max()),
               max_abs_diff_se=float((chk2.se-chk2.ref_se).abs().max())), open('trends_crosscheck.json','w'), indent=1)
print('crosscheck rows matched', chk.ref.notna().sum(), 'of', len(chk), 'max abs diff est', (chk.estimate-chk.ref).abs().max(), 'max abs diff se', (chk2.se-chk2.ref_se).abs().max())
print(tr.shape, lev.shape, het.shape)
