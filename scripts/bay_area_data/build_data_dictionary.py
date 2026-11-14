"""Generate data_dictionary.md. Every column of every delivered file must match a documented entry (asserted).
Download dates come from the acquisition logs (UTC); PLACES measure wording comes from the data.

Usage: python build_data_dictionary.py
"""
import os, re, json, datetime, pandas as pd, pyarrow.parquet as pq

def logdate(path, col):
    d = pd.read_csv(path)[col].dropna().str[:10]; return d.min() if d.min() == d.max() else f"{d.min()} to {d.max()}"
def filedate(path): return datetime.datetime.fromtimestamp(os.path.getmtime(path), datetime.timezone.utc).strftime("%Y-%m-%d")
acs_d = sorted({logdate(f"raw/acs/acs5_{v}_download_log.csv", "downloaded_utc") for v in (2014, 2019, 2024)}); acs_d = acs_d[0] if len(acs_d) == 1 else " / ".join(acs_d)
W = "https://www2.census.gov/"
SRC = {  # id: (description, url, vintage, downloaded UTC, script)
 "ACS5": ("American Community Survey 5-year detailed tables (B08303, B08013, B08301, B08302, B01001, B19013, B17001, B15003, B03002, B25044, B25077, B25064), tract and county, estimates and 90% margins of error",
          W + "programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/ ; " + W + "programs-surveys/acs/summary_file/{2014,2019}/data/5_year_seq_by_state/California/", "2010-2014, 2015-2019, 2020-2024", acs_d, "acquire_acs_tablebased.py, acquire_acs_sequence.py"),
 "ACS1": ("Published ACS 1-year county tables B08303, B08013, C08301 (table-based summary files); county totals for workers 16+, not age-specific",
          W + "programs-surveys/acs/summary_file/{year}/table-based-SF/data/1YRData/", "2021-2025 (2025 released 2026-10-29)", logdate("raw/acs1/acs1_download_log.csv", "downloaded_utc"), "acquire_acs1_county.py"),
 "PUMS": ("ACS Public Use Microdata Sample, California person file, 1-year", W + "programs-surveys/acs/data/pums/{year}/1-Year/csv_pca.zip", "2010-2019, 2021-2024 (no 2020 file; 2025 not yet published when checked)", logdate("raw/pums/pums_download_log.csv", "downloaded_utc"), "acquire_pums.py"),
 "PUMAGEO": ("PUMA-to-county relationships: Census 2000 PUMA equivalency, 2010 PUMA equivalency, 2010 and 2020 tract-to-PUMA files",
             W + "census_2000/datasets/PUMS/FivePercent/California/PUMEQ5-CA.TXT ; " + W + "geo/docs/reference/puma/PUMSEQ10_06.txt ; " + W + "geo/docs/maps-data/data/rel/2010_Census_Tract_to_2010_PUMA.txt ; " + W + "geo/docs/maps-data/data/rel2020/2020_Census_Tract_to_2020_PUMA.txt", "2000, 2010, 2020 PUMA definitions", filedate("raw/geo/PUMEQ5-CA.TXT"), "build_geography.py"),
 "TRACTREL": ("Census 2020-to-2010 tract relationship file, California", W + "geo/docs/maps-data/data/rel2020/tract/tab20_tract20_tract10_st06.txt", "2010 and 2020 tract boundaries", filedate("raw/geo/tab20_tract20_tract10_st06.txt"), "build_analysis_datasets.py"),
 "ZILLOW": ("Zillow Home Value Index (all homes, mid-tier, smoothed, seasonally adjusted) and Zillow Observed Rent Index (all homes plus multifamily, smoothed), county and ZIP, monthly",
            "https://files.zillowstatic.com/research/public_csvs/zhvi/ ; https://files.zillowstatic.com/research/public_csvs/zori/", "ZHVI 2000-01 to 2026-09; ZORI 2015-01 to 2026-09", logdate("raw/zillow/zillow_download_log.csv", "downloaded_utc"), "acquire_zillow.py"),
 "PLACES": ("CDC PLACES: Local Data for Better Health, census tract data, long format, releases 2020-2025 (dataset ids 4ai3-zynv, 373s-ayzu, nw2y-v4gm, em5e-5hvn, ai6z-tcin, cwsq-ngmh)",
            "https://data.cdc.gov/resource/{dataset id}", "BRFSS 2017-2023; 2010 tracts (releases 2020-2023), 2020 tracts (releases 2024-2025)", logdate("raw/places/places_download_log.csv", "downloaded_utc"), "acquire_cdc_places.py"),
 "MORT-A": ("CDC: Rates and Trends in Heart Disease and Stroke Mortality Among US Adults (35+) by County, Age Group, Race/Ethnicity, and Sex, 2000-2019 (NVSS)", "https://data.cdc.gov/resource/7b9s-s8ck", "annual 1999-2019", logdate("raw/mortality/mortality_download_log.csv", "downloaded_utc"), "acquire_cdc_mortality.py"),
 "MORT-B": ("CDC: Cardiovascular Disease Death Rates, Trends, and Excess Death Rates Among US Adults (35+) by County and Age Group, 2010-2020 (NVSS)", "https://data.cdc.gov/resource/rsk5-566a", "annual 2010-2020", logdate("raw/mortality/mortality_download_log.csv", "downloaded_utc"), "acquire_cdc_mortality.py"),
 "MORT-P": ("CDC: Heart Disease / Stroke Mortality Data Among US Adults (35+) by State/Territory and County, three-year pooled (16 datasets; ids in acquire_cdc_mortality.py)", "https://data.cdc.gov/resource/{dataset id}", "periods 2014-2016 to 2022-2024 (no 2020-2022)", logdate("raw/mortality/mortality_download_log.csv", "downloaded_utc"), "acquire_cdc_mortality.py"),
 "CCRS": ("California Highway Patrol, California Crash Reporting System, Crashes tables, via the data.ca.gov datastore SQL API", "https://data.ca.gov/dataset/ccrs", "2016-2026 (2026 partial)", logdate("raw/crash/ccrs_query_log.csv", "queried_utc"), "acquire_ccrs.py, build_road_rage_proxy.py"),
 "DERIVED": ("Derived in this project from the sources named in the definition", "", "", "", "build_analysis_datasets.py"),
}
P = pd.read_parquet("places_tract_long.parquet", columns=["release", "measureid", "measure"]); PM = P.sort_values("release").groupby("measureid").measure.last().to_dict()
MEAS = ["CHD", "STROKE", "BPHIGH", "OBESITY", "LPA", "DIABETES", "CSMOKING", "SLEEP", "MHLTH", "DEPRESSION"]
PL_CAV = "MODEL-BASED small-area estimate, not a direct survey estimate; crude (not age-adjusted) prevalence for all adults 18+, NOT age-specific; built partly from demographic predictors (see 'Read first')."
MOE = "90% margin of error; Census Bureau approximation formulas for sums, proportions and ratios (overstated when many cells are summed); missing where the source margin is a jam value or the estimate is top-coded."
ID = [("county_fips", "3-digit county FIPS code (California state code 06 omitted).", "ACS5", "", "Verified by county name against the ACS geography file."),
      ("county_name", "County name.", "ACS5", "", ""), ("core9", "True for the nine Bay Area counties (Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma); False for the six adjacent counties.", "DERIVED", "", "")]
