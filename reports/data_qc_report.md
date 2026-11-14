# National county dataset: QC report

Generated 2026-11-13 23:13 UTC by `run_national_qc.py`. Every number below was computed by that script from the saved files.

`national_county.parquet`: 9,408 rows x 339 columns. `national_mortality_annual.parquet`: 1,975,680 rows x 11 columns.

## 0. Where coverage is less than, or different from, what was requested

1. **Analysis units, not raw counties.** The CDC mortality series has 3,136 county units. The 3,143 (2006-2010) or 3,142 (later) ACS counties of the 50 states and DC were mapped onto them: Bedford city VA is merged into Bedford County, and eight south-east Alaska boroughs/census areas form two combined units (02901, 02902). No county was dropped. Puerto Rico and the territories are not included (not requested).
2. **Tables B08134 and B08136 do not exist for 2006-2010.** The collapsed tables C08134 and C08136 were used instead (total, drove alone, carpooled, public transit, other). Car and transit measures are unaffected; no finer sub-modes exist for that period.
3. **Published aggregate travel time by mode is suppressed for many units**: car 26.0% (2006-2010), 51.6% (2010-2014), 55.7% (2015-2019); transit 45.8% (2006-2010), 61.6% (2010-2014), 67.0% (2015-2019). The primary exposure therefore uses bin-midpoint minutes scaled to each county's published all-mode aggregate (section 6), which exists for all but one unit-period (next item).
4. **One unit lacks the all-mode aggregate too**: Loving County, Texas (48301), 2015-2019, population 98. Its midpoint minutes were scaled by the median factor of the period (flag `agg_scaled_with_median_factor`).
5. **Health-insurance coverage is missing for 2006-2010** (table B27001 is not in that file; the question began in 2008). `share_uninsured` and `share_uninsured_18_64` are available for 2010-2014 and 2015-2019 only, and the adult band is 18-64 in 2010-2014 but 19-64 in 2015-2019.
6. **Mortality is suppressed in the source for small units in every year**: 53 units for ages 35-64 and 112 units for ages 65+ (both sexes); by sex 151/157 units (men/women, 35-64) and 314/272 units (65+). The units without a 65+ rate have 2015-2019 populations between 66 and 5,698 (median 1,425). Complete-case rows cover 99.95% of the 2015-2019 population (section 9).
7. **Mortality scope.** Only all-races rows (both sexes, men, women) were downloaded; the race-specific strata of the source were not. The annual file also carries 1999 (published in the same series) in addition to the requested 2000-2019. Rates are model-smoothed and age-standardized within band; there are no counts and no other age bands.
8. **PLACES is not period-matched.** County PLACES starts with the 2020 release (BRFSS 2018; 2017 for high blood pressure and cholesterol). The same values are attached to all three period rows; they are contemporaneous with 2015-2019 only. The 2020 release is the main set (3,136 of 3,136 units); the 2021 release (BRFSS 2019) is also included but lacks the 21 New Jersey counties. PLACES values are model-based.
9. **Rural-urban classification**: NCHS 2013 (and 2006) codes for every unit, obtained from ftp.cdc.gov after access to www.cdc.gov and ftp.cdc.gov was granted (the files have moved from www.cdc.gov to ftp.cdc.gov). The USDA Rural-Urban Continuum Codes were not downloaded (www.ers.usda.gov is not reachable and was not needed). Census 2010 percent urban and population density are included as well. All are time-invariant in the file.
10. **CBSA membership**: February 2013 and September 2018 delineations. No delineation contemporaneous with 2006-2010 (December 2009) was added.
11. **Published mean travel time**: taken as published aggregate / published universe (B08013 / B08303). The data-profile table (DP03) could not be queried because the Census API requires a key.
12. **One source file came from a different Census file on the same host.** Michigan 2014 sequence 105: the per-sequence zip is rejected by the www2.census.gov firewall, so its two members were read from the Census Bureau's whole-state bundle (`5_year_by_state/<State>_All_Geographies_Not_Tracts_Block_Groups.zip`). This sequence holds B25077 (median home value).
13. **Dollar amounts are nominal** (2010, 2014 and 2019 dollars); no price index was applied.
14. **The exposure measures commuting only.** The ACS asks about the usual journey to work; non-commute driving, commute days per week (assumed 4.5) and time as a car passenger versus driver (other than drove-alone versus carpool) are not observed.

## 1. Row counts and keys

Expected number of counties = the count in the Census Gazetteer county file of the same vintage (50 states + DC), an independent file. The 2010 Gazetteer and the 2006-2010 ACS both carry Bedford city VA (3,143 counties); later vintages have 3,142. After mapping to the CDC mortality units there are 3,136 units in every period.

| acs_vintage | acs_counties | analysis_units | gazetteer_counties | acs_not_in_gazetteer | gazetteer_not_in_acs | rows_in_dataset | rows_with_acs | rows_with_cdc_mortality_unit |
|---|---|---|---|---|---|---|---|---|
| 2010 | 3143 | 3136 | 3143 | 0 | 0 | 3136 | 3136 | 3136 |
| 2014 | 3142 | 3136 | 3142 | 0 | 0 | 3136 | 3136 | 3136 |
| 2019 | 3142 | 3136 | 3142 | 0 | 0 | 3136 | 3136 | 3136 |

Counts by state and period (51 states x 3 periods) against the Gazetteer-based expected number of units: **0 mismatches** (full table: `qc/national_counts_by_state_period.csv`). States: 51; missing state_abbr: 0.

