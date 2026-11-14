"""Acquire ACS 5-year detailed tables from the legacy sequence-based summary files
(www2.census.gov), for vintages that have no table-based files (<= 2020).
Filters to study-area tracts (sumlevel 140) and counties (sumlevel 050) and writes the
same schema as acquire_acs_tablebased.py (GEO_ID, vintage, sumlevel, <TABLE>_E###, <TABLE>_M###).

Layout (verified against the 2014 files; asserted at run time for every vintage):
  geography file g<yr>5ca.csv : col 2 SUMLEVEL, col 4 LOGRECNO, col 48 GEOID, col 49 NAME
  sequence file               : field 5 LOGRECNO, data from field 6; lookup Start Position is 1-based
Missing/suppressed cells are '.' or blank in these files and become NaN.

Usage: python acquire_acs_sequence.py <vintage> [TABLE ...]
"""
import io, os, sys, zipfile, datetime, requests, pandas as pd

BASE = "https://www2.census.gov/programs-surveys/acs/summary_file/"
TABLES = ["B08303", "B08013", "B08301", "B08302", "B01001", "B19013", "B17001",
          "B15003", "B03002", "B25044", "B25077", "B25064"]
DIRS = {"140": "Tracts_Block_Groups_Only", "050": "All_Geographies_Not_Tracts_Block_Groups"}

def load_lookup(vintage):
    r = requests.get(f"{BASE}{vintage}/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt", timeout=300)
    r.raise_for_status()
    L = pd.read_csv(io.BytesIO(r.content), dtype=str, encoding="latin-1", keep_default_na=False)
    # non-header rows carry blank or empty strings in these columns, so test for digits explicitly
    is_hdr = L["Start Position"].str.strip().str.isdigit() & L["Total Cells in Table"].str.contains(r"\d")
    H = L[is_hdr].copy()
    H["start"] = H["Start Position"].str.strip().astype(int)
    H["cells"] = H["Total Cells in Table"].str.extract(r"(\d+)")[0].astype(int)
    H["seq"] = H["Sequence Number"].astype(int)
    S = L[L["Total Cells in Sequence"].str.strip().str.isdigit()].copy()
    S["seq"] = S["Sequence Number"].astype(int)
    seq_cells = S.groupby("seq")["Total Cells in Sequence"].first().str.strip().astype(int).to_dict()
    return H.set_index("Table ID")[["seq", "start", "cells"]], seq_cells

def load_geo(vintage, county_geoids):
    url = f"{BASE}{vintage}/data/5_year_seq_by_state/California/{DIRS['140']}/g{vintage}5ca.csv"
    r = requests.get(url, timeout=300); r.raise_for_status()
    G = pd.read_csv(io.BytesIO(r.content), header=None, dtype=str, encoding="latin-1")
    G = G[[2, 4, 48, 49]].rename(columns={2: "sumlevel", 4: "logrecno", 48: "geoid_raw", 49: "name"})
    G = G[G.sumlevel.isin(["140", "050"])].copy()
    ok = G.geoid_raw.str.match(r"^(14000US\d{11}|05000US\d{5})$")
    assert ok.all(), f"geography layout changed for {vintage}: {G[~ok].head()}"
    G["fips"] = G.geoid_raw.str.split("US").str[1]
    G = G[G.fips.str[:5].isin(county_geoids)].copy()
    G["GEO_ID"] = G.sumlevel + "0000US" + G.fips
    return G

BUNDLES = {"140": "California_Tracts_Block_Groups_Only.zip", "050": "California_All_Geographies_Not_Tracts_Block_Groups.zip"}

class ServerRejected(Exception):
    """www2.census.gov answered HTTP 200 with an HTML 'Request Rejected' page instead of the file."""

def _read_members(zf, vintage, seq, n_cells):
    out = {}
    for kind in ("e", "m"):
        name = f"{kind}{vintage}5ca{seq:04d}000.txt"
        df = pd.read_csv(zf.open(name), header=None, dtype=str, encoding="latin-1", na_values=["."], keep_default_na=True)
        assert df.shape[1] == 6 + n_cells, f"{name}: {df.shape[1]} fields, lookup says {6 + n_cells}"
        out[kind] = df
    return out

def fetch_sequence(vintage, seq, sumlevel, n_cells):
    url = f"{BASE}{vintage}/data/5_year_seq_by_state/California/{DIRS[sumlevel]}/{vintage}5ca{seq:04d}000.zip"
    r = requests.get(url, timeout=600); r.raise_for_status()
    if b"Request Rejected" in r.content[:300] or not zipfile.is_zipfile(io.BytesIO(r.content)):
        raise ServerRejected(f"{url} -> {len(r.content)} bytes, content-type {r.headers.get('content-type')}")
    return _read_members(zipfile.ZipFile(io.BytesIO(r.content)), vintage, seq, n_cells), url