def share(name, text, cells): return (name, f"{text} ({cells}).", "ACS5", "per acs_period", "Share in 0-1. Missing where the denominator is zero.")
D = {}
D["tract_analysis.parquet"] = ("One row per census tract x cross-section (7,068 rows). Key: tract_geoid + acs_vintage. Each cross-section is on its native tract boundaries.", ID + [
  ("cross_section", "Design-level label: ACS period and the PLACES release paired with it.", "DERIVED", "", "Three values. The 2010-2014 cross-section has no PLACES release (no outcomes)."),
  ("tract_geoid", "11-digit census tract identifier (state + county + tract).", "ACS5", "boundaries per tract_vintage", "The same code in different vintages is not necessarily the same area; see overlap_same_geoid."),
  ("acs_vintage", "End year of the ACS 5-year period (2014, 2019, 2024).", "ACS5", "", ""), ("acs_period", "ACS 5-year period.", "ACS5", "", ""),
  ("tract_vintage", "Census tract boundary vintage of the row (2010 or 2020).", "ACS5", "", "2010 for acs_vintage 2014 and 2019; 2020 for 2024."),
  ("pop_total", "Total population (B01001_001).", "ACS5", "per acs_period", ""), ("workers_total", "Workers aged 16+ (B08301_001), including those who worked from home.", "ACS5", "per acs_period", ""),
  ("commuters_total", "Workers aged 16+ who did not work from home (B08303_001); universe of the travel-time variables.", "ACS5", "per acs_period", ""),
  ("households_total", "Occupied housing units (B25044_001).", "ACS5", "per acs_period", ""),
  share("share_commute_45plus", "Share of commuters with travel time of 45 minutes or more", "B08303_011-013 / 001"), share("share_commute_60plus", "Share of commuters with travel time of 60 minutes or more", "B08303_012-013 / 001"),
  share("share_commute_90plus", "Share of commuters with travel time of 90 minutes or more", "B08303_013 / 001"), share("share_commute_lt15", "Share of commuters with travel time under 15 minutes", "B08303_002-004 / 001"),
  share("share_drive_alone", "Share of all workers who drove alone", "B08301_003 / 001"), share("share_carpool", "Share of all workers who carpooled", "B08301_004 / 001"),
  share("share_transit", "Share of all workers using public transportation", "B08301_010 / 001"), share("share_walk", "Share of all workers who walked", "B08301_019 / 001"),
  share("share_bike", "Share of all workers who bicycled", "B08301_018 / 001"), share("share_wfh", "Share of all workers who worked from home", "B08301_021 / 001"),
  share("share_taxi_moto_other", "Share of all workers using taxi or ride-hailing, motorcycle or other means", "B08301_016, 017, 020 / 001"),
  share("share_drive_alone_commuters", "Share of commuters (workers excluding those working from home) who drove alone", "B08301_003 / (001 - 021)"),
  share("share_depart_before_6am", "Share of commuters leaving home before 6:00 a.m.", "B08302_002-004 / 001"), share("share_depart_before_7am", "Share of commuters leaving home before 7:00 a.m.", "B08302_002-006 / 001"),
  share("share_female", "Share of population that is female", "B01001_026 / 001"), share("poverty_rate", "Share of the poverty-status universe with income below the poverty level", "B17001_002 / 001"),
  share("share_bachelors_plus", "Share of population 25+ with a bachelor's degree or higher", "B15003_022-025 / 001"), share("share_nh_white", "Share non-Hispanic White alone", "B03002_003 / 001"),
  share("share_nh_black", "Share non-Hispanic Black alone", "B03002_004 / 001"), share("share_nh_asian", "Share non-Hispanic Asian alone", "B03002_006 / 001"), share("share_hispanic", "Share Hispanic or Latino", "B03002_012 / 001"),
  share("share_no_vehicle_hh", "Share of occupied housing units with no vehicle available", "B25044_003 + 010 / 001"),
  share("share_age_under18", "Share of population under 18", "B01001 age cells / 001"), share("share_age_18_34", "Share of population aged 18-34", "B01001 age cells / 001"),
  share("share_age_35_64", "Share of population aged 35-64", "B01001 age cells / 001"), share("share_age_65plus", "Share of population aged 65+", "B01001 age cells / 001"),
  ("mean_commute_min", "Mean travel time to work in minutes: aggregate travel time (B08013_001) / commuters (B08303_001).", "ACS5", "per acs_period", "Missing where the aggregate is withheld by the Census Bureau or there are no commuters (15, 14 and 24 tracts by period)."),
  ("median_hh_income", "Median household income (B19013_001), nominal dollars of income_dollar_year.", "ACS5", "per acs_period", "Not inflation-adjusted across periods. Top-coded at 250,001; see median_hh_income_topcoded."),
  ("median_home_value", "Median value of owner-occupied housing units (B25077_001), nominal dollars.", "ACS5", "per acs_period", "Top-coded at 1,000,001 (2010-2014) and 2,000,001 (later): right-censored, cap changed between periods."),
  ("median_gross_rent", "Median gross rent (B25064_001), nominal dollars per month.", "ACS5", "per acs_period", "Top-coded at 2,001 (2010-2014) and 3,501 (later)."),
  ("income_dollar_year", "Year of the dollars in which median_hh_income is expressed.", "ACS5", "", ""),
  (r"re:median_(hh_income|home_value|gross_rent)_topcoded", "True where the median equals the ACS cap plus one (value is right-censored).", "DERIVED", "", "Use censored-data methods or exclude; do not treat as a real median."),
  (r"re:.+_moe", MOE.split(";")[0] + " of the variable with the same name.", "ACS5", "per acs_period", MOE),
] + [(f"{m.lower()}_prev", f"{PM[m]} (percent).", "PLACES", "per places_release and *_data_year", PL_CAV) for m in MEAS] + [
  (r"re:.+_prev_(lo|hi)", "Lower / upper 95% confidence limit of the PLACES estimate (percent).", "PLACES", "", "Model-based interval."),
  (r"re:.+_data_year", "BRFSS survey year of that measure in the paired release.", "PLACES", "", "Short sleep is one year earlier than the other measures (2018, 2022)."),
  ("places_release", "PLACES release paired with the ACS period: the latest release on the same tract boundaries whose data years all fall inside the period (2021 release for 2015-2019; 2025 release for 2020-2024).", "PLACES", "", "Missing for 2010-2014 and for tracts with no PLACES estimate."),
  ("places_totalpopulation", "Total population used by PLACES for the tract.", "PLACES", "", "From the PLACES file, not ACS."),
  ("places_totalpop18plus", "Adult (18+) population used by PLACES.", "PLACES", "", "Present only in the 2024 and 2025 releases."),
  ("has_places", "True where the tract has PLACES estimates in the paired release.", "DERIVED", "", ""),
  ("overlap_same_geoid", "For the tract with the same code in the other boundary vintage: the smaller of (intersection land area / 2020 tract land area) and (intersection / 2010 tract land area).", "TRACTREL", "", "Missing if the code does not exist in the other vintage. Land-area based, not population based."),
  ("boundary_stable_99", "True where overlap_same_geoid >= 0.99.", "TRACTREL", "", "Threshold is a choice; use overlap_same_geoid for another."),
  ("n_partner_tracts_other_vintage", "Number of tracts in the other boundary vintage that intersect this tract.", "TRACTREL", "", "")])