Duplicate keys (fips + acs_vintage): **0**. Duplicate keys in the annual mortality file (fips + year + topic + age_band + sex): **0**.
Units present in all three periods: 3,136 of 3,136. Rows without ACS data: 0; rows without a CDC mortality unit: 0.

## 2. County changes (crosswalk)

ACS county codes that were mapped to a different analysis unit (`national_county_crosswalk.csv` lists every county). Counts were summed over components; medians of multi-county units are household-weighted means (flag `median_approx`); categorical attributes (rural-urban code, CBSA) come from the most populous component; PLACES prevalences are population-weighted means.

| acs_geoid | acs_name | unit_fips | acs_vintages | reason |
|---|---|---|---|---|
| 02100 | Haines Borough, Alaska | 02902 | 2010, 2014, 2019 | CDC combined unit Juneau-Haines-Hoonah-Angoon-Skagway |
| 02105 | Hoonah-Angoon Census Area, Alaska | 02902 | 2010, 2014, 2019 | CDC combined unit Juneau-Haines-Hoonah-Angoon-Skagway |
| 02110 | Juneau City and Borough, Alaska | 02902 | 2010, 2014, 2019 | CDC combined unit Juneau-Haines-Hoonah-Angoon-Skagway (Alaska boundary changes 2007-2013) |
| 02130 | Ketchikan Gateway Borough, Alaska | 02901 | 2010, 2014, 2019 | CDC combined unit Ketchikan-Prince of Wales-Wrangell-Petersburg (Alaska boundary changes 2008-2013) |
| 02195 | Petersburg Borough, Alaska | 02901 | 2014, 2019 | CDC combined unit Ketchikan-Prince of Wales-Wrangell-Petersburg |
| 02195 | Petersburg Census Area, Alaska | 02901 | 2010 | CDC combined unit Ketchikan-Prince of Wales-Wrangell-Petersburg |
| 02198 | Prince of Wales-Hyder Census Area, Alaska | 02901 | 2010, 2014, 2019 | CDC combined unit Ketchikan-Prince of Wales-Wrangell-Petersburg |
| 02230 | Skagway Municipality, Alaska | 02902 | 2010, 2014, 2019 | CDC combined unit Juneau-Haines-Hoonah-Angoon-Skagway |
| 02270 | Wade Hampton Census Area, Alaska | 02158 | 2010, 2014 | Wade Hampton Census Area AK renamed Kusilvak Census Area (new code) in 2015; ACS 2006-2010 and 2010-2014 use 02270 |
| 02275 | Wrangell City and Borough, Alaska | 02901 | 2010, 2014, 2019 | CDC combined unit Ketchikan-Prince of Wales-Wrangell-Petersburg |
| 46113 | Shannon County, South Dakota | 46102 | 2010, 2014 | Shannon County SD renamed Oglala Lakota County (new code) in 2015; ACS 2006-2010 and 2010-2014 use 46113 |
| 51515 | Bedford city, Virginia | 51019 | 2010 | Bedford city VA (independent city) merged into Bedford County in July 2013; separate only in ACS 2006-2010 |

Not affected in these vintages (checked against the ACS geography files): Broomfield County CO (08014, created 2001) is present in all three vintages and in the CDC series; Connecticut still has its eight counties (planning regions replace them only from the 2022 ACS); Valdez-Cordova Census Area AK (02261) was split in 2019 but the 2015-2019 ACS and the CDC series both still use 02261.
Checks: 08014 rows = 3; Connecticut units per period = [8]; 02261 rows = 3; 02063/02066 rows = 0.

## 3. Mortality coverage

Annual file: 3,136 units x 21 years (1999-2019) x 5 causes x 2 age bands x 3 sex strata = 1,975,680 rows. The download (race = Overall) was checked against the server-side row count.

Suppressed values ('Value suppressed' in the source) by stratum, all causes and years:

| sex | age_band | rows | suppressed | units_ever_suppressed | pct_suppressed |
|---|---|---|---|---|---|
| all | 35_64 | 329280 | 5595 | 54 | 1.7 |
| all | 65plus | 329280 | 11790 | 113 | 3.58 |
| men | 35_64 | 329280 | 15885 | 152 | 4.82 |
| men | 65plus | 329280 | 33000 | 315 | 10.02 |
| women | 35_64 | 329280 | 16515 | 158 | 5.02 |
| women | 65plus | 329280 | 28590 | 273 | 8.68 |

Number of non-suppressed annual values behind each five-year mean (the mean is set to missing unless all five are present):

| period | mort_cvd_35_64_n_years | mort_cvd_65plus_n_years |
|---|---|---|
| 2006-2010 | 0 years: 53 units, 5 years: 3083 units | 0 years: 112 units, 5 years: 3024 units |
| 2010-2014 | 0 years: 53 units, 5 years: 3083 units | 0 years: 112 units, 5 years: 3024 units |
| 2015-2019 | 0 years: 53 units, 5 years: 3083 units | 0 years: 112 units, 5 years: 3024 units |

Rate inside its published confidence limits: 1,975,680 of 1,975,680 rows (0 outside). Rate range: 1.1 to 4188.4 per 100,000.

## 4. Missingness per variable

Full table for all 339 columns: `qc/national_missingness_by_variable_period.csv`. Columns with any missing value, grouped by pattern (number missing in 2006-2010 / 2010-2014 / 2015-2019, out of 3,136 units each):

