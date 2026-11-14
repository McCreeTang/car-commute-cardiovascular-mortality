"""Acquire ACS 5-year detailed tables for ALL US counties (summary level 050) and states (040, component 00)
from the Census Bureau sequence-based summary files on www2.census.gov (no API key needed).

Vintages: 2010 (2006-2010), 2014 (2010-2014), 2019 (2015-2019); 50 states + DC (Puerto Rico not requested).
Output: raw/acs_nat/acs5_<vintage>_<table>.parquet  (GEO_ID, geoid, sumlevel, name, vintage, <TABLE>_E###, <TABLE>_M###)
        raw/acs_nat/acs5_nat_download_log.csv

Layout (asserted at run time for every file):
  geography file g<yr>5<st>.csv : col 2 SUMLEVEL, col 3 COMPONENT, col 4 LOGRECNO, col 48 GEOID, col 49 NAME
  sequence file                 : field 5 LOGRECNO, data from field 6; lookup Start Position is 1-based
Missing or suppressed cells are '.' or blank in these files and become NaN.
In 2006-2010 the tables B08134/B08136 were not published; the collapsed C08134/C08136 are taken instead.
B23025 and B27001 do not exist in the 2006-2010 file.
The server answers HTTP 429 when requests arrive too fast (3 worker threads, pauses and retries are used), and its
firewall rejects a few individual URLs outright; those members are then read from the Census Bureau's whole-state
bundle on the same host and logged in raw/acs_nat/acs5_nat_bundle_fallbacks_<vintage>.csv. Downloaded zips are cached
in raw/acs_nat/zips, so a rerun only fetches what is missing.

Usage: python acquire_acs_national.py [vintage ...]
"""
import io, os, sys, time, zipfile, datetime, requests, pandas as pd
from concurrent.futures import ThreadPoolExecutor

BASE = "https://www2.census.gov/programs-surveys/acs/summary_file/"
LOOKUP = {2010: "2010/documentation/5_year/user_tools/Sequence_Number_and_Table_Number_Lookup.txt",
          2014: "2014/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt",
          2019: "2019/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt"}
COMMON = ["B08303", "B08301", "B08013", "B08101", "B01001", "B23001", "B19013", "B17001", "B15002", "B03002", "B25044", "B25077"]
TABLES = {2010: COMMON + ["C08134", "C08136"],
          2014: COMMON + ["B08134", "B08136", "B23025", "B27001"],
          2019: COMMON + ["B08134", "B08136", "B23025", "B27001"]}
STATES = {"Alabama": "al", "Alaska": "ak", "Arizona": "az", "Arkansas": "ar", "California": "ca", "Colorado": "co", "Connecticut": "ct",
          "Delaware": "de", "DistrictOfColumbia": "dc", "Florida": "fl", "Georgia": "ga", "Hawaii": "hi", "Idaho": "id", "Illinois": "il",
          "Indiana": "in", "Iowa": "ia", "Kansas": "ks", "Kentucky": "ky", "Louisiana": "la", "Maine": "me", "Maryland": "md",
          "Massachusetts": "ma", "Michigan": "mi", "Minnesota": "mn", "Mississippi": "ms", "Missouri": "mo", "Montana": "mt",
          "Nebraska": "ne", "Nevada": "nv", "NewHampshire": "nh", "NewJersey": "nj", "NewMexico": "nm", "NewYork": "ny",
          "NorthCarolina": "nc", "NorthDakota": "nd", "Ohio": "oh", "Oklahoma": "ok", "Oregon": "or", "Pennsylvania": "pa",
          "RhodeIsland": "ri", "SouthCarolina": "sc", "SouthDakota": "sd", "Tennessee": "tn", "Texas": "tx", "Utah": "ut",
          "Vermont": "vt", "Virginia": "va", "Washington": "wa", "WestVirginia": "wv", "Wisconsin": "wi", "Wyoming": "wy"}
SUB = "All_Geographies_Not_Tracts_Block_Groups"
RAW = "raw/acs_nat"; ZIPS = os.path.join(RAW, "zips")

class ServerRejected(Exception):
    """www2.census.gov answered HTTP 200 with an HTML 'Request Rejected' page instead of the file."""

def get(url, tries=12):
    """www2.census.gov answers HTTP 429 when requests arrive too fast: wait and retry with a growing pause."""
    last = None
    for k in range(tries):
        try:
            time.sleep(0.3)
            r = requests.get(url, timeout=600)
            if r.status_code == 429:
                raise requests.HTTPError(f"429 Too Many Requests: {url}")
            r.raise_for_status()
            if b"Request Rejected" in r.content[:400]:
                raise ServerRejected(url)
            return r.content
        except ServerRejected:
            raise                      # a firewall rejection of this URL is deterministic: do not retry
        except Exception as ex:
            last = ex; time.sleep(min(20 * (k + 1), 120))
    raise last

