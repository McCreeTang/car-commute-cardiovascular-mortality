# Methods and results: national county models of car-commute time and cardiovascular mortality

US county units, American Community Survey commute data and CDC county cardiovascular mortality at ages 35-64 and 65+. Three pre-specified tests: 2015-2019 cross-section (T1), change from 2006-2010 to 2015-2019 (T2), matched high- versus low-driving counties (T3). No year from 2020 onward enters any model.

**Reading rule.** Everything here is observational and ecological. Coefficients are associations between county-level quantities; none is a causal effect and none describes individuals. The model set, the matching rule, the multiplicity families and the decision rule were fixed in [national_prespecified_plan.md]({{artifact:55b27226-16f3-44cc-9873-07fd33597057}}) before any national exposure-outcome association was computed. Every pre-specified model is reported. Analyses added afterwards are labelled post hoc (section 9). Every number below is formatted by `nat07_write_report.py` from the saved result files.

## 1. Summary of results

1. **No test shows higher cardiovascular mortality where car-commute time is higher.** All three pre-specified estimates for all-cardiovascular mortality at ages 35-64 are negative: T1 -4.6% (-11.1% to +2.4%; p 0.186) per additional car-commute hour a week per adult; T2 -1.7% (-6.6% to +3.5%; p 0.511) per hour a week of change; T3 -6.2% (-11.2% to -0.8%; p 0.026) for high- versus low-driving counties (regression-adjusted pair difference, the estimate designated by the plan because one matching covariate missed the balance target; unadjusted -3.9% (-9.2% to +1.7%; p 0.166)). Benjamini-Hochberg q-values across the three: 0.278, 0.511, 0.077; Holm-adjusted p: 0.371, 0.511, 0.077. None is below 0.05.
2. **By the pre-specified rule the primary result (T1) is null.** The state-clustered interval includes zero. It excludes the driving-specific literature benchmark (+4.1% per hour a week, from one cohort of men) because the point estimate is negative, not because the design is precise: the minimum detectable effect is 10.5%, 2.5 times that benchmark and 37 times the generic-sitting benchmark (+0.28%). The design cannot detect effects of the size implied by sitting-time studies.
3. **Weighting changes the precision and the significance, not the sign.** The unweighted T1 estimate is -6.9% (-9.3% to -4.4%; p <0.001), an inverse association with an interval that excludes zero under both state-clustered and Conley inference. The population-weighted estimate has the same sign and a wider interval; under Conley (200 km) errors its interval is -8.94% to -0.05% (p 0.048). The plan requires both inference methods for 'evidence against', so the weighted primary estimate stays classified as null.
4. **Raw and adjusted estimates differ greatly.** With no covariates the weighted estimate is -28.9% (-33.8% to -23.6%; p <0.001); adding age and sex composition leaves it at -27.5% (-36.2% to -17.6%; p <0.001); adding socioeconomic and racial/ethnic composition moves it to -3.6% (-11.0% to +4.5%; p 0.367). Most of the raw inverse association is accounted for by county socioeconomic composition.
5. **Falsification tests.** (a) At ages 65+ the T1 car coefficient is +2.2% (-1.0% to +5.5%; p 0.173) weighted and -1.7% (-3.8% to +0.5%; p 0.121) unweighted; the 35-64 minus 65+ difference in log coefficients is -0.069 (95% CI -0.134 to -0.003; p 0.039) weighted and -0.054 (-0.071 to -0.038; p <0.001) unweighted. The inverse association is therefore concentrated in the working-age band. (b) Within metropolitan counties the weighted estimate is -2.3% (-11.3% to +7.6%; p 0.632) and the unweighted -6.7% (-11.2% to -1.8%; p 0.009). (c) The transit coefficient is -4.0% (-11.6% to +4.3%; p 0.332) weighted and +2.1% (-2.8% to +7.3%; p 0.401) unweighted; it changes sign when the five New York City counties are excluded (+13.5%, p 0.030) and should not be interpreted.
6. **Secondary outcomes.** Of seven weighted secondary estimates, one has q < 0.05: stroke at 35-64, -8.1% (-13.1% to -2.8%; p 0.004), q 0.028, also inverse. Coronary heart disease at 35-64 is -0.3% (-11.2% to +11.9%; p 0.956); men -3.7% (-10.2% to +3.3%; p 0.281); women -6.8% (-14.0% to +1.1%; p 0.088).
7. **Change model (T2): null and weakly identified.** Sampling error accounts for most of the identifying variation in the change in car hours: conditional reliability 0.22 in the weighted model and below zero unweighted (estimated noise variance exceeds the observed variance). In counties of at least 65,000 people in both periods (n = 791) reliability is 0.73 and the estimate is -2.7% (-11.3% to +6.7%; p 0.551).
8. **Sensitivity family (26 pre-specified estimates for all-CVD 35-64).** 25 are negative and 1 positive; 8 are nominally significant and negative, 0 nominally significant and positive; 6 have q < 0.05, all negative (the raw M0 and M1 rungs and the unweighted M3 and M4 models). The one positive estimate is +2.1% (-3.1% to +7.5%; p 0.423) when the South is left out.
9. **Bay Area counties sit high on exposure and low on mortality.** Of the 15 study counties, 14 are above the national median of car-commute hours per adult and 14 are below the national median of all-CVD mortality at 35-64 (section 8). This is description, not a test.

## 2. Data, units and samples