| missing (2006-10 / 2010-14 / 2015-19) | n_columns | columns |
|---|---|---|
| 0 / 0 / 1 | 7 | `all_agg_min_pub`, `all_agg_min_pub_moe`, `mean_tt_all_pub`, `mean_tt_all_pub_moe`, `rake_factor`, `all_min_per_day_per_adult16`, `all_hours_wk_per_adult16` |
| 1 / 0 / 0 | 2 | `car_worker_share_pop_65plus`, `worker_share_pop_65plus` |
| 1 / 1 / 2 | 1 | `median_home_value` |
| 112 / 112 / 112 | 20 | `mort_chd_65plus`, `mort_cvd_65plus`, `mort_hd_65plus`, `mort_hf_65plus`, `mort_stroke_65plus`, `mort_chd_65plus_midyear`, `mort_cvd_65plus_midyear`, `mort_hd_65plus_midyear`, `mort_hf_65plus_midyear`, `mort_stroke_65plus_midyear`, `mort_chd_65plus_midyear_lo`, `mort_cvd_65plus_midyear_lo`, `mort_hd_65plus_midyear_lo`, `mort_hf_65plus_midyear_lo`, `mort_stroke_65plus_midyear_lo`, `mort_chd_65plus_midyear_hi`, `mort_cvd_65plus_midyear_hi`, `mort_hd_65plus_midyear_hi`, `mort_hf_65plus_midyear_hi`, `mort_stroke_65plus_midyear_hi` |
| 1296 / 1296 / 1296 | 3 | `cbsa_code_2018`, `cbsa_title_2018`, `cbsa_central_outlying_2018` |
| 1329 / 1329 / 1329 | 3 | `cbsa_code_2013`, `cbsa_title_2013`, `cbsa_central_outlying_2013` |
| 1436 / 1932 / 2101 | 7 | `transit_agg_min_pub`, `transit_agg_min_pub_moe`, `mean_tt_transit_pub`, `transit_min_per_day_per_adult16_pub`, `transit_hours_wk_per_adult16_pub`, `transit_hours_wk_per_adult16_pub_moe`, `transit_hours_wk_per_adult18_pub` |
| 151 / 151 / 151 | 10 | `mort_chd_35_64_men`, `mort_cvd_35_64_men`, `mort_hd_35_64_men`, `mort_hf_35_64_men`, `mort_stroke_35_64_men`, `mort_chd_35_64_men_midyear`, `mort_cvd_35_64_men_midyear`, `mort_hd_35_64_men_midyear`, `mort_hf_35_64_men_midyear`, `mort_stroke_35_64_men_midyear` |
| 157 / 157 / 157 | 10 | `mort_chd_35_64_women`, `mort_cvd_35_64_women`, `mort_hd_35_64_women`, `mort_hf_35_64_women`, `mort_stroke_35_64_women`, `mort_chd_35_64_women_midyear`, `mort_cvd_35_64_women_midyear`, `mort_hd_35_64_women_midyear`, `mort_hf_35_64_women_midyear`, `mort_stroke_35_64_women_midyear` |
| 1946 / 1946 / 1946 | 1 | `csa_code_2018` |
| 1986 / 1986 / 1986 | 1 | `csa_code_2013` |
| 21 / 21 / 21 | 20 | `places_r2021_access2_aa`, `places_r2021_access2_crude`, `places_r2021_binge_aa`, `places_r2021_binge_crude`, `places_r2021_bphigh_aa`, `places_r2021_bphigh_crude`, `places_r2021_chd_aa`, `places_r2021_chd_crude`, `places_r2021_csmoking_aa`, `places_r2021_csmoking_crude`, `places_r2021_diabetes_aa`, `places_r2021_diabetes_crude`, `places_r2021_highchol_aa`, `places_r2021_highchol_crude`, `places_r2021_lpa_aa`, `places_r2021_lpa_crude`, `places_r2021_obesity_aa`, `places_r2021_obesity_crude`, `places_r2021_stroke_aa`, `places_r2021_stroke_crude` |
| 272 / 272 / 272 | 10 | `mort_chd_65plus_women`, `mort_cvd_65plus_women`, `mort_hd_65plus_women`, `mort_hf_65plus_women`, `mort_stroke_65plus_women`, `mort_chd_65plus_women_midyear`, `mort_cvd_65plus_women_midyear`, `mort_hd_65plus_women_midyear`, `mort_hf_65plus_women_midyear`, `mort_stroke_65plus_women_midyear` |
| 3 / 2 / 2 | 1 | `median_hh_income_moe` |
| 3131 / 3131 / 3131 | 1 | `fips_note` |
| 3136 / 0 / 0 | 4 | `unemployment_rate_b23025`, `share_uninsured`, `share_uninsured_18_64`, `uninsured_18_64_youngest_age` |
| 314 / 314 / 314 | 10 | `mort_chd_65plus_men`, `mort_cvd_65plus_men`, `mort_hd_65plus_men`, `mort_hf_65plus_men`, `mort_stroke_65plus_men`, `mort_chd_65plus_men_midyear`, `mort_cvd_65plus_men_midyear`, `mort_hd_65plus_men_midyear`, `mort_hf_65plus_men_midyear`, `mort_stroke_65plus_men_midyear` |
| 5 / 3 / 4 | 1 | `median_home_value_moe` |
| 53 / 53 / 53 | 20 | `mort_chd_35_64`, `mort_cvd_35_64`, `mort_hd_35_64`, `mort_hf_35_64`, `mort_stroke_35_64`, `mort_chd_35_64_midyear`, `mort_cvd_35_64_midyear`, `mort_hd_35_64_midyear`, `mort_hf_35_64_midyear`, `mort_stroke_35_64_midyear`, `mort_chd_35_64_midyear_lo`, `mort_cvd_35_64_midyear_lo`, `mort_hd_35_64_midyear_lo`, `mort_hf_35_64_midyear_lo`, `mort_stroke_35_64_midyear_lo`, `mort_chd_35_64_midyear_hi`, `mort_cvd_35_64_midyear_hi`, `mort_hd_35_64_midyear_hi`, `mort_hf_35_64_midyear_hi`, `mort_stroke_35_64_midyear_hi` |
| 637 / 443 / 535 | 4 | `mean_tt_transit_mid`, `share_transit_commuters_45plus`, `share_transit_commuters_60plus`, `transit_hours_wk_per_commuter` |
| 812 / 1619 / 1747 | 7 | `drivealone_agg_min_pub`, `drivealone_agg_min_pub_moe`, `mean_tt_drivealone_pub`, `drivealone_min_per_day_per_adult16_pub`, `drivealone_hours_wk_per_adult16_pub`, `drivealone_hours_wk_per_adult16_pub_moe`, `drivealone_hours_wk_per_adult18_pub` |
| 814 / 1619 / 1747 | 7 | `car_agg_min_pub`, `car_agg_min_pub_moe`, `mean_tt_car_pub`, `car_min_per_day_per_adult16_pub`, `car_hours_wk_per_adult16_pub`, `car_hours_wk_per_adult16_pub_moe`, `car_hours_wk_per_adult18_pub` |

