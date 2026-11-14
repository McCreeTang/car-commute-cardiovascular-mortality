"""Acquire CDC county cardiovascular mortality by age group for ALL US counties (data.cdc.gov, source NVSS).

Dataset 7b9s-s8ck: Rates and Trends in Heart Disease and Stroke Mortality Among US Adults (35+) by County, Age Group,
Race/Ethnicity, and Sex - 2000-2019 (annual rows 1999-2019 plus trend rows; five topics; ages 35-64 and 65+ only).
Values are AGE-STANDARDIZED (within the age band), SPATIOTEMPORALLY SMOOTHED model rates per 100,000 with the published
confidence limits - not raw death counts.

Scope downloaded here: race = Overall (all races), sex = Overall, Men, Women; every county, topic, age group and period.
The race-specific rows (3.6 million rows) are not downloaded. The download is checked against a server-side count(*).

Output: raw/mortality_nat/cdc_7b9s-s8ck_race_overall.parquet, raw/mortality_nat/mortality_nat_download_log.csv
Usage: python acquire_cdc_mortality_national.py
"""
import io, os, time, datetime, requests, pandas as pd
from concurrent.futures import ThreadPoolExecutor

DID = "7b9s-s8ck"; URL = f"https://data.cdc.gov/resource/{DID}"; WHERE = "stratification2='Overall'"
RAW = "raw/mortality_nat"; PAGE = 50000

def page(off):
    for k in range(5):
        try:
            r = requests.get(URL + ".csv", params={"$where": WHERE, "$order": ":id", "$limit": PAGE, "$offset": off}, timeout=900)
            r.raise_for_status()
            return pd.read_csv(io.StringIO(r.text), dtype=str, keep_default_na=False)
        except Exception as ex:
            last = ex; time.sleep(5 * (k + 1))
    raise last

if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    n_server = int(requests.get(URL + ".json", params={"$select": "count(*) as n", "$where": WHERE}, timeout=600).json()[0]["n"])
    with ThreadPoolExecutor(4) as ex:
        parts = list(ex.map(page, range(0, n_server, PAGE)))
    df = pd.concat(parts, ignore_index=True)
    assert len(df) == n_server, f"downloaded {len(df)}, server count {n_server}"
    key = ["locationid", "year", "topic", "stratification1", "stratification2", "stratification3", "data_value_type"]
    assert not df.duplicated(key).any(), "duplicate strata: paging overlapped"
    df.to_parquet(os.path.join(RAW, f"cdc_{DID}_race_overall.parquet"), index=False)
    log = {"dataset_id": DID, "url": URL, "where": WHERE, "rows": len(df), "server_count": n_server, "counties": df.locationid.nunique(),
           "columns": ";".join(df.columns), "downloaded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    pd.DataFrame([log]).to_csv(os.path.join(RAW, "mortality_nat_download_log.csv"), index=False)
    print({k: v for k, v in log.items() if k != "columns"}, flush=True)