BANDS = "age band (16plus, 16_34, 35_64, 65plus)"; PUMS_CAV = "PUMS sample estimate. Not available for San Benito (shares its PUMA with part of Monterey County), for 2020 (no 1-year file), or after 2024."
D["county_year_panel.parquet"] = ("One row per county x year, 2010-2026 (255 rows). Key: county_fips + year. Sources differ in the years they cover; see the QC report coverage table.", ID + [
  ("year", "Calendar year.", "DERIVED", "", ""),
  ("zhvi_mean", "Zillow Home Value Index, mean of the monthly values in the year (dollars).", "ZILLOW", "2010-2026", "Smoothed, seasonally adjusted, mid-tier (33rd-67th percentile), single-family and condo. Nominal dollars. 2026 has 9 months."),
  ("zhvi_n_months", "Number of monthly ZHVI values averaged.", "ZILLOW", "", "Below 12 marks a partial year."),
  ("zori_mean", "Zillow Observed Rent Index, mean of the monthly values in the year (dollars per month).", "ZILLOW", "2015-2026", "Series starts 2015-01; 13 of 15 counties in 2015, all 15 from 2022. Smoothed, not seasonally adjusted."),
  ("zori_n_months", "Number of monthly ZORI values averaged.", "ZILLOW", "", ""),
  (r"re:pums_commuters_(16plus|16_34|35_64|65plus)", f"Weighted number of commuters (workers who did not work from home) in the {BANDS}.", "PUMS", "2010-2019, 2021-2024", PUMS_CAV),
  (r"re:pums_n_commuters_.+", "Unweighted number of commuter records behind the estimate.", "PUMS", "", ""),
  (r"re:pums_mean_commute_min_(16plus|16_34|35_64|65plus)", f"Mean travel time to work in minutes among commuters, by {BANDS}.", "PUMS", "2010-2019, 2021-2024", PUMS_CAV + " Travel time is top-coded in PUMS."),
  (r"re:pums_share_commute_(60|90)plus_(16plus|16_34|35_64|65plus)", "Share of commuters with travel time of 60 (or 90) minutes or more.", "PUMS", "2010-2019, 2021-2024", PUMS_CAV),
  (r"re:pums_share_drive_alone_workers_(16plus|16_34|35_64|65plus)", "Share of workers (including those working from home) who drove alone.", "PUMS", "2010-2019, 2021-2024", PUMS_CAV),
  (r"re:pums_share_wfh_workers_(16plus|16_34|35_64|65plus)", "Share of workers who worked from home.", "PUMS", "2010-2019, 2021-2024", PUMS_CAV + " Rises sharply from 2021."),
  (r"re:pums_pop_share_commute_60plus_(16plus|16_34|35_64|65plus)", "Share of ALL persons in the age band (workers or not) who commute 60 minutes or more; exposure prevalence for attributable-burden work.", "PUMS", "2010-2019, 2021-2024", PUMS_CAV),
  (r"re:pums_.+_se_.+", "Standard error of the PUMS estimate with the same name, from the 80 replicate weights (successive-difference replication: variance = 4/80 x sum of squared deviations).", "PUMS", "", ""),
  ("pums_available", "True where PUMS commute measures exist for the county-year.", "DERIVED", "", ""),
  ("acs5_acs_period", "ACS 5-year period whose county estimates are placed in this row (at the period end year).", "ACS5", "", "Present only in 2014, 2019, 2024."),
  (r"re:acs5_.+_moe", "90% margin of error of the ACS 5-year county estimate with the same name.", "ACS5", "", MOE),
  (r"re:acs5_.+", "ACS 5-year county estimate; definition as the same-named variable in tract_analysis.", "ACS5", "2010-2014, 2015-2019, 2020-2024", "Five-year pooled estimate placed at the period end year; the only commute source that includes San Benito."),
  (r"re:acs1_.+_moe", "90% margin of error of the ACS 1-year county estimate with the same name.", "ACS1", "2021-2025", MOE),
  ("acs1_available", "True where published ACS 1-year county estimates exist for the county-year (2021-2025, all 15 counties).", "DERIVED", "", ""),
  ("acs1_mean_commute_min", "Mean travel time to work in minutes from published 1-year county tables: B08013_001 / B08303_001.", "ACS1", "2021-2025", "County total for workers 16+ who did not work from home; NOT age-specific. Carries the series to 2025, a year with no PUMS file. Agrees with PUMS estimates within sampling error in 2021-2024 but is a different estimator; do not splice onto the age-band series."),
  (r"re:acs1_share_commute_(60|90)plus", "Share of commuters with travel time of 60 (or 90) minutes or more: B08303_012-013 (or 013) / 001, published 1-year county table.", "ACS1", "2021-2025", "Not age-specific."),
  ("acs1_share_drive_alone", "Share of all workers who drove alone: C08301_003 / 001.", "ACS1", "2021-2025", "From the collapsed table C08301 (identical to B08301 on shared cells; B08301 is withheld for some smaller counties). Not age-specific."),
  ("acs1_share_wfh", "Share of all workers who worked from home: C08301_011 / 001.", "ACS1", "2021-2025", "From C08301. Not age-specific."),
  (r"re:acs1_(commuters|workers)_total", "Commuters (B08303_001) / all workers 16+ (C08301_001), published 1-year county table.", "ACS1", "2021-2025", ""),
  (r"re:mort_(chd|cvd|hd|hf|stroke)_(35_64|65plus)", "Death rate per 100,000 for coronary heart disease (chd), cardiovascular disease (cvd), all heart disease (hd), heart failure (hf) or all stroke, ages 35-64 or 65+, all races, both sexes.", "MORT-A", "2010-2019 in this panel", "MODEL-SMOOTHED rate (age-standardized within the age band, spatiotemporally smoothed), not a raw count. Only two age bands exist; none under 35."),
  (r"re:mort_majorcvd_(35_64|65plus)", "Death rate per 100,000 for major cardiovascular disease, ages 35-64 or 65+.", "MORT-B", "2010-2020", "Model-smoothed (age-standardized, spatially smoothed). Different model and cause grouping from mort_cvd_*; do not splice the two."),
  (r"re:pooled3yr_(hd|stroke)_35plus", "Three-year pooled age-adjusted death rate per 100,000 for heart disease or stroke, all adults 35+, all races, both sexes, placed at the period midpoint year.", "MORT-P", "midpoints 2015-2020, 2022, 2023", "NOT by age group. Spatially smoothed. No 2020-2022 period published; the 2014-2016 label is inferred from the year field."),
  ("pooled3yr_period", "Three-year period of the pooled rate in this row.", "MORT-P", "", "")])
