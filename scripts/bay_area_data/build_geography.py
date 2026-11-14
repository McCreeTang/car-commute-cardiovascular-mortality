"""Build the geography reference files used by the other acquisition scripts.

1. study_counties.csv  - the 15 study counties, FIPS taken from the Census ACS geography file (name match), with core9 flag.
   (The brief asked for the Census API NAME field; api.census.gov rejects data queries without a key, so the
   geography file of the 2020-2024 ACS 5-year summary file is used instead - agreed with the user.)
2. puma_county_map.csv - PUMA -> county for the three PUMA definitions used by ACS 1-year PUMS:
     Census 2000 PUMAs (PUMS 2010-2011), 2010 PUMAs (PUMS 2012-2021), 2020 PUMAs (PUMS 2022-2024).
3. ca_county_names_58.csv - the 58 California county names (used by acquire_ccrs.py for the CCRS county code).
4. puma_mixed_shares.csv - population shares for the one PUMA per definition that mixes San Benito County
   with part of Monterey County (outside the study area).

Usage: python build_geography.py [outdir]     (default outdir: ref)
"""
import io, os, re, sys, requests, pandas as pd

ACS = "https://www2.census.gov/programs-surveys/acs/summary_file/"
CORE = ["Alameda", "Contra Costa", "Marin", "Napa", "San Francisco", "San Mateo", "Santa Clara", "Solano", "Sonoma"]
EXT = ["San Joaquin", "Stanislaus", "Sacramento", "Merced", "San Benito", "Santa Cruz"]
SRC = {"geos": ACS + "2024/table-based-SF/documentation/Geos20245YR.txt",
       "b01001_2024": ACS + "2024/table-based-SF/data/5YRData/acsdt5y2024-b01001.dat",
       "puma2000": "https://www2.census.gov/census_2000/datasets/PUMS/FivePercent/California/PUMEQ5-CA.TXT",
       "puma2010_equiv": "https://www2.census.gov/geo/docs/reference/puma/PUMSEQ10_06.txt",
       "tract_puma_2010": "https://www2.census.gov/geo/docs/maps-data/data/rel/2010_Census_Tract_to_2010_PUMA.txt",
       "tract_puma_2020": "https://www2.census.gov/geo/docs/maps-data/data/rel2020/2020_Census_Tract_to_2020_PUMA.txt"}
PUMS_YEARS = {2000: "2010-2011", 2010: "2012-2021", 2020: "2022-2024"}

def get(url):
    r = requests.get(url, timeout=900); r.raise_for_status()
    assert b"Request Rejected" not in r.content[:300], f"server rejection page for {url}"
    return r.content

def study_counties():
    geo = pd.read_csv(io.BytesIO(get(SRC["geos"])), sep="|", dtype=str, encoding="utf-8", encoding_errors="replace")
    ca = geo[(geo.SUMLEVEL == "050") & (geo.STUSAB == "CA")].copy()
    assert len(ca) == 58
    ca["county_name"] = ca.NAME.str.replace(" County, California", "", regex=False)
    study_counties.ca58 = sorted(ca.county_name)        # all 58 names; their alphabetical index is the CCRS county code
    sel = ca[ca.county_name.isin(CORE + EXT)].copy()
    assert len(sel) == 15 and set(sel.county_name) == set(CORE + EXT)
    out = sel.rename(columns={"STATE": "state_fips", "COUNTY": "county_fips", "GEO_ID": "geo_id"})[["county_name", "state_fips", "county_fips", "geo_id"]]
    out["core9"] = out.county_name.isin(CORE); out["county_geoid"] = out.state_fips + out.county_fips
    return out.sort_values("county_fips").reset_index(drop=True)

def puma2000():
    """PUMEQ5: fixed-width records with one leading space; 780 = PUMA, 781 = PUMA-county part, with Census 2000 population."""
    recs = []
    for l in get(SRC["puma2000"]).decode("latin-1").splitlines():
        m = re.match(r"^ (780|781) (\d{2}) (\d{5}) (\d{5})(?: (\d{3}))?", l)
        if not m: continue
        m2 = re.match(r"^.*?\s(\d+) ([A-Za-z].*?)\s*$", l[m.end():])
        recs.append({"sumlev": m.group(1), "puma": m.group(4), "county": m.group(5), "pop": int(m2.group(1))})
    E = pd.DataFrame(recs); tot = E[E.sumlev == "780"].set_index("puma")["pop"]; part = E[E.sumlev == "781"]
    assert len(tot) == 233 and (part.groupby("puma")["pop"].sum().reindex(tot.index) == tot).all()
    return part[["puma", "county", "pop"]]

def puma2010_parts():
    """PUMSEQ10: 250-char fixed width; 795 = PUMA, 796 = PUMA-county part, with Census 2010 population."""
    recs = []
    for l in get(SRC["puma2010_equiv"]).decode("latin-1").splitlines():
        m = re.match(r"^796\d{2}\d{8}(\d{5})(\d{3})\d{8}\s+(\d+)", l)
        if m: recs.append({"puma": m.group(1), "county": m.group(2), "pop": int(m.group(3))})
    return pd.DataFrame(recs)

