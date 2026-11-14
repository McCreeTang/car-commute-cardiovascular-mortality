# Cardiovascular mortality attributable to car-commute sitting time: methods and results of the burden model

Under the central generic-sitting assumption (scenario A), the lengthening of car commutes between 2010 and 2019 is associated with a median of 8.0 (0.4 to 20.8) cardiovascular deaths per year among residents aged 35 and over in the 14 study counties, which is 0.034 (0.002 to 0.089)% of an estimated 23,516 baseline cardiovascular deaths. The burden is small in absolute and relative terms, and its lower bound is close to zero because the share of car time that adds to total sitting is unknown and was allowed to range from 0 to 1. The low-slope scenario (B) gives 3.2 (-2.0 to 15.6) deaths per year and its interval spans zero. The driving-specific hazard ratios from the single available cohort of US men (scenario E) give a much larger median, 147 (-39 to 379) deaths per year, and that interval also spans zero. The two approaches therefore differ by a factor of about 18 at the median, and the data cannot say which is closer to the truth. These are model-based associations under declared assumptions, not causal effects; no cardiovascular outcome was observed in any commuter. A separately labelled post-2020 scenario (section 7) applies 2019 mortality rates to 2024 commuting; under scenario A it implies that 36 (22 to 50)% of the burden of the 2010-2019 lengthening had been reversed by 2024. That scenario is not an estimate of observed mortality.

## 1. Data and population

Exposure comes from the 1-year ACS Public Use Microdata Sample person file for 2010 and 2019 (primary period) and 2021 to 2024 (post-2020, descriptive only; no 2020 file exists). All persons aged 16 or older living in the 14 counties with person-level data were used: 79,962 records in 2010, 89,930 in 2019, and 92,285, 93,647, 94,146 and 95,266 in 2021, 2022, 2023 and 2024. The burden engine uses 2010, 2019 and 2024; 2021 to 2023 enter the exposure tables only. The 7,738 records in these six years from the PUMA that combines San Benito with part of Monterey County were excluded, so San Benito is not in the burden model. Non-workers, people working from home and commuters by non-car modes are kept in every denominator with zero exposure. Weighted population totals and their replicate-weight standard errors by county, region, year and age band were compared with `pums_county_year_age.parquet` over 612 rows; the maximum absolute difference was 0 persons.

Baseline mortality is the 2019 county cardiovascular disease death rate for ages 35-64 and 65+ (CDC, model-smoothed, age-standardised within band) from `mortality_long.parquet`. Age bands: 16-34, 35-44, 45-54, 55-64, 65+, and the aggregates 35-64 and 65+ that match the mortality data. County groups: core nine, five adjacent, all 14.

## 2. Exposure

For person *i* with one-way travel time *t_i* (minutes) by car alone or carpool:

- hours in the car on a commuting day: *a_i* = 2 x *t_i* / 60 (zero for everyone else);
- weekly car-commute hours: *h_i* = *d* x *a_i*, where *d* is commute days per week;
- net additional daily sitting: *x_i* = *f* x *h_i* / 7, where *f* is the fraction of car time that is additional to, rather than a replacement for, other sitting.

**Commute days per week (assumed).** The ACS does not ask how many days a week a person commutes. The model uses *d* = 4.5 as the central value with a uniform range of 4 to 5, and 3 and 5 as fixed sensitivity values. As a plausibility check only, five days a week multiplied by the mean weeks worked in the past year among 2019 car commuters (48.8 of 52) gives 4.70 days per week averaged over the year.

**Travel-time top-code.** The Census Bureau replaces every travel time above a threshold with a single value. In this file the replacement value is 141, 142 and 141 minutes in 2010, 2019 and 2024, and the largest uncensored value is 100, 115 and 115 minutes. In 2021, 2022 and 2023 the replacement value is 141, 141 and 141 minutes and the largest uncensored value is 115, 118 and 115 minutes. The threshold therefore differs between 2010 and 2019. The published replacement value was kept in the main analysis. Two sensitivity analyses replace it with the largest uncensored value of the year (a lower bound) and with 180 minutes. Every top-coded commuter exceeds 10 hours a week and 30 minutes one way under any value of *d* used here, so the categorical scenario and the 30-minute cap are unaffected by the top-code.

**Travel time is door-to-door.** It is treated as in-vehicle time, which overstates sitting slightly for car modes and more for transit; the all-seated-motorised sensitivity (car, taxi, motorcycle, bus, rail, ferry) should be read with that in mind.

### Exposure results

Table 1. Car-commute exposure among all residents, all 14 counties (car alone or carpool; weekly hours at *d* = 4.5). Standard errors from the 80 replicate weights in parentheses.

| Age | Year | Residents | Car commuters, % of residents | Mean one-way minutes, car commuters | One-way 60-89 min, % of residents | One-way 90+ min, % of residents | Mean weekly car-commute hours per resident | More than 10 h/week, % of residents |
|---|---|---|---|---|---|---|---|---|
| 16-34 | 2010 | 2,741,786 | 45.0 (0.3) | 24.5 (0.2) | 2.4 | 0.9 | 1.65 (0.02) | 1.3 (0.1) |
| 16-34 | 2019 | 2,941,599 | 49.5 (0.4) | 29.2 (0.3) | 3.8 | 2.0 | 2.17 (0.03) | 2.8 (0.1) |
| 16-34 | 2024 | 2,872,955 | 47.1 (0.4) | 28.3 (0.2) | 3.2 | 1.6 | 2.00 (0.02) | 2.5 (0.1) |
| 35-44 | 2010 | 1,491,664 | 59.6 (0.6) | 27.4 (0.3) | 4.1 | 1.5 | 2.45 (0.03) | 2.5 (0.1) |
| 35-44 | 2019 | 1,568,969 | 61.7 (0.4) | 32.9 (0.4) | 6.4 | 3.4 | 3.05 (0.04) | 4.9 (0.2) |
| 35-44 | 2024 | 1,655,047 | 57.2 (0.5) | 31.0 (0.3) | 5.0 | 2.5 | 2.66 (0.04) | 3.7 (0.2) |
| 45-54 | 2010 | 1,503,244 | 58.4 (0.5) | 26.4 (0.2) | 3.0 | 1.5 | 2.31 (0.03) | 2.1 (0.1) |
| 45-54 | 2019 | 1,433,257 | 62.1 (0.5) | 32.5 (0.3) | 6.1 | 3.3 | 3.02 (0.03) | 4.6 (0.2) |
| 45-54 | 2024 | 1,410,364 | 57.7 (0.6) | 30.8 (0.4) | 5.2 | 2.5 | 2.67 (0.04) | 3.8 (0.2) |
| 55-64 | 2010 | 1,193,036 | 46.3 (0.5) | 25.5 (0.3) | 2.4 | 1.0 | 1.77 (0.03) | 1.6 (0.1) |
| 55-64 | 2019 | 1,381,777 | 50.3 (0.5) | 30.6 (0.4) | 4.2 | 2.3 | 2.31 (0.04) | 3.3 (0.2) |
| 55-64 | 2024 | 1,340,845 | 47.6 (0.5) | 29.8 (0.4) | 3.6 | 1.9 | 2.13 (0.04) | 2.9 (0.2) |
| 35-64 | 2010 | 4,187,944 | 55.4 (0.3) | 26.6 (0.1) | 3.2 | 1.4 | 2.21 (0.02) | 2.1 (0.1) |
| 35-64 | 2019 | 4,384,003 | 58.2 (0.3) | 32.1 (0.2) | 5.6 | 3.0 | 2.81 (0.02) | 4.3 (0.1) |
| 35-64 | 2024 | 4,406,256 | 54.4 (0.3) | 30.6 (0.2) | 4.7 | 2.3 | 2.50 (0.02) | 3.5 (0.1) |
| 65+ | 2010 | 1,222,553 | 10.7 (0.3) | 24.0 (0.6) | 0.4 | 0.3 | 0.39 (0.01) | 0.4 (0.1) |
| 65+ | 2019 | 1,698,224 | 13.5 (0.3) | 28.5 (0.5) | 0.9 | 0.5 | 0.58 (0.02) | 0.7 (0.1) |
| 65+ | 2024 | 1,907,542 | 12.6 (0.3) | 27.5 (0.5) | 0.8 | 0.4 | 0.52 (0.02) | 0.6 (0.1) |

