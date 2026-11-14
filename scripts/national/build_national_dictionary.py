"""Write national_data_dictionary.md for national_county.parquet and national_mortality_annual.parquet.
Every column must match exactly one rule below (asserted). Usage: python build_national_dictionary.py"""
import re, json, datetime, pandas as pd

d = pd.read_parquet("national_county.parquet"); a = pd.read_parquet("national_mortality_annual.parquet")
acslog = pd.read_csv("raw/acs_nat/acs5_nat_download_log.csv"); mlog = pd.read_csv("raw/mortality_nat/mortality_nat_download_log.csv")
rlog = pd.read_csv("raw/ref_nat/ref_download_log.csv"); plog = pd.read_csv("raw/places_nat/places_nat_download_log.csv")
day = lambda s: str(s)[:10]
SRC = {
 "ACS5": ("American Community Survey 5-year detailed tables, county level (summary level 050), estimates and 90% margins of error, from the sequence-based summary files", "https://www2.census.gov/programs-surveys/acs/summary_file/{2010,2014,2019}/data/5_year_seq_by_state/<State>/All_Geographies_Not_Tracts_Block_Groups/", "2006-2010, 2010-2014, 2015-2019", day(acslog.downloaded_utc.max())),
 "MORT": ("CDC, Rates and Trends in Heart Disease and Stroke Mortality Among US Adults (35+) by County, Age Group, Race/Ethnicity, and Sex, 2000-2019 (National Vital Statistics System); dataset 7b9s-s8ck, race = Overall", "https://data.cdc.gov/resource/7b9s-s8ck", "annual 1999-2019", day(mlog.downloaded_utc.max())),
 "NCHS": ("NCHS Urban-Rural Classification Scheme for Counties, 2013 and 2006 codes (file NCHSURCodes2013-Past-Version.xlsx)", "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/OAE/urbanrural/NCHSURCodes2013-Past-Version.xlsx", "2013 scheme (2010 census, February 2013 OMB delineation); 2006 scheme", day(rlog.downloaded_utc.max())),
 "CBSA": ("OMB core based statistical area delineation files (Census Bureau copies), List 1", "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2013/delineation-files/list1.xls ; https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2018/delineation-files/list1_Sep_2018.xls", "February 2013; September 2018", day(rlog.downloaded_utc.max())),
 "GAZ": ("Census Gazetteer county files", "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/ (Gaz_counties_national.zip [2010], 2014_Gazetteer/2014_Gaz_counties_national.zip, 2019_Gazetteer/2019_Gaz_counties_national.zip)", "2010, 2014, 2019", day(rlog.downloaded_utc.max())),
 "URB": ("Census 2010 percent urban and rural by county", "https://www2.census.gov/geo/docs/reference/ua/PctUrbanRural_County.xls", "2010 Census", day(rlog.downloaded_utc.max())),
 "PLACES20": ("CDC PLACES county data, 2020 release (GIS-friendly file mssc-ksj7; data years from dv4u-3x3q)", "https://data.cdc.gov/resource/mssc-ksj7", "BRFSS 2018 (2017 for high blood pressure and high cholesterol)", day(plog.downloaded_utc.max())),
 "PLACES21": ("CDC PLACES county data, 2021 release (pqpp-u99h)", "https://data.cdc.gov/resource/pqpp-u99h", "BRFSS 2019 (2018 for short sleep); no New Jersey", day(plog.downloaded_utc.max())),
 "DERIVED": ("Derived in build_national_dataset.py from the sources named in the definition", "", "", ""),
}
PL = "MODEL-BASED small-area estimate (multilevel regression and poststratification of BRFSS), built partly from county demographic and socioeconomic predictors, so associations with those predictors are partly built in. All adults 18+; not age-specific. TIME-INVARIANT in this file: the same value is repeated on all three period rows and is contemporaneous with 2015-2019 only."
MEAS = {"csmoking": "current cigarette smoking", "obesity": "obesity (BMI >= 30)", "diabetes": "diagnosed diabetes", "lpa": "no leisure-time physical activity", "bphigh": "high blood pressure", "highchol": "high cholesterol among adults screened",
        "binge": "binge drinking", "sleep": "short sleep duration (< 7 hours)", "access2": "no health insurance among adults 18-64", "chd": "coronary heart disease (ever told)", "stroke": "stroke (ever told)"}
