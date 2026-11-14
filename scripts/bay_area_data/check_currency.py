"""Check how current each source is: what the latest published period is, and whether anything newer than the
acquired data exists. Writes ref/currency_check.json (read by run_qc.py). Nothing is downloaded beyond listings,
headers and catalog/metadata queries.

Note on www2.census.gov: the server can answer HTTP 200 with an HTML "Request Rejected" page, so existence of a
file is judged from directory listings and from the first bytes of the response, never from the status code alone.

Usage: python check_currency.py
"""
import re, json, time, datetime, requests, pandas as pd

W = "https://www2.census.gov/programs-surveys/acs/"
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
def ls(url):
    r = requests.get(url, timeout=120); ok = r.status_code == 200 and "Request Rejected" not in r.text[:300]
    return r.status_code, (sorted(set(h for h in re.findall(r'href="([^"?/][^"]*/?)"', r.text) if not h.startswith("http"))) if ok else [])
def classify(url):
    """'data' if the response starts like a data file, 'zip' for a zip, 'rejection page', or 'http <status>'."""
    with requests.get(url, stream=True, timeout=120) as r:
        head = r.raw.read(300, decode_content=True)
        if r.status_code != 200: return f"http {r.status_code}", None
        if b"Request Rejected" in head: return "rejection page (not a file)", None
        return ("zip" if head[:2] == b"PK" else "data" if head.startswith(b"GEO_ID") else "other"), r.headers.get("last-modified")
def get_json(url, params=None):
    for attempt in (1, 2):
        try:
            r = requests.get(url, params=params, timeout=180); r.raise_for_status(); return r.json()
        except requests.exceptions.RequestException as e:
            err = e
            if attempt == 1: time.sleep(30)
    raise err
def catalog(q):
    return get_json("https://data.cdc.gov/api/catalog/v1", {"q": q, "limit": 100, "only": "datasets", "search_context": "data.cdc.gov"})["results"]

def check_pums():
    st, ent = ls(W + "data/pums/"); years = sorted(int(e[:4]) for e in ent if re.fullmatch(r"\d{4}/", e)); out = {"listing_url": W + "data/pums/", "listing_status": st, "latest_year_directory": max(years), "checked_utc": now(), "files": {}}
    for y in (max(years), 2025, 2026):
        d_st, _ = ls(f"{W}data/pums/{y}/")
        for span in ("1-Year", "5-Year"):
            kind, mod = classify(f"{W}data/pums/{y}/{span}/csv_pca.zip"); out["files"][f"{y} {span}"] = {"year_directory_status": d_st, "california_person_file": kind, "last_modified": mod}
    return out

def check_acs_summary():
    st, ent = ls(W + "summary_file/"); years = sorted(int(e[:4]) for e in ent if re.fullmatch(r"\d{4}/", e)); out = {"listing_url": W + "summary_file/", "latest_year_directory": max(years), "checked_utc": now(), "years": {}}
    for y in (2024, 2025, 2026):
        d_st, d_ent = ls(f"{W}summary_file/{y}/table-based-SF/data/"); info = {"data_directory_status": d_st, "data_directory_entries": d_ent}
        for span, pre in (("1YRData", "acsdt1y"), ("5YRData", "acsdt5y")):
            s_st, s_ent = ls(f"{W}summary_file/{y}/table-based-SF/data/{span}/"); kind, mod = classify(f"{W}summary_file/{y}/table-based-SF/data/{span}/{pre}{y}-b08303.dat")
            info[span] = {"directory_status": s_st, "table_files_listed": sum(e.endswith(".dat") for e in s_ent), "b08303_response": kind, "b08303_last_modified": mod, "published": s_st == 200 and kind == "data"}
        out["years"][str(y)] = info
    return out