D["pums_commuters.parquet"] = ("One row per person aged 16+ living in a study-area PUMA, per survey year (1,243,780 rows). Key: year + serialno + sporder. Contains all persons 16+, not commuters only.", ID + [
  ("year", "ACS survey year.", "PUMS", "", "No 2020."), ("puma_vintage", "PUMA definition of the year: 2000 (2010-2011), 2010 (2012-2021), 2020 (2022-2024).", "PUMAGEO", "", "PUMA-level series break at 2012 and 2022."),
  ("puma", "5-digit PUMA of residence.", "PUMS", "", ""), ("puma_mixed_outside", "True for the PUMA that combines San Benito with part of Monterey County.", "PUMAGEO", "", "county_fips is missing for these rows; exclude from county estimates."),
  ("serialno", "Housing unit / group quarters serial number.", "PUMS", "", ""), ("sporder", "Person number within the household.", "PUMS", "", ""),
  ("agep", "Age in years.", "PUMS", "", "Top-coded by the Census Bureau."), ("sex", "Sex (1 male, 2 female).", "PUMS", "", ""),
  ("esr", "Employment status recode.", "PUMS", "", ""), ("cow", "Class of worker.", "PUMS", "", ""), ("schl", "Educational attainment.", "PUMS", "", "Codes changed over the years; see the PUMS data dictionary for each year."),
  ("rac1p", "Race recode.", "PUMS", "", ""), ("hisp", "Hispanic origin recode.", "PUMS", "", ""), ("jwrip", "Vehicle occupancy (1 drove alone, 2-10 carpool size).", "PUMS", "", ""),
  ("jwdp", "Time of departure for work, coded interval.", "PUMS", "", "Code list per year in the PUMS data dictionary."), ("jwap", "Time of arrival at work, coded interval.", "PUMS", "", ""),
  ("wkhp", "Usual hours worked per week.", "PUMS", "", ""), ("wk_raw", "Weeks worked in the past 12 months, as coded in the source variable named in wk_var.", "PUMS", "", "WKW (categories) through 2018; WKWN (number of weeks) from 2019. Not comparable without recoding."),
  ("wk_var", "Source variable for wk_raw (WKW or WKWN).", "PUMS", "", ""), ("jwmnp", "Travel time to work in minutes.", "PUMS", "", "Top-coded (observed maximum 141-146 by year). Missing for non-workers and people who worked from home."),
  ("jwtr_raw", "Means of transportation code as published.", "PUMS", "", "Codes 03-05 mean different rail modes before and after 2019; use mode_cat across years."), ("jwtr_scheme", "Source variable: JWTR (2010-2018) or JWTRNS (2019+).", "PUMS", "", ""),
  ("mode_cat", "Harmonized mode: car_alone, carpool, bus, rail, ferry, taxi, motorcycle, bicycle, walk, wfh, other.", "DERIVED", "", "Rail pools codes 03-05. Trolley bus moved from the bus code to the light-rail code in 2019."),
  ("worker_at_work", "True for workers in the journey-to-work universe (means of transportation reported).", "DERIVED", "", ""), ("wfh", "True if worked from home.", "DERIVED", "", ""),
  ("commuter", "True if a travel time is reported (worker who did not work from home).", "DERIVED", "", ""),
  ("powpuma", "Place-of-work PUMA code as published.", "PUMS", "", "A coarser unit than residence PUMAs, with its own coding; NOT mapped to counties here. Use with powsp."), ("powsp", "Place-of-work state or foreign country code.", "PUMS", "", ""),
  ("pincp", "Total person income, past 12 months (nominal dollars).", "PUMS", "", "Multiply by adjinc for dollars of the survey year."), ("wagp", "Wage or salary income.", "PUMS", "", ""), ("pernp", "Total person earnings.", "PUMS", "", ""),
  ("adjinc", "Income adjustment factor (published value divided by 1,000,000).", "PUMS", "", ""), ("pwgtp", "Person weight.", "PUMS", "", "Positive for every record."),
  (r"re:pwgtp\d+", "Replicate person weights 1-80 for variance estimation.", "PUMS", "", "A few replicate values are negative as published; do not clip.")])