TOP = {"cvd": "all cardiovascular disease", "hd": "all heart disease", "chd": "coronary heart disease", "stroke": "all stroke", "hf": "heart failure"}
AG = {"35_64": "ages 35-64", "65plus": "ages 65+"}
MODE = {"car": "car, truck or van (drove alone + carpooled)", "drivealone": "car, truck or van, drove alone", "transit": "public transportation (excluding taxicab)", "all": "all modes"}
MORTCAV = "MODEL-SMOOTHED rate: age-standardized within the age band (10-year age groups, 2010 US population) and smoothed over space, time and demographic group by a Bayesian spatiotemporal model. Not a death count; neighbouring counties and adjacent years are not independent. Only two age bands exist."
MOE = "90% margin of error. Census approximation formulas (root sum of squares for sums; proportion/ratio formulas); approximate, overstated when many cells are summed."
MIDDEF = "bin-midpoint minutes from the mode-by-travel-time table (B08134; C08134 in 2006-2010; midpoints 5, 12, 17, 22, 27, 32, 39.5, 52; 60+ bin = 75 min car / 80 min transit) scaled so that car + transit + other modes equal the county's published all-mode aggregate (B08013)"

def m(mode): return MODE[mode]
RULES = [   # (regex, definition, source, vintage, caveats)  - definition/caveat may be a function of the match
 (r"fips", "5-digit state + county FIPS code of the analysis unit (CDC mortality county unit).", "DERIVED", "", "3,136 units. 02901 and 02902 are combined south-east Alaska units; 51019 includes Bedford city; 46102 and 02158 carry the post-2015 codes in every period. See national_county_crosswalk.csv."),
 (r"period", "ACS 5-year period: 2006-2010, 2010-2014 or 2015-2019.", "DERIVED", "", "2006-2010 and 2010-2014 share the year 2010; use 2006-2010 vs 2015-2019 for non-overlapping change."),
 (r"acs_vintage", "End year of the ACS period (2010, 2014, 2019). Key together with fips.", "ACS5", "", ""),
 (r"county_name", "County name from the ACS geography file (combined units: descriptive name).", "ACS5", "per period", ""),
 (r"county_name_acs", "Same as county_name (kept for traceability).", "ACS5", "per period", ""),
 (r"county_name_cdc", "County name in the CDC mortality file.", "MORT", "", ""),
 (r"state_fips", "2-digit state FIPS code.", "DERIVED", "", ""),
 (r"state_abbr", "State postal abbreviation.", "GAZ", "per period", ""),
 (r"census_(region|division)", lambda g: f"Census {g[0]} of the state.", "DERIVED", "", "Standard Census Bureau grouping of states, coded in the build script."),
 (r"n_acs_components", "Number of ACS counties summed into the unit in this period.", "DERIVED", "", ""),
 (r"unit_aggregated", "True where the unit is built from more than one ACS county in this period.", "DERIVED", "", "7 rows: Bedford (2006-2010) and the two Alaska units (all periods)."),
 (r"acs_component_geoids", "ACS county codes behind the unit in this period (semicolon-separated).", "ACS5", "per period", ""),
 (r"fips_note", "Explanation of the recode or merge, where one applies.", "DERIVED", "", ""),
 (r"in_acs|in_cdc_mortality", "True where the unit has ACS data / exists in the CDC mortality series.", "DERIVED", "", ""),
 (r"pop_total", "Total population (B01001_001).", "ACS5", "per period", ""),
 (r"pop_(u18|18_34|35_64|65plus|45_64)", lambda g: f"Population in the age band {g[0].replace('u18', 'under 18').replace('_', '-').replace('plus', '+')} (sum of B01001 sex-by-age cells).", "ACS5", "per period", ""),
 (r"pop_18plus", "Residents aged 18 and over (B01001_001 minus the under-18 cells).", "ACS5", "per period", "Adult-resident denominator (alternative)."),
 (r"pop_16plus", "Residents aged 16 and over (B23001_001).", "ACS5", "per period", "PRIMARY adult-resident denominator; same age universe as the commuting questions."),
 (r"share_age_(under18|18_34|35_64|65plus)", lambda g: f"Share of population in the age band {g[0]}.", "ACS5", "per period", "Share in 0-1."),
 (r"share_female", "Share of population that is female (B01001_026 / 001).", "ACS5", "per period", "Share in 0-1."),
 (r"workers_total", "Workers aged 16+ (B08301_001), including those who worked from home.", "ACS5", "per period", ""),
 (r"commuters_total", "Workers aged 16+ who did not work from home (B08303_001); universe of the travel-time tables.", "ACS5", "per period", ""),
 (r"workers_per_adult16", "workers_total / pop_16plus.", "ACS5", "per period", ""),
 (r"share_(car|drive_alone|carpool|transit|bike|walk|wfh)", lambda g: "Share of all workers (B08301_001) who " + {"car": "used a car, truck or van (drove alone or carpooled; B08301_002)", "drive_alone": "drove alone (B08301_003)", "carpool": "carpooled (B08301_004)", "transit": "used public transportation (B08301_010)", "bike": "bicycled (B08301_018)", "walk": "walked (B08301_019)", "wfh": "worked from home (B08301_021)"}[g[0]] + ".", "ACS5", "per period", "Share in 0-1."),
 (r"share_drive_alone_commuters", "Share of commuters (workers excluding those working from home) who drove alone.", "ACS5", "per period", "Share in 0-1."),
 (r"share_commute_(45plus|60plus|90plus|lt15)", lambda g: f"Share of commuters, all modes, with one-way travel time {g[0].replace('plus', ' minutes or more').replace('lt15', 'under 15 minutes')} (B08303).", "ACS5", "per period", "Share in 0-1."),
 (r"all_agg_min_pub", "Published aggregate one-way travel time to work, all modes, minutes (B08013_001).", "ACS5", "per period", "Published for every county; the scaling target of the by-mode estimates."),
 (r"all_agg_pub_suppressed", "True where B08013_001 is not published.", "DERIVED", "", "False in every row."),
 (r"mean_tt_all_pub", "Published mean one-way travel time, all modes, minutes: B08013_001 / B08303_001 (the ACS definition of mean travel time to work).", "ACS5", "per period", ""),
 (r"mean_tt_all_midraw", "Mean one-way travel time, all modes, from UNSCALED bin midpoints (60+ bin at 75/80 minutes).", "ACS5", "per period", "QC quantity only; compare with mean_tt_all_pub. Not used in the exposure."),
 (r"rake_factor", "all_agg_min_pub divided by the unscaled bin-midpoint minutes of all modes: the county scaling factor applied to the by-mode midpoint minutes.", "DERIVED", "per period", "Below 1 in most counties because reported times heap at the lower bin bounds, so midpoints overstate."),
 (r"agg_scaled_with_median_factor", "True where the all-mode aggregate (B08013) is withheld and the by-mode midpoint minutes were scaled by the period median rake factor instead of the county's own.", "DERIVED", "", "One row: Loving County TX, 2015-2019."),
 (r"all_min_per_day_per_adult16", "2 x all_agg_min_pub / pop_16plus: commute minutes per commuting day per adult resident, all modes.", "ACS5", "per period", ""),
 (r"all_hours_wk_per_adult16", "Weekly commute hours per adult resident, all modes: 2 x all_agg_min_pub x 4.5 / 60 / pop_16plus.", "ACS5", "per period", "Assumes 4.5 commute days per week."),
 (r"(car|drivealone|transit)_commuters", lambda g: f"Commuters by {m(g[0])} (total cell of the mode block of B08134 / C08134).", "ACS5", "per period", ""),
 (r"(car|drivealone|transit)_agg_min_mid", lambda g: f"PRIMARY estimate of aggregate one-way minutes by {m(g[0])}: {MIDDEF}.", "ACS5", "per period", "Available for every county. Agreement with the published aggregate where it exists is in the QC report (car: r > 0.999). Transit values in counties with few transit commuters are noisy."),
 (r"(car|drivealone|transit)_agg_min_midraw", lambda g: f"UNSCALED bin-midpoint aggregate minutes by {m(g[0])}.", "ACS5", "per period", "Transparency/QC only; overstates in most counties."),
 (r"(car|drivealone|transit)_agg_min_pub", lambda g: f"Published aggregate one-way minutes by {m(g[0])} (B08136; C08136 in 2006-2010, where car = drove alone + carpooled).", "ACS5", "per period", "SUPPRESSED by the Census Bureau for many small counties (see *_agg_pub_suppressed and the QC report)."),
 (r"(car|drivealone|transit)_agg_pub_suppressed", lambda g: f"True where the published aggregate for {m(g[0])} is not available.", "DERIVED", "", ""),
 (r"mean_tt_(car|drivealone|transit)_mid", lambda g: f"Mean one-way travel time of commuters by {m(g[0])}, minutes: primary aggregate / commuters.", "ACS5", "per period", "Missing where the county has no commuters by this mode."),
 (r"mean_tt_(car|drivealone|transit)_pub", lambda g: f"Mean one-way travel time by {m(g[0])} from the published aggregate.", "ACS5", "per period", "Missing where suppressed."),
 (r"share_(car|drivealone|transit)_commuters_(45|60)plus", lambda g: f"Share of commuters by {m(g[0])} with one-way travel time of {g[1]} minutes or more.", "ACS5", "per period", "Share in 0-1; missing where no commuters by this mode."),
 (r"(car|drivealone|transit)_commuters_per_adult16", lambda g: f"Commuters by {m(g[0])} per resident aged 16+.", "ACS5", "per period", ""),
 (r"(car|drivealone|transit)_commuters_(45|60)plus_per_adult16", lambda g: f"Commuters by {m(g[0])} travelling {g[1]}+ minutes one way, per resident aged 16+ (population prevalence of long commutes by this mode).", "ACS5", "per period", ""),
 (r"(car|drivealone|transit)_min_per_day_per_adult16(_pub)?", lambda g: f"2 x aggregate one-way minutes by {m(g[0])} / pop_16plus: minutes per commuting day per adult resident ({'published aggregate' if g[1] else 'primary estimate'}). Multiply by commute days / 60 for weekly hours.", "ACS5", "per period", lambda g: "Missing where suppressed." if g[1] else "Days-free component of the exposure."),
 (r"(car|drivealone|transit)_hours_wk_per_adult(16|18)(_pub)?", lambda g: f"{'PRIMARY EXPOSURE. ' if (g[0] in ('car', 'transit') and g[1] == '16' and not g[2]) else ''}Weekly commute hours by {m(g[0])} per resident aged {g[1]}+: 2 x aggregate one-way minutes x 4.5 / 60 / pop_{g[1]}plus, using the {'published aggregate' if g[2] else 'primary (scaled midpoint) estimate'}.", "ACS5", "per period", lambda g: ("Missing where suppressed. " if g[2] else "") + "Assumes 2 trips per day and 4.5 commute days per week for every commuter; averaged over ALL adult residents, workers or not. Car includes carpool passengers. Ecological exposure: says nothing about which residents drive."),
 (r"(car|drivealone|transit)_hours_wk_per_commuter", lambda g: f"Weekly commute hours per commuter by {m(g[0])}: 2 x mean_tt_{g[0]}_mid x 4.5 / 60.", "ACS5", "per period", "Intensity among commuters; missing where no commuters by this mode."),
 (r"commute_days_assumed", "Assumed commute days per week (4.5).", "DERIVED", "", "Constant."),
 (r"top_bin_minutes_(car|transit)", lambda g: f"Assumed mean minutes of the open-ended 60+ bin for {g[0]} (75 car, 80 transit).", "DERIVED", "", "Constant."),
 (r"(workers|car_workers|transit_workers)_(45_64|65plus|16_44)", lambda g: f"{ {'workers': 'Workers', 'car_workers': 'Workers commuting by car, truck or van (drove alone + carpooled)', 'transit_workers': 'Workers commuting by public transportation'}[g[0]] } aged {g[1].replace('_', '-').replace('plus', '+')} (B08101).", "ACS5", "per period", "B08101 age bands are 16-19, 20-24, 25-44, 45-54, 55-59, 60-64, 65+; a 35-64 band cannot be formed."),
 (r"(car_worker|transit_worker|worker)_share_pop_(45_64|65plus)", lambda g: f"{ {'car_worker': 'Car commuters', 'transit_worker': 'Transit commuters', 'worker': 'Workers'}[g[0]] } aged {g[1].replace('_', '-').replace('plus', '+')} divided by residents of the same age (B08101 / B01001).", "ACS5", "per period", "Age-specific exposure prevalence; 45-64, not 35-64."),
 (r"median_hh_income", "Median household income (B19013_001), nominal dollars of income_dollar_year.", "ACS5", "per period", "Not inflation-adjusted across periods. Multi-county units: household-weighted mean of component medians (median_approx)."),
 (r"income_dollar_year", "Year of the dollars of median_hh_income.", "ACS5", "", ""),
 (r"median_home_value", "Median value of owner-occupied housing units (B25077_001), nominal dollars.", "ACS5", "per period", "Top-coded at 1,000,001 (2006-2010) / 2,000,001 (later). Missing for Kalawao County HI. Multi-county units: weighted mean (median_approx)."),
 (r"median_approx", "True where medians are weighted means of component-county medians.", "DERIVED", "", ""),
 (r"median_home_value_topcoded", "True where median_home_value equals the top code.", "DERIVED", "", ""),
 (r"poverty_rate", "Share of the poverty-status universe below the poverty level (B17001_002 / 001).", "ACS5", "per period", "Share in 0-1."),
 (r"share_bachelors_plus", "Share of population 25+ with a bachelor's degree or higher (B15002).", "ACS5", "per period", "Share in 0-1. B15002 is used because B15003 does not exist in 2006-2010."),
 (r"share_less_than_hs", "Share of population 25+ without a high school diploma or equivalent (B15002).", "ACS5", "per period", "Share in 0-1."),
 (r"share_(nh_white|nh_black|nh_aian|nh_asian|hispanic)", lambda g: "Share of population: " + {"nh_white": "non-Hispanic White alone", "nh_black": "non-Hispanic Black alone", "nh_aian": "non-Hispanic American Indian / Alaska Native alone", "nh_asian": "non-Hispanic Asian alone", "hispanic": "Hispanic or Latino"}[g[0]] + " (B03002).", "ACS5", "per period", "Share in 0-1."),
 (r"unemployment_rate", "Unemployed / civilian labor force, ages 16+ (sum of B23001 cells).", "ACS5", "per period", "Share in 0-1. Identical to B23025 where that table exists."),
 (r"unemployment_rate_b23025", "Unemployment rate from B23025 (005 / 003).", "ACS5", "2010-2014, 2015-2019", "Check column; B23025 does not exist in 2006-2010."),
 (r"labor_force_participation", "(Employed + unemployed + armed forces) / pop_16plus (B23001).", "ACS5", "per period", "Share in 0-1."),
 (r"share_uninsured", "Share of the civilian noninstitutionalized population without health insurance (B27001).", "ACS5", "2010-2014, 2015-2019", "MISSING for 2006-2010: the insurance question started in 2008 and B27001 is not in the 2006-2010 file."),
 (r"share_uninsured_18_64", "Share uninsured among ages 18-64 (2010-2014) or 19-64 (2015-2019) (B27001).", "ACS5", "2010-2014, 2015-2019", "MISSING for 2006-2010. The youngest adult band changed from 18-24 to 19-25 between vintages (uninsured_18_64_youngest_age)."),
 (r"uninsured_18_64_youngest_age", "Lower age bound of share_uninsured_18_64 in this vintage (18 or 19).", "DERIVED", "", ""),
 (r"households_total", "Occupied housing units (B25044_001).", "ACS5", "per period", ""),
 (r"share_no_vehicle_hh", "Share of occupied housing units with no vehicle available (B25044_003 + 010 / 001).", "ACS5", "per period", "Share in 0-1."),
 (r"share_owner_occupied", "Share of occupied housing units that are owner-occupied (B25044_002 / 001).", "ACS5", "per period", "Share in 0-1."),
 (r"land_area_sqmi", "Land area in square miles (Gazetteer ALAND_SQMI; summed for multi-county units).", "GAZ", "Gazetteer of the period end year", ""),
 (r"gaz_n", "Number of Gazetteer counties summed into the unit.", "GAZ", "", ""),
 (r"intpt_(lat|lon)", lambda g: f"Internal point {'latitude' if g[0] == 'lat' else 'longitude'} (largest component for multi-county units).", "GAZ", "Gazetteer of the period end year", ""),
 (r"pop_density", "pop_total / land_area_sqmi (persons per square mile).", "DERIVED", "per period", "Very skewed; consider the logarithm."),
 (r"nchs_ur_(2013|2006)", lambda g: f"NCHS Urban-Rural Classification code, {g[0]} scheme: 1 large central metro, 2 large fringe metro, 3 medium metro, 4 small metro, 5 micropolitan, 6 noncore.", "NCHS", "", "Time-invariant in this file. Multi-county units take the code of the most populous component."),
 (r"nchs_ur_2013_label", "Label of nchs_ur_2013.", "NCHS", "", ""),
 (r"metro_2013", "True where nchs_ur_2013 is 1-4 (metropolitan).", "NCHS", "", ""),
 (r"cbsa_code_(2013|2018)", lambda g: f"CBSA code of the county, {'February 2013' if g[0] == '2013' else 'September 2018'} delineation.", "CBSA", "", "Missing for counties outside any CBSA. Time-invariant in this file."),
 (r"cbsa_title_(2013|2018)", "CBSA title.", "CBSA", "", ""),
 (r"cbsa_type_(2013|2018)", "Metropolitan, Micropolitan or None.", "CBSA", "", ""),
 (r"cbsa_central_outlying_(2013|2018)", "Central or Outlying county of the CBSA.", "CBSA", "", ""),
 (r"csa_code_(2013|2018)", "Combined statistical area code, where the CBSA belongs to one.", "CBSA", "", ""),
 (r"pct_urban_2010", "Percent of the 2010 Census population living in urban areas.", "URB", "2010", "Time-invariant."),
 (r"pop_census_2010", "2010 Census population (from the percent-urban file).", "URB", "2010", ""),
 (r"places_r2020_(\w+?)_(aa|crude)", lambda g: f"PLACES 2020 release: {MEAS[g[0]]} among adults, percent, {'age-adjusted' if g[1] == 'aa' else 'crude'} prevalence. BRFSS {'2017' if g[0] in ('bphigh', 'highchol') else '2018'}.", "PLACES20", "", lambda g: PL + (" chd and stroke are OUTCOME-like measures, not confounders." if g[0] in ("chd", "stroke") else "")),
 (r"places_r2020_(\w+?)_aa_(lo|hi)", lambda g: f"{'Lower' if g[1] == 'lo' else 'Upper'} 95% confidence limit of places_r2020_{g[0]}_aa.", "PLACES20", "", "Model-based interval; population-weighted mean of limits for multi-county units (approximate)."),
 (r"places_r2020_n_components", "Number of PLACES counties averaged into the unit (population weights).", "PLACES20", "", ""),
 (r"places_r2021_(\w+?)_(aa|crude)", lambda g: f"PLACES 2021 release: {MEAS[g[0]]} among adults, percent, {'age-adjusted' if g[1] == 'aa' else 'crude'} prevalence. BRFSS {'2018' if g[0] == 'sleep' else '2019'}.", "PLACES21", "", lambda g: PL + (" Missing for the 21 New Jersey counties (no usable 2019 BRFSS data)." if g[0] != "sleep" else "")),
 (r"has_places_r(2020|2021)", lambda g: f"True where the unit has PLACES {g[0]} release estimates.", "DERIVED", "", ""),
 (r"mort_mid_year", "Middle year of the period (2008, 2012, 2017) used for the *_midyear mortality columns.", "DERIVED", "", ""),
 (r"mort_(cvd|hd|chd|stroke|hf)_(35_64|65plus)(_men|_women)?", lambda g: f"Death rate per 100,000 for {TOP[g[0]]}, {AG[g[1]]}, {'both sexes' if not g[2] else g[2][1:]}, all races: MEAN of the five annual rates of the period.", "MORT", "same five years as the ACS period", lambda g: MORTCAV + " Missing unless all five annual values are published."),
 (r"mort_(cvd|hd|chd|stroke|hf)_(35_64|65plus)(_men|_women)?_midyear", lambda g: f"Annual death rate per 100,000 for {TOP[g[0]]}, {AG[g[1]]}, {'both sexes' if not g[2] else g[2][1:]}, in the middle year of the period.", "MORT", "2008, 2012, 2017", MORTCAV),
 (r"mort_(cvd|hd|chd|stroke|hf)_(35_64|65plus)_midyear_(lo|hi)", lambda g: f"Published {'lower' if g[2] == 'lo' else 'upper'} confidence limit of the mid-year rate.", "MORT", "2008, 2012, 2017", "Model-based (credible) interval as published."),
 (r"mort_(cvd|hd|chd|stroke|hf)_(35_64|65plus)_n_years", "Number of published (non-suppressed) annual rates in the period (0-5).", "MORT", "", ""),
 (r"complete_case_main", "True where the primary exposures, CVD mortality in both age bands and the core covariates are all present (list in the QC report).", "DERIVED", "", ""),
 (r"complete_case_main_places", "complete_case_main and the four PLACES 2020 release risk-factor estimates present.", "DERIVED", "", "PLACES is contemporaneous with 2015-2019 only."),
 (r"(.+)_moe", lambda g: f"Margin of error of `{g[0]}`.", "ACS5", "per period", MOE + " Missing for medians of multi-county units."),
]
ARULES = [
 ("fips", "Analysis unit (see national_county.parquet).", "MORT", "", ""), ("state_abbr", "State postal abbreviation as published.", "MORT", "", ""), ("county_name_cdc", "County name as published.", "MORT", "", ""),
 ("year", "Calendar year, 1999-2019.", "MORT", "", "1999 is included as published; the requested range was 2000-2019. No pandemic years."),
 ("topic", "Cause: cvd (all cardiovascular disease), hd (all heart disease), chd (coronary heart disease), stroke (all stroke), hf (heart failure).", "MORT", "", ""),
 ("age_band", "35_64 or 65plus.", "MORT", "", "The only age bands published."), ("sex", "all, men or women.", "MORT", "", "All races combined; race-specific rows were not downloaded."),
 ("rate", "Death rate per 100,000.", "MORT", "", MORTCAV), ("ci_low", "Published lower confidence limit.", "MORT", "", ""), ("ci_high", "Published upper confidence limit.", "MORT", "", ""),
 ("suppressed", "True where the source marks the value as suppressed (rate missing).", "MORT", "", ""),
]