def tract_puma(vintage):
    d = pd.read_csv(io.BytesIO(get(SRC[f"tract_puma_{vintage}"])), dtype=str, encoding="utf-8-sig")
    assert list(d.columns) == ["STATEFP", "COUNTYFP", "TRACTCE", "PUMA5CE"]
    return d[d.STATEFP == "06"].rename(columns={"PUMA5CE": "puma", "COUNTYFP": "county"})

def acs2024_tract_pop(geo_ids):
    got = {}
    with requests.get(SRC["b01001_2024"], stream=True, timeout=900) as r:
        it = r.iter_lines(); hdr = next(it).decode().split("|"); assert hdr[:2] == ["GEO_ID", "B01001_E001"]
        pre = tuple(sorted({g[:14].encode() for g in geo_ids}))
        for raw in it:
            if raw.startswith(pre):
                f = raw.decode().split("|")
                if f[0] in geo_ids: got[f[0]] = int(f[1])
    return got

def build(outdir="ref"):
    os.makedirs(outdir, exist_ok=True)
    c = study_counties(); c.to_csv(os.path.join(outdir, "study_counties.csv"), index=False)
    pd.DataFrame({"county_name": study_counties.ca58}).to_csv(os.path.join(outdir, "ca_county_names_58.csv"), index=False)
    name = c.set_index("county_fips").county_name.to_dict(); core = c.set_index("county_fips").core9.to_dict()
    p00 = puma2000(); t10 = tract_puma(2010); t20 = tract_puma(2020); e10 = puma2010_parts()
    member = {2000: p00[["puma", "county"]].drop_duplicates(), 2010: t10[["puma", "county"]].drop_duplicates(), 2020: t20[["puma", "county"]].drop_duplicates()}
    # population shares of the mixed PUMA (San Benito = 069, Monterey = 053)
    sh = []
    for v, pops, basis in ((2000, p00, "Census 2000 100% count (PUMEQ5-CA.TXT, summary level 781)"), (2010, e10, "Census 2010 count (PUMSEQ10_06.txt, summary level 796)")):
        mixed = [p for p, g in member[v].groupby("puma") if "069" in set(g.county)]
        assert len(mixed) == 1; g = pops[pops.puma == mixed[0]].set_index("county")["pop"]
        sh.append({"puma_vintage": v, "puma": mixed[0], "san_benito_pop": int(g["069"]), "outside_pop": int(g.drop("069").sum()), "basis": basis})
    mixed20 = [p for p, g in member[2020].groupby("puma") if "069" in set(g.county)]; assert len(mixed20) == 1
    mem = t20[t20.puma == mixed20[0]].copy(); mem["GEO_ID"] = "1400000US06" + mem.county + mem.TRACTCE
    pop = acs2024_tract_pop(set(mem.GEO_ID)); assert len(pop) == len(mem); mem["pop"] = mem.GEO_ID.map(pop)
    g = mem.groupby("county")["pop"].sum()
    sh.append({"puma_vintage": 2020, "puma": mixed20[0], "san_benito_pop": int(g["069"]), "outside_pop": int(g.drop("069").sum()),
               "basis": "ACS 2020-2024 B01001_E001 summed over member tracts (2020 tract-to-PUMA file)"})
    SH = pd.DataFrame(sh); SH["san_benito_share"] = (SH.san_benito_pop / (SH.san_benito_pop + SH.outside_pop)).round(4); SH["outside_county"] = "Monterey (part)"
    SH.to_csv(os.path.join(outdir, "puma_mixed_shares.csv"), index=False)
    share = SH.set_index("puma_vintage").san_benito_share
    rows = []
    for v, m in member.items():
        for p, gg in m.groupby("puma"):
            cs = sorted(set(gg.county))
            if not any(x in name for x in cs): continue
            mixed = any(x not in name for x in cs); single = cs[0] if len(cs) == 1 else None
            assert mixed or single is not None, f"PUMA {p} spans several study counties"
            rows.append({"puma_vintage": v, "pums_years": PUMS_YEARS[v], "puma": p, "county_fips": single, "county_name": name.get(single) if single else None,
                         "core9": bool(core.get(single, False)) if single else False, "n_counties": len(cs), "puma_mixed_outside": mixed,
                         "mixed_detail": (f"San Benito ({share[v]:.1%} of PUMA population) + Monterey (part), outside study area" if mixed else ""),
                         "san_benito_share": float(share[v]) if mixed else None})
    P = pd.DataFrame(rows); assert not P.duplicated(["puma_vintage", "puma"]).any()
    P.to_csv(os.path.join(outdir, "puma_county_map.csv"), index=False)
    return c, P, SH

if __name__ == "__main__":
    c, P, SH = build(sys.argv[1] if len(sys.argv) > 1 else "ref")
    print("counties", len(c), "| PUMA rows by definition", P.groupby("puma_vintage").size().to_dict()); print(SH.to_string(index=False))
