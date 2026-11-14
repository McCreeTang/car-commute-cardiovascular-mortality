
"""Shared helpers for the commute-sitting burden model.
Paths to the input artifacts are read from burden/paths.json (keys: pums, pcya, mort, dr)."""
import json, os, re
import numpy as np, pandas as pd
import pyarrow.dataset as ds

HERE = os.path.dirname(os.path.abspath(__file__))
PATHS = json.load(open(os.path.join(HERE, 'paths.json')))
YEARS = [2010, 2019, 2024]                     # years used by the burden engine
EXPOSURE_YEARS = [2010, 2019, 2021, 2022, 2023, 2024]   # exposure tables only; no 2020 ACS 1-year PUMS file exists
REPCOLS = ['pwgtp%d' % i for i in range(1, 81)]
WCOLS = ['pwgtp'] + REPCOLS
SDR = 4.0 / 80.0                       # ACS successive-difference replication factor
MODESETS = {'car': ['car_alone', 'carpool'],
            'seated_motorized': ['car_alone', 'carpool', 'taxi', 'motorcycle', 'bus', 'rail', 'ferry']}
FINE_BANDS = ['16_34', '35_44', '45_54', '55_64', '65plus']
MORT_BANDS = {'35_64': ['35_44', '45_54', '55_64'], '65plus': ['65plus']}
GROUPS = ['core9', 'adjacent5', 'all14']


def age_band(a):
    return pd.cut(a, [15, 34, 44, 54, 64, 200], labels=FINE_BANDS).astype(str)


def load_pums(years=YEARS):
    """Persons 16+ in the 14 counties with person-level data (San Benito/Monterey mixed PUMA excluded)."""
    cols = ['year', 'county_fips', 'county_name', 'core9', 'puma_mixed_outside', 'agep', 'sex', 'jwmnp',
            'mode_cat', 'commuter', 'wfh', 'worker_at_work', 'wk_raw', 'wk_var'] + WCOLS
    t = ds.dataset(PATHS['pums']).to_table(columns=cols, filter=ds.field('year').isin(list(years)))
    df = t.to_pandas()
    n_all = len(df)
    excl_by_year = {int(y): int(n) for y, n in df[df.puma_mixed_outside].groupby('year').size().items()}
    df = df[~df.puma_mixed_outside].reset_index(drop=True)
    df.attrs['n_excluded_mixed'] = n_all - len(df)
    df.attrs['n_excluded_mixed_by_year'] = excl_by_year
    df['band'] = age_band(df.agep)
    df['group'] = np.where(df.core9, 'core9', 'adjacent5')
    df['jw'] = df.jwmnp.astype('float64')            # NaN for non-commuters
    # top-code: the single maximum value of each year is the Census replacement value for all
    # travel times above that year's threshold
    df['topcoded'] = False
    info = {}
    for y, g in df.groupby('year'):
        vmax = g.jw.max()
        nxt = g.jw[g.jw < vmax].max()
        df.loc[(df.year == y) & (df.jw == vmax), 'topcoded'] = True
        info[int(y)] = {'topcode_value': float(vmax), 'max_uncensored_value': float(nxt)}
    df.attrs['topcode'] = info
    return df


def hours_per_commute_day(df, modeset='car', topcode='as_published', cap_min=None):
    """Round-trip in-vehicle hours on a commuting day = 2 x one-way minutes / 60 for the chosen modes; 0 otherwise.
    topcode: 'as_published' | 'floor' (largest uncensored value of the year) | 'min180'."""
    jw = df.jw.to_numpy().copy()
    if topcode != 'as_published':
        tc = df.topcoded.to_numpy()
        if topcode == 'floor':
            for y, v in df.attrs['topcode'].items():
                jw[tc & (df.year.to_numpy() == y)] = v['max_uncensored_value']
        elif topcode == 'min180':
            jw[tc] = 180.0
        else:
            raise ValueError(topcode)
    incar = df.mode_cat.isin(MODESETS[modeset]).to_numpy() & np.isfinite(jw)
    a = np.where(incar, jw, 0.0)
    if cap_min is not None:
        a = np.minimum(a, cap_min)
    return 2.0 * a / 60.0


def sdr_se(theta0, theta_rep):
    """Replicate-weight standard error; theta_rep has the 80 replicates on its last axis."""
    return np.sqrt(SDR * ((theta_rep - np.expand_dims(theta0, -1)) ** 2).sum(-1))


def lognormal_se(lo, hi, level=0.95):
    from scipy.stats import norm
    z = norm.ppf(0.5 + level / 2.0)
    return (np.log(hi) - np.log(lo)) / (2.0 * z)