Among residents aged 35-64, mean weekly car-commute hours per resident rose from 2.21 (SE 0.02) in 2010 to 2.81 (SE 0.02) in 2019 and stood at 2.50 (SE 0.02) in 2024. Mean one-way travel time among car commuters aged 35-64 rose from 26.6 to 32.1 minutes between 2010 and 2019. Part of the rise in hours per resident reflects a larger share of residents commuting by car (55.4% in 2010, 58.2% in 2019), which is why counterfactual 1b below separates duration from participation. The 2024 values describe a differently selected group of commuters because working from home rose from 5.3% to 12.7% of residents aged 35-64 between 2019 and 2024.

Table 2. Mean weekly car-commute hours per resident by county group (*d* = 4.5; SE in parentheses).

| Age | County group | Hours 2010 | Hours 2019 | Hours 2024 | One-way min 2010 | One-way min 2019 | One-way min 2024 |
|---|---|---|---|---|---|---|---|
| 16-34 | Core nine counties | 1.62 (0.02) | 2.08 (0.03) | 1.90 (0.03) | 24.3 | 29.2 | 28.0 |
| 16-34 | Five adjacent counties | 1.73 (0.04) | 2.35 (0.06) | 2.20 (0.05) | 25.0 | 29.1 | 28.8 |
| 35-64 | Core nine counties | 2.20 (0.02) | 2.73 (0.02) | 2.43 (0.02) | 26.4 | 32.0 | 30.5 |
| 35-64 | Five adjacent counties | 2.23 (0.03) | 3.01 (0.04) | 2.68 (0.05) | 27.0 | 32.4 | 30.9 |
| 65+ | Core nine counties | 0.39 (0.02) | 0.57 (0.02) | 0.53 (0.02) | 23.9 | 28.3 | 26.9 |
| 65+ | Five adjacent counties | 0.36 (0.03) | 0.58 (0.04) | 0.50 (0.03) | 24.3 | 28.9 | 29.2 |

The year-by-year path for 2021 to 2024 is in section 7 (Table 9).

Ages 16-34: exposure is reported in Table 1 and in [exposure_distributions.csv]({{artifact:264325c1-f985-4878-a7e9-62e12300e29d}}). **Burden was not assessed under age 35 because no baseline cardiovascular mortality rates are available for that age range; none were imputed.**

## 3. Risk functions

Every relative risk was read by row id from `dose_response_parameters.csv` at run time. Of the 62 rows in that table, 31 are flagged abstract_only; the 8 rows used here (DR001, DR002, DR003, DR027, DR028, DR033, DR047, DR050) are all full-text rows, so **no abstract-only or press-release estimate enters the model** (abstract-only rows used: none).

Table 3. Risk parameters.

| Parameter | Estimate | Interval | Row id | Abstract only | Source and field | Monte Carlo distribution |
|---|---|---|---|---|---|---|
| RR of CVD mortality per additional h/day sitting, scenario A (central) | 1.02 | 1.01-1.03 (95% CI) | DR027 | False | Patterson 2018; read from estimate/ci columns | log-normal, SE(log)=0.00500 from the published CI |
| RR per h/day, scenario B (below 6 h/day total sitting) | 1.01 | 0.99-1.02 (95% CI) | DR028 | False | Patterson 2018; read from notes field: "Below 6 h/day: 1.01 (0.99-1.02)" | log-normal, SE(log)=0.00762 from the published CI |
| RR per h/day, scenario C (above 6 h/day total sitting) | 1.04 | 1.03-1.04 (95% CI) | DR028 | False | Patterson 2018; read from estimate/ci columns | log-normal, SE(log)=0.00246 from the published CI |
| RR of fatal+non-fatal CVD per h/day sedentary, scenario D | 1.05 | 1.02-1.07 (95% CI) | DR033 | False | Onagbiye 2024; read from notes field: "Per hour sedentary RR 1.05 (1.02-1.07)" | log-normal, SE(log)=0.01221 from the published CI |
| HR CVD mortality, 4-7 vs <4 h/week in a car, scenario E | 1.09 | 0.78-1.52 (95% CI) | DR001 | False | Warren 2010; read from estimate/ci columns | log-normal, SE(log)=0.17020 from the published CI |
| HR CVD mortality, 7-10 vs <4 h/week in a car, scenario E | 1.23 | 0.89-1.7 (95% CI) | DR002 | False | Warren 2010; read from estimate/ci columns | log-normal, SE(log)=0.16510 from the published CI |
| HR CVD mortality, >10 vs <4 h/week in a car, scenario E | 1.5 | 1.08-2.09 (95% CI) | DR003 | False | Warren 2010; read from estimate/ci columns | log-normal, SE(log)=0.16842 from the published CI |
| ILLUSTRATIVE: IRR of MI onset within 2 h of an anger outburst | 2.43 | 2.01-2.9 (95% CI) | DR047 | False | Mostofsky 2013; read from estimate/ci columns | log-normal, SE(log)=0.09352 from the published CI |
| ILLUSTRATIVE: OR of acute stroke within 1 h of anger or emotional upset | 1.37 | 1.15-1.64 (99% CI) | DR050 | False | Smyth 2022; read from estimate/ci columns | log-normal, SE(log)=0.06890 from the published CI |

- Scenarios A to D (generic sitting): RR_i = exp(beta x *x_i*), beta = ln(RR per hour per day). A is the linear slope; B and C are the slopes below and above 6 hours of total daily sitting, used as low and high variants because individual total sitting is unknown; D is the per-hour slope for fatal plus non-fatal cardiovascular disease, applied to mortality as an upper alternative.
- Scenario E (driving-specific): RR_i = 1 for *h_i* < 4, HR_1 for 4 <= *h_i* < 7, HR_2 for 7 <= *h_i* <= 10, HR_3 for *h_i* > 10 hours per week in a car. The hazard ratios come from men only. E_both applies them to both sexes, which is an assumption; E_men restricts exposure, population and mortality rates to men. No displacement factor *f* is applied because the exposure in the source study is car time itself. The source measured all car time, whereas only commute car time is available here.
- The same relative risks are applied in every age band, because the parameter table holds no usable age-specific estimate.

## 4. Counterfactuals and attributable burden

For a stratum with person weights *w_i*, the potential impact fraction is