- Units: CDC mortality county units. Cross-sectional sample: 3,024 units with complete exposure, mortality (both age bands) and covariates in 2015-2019, in 51 states (50 states and DC), total population 324,520,919; 1,159 metropolitan (NCHS 2013 classes 1-4) and 1,865 non-metropolitan. Sex-specific rates are published for 2,972 (men) and 2,967 (women) of these units.
- Change sample: 3,024 units complete in both 2006-2010 and 2015-2019; 791 have at least 65,000 residents in both periods and hold 84.3% of the 2015-2019 population of the sample.
- Outcome: natural log of the five-year mean of annual, model-smoothed, within-band age-standardised death rates per 100,000 (CDC), all races, both sexes unless stated.
- Exposure: weekly commute hours by car, truck or van (drove alone or carpooled) per resident aged 16+ (journey to work only; 2 trips x one-way minutes x 4.5 days; bin-midpoint minutes scaled to the county's published total). Comparison exposure: the same for public transport.
- In the cross-sectional sample the two exposures are nearly uncorrelated (unweighted r = +0.039); 80 units have at least 0.25 transit hours a week per adult.
- National car-commuter prevalence in 2015-2019 (from the exposure columns): 0.502 of residents 16+, 0.595 at ages 45-64, 0.139 at 65+. Ratio 45-64 to 16+: 1.185. Ratio 65+ to 45-64: 0.23.

**Table 2.1 Cross-sectional sample, 2015-2019: unweighted and population-weighted (ages 35-64) summaries.**

| Variable | Mean | SD | 10th pct | Median | 90th pct | Weighted mean | Weighted SD |
|---|---|---|---|---|---|---|---|
| Car-commute hours/week per adult 16+ | 1.761 | 0.457 | 1.213 | 1.735 | 2.351 | 1.982 | 0.442 |
| Transit-commute hours/week per adult 16+ | 0.037 | 0.141 | 0.000 | 0.008 | 0.062 | 0.218 | 0.443 |
| All-CVD mortality 35-64 (per 100,000) | 146.670 | 57.450 | 84.220 | 133.860 | 226.574 | 117.883 | 45.752 |
| All-CVD mortality 65+ (per 100,000) | 1555.616 | 264.643 | 1243.006 | 1535.020 | 1900.114 | 1435.229 | 227.350 |
| Share aged 35-64 | 0.384 | 0.028 | 0.350 | 0.388 | 0.414 | 0.386 | 0.024 |
| Share aged 65+ | 0.187 | 0.045 | 0.134 | 0.184 | 0.244 | 0.157 | 0.039 |
| Log median household income | 10.854 | 0.251 | 10.549 | 10.854 | 11.157 | 11.067 | 0.263 |
| Poverty rate | 0.152 | 0.062 | 0.082 | 0.143 | 0.233 | 0.133 | 0.049 |
| Share with bachelor's degree or more | 0.220 | 0.096 | 0.125 | 0.195 | 0.350 | 0.323 | 0.113 |
| Unemployment rate | 0.053 | 0.025 | 0.027 | 0.050 | 0.083 | 0.054 | 0.016 |
| Share non-Hispanic Black | 0.092 | 0.145 | 0.003 | 0.024 | 0.303 | 0.123 | 0.125 |
| Share Hispanic | 0.093 | 0.137 | 0.014 | 0.042 | 0.238 | 0.178 | 0.168 |
| Share uninsured, 19-64 | 0.140 | 0.071 | 0.063 | 0.126 | 0.238 | 0.124 | 0.061 |
| Log population density | 3.921 | 1.658 | 1.822 | 3.850 | 6.041 | 6.289 | 1.693 |

## 3. T1: cross-sectional models, 2015-2019

### 3.1 Specification

`log(rate_i) = a + b_car * car_hours_i + b_transit * transit_hours_i + g'X_i + e_i`, with the covariate ladder:

- M0: the two exposures only.
- M1: + shares aged 18-34, 35-64, 65+ (reference under 18) and share female.
- M2: + log median household income, poverty rate, share with a bachelor's degree or more, share without a high-school diploma, unemployment rate, shares non-Hispanic Black, Hispanic, non-Hispanic Asian, non-Hispanic American Indian/Alaska Native, share uninsured at ages 19-64.
- **M3 (primary)**: + NCHS 2013 urban-rural class (six classes), log population density, state fixed effects.
- M4 (sensitivity): + PLACES age-adjusted prevalence of current smoking, obesity, diabetes and no leisure-time physical activity (model-based estimates; possible mediators).

Weights: population aged 35-64 (65+ for the 65+ outcomes); unweighted estimates beside them. Inference: CR1 standard errors clustered by state (51 clusters, t reference with 50 df); alternative: Conley spatial HAC, Bartlett kernel, 200 km cutoff (100 and 500 km in the file), normal reference. Reported scale: 100 x (exp(b) - 1), the percent difference in the death rate per additional hour a week. MDE = 2.857 x state-clustered SE (80% power, two-sided 5%), converted to percent. The estimator was checked against statsmodels WLS with cluster-robust errors (identical coefficient, SE and p to 9 digits for the primary model).

### 3.2 Coefficient ladder

**Table 3.1 All CVD, 35-64: percent difference in the death rate per additional commute hour a week per adult (n = 3,024 units).**

| Model | Weighting | Car hours: estimate (95% CI, state-clustered); p | Car: Conley 200 km 95% CI; p | Transit hours: estimate (95% CI); p | Car = transit, p | R2 | MDE, car |
|---|---|---|---|---|---|---|---|
| M0 | Population-weighted | -28.9% (-33.8% to -23.6%; p <0.001) | -33.1% to -24.3%; p <0.001 | -22.5% (-30.7% to -13.3%; p <0.001) | 0.068 | 0.178 | 10.7% |
| M0 | Unweighted | -10.5% (-16.5% to -4.0%; p 0.002) | -16.2% to -4.4%; p <0.001 | -41.4% (-59.4% to -15.4%; p 0.005) | 0.030 | 0.057 | 10.4% |
| M1 | Population-weighted | -27.5% (-36.2% to -17.6%; p <0.001) | -34.0% to -20.2%; p <0.001 | -21.5% (-30.3% to -11.6%; p <0.001) | 0.051 | 0.243 | 19.9% |
| M1 | Unweighted | -16.1% (-23.6% to -8.0%; p <0.001) | -22.5% to -9.2%; p <0.001 | -46.0% (-64.6% to -17.8%; p 0.005) | 0.041 | 0.082 | 14.1% |
| M2 | Population-weighted | -3.6% (-11.0% to +4.5%; p 0.367) | -9.4% to +2.6%; p 0.250 | -5.1% (-12.7% to +3.1%; p 0.209) | 0.655 | 0.804 | 12.1% |
| M2 | Unweighted | -0.4% (-4.1% to +3.5%; p 0.838) | -3.8% to +3.1%; p 0.826 | -0.7% (-7.4% to +6.4%; p 0.829) | 0.921 | 0.734 | 5.5% |
| M3 **(primary)** | Population-weighted | -4.6% (-11.1% to +2.4%; p 0.186) | -8.94% to -0.05%; p 0.048 | -4.0% (-11.6% to +4.3%; p 0.332) | 0.895 | 0.899 | 10.5% |
| M3 | Unweighted | -6.9% (-9.3% to -4.4%; p <0.001) | -9.1% to -4.6%; p <0.001 | +2.1% (-2.8% to +7.3%; p 0.401) | 0.003 | 0.867 | 3.8% |
| M4 | Population-weighted | -4.2% (-10.7% to +2.8%; p 0.227) | -8.4% to +0.3%; p 0.066 | -0.2% (-7.4% to +7.6%; p 0.954) | 0.409 | 0.904 | 10.5% |
| M4 | Unweighted | -6.9% (-9.3% to -4.4%; p <0.001) | -9.1% to -4.6%; p <0.001 | +4.5% (-0.6% to +9.9%; p 0.081) | <0.001 | 0.871 | 3.8% |

**Table 3.2 All CVD, 65+: percent difference in the death rate per additional commute hour a week per adult (n = 3,024 units).**

| Model | Weighting | Car hours: estimate (95% CI, state-clustered); p | Car: Conley 200 km 95% CI; p | Transit hours: estimate (95% CI); p | Car = transit, p | R2 | MDE, car |
|---|---|---|---|---|---|---|---|
| M0 | Population-weighted | -4.7% (-9.6% to +0.6%; p 0.079) | -8.2% to -1.0%; p 0.014 | -5.6% (-13.6% to +3.2%; p 0.199) | 0.777 | 0.028 | 7.9% |
| M0 | Unweighted | -0.2% (-3.5% to +3.2%; p 0.912) | -2.9% to +2.6%; p 0.895 | -18.7% (-33.4% to -0.8%; p 0.042) | 0.048 | 0.030 | 4.9% |
| M1 | Population-weighted | -12.1% (-17.4% to -6.3%; p <0.001) | -16.6% to -7.3%; p <0.001 | -8.1% (-15.7% to +0.3%; p 0.057) | 0.178 | 0.112 | 9.4% |
| M1 | Unweighted | -4.1% (-8.2% to +0.1%; p 0.056) | -7.1% to -1.1%; p 0.009 | -21.7% (-37.0% to -2.5%; p 0.029) | 0.070 | 0.065 | 6.3% |
| M2 | Population-weighted | +0.6% (-2.7% to +4.1%; p 0.711) | -2.8% to +4.2%; p 0.721 | +3.4% (+0.7% to +6.2%; p 0.014) | 0.108 | 0.563 | 4.9% |
| M2 | Unweighted | +0.7% (-1.9% to +3.5%; p 0.586) | -1.4% to +2.9%; p 0.512 | +4.4% (-0.9% to +10.0%; p 0.104) | 0.174 | 0.486 | 3.9% |
| M3 | Population-weighted | +2.2% (-1.0% to +5.5%; p 0.173) | -1.2% to +5.6%; p 0.202 | +1.2% (-2.2% to +4.6%; p 0.487) | 0.595 | 0.720 | 4.6% |
| M3 | Unweighted | -1.7% (-3.8% to +0.5%; p 0.121) | -3.5% to +0.2%; p 0.076 | -0.1% (-7.3% to +7.6%; p 0.969) | 0.685 | 0.652 | 3.1% |
| M4 | Population-weighted | +2.3% (-0.8% to +5.4%; p 0.144) | -1.1% to +5.7%; p 0.189 | +1.2% (-2.4% to +5.0%; p 0.510) | 0.624 | 0.723 | 4.4% |
| M4 | Unweighted | -1.7% (-3.8% to +0.5%; p 0.123) | -3.5% to +0.2%; p 0.076 | +0.6% (-7.4% to +9.3%; p 0.886) | 0.589 | 0.657 | 3.1% |

Reading. At ages 35-64 the raw association (M0) is strongly inverse, -28.9% (-33.8% to -23.6%; p <0.001) weighted and -10.5% (-16.5% to -4.0%; p 0.002) unweighted: counties with more car-commute time per adult have lower working-age cardiovascular mortality before any adjustment. Socioeconomic and racial/ethnic composition (M2) accounts for most of it (-3.6% (-11.0% to +4.5%; p 0.367) weighted; -0.4% (-4.1% to +3.5%; p 0.838) unweighted). In the primary model the weighted estimate is -4.6% (-11.1% to +2.4%; p 0.186) and the unweighted estimate is -6.9% (-9.3% to -4.4%; p <0.001). Adding the modelled risk-factor prevalences (M4) changes little (-4.2% (-10.7% to +2.8%; p 0.227) weighted). The car and transit coefficients cannot be distinguished in the weighted primary model (p 0.895); unweighted they differ (p 0.003), with a transit coefficient of +2.1% (-2.8% to +7.3%; p 0.401).

### 3.3 Secondary outcomes (family B)

**Table 3.3 Car coefficient in M3 for the secondary outcomes.** q = Benjamini-Hochberg q-value within the family of seven weighted estimates.

| Outcome | n | Population-weighted: estimate (95% CI); p; q | Unweighted: estimate (95% CI); p |
|---|---|---|---|
| All CVD, 65+ | 3,024 | +2.2% (-1.0% to +5.5%; p 0.173); q 0.404 | -1.7% (-3.8% to +0.5%; p 0.121) |
| Coronary heart disease, 35-64 | 3,024 | -0.3% (-11.2% to +11.9%; p 0.956); q 0.956 | -8.0% (-11.9% to -4.0%; p <0.001) |
| Coronary heart disease, 65+ | 3,024 | +3.3% (-4.3% to +11.5%; p 0.397); q 0.556 | -4.9% (-8.4% to -1.3%; p 0.009) |
| Stroke, 35-64 | 3,024 | -8.1% (-13.1% to -2.8%; p 0.004); q 0.028 | -6.2% (-9.3% to -3.0%; p <0.001) |
| Stroke, 65+ | 3,024 | +1.8% (-3.7% to +7.5%; p 0.525); q 0.613 | -0.3% (-2.8% to +2.3%; p 0.821) |
| All CVD, men 35-64 | 2,972 | -3.7% (-10.2% to +3.3%; p 0.281); q 0.491 | -7.3% (-9.9% to -4.5%; p <0.001) |
| All CVD, women 35-64 | 2,967 | -6.8% (-14.0% to +1.1%; p 0.088); q 0.309 | -9.7% (-12.6% to -6.7%; p <0.001) |

1 of 7 weighted secondary estimates has q < 0.05: Stroke, 35-64 -8.1% (-13.1% to -2.8%; p 0.004), q 0.028. No secondary estimate is positive with an interval excluding zero. Among men, the group studied by the driving-specific cohort, the estimate is -3.7% (-10.2% to +3.3%; p 0.281) weighted and -7.3% (-9.9% to -4.5%; p <0.001) unweighted.

### 3.4 Falsification tests

**Table 3.4 (a) Car coefficient at 35-64 versus 65+ (same units, state-clustered covariance across the two equations).** Difference is on the log scale.

| Sample | Model | Weighting | 35-64 | 65+ | Difference 35-64 minus 65+ (95% CI); p | Ratio 65+ / 35-64 |
|---|---|---|---|---|---|---|
| all (n = 3,024) | M0 | Population-weighted | -28.9% | -4.7% | -0.293 (-0.354 to -0.231); p <0.001 | +0.14 |
| all (n = 3,024) | M0 | Unweighted | -10.5% | -0.2% | -0.109 (-0.153 to -0.064); p <0.001 | +0.02 |
| all (n = 3,024) | M2 | Population-weighted | -3.6% | +0.6% | -0.043 (-0.108 to +0.022); p 0.193 | -0.17 |
| all (n = 3,024) | M2 | Unweighted | -0.4% | +0.7% | -0.011 (-0.032 to +0.010); p 0.297 | -1.88 |
| all (n = 3,024) | M3 | Population-weighted | -4.6% | +2.2% | -0.069 (-0.134 to -0.003); p 0.039 | -0.46 |
| all (n = 3,024) | M3 | Unweighted | -6.9% | -1.7% | -0.054 (-0.071 to -0.038); p <0.001 | +0.24 |
| all (n = 3,024) | M4 | Population-weighted | -4.2% | +2.3% | -0.065 (-0.130 to -0.000); p 0.049 | -0.52 |
| all (n = 3,024) | M4 | Unweighted | -6.9% | -1.7% | -0.054 (-0.071 to -0.038); p <0.001 | +0.24 |
| metro (n = 1,159) | M3 | Population-weighted | -2.3% | +3.9% | -0.061 (-0.156 to +0.033); p 0.200 | -1.65 |
| metro (n = 1,159) | M3 | Unweighted | -6.7% | -0.9% | -0.060 (-0.101 to -0.018); p 0.005 | +0.13 |
| nonmetro (n = 1,865) | M3 | Population-weighted | -9.1% | -2.9% | -0.066 (-0.105 to -0.026); p 0.002 | +0.31 |
| nonmetro (n = 1,865) | M3 | Unweighted | -6.7% | -2.0% | -0.049 (-0.075 to -0.022); p <0.001 | +0.30 |

The hypothesis under test predicts a positive coefficient at 35-64 that is larger than at 65+. The observed pattern is an inverse or null coefficient at 35-64 and a coefficient near zero at 65+ (+2.2% (-1.0% to +5.5%; p 0.173) weighted; -1.7% (-3.8% to +0.5%; p 0.121) unweighted). In the primary model (M3) the difference between bands excludes zero in the full sample under both weightings. In the unweighted primary model the 65+ coefficient is 0.24 of the 35-64 coefficient; the ratio of car-commuter prevalence at 65+ to that at 45-64 is 0.23. So whatever produces the inverse association tracks the working-age band. That is the pattern expected of a characteristic of working-age residents that travels with commuting, and it is equally the pattern a protective effect would produce; these data cannot separate the two, and the pre-specified reading is an inverse ecological association, not a protective effect.

(b) Metropolitan counties only (n = 1,159): -2.3% (-11.3% to +7.6%; p 0.632) weighted, -6.7% (-11.2% to -1.8%; p 0.009) unweighted. Non-metropolitan counties (n = 1,865; descriptive): -9.1% (-13.3% to -4.6%; p <0.001) weighted, -6.7% (-10.1% to -3.2%; p <0.001) unweighted. The association does not reverse within metropolitan counties.

(c) Transit as the comparison exposure. In M3 the transit coefficient is -4.0% (-11.6% to +4.3%; p 0.332) weighted and +2.1% (-2.8% to +7.3%; p 0.401) unweighted. Excluding the five New York City counties gives +13.5% (+1.3% to +27.3%; p 0.030); leaving out the Northeast gives +21.0% (p 0.005). The transit coefficient depends on a few counties and carries no weight as a driving-versus-sitting contrast.

### 3.5 Diagnostics and functional form

Moran's I of the M3 residuals (8 nearest neighbours, 999 permutations): All CVD, 35-64, population-weighted: 0.220 (p 0.001); All CVD, 35-64, unweighted: 0.175 (p 0.001); All CVD, 65+, population-weighted: 0.213 (p 0.001); All CVD, 65+, unweighted: 0.160 (p 0.001). Residuals are spatially autocorrelated, as expected for smoothed rates, so the state-clustered and Conley intervals are the ones to read; model-based standard errors would be too small.

**Table 3.5 M3 with national population-weighted quintiles of car hours in place of the linear term (descriptive).** Percent difference versus the lowest quintile.

| Outcome | Weighting | Q2 vs Q1 | Q3 vs Q1 | Q4 vs Q1 | Q5 vs Q1 |
|---|---|---|---|---|---|
| All CVD, 35-64 | Population-weighted | +2.1% (-0.5% to +4.9%) | +2.3% (-1.0% to +5.8%) | -0.1% (-4.0% to +4.0%) | -4.2% (-10.9% to +2.9%) |
| All CVD, 35-64 | Unweighted | -1.3% (-2.7% to +0.1%) | -2.7% (-4.6% to -0.7%) | -5.7% (-7.7% to -3.6%) | -9.1% (-11.6% to -6.6%) |
| All CVD, 65+ | Population-weighted | +2.2% (+0.6% to +3.9%) | +2.6% (+0.4% to +4.9%) | +4.8% (+1.7% to +8.0%) | +3.2% (-0.9% to +7.3%) |
| All CVD, 65+ | Unweighted | +0.2% (-0.9% to +1.3%) | -0.4% (-1.8% to +1.0%) | -0.6% (-2.1% to +0.8%) | -1.8% (-3.9% to +0.3%) |

Cuts [1.648, 1.889, 2.06, 2.349] hours a week; units per quintile (Q1 to Q5): 1252, 706, 393, 367, 306. Unweighted, mortality at 35-64 falls monotonically across quintiles. Population-weighted, the contrasts at 35-64 are small, not monotonic and all include zero; at 65+ the weighted estimates for quintiles 2 to 4 are a few percent above the lowest quintile and the unweighted ones are near zero.

### 3.6 Scale of the literature and minimum detectable effect

**Table 3.6 Expected percent difference in mortality per additional commute hour a week under literature estimates, against the primary estimate.**

| Benchmark | Conversion | Expected (range from the source CI) | x age concentration (1.185) | MDE / benchmark, weighted | MDE / benchmark, unweighted | Inside weighted 95% CI? | Inside unweighted 95% CI? |
|---|---|---|---|---|---|---|---|
| Generic sitting (DR027), half of commute time is net sitting | 100*(RR^(0.5/7)-1) | +0.14% (+0.07% to +0.21%) | +0.17% | 74.4 | 26.8 | yes | no |
| Generic sitting (DR027), all commute time is net sitting | 100*(RR^(1.0/7)-1) | +0.28% (+0.14% to +0.42%) | +0.34% | 37.2 | 13.4 | yes | no |
| Driving-specific (DR003, >10 vs <4 h/week), top category 12 h | ln(HR)/(12-2) h/week | +4.14% (+0.77% to +7.65%) | +4.92% | 2.5 | 0.9 | no | no |
| Driving-specific (DR001-DR003 trend), top category 12 h | inverse-variance slope through reference; midpoints 2, 5.5, 8.5, 12 h/week | +3.76% (+1.05% to +6.53%) | +4.46% | 2.8 | 1.0 | no | no |
| Driving-specific (DR003), top category 15 h | ln(HR)/(15-2) h/week | +3.17% (+0.59% to +5.83%) | +3.76% | 3.3 | 1.2 | no | no |
| Driving-specific (DR001-DR003 trend), top category 15 h | inverse-variance slope through reference; midpoints 2, 5.5, 8.5, 15 h/week | +3.15% (+0.90% to +5.44%) | +3.74% | 3.3 | 1.2 | no | no |

Primary estimate -4.6% (-11.1% to +2.4%; p 0.186), MDE 10.5%; unweighted -6.9% (-9.3% to -4.4%; p <0.001), MDE 3.8%. Conversions and assumptions: (i) generic sitting: a relative risk of 1.02 per additional hour a day of total sedentary time; one more commute hour a week adds f/7 hours a day, f being the net-sitting fraction. (ii) driving-specific: hazard ratios for men riding in a car 4-7, 7-10 and >10 versus <4 hours a week, with category midpoints 2, 5.5, 8.5 and an assumed 12 (or 15) hours for the open top category; either ln(HR)/(difference in midpoints) for the top category or the inverse-variance weighted slope through the reference over the three contrasts (their correlation is ignored). Both assume log-linear individual risk, that a one-hour higher county mean acts like a uniform one-hour shift, that commute time adds one-for-one to total car time (or f-for-one to sitting), and that the estimates apply to both sexes, to ages 35-64 and to deaths in the same five years. Because the exposure is averaged over all residents 16+ while car commuting is 1.185 times as prevalent at 45-64, the benchmarks are also shown multiplied by that factor.

What the design can and cannot say: the weighted MDE (10.5%) is 37 times the upper generic-sitting benchmark and 2.5 times the driving-specific one; the unweighted MDE (3.8%) is 13 and 0.9 times. An effect of the size implied by sitting-time studies is far below what either model can detect and lies inside the weighted interval. The driving-specific benchmark lies above the upper limit of both intervals (+2.4% weighted, -4.4% unweighted). Under the plan's rule the weighted null is therefore informative against the driving-specific estimate and uninformative about sitting-sized effects.

## 4. T2: change from 2006-2010 to 2015-2019

### 4.1 Specification

`log(rate_2015-19) - log(rate_2006-10) = a_state + b_car * change in car hours + b_transit * change in transit hours + g' * change in X + class_2006 + e`. Changes in X: shares aged 18-34, 35-64, 65+, share female, log median household income (nominal), poverty rate, share with bachelor's degree or more, share without high-school diploma, unemployment rate, shares non-Hispanic Black, Hispanic, non-Hispanic Asian, non-Hispanic American Indian/Alaska Native, log population density. Baseline urban-rural class: NCHS 2006 scheme. Uninsured share is unavailable for 2006-2010. Weights: mean of the two periods' population in the age band. State-clustered CR1 errors, t(50); Conley 200 km as alternative.

Between the two periods the population-weighted mean of car hours rose from 1.872 to 1.975 hours a week per adult (66.4% of units increased), and population-weighted mean all-CVD mortality moved from 121.6 to 118.5 per 100,000 at 35-64 and from 1680.0 to 1444.8 at 65+.

### 4.2 Results

**Table 4.1 Percent difference in the change of the death rate per additional hour a week of change in the exposure.** Reliability = 1 - sampling variance / variance of the exposure change (conditional: after partialling out the other regressors and fixed effects).

| Outcome | Sample | Weighting | Exposure change | Estimate (95% CI, state-clustered); p | Conley 200 km p | MDE | SD of exposure change | Mean sampling SD | Reliability raw / conditional | Estimate / conditional reliability |
|---|---|---|---|---|---|---|---|---|---|---|
| All CVD, 35-64 **(T2)** | all (n = 3,024) | Population-weighted | car hours | -1.7% (-6.6% to +3.5%; p 0.511) | 0.474 | 7.6% | 0.119 | 0.082 | 0.53 / 0.22 | -7.4% |
| All CVD, 35-64 | all (n = 3,024) | Population-weighted | transit hours | -15.0% (-25.2% to -3.4%; p 0.014) | 0.010 | 20.0% | 0.062 | 0.027 | 0.81 / 0.64 | -22.3% |
| All CVD, 35-64 | all (n = 3,024) | Unweighted | car hours | -0.5% (-2.8% to +2.0%; p 0.700) | 0.652 | 3.5% | 0.188 | 0.224 | -0.42 / -0.62 | not defined |
| All CVD, 35-64 | all (n = 3,024) | Unweighted | transit hours | -6.0% (-17.3% to +6.8%; p 0.335) | 0.263 | 19.9% | 0.032 | 0.096 | -7.90 / -8.92 | not defined |
| All CVD, 65+ | all (n = 3,024) | Population-weighted | car hours | -0.9% (-3.5% to +1.8%; p 0.508) | 0.552 | 3.8% | 0.121 | 0.089 | 0.46 / 0.15 | -5.8% |
| All CVD, 65+ | all (n = 3,024) | Population-weighted | transit hours | -15.0% (-25.3% to -3.3%; p 0.014) | <0.001 | 20.1% | 0.059 | 0.030 | 0.75 / 0.54 | -26.1% |
| All CVD, 65+ | all (n = 3,024) | Unweighted | car hours | -0.004% (-1.7% to +1.7%; p 0.997) | 0.996 | 2.5% | 0.188 | 0.224 | -0.42 / -0.62 | not defined |
| All CVD, 65+ | all (n = 3,024) | Unweighted | transit hours | -4.9% (-15.6% to +7.1%; p 0.398) | 0.357 | 18.5% | 0.032 | 0.096 | -7.90 / -8.92 | not defined |
| Coronary heart disease, 35-64 | all (n = 3,024) | Population-weighted | car hours | -1.6% (-7.5% to +4.6%; p 0.598) | 0.628 | 9.1% | 0.119 | 0.082 | 0.53 / 0.22 | -7.0% |
| Coronary heart disease, 35-64 | all (n = 3,024) | Population-weighted | transit hours | -27.6% (-45.3% to -4.2%; p 0.025) | 0.015 | 49.1% | 0.062 | 0.027 | 0.81 / 0.64 | -39.5% |
| Coronary heart disease, 35-64 | all (n = 3,024) | Unweighted | car hours | +0.9% (-3.0% to +5.0%; p 0.651) | 0.638 | 5.9% | 0.188 | 0.224 | -0.42 / -0.62 | not defined |
| Coronary heart disease, 35-64 | all (n = 3,024) | Unweighted | transit hours | -13.6% (-29.0% to +5.3%; p 0.144) | 0.061 | 32.4% | 0.032 | 0.096 | -7.90 / -8.92 | not defined |
| Stroke, 35-64 | all (n = 3,024) | Population-weighted | car hours | +1.3% (-2.6% to +5.4%; p 0.498) | 0.522 | 5.7% | 0.119 | 0.082 | 0.53 / 0.22 | +6.2% |
| Stroke, 35-64 | all (n = 3,024) | Population-weighted | transit hours | -7.2% (-15.5% to +1.9%; p 0.116) | 0.287 | 14.3% | 0.062 | 0.027 | 0.81 / 0.64 | -11.0% |
| Stroke, 35-64 | all (n = 3,024) | Unweighted | car hours | +0.4% (-2.1% to +2.9%; p 0.753) | 0.732 | 3.6% | 0.188 | 0.224 | -0.42 / -0.62 | not defined |
| Stroke, 35-64 | all (n = 3,024) | Unweighted | transit hours | -0.8% (-14.2% to +14.6%; p 0.908) | 0.895 | 22.8% | 0.032 | 0.096 | -7.90 / -8.92 | not defined |
| All CVD, 35-64 | pop>=65,000 both periods (n = 791) | Population-weighted | car hours | -2.7% (-11.3% to +6.7%; p 0.551) | 0.548 | 14.0% | 0.102 | 0.037 | 0.87 / 0.73 | -3.7% |
| All CVD, 35-64 | pop>=65,000 both periods (n = 791) | Population-weighted | transit hours | -12.3% (-25.8% to +3.7%; p 0.123) | 0.088 | 26.9% | 0.066 | 0.012 | 0.97 / 0.93 | -13.1% |
| All CVD, 35-64 | pop>=65,000 both periods (n = 791) | Unweighted | car hours | -4.3% (-9.9% to +1.6%; p 0.150) | 0.210 | 8.9% | 0.103 | 0.056 | 0.71 / 0.56 | -7.5% |
| All CVD, 35-64 | pop>=65,000 both periods (n = 791) | Unweighted | transit hours | -10.8% (-24.8% to +5.9%; p 0.187) | 0.123 | 27.5% | 0.039 | 0.013 | 0.90 / 0.86 | -12.5% |
| All CVD, 65+ | pop>=65,000 both periods (n = 791) | Population-weighted | car hours | -2.7% (-7.3% to +2.1%; p 0.253) | 0.368 | 7.1% | 0.102 | 0.038 | 0.86 / 0.73 | -3.7% |
| All CVD, 65+ | pop>=65,000 both periods (n = 791) | Population-weighted | transit hours | -14.8% (-25.7% to -2.2%; p 0.024) | 0.003 | 21.6% | 0.064 | 0.012 | 0.97 / 0.93 | -15.7% |
| All CVD, 65+ | pop>=65,000 both periods (n = 791) | Unweighted | car hours | -3.4% (-8.2% to +1.7%; p 0.183) | 0.228 | 7.6% | 0.103 | 0.056 | 0.71 / 0.56 | -5.9% |
| All CVD, 65+ | pop>=65,000 both periods (n = 791) | Unweighted | transit hours | -12.2% (-28.1% to +7.1%; p 0.195) | 0.119 | 32.8% | 0.039 | 0.013 | 0.90 / 0.86 | -14.1% |
| Coronary heart disease, 35-64 | pop>=65,000 both periods (n = 791) | Population-weighted | car hours | -5.2% (-14.7% to +5.4%; p 0.319) | 0.420 | 16.3% | 0.102 | 0.037 | 0.87 / 0.73 | -7.0% |
| Coronary heart disease, 35-64 | pop>=65,000 both periods (n = 791) | Population-weighted | transit hours | -27.2% (-46.4% to -1.1%; p 0.042) | 0.047 | 54.6% | 0.066 | 0.012 | 0.97 / 0.93 | -28.9% |
| Coronary heart disease, 35-64 | pop>=65,000 both periods (n = 791) | Unweighted | car hours | -4.4% (-14.7% to +7.3%; p 0.440) | 0.455 | 17.8% | 0.103 | 0.056 | 0.71 / 0.56 | -7.6% |
| Coronary heart disease, 35-64 | pop>=65,000 both periods (n = 791) | Unweighted | transit hours | -16.8% (-33.6% to +4.3%; p 0.108) | 0.090 | 37.9% | 0.039 | 0.013 | 0.90 / 0.86 | -19.3% |
| Stroke, 35-64 | pop>=65,000 both periods (n = 791) | Population-weighted | car hours | +2.0% (-4.8% to +9.3%; p 0.566) | 0.622 | 10.3% | 0.102 | 0.037 | 0.87 / 0.73 | +2.7% |
| Stroke, 35-64 | pop>=65,000 both periods (n = 791) | Population-weighted | transit hours | -6.5% (-18.4% to +7.1%; p 0.325) | 0.466 | 21.4% | 0.066 | 0.012 | 0.97 / 0.93 | -7.0% |
| Stroke, 35-64 | pop>=65,000 both periods (n = 791) | Unweighted | car hours | -3.3% (-9.9% to +3.9%; p 0.356) | 0.411 | 10.7% | 0.103 | 0.056 | 0.71 / 0.56 | -5.7% |
| Stroke, 35-64 | pop>=65,000 both periods (n = 791) | Unweighted | transit hours | -10.5% (-25.4% to +7.3%; p 0.225) | 0.245 | 29.5% | 0.039 | 0.013 | 0.90 / 0.86 | -12.2% |

Primary T2 estimate: -1.7% (-6.6% to +3.5%; p 0.511); unweighted -0.5% (-2.8% to +2.0%; p 0.700); MDE 7.6% weighted and 3.5% unweighted. Neither interval excludes zero, nor does the 65+ estimate (-0.9% (-3.5% to +1.8%; p 0.508)).

Attenuation. The population-weighted SD of the change in car hours is 0.119 hours a week, against a root-mean sampling SD of 0.082. After the other regressors and state effects are removed, only 22% of the remaining weighted variance is signal (conditional reliability 0.22); a coefficient is attenuated by about that factor under classical error, so a true effect would need to be about 39% per hour a week to reach the MDE. Unweighted, the estimated sampling variance exceeds the observed variance (reliability -0.42 raw, -0.62 conditional): the unweighted change in car hours is, by this estimate, indistinguishable from noise and no corrected value is defined. The published margins of error are conservative, and those of small counties in 2006-2010 are inflated, so reliability is understated to an unknown degree. In counties with at least 65,000 residents in both periods the conditional reliability is 0.73 (weighted) and 0.56 (unweighted) and the estimates are -2.7% (-11.3% to +6.7%; p 0.551) and -4.3% (-9.9% to +1.6%; p 0.150), with MDEs of 14.0% and 8.9%. The change design has no ability to detect effects of the size in Table 3.6.

Change in transit hours. The weighted coefficient is -15.0% (-25.2% to -3.4%; p 0.014) at 35-64 and -15.0% (-25.3% to -3.3%; p 0.014) at 65+; unweighted estimates are not distinguishable from zero and the unweighted reliability is negative. Because the association is as large at 65+ as at 35-64, the pre-specified falsification logic reads it as not specific to commuters. **Post hoc check (not in the plan):** the identifying variation is concentrated in a few large metropolitan counties (the five largest shares: Bronx County NY 12.3%, San Francisco County CA 7.1%, Alameda County CA 5.8%, Contra Costa County CA 3.9%, Hudson County NJ 3.6%; top 5 together 33%, top 20 55%). Dropping the 5, 10 and 20 units with the largest share of it gives -19.9% (-30.3% to -7.9%; p 0.002), -23.3% (-38.4% to -4.6%; p 0.018) and -19.5% (-38.4% to +5.2%; p 0.110) at 35-64, and -9.1% (-24.5% to +9.5%; p 0.308) at 65+ with 20 dropped. The point estimate is not produced by a handful of units, but its precision is. Its cause was not established: a co-trend in large transit-served metropolitan areas unrelated to commuting was not ruled out and cannot be tested with these data. It is not evidence of a benefit of transit commuting.

## 5. T3: matched high- versus low-driving counties, 2015-2019

### 5.1 Design

High-driving = top quartile and low-driving = bottom quartile of car-commute hours within each NCHS 2013 urban-rural class (757 and 758 units). Exact matching on urban-rural class and census region; within those strata, optimal 1:1 matching without replacement on the Mahalanobis distance of 11 covariates (Table 5.2), allowed only within a caliper of 0.2 SD of the logit propensity score (SD 3.30; caliper 0.66). The propensity model is a logistic regression of high versus low on the matching covariates and class and region indicators.

**Matched: 249 pairs. Discarded: 508 high-driving and 509 low-driving units** without an admissible partner. The two groups are strongly separated on the covariates (the logit propensity score differs by 1.68 SD before matching), so two-thirds of each group lie outside the region of overlap, and the matched contrast describes only counties that have a counterpart. 55 pairs are within one state. Mean car hours: 2.15 (high) versus 1.36 (low), a within-pair difference of 0.78 hours a week per adult.

**Table 5.1 Units available and pairs formed, by urban-rural class and region.**

| NCHS 2013 class | Region | Low-driving available | High-driving available | Pairs |
|---|---|---|---|---|
| 1 | Midwest | 1 | 0 | 0 |
| 1 | Northeast | 9 | 0 | 0 |
| 1 | South | 5 | 13 | 2 |
| 1 | West | 2 | 4 | 1 |
| 2 | Midwest | 20 | 18 | 4 |
| 2 | Northeast | 19 | 6 | 4 |
| 2 | South | 43 | 63 | 19 |
| 2 | West | 10 | 5 | 2 |
| 3 | Midwest | 16 | 20 | 2 |
| 3 | Northeast | 6 | 11 | 0 |
| 3 | South | 60 | 51 | 23 |
| 3 | West | 11 | 11 | 2 |
| 4 | Midwest | 19 | 28 | 8 |
| 4 | Northeast | 7 | 8 | 1 |
| 4 | South | 34 | 48 | 12 |
| 4 | West | 29 | 4 | 4 |
| 5 | Midwest | 50 | 58 | 13 |
| 5 | Northeast | 6 | 19 | 3 |
| 5 | South | 58 | 68 | 33 |
| 5 | West | 44 | 13 | 4 |
| 6 | Midwest | 112 | 107 | 47 |
| 6 | Northeast | 3 | 18 | 2 |
| 6 | South | 88 | 172 | 52 |
| 6 | West | 106 | 12 | 11 |

### 5.2 Balance

**Table 5.2 Standardised mean differences (high minus low, divided by the pooled SD before matching).**

| Variable | Role | Mean high / low, before | SMD before | Mean high / low, after | SMD after |
|---|---|---|---|---|---|
| `share_age_35_64` | matched on | 0.397 / 0.372 | +0.831 | 0.389 / 0.388 | +0.032 |
| `share_age_65plus` | matched on | 0.183 / 0.190 | -0.151 | 0.193 / 0.189 | +0.077 |
| `share_female` | matched on | 0.502 / 0.494 | +0.328 | 0.500 / 0.498 | +0.082 |
| `log_income` | matched on | 10.912 / 10.799 | +0.445 | 10.830 / 10.830 | +0.001 |
| `poverty_rate` | matched on | 0.136 / 0.170 | -0.539 | 0.153 / 0.153 | -0.002 |
| `share_bachelors_plus` | matched on | 0.208 / 0.236 | -0.287 | 0.205 / 0.211 | -0.061 |
| `unemployment_rate` | matched on | 0.050 / 0.058 | -0.302 | 0.052 / 0.051 | +0.038 |
| `share_nh_black` | matched on | 0.092 / 0.096 | -0.026 | 0.092 / 0.097 | -0.035 |
| `share_hispanic` | matched on | 0.076 / 0.124 | -0.330 | 0.087 / 0.106 | -0.128 |
| `share_uninsured_18_64` | matched on | 0.133 / 0.148 | -0.205 | 0.146 / 0.147 | -0.014 |
| `log_density` | matched on | 4.093 / 3.581 | +0.288 | 3.661 / 3.679 | -0.010 |
| `share_less_than_hs` | not matched on | 0.131 / 0.132 | -0.004 | 0.138 / 0.139 | -0.016 |
| `share_nh_asian` | not matched on | 0.012 / 0.016 | -0.132 | 0.009 / 0.015 | -0.173 |
| `share_nh_aian` | not matched on | 0.005 / 0.035 | -0.356 | 0.005 / 0.013 | -0.089 |
| `share_no_vehicle_hh` | not matched on | 0.053 / 0.077 | -0.453 | 0.056 / 0.068 | -0.237 |
| `workers_per_adult16` | not matched on | 0.558 / 0.521 | +0.450 | 0.537 / 0.533 | +0.047 |
| `places_r2020_csmoking_aa` | not matched on | 21.471 / 21.054 | +0.099 | 21.792 / 21.520 | +0.065 |
| `places_r2020_obesity_aa` | not matched on | 35.046 / 34.893 | +0.032 | 35.469 / 35.800 | -0.070 |
| `places_r2020_diabetes_aa` | not matched on | 10.688 / 11.154 | -0.196 | 10.968 / 11.128 | -0.067 |
| `places_r2020_lpa_aa` | not matched on | 27.110 / 26.658 | +0.084 | 27.799 / 27.961 | -0.030 |
| `intpt_lat` | not matched on | 37.565 / 39.065 | -0.278 | 37.021 / 38.280 | -0.233 |
| `intpt_lon` | not matched on | -88.085 / -96.643 | +0.659 | -90.637 / -93.469 | +0.218 |
| `car_hours_wk_per_adult16` | exposure | 2.231 / 1.309 | +2.645 | 2.145 / 1.363 | +2.242 |
| `transit_hours_wk_per_adult16` | exposure | 0.028 / 0.055 | -0.160 | 0.020 / 0.038 | -0.106 |
| `logit_ps` | propensity score | 1.695 / -2.548 | +1.676 | 0.206 / -0.054 | +0.103 |

Before matching the largest absolute SMD among the matching covariates is 0.83; after matching it is 0.128. The pre-specified target (all below 0.1) is missed by `share_hispanic` (-0.128). Covariates not matched on that remain above 0.1: `share_nh_asian` (-0.173), `share_no_vehicle_hh` (-0.237), `intpt_lat` (-0.233), `intpt_lon` (+0.218). High-driving matched counties have fewer households without a vehicle and lie further south and east than their partners. Because the target was missed, the plan designates the regression-adjusted pair difference as the estimate to interpret.

### 5.3 Contrast

**Table 5.3 Within-pair difference in the death rate, high- minus low-driving county.** Intervals: CR1 clustered by the state of the high-driving county, t reference.

| Outcome | Estimator | Pairs / state clusters | Difference (95% CI); p | Paired-t 95% CI; p | Per hour a week (ratio of means) | E-value: point / CI limit | MDE |
|---|---|---|---|---|---|---|---|
| All CVD, 35-64 | unadjusted pair difference | 249 / 42 | -3.9% (-9.2% to +1.7%; p 0.166) | -7.59% to -0.05%; p 0.047 | -5.0% (-11.6% to +2.2%) | 1.25 / 1.00 | 8.4% |
| All CVD, 35-64 **(T3)** | regression-adjusted for covariate differences | 249 / 42 | -6.2% (-11.2% to -0.8%; p 0.026) |  | -7.8% (-14.1% to -1.0%) | 1.33 / 1.10 | 8.2% |
| All CVD, 65+ | unadjusted pair difference | 249 / 42 | +0.6% (-2.4% to +3.6%; p 0.706) | -1.6% to +2.8%; p 0.617 | +0.7% (-3.0% to +4.6%) | 1.08 / 1.00 | 4.3% |
| All CVD, 65+ | regression-adjusted for covariate differences | 249 / 42 | -1.0% (-4.4% to +2.5%; p 0.559) |  | -1.3% (-5.6% to +3.2%) | 1.11 / 1.00 | 5.0% |

At ages 35-64 the high-driving county of a pair has the higher rate in 42.6% of pairs (Wilcoxon signed-rank p 0.060). The unadjusted mean difference is -3.9% (-9.2% to +1.7%; p 0.166); adjusted for the remaining covariate differences it is -6.2% (-11.2% to -0.8%; p 0.026). At 65+ the differences are +0.6% (-2.4% to +3.6%; p 0.706) and -1.0% (-4.4% to +2.5%; p 0.559). The ordinary paired-t interval for the unadjusted 35-64 difference is narrower (-7.59% to -0.05%) than the state-clustered one because pairs in the same state are not independent.

Sensitivity to unmeasured confounding. E-values (rate-ratio scale): for the adjusted 35-64 estimate, 1.33 for the point estimate and 1.10 for the confidence limit nearer the null; an unmeasured county characteristic associated with both high driving and mortality by a rate ratio of about 1.10 each, beyond the measured covariates, would be enough to move the interval to include no difference. For the unadjusted estimate the E-values are 1.25 and 1.00 (the interval already includes zero). Rosenbaum bounds: the one-sided signed-rank p-value at Gamma = 1 is 0.030, above 0.025, so the unadjusted contrast is not significant even with no hidden bias and the bounds are not applicable, as the plan specified. The inverse matched association is therefore fragile: it appears only after regression adjustment and would be removed by weak unmeasured confounding.

## 6. Sensitivity analyses

All are M3, population-weighted, log all-CVD mortality at 35-64, 2015-2019, state-clustered, unless stated. Compared with the primary estimate (-4.6% (-11.1% to +2.4%; p 0.186)). q = Benjamini-Hochberg q-value in the pre-specified family of 26.

**Table 6.1 Driving-exposure coefficient across the sensitivity family.**

| Spec | Description | n | Unit | Estimate (95% CI); p | q | Sign differs | Significance changes | Ratio to primary | Transit coefficient; p |
|---|---|---|---|---|---|---|---|---|---|
| L-M0-w | M0, population-weighted | 3,024 | per hour a week | -28.9% (-33.8% to -23.6%; p <0.001) | 0.000 | no | yes | 7.24 | -22.5%; p <0.001 |
| L-M1-w | M1, population-weighted | 3,024 | per hour a week | -27.5% (-36.2% to -17.6%; p <0.001) | 0.000 | no | yes | 6.83 | -21.5%; p <0.001 |
| L-M2-w | M2, population-weighted | 3,024 | per hour a week | -3.6% (-11.0% to +4.5%; p 0.367) | 0.523 | no | no | 0.78 | -5.1%; p 0.209 |
| L-M4-w | M4, population-weighted | 3,024 | per hour a week | -4.2% (-10.7% to +2.8%; p 0.227) | 0.393 | no | no | 0.91 | -0.2%; p 0.954 |
| L-M0-u | M0, unweighted | 3,024 | per hour a week | -10.5% (-16.5% to -4.0%; p 0.002) | 0.011 | no | yes | 2.35 | -41.4%; p 0.005 |
| L-M1-u | M1, unweighted | 3,024 | per hour a week | -16.1% (-23.6% to -8.0%; p <0.001) | 0.002 | no | yes | 3.74 | -46.0%; p 0.005 |
| L-M2-u | M2, unweighted | 3,024 | per hour a week | -0.4% (-4.1% to +3.5%; p 0.838) | 0.872 | no | no | 0.08 | -0.7%; p 0.829 |
| L-M3-u | M3, unweighted | 3,024 | per hour a week | -6.9% (-9.3% to -4.4%; p <0.001) | 0.000 | no | yes | 1.51 | +2.1%; p 0.401 |
| L-M4-u | M4, unweighted | 3,024 | per hour a week | -6.9% (-9.3% to -4.4%; p <0.001) | 0.000 | no | yes | 1.52 | +4.5%; p 0.081 |
| F-metro | M3, metropolitan counties only | 1,159 | per hour a week | -2.3% (-11.3% to +7.6%; p 0.632) | 0.715 | no | no | 0.49 | -4.7%; p 0.261 |
| S1 | Drive-alone hours in place of car hours | 3,024 | per hour a week | -5.2% (-12.2% to +2.3%; p 0.162) | 0.325 | no | no | 1.15 | -4.2%; p 0.303 |
| S2 | Mean one-way car travel time (per 10 min), with car commuters per adult | 3,024 | per 10 minutes one way | -3.5% (-8.6% to +1.9%; p 0.190) | 0.354 | no | no |  | -6.0%; p 0.269 |
| S3 | Share of car commuters at 60+ min (per 10 points), with car commuters per adult | 3,024 | per 10 percentage points | -1.6% (-5.3% to +2.2%; p 0.399) | 0.523 | no | no |  | -5.5%; p 0.322 |
| S4a | Published car aggregate (units where published) | 1,361 | per hour a week | -1.7% (-10.9% to +8.5%; p 0.731) | 0.792 | no | no | 0.36 | -4.6%; p 0.218 |
| S4b | Published car and transit aggregates (units where both published) | 1,031 | per hour a week | -0.5% (-9.9% to +9.8%; p 0.913) | 0.913 | no | no | 0.11 | -4.6%; p 0.250 |
| S5 | Excluding counties under 20,000 population | 1,829 | per hour a week | -3.2% (-10.5% to +4.8%; p 0.417) | 0.523 | no | no | 0.68 | -3.9%; p 0.360 |
| S6 | 2010-2014 cross-section | 3,024 | per hour a week | -6.5% (-12.5% to -0.2%; p 0.043) | 0.140 | no | yes | 1.44 | -6.9%; p 0.113 |
| S7-men | Men, ages 35-64 | 2,972 | per hour a week | -3.7% (-10.2% to +3.3%; p 0.281) | 0.429 | no | no | 0.81 | -4.4%; p 0.210 |
| S7-women | Women, ages 35-64 | 2,967 | per hour a week | -6.8% (-14.0% to +1.1%; p 0.088) | 0.225 | no | no | 1.49 | -1.9%; p 0.717 |
| S8 | Five commute days a week (rescaling; not a separate test) | 3,024 | per hour a week | -4.1% (-10.0% to +2.1%; p 0.186) | not in family | no | no | 0.90 | -3.6%; p 0.332 |
| S9-Northeast | Leaving out the Northeast | 2,807 | per hour a week | -6.3% (-13.2% to +1.2%; p 0.095) | 0.225 | no | no | 1.38 | +21.0%; p 0.005 |
| S9-Midwest | Leaving out the Midwest | 2,019 | per hour a week | -6.7% (-14.0% to +1.1%; p 0.087) | 0.225 | no | no | 1.49 | -3.8%; p 0.267 |
| S9-South | Leaving out the South | 1,628 | per hour a week | +2.1% (-3.1% to +7.5%; p 0.423) | 0.523 | yes | no | -0.44 | -6.2%; p 0.074 |
| S9-West | Leaving out the West | 2,618 | per hour a week | -7.1% (-13.2% to -0.5%; p 0.036) | 0.133 | no | yes | 1.56 | -3.5%; p 0.351 |
| S10 | M3 + workers per adult 16+ | 3,024 | per hour a week | -4.8% (-11.0% to +1.9%; p 0.155) | 0.325 | no | no | 1.03 | -4.2%; p 0.308 |
| S11 | Excluding the five New York City counties | 3,019 | per hour a week | -4.1% (-10.9% to +3.3%; p 0.264) | 0.429 | no | no | 0.88 | +13.5%; p 0.030 |
| S12 | Car hours without the transit term | 3,024 | per hour a week | -2.7% (-10.6% to +5.9%; p 0.519) | 0.613 | no | no | 0.58 |  |

Where sign, size or significance change:

- **Sign.** One of 26 estimates is positive: leaving out the South, +2.1% (-3.1% to +7.5%; p 0.423). With the Northeast, Midwest or West left out the estimates are -6.3%, -6.7% and -7.1%. The weighted inverse estimate therefore depends on Southern counties.
- **Significance.** The primary estimate is not significant. 8 of 26 are nominally significant, all negative: the raw rungs M0 and M1 (weighted and unweighted), the unweighted M3 and M4 models, the 2010-2014 cross-section (-6.5% (-12.5% to -0.2%; p 0.043), q 0.140) and leaving out the West (-7.1% (-13.2% to -0.5%; p 0.036), q 0.133). 6 keep q < 0.05: L-M0-w, L-M1-w, L-M0-u, L-M1-u, L-M3-u, L-M4-u.
- **Size.** Among estimates in hours a week, ratios to the primary range from -0.44 to 7.24; excluding the raw rungs M0 and M1 the range is -0.44 to 1.56.
- **Alternative exposures.** Drive-alone hours: -5.2% (-12.2% to +2.3%; p 0.162). Mean one-way car travel time, holding car commuters per adult fixed: -3.5% (-8.6% to +1.9%; p 0.190) per 10 minutes, with -3.6% (-7.161% to -0.003%; p 0.050) per 10 points of car commuters per adult. Share of car commuters travelling 60+ minutes: -1.6% (-5.3% to +2.2%; p 0.399) per 10 points. None is positive.
- **Published aggregates.** Where the published car aggregate exists (n = 1,361): -1.7% (-10.9% to +8.5%; p 0.731), against -1.5% for the scaled-midpoint measure on the same units. Where both published aggregates exist (n = 1,031): -0.5% (-9.9% to +9.8%; p 0.913), against -0.6%. The choice of measure makes no material difference; the smaller estimates reflect the subsample, not the measure.
- **Employment.** Adding workers per adult 16+ (S10) leaves the car coefficient at -4.8% (-11.0% to +1.9%; p 0.155); workers per adult itself is associated with -5.9% (-10.3% to -1.3%; p 0.013) mortality per 10 percentage points. The employment component of the exposure, one of the two candidate explanations named in the plan for an inverse association, does not account for the car coefficient in this model.
- **Small counties, sex, commute days.** Excluding counties under 20,000 residents: -3.2% (-10.5% to +4.8%; p 0.417). Men -3.7% (-10.2% to +3.3%; p 0.281); women -6.8% (-14.0% to +1.1%; p 0.088). Assuming five commute days rescales the coefficient by 4.5/5 = 0.9 (-4.1%; same p).
- **Transit coefficient.** Unstable: -4.0% in the primary model, +13.5% (p 0.030) without New York City, +21.0% (p 0.005) without the Northeast.

## 7. The three tests against the pre-specified decision rule

**Table 7.1 Family A: car-commute time and all-CVD mortality at 35-64.**

| Test | n | Unit | Estimate (95% CI); p | MDE | BH q | Holm p | Classification under the plan |
|---|---|---|---|---|---|---|---|
| T1 cross-section (M3, weighted) | 3,024 | per hour a week | -4.6% (-11.1% to +2.4%); p 0.186 | 10.5% | 0.278 | 0.371 | Null (interval includes zero). Informative against the driving-specific benchmark; uninformative about sitting-sized effects. |
| T2 change 2006-2010 to 2015-2019 (weighted) | 3,024 | per hour a week | -1.7% (-6.6% to +3.5%); p 0.511 | 7.6% | 0.511 | 0.511 | Null (interval includes zero); weakly identified (conditional reliability 0.22). |
| T3 matched high vs low (regression-adjusted for covariate differences) | 249 | high vs low driving | -6.2% (-11.2% to -0.8%); p 0.026 | 8.2% | 0.077 | 0.077 | Inverse association in this test (interval excludes zero); not significant after multiplicity adjustment; unadjusted pair difference null. |

- **Support for the hypothesis: none.** No test gives a positive coefficient; no positive estimate with an interval excluding zero appears for any outcome, weighting, subsample or alternative exposure.
- **Primary test: null.** The weighted interval includes zero under state clustering. Under Conley errors it just excludes zero (-8.94% to -0.05%; p 0.048); the plan requires both for 'evidence against'.
- **Inconsistency that is not resolved here.** The unweighted T1 estimate is inverse with intervals excluding zero under both inference methods (-6.9% (-9.3% to -4.4%; p <0.001)), which would meet the 'evidence against' criterion had it been the primary estimate. Weighted and unweighted estimates agree in sign and differ in significance. The weighted estimate rests on large counties and is sensitive to the South; the unweighted estimate treats every county alike and rests on many small counties whose exposure is measured with more error and whose mortality is more heavily smoothed.
- **Across the three tests** all point estimates are negative, and one (T3, adjusted) has an unadjusted p below 0.05 but q = 0.077. The pre-specified criteria for consistent evidence in either direction are not met.
- **Interpretation allowed by the design.** An inverse ecological association is not a protective effect. Of the two candidate explanations named in the plan, the employment component alone does not account for it: S10 leaves the coefficient essentially unchanged (-4.8% against -4.6%), and in S2 both margins have negative point estimates (-3.5% per 10 minutes of car travel time, p 0.190; -3.6% per 10 points of car commuters per adult, p 0.050). Urban form and regional composition remain (the estimate changes sign without the South, and matched high-driving counties have fewer car-free households). Selection of healthier, employed, higher-income households into long car commutes is a further possibility that these data cannot test.

## 8. The 15 Bay Area study counties in the national distributions (descriptive)

Percentiles are the percent of national units at or below the county's value (2015-2019; 3,136 units for exposure, 3,083 for mortality at 35-64, 3,024 at 65+). Change = 2015-2019 minus 2006-2010.

| County | Group | Car hours/week per adult (pctile) | Transit hours (pctile) | All-CVD 35-64 per 100,000 (pctile) | All-CVD 65+ (pctile) | Change in car hours (pctile) | Change in log all-CVD 35-64 (pctile) | Car quartile within urban-rural class | In matched set |
|---|---|---|---|---|---|---|---|---|---|
| Alameda | core 9 | 1.92 (68) | 0.74 (99) | 78.3 (7) | 1174 (6) | +0.16 (77) | -0.226 (1) | 3 | no |
| Contra Costa | core 9 | 2.52 (94) | 0.63 (99) | 71.8 (4) | 1184 (6) | +0.39 (96) | -0.166 (3) | 3 | no |
| Marin | core 9 | 1.95 (71) | 0.53 (99) | 39.3 (0) | 930 (0) | +0.14 (72) | -0.176 (2) | 1 | no |
| Napa | core 9 | 2.02 (76) | 0.09 (93) | 70.8 (4) | 1272 (13) | +0.14 (72) | -0.047 (21) | 4 | matched, high-driving |
| San Francisco | core 9 | 1.23 (12) | 1.50 (100) | 73.1 (5) | 1070 (2) | +0.06 (49) | -0.194 (2) | 1 | matched, low-driving |
| San Mateo | core 9 | 2.04 (77) | 0.54 (99) | 57.4 (1) | 1093 (2) | +0.29 (91) | -0.211 (1) | 1 | matched, low-driving |
| Santa Clara | core 9 | 2.29 (88) | 0.23 (97) | 58.7 (1) | 1084 (2) | +0.43 (97) | -0.110 (7) | 4 | no |
| Solano | core 9 | 2.52 (94) | 0.19 (97) | 93.2 (16) | 1241 (10) | +0.24 (87) | -0.128 (5) | 4 | no |
| Sonoma | core 9 | 1.98 (73) | 0.09 (93) | 67.4 (3) | 1282 (14) | +0.07 (53) | -0.109 (8) | 3 | no |
| Merced | adjacent 6 | 1.92 (69) | 0.04 (84) | 116.4 (36) | 1485 (42) | +0.15 (74) | -0.083 (13) | 3 | no |
| Sacramento | adjacent 6 | 2.06 (79) | 0.11 (94) | 116.4 (36) | 1444 (36) | +0.17 (79) | -0.037 (25) | 3 | no |
| San Benito | adjacent 6 | 3.05 (99) | 0.04 (86) | 73.9 (5) | 1214 (8) | +0.71 (99) | -0.053 (20) | 4 | no |
| San Joaquin | adjacent 6 | 2.51 (94) | 0.10 (93) | 125.1 (44) | 1525 (48) | +0.38 (95) | -0.055 (19) | 4 | no |
| Santa Cruz | adjacent 6 | 1.95 (71) | 0.11 (95) | 58.5 (1) | 1165 (5) | +0.08 (56) | -0.175 (2) | 3 | no |
| Stanislaus | adjacent 6 | 2.21 (85) | 0.04 (85) | 141.3 (55) | 1618 (62) | +0.28 (91) | +0.001 (39) | 4 | no |

The nine core counties lie between percentiles 12 (San Francisco) and 94 of car-commute hours and between percentiles 0.1 and 16.3 of all-CVD mortality at 35-64; all nine are above percentile 93 of transit hours. Their changes in car hours lie between percentiles 49 and 97 and their changes in log mortality between percentiles 0.8 and 21.3 (larger declines than most of the country). The region combines long car commutes, high transit use and low cardiovascular mortality, the same direction as the national inverse association and an illustration of why it cannot be read causally: the nine core counties are at or above percentile 95 of median household income and percentile 77 of the share with a bachelor's degree. 3 Bay Area counties (Alameda, Contra Costa, San Francisco) are among the five units carrying the most identifying variation in the weighted transit-change coefficient (section 4.2).

## 9. Departures from and additions to the pre-specified plan

No pre-specified model was dropped or altered. Additions, all reported:

1. **Post hoc:** influence check of the weighted transit-change coefficient in T2 (dropping the 5, 10 and 20 units with the largest share of identifying variation, and the five New York City counties), run after seeing that coefficient. Script `nat03b_change_posthoc.py`; files `national_change_transit_influence_posthoc.csv` and `national_change_transit_influence_units_posthoc.csv`.
2. Added without being named in the plan: an MDE for the matched contrast (same formula with the matched design's cluster degrees of freedom); the MDE of T2 expressed on the error-free scale (MDE / conditional reliability); Conley standard errors at 100 and 500 km for every cross-sectional coefficient; coronary heart disease and stroke versions of the 35-64 versus 65+ contrast (in the contrasts file, not discussed); the full ladder for every secondary outcome (in the models file).
3. The plan's family C counts M3 unweighted as a sensitivity estimate and it is reported both there and in the ladder.
4. The plan describes the five-year mean rate as the outcome; means are missing unless all five annual rates are published, so no partial-period means enter.
5. **Erratum to the plan (the plan file itself was not edited).** Section 5 of the plan prints the upper limit of the DR003 driving-specific benchmark as 7.6% per hour a week. The value computed from the dose-response table is 7.65% (7.7% to one decimal), as shown in Table 3.6. The point value used in the decision rule (4.1%) and every other benchmark figure in the plan agree with the computed values.

## 10. Assumptions

1. Linear effect of hours on the log rate; the two commute exposures enter additively.
2. Commuters travel 4.5 days a week and make two trips a day; a different constant rescales the coefficients only.
3. Bin-midpoint minutes scaled to the published county total measure mode-specific time without differential error across counties.
4. State clustering (51 clusters) or a 200 km Bartlett kernel captures the dependence among county residuals, including that induced by mortality smoothing.
5. Population weights are treated as fixed.
6. In T2, sampling errors of the two periods are independent and classical; margins of error are converted with 1.645.
7. In T3, Mahalanobis distance uses the covariance of the 11 covariates among top- and bottom-quartile units; calipers use the logit propensity score; pair differences are clustered by the high-driving county's state.
8. E-values treat the rate ratio of a rare outcome as a risk ratio.
9. Literature benchmarks: the assumptions listed under Table 3.6.

## 11. Limitations

This is an ecological, observational analysis of county populations, and no coefficient here is an effect of driving on a person. The exposure is the usual journey to work reported in the American Community Survey, averaged over all residents aged 16 or more: it omits all non-commute driving, counts carpool passengers as car time, assumes 4.5 commute days for everyone, and says nothing about which residents drive, for how many years, or whether those who died ever commuted; road rage and traffic stress are not measured at all. Mode-specific minutes are bin midpoints scaled to the county total, and sampling error is large in small counties, which attenuates coefficients (in the change model most of the identifying variation is noise, and the margins used to quantify this are approximate and conservative). The outcome is a model-smoothed, age-standardised rate for two broad age bands that ends in 2019: smoothing borrows strength across neighbouring counties, years and demographic groups, so county values are dependent, small-county values are pulled toward their neighbours, published uncertainty is understated, and differences between periods partly reflect the smoothing model; state-clustered and Conley errors address this only partly, and the residuals remain spatially autocorrelated. Exposure and outcome are contemporaneous, with no latency, and refer to different people; migration, residential sorting and the healthy-worker effect could each produce an inverse association like the one found, and adjustment for county composition (income, poverty, education, unemployment, race and ethnicity, insurance, urban-rural class, density, state) cannot remove confounding by unmeasured characteristics such as occupation mix, wealth, diet, air pollution, health-care access or measured rather than modelled smoking. The smoking, obesity, diabetes and inactivity covariates are model-based PLACES estimates for 2018 built partly from the same demographic predictors, are possible mediators, and are used only in a sensitivity model. Health-insurance coverage does not exist for 2006-2010 and is omitted from the change model; dollar amounts are nominal. The matched contrast discards two-thirds of high- and low-driving counties for lack of overlap, misses its balance target on one covariate, retains imbalance on vehicle ownership and geography, defines high and low driving relative to each urban-rural class, and gives an inverse association only after regression adjustment that weak unmeasured confounding would remove. The transit comparison rests on about 80 counties and changes sign when New York City is excluded, so it cannot serve as a sitting-without-driving control. The population-weighted and unweighted estimates differ in significance, and the weighted estimate changes sign without the South. The literature benchmarks come from one cohort of men for driving-specific risk and from self-reported total sitting for generic risk, and converting them to county commute hours requires the assumptions listed above; the design's minimum detectable effects are many times the sitting-based benchmark, so the absence of a positive association does not show that prolonged driving is harmless. Pandemic years are excluded, so nothing here speaks to commuting after 2019.

## 12. Files

- [national_prespecified_plan.md]({{artifact:55b27226-16f3-44cc-9873-07fd33597057}}): the plan saved before fitting
- [national_cross_section_models.csv]({{artifact:f129ed3a-61b0-46a7-a3dd-fff2cc221970}}): T1: every outcome x sample x rung x weighting x exposure, with state-clustered and Conley inference, car = transit tests, MDE
- [national_falsification_contrasts.csv]({{artifact:18925103-4e83-49bc-ab2d-7d2c1eb11099}}): 35-64 versus 65+ contrasts with cross-equation covariance
- [national_cross_section_diagnostics.csv]({{artifact:efcc6b62-d06d-4293-bbf8-6874a4ab7c92}}): Moran's I and quintile models
- [national_benchmarks.csv]({{artifact:d4ab0cd0-c64b-429c-b7a7-a22bf61e16bd}}): literature benchmarks against the primary estimate and MDE
- [national_cross_section_sample.csv]({{artifact:d2f5efea-b7cb-47df-b71d-69a24633bf64}}): sample summaries
- [national_cross_section_sample_extra.json]({{artifact:2b3805cf-7058-4ab8-a5a7-c01aa4e74da4}}): sample counts and car-commuter prevalence by age
- [national_change_models.csv]({{artifact:46386901-a87d-4d37-b27b-e1ce04da2b10}}): T2 estimates, reliability, MDE
- [national_change_analysis_data.csv]({{artifact:24d83973-31aa-474e-a7ac-70686c8e8196}}): county-level changes used in T2
- [national_change_sample.json]({{artifact:f075141a-ee10-45d5-a3b0-81fdf303d9bc}}): T2 sample summary
- [national_change_transit_influence_posthoc.csv]({{artifact:f681c9da-9bad-43c0-b9bb-7891d8f41825}}): post hoc influence check
- [national_change_transit_influence_units_posthoc.csv]({{artifact:05c3fe2a-04d3-4f3a-a704-ab3fcd2881dd}}): post hoc: the 20 units with the largest share of identifying variation in the transit change
- [national_matched_contrast.csv]({{artifact:86956414-e997-4660-a2c1-823493e90f8d}}): T3 contrasts, E-values, Rosenbaum summary
- [national_matched_balance.csv]({{artifact:50b78b71-9940-4297-adfe-99668286223f}}): balance before and after matching
- [national_matched_pairs.csv]({{artifact:f9d8e92c-97b6-4088-ac03-7f27ae00889c}}): the matched pairs with covariates
- [national_matched_counts.csv]({{artifact:b310d902-5fa3-49d7-b6a9-04af1b6ab4be}}): units available and matched by stratum
- [national_matched_rosenbaum.csv]({{artifact:5e91deed-552d-42d5-b74c-cecf0720555c}}): Rosenbaum bound p-values by Gamma
- [national_matched_meta.json]({{artifact:2bb4e936-172e-423e-b046-f46fda931f4e}}): matching counts, caliper, balance summary
- [national_sensitivity.csv]({{artifact:3f851a37-20ed-427f-b481-e25b31984697}}): sensitivity family with flags and q-values
- [national_family_A.csv]({{artifact:7099c5a3-e475-4ac0-b6c2-34bce80f090b}}): the three confirmatory tests with BH and Holm adjustment
- [national_plot_tables.parquet]({{artifact:dbeca562-34c7-46ad-b554-b50e206ef296}}): county-level exposure, outcome and residualised values behind M3 (binned scatter)
- [national_plot_coefficient_ladder.csv]({{artifact:6e4359ad-ed75-44c8-8428-201ad9b1cd21}}): ladder for plotting
- [national_plot_falsification.csv]({{artifact:37fcb00f-223f-4651-a16f-e99b35a27327}}): falsification contrasts for plotting
- [national_plot_change.csv]({{artifact:44dd23d1-93b1-41a1-a433-81aacc2fd34a}}): county-level changes with residualised values
- [national_plot_matched_pairs.csv]({{artifact:3abde0f9-dd31-4dad-a1de-0892c89d93b5}}): matched-pair differences
- [national_bay_area_position.csv]({{artifact:5f0e907b-01e1-4779-abd6-480642e14fa0}}): the 15 Bay Area study counties in the national distributions
- Scripts, run in this order from the workspace root: [nat_common.py]({{artifact:b9f13bf3-c6e6-4ff1-9814-b6f70972c2cf}}), [nat02_cross_section.py]({{artifact:4baaae58-980f-4233-b934-29731ba59fe6}}), [nat03_change.py]({{artifact:4e654a41-2021-4e75-9857-2a05fc06ea03}}), [nat03b_change_posthoc.py]({{artifact:0895f6a6-a315-4db8-abb7-565e5a2e44af}}), [nat04_matched.py]({{artifact:17ecc09d-e7d3-4e75-8bf4-5a166a4e5a6b}}), [nat05_sensitivity.py]({{artifact:095d63d4-22a0-49fa-8c19-6fa5690bf0ee}}), [nat06_plot_tables.py]({{artifact:df4a6691-0fd6-4d59-99e8-6ac67f7ca958}}), [nat07_write_report.py]({{artifact:ff26d896-1154-4ab4-8a83-b7369974c8e0}}). Input paths are read from `handoff/national_input_paths.json` (keys county, annual, dose: the national county parquet, the annual mortality parquet, and the dose-response table).

Software: Python 3.11.17; numpy 2.4.6, pandas 2.3.3, scipy 1.17.1, statsmodels 0.15.0. Seed 20261113.