def load_lookup(vintage):
    p = f"ref/acs_lookup_{vintage}.txt"
    if not os.path.exists(p):
        os.makedirs("ref", exist_ok=True); open(p, "wb").write(get(BASE + LOOKUP[vintage]))
    L = pd.read_csv(p, dtype=str, encoding="latin-1", keep_default_na=False); L.columns = [c.strip() for c in L.columns]
    is_hdr = L["Start Position"].str.strip().str.isdigit() & L["Total Cells in Table"].str.contains(r"\d")
    H = L[is_hdr].copy()
    H["start"] = H["Start Position"].str.strip().astype(int)
    H["cells"] = H["Total Cells in Table"].str.extract(r"(\d+)")[0].astype(int)
    H["seq"] = H["Sequence Number"].astype(int)
    S = L[L["Total Cells in Sequence"].str.strip().str.isdigit()].copy(); S["seq"] = S["Sequence Number"].astype(int)
    seq_cells = S.groupby("seq")["Total Cells in Sequence"].first().str.strip().astype(int).to_dict()
    return H.set_index("Table ID")[["seq", "start", "cells"]], seq_cells

def load_geo(vintage, state, ab):
    url = f"{BASE}{vintage}/data/5_year_seq_by_state/{state}/{SUB}/g{vintage}5{ab}.csv"
    G = pd.read_csv(io.BytesIO(get(url)), header=None, dtype=str, encoding="latin-1")
    G = G[[2, 3, 4, 48, 49]].rename(columns={2: "sumlevel", 3: "component", 4: "logrecno", 48: "geoid_raw", 49: "name"})
    G = G[(G.sumlevel.isin(["050", "040"])) & (G.component == "00")].copy()
    ok = G.geoid_raw.str.match(r"^(05000US\d{5}|04000US\d{2})$")
    assert ok.all() and len(G) >= 2, f"geography layout changed for {vintage} {state}"
    G["geoid"] = G.geoid_raw.str.split("US").str[1]
    G["GEO_ID"] = G.sumlevel + "0000US" + G.geoid
    return G[["sumlevel", "logrecno", "GEO_ID", "geoid", "name"]], url

def bundle_members(vintage, state, ab, seq):
    """Fallback used ONLY when the per-sequence zip is rejected by the server firewall: read the same two members
    from the Census Bureau's whole-state bundle on the same host (5_year_by_state/<State>_All_Geographies_Not_Tracts_Block_Groups.zip)."""
    url = f"{BASE}{vintage}/data/5_year_by_state/{state}_{SUB}.zip"; path = os.path.join(ZIPS, f"bundle_{vintage}_{state}_{SUB}.zip")
    if not (os.path.exists(path) and zipfile.is_zipfile(path)):
        with requests.get(url, stream=True, timeout=1800) as r:
            r.raise_for_status()
            with open(path + ".part", "wb") as f:
                for ch in r.iter_content(1 << 22): f.write(ch)
        os.replace(path + ".part", path)
    if not zipfile.is_zipfile(path):
        raise ServerRejected(f"{url}: not a zip ({os.path.getsize(path)} bytes)")
    with zipfile.ZipFile(path) as zf:
        return {kind: zf.read(f"{kind}{vintage}5{ab}{seq:04d}000.txt") for kind in ("e", "m")}, url

FALLBACKS = []

def fetch_seq(vintage, state, ab, seq, n_cells):
    name = f"{vintage}5{ab}{seq:04d}000.zip"; path = os.path.join(ZIPS, name)
    url = f"{BASE}{vintage}/data/5_year_seq_by_state/{state}/{SUB}/{name}"
    if not (os.path.exists(path) and zipfile.is_zipfile(path)):
        try:
            b = get(url)
            if not zipfile.is_zipfile(io.BytesIO(b)):
                raise ServerRejected(f"{url}: {len(b)} bytes, not a zip")
            with open(path + ".part", "wb") as f: f.write(b)
        except ServerRejected as rej:
            print(f"per-sequence file rejected, using state bundle: {rej}", flush=True)
            members, burl = bundle_members(vintage, state, ab, seq)
            with zipfile.ZipFile(path + ".part", "w", zipfile.ZIP_DEFLATED) as zf:
                for kind, data in members.items(): zf.writestr(f"{kind}{vintage}5{ab}{seq:04d}000.txt", data)
            FALLBACKS.append({"vintage": vintage, "state": state, "sequence": seq, "rejected_url": url, "bundle_url": burl})
            pd.DataFrame(FALLBACKS).to_csv(os.path.join(RAW, f"acs5_nat_bundle_fallbacks_{vintage}.csv"), index=False)
        os.replace(path + ".part", path)
    out = {}
    with zipfile.ZipFile(path) as zf:
        for kind in ("e", "m"):
            df = pd.read_csv(zf.open(f"{kind}{vintage}5{ab}{seq:04d}000.txt"), header=None, dtype=str, encoding="latin-1",
                             na_values=["."], keep_default_na=True)
            assert df.shape[1] == 6 + n_cells, f"{name} {kind}: {df.shape[1]} fields, lookup says {6 + n_cells}"
            out[kind] = df
    return out, url