D["pums_county_year_age.parquet"] = ("PUMS estimates by county (and three regional totals) x year x age band (2,142 rows). Key: county_fips + year + age_band.", ID + [
  ("year", "ACS survey year.", "PUMS", "", ""), ("is_region_total", "True for the rows CORE9, EXT5 (extended counties excluding San Benito) and ALL14.", "DERIVED", "", ""),
  ("age_band", "Age band: 16_24, 25_34, 35_44, 45_54, 55_64, 65plus, and the aggregates 16_34, 35_64, 16plus.", "DERIVED", "", "Aggregate bands overlap the fine bands; do not sum across them."),
  ("pop", "Weighted persons in the band.", "PUMS", "", ""), ("workers", "Weighted workers in the journey-to-work universe.", "PUMS", "", ""), ("commuters", "Weighted commuters (workers not working from home).", "PUMS", "", ""),
  ("mean_commute_min", "Mean travel time among commuters (minutes).", "PUMS", "", "Travel time is top-coded."), (r"re:share_commute_(45|60|90)plus", "Share of commuters with travel time at or above the threshold.", "PUMS", "", ""),
  ("share_drive_alone_workers", "Share of workers who drove alone.", "PUMS", "", ""), ("share_wfh_workers", "Share of workers who worked from home.", "PUMS", "", ""),
  ("pop_share_commute_60plus", "Share of all persons in the band commuting 60 minutes or more.", "PUMS", "", ""), ("pop_share_commuter", "Share of all persons in the band who are commuters.", "PUMS", "", ""),
  (r"re:.+_se", "Replicate-weight standard error of the same-named estimate.", "PUMS", "", ""), (r"re:n_(persons|workers|commuters)", "Unweighted record counts.", "PUMS", "", "Small counts mean unstable estimates."),
  ("puma_vintage", "PUMA definition in force that year.", "PUMAGEO", "", "")])