def check_zillow():
    base = "https://files.zillowstatic.com/research/public_csvs/"; files = {"zhvi county": "zhvi/County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv", "zhvi zip": "zhvi/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
             "zori county": "zori/County_zori_uc_sfrcondomfr_sm_month.csv", "zori zip": "zori/Zip_zori_uc_sfrcondomfr_sm_month.csv"}
    log = pd.read_csv("raw/zillow/zillow_download_log.csv"); have = {f"{a} {b}": c for a, b, c in zip(log.measure, log.level, log.last_month)}; out = {"checked_utc": now(), "files": {}}
    for k, p in files.items():
        with requests.get(base + p, stream=True, timeout=120) as r:
            buf = b""
            for ch in r.iter_content(1 << 16):
                buf += ch
                if b"\n" in buf: break
            dates = [c for c in buf.split(b"\n")[0].decode("utf-8").strip().split(",") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", c)]
            out["files"][k] = {"last_month_at_source": dates[-1], "last_month_acquired": have[k], "newer_available": dates[-1] > have[k], "source_last_modified": r.headers.get("last-modified")}
    return out

def check_places():
    seen = {}
    for q in ("PLACES census tract", "PLACES Local Data for Better Health", "PLACES 2026 release", "PLACES tract 2026"):
        for x in catalog(q): seen[x["resource"]["id"]] = x["resource"]["name"]
    P = {i: n for i, n in seen.items() if "places" in n.lower()}; rel = sorted({int(m.group(1)) for n in P.values() for m in [re.search(r"(20\d{2})\s*release", n, flags=re.I)] if m})
    v = get_json("https://data.cdc.gov/api/views/cwsq-ngmh.json"); g = get_json("https://data.cdc.gov/resource/cwsq-ngmh.json", {"$select": "year,count(distinct measureid) as m", "$where": "stateabbr='CA'", "$group": "year"})
    return {"checked_utc": now(), "places_datasets_seen": len(P), "release_years_in_catalog": rel, "titles_mentioning_2026": [n for n in P.values() if "2026" in n], "titles_without_release_year": [n for n in P.values() if not re.search(r"20\d{2}\s*release", n, flags=re.I)],
            "standing_tract_dataset": {"id": "cwsq-ngmh", "title": v["name"], "rows_updated": datetime.datetime.fromtimestamp(v["rowsUpdatedAt"], datetime.timezone.utc).strftime("%Y-%m-%d"), "brfss_years_and_measures": {x["year"]: int(x["m"]) for x in g}}}

def check_mortality():
    qs = ["heart disease mortality county age group", "stroke mortality county age group", "cardiovascular disease death rates county age", "rates and trends heart disease stroke mortality county", "hypertension-related cardiovascular disease mortality county",
          "provisional mortality county heart disease", "provisional death counts county cause of death", "provisional county-level mortality", "VSRR provisional county deaths", "NCHS county mortality cause of death age", "excess death rates county cardiovascular",
          "heart disease deaths by county and age", "coronary heart disease mortality county", "heart failure mortality county", "underlying cause of death county", "mortality county age group 2021 2022 2023", "Interactive Atlas of Heart Disease and Stroke county"]
    seen = {}
    for q in qs:
        for x in catalog(q): seen[x["resource"]["id"]] = {"name": x["resource"]["name"], "cols": " ".join((x["resource"].get("columns_field_name") or [])).lower()}
    known = set(pd.read_csv("raw/mortality/mortality_download_log.csv").dataset_id)
    mc = {i: d for i, d in seen.items() if re.search(r"mortal|death", d["name"], flags=re.I) and (re.search(r"count(y|ies)", d["name"], flags=re.I) or any(k in d["cols"] for k in ("county", "fips", "locationid")))}
    cardio = {i: d["name"] for i, d in mc.items() if re.search(r"heart|stroke|cardiovascular|coronary|circulatory|hypertension", d["name"], flags=re.I)}
    out = {"checked_utc": now(), "queries": len(qs), "datasets_returned": len(seen), "county_mortality_datasets": len(mc), "cardiovascular_county_mortality_datasets": len(cardio),
           "cardiovascular_not_acquired": {i: n for i, n in cardio.items() if i not in known}, "provisional_county_series_titles": sorted(d["name"] for d in mc.values() if "provisional" in d["name"].lower()), "age_stratified": {}}
    for did in ("7b9s-s8ck", "rsk5-566a", "uc9k-vc2j"):
        v = get_json(f"https://data.cdc.gov/api/views/{did}.json"); g = get_json(f"https://data.cdc.gov/resource/{did}.json", {"$select": "year,count(*) as n", "$where": "locationabbr='CA'", "$group": "year", "$limit": 500})
        ann = sorted(int(x["year"]) for x in g if re.fullmatch(r"\d{4}", x["year"]))
        out["age_stratified"][did] = {"title": v["name"], "rows_updated": datetime.datetime.fromtimestamp(v["rowsUpdatedAt"], datetime.timezone.utc).strftime("%Y-%m-%d"), "first_year": ann[0], "last_year": ann[-1], "acquired": did in known}
    pooled = sorted(m.group(1) for n in cardio.values() for m in [re.search(r"State/Territory and County\s+\S\s+(\d{4}-\d{4})$", n)] if m); out["pooled_three_year_latest_period"] = pooled[-1] if pooled else None
    out["any_age_stratified_year_after_2020"] = any(d["last_year"] > 2020 for d in out["age_stratified"].values())
    return out

if __name__ == "__main__":
    res = {"pums": check_pums(), "acs_summary_files": check_acs_summary(), "zillow": check_zillow(), "places": check_places(), "mortality": check_mortality()}
    json.dump(res, open("ref/currency_check.json", "w"), indent=1); print("written ref/currency_check.json at", now())
