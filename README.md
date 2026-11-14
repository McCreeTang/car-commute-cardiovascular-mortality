# Car-commute time and cardiovascular mortality

Code, derived data and analysis reports for the manuscript:

> Car-commute time and cardiovascular mortality: a San Francisco Bay Area burden model and a national county comparison

Author: [Author name], Independent researcher, [City], California, USA. Correspondence: [email].

## What is here

| Folder | Contents |
|---|---|
| `scripts/bay_area_data/` | Acquisition of ACS summary files and PUMS microdata, Zillow indices, CDC PLACES and county mortality, California crash records; dataset build and quality checks for the 15 Bay Area study counties |
| `scripts/bay_area_models/` | Commute and housing trends with replicate-weight variance; tract-level spatial models; county-year fixed-effects models; sensitivity analyses |
| `scripts/burden/` | Age-stratified comparative risk assessment with 40,000-draw Monte Carlo; validity checks; post-2020 scenario |
| `scripts/national/` | National county dataset (3,136 county units, three ACS periods) and the pre-specified cross-section, change and matched analyses |
| `data_derived/` | Analysis-ready datasets built from public sources (tract, county-year, national county, mortality) |
| `results/` | Every result table reported in the manuscript, plus the literature parameter table and reference list |
| `reports/` | Methods-and-results reports generated from the result files, pre-specified analysis plans, data dictionaries, quality-control reports and the STROBE checklist |
| `figures/` | Manuscript and supplementary figures at 300 dpi |

The person-level PUMS extract (1.24 million records, about 100 MB) is not in this repository; it is rebuilt by `scripts/bay_area_data/acquire_pums.py` from the Census Bureau files, and the aggregate `pums_county_year_age.parquet` derived from it is included.

## Reproducing

Scripts were run with Python 3.11, pandas, numpy, scipy, statsmodels, pyarrow, geopandas, libpysal, spreg and esda. Each script group reads input paths from a small JSON file described at the top of the script (for example `handoff/input_paths.json` for the Bay Area models and `burden/paths.json` for the burden model); recreate it with local paths before running. Raw downloads come from www2.census.gov (ACS summary files and PUMS), files.zillowstatic.com (Zillow indices), data.cdc.gov (PLACES, county mortality) and data.ca.gov (crash records). The Census API was not used because it now requires a key. Sources are live and revised by their publishers, so a rerun may return slightly different values.

## Data sources

US Census Bureau American Community Survey (5-year summary files 2006–2010, 2010–2014, 2015–2019, 2020–2024; 1-year PUMS 2010–2019 and 2021–2024; 1-year county tables 2021–2025); Zillow Home Value Index and Observed Rent Index; CDC PLACES tract and county data; CDC county heart disease and stroke mortality series (NVSS); NCHS Urban–Rural Classification Scheme; California Highway Patrol Crash Reporting System via data.ca.gov; Census TIGER/Line and cartographic boundary files.

## Analysis plans

`reports/analysis_plan_prespecified.md` (Bay Area tract and panel models) and `reports/national_prespecified_plan.md` (national comparison) were saved before the corresponding models were fitted. Departures are listed in the respective methods reports. The national plan prints one benchmark limit as 7.6% where the computed value is 7.65%; the report records the correction.

## Licence

Code: MIT License. Derived data and reports: CC BY 4.0. Source data remain subject to their publishers' terms.

## Citation

Please cite the manuscript once published, and this repository by its Zenodo DOI (to be added at acceptance).