def one_state(vintage, state, ab, H, seq_cells, tables):
    G, gurl = load_geo(vintage, state, ab)
    res = {}; urls = {}
    for seq in sorted({int(H.loc[t, "seq"]) for t in tables}):
        d, url = fetch_seq(vintage, state, ab, seq, seq_cells[seq])
        for t in [t for t in tables if int(H.loc[t, "seq"]) == seq]:
            start, cells = int(H.loc[t, "start"]), int(H.loc[t, "cells"])
            cols = list(range(start - 1, start - 1 + cells))
            e = d["e"][[5] + cols].copy(); e.columns = ["logrecno"] + [f"{t}_E{i:03d}" for i in range(1, cells + 1)]
            m = d["m"][[5] + cols].copy(); m.columns = ["logrecno"] + [f"{t}_M{i:03d}" for i in range(1, cells + 1)]
            x = G.merge(e, on="logrecno", how="left", validate="1:1").merge(m, on="logrecno", how="left", validate="1:1")
            assert x[f"{t}_E001"].notna().any() or cells == 1, f"{vintage} {state} {t}: all rows unmatched"
            res[t] = x.drop(columns="logrecno"); urls[t] = url
    return state, res, urls, gurl

def run(vintage, workers=3):
    os.makedirs(ZIPS, exist_ok=True)
    H, seq_cells = load_lookup(vintage); tables = TABLES[vintage]
    n_hdr = H.index.value_counts(); bad = {t: int(n_hdr.get(t, 0)) for t in tables if n_hdr.get(t, 0) != 1}
    assert not bad, f"tables without exactly one lookup location in {vintage}: {bad}"
    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(lambda sa: one_state(vintage, sa[0], sa[1], H, seq_cells, tables), STATES.items()))
    log = []
    for t in tables:
        df = pd.concat([r[1][t] for r in results], ignore_index=True)
        cells = int(H.loc[t, "cells"])
        vcols = [c for c in df.columns if c.startswith(t + "_")]
        df[vcols] = df[vcols].apply(pd.to_numeric, errors="coerce")
        df = df[["GEO_ID", "geoid", "sumlevel", "name"] + [f"{t}_{k}{i:03d}" for i in range(1, cells + 1) for k in ("E", "M")]].copy()
        df.insert(4, "vintage", vintage)
        assert not df.GEO_ID.duplicated().any()
        out = os.path.join(RAW, f"acs5_{vintage}_{t.lower()}.parquet"); df.to_parquet(out, index=False)
        log.append({"vintage": vintage, "table": t, "sequence": int(H.loc[t, "seq"]), "start": int(H.loc[t, "start"]), "cells": cells,
                    "url_pattern": f"{BASE}{vintage}/data/5_year_seq_by_state/<State>/{SUB}/{vintage}5<st>{int(H.loc[t, 'seq']):04d}000.zip",
                    "states": len(results), "county_rows": int((df.sumlevel == "050").sum()), "state_rows": int((df.sumlevel == "040").sum()),
                    "county_rows_cell1_missing": int(df[df.sumlevel == "050"][f"{t}_E001"].isna().sum()),
                    "downloaded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "file": out})
        print({k: log[-1][k] for k in ("vintage", "table", "county_rows", "state_rows", "county_rows_cell1_missing")}, flush=True)
    lp = os.path.join(RAW, "acs5_nat_download_log.csv")
    old = pd.read_csv(lp) if os.path.exists(lp) else pd.DataFrame()
    if len(old): old = old[old.vintage != vintage]
    pd.concat([old, pd.DataFrame(log)], ignore_index=True).to_csv(lp, index=False)

def write_cell_labels(out="ref/acs_nat_cell_labels.csv"):
    """Label of every cell of the downloaded tables in each vintage, from the sequence lookup files; the build script
    selects cells by these labels and asserts them."""
    rows = []
    for v in TABLES:
        load_lookup(v)
        L = pd.read_csv(f"ref/acs_lookup_{v}.txt", dtype=str, encoding="latin-1", keep_default_na=False); L.columns = [c.strip() for c in L.columns]
        x = L[L["Table ID"].isin(TABLES[v])].copy(); x["ln"] = pd.to_numeric(x["Line Number"].str.strip(), errors="coerce")
        title = x[x["Start Position"].str.strip().str.isdigit()].set_index("Table ID")["Table Title"].to_dict()
        x = x[x.ln.notna() & (x.ln % 1 == 0)]
        rows += [{"vintage": v, "table": r["Table ID"], "cell": int(r.ln), "label": r["Table Title"].strip(), "concept": title[r["Table ID"]].strip()} for _, r in x.iterrows()]
    pd.DataFrame(rows).to_csv(out, index=False)

if __name__ == "__main__":
    for v in ([int(a) for a in sys.argv[1:]] or [2010, 2014, 2019]):
        run(v)
    write_cell_labels()