## 5. Range checks

| check | rows violating |
|---|---|
| all share/rate columns in [0, 1] (38 columns) | 0 |
| pop_18plus <= pop_16plus <= pop_total | 0 |
| workers_total <= pop_16plus | 0 |
| commuters_total <= workers_total | 0 |
| car_commuters + transit_commuters <= commuters_total | 0 |
| drivealone_commuters <= car_commuters | 0 |
| car_agg_min_mid + transit_agg_min_mid <= all_agg_min_pub (tolerance 1e-6) | 0 |
| hours and minutes columns >= 0 | 0 |
| mean_tt_all_pub between 2 and 80 minutes | 0 |
| car_hours_wk_per_adult16 below 10 | 0 |
| mortality means > 0 | 0 |
| mid-year mortality inside its confidence limits | 0 |
| 65+ CVD rate > 35-64 CVD rate | 0 |
| heart disease <= all CVD; CHD <= heart disease (both age bands, means) | 47 |
| nchs_ur_2013 in 1..6 | 0 |
| PLACES prevalences in (0, 100) | 0 |
| land_area_sqmi > 0 and pop_density > 0 | 0 |
| pct_urban_2010 in [0, 100] | 0 |

Note on the nested-cause check: all 47 violating rows are in the 35-64 band and in very small units (median population 3,510); largest excess 17.3 per 100,000. The published values are model-smoothed estimates, not counts, so a sub-cause can exceed its parent where data are sparse. Values were left as published.

Unemployment rate summed from B23001 against the published B23025 cells (2010-2014 and 2015-2019, 6,272 rows): maximum absolute difference 0.00e+00.

Distribution of key variables by period (unweighted across units; full table `qc/national_range_summary.csv`):

| period | variable | count | min | 1% | 50% | 99% | max |
|---|---|---|---|---|---|---|---|
| 2006-2010 | car_hours_wk_per_adult16 | 3136.000 | 0.036 | 0.717 | 1.646 | 2.930 | 3.764 |
| 2010-2014 | car_hours_wk_per_adult16 | 3136.000 | 0.029 | 0.708 | 1.630 | 2.909 | 3.594 |
| 2015-2019 | car_hours_wk_per_adult16 | 3136.000 | 0.046 | 0.690 | 1.721 | 3.059 | 3.775 |
| 2006-2010 | mean_tt_all_pub | 3136.000 | 4.312 | 11.098 | 22.419 | 37.497 | 44.161 |
| 2010-2014 | mean_tt_all_pub | 3136.000 | 4.575 | 11.518 | 22.813 | 38.253 | 42.808 |
| 2015-2019 | mean_tt_all_pub | 3135.000 | 5.102 | 11.776 | 23.685 | 38.956 | 52.637 |
| 2006-2010 | mort_cvd_35_64 | 3083.000 | 39.340 | 61.075 | 129.700 | 291.204 | 382.440 |
| 2010-2014 | mort_cvd_35_64 | 3083.000 | 35.620 | 56.716 | 127.700 | 296.186 | 412.880 |
| 2015-2019 | mort_cvd_35_64 | 3083.000 | 36.860 | 56.046 | 133.700 | 316.854 | 399.960 |
| 2006-2010 | mort_cvd_65plus | 3024.000 | 736.660 | 1153.830 | 1772.240 | 2592.709 | 3174.160 |
| 2010-2014 | mort_cvd_65plus | 3024.000 | 648.820 | 1037.051 | 1603.530 | 2350.482 | 3472.380 |
| 2015-2019 | mort_cvd_65plus | 3024.000 | 600.400 | 1004.866 | 1535.020 | 2265.340 | 3229.280 |
| 2006-2010 | rake_factor | 3136.000 | 0.634 | 0.869 | 0.950 | 1.097 | 1.388 |
| 2010-2014 | rake_factor | 3136.000 | 0.745 | 0.876 | 0.952 | 1.089 | 1.426 |
| 2015-2019 | rake_factor | 3135.000 | 0.746 | 0.875 | 0.956 | 1.101 | 1.421 |
| 2006-2010 | share_drive_alone | 3136.000 | 0.045 | 0.505 | 0.792 | 0.880 | 0.917 |
| 2010-2014 | share_drive_alone | 3136.000 | 0.051 | 0.504 | 0.804 | 0.892 | 0.964 |
| 2015-2019 | share_drive_alone | 3136.000 | 0.057 | 0.518 | 0.812 | 0.896 | 0.971 |
| 2006-2010 | share_wfh | 3136.000 | 0.000 | 0.008 | 0.041 | 0.196 | 0.405 |
| 2010-2014 | share_wfh | 3136.000 | 0.000 | 0.008 | 0.040 | 0.176 | 0.355 |
| 2015-2019 | share_wfh | 3136.000 | 0.000 | 0.007 | 0.045 | 0.165 | 0.341 |
| 2006-2010 | transit_hours_wk_per_adult16 | 3136.000 | 0.000 | 0.000 | 0.007 | 0.485 | 2.466 |
| 2010-2014 | transit_hours_wk_per_adult16 | 3136.000 | 0.000 | 0.000 | 0.008 | 0.522 | 2.485 |
| 2015-2019 | transit_hours_wk_per_adult16 | 3136.000 | 0.000 | 0.000 | 0.007 | 0.578 | 2.699 |

