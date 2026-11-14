# Road rage proxy assessment: California Crash Reporting System (CCRS)

Generated 2026-11-12 by `build_road_rage_proxy.py`. Every number below is computed from the CCRS tables queried on data.ca.gov (package last modified 2026-11-13).

## Verdict

**Descriptive context only.** The CCRS data are not adequate as a road-rage exposure or outcome variable in the association models or the attributable-burden model. They can support a descriptive paragraph or supplementary figure on crash patterns in the study counties from 2016 onward, with the caveats below stated alongside.

## What was examined

- Source: California Highway Patrol, California Crash Reporting System, package `ccrs` on data.ca.gov. Three tables per year (Crashes, Parties, InjuredWitnessPassengers), years 2016-2026. Only the Crashes tables were tabulated here.
- Field definitions: the publisher's "Raw Data Template" (CCRS raw data export layout, dated 9/27/2024).
- Geography: County Code is the county in which the crash occurred (publisher's definition); it is the alphabetical index of the 58 counties, verified against the recorded city names for all 15 study counties.
- Not examined: the Parties and InjuredWitnessPassengers tables (so no tabulation by driver age or at-fault party), and the four Caltrans "Crash Data on State Highway System" packages (2021-2024, state highways only), which were listed in the catalog but not opened.

## Is there a road-rage flag?

No. Neither the three CCRS tables (75, 49 and 22 fields in the 2019 tables) nor the publisher's layout document contains any field or value for road rage or aggressive driving. The closest fields are:

- `Primary Collision Factor Code`: A vehicle code violation, B other improper driving, C other than driver, D unknown, E fell asleep, dash not stated (publisher's definitions). Category A is 93.5% of study-county crashes across all years.
- `Primary Collision Factor Violation`: free text holding the Vehicle Code section. It has 6,544 distinct raw strings in the study counties; 92.3-94.1% of crashes per year parse to a section number, 4.5-5.1% are blank and 1.3-3.2% are words without a section number (rising over time).
- `HitRun` (felony or misdemeanor), and in the Parties table `Other Associate Factor`, `Inattention` and `StatedAge`.

Any aggressive-driving indicator therefore has to be constructed by the analyst from violation sections. The grouping used here:

- `unsafe_speed`: 22350 basic speed law (unsafe speed for conditions); 22349 maximum speed limit; 22348 excessive speed
- `following_too_closely`: 21703 following too closely
- `unsafe_lane_change`: 21658 lane straddling / unsafe lane change
- `unsafe_passing`: 21750-21759 overtaking and passing
- `reckless_or_speed_contest`: 23103-23105 reckless driving; 23109 speed contest / exhibition of speed
- `unsafe_turn_or_signal`: 22107 unsafe turning movement or lane move without signal; 22108 signal duration
- `signal_or_stop_sign`: 21453 red signal; 22450 stop sign

The "narrow composite" is the sum of the first five groups. Free-text entries without a section number were assigned by keyword; they are 0.7-1.8% of indicator crashes per year. The section descriptions are the analyst's reading of the California Vehicle Code and were not retrieved from an official legal source in this work; they should be checked before publication.

## Counts, 15 study counties combined

| year | all crashes | unsafe speed | following too closely | unsafe lane change | unsafe passing | reckless or speed contest | narrow composite | composite % of crashes | unsafe speed % of composite | hit-and-run % of crashes | with latitude % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 132,334 | 44,823 | 2,361 | 10,490 | 1,255 | 109 | 59,038 | 44.6 | 75.9 | 20.6 | 57.7 |
| 2017 | 132,166 | 45,131 | 2,165 | 10,597 | 1,311 | 94 | 59,298 | 44.9 | 76.1 | 21.4 | 65.7 |
| 2018 | 133,374 | 44,816 | 2,034 | 10,697 | 1,238 | 92 | 58,877 | 44.1 | 76.1 | 21.8 | 70.1 |
| 2019 | 130,950 | 43,535 | 2,010 | 10,616 | 1,303 | 120 | 57,584 | 44.0 | 75.6 | 22.3 | 69.8 |
| 2020 | 98,818 | 28,313 | 1,069 | 7,475 | 927 | 133 | 37,917 | 38.4 | 74.7 | 25.9 | 70.7 |
| 2021 | 113,348 | 34,378 | 1,336 | 9,148 | 1,057 | 129 | 46,048 | 40.6 | 74.7 | 26.4 | 74.9 |
| 2022 | 113,860 | 34,262 | 1,356 | 8,745 | 1,069 | 117 | 45,549 | 40.0 | 75.2 | 26.7 | 76.6 |
| 2023 | 117,677 | 36,169 | 1,359 | 9,343 | 1,046 | 126 | 48,043 | 40.8 | 75.3 | 26.6 | 77.8 |
| 2024 | 118,791 | 35,853 | 1,605 | 9,722 | 1,084 | 146 | 48,410 | 40.8 | 74.1 | 26.0 | 78.3 |
| 2025 | 113,905 | 34,148 | 1,929 | 9,399 | 1,090 | 165 | 46,731 | 41.0 | 73.1 | 25.0 | 79.1 |
| 2026 | 88,461 | 26,703 | 1,836 | 7,385 | 887 | 96 | 36,907 | 41.7 | 72.4 | 23.1 | 80.2 |

County-by-year counts for every indicator are in `road_rage_proxy_counts.csv` (165 rows: 15 counties x 11 years).

## Selected county values

Population denominators are approximate: ACS 5-year county population, 2015-2019 for crash years up to 2019 and 2020-2024 afterwards.

| county | all crashes 2019 | all crashes 2024 | narrow pct of crashes 2019 | narrow pct of crashes 2024 | narrow per 100k pop 2019 | narrow per 100k pop 2024 |
|---|---|---|---|---|---|---|
| Alameda | 23,091 | 20,119 | 46.94 | 45.71 | 654.3 | 557.5 |
| Contra Costa | 12,331 | 11,256 | 46.89 | 42.87 | 506.2 | 414.2 |
| Marin | 2,922 | 2,653 | 44.25 | 39.69 | 497.4 | 408.2 |
| Merced | 4,424 | 3,756 | 31.8 | 27.08 | 518.5 | 350.4 |
| Napa | 1,860 | 1,708 | 35.27 | 33.02 | 469.8 | 418.2 |
| Sacramento | 21,326 | 20,487 | 45.94 | 39.77 | 642.7 | 511.2 |
| San Benito | 829 | 804 | 39.69 | 30.47 | 544.9 | 364.1 |
| San Francisco | 6,883 | 6,255 | 41.93 | 43.41 | 329.8 | 327.0 |
| San Joaquin | 11,964 | 10,996 | 44.37 | 39.21 | 714.9 | 540.7 |
| San Mateo | 7,602 | 6,390 | 43.36 | 40.59 | 429.5 | 349.4 |
| Santa Clara | 16,270 | 14,267 | 51.02 | 48.78 | 430.7 | 365.9 |
| Santa Cruz | 3,552 | 3,014 | 30.83 | 32.58 | 399.7 | 370.7 |
| Solano | 5,153 | 5,557 | 43.06 | 39.54 | 502.2 | 486.2 |
| Sonoma | 5,532 | 3,849 | 36.14 | 35.78 | 400.0 | 283.9 |
| Stanislaus | 7,211 | 7,680 | 32.92 | 28.98 | 437.0 | 401.8 |

## Why this is not adequate for modelling

1. **Definition.** There is no road-rage variable. The composite measures what an officer recorded as the primary cause of a crash that happened, not driver anger or hostile behaviour, and road-rage incidents that do not end in a reported crash are not in the data at all.
2. **Specificity.** Unsafe speed makes up 72.4-76.1% of the narrow composite each year, and it is almost entirely section 22350, the basic speed law (404,765 crashes over all years, against 81 for the maximum-speed sections). That citation is commonly the recorded primary factor for rear-end crashes in dense traffic, so the composite largely tracks congestion, which is the study's exposure. Using it as a mediator or outcome of long commutes would be close to circular.
3. **Sparse specific indicators.** The most specific group, reckless driving or speed contest, has 92-165 crashes per year across all 15 counties, and 17 of 165 county-years have none. The smallest county-year (San Benito, 2026) has 562 crashes in total.
4. **Coverage years.** CCRS on data.ca.gov starts in 2016; nothing is available for 2010-2015, so the first part of the study window is uncovered. 2026 is a partial year (88,461 crashes so far). The tables are still being updated, and the `Is Preliminary` flag is set on at most 93 records in any year (0.1% of that year's crashes, in 2026), so it does not show how incomplete recent years are. The Parties table is missing for 2025.
5. **Denominator.** No vehicle-miles-travelled or trip denominator was acquired, and crash counts depend on traffic volume, through traffic and reporting practice. County is the place of occurrence, not the driver's county of residence, so a commuter from an outer county who crashes in the core is counted in the core. Per-resident rates are therefore only a rough scale adjustment.
6. **Spatial resolution.** A latitude is recorded for 57.7-80.2% of crashes per year, so tract-level assignment would be incomplete and probably not at random.
7. **Period effects.** Crash counts fell from 130,950 in 2019 to 98,818 in 2020, and the composite's share of crashes shifted from 44.0% to 38.4%, consistent with a change in traffic conditions and not obviously in driver behaviour.

## What it can support

- A descriptive statement of crash volume and the mix of recorded primary factors in the study counties, 2016 onward, clearly labelled as crash-causation attributions.
- The hit-and-run share (20.6-26.7% of crashes per year) as a separate descriptive series.
- If age-specific context is wanted, the Parties table carries `StatedAge` and `IsAtFault`; that tabulation was not done here.

For the manuscript, driving stress and road rage are better treated as a mechanism discussed from the literature than as a measured variable.