D["places_tract_long.parquet"] = ("All PLACES tract estimates for the study counties, every measure and release (484,120 rows). Key: release + tract_geoid + measureid.", ID + [
  ("release", "PLACES release year (2020-2025).", "PLACES", "", ""), ("data_year", "BRFSS survey year of the measure in that release.", "PLACES", "", "Each release mixes two years; consecutive releases repeat some measures (high blood pressure only odd years, short sleep only even years)."),
  ("tract_geoid", "11-digit census tract identifier.", "PLACES", "per tract_vintage", ""), ("tract_vintage", "Tract boundary vintage of the release (2010 for releases 2020-2023, 2020 for 2024-2025).", "DERIVED", "", "Determined by matching identifiers to ACS tract lists."),
  ("category", "PLACES measure category.", "PLACES", "", ""), ("measureid", "Measure code.", "PLACES", "", ""), ("measure", "Full measure wording.", "PLACES", "", ""), ("short_question_text", "Short measure label.", "PLACES", "", ""),
  ("data_value_type", "Type of estimate (crude prevalence at tract level).", "PLACES", "", ""), ("datavaluetypeid", "Code of the estimate type.", "PLACES", "", ""),
  ("data_value", "Estimate (percent).", "PLACES", "", PL_CAV), (r"re:(low|high)_confidence_limit", "95% confidence limits.", "PLACES", "", ""),
  (r"re:data_value_footnote(_symbol)?", "Footnote fields as published.", "PLACES", "", "Empty in the study-area rows."), ("totalpopulation", "Population used by PLACES.", "PLACES", "", ""), ("totalpop18plus", "Adult population used by PLACES.", "PLACES", "", "Releases 2024-2025 only.")])
D["mortality_long.parquet"] = ("All downloaded county mortality values for the study counties, every stratum and value type (32,970 rows).", ID + [
  ("dataset_id", "data.cdc.gov dataset identifier.", "MORT-A", "", "See series."), ("series", "age_stratified_1999_2019 (MORT-A), major_cvd_age_2010_2020 (MORT-B) or pooled_3yr_35plus (MORT-P).", "DERIVED", "", "The three series use different models; do not splice."),
  ("period", "Period as published: a year, a trend period, or the three-year window.", "MORT-A", "", ""), ("year", "Calendar year (annual rows) or midpoint year (pooled rows); missing for trend-period rows.", "DERIVED", "", ""),
  ("period_inferred", "True where the three-year window is inferred from the year field because the dataset title carries no period.", "DERIVED", "", "Applies to 2014-2016."),
  ("age_group", "35-64, 65+ or 35+ (pooled).", "MORT-A", "", "No finer bands and no ages under 35 are published. One source label for 65+ is garbled in the source and was normalized."),
  ("race", "Race/ethnicity stratum or Overall.", "MORT-A", "", "Categories differ between datasets."), ("sex", "Sex stratum or Overall.", "MORT-A", "", ""),
  ("topic_label", "Cause-of-death topic as published.", "MORT-A", "", ""), ("topic", "Short topic code (chd, hf, hd, cvd, stroke, majorcvd).", "DERIVED", "", ""),
  ("value_type", "Type of value as published (smoothed rate, predicted rate, rate ratio, rate difference, percent change).", "MORT-A", "", ""), ("unit", "Unit as published.", "MORT-A", "", ""),
  ("value", "Value.", "MORT-A", "", "Rates are MODEL-SMOOTHED age-standardized rates per 100,000, not counts."), (r"re:ci_(low|high)", "Confidence limits where published.", "MORT-A", "", "Not published for the pooled series."),
  ("footnote", "Footnote as published (for example value suppressed, insufficient data).", "MORT-A", "", ""), ("value_missing", "True where no value is published.", "DERIVED", "", "")])