def fetch_sequence_from_bundle(vintage, seq, sumlevel, n_cells, cachedir="raw/acs"):
    """Fallback used ONLY when the per-sequence zip is rejected by the server: read the same member from the
    Census Bureau's whole-state bundle (same host). Members were verified byte-identical to the per-sequence
    files for 2019 sequence 114 (SHA-256)."""
    url = f"{BASE}{vintage}/data/5_year_by_state/{BUNDLES[sumlevel]}"
    path = os.path.join(cachedir, f"{vintage}_{BUNDLES[sumlevel]}")
    if not (os.path.exists(path) and zipfile.is_zipfile(path)):
        with requests.get(url, stream=True, timeout=1800) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for ch in r.iter_content(1 << 22): f.write(ch)
    if not zipfile.is_zipfile(path):
        raise ServerRejected(f"{url} -> not a zip ({os.path.getsize(path)} bytes)")
    return _read_members(zipfile.ZipFile(path), vintage, seq, n_cells), url

def run(vintage, tables, counties_csv="ref/study_counties.csv", outdir="raw/acs"):
    c = pd.read_csv(counties_csv, dtype=str)
    H, seq_cells = load_lookup(vintage)
    # some large tables span several sequences (several header rows); this parser reads one location per
    # table, so refuse any requested table that does not have exactly one header row
    n_hdr = H.index.value_counts()
    bad = {t: int(n_hdr.get(t, 0)) for t in tables if n_hdr.get(t, 0) != 1}
    assert not bad, f"tables without exactly one lookup location in {vintage}: {bad}"
    G = load_geo(vintage, set(c.county_geoid))
    os.makedirs(outdir, exist_ok=True); log = []; cache = {}
    for t in tables:
        try:
            seq, start, cells = (int(v) for v in H.loc[t])
            parts = []; urls = []; notes = []
            for sl in ("140", "050"):
                if (seq, sl) not in cache:
                    try:
                        cache[(seq, sl)] = fetch_sequence(vintage, seq, sl, seq_cells[seq]) + ("per-sequence file",)
                    except ServerRejected as rej:
                        print(f"per-sequence file rejected, using state bundle: {rej}", flush=True)
                        cache[(seq, sl)] = fetch_sequence_from_bundle(vintage, seq, sl, seq_cells[seq]) + (f"STATE BUNDLE fallback (sumlevel {sl}); per-sequence file rejected by server",)
                (d, url, how) = cache[(seq, sl)]; urls.append(url); notes.append(how)
                g = G[G.sumlevel == sl][["logrecno", "GEO_ID"]]
                cols = list(range(start - 1, start - 1 + cells))
                e = d["e"][[5] + cols].copy(); e.columns = ["logrecno"] + [f"{t}_E{i:03d}" for i in range(1, cells + 1)]
                m = d["m"][[5] + cols].copy(); m.columns = ["logrecno"] + [f"{t}_M{i:03d}" for i in range(1, cells + 1)]
                x = g.merge(e, on="logrecno", how="left", validate="1:1").merge(m, on="logrecno", how="left", validate="1:1")
                parts.append(x.drop(columns="logrecno"))
            df = pd.concat(parts, ignore_index=True)
            vcols = [k for k in df.columns if k != "GEO_ID"]
            df[vcols] = df[vcols].apply(pd.to_numeric, errors="coerce")
            order = ["GEO_ID"] + [f"{t}_{k}{i:03d}" for i in range(1, cells + 1) for k in ("E", "M")]
            df = df[order].copy()
            df.insert(1, "vintage", int(vintage)); df.insert(2, "sumlevel", df.GEO_ID.str[:3])
            out = os.path.join(outdir, f"acs5_{vintage}_{t.lower()}.parquet"); df.to_parquet(out, index=False)
            info = {"vintage": int(vintage), "table": t.lower(), "url": " ; ".join(urls), "source_note": " ; ".join(notes), "sequence": seq, "start": start, "cells": cells,
                    "tract_rows": int((df.sumlevel == "140").sum()), "county_rows": int((df.sumlevel == "050").sum()),
                    "tract_rows_all_null": int(df[df.sumlevel == "140"][f"{t}_E001"].isna().sum()),
                    "downloaded_utc": datetime.datetime.utcnow().isoformat(timespec="seconds"), "file": out}
        except Exception as ex:
            info = {"vintage": int(vintage), "table": t.lower(), "error": f"{type(ex).__name__}: {ex}"}
        log.append(info); print(info, flush=True)
    lp = os.path.join(outdir, f"acs5_{vintage}_download_log.csv")
    old = pd.read_csv(lp) if os.path.exists(lp) else pd.DataFrame()
    pd.concat([old, pd.DataFrame(log)], ignore_index=True).to_csv(lp, index=False)
    return log, G

if __name__ == "__main__":
    run(sys.argv[1], [t.upper() for t in sys.argv[2:]] or TABLES)