def describe(col):
    hits = []
    for rx, de, src, vin, cav in RULES:
        mt = re.fullmatch(rx, col)
        if mt:
            g = mt.groups(); hits.append((de(g) if callable(de) else de, src, vin, cav(g) if callable(cav) else cav))
    if len(hits) > 1 and col.endswith("_moe"): hits = hits[-1:]         # the generic margin-of-error rule
    if len(hits) > 1: hits = hits[:1] if all(h == hits[0] for h in hits) else hits
    assert len(hits) == 1, f"{col}: {len(hits)} dictionary rules match"
    return hits[0]

if __name__ == "__main__":
    out = ["# National county dataset: data dictionary", "", f"Generated {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')} (UTC) by `build_national_dictionary.py`.", "",
           "## Read first", "",
           "1. **Unit and key.** `national_county.parquet` has one row per county unit x ACS period (key `fips` + `acs_vintage`): 3,136 units x 3 periods. Units are the CDC mortality county units; ACS counties were mapped onto them (`national_county_crosswalk.csv`).",
           "2. **Ecological data.** Every value describes a county population. Nothing here identifies which residents drive or who died; associations are not individual-level and not causal.",
           "3. **Exposure.** `car_hours_wk_per_adult16` and `transit_hours_wk_per_adult16` are weekly commute hours averaged over all residents aged 16+ (2 trips x one-way minutes x 4.5 assumed days). They rest on the journey-to-work question only (usual commute last week); non-commute driving is not measured. Aggregate minutes by mode are the scaled bin-midpoint estimate (`*_agg_min_mid`), because the published by-mode aggregate (`*_agg_min_pub`) is suppressed for " + ", ".join(f"{100 * v:.1f}% ({k})" for k, v in d.groupby("period").car_agg_pub_suppressed.mean().items()) + " of units. Change the days assumption with `*_min_per_day_per_adult16`.",
           "4. **Mortality is model-smoothed.** Rates are age-standardized within two age bands only (35-64, 65+), smoothed over space, time and demographic group, and end in 2019. Smoothing borrows information from neighbouring counties and years, so county values are not independent and values for small counties are pulled toward their neighbours.",
           "5. **PLACES is model-based and not period-matched.** The PLACES columns are small-area model estimates for BRFSS 2017-2019 repeated on all three period rows.",
           "6. **Time-invariant columns.** Rural-urban codes, CBSA membership, percent urban and PLACES do not vary by period in this file.",
           "7. **Dollar amounts are nominal.** No pandemic years (2020 onward) are in either file.", "",
           "## Sources", "", "| id | source | URL | vintage | downloaded (UTC) |", "|---|---|---|---|---|"]
    for k, (name, url, vin, dl) in SRC.items(): out.append(f"| {k} | {name} | {url} | {vin} | {dl} |")
    tabs = acslog.groupby("vintage").table.agg(lambda s: ", ".join(sorted(s))).to_dict()
    out += ["", "ACS tables by vintage: " + "; ".join(f"{v}: {t}" for v, t in tabs.items()) + ". B08134/B08136 were not published for 2006-2010 (the collapsed C08134/C08136 are used); B23025 and B27001 do not exist for 2006-2010.", "",
            "Scripts: `acquire_acs_national.py`, `acquire_cdc_mortality_national.py`, `acquire_national_confounders.py`, `build_national_dataset.py`, `run_national_qc.py`, `build_national_dictionary.py` (run in this order from the workspace root). Sources are live and can be revised by their publishers.", "",
            f"## national_county.parquet ({len(d):,} rows x {d.shape[1]} columns)", "", "| variable | definition | source | vintage | caveats |", "|---|---|---|---|---|"]
    for c in d.columns:
        de, src, vin, cav = describe(c); out.append(f"| `{c}` | {de} | {src} | {vin or SRC[src][2]} | {cav} |")
    out += ["", f"## national_mortality_annual.parquet ({len(a):,} rows x {a.shape[1]} columns)", "", "One row per county unit x year x cause x age band x sex. Key: fips + year + topic + age_band + sex.", "", "| variable | definition | source | vintage | caveats |", "|---|---|---|---|---|"]
    assert list(a.columns) == [r[0] for r in ARULES], list(a.columns)
    for c, de, src, vin, cav in ARULES: out.append(f"| `{c}` | {de} | {src} | {vin or SRC[src][2]} | {cav} |")
    out += ["", "## national_county_crosswalk.csv", "", "One row per ACS county x vintage: `acs_vintage`, `acs_geoid` (ACS county code), `acs_name`, `unit_fips` (analysis unit), `changed` (True where the code was recoded or merged), `reason`.", ""]
    # one provenance table of every download
    logs = [acslog.assign(source="ACS5", item=acslog.table + " " + acslog.vintage.astype(str), url=acslog.url_pattern, rows=acslog.county_rows)[["source", "item", "url", "rows", "downloaded_utc"]],
            mlog.assign(source="MORT", item=mlog.dataset_id + " (" + mlog["where"] + ")")[["source", "item", "url", "rows", "downloaded_utc"]],
            rlog.assign(source="REF", item=rlog.file, rows=pd.NA)[["source", "item", "url", "rows", "downloaded_utc"]],
            plog.assign(source="PLACES", item=plog.dataset_id + " release " + plog.release.astype(str))[["source", "item", "url", "rows", "downloaded_utc"]]]
    pd.concat(logs, ignore_index=True).to_csv("national_download_log.csv", index=False)
    import os
    links = json.load(open("artifact_links.json")) if os.path.exists("artifact_links.json") else {}     # filename -> artifact link marker
    if links: out += ["## Files", ""] + [f"- [{k}]({v})" for k, v in links.items()] + [""]
    open("national_data_dictionary.md", "w", encoding="utf-8").write("\n".join(out)); print(len(d.columns), "columns documented")