D["tract_2010_2020_relationship.parquet"] = ("Every intersecting pair of 2020 and 2010 tracts where either tract is in the study area (4,058 rows).", [
  (r"re:tract_geoid_20(10|20)", "Tract identifier in that boundary vintage.", "TRACTREL", "", ""), (r"re:in_study_20(10|20)", "True where that tract lies in a study county.", "DERIVED", "", "For a tract outside the study area only its overlaps with study tracts are kept."),
  (r"re:area(land|water)_tract_(10|20)", "Land / water area of the tract (square metres).", "TRACTREL", "", ""), (r"re:area(land|water)_part", "Land / water area of the intersection.", "TRACTREL", "", ""),
  (r"re:share_of_20(10|20)_land", "Intersection land area as a share of that tract's land area.", "DERIVED", "", "Area weights, not population weights.")])
ZL = [("year", "Calendar year.", "ZILLOW", "", "2026 is partial (9 months)."), ("zhvi_mean", "Mean of monthly ZHVI values (dollars).", "ZILLOW", "2000-2026", "Smoothed, seasonally adjusted, mid-tier; nominal dollars."), ("zhvi_n_months", "Months averaged.", "ZILLOW", "", ""),
      ("zori_mean", "Mean of monthly ZORI values (dollars per month).", "ZILLOW", "2015-2026", "Series starts 2015-01."), ("zori_n_months", "Months averaged.", "ZILLOW", "", "")]
D["zillow_county_annual.parquet"] = ("County x year Zillow indices, 2000-2026 (405 rows).", ID + ZL)
D["zillow_zip_annual.parquet"] = ("ZIP x year Zillow indices (11,190 rows; 415 ZIP codes).", ID + [("zip", "5-digit ZIP code.", "ZILLOW", "", "Assigned to one county by Zillow's county name field.")] + ZL)
D["road_rage_proxy_counts.csv"] = ("County x year crash counts by constructed indicator group, 2016-2026 (165 rows). Descriptive context only; see road_rage_proxy_assessment.md.", ID + [
  ("year", "Crash year.", "CCRS", "", "2026 partial."), (r"re:(following_too_closely|reckless_or_speed_contest|signal_or_stop_sign|unsafe_lane_change|unsafe_passing|unsafe_speed|unsafe_turn_or_signal|other_or_none)", "Crashes whose primary collision factor violation falls in the group.", "CCRS", "2016-2026", "Analyst-defined grouping of Vehicle Code sections; county is place of crash."),
  ("all_crashes", "All crashes recorded in the county.", "CCRS", "", ""), ("narrow_composite", "Sum of unsafe speed, following too closely, unsafe lane change, unsafe passing, reckless or speed contest.", "DERIVED", "", "72-76% is unsafe speed (basic speed law)."),
  ("hit_and_run", "Crashes flagged felony or misdemeanor hit-and-run.", "CCRS", "", ""), ("pop_vintage", "ACS period of the population denominator.", "ACS5", "", ""), ("population", "County population used as denominator.", "ACS5", "", "Approximate: 2015-2019 for crash years to 2019, 2020-2024 afterwards."),
  ("narrow_pct_of_crashes", "narrow_composite as a percentage of all_crashes.", "DERIVED", "", ""), (r"re:(narrow|crashes)_per_100k_pop", "Count per 100,000 residents.", "DERIVED", "", "Rough scale adjustment only.")])
D["puma_county_map.csv"] = ("PUMA-to-county lookup for the three PUMA definitions (243 rows).", ID + [("puma_vintage", "PUMA definition (2000, 2010, 2020).", "PUMAGEO", "", ""), ("pums_years", "PUMS years using the definition.", "PUMAGEO", "", ""), ("puma", "5-digit PUMA.", "PUMAGEO", "", ""),
  ("n_counties", "Number of counties the PUMA touches.", "PUMAGEO", "", ""), ("puma_mixed_outside", "True where the PUMA includes a county outside the study area.", "PUMAGEO", "", "One PUMA per definition (San Benito + part of Monterey)."),
  ("mixed_detail", "Description of the mixed PUMA.", "DERIVED", "", ""), ("san_benito_share", "San Benito's share of the mixed PUMA's population.", "PUMAGEO", "", "30.6%, 41.8%, 44.7% by definition.")])
D["acs5_cells.parquet"] = ("Cell-level ACS 5-year values for the 12 tables: one row per geography x vintage, tract and county rows (7,113 rows). Key: GEO_ID + acs_vintage. Use acs5_cell_labels.csv for the meaning of each cell.", ID + [
  ("GEO_ID", "Census geographic identifier (1400000US + tract, 0500000US + county).", "ACS5", "", "Harmonized to this form for all vintages."), ("geoid", "FIPS part of GEO_ID (11 digits for tracts, 5 for counties).", "ACS5", "", ""),
  ("sumlevel", "Summary level: 140 tract, 050 county.", "ACS5", "", ""), ("acs_vintage", "End year of the ACS 5-year period.", "ACS5", "", ""), ("acs_period", "ACS 5-year period.", "ACS5", "", ""),
  ("tract_vintage", "Tract boundary vintage (tract rows only).", "ACS5", "", ""),
  (r"re:B\d{5}_E\d{3}", "Published estimate for the table cell.", "ACS5", "per acs_period", "Jam values set to missing. Medians can be top-coded (cap plus one). Public-transport sub-mode cells B08301_011-016 changed meaning between vintages."),
  (r"re:B\d{5}_M\d{3}", "Published 90% margin of error for the table cell.", "ACS5", "per acs_period", "Jam values set to missing.")])