Top-coded median home value rows: 1. Rows with `median_approx` (multi-county unit): 7.

## 6. Exposure construction: suppression of published aggregates and validation of the estimate used

Units whose published aggregate travel time is suppressed (B08013 for all modes; B08136, or C08136 in 2006-2010, by mode). For multi-county units the published aggregate is missing if any component is suppressed.

| period | all (n) | all (%) | car (n) | car (%) | drivealone (n) | drivealone (%) | transit (n) | transit (%) |
|---|---|---|---|---|---|---|---|---|
| 2006-2010 | 0 | 0.0 | 814 | 26.0 | 812 | 25.9 | 1436 | 45.8 |
| 2010-2014 | 0 | 0.0 | 1619 | 51.6 | 1619 | 51.6 | 1932 | 61.6 |
| 2015-2019 | 1 | 0.0 | 1747 | 55.7 | 1747 | 55.7 | 2101 | 67.0 |

Share of population living in units with a suppressed car aggregate: 2006-2010 5.38%; 2010-2014 31.13%; 2015-2019 29.30%.

Primary estimate (`*_agg_min_mid`: bin midpoints scaled to the county's published all-mode aggregate) against the published by-mode aggregate, in units where the latter exists and is positive. Compared as weekly hours per adult resident:

| period | mode | units_compared | pearson_r | slope (estimate on published) | total estimate / total published | median abs % diff | 95th pct abs % diff | pearson_r unscaled midpoints | slope unscaled midpoints |
|---|---|---|---|---|---|---|---|---|---|
| 2006-2010 | car | 2322 | 0.9995 | 1.01 | 1.0037 | 0.3 | 1.79 | 0.99 | 1.032 |
| 2006-2010 | drivealone | 2324 | 0.9985 | 1.01 | 1.0059 | 0.69 | 3.53 | 0.9919 | 1.043 |
| 2006-2010 | transit | 1700 | 0.9983 | 0.99 | 0.9853 | 7.26 | 27.91 | 0.9972 | 1.064 |
| 2010-2014 | car | 1517 | 0.9995 | 1.01 | 1.0046 | 0.34 | 1.67 | 0.9914 | 1.03 |
| 2010-2014 | drivealone | 1517 | 0.9988 | 1.011 | 1.0066 | 0.67 | 3.28 | 0.993 | 1.039 |
| 2010-2014 | transit | 1204 | 0.9987 | 0.992 | 0.9855 | 7.53 | 27.31 | 0.9976 | 1.064 |
| 2015-2019 | car | 1389 | 0.9992 | 1.01 | 1.0053 | 0.34 | 1.86 | 0.9896 | 1.038 |
| 2015-2019 | drivealone | 1389 | 0.9984 | 1.01 | 1.0072 | 0.68 | 3.53 | 0.9911 | 1.045 |
| 2015-2019 | transit | 1035 | 0.9985 | 0.989 | 0.9822 | 8.11 | 28.32 | 0.9973 | 1.056 |

Second check, which also covers the counties whose own aggregate is suppressed: county estimates summed to states against the published STATE aggregates by mode (state aggregates are published for all states except Wyoming in 2010-2014 and 2015-2019):

| period | mode | states compared | sum of county estimates / published state aggregates | lowest state ratio | highest state ratio | share of state minutes in counties with suppressed aggregate (%) |
|---|---|---|---|---|---|---|
| 2006-2010 | car | 51 | 1.0036 | 0.997 | 1.026 | 5.0 |
| 2006-2010 | transit | 51 | 0.9853 | 0.857 | 1.049 | 0.1 |
| 2010-2014 | car | 50 | 1.0041 | 0.998 | 1.045 | 29.9 |
| 2010-2014 | transit | 50 | 0.9855 | 0.855 | 1.045 | 4.9 |
| 2015-2019 | car | 50 | 1.0046 | 0.997 | 1.055 | 27.6 |
| 2015-2019 | transit | 50 | 0.982 | 0.844 | 1.026 | 4.0 |

Sampling error of the primary exposure (`car_hours_wk_per_adult16`): approximate coefficient of variation = (margin of error / 1.645) / estimate, by population size. The margin of error uses Census approximation formulas and is conservative (bin margins treated as independent).

| period | population | units | median_cv_pct | units_cv_over_30pct |
|---|---|---|---|---|
| 2006-2010 | < 5,000 | 298 | 38.8 | 203 |
| 2006-2010 | 5,000-19,999 | 1003 | 13.4 | 31 |
| 2006-2010 | 20,000-99,999 | 1261 | 6.1 | 0 |
| 2006-2010 | 100,000+ | 574 | 1.5 | 0 |
| 2010-2014 | < 5,000 | 299 | 13.3 | 21 |
| 2010-2014 | 5,000-19,999 | 997 | 6.6 | 3 |
| 2010-2014 | 20,000-99,999 | 1252 | 3.8 | 0 |
| 2010-2014 | 100,000+ | 588 | 1.5 | 0 |
| 2015-2019 | < 5,000 | 308 | 15.1 | 34 |
| 2015-2019 | 5,000-19,999 | 999 | 6.8 | 3 |
| 2015-2019 | 20,000-99,999 | 1233 | 3.8 | 0 |
| 2015-2019 | 100,000+ | 596 | 1.5 | 0 |

The larger values for small units in 2006-2010 reflect the published margins of zero-estimate cells, which are much larger in that file (median 119) than in 2010-2014 (19) or 2015-2019 (19); they do not indicate a smaller sample.

Diagnostics behind the open-ended 60+ bin assumption (75 minutes for car, 80 for transit; `qc/national_topbin_calibration.csv`). `top_bin_mean_matching_state_totals` is the 60+ mean that would be needed if the closed-bin midpoints were exact; values below 60 show that the midpoints overstate (reported times heap at 10, 15, 20, 30, 45), which is why the midpoint minutes are scaled to the published county total rather than used directly. `bounded_ls_top_bin_*` is the 60+ coefficient of a bounded least-squares fit of the published aggregates on the nine bin counts.

| vintage | mode | states_used | top_bin_mean_matching_state_totals | bounded_ls_top_bin_states | bounded_ls_n_states | bounded_ls_top_bin_counties | bounded_ls_n_counties | top_bin_assumed |
|---|---|---|---|---|---|---|---|---|
| 2010 | all | 51 | 57.85 | 75.42 | 51 | 76.17 | 2324 |  |
| 2010 | drivealone | 51 | 50.31 | 74.31 | 51 | 76.18 | 2324 | 75.00 |
| 2010 | car | 51 | 52.83 | 74.36 | 51 | 76.63 | 2322 | 75.00 |
| 2010 | transit | 51 | 72.42 | 78.13 | 51 | 79.85 | 1700 | 80.00 |
| 2014 | all | 50 | 58.50 | 75.55 | 50 | 76.05 | 1517 |  |
| 2014 | car | 50 | 53.34 | 74.37 | 50 | 76.35 | 1517 | 75.00 |
| 2014 | drivealone | 50 | 51.30 | 74.23 | 50 | 75.85 | 1517 | 75.00 |
| 2014 | transit | 50 | 72.59 | 78.34 | 50 | 79.79 | 1204 | 80.00 |
| 2019 | all | 50 | 61.19 | 76.88 | 50 | 76.97 | 1389 |  |
| 2019 | car | 50 | 56.75 | 75.62 | 50 | 76.93 | 1389 | 75.00 |
| 2019 | drivealone | 50 | 55.37 | 75.34 | 50 | 76.38 | 1389 | 75.00 |
| 2019 | transit | 50 | 74.11 | 79.64 | 50 | 80.93 | 1035 | 80.00 |

## 7. Derived mean travel time against the published ACS mean

Published mean = published aggregate travel time (B08013) / workers who did not work at home (B08303), the definition of the ACS mean travel time to work. The ACS data-profile table itself (DP03) could not be queried because the Census API needs a key. Derived mean = unscaled bin midpoints from the mode-by-travel-time table (`mean_tt_all_midraw`, 60+ bin at 75 or 80 minutes); it is an independent calculation from different table cells. The primary exposure does not use the unscaled value.

2015-2019, 14 counties (the eight most populous and six mid-sized counties taken at fixed intervals of the FIPS-sorted list):

| fips | county_name | pop_total | mean_tt_all_pub | mean_tt_all_pub_moe | mean_tt_all_midraw | rake_factor | difference (derived - published) |
|---|---|---|---|---|---|---|---|
| 06037 | Los Angeles County, California | 10081570 | 31.84 | 0.14 | 33.89 | 0.94 | 2.04 |
| 17031 | Cook County, Illinois | 5198275 | 33.44 | 0.17 | 36.00 | 0.93 | 2.56 |
| 48201 | Harris County, Texas | 4646630 | 29.46 | 0.21 | 31.49 | 0.94 | 2.03 |
| 04013 | Maricopa County, Arizona | 4328810 | 26.44 | 0.19 | 28.18 | 0.94 | 1.74 |
| 06073 | San Diego County, California | 3316073 | 26.47 | 0.19 | 28.06 | 0.94 | 1.59 |
| 06059 | Orange County, California | 3168044 | 28.04 | 0.20 | 29.62 | 0.95 | 1.58 |
| 12086 | Miami-Dade County, Florida | 2699428 | 32.75 | 0.25 | 35.18 | 0.93 | 2.43 |
| 48113 | Dallas County, Texas | 2606868 | 27.67 | 0.21 | 29.54 | 0.94 | 1.88 |
| 01001 | Autauga County, Alabama | 55380 | 24.38 | 1.67 | 25.70 | 0.95 | 1.32 |
| 16069 | Nez Perce County, Idaho | 40217 | 17.02 | 1.22 | 17.67 | 0.96 | 0.65 |
| 21141 | Logan County, Kentucky | 26902 | 23.93 | 2.19 | 25.66 | 0.93 | 1.73 |
| 28123 | Scott County, Mississippi | 28332 | 26.05 | 2.79 | 28.59 | 0.91 | 2.54 |
| 39051 | Fulton County, Ohio | 42253 | 23.15 | 0.90 | 24.55 | 0.94 | 1.40 |
| 47145 | Roane County, Tennessee | 53075 | 27.83 | 1.98 | 29.07 | 0.96 | 1.23 |

All units:

| period | units | pearson_r | mean difference (min) | median abs difference (min) | 95th pct abs difference (min) | within published MOE (%) |
|---|---|---|---|---|---|---|
| 2006-2010 | 3136 | 0.9833 | 0.99 | 1.15 | 2.36 | 72.0 |
| 2010-2014 | 3136 | 0.9855 | 0.98 | 1.13 | 2.24 | 72.5 |
| 2015-2019 | 3135 | 0.9846 | 0.89 | 1.08 | 2.3 | 74.5 |

## 8. Bay Area counties against the earlier Bay Area county panel

The earlier panel (`county_year_panel.parquet`) holds ACS 5-year county estimates for 15 California counties (9 Bay Area + 6 adjacent) at 2014 and 2019, built from the same Census summary files through a different script. Matched county-periods: 30 of 30.

| bay_area_panel_column | national_column | county-periods compared | max abs difference | max abs relative difference | within Bay Area panel MOE |
|---|---|---|---|---|---|
| acs5_pop_total | pop_total | 30 | 0.0 | 0.0 | 30 of 30 |
| acs5_commuters_total | commuters_total | 30 | 0.0 | 0.0 | 30 of 30 |
| acs5_mean_commute_min | mean_tt_all_pub | 30 | 0.0 | 0.0 | 30 of 30 |
| acs5_share_drive_alone | share_drive_alone | 30 | 0.0 | 0.0 | 30 of 30 |
| acs5_share_wfh | share_wfh | 30 | 0.0 | 0.0 | 30 of 30 |
| acs5_share_commute_60plus | share_commute_60plus | 30 | 0.0 | 0.0 | 30 of 30 |
| acs5_share_commute_90plus | share_commute_90plus | 30 | 0.0 | 0.0 | 30 of 30 |
| acs5_median_hh_income | median_hh_income | 30 | 0.0 | 0.0 | 30 of 30 |
| acs5_median_home_value | median_home_value | 30 | 0.0 | 0.0 | 30 of 30 |

Annual mortality (5 causes x 2 age bands, 2010-2019): 1,500 county-year values in the Bay Area panel, 1,500 matched in the national annual file, maximum absolute difference 0.0.

For reference, the primary exposure (`car_hours_wk_per_adult16`) of the nine Bay Area counties:

| fips | county_name | 2006-2010 | 2010-2014 | 2015-2019 |
|---|---|---|---|---|
| 06001 | Alameda County, California | 1.76 | 1.692 | 1.92 |
| 06013 | Contra Costa County, California | 2.132 | 2.192 | 2.518 |
| 06041 | Marin County, California | 1.812 | 1.798 | 1.955 |
| 06055 | Napa County, California | 1.878 | 1.864 | 2.02 |
| 06075 | San Francisco County, California | 1.171 | 1.17 | 1.228 |
| 06081 | San Mateo County, California | 1.756 | 1.832 | 2.045 |
| 06085 | Santa Clara County, California | 1.858 | 1.936 | 2.29 |
| 06095 | Solano County, California | 2.279 | 2.144 | 2.517 |
| 06097 | Sonoma County, California | 1.91 | 1.86 | 1.978 |

## 9. Population coverage

`complete_case_main` requires: `car_hours_wk_per_adult16`, `transit_hours_wk_per_adult16`, `mort_cvd_35_64`, `mort_cvd_65plus`, `median_hh_income`, `poverty_rate`, `share_bachelors_plus`, `share_nh_black`, `share_hispanic`, `unemployment_rate`, `share_no_vehicle_hh`, `pop_density`, `share_age_65plus`, `share_female`, `nchs_ur_2013`. `complete_case_main_places` adds `places_r2020_csmoking_aa`, `places_r2020_obesity_aa`, `places_r2020_diabetes_aa`, `places_r2020_lpa_aa` (PLACES 2020 release, BRFSS 2018; contemporaneous with 2015-2019 only).

| period | units | US population, sum of state estimates | sum of county estimates | sum over dataset rows | complete_case_main rows | population share (%) | complete_case_main_places rows | population share with PLACES (%) |
|---|---|---|---|---|---|---|---|---|
| 2006-2010 | 3136 | 303965272 | 303965272 | 303965272 | 3024 | 99.941 | 3024 | 99.941 |
| 2010-2014 | 3136 | 314107084 | 314107084 | 314107084 | 3024 | 99.943 | 3024 | 99.943 |
| 2015-2019 | 3136 | 324697795 | 324697795 | 324697795 | 3024 | 99.946 | 3024 | 99.946 |

Rows that are not complete cases: 336; missing variable counts among them: {'mort_cvd_35_64': 159, 'mort_cvd_65plus': 336}.
Units never complete: 02013 Aleutians East Borough, Alaska, 02016 Aleutians West Census Area, Alaska, 02060 Bristol Bay Borough, Alaska, 02068 Denali Borough, Alaska, 02070 Dillingham Census Area, Alaska, 02164 Lake and Peninsula Borough, Alaska, 02282 Yakutat City and Borough, Alaska, 06003 Alpine County, California, 08017 Cheyenne County, Colorado, 08053 Hinsdale County, Colorado, 08057 Jackson County, Colorado, 08061 Kiowa County, Colorado, 08079 Mineral County, Colorado, 08111 San Juan County, Colorado, 13265 Taliaferro County, Georgia, 15005 Kalawao County, Hawaii, 16025 Camas County, Idaho, 16033 Clark County, Idaho, 20025 Clark County, Kansas, 20033 Comanche County, Kansas, 20071 Greeley County, Kansas, 20075 Hamilton County, Kansas, 20083 Hodgeman County, Kansas, 20101 Lane County, Kansas, 20187 Stanton County, Kansas, 20199 Wallace County, Kansas, 20203 Wichita County, Kansas, 21201 Robertson County, Kentucky, 28055 Issaquena County, Mississippi, 30011 Carter County, Montana, 30019 Daniels County, Montana, 30025 Fallon County, Montana, 30033 Garfield County, Montana, 30037 Golden Valley County, Montana, 30055 McCone County, Montana, 30069 Petroleum County, Montana, 30075 Powder River County, Montana, 30079 Prairie County, Montana, 30103 Treasure County, Montana, 30109 Wibaux County, Montana, 31005 Arthur County, Nebraska, 31007 Banner County, Nebraska, 31009 Blaine County, Nebraska, 31049 Deuel County, Nebraska, 31057 Dundy County, Nebraska, 31073 Gosper County, Nebraska, 31075 Grant County, Nebraska, 31085 Hayes County, Nebraska, 31091 Hooker County, Nebraska, 31103 Keya Paha County, Nebraska, 31113 Logan County, Nebraska, 31115 Loup County, Nebraska, 31117 McPherson County, Nebraska, 31149 Rock County, Nebraska, 31165 Sioux County, Nebraska, 31171 Thomas County, Nebraska, 31183 Wheeler County, Nebraska, 32009 Esmeralda County, Nevada, 32011 Eureka County, Nevada, 35021 Harding County, New Mexico ... (112 units in total).

## 10. Rural-urban classification, CBSA and PLACES coverage

NCHS 2013 Urban-Rural Classification (2015-2019 rows; exposure medians are descriptive only):

| nchs_ur_2013 | nchs_ur_2013_label | units | population | car_hours_median | transit_hours_median |
|---|---|---|---|---|---|
| 1 | Large central metro | 68 | 100044273 | 1.901 | 0.159 |
| 2 | Large fringe metro | 368 | 81105723 | 2.385 | 0.023 |
| 3 | Medium metro | 372 | 67902921 | 1.902 | 0.013 |
| 4 | Small metro | 358 | 29589717 | 1.717 | 0.013 |
| 5 | Micropolitan | 641 | 27263900 | 1.614 | 0.007 |
| 6 | Noncore | 1329 | 18791261 | 1.577 | 0.003 |

CBSA membership (2015-2019 rows): February 2013 delineation: {'None': 1329, 'Metropolitan': 1166, 'Micropolitan': 641}; September 2018 delineation: {'None': 1296, 'Metropolitan': 1180, 'Micropolitan': 660}.
PLACES 2020 release (BRFSS 2018): 3,136 of 3,136 units. PLACES 2021 release (BRFSS 2019): 3,115 of 3,136 units; missing by state: {'NJ': 21}.

## Files

- [national_county.parquet]({{artifact:8d581f0e-d303-4798-aacf-8b7042909763}})
- [national_mortality_annual.parquet]({{artifact:0260ee9f-63da-4cf9-a4fb-495a18b2ad38}})
- [national_county_crosswalk.csv]({{artifact:5afa4ed8-b525-4596-959a-4b560285d1b4}})
- [national_acs5_cells.parquet]({{artifact:07a36314-d9ea-4c97-b983-d73f172421ec}})
- [national_download_log.csv]({{artifact:f091b88d-b9de-4c41-bd56-f7f2e4615ec8}})
- [national_counts_by_state_period.csv]({{artifact:e4472c74-6619-4c48-afd8-2b1ac64ee5c3}})
- [national_missingness_by_variable_period.csv]({{artifact:15bea8bb-8764-4cfd-9fec-397d2ebcb062}})
- [national_range_summary.csv]({{artifact:535a75cb-dfbb-4490-b449-605c8a5d73b4}})
- [national_exposure_validation.csv]({{artifact:b842a23f-e769-4ef9-a2c8-0041a451e70d}})
- [national_topbin_calibration.csv]({{artifact:0b1a2caa-75f5-48e6-a24c-7b18bd061bea}})
- [acquire_acs_national.py]({{artifact:c9e1060e-1789-47cf-8e34-7949994a0d40}})
- [acquire_cdc_mortality_national.py]({{artifact:496e689d-74af-40a9-a0c9-e1a7dca7a0a1}})
- [acquire_national_confounders.py]({{artifact:419022a0-fda9-4aa5-abfe-fc27ac0a6998}})
- [build_national_dataset.py]({{artifact:b49fd30c-bb4f-4ae3-bee3-316fbe864250}})
- [run_national_qc.py]({{artifact:3a600be2-744d-46fb-9038-87b2088f4a07}})
- [build_national_dictionary.py]({{artifact:943e0849-c270-49b8-9c1d-2e1611c699b9}})
- [national_raw_inputs.zip]({{artifact:5b321137-45e5-469e-a356-f1fbe4870b45}})