PIF = [ sum_i *w_i* RR(*x_i*) - sum_i *w_i* RR(*x_i*') ] / sum_i *w_i* RR(*x_i*),

where *x_i*' is the counterfactual exposure:

1. **2010 distribution kept.** PIF = 1 - E_2010[RR] / E_2019[RR], with each expectation taken over all residents of the stratum in that survey year.
2. **(1b, added) 2010 durations with the 2019 car-commuter share.** E_cf[RR] = 1 + s_2019 x (E_2010[RR | car commuter] - 1), where s_2019 is the 2019 share of residents commuting by car. This removes the part of counterfactual 1 that is due to more residents commuting by car in 2019 than in the post-recession year 2010.
3. **Cap.** One-way car travel time capped at 30 minutes.
4. **No car commuting.** *x_i*' = 0 for everyone; a theoretical upper bound, not a feasible scenario.

Attributable deaths per year in county group *g* and mortality age band *b* are the sum over counties of county-specific fractions times county baseline deaths:

AD_gb = sum over counties c in g of PIF_cb x (rate_cb / 100,000) x N_cb,

with rate_cb the 2019 county cardiovascular death rate and N_cb the 2019 weighted PUMS population. The reported attributable fraction for 35-64, 65+ and 35+ is AD_gb divided by baseline deaths (a death-weighted mean of county fractions). For the 10-year bands, which have no mortality rates, the fraction is the pooled-person PIF of the stratum and no deaths are computed.

## 5. Uncertainty

Monte Carlo simulation with 40,000 draws and seed 20261113 propagates jointly:

- relative risks: log-normal, SE(log) = (ln upper - ln lower) / (2 x z) from the published interval; the three scenario-E hazard ratios share a reference group and are drawn with an assumed correlation of 0.5;
- survey sampling error: each draw adds to every full-sample weighted sum a random combination of its 80 replicate deviations, theta* = theta_0 + sqrt(4/80) x sum_r z_r (theta_r - theta_0) with z_r standard normal, which reproduces the ACS replicate variance and keeps all strata of a survey year correlated; the 2010, 2019 and 2024 samples are perturbed independently;
- assumed parameters: *d* uniform on 4 to 5; *f* uniform on 0 to 1 for scenarios A to D (results at fixed *f* = 0.25, 0.5, 0.75 and 1.0 are also reported);
- baseline mortality rates: log-normal from the published interval of each county rate (treated as a 95% interval; an addition to the three sources named in the task).

Results are medians with 2.5th and 97.5th percentiles (95% uncertainty interval, UI). "Central" values in the result files are deterministic evaluations at *d* = 4.5, *f* = 0.5 and the point estimates. The full list of parameters and assumptions is in [burden_assumptions.csv]({{artifact:a0176575-f463-48e3-806d-6cab09f894d7}}).

## 6. Results

Table 4. Attributable cardiovascular deaths per year and attributable fraction, ages 35 and over, all 14 counties, 2019 (median and 95% UI; *f* uniform on 0 to 1 for A to D). Baseline deaths: 23,516 (95% UI 23,270 to 23,764) for both sexes and 12,863 for men.

| Scenario | Counterfactual | Attributable deaths per year | Attributable fraction, % | Share of draws above zero | UI spans zero |
|---|---|---|---|---|---|
| A central sitting slope | (1) 2010 distribution kept | 8.0 (0.4 to 20.8) | 0.034 (0.002 to 0.089) | 1.000 | no |
| A central sitting slope | (1b) 2010 durations, 2019 car-commuter share | 4.6 (0.2 to 12.4) | 0.020 (0.001 to 0.053) | 1.000 | no |
| A central sitting slope | (2) one-way car commute capped at 30 min | 8.4 (0.4 to 21.8) | 0.036 (0.002 to 0.093) | 1.000 | no |
| A central sitting slope | (3) no car commuting (upper bound) | 28.6 (1.4 to 73.1) | 0.122 (0.006 to 0.311) | 1.000 | no |
| B low sitting slope | (1) 2010 distribution kept | 3.2 (-2.0 to 15.6) | 0.014 (-0.009 to 0.066) | 0.906 | yes |
| B low sitting slope | (1b) 2010 durations, 2019 car-commuter share | 1.9 (-1.2 to 9.2) | 0.008 (-0.005 to 0.039) | 0.906 | yes |
| B low sitting slope | (2) one-way car commute capped at 30 min | 3.4 (-2.1 to 16.3) | 0.014 (-0.009 to 0.069) | 0.906 | yes |
| B low sitting slope | (3) no car commuting (upper bound) | 11.5 (-7.3 to 55.3) | 0.049 (-0.031 to 0.235) | 0.906 | yes |
| C high sitting slope | (1) 2010 distribution kept | 16.8 (0.8 to 35.9) | 0.071 (0.004 to 0.153) | 1.000 | no |
| C high sitting slope | (1b) 2010 durations, 2019 car-commuter share | 9.8 (0.5 to 21.5) | 0.042 (0.002 to 0.091) | 1.000 | no |
| C high sitting slope | (2) one-way car commute capped at 30 min | 17.8 (0.9 to 37.5) | 0.076 (0.004 to 0.160) | 1.000 | no |
| C high sitting slope | (3) no car commuting (upper bound) | 60.2 (3.0 to 124.7) | 0.256 (0.013 to 0.530) | 1.000 | no |
| D fatal + non-fatal slope | (1) 2010 distribution kept | 19.7 (1.0 to 52.1) | 0.084 (0.004 to 0.221) | 1.000 | no |
| D fatal + non-fatal slope | (1b) 2010 durations, 2019 car-commuter share | 11.5 (0.6 to 31.0) | 0.049 (0.002 to 0.132) | 1.000 | no |
| D fatal + non-fatal slope | (2) one-way car commute capped at 30 min | 20.8 (1.0 to 55.3) | 0.089 (0.004 to 0.235) | 1.000 | no |
| D fatal + non-fatal slope | (3) no car commuting (upper bound) | 70.4 (3.5 to 181.7) | 0.299 (0.015 to 0.773) | 1.000 | no |
| E driving-specific HRs, both sexes | (1) 2010 distribution kept | 147.1 (-39.1 to 379.5) | 0.626 (-0.166 to 1.612) | 0.936 | yes |
| E driving-specific HRs, both sexes | (1b) 2010 durations, 2019 car-commuter share | 109.9 (-14.2 to 265.5) | 0.468 (-0.060 to 1.129) | 0.957 | yes |
| E driving-specific HRs, both sexes | (2) one-way car commute capped at 30 min | 187.0 (-80.1 to 497.9) | 0.795 (-0.340 to 2.115) | 0.921 | yes |
| E driving-specific HRs, both sexes | (3) no car commuting (upper bound) | 382.5 (-224.6 to 1117.0) | 1.626 (-0.957 to 4.758) | 0.886 | yes |
| E driving-specific HRs, men only | (1) 2010 distribution kept | 110.5 (-22.4 to 274.6) | 0.859 (-0.174 to 2.134) | 0.947 | yes |
| E driving-specific HRs, men only | (1b) 2010 durations, 2019 car-commuter share | 86.5 (-8.5 to 206.4) | 0.672 (-0.066 to 1.602) | 0.962 | yes |
| E driving-specific HRs, men only | (2) one-way car commute capped at 30 min | 154.2 (-58.0 to 393.7) | 1.199 (-0.454 to 3.055) | 0.927 | yes |
| E driving-specific HRs, men only | (3) no car commuting (upper bound) | 299.6 (-153.9 to 835.3) | 2.329 (-1.197 to 6.486) | 0.898 | yes |

Reading Table 4:

- **Scenario A, 2010 to 2019 lengthening:** 8.0 (0.4 to 20.8) deaths per year, 0.034 (0.002 to 0.089)% of baseline deaths. Holding the 2019 car-commuter share fixed and changing durations only (1b) gives 4.6 (0.2 to 12.4). Capping one-way car commutes at 30 minutes gives 8.4 (0.4 to 21.8), and removing all car commuting gives 28.6 (1.4 to 73.1).
- **Scenarios B, C and D** scale the same exposure contrast by their slopes: 3.2 (-2.0 to 15.6) (B), 16.8 (0.8 to 35.9) (C) and 19.7 (1.0 to 52.1) (D) deaths per year for counterfactual 1. The interval for B spans zero in 180 of its 180 rows with deaths (strata x counterfactuals x settings of *f*) because the published lower confidence limit of that slope is below 1.
- **Scenario E** gives 147 (-39 to 379) deaths per year for both sexes and 110 (-22 to 275) for men only under counterfactual 1, and 382 (-225 to 1117) under the no-car bound. The interval spans zero in 33 of 36 E_both rows and 32 of 36 E_men rows, because the confidence intervals of the two lower hazard ratios include 1.
- The intervals for A, C and D exclude zero only because their slope confidence intervals exclude 1 and *f* is assumed positive; with *f* = 0 the burden is zero by construction, and the lower bounds sit close to zero.

Table 5. Attributable deaths per year by mortality age band, all 14 counties, 2019 (median and 95% UI).

| Age | Scenario | (1) 2010 distribution kept | (1b) 2010 durations, 2019 car-commuter share | (2) one-way car commute capped at 30 min | (3) no car commuting (upper bound) | Baseline deaths |
|---|---|---|---|---|---|---|
| 35-64 | A central sitting slope | 3.0 (0.1 to 7.8) | 2.3 (0.1 to 6.0) | 4.3 (0.2 to 11.1) | 13.4 (0.7 to 34.2) | 3554 |
| 35-64 | B low sitting slope | 1.2 (-0.8 to 5.8) | 0.9 (-0.6 to 4.5) | 1.7 (-1.1 to 8.3) | 5.4 (-3.4 to 25.9) | 3554 |
| 35-64 | C high sitting slope | 6.3 (0.3 to 13.3) | 4.9 (0.2 to 10.4) | 9.1 (0.5 to 19.0) | 28.1 (1.4 to 58.1) | 3554 |
| 35-64 | D fatal + non-fatal slope | 7.4 (0.4 to 19.4) | 5.7 (0.3 to 15.2) | 10.6 (0.5 to 27.8) | 32.9 (1.6 to 84.5) | 3554 |
| 35-64 | E driving-specific HRs, both sexes | 64.3 (-3.4 to 140.9) | 56.3 (0.5 to 120.6) | 95.2 (-38.5 to 245.0) | 185.5 (-98.6 to 502.5) | 3554 |
| 35-64 | E driving-specific HRs, men only | 56.6 (-0.5 to 119.3) | 47.4 (2.9 to 97.6) | 87.2 (-32.0 to 216.3) | 161.4 (-73.2 to 415.3) | 2532 |
| 65+ | A central sitting slope | 4.9 (0.2 to 13.3) | 2.3 (0.1 to 6.5) | 4.1 (0.2 to 10.8) | 15.2 (0.8 to 38.9) | 19961 |
| 65+ | B low sitting slope | 2.0 (-1.3 to 9.8) | 0.9 (-0.6 to 4.7) | 1.7 (-1.0 to 8.1) | 6.1 (-3.9 to 29.4) | 19961 |
| 65+ | C high sitting slope | 10.4 (0.5 to 23.1) | 4.8 (0.2 to 11.7) | 8.7 (0.4 to 18.7) | 32.0 (1.6 to 66.7) | 19961 |
| 65+ | D fatal + non-fatal slope | 12.2 (0.6 to 33.3) | 5.6 (0.3 to 16.4) | 10.2 (0.5 to 27.6) | 37.4 (1.9 to 97.4) | 19961 |
| 65+ | E driving-specific HRs, both sexes | 82.1 (-38.2 to 243.6) | 53.2 (-16.7 to 152.5) | 91.7 (-42.0 to 253.9) | 196.6 (-124.8 to 617.4) | 19961 |
| 65+ | E driving-specific HRs, men only | 53.5 (-24.5 to 161.5) | 38.7 (-14.7 to 116.8) | 66.7 (-26.6 to 179.2) | 138.3 (-81.3 to 421.8) | 10331 |

For scenario A and counterfactual 1 the attributable fraction is 0.084 (0.004 to 0.218)% at ages 35-64 and 0.025 (0.001 to 0.067)% at 65+. More of the attributable deaths fall in the 65+ band (4.9 (0.2 to 13.3) against 3.0 (0.1 to 7.8)) only because baseline deaths there are far higher; see the limitation on within-band age below, which makes the 65+ figure the less reliable of the two.

Table 6. Attributable deaths per year by county group, counterfactual 1 (2010 distribution kept), 2019 (median and 95% UI; attributable fraction in % in brackets).

| Scenario | County group | 35-64 | 65+ | 35+ |
|---|---|---|---|---|
| A central sitting slope | Core nine counties | 1.5 (0.1 to 3.8) [0.070] | 3.1 (0.2 to 8.4) [0.023] | 4.6 (0.2 to 12.1) [0.030] |
| A central sitting slope | Five adjacent counties | 1.5 (0.1 to 4.0) [0.104] | 1.8 (0.1 to 5.3) [0.027] | 3.3 (0.2 to 9.0) [0.041] |
| A central sitting slope | All 14 counties | 3.0 (0.1 to 7.8) [0.084] | 4.9 (0.2 to 13.3) [0.025] | 8.0 (0.4 to 20.8) [0.034] |
| E driving-specific HRs, both sexes | Core nine counties | 36.9 (0.6 to 78.5) [1.754] | 54.7 (-24.2 to 163.3) [0.410] | 92.1 (-21.2 to 235.3) [0.596] |
| E driving-specific HRs, both sexes | Five adjacent counties | 27.4 (-5.0 to 64.3) [1.885] | 26.4 (-15.4 to 87.7) [0.398] | 53.9 (-19.2 to 148.3) [0.667] |
| E driving-specific HRs, both sexes | All 14 counties | 64.3 (-3.4 to 140.9) [1.809] | 82.1 (-38.2 to 243.6) [0.411] | 147.1 (-39.1 to 379.5) [0.626] |

Table 7. Scenarios A to D at fixed values of the net-sitting fraction *f*: attributable deaths per year, ages 35+, all 14 counties, counterfactual 1 (median and 95% UI over the remaining uncertainty).

| Scenario | f = 0.25 | f = 0.5 | f = 0.75 | f = 1.0 | f uniform 0 to 1 |
|---|---|---|---|---|---|
| A central sitting slope | 4.2 (2.1 to 6.7) | 8.5 (4.2 to 13.5) | 12.8 (6.2 to 20.4) | 17.1 (8.3 to 27.3) | 8.0 (0.4 to 20.8) |
| B low sitting slope | 2.1 (-1.1 to 5.5) | 4.2 (-2.1 to 11.0) | 6.4 (-3.2 to 16.6) | 8.5 (-4.3 to 22.1) | 3.2 (-2.0 to 15.6) |
| C high sitting slope | 8.4 (6.6 to 10.6) | 17.0 (13.3 to 21.2) | 25.6 (20.1 to 32.1) | 34.4 (26.9 to 43.1) | 16.8 (0.8 to 35.9) |
| D fatal + non-fatal slope | 10.5 (5.2 to 16.5) | 21.1 (10.5 to 33.4) | 31.8 (15.8 to 50.6) | 42.7 (21.1 to 68.2) | 19.7 (1.0 to 52.1) |

Table 8. Pooled-person attributable fraction (%) by 10-year age band, scenario A, all 14 counties (median and 95% UI; *f* uniform 0 to 1). The 2024 column is descriptive: fractions only, because county age-specific mortality ends in 2019/2020, and 2024 commuters are a differently selected group.

| Age | Year | (1) 2010 distribution kept | (1b) 2010 durations, 2019 car-commuter share | (2) one-way car commute capped at 30 min | (3) no car commuting (upper bound) |
|---|---|---|---|---|---|
| 35-44 | 2019 | 0.078 (0.004 to 0.207) | 0.068 (0.003 to 0.177) | 0.128 (0.006 to 0.332) | 0.402 (0.020 to 1.028) |
| 35-44 | 2024 | 0.027 (0.001 to 0.082) | 0.041 (0.002 to 0.111) | 0.102 (0.005 to 0.265) | 0.352 (0.017 to 0.901) |
| 45-54 | 2019 | 0.093 (0.005 to 0.244) | 0.074 (0.004 to 0.194) | 0.125 (0.006 to 0.323) | 0.399 (0.020 to 1.019) |
| 45-54 | 2024 | 0.046 (0.002 to 0.126) | 0.050 (0.002 to 0.132) | 0.101 (0.005 to 0.263) | 0.353 (0.017 to 0.900) |
| 55-64 | 2019 | 0.071 (0.004 to 0.187) | 0.051 (0.003 to 0.136) | 0.088 (0.004 to 0.229) | 0.306 (0.015 to 0.783) |
| 55-64 | 2024 | 0.046 (0.002 to 0.126) | 0.040 (0.002 to 0.108) | 0.077 (0.004 to 0.199) | 0.281 (0.014 to 0.718) |
| 35-64 | 2019 | 0.079 (0.004 to 0.205) | 0.064 (0.003 to 0.167) | 0.115 (0.006 to 0.297) | 0.371 (0.018 to 0.948) |
| 35-64 | 2024 | 0.039 (0.002 to 0.103) | 0.044 (0.002 to 0.115) | 0.094 (0.005 to 0.244) | 0.331 (0.016 to 0.845) |
| 65+ | 2019 | 0.025 (0.001 to 0.067) | 0.012 (0.001 to 0.034) | 0.020 (0.001 to 0.053) | 0.077 (0.004 to 0.196) |
| 65+ | 2024 | 0.017 (0.001 to 0.048) | 0.008 (0.000 to 0.025) | 0.017 (0.001 to 0.044) | 0.069 (0.003 to 0.177) |

## 7. Post-2020 scenario: 2024 commuting with 2019 mortality rates (a scenario, not observed mortality)

**This section is a labelled scenario, not a finding about observed mortality.** It is kept out of the primary 2010-2019 results and out of every association analysis. Three points govern how to read it:

- **Assumption: 2019 mortality rates are applied to 2024.** No county cardiovascular mortality by age band exists after 2019/2020, so the 2019 county rates are multiplied by 2024 PUMS populations. Cardiovascular mortality changed during and after the pandemic for reasons unrelated to commuting, and none of that is represented here.
- **Post-2020 commuters are a differently selected group.** Working from home rose from 5.3% of residents aged 35-64 in 2019 to 21.2% in 2021 and was 12.7% in 2024, so who commutes by car, and how far, changed for reasons other than housing costs and congestion.
- **It is not an estimate of post-pandemic mortality.** The numbers are what the risk functions of section 3 imply for the change in car-commute time alone, with everything else held at 2019.

### Exposure after 2020

Table 9. Mean weekly car-commute hours per resident, 2010, 2019, 2021, 2022, 2023, 2024 (car alone or carpool; *d* = 4.5; SE in parentheses). There is no 2020 column because no standard 2020 ACS 1-year PUMS file exists. Years after 2019 are descriptive only.

| County group | Age | 2010 | 2019 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|
| All 14 counties | 16-34 | 1.65 (0.02) | 2.17 (0.03) | 1.67 (0.03) | 1.82 (0.03) | 1.96 (0.02) | 2.00 (0.02) |
| All 14 counties | 35-44 | 2.45 (0.03) | 3.05 (0.04) | 2.02 (0.02) | 2.42 (0.03) | 2.65 (0.04) | 2.66 (0.04) |
| All 14 counties | 45-54 | 2.31 (0.03) | 3.02 (0.03) | 2.11 (0.04) | 2.39 (0.03) | 2.65 (0.04) | 2.67 (0.04) |
| All 14 counties | 55-64 | 1.77 (0.03) | 2.31 (0.04) | 1.73 (0.03) | 1.88 (0.03) | 2.09 (0.04) | 2.13 (0.04) |
| All 14 counties | 35-64 | 2.21 (0.02) | 2.81 (0.02) | 1.96 (0.02) | 2.24 (0.02) | 2.47 (0.02) | 2.50 (0.02) |
| All 14 counties | 65+ | 0.39 (0.01) | 0.58 (0.02) | 0.44 (0.01) | 0.47 (0.02) | 0.53 (0.01) | 0.52 (0.02) |
| Core nine counties | 16-34 | 1.62 (0.02) | 2.08 (0.03) | 1.48 (0.03) | 1.68 (0.03) | 1.84 (0.03) | 1.90 (0.03) |
| Core nine counties | 35-64 | 2.20 (0.02) | 2.73 (0.02) | 1.79 (0.02) | 2.11 (0.02) | 2.36 (0.02) | 2.43 (0.02) |
| Core nine counties | 65+ | 0.39 (0.02) | 0.57 (0.02) | 0.45 (0.02) | 0.48 (0.02) | 0.53 (0.02) | 0.53 (0.02) |
| Five adjacent counties | 16-34 | 1.73 (0.04) | 2.35 (0.06) | 2.05 (0.05) | 2.09 (0.05) | 2.20 (0.05) | 2.20 (0.05) |
| Five adjacent counties | 35-64 | 2.23 (0.03) | 3.01 (0.04) | 2.36 (0.04) | 2.57 (0.05) | 2.75 (0.04) | 2.68 (0.05) |
| Five adjacent counties | 65+ | 0.36 (0.03) | 0.58 (0.04) | 0.43 (0.03) | 0.45 (0.03) | 0.53 (0.03) | 0.50 (0.03) |

Among residents aged 35-64 in all 14 counties, weekly car-commute hours per resident went from 2.81 in 2019 to 1.96 in 2021, which is below the 2010 value of 2.21, and then to 2.24 in 2022, 2.47 in 2023 and 2.50 in 2024. The share of residents aged 35-64 commuting by car was 58.2% in 2019, 45.7% in 2021 and 54.4% in 2024. All mode definitions, days-per-week values and the remaining metrics for these years are in [exposure_distributions.csv]({{artifact:264325c1-f985-4878-a7e9-62e12300e29d}}).

### Scenario definition

For target year 2024 and a kept distribution of year *y* (2010 or 2019), in county group *g* and mortality age band *b*:

AD_gb(y) = sum over counties c in g of [ 1 - E_y[RR] / E_2024[RR] ] x (rate_cb,2019 / 100,000) x N_cb,2024.

Counterfactual (i) keeps the 2010 distribution and counterfactual (ii) keeps the 2019 distribution. A negative AD(2019) means fewer modelled deaths than if the 2019 commute distribution had persisted. The share of the 2010-2019 burden reversed by the 2019-2024 change is

R_gb = -AD_gb(2019) / [ AD_gb(2010) - AD_gb(2019) ].

The denominator is the burden of the 2010-to-2019 change evaluated on the same 2024 population and 2019 rates, so R is not moved by population growth or ageing between 2019 and 2024. A second version divides the same numerator by the 2010-2019 burden as reported for 2019 in section 6 (2019 population). For the 10-year bands, which have no deaths, R is the pooled-person ratio (E_2019[RR] - E_2024[RR]) / (E_2019[RR] - E_2010[RR]). Uncertainty is propagated exactly as in section 5, with the same seed and the same 40,000 draws as the main run; the 2019 results recomputed inside this run differ from [burden_results.csv]({{artifact:ed1fab53-f43e-4523-ad34-8e73c8b798c8}}) by at most 2.8e-14 deaths.

### Scenario results

Table 10. SCENARIO. Attributable cardiovascular deaths per year for 2024 commuting and population with 2019 mortality rates, all 14 counties (median and 95% UI; *f* uniform on 0 to 1 for scenario A).

| Scenario | Age | (i) 2010 distribution kept | (ii) 2019 distribution kept | Share of draws at or below zero, (ii) | UI spans zero, (ii) | Baseline deaths (2024 population x 2019 rates) |
|---|---|---|---|---|---|---|
| A central sitting slope | 35-64 | 1.61 (0.08 to 4.27) | -1.43 (-3.88 to -0.07) | 1.000 | no | 3,609 |
| A central sitting slope | 65+ | 3.81 (0.19 to 10.68) | -1.48 (-5.54 to -0.04) | 0.993 | no | 22,454 |
| A central sitting slope | 35+ | 5.45 (0.27 to 14.78) | -3.00 (-8.94 to -0.14) | 1.000 | no | 26,064 |
| E driving-specific HRs, both sexes | 35-64 | 39.3 (1.1 to 84.8) | -26.6 (-65.9 to 5.3) | 0.947 | yes | 3,609 |
| E driving-specific HRs, both sexes | 65+ | 61.0 (-34.2 to 195.4) | -28.0 (-104.5 to 14.5) | 0.901 | yes | 22,454 |
| E driving-specific HRs, both sexes | 35+ | 101.3 (-30.3 to 273.4) | -55.5 (-163.2 to 16.9) | 0.932 | yes | 26,064 |
| E driving-specific HRs, men only | 35-64 | 37.7 (2.3 to 79.3) | -21.3 (-53.5 to 4.2) | 0.948 | yes | 2,615 |
| E driving-specific HRs, men only | 65+ | 46.4 (-28.8 to 155.1) | -12.7 (-62.4 to 17.1) | 0.813 | yes | 11,799 |
| E driving-specific HRs, men only | 35+ | 84.9 (-22.5 to 226.6) | -33.8 (-107.2 to 8.3) | 0.941 | yes | 14,413 |

Table 11. SCENARIO. Share of the 2010-2019 attributable burden reversed by the 2019-2024 change, all 14 counties (median and 95% UI, in %).

| Scenario | Age | R on the 2024 population | R against the 2019 burden as reported | Basis |
|---|---|---|---|---|
| A central sitting slope | 35-64 | 47% (37 to 57) | 49% (38 to 58) | deaths, county-weighted |
| A central sitting slope | 65+ | 30% (7 to 51) | 34% (8 to 57) | deaths, county-weighted |
| A central sitting slope | 35+ | 36% (22 to 50) | 39% (23 to 55) | deaths, county-weighted |
| E driving-specific HRs, both sexes | 35-64 | 41% (3 to 62) | 42% (3 to 64) | deaths, county-weighted |
| E driving-specific HRs, both sexes | 65+ | 33% (-35 to 104) | 37% (-39 to 116) | deaths, county-weighted |
| E driving-specific HRs, both sexes | 35+ | 36% (1 to 72) | 39% (1 to 77) | deaths, county-weighted |
| E driving-specific HRs, men only | 35-64 | 37% (-4 to 59) | 39% (-3 to 62) | deaths, county-weighted |
| E driving-specific HRs, men only | 65+ | 23% (-98 to 135) | 26% (-112 to 155) | deaths, county-weighted |
| E driving-specific HRs, men only | 35+ | 30% (-14 to 79) | 33% (-15 to 85) | deaths, county-weighted |
| A central sitting slope | 35-44 | 64% (48 to 79) | not available (no deaths) | pooled persons |
| A central sitting slope | 45-54 | 50% (36 to 64) | not available (no deaths) | pooled persons |
| A central sitting slope | 55-64 | 34% (17 to 50) | not available (no deaths) | pooled persons |

Table 12. SCENARIO. Ages 35+, by county group (median and 95% UI).

| Scenario | County group | (i) 2010 distribution kept | (ii) 2019 distribution kept | Reversed share R |
|---|---|---|---|---|
| A central sitting slope | Core nine counties | 3.17 (0.16 to 8.84) | -1.58 (-5.15 to -0.07) | 34% (15 to 53) |
| A central sitting slope | Five adjacent counties | 2.21 (0.11 to 6.33) | -1.28 (-4.47 to -0.05) | 38% (13 to 60) |
| A central sitting slope | All 14 counties | 5.45 (0.27 to 14.78) | -3.00 (-8.94 to -0.14) | 36% (22 to 50) |
| E driving-specific HRs, both sexes | Core nine counties | 59.7 (-20.9 to 171.0) | -36.1 (-105.5 to 5.6) | 39% (-6 to 97) |
| E driving-specific HRs, both sexes | Five adjacent counties | 40.1 (-10.2 to 110.7) | -17.6 (-71.5 to 16.4) | 33% (-68 to 107) |
| E driving-specific HRs, both sexes | All 14 counties | 101.3 (-30.3 to 273.4) | -55.5 (-163.2 to 16.9) | 36% (1 to 72) |

Reading Tables 10 to 12:

- **Scenario A, ages 35+.** With the 2010 distribution kept, the 2024 scenario gives 5.45 (0.27 to 14.78) deaths per year, against 7.97 (0.39 to 20.84) for 2019 in section 6. With the 2019 distribution kept it gives -3.00 (-8.94 to -0.14), and the interval excludes zero. On the same population, 36% (22 to 50) of the burden of the 2010-2019 lengthening is reversed; by age band the share is 47% (37 to 57) at 35-64 and 30% (7 to 51) at 65+.
- **Scenario E.** With the 2019 distribution kept the scenario gives -55 (-163 to 17) deaths per year for both sexes (interval spans zero) and -34 (-107 to 8) for men only (interval spans zero); the reversed share is 36% (1 to 72) and 30% (-14 to 79), with wide intervals because the hazard ratios are imprecise.
- For scenario A the reversed share depends almost only on the change in mean car-commute hours, because the unknown slope and net-sitting fraction scale numerator and denominator alike; its interval therefore reflects survey sampling error and county weighting rather than the uncertainty of the risk function.
- Checks specific to this scenario (rows P1 to P5 of [burden_validity_checks.csv]({{artifact:bbc5374e-808a-4a8b-a7b8-fb28be8d9d3d}})): keeping the 2024 distribution gives zero (max 9.3e-13); the sign of (ii) agrees with the sign of the 2019-2024 change in mean car-commute hours per resident in 24 of 24 comparisons for scenario A (county group by age band; deaths and pooled fractions), 24 of 24 for E both sexes, 24 of 24 for E men, and in 28 of 28 county-by-mortality-age-band strata for scenario A; a second seed moves median deaths by at most 1.5%, interval bounds by at most 2.0% of the interval width and the median reversed share by at most 0.0018.

## 8. Illustrative scenario: anger while driving as a trigger (not part of any total)

**This scenario is illustrative only and is excluded from every total above.** No study has measured road rage or driving anger against a cardiovascular event, and no dataset supplies the frequency of anger outbursts while driving. The scenario combines primary-study trigger estimates (myocardial infarction within 2 hours of an anger outburst, row DR047; acute stroke within 1 hour of anger or emotional upset, row DR050, published with a 99% interval; the press-release row DR054 is not used) with an assumed rate of driving-anger outbursts per hour of car commuting, drawn log-uniformly from 0.002-0.1 (central 0.0141). For person *i*, RR_i = 1 + (RR_trigger - 1) x lambda x *h_i* x W / 168, where W is the hazard window in hours. It further assumes that a trigger estimate for event onset applies equally to coronary heart disease deaths and stroke deaths. Survey data on road-rage behaviour cited in the literature review describe how many drivers report such behaviour in a year, not outbursts per hour of driving, and were not used to set the rate.

Table 13. Illustrative anger-trigger scenario, ages 35+, all 14 counties, 2019 (median and 95% UI).

| Pathway | Counterfactual | Deaths per year | Fraction, % | Baseline deaths (CHD or stroke) |
|---|---|---|---|---|
| MI trigger applied to CHD deaths | (1) 2010 distribution kept | 0.53 (0.08 to 3.59) | 0.0062 (0.0009 to 0.0419) | 8575 |
| MI trigger applied to CHD deaths | (1b) 2010 durations, 2019 car-commuter share | 0.31 (0.05 to 2.15) | 0.0037 (0.0005 to 0.0250) | 8575 |
| MI trigger applied to CHD deaths | (2) one-way car commute capped at 30 min | 0.56 (0.08 to 3.76) | 0.0065 (0.0010 to 0.0438) | 8575 |
| MI trigger applied to CHD deaths | (3) no car commuting (upper bound) | 1.92 (0.29 to 12.88) | 0.0224 (0.0033 to 0.1500) | 8575 |
| Stroke trigger applied to stroke deaths | (1) 2010 distribution kept | 0.04 (0.01 to 0.27) | 0.0007 (0.0001 to 0.0053) | 5125 |
| Stroke trigger applied to stroke deaths | (1b) 2010 durations, 2019 car-commuter share | 0.02 (0.00 to 0.15) | 0.0004 (0.0001 to 0.0029) | 5125 |
| Stroke trigger applied to stroke deaths | (2) one-way car commute capped at 30 min | 0.04 (0.01 to 0.27) | 0.0007 (0.0001 to 0.0053) | 5125 |
| Stroke trigger applied to stroke deaths | (3) no car commuting (upper bound) | 0.13 (0.02 to 0.95) | 0.0026 (0.0004 to 0.0185) | 5125 |

Under these assumptions the pathway is very small: 0.53 (0.08 to 3.59) coronary deaths and 0.04 (0.01 to 0.27) stroke deaths per year for the 2010 to 2019 lengthening, and 1.92 (0.29 to 12.88) and 0.13 (0.02 to 0.95) under the no-car bound. The result is driven almost entirely by the assumed outburst rate and should not be cited as an estimate.

## 9. Sensitivity analyses

Table 14. Attributable deaths per year, ages 35+, all 14 counties. Deterministic rows use central values (*d* = 4.5, *f* = 0.5, point relative risks); Monte Carlo rows give the median and 95% UI.

| Analysis | A, counterfactual 1 | A, no car | E both sexes, counterfactual 1 | E both sexes, no car |
|---|---|---|---|---|
| Base (deterministic central) | 8.6 | 30.6 | 139.9 | 360.0 |
| All seated motorised modes | 10.5 | 36.0 | 178.0 | 450.2 |
| Top-code replaced by largest uncensored value | 8.4 | 30.0 | 139.9 | 360.0 |
| Top-code replaced by 180 min | 9.0 | 31.5 | 139.9 | 360.0 |
| Commute days per week = 3 | 5.7 | 20.4 | 80.0 | 184.5 |
| Commute days per week = 5 | 9.5 | 34.0 | 160.4 | 431.9 |
| Daily sitting averaged over workdays only | 13.4 | 47.7 | n/a | n/a |
| Major cardiovascular disease rate series | 8.6 | 30.7 | 140.1 | 361.0 |
| Group-level pooled fraction x group deaths | 8.5 | 30.5 | 141.7 | 358.5 |
| E: top category >= 10 h/week (d = 4.5) | n/a | n/a | 139.9 | 360.0 |
| E: top category >= 10 h/week with d = 5 | n/a | n/a | 191.8 | 497.4 |
| E: plus 2 h/week non-commute car time | n/a | n/a | 210.1 | 660.4 |
| E: plus 3.9 h/week non-commute car time | n/a | n/a | 257.6 | 969.0 |
| Monte Carlo base | 8.0 (0.4 to 20.8) | 28.6 (1.4 to 73.1) | 147.1 (-39.1 to 379.5) | 382.5 (-224.6 to 1117.0) |
| Monte Carlo, d uniform 3 to 5 | 7.0 (0.3 to 19.1) | 25.0 (1.2 to 67.3) | 122.1 (-42.5 to 346.9) | 293.6 (-184.1 to 997.0) |
| Monte Carlo, SE from the wider CI half-width | 8.0 (0.4 to 20.9) | 28.6 (1.4 to 73.3) | 147.1 (-39.6 to 379.8) | 382.4 (-226.0 to 1120.5) |
| Monte Carlo, E hazard ratios uncorrelated | n/a | n/a | 151.0 (12.5 to 317.2) | 392.9 (-88.7 to 957.3) |
| Monte Carlo, E hazard ratios perfectly correlated | n/a | n/a | 144.7 (-77.7 to 426.1) | 376.6 (-329.3 to 1248.4) |

- **Within-band age gradient (35-64).** Deaths in this band are concentrated at its older end, where car commuting is less common. Applying the pooled fraction of 55-64-year-olds to all 35-64 deaths gives 2.73 deaths per year for scenario A, counterfactual 1, and applying that of 35-44-year-olds gives 3.01, against 3.03 with the pooled 35-64 fraction and 3.21 in the base calculation (county-specific fractions); for scenario E the same four values are 50.9, 63.0, 61.9 and 62.8.
- **Scenario E is sensitive to choices the data cannot settle.** Adding non-commute car time moves commuters into higher categories and raises the estimate, and at five commute days a week the many reports of exactly 60 minutes sit on the 10-hour boundary. The assumed correlation between the three hazard ratios changes the interval: for counterfactual 1 it is 151.0 (12.5 to 317.2) with uncorrelated hazard ratios, 147.1 (-39.1 to 379.5) at the assumed 0.5 and 144.7 (-77.7 to 426.1) with perfect correlation, so whether the interval spans zero depends on an assumption.
- The top-code treatment, the mortality series and the level at which fractions are pooled change the scenario A results in Table 14 by at most 0.90 deaths per year.

## 10. Validity checks

All 33 checks passed (0 failed). Full detail is in [burden_validity_checks.csv]({{artifact:bbc5374e-808a-4a8b-a7b8-fb28be8d9d3d}}).

| Check | What was tested | Value | Tolerance | Passed |
|---|---|---|---|---|
| V1_rr_equals_1 | All relative risks set to 1 (2,000 draws, sampling/assumption draws left random): max \|PAF or attributable deaths\| over all strata, scenarios, counterfactuals | 0 | 1e-09 | yes |
| V2a_cap_not_binding | Cap counterfactual with a cap above every travel time (counterfactual = observed): max \|PAF or deaths\| | 0 | 1e-09 | yes |
| V2b_baseline_equals_target | Baseline-year counterfactuals with baseline year = 2019 (counterfactual = observed): max \|PAF or deaths\| | 7.28e-13 | 1e-09 | yes |
| V3a_monotone_exposure_A | Attributable deaths (no-car counterfactual, all 14 counties, 35+, central) increase with travel time scaled by [0.5, 0.75, 1.0, 1.25, 1.5, 2.0] | 7.66 | 0 | yes |
| V3a_monotone_exposure_B | Attributable deaths (no-car counterfactual, all 14 counties, 35+, central) increase with travel time scaled by [0.5, 0.75, 1.0, 1.25, 1.5, 2.0] | 3.84 | 0 | yes |
| V3a_monotone_exposure_C | Attributable deaths (no-car counterfactual, all 14 counties, 35+, central) increase with travel time scaled by [0.5, 0.75, 1.0, 1.25, 1.5, 2.0] | 15.2 | 0 | yes |
| V3a_monotone_exposure_D | Attributable deaths (no-car counterfactual, all 14 counties, 35+, central) increase with travel time scaled by [0.5, 0.75, 1.0, 1.25, 1.5, 2.0] | 19 | 0 | yes |
| V3a_monotone_exposure_E_both | Attributable deaths (no-car counterfactual, all 14 counties, 35+, central) increase with travel time scaled by [0.5, 0.75, 1.0, 1.25, 1.5, 2.0] | 113 | 0 | yes |
| V3b_monotone_f | Scenario A deaths (no-car) increase with net-sitting fraction f = 0.25, 0.5, 0.75, 1.0 | 15.3 | 0 | yes |
| V3c_monotone_days | Scenario A deaths (no-car) increase with commute days per week = 3, 4, 5 | 6.82 | 0 | yes |
| V3d_monotone_cap | Scenario A deaths under a travel-time cap decrease as the cap rises (15, 30, 45, 60, 90 min) | -1.74 | 0 | yes |
| V3e_cap_below_nocar | Cap-30 burden is smaller than the no-car burden (scenario A, central) | 21.6 | 0 | yes |
| V4a_seed_median | Seed 20261113 vs 777, 40,000 draws each: max relative difference in median attributable deaths (all 14 counties, 35+, every scenario x counterfactual x f setting; 88 rows) | 0.0114 | 0.03 | yes |
| V4b_seed_bounds | Seed 20261113 vs 777: max \|difference in a 95% bound\| / interval width, same rows | 0.0123 | 0.03 | yes |
| V4c_mc_error | Scenario A, 2010-distribution counterfactual: SD of the median across 20 batches of 2,000 draws / sqrt(20), relative to the median | 0.00424 | 0.03 | yes |
| V5_series_vs_direct | Power-series evaluation of the exposure-weighted excess risk vs direct exponentials, all cells x 81 weights, four slopes up to 0.2 per commuting-day hour: max abs difference / max value | 3.43e-15 | 1e-10 | yes |
| V6_independent_paf | Scenario A central pooled PAF, 35-64, all 14 counties, 2010-distribution counterfactual: engine vs direct pandas computation (abs difference) | 4.44e-16 | 1e-12 | yes |
| V7_baseline_deaths | Baseline CVD deaths 35+, 14 counties, 2019: engine vs rate x population from pums_county_year_age.parquet (abs difference) | 3.64e-12 | 1e-06 | yes |
| V11_independent_categorical_paf | Scenario E central pooled PAFs (35-64 three counterfactuals; men 65+ 2010-distribution): engine vs direct pandas computation, max abs difference | 4.51e-17 | 1e-12 | yes |
| V12_independent_county_deaths | Scenario A central attributable deaths, 35-64, cap-30 counterfactual, summed over 14 county-specific PAFs: engine vs direct pandas computation (abs difference) | 2.18e-13 | 1e-09 | yes |
| V8_sampling_draws | SD of the simulated 2019 population 35-64 (4,000 draws) / replicate-weight SE in pums_county_year_age.parquet | 0.971 | 0.95-1.05 | yes |
| V9_median_vs_central | Scenario A, f fixed at 0.5: Monte Carlo median / deterministic central attributable deaths (informational) | 0.995 | 0.9-1.1 | yes |
| V10_population_reconciliation | Max abs difference in weighted population (and its SE) vs pums_county_year_age.parquet over 306 county/region x year x age-band rows | 0 | 1e-06 | yes |
| P1_post2020_counterfactual_equals_observed | Post-2020 scenario with the 2024 distribution kept (counterfactual = observed), 2,000 draws, every scenario and stratum: max \|fraction or deaths\| | 9.25e-13 | 1e-09 | yes |
| P2_sign_agrees_group_strata_A | Scenario A, central: sign of the 2019-kept deaths / pooled fraction equals the sign of the 2019-to-2024 change in mean car-commute hours per resident, county group x age band strata (share agreeing) | 1 | 1.0 | yes |
| P2_sign_agrees_group_strata_E_both | Scenario E_both, central: sign of the 2019-kept deaths / pooled fraction equals the sign of the 2019-to-2024 change in mean car-commute hours per resident, county group x age band strata (share agreeing) | 1 | 1.0 | yes |
| P2_sign_agrees_group_strata_E_men | Scenario E_men, central: sign of the 2019-kept deaths / pooled fraction equals the sign of the 2019-to-2024 change in mean car-commute hours per resident, county group x age band strata (share agreeing) | 1 | 1.0 | yes |
| P2_sign_agrees_county_strata_A | Scenario A, central: sign of the county-specific 2019-kept fraction equals the sign of the change in mean car-commute hours per resident, 14 counties x 2 mortality age bands (share agreeing) | 1 | 1.0 | yes |
| P3a_post2020_seed_median | Post-2020 scenario, seed 20261113 vs 777, 40000 draws each: max relative difference in median deaths (all 14 counties; 35-64, 65+, 35+; A, E both sexes, E men; both counterfactuals) | 0.0155 | 0.03 | yes |
| P3b_post2020_seed_bounds | Same rows: max \|difference in a 95% bound\| / interval width | 0.0204 | 0.03 | yes |
| P3c_post2020_seed_reversal | Same strata: max absolute difference in the median reversal fraction | 0.00178 | 0.01 | yes |
| P4_reproduces_main_2019_results | Median and 95% bounds of 2019 attributable deaths (2010 kept) recomputed in the post-2020 run vs burden_results.csv, 27 rows: max abs difference | 2.84e-14 | 1e-08 | yes |
| P5_independent_reversal_fraction | Scenario A central pooled reversal fraction, 35-64, all 14 counties: engine vs direct pandas computation (abs difference) | 6.66e-15 | 1e-09 | yes |

## 11. Limitations

This is a modelling exercise on observational, cross-sectional survey data; it reports associations implied by borrowed relative risks and cannot show that commuting caused any death. The central scenarios transfer a generic total-sitting dose-response to car-commute time, which assumes car sitting is exchangeable with other sitting; the only driving-specific cardiovascular mortality estimate comes from one cohort of US men with exposure measured once in 1982, and two other cohorts found no mortality association with driving or transport sitting. The fraction of commute time that is net additional sitting has no direct estimate and one cohort found long drivers slightly less likely to report high total sitting, so *f* was treated as unknown between 0 and 1 and dominates the uncertainty of scenarios A to D. Commute days per week are not recorded in the ACS and were assumed. Individual total sitting and physical activity are unknown, so the sitting slope could not be restricted to inactive commuters even though activity strongly modifies the association in the source literature. The same relative risk was applied at every age. Mortality rates exist only for 35-64 and 65+, are model-smoothed and age-standardised within band, and were multiplied by survey population counts, so "deaths" are rate-equivalent estimates rather than counts from death certificates. Within each band, commuters are younger than the people who die: in 2019, ages 65-69 held 31% of the 65+ population but 61% of its car-commute hours, and ages 75 and over held 42% of the population but 13% of the hours, so applying the band-wide 65+ death rate to commuters probably overstates attributable deaths at 65+ by an amount that cannot be quantified without finer mortality data; the same issue in the 35-64 band was bounded in section 9. Working commuters are also likely to be healthier than non-working residents of the same age, which works in the same direction. Burden was not assessed under age 35. The 2010 baseline followed a recession, so counterfactual 1 mixes longer commutes with higher employment; counterfactual 1b separates them. Travel time is top-coded with a threshold that changed between 2010 and 2019, is self-reported with heaping at round values, and is door-to-door rather than in-vehicle. San Benito County has no person-level data and is excluded. The 2021-2024 figures describe commuters selected differently after the rise in working from home, and no mortality data exist for those years; the post-2020 scenario in section 7 applies 2019 mortality rates to 2024 as an assumption and is not an estimate of deaths that occurred. The anger-trigger scenario rests on an assumed outburst frequency and is illustrative only. Several further choices are assumptions rather than estimates: the correlation between the three driving-specific hazard ratios, the category boundaries, the treatment of the mortality-rate interval as a 95% interval, and independence of rate uncertainty across counties.

## 12. Files

- [exposure_distributions.csv]({{artifact:264325c1-f985-4878-a7e9-62e12300e29d}}): weighted exposure distributions by year, county group, age band, mode definition and days per week, with replicate-weight SEs
- [burden_results.csv]({{artifact:ed1fab53-f43e-4523-ad34-8e73c8b798c8}}): attributable fraction and deaths per year by age band, county group, scenario, counterfactual and net-sitting fraction, with 95% UIs
- [burden_assumptions.csv]({{artifact:a0176575-f463-48e3-806d-6cab09f894d7}}): every parameter and assumption with value, range, source row id and abstract_only flag
- [burden_validity_checks.csv]({{artifact:bbc5374e-808a-4a8b-a7b8-fb28be8d9d3d}}): validity checks
- [burden_sensitivity.csv]({{artifact:21f76a51-1ff6-4bdb-8831-24769f0545a2}}): sensitivity analyses
- [burden_anger_illustrative.csv]({{artifact:25cc6c9c-7a0e-41f9-960b-f428f5fe27f6}}): illustrative anger-trigger scenario (excluded from totals)
- [burden_post2020_scenario.csv]({{artifact:3da2886c-802f-4144-96b5-c91880de5d7a}}): SCENARIO: 2024 commuting and population with 2019 mortality rates, 2010-kept and 2019-kept counterfactuals, reversed share (not observed mortality)
- [burden_draws_headline.csv]({{artifact:ff6e1408-83f0-411c-885f-614b32f4858d}}): Monte Carlo draws of attributable deaths, ages 35+, all 14 counties, for plotting
- [exposure_reconciliation.csv]({{artifact:ad515c70-db18-4e44-b75e-22e4660203ce}}): population reconciliation against pums_county_year_age.parquet
- [burden_lib.py]({{artifact:5a79037a-20cd-4a5f-bde9-94dc61a4d977}}): data loading and helpers
- [burden_model.py]({{artifact:822ceffd-4df7-4d07-a5aa-e6932c6c2090}}): comparative risk assessment engine
- [01_exposure.py]({{artifact:c2bdb49d-58e7-48e5-821f-72d06be63221}}): step 1
- [02_burden_mc.py]({{artifact:0da44fa1-8164-480e-9321-1ccd55fb8d5c}}): steps 2 and 3
- [03_validity_sensitivity.py]({{artifact:e492ab55-e892-4cb2-8a68-6da570df1967}}): validity checks and sensitivity analyses
- [05_post2020_scenario.py]({{artifact:dc08f76d-3c47-4fc2-9e7c-3bf121579eab}}): post-2020 scenario and its validity checks
- [04_write_report.py]({{artifact:3286d99c-a784-4193-8647-296281294a27}}): writes this document from the result files

The scripts read input locations from `burden/paths.json` (keys `pums`, `pcya`, `mort`, `dr` pointing to pums_commuters.parquet, pums_county_year_age.parquet, mortality_long.parquet and dose_response_parameters.csv) and are run from the workspace root in the order 01, 02, 03, 05, 04.