D["acs5_cell_labels.csv"] = ("Label of every table cell in each vintage, from Census API metadata (672 rows).", [
  ("table", "ACS table.", "ACS5", "", ""), ("cell", "Cell number within the table.", "ACS5", "", ""), (r"re:(estimate|moe)_column", "Matching column name in acs5_cells.parquet.", "DERIVED", "", ""),
  ("acs_vintage", "Vintage the label applies to.", "ACS5", "", ""), ("label", "Cell label as published.", "ACS5", "", ""), ("concept", "Table title as published.", "ACS5", "", ""),
  ("label_differs_across_vintages", "True where the cell's label is not the same in all three vintages.", "DERIVED", "", "Nine cells: public-transport sub-modes, taxi, worked from home (wording), and the dollar year of median income.")])
D["study_counties.csv"] = ("The 15 study counties (15 rows).", ID + [("state_fips", "State FIPS (06).", "ACS5", "", ""), ("geo_id", "Census geographic identifier.", "ACS5", "", ""), ("county_geoid", "5-digit state + county FIPS.", "ACS5", "", "")])

def columns(f):
    if f.endswith(".parquet"): return pq.ParquetFile(f).schema.names
    return list(pd.read_csv(f if os.path.exists(f) else os.path.join("ref", f), nrows=1).columns)

if __name__ == "__main__":
    out = ["# Data dictionary", "", f"Generated {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')} (UTC) by `build_data_dictionary.py`. Study area: 15 California counties; `core9` marks the nine Bay Area counties on every table.", "",
           "## Read first", "",
           "1. **PLACES outcomes are model-based and not age-specific.** Every PLACES value (the `*_prev` columns and `places_tract_long.parquet`) is a model-based small-area estimate, not a direct survey measurement. CDC derives it by multilevel regression and poststratification of BRFSS responses, so the estimate for a tract is built partly from demographic predictors (the tract's population composition and area characteristics). Associations between PLACES prevalence and tract demographics are therefore partly built in by construction. Tract values are crude prevalences for all adults aged 18 and over; there are no age-specific or age-adjusted tract estimates, so they cannot support age-stratified outcome analysis. (Method description per CDC PLACES documentation; not re-verified from the methodology page in this work.)",
           "2. **Mortality rates are model-smoothed**, age-standardized within two age bands only (35-64 and 65+), and end in 2019 (five topics) or 2020 (major cardiovascular disease). They are not death counts.",
           "3. **Tract boundaries are native to each cross-section** (2010 tracts for 2010-2014 and 2015-2019; 2020 tracts for 2020-2024). Nothing was interpolated.",
           "4. **Dollar amounts are nominal.**",
           "5. **How current each source is.** Person-level PUMS data end in 2024 (the 2025 file was not published when checked), so age-specific commute measures end in 2024. The 2025 commute values are the `acs1_*` columns: published county totals, not age-specific. Tract tables end with ACS 2020-2024; PLACES with the 2025 release (BRFSS 2023); mortality by age with 2019/2020; Zillow with September 2026. See the Source currency section of `data_qc_report.md` for what was checked and when.", "6. **ACS came from Census bulk summary files**, not the API (the API requires a key); the estimates and margins of error are the published ones.", "",
           "## Reproducing", "", "Run from the workspace root, in this order: `build_geography.py`; `acquire_acs_tablebased.py 2024`; `acquire_acs1_county.py`; `acquire_acs_sequence.py 2014`; `acquire_acs_sequence.py 2019`; `acquire_pums.py`; `acquire_zillow.py`; `acquire_cdc_places.py`; `acquire_cdc_mortality.py`; `acquire_ccrs.py`; `build_road_rage_proxy.py`; `build_analysis_datasets.py`; `check_currency.py`; `run_qc.py`; `build_data_dictionary.py`. Sources are live and are revised by their publishers, so a later run can return different values.", "",
           "## Sources", "", "| id | source | URL | vintage | downloaded (UTC) | script |", "|---|---|---|---|---|---|"]
    out += [f"| {k} | {d} | {u} | {v} | {dt} | {s} |" for k, (d, u, v, dt, s) in SRC.items()]
    n_cols = n_rows = 0
    for f, (desc, rows) in D.items():
        cols = columns(f); used = set(); out += ["", f"## {f}", "", desc, "", "| variable | definition | source | vintage | downloaded (UTC) | caveats |", "|---|---|---|---|---|---|"]
        for name, definition, src, vint, cav in rows:
            if name.startswith("re:"):
                hit = [c for c in cols if c not in used and re.fullmatch(name[3:], c)]; shown = "`" + name[3:].replace("|", "/") + "` (" + str(len(hit)) + " columns)"
            else:
                hit = [c for c in cols if c == name and c not in used]; shown = f"`{name}`"
            if not hit: continue            # entry does not apply to this file (shared identifier rows)
            used.update(hit); n_rows += 1
            out.append(f"| {shown} | {definition} | {src} | {vint or SRC[src][2]} | {SRC[src][3]} | {cav} |")
        missing = [c for c in cols if c not in used]
        assert not missing, f"{f}: undocumented columns {missing}"
        n_cols += len(cols)
    open("data_dictionary.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("files", len(D), "| columns documented", n_cols, "| dictionary rows", n_rows, "| chars", sum(map(len, out)))
