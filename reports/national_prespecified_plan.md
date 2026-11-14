# National county study of car-commute time and cardiovascular mortality: pre-specified analysis plan

Written 2026-11-13 23:28 UTC, BEFORE any national exposure-outcome association was computed, tabulated or plotted. This file is not edited after it is saved. Anything added later is labelled "post hoc" in the results.

## 0. What had been seen when this plan was written

- The data dictionary and QC report of the national dataset (marginal distributions of exposures and of mortality; missingness; exposure medians by urban-rural class).
- The earlier Bay Area analysis (`methods_results_ecological.md`), which includes 15-county regressions of county mortality on drive-alone share and 60+ minute share. Those are exposure-outcome associations for 15 of the 3,136 units, with different exposure definitions.
- The literature table `dose_response_parameters.csv`.
- In this session, tabulations of exposure and covariate columns ONLY (the mortality and PLACES columns were not loaded): counts of counties by urban-rural class, census region and within-class exposure quartile; missingness of covariates; national car-commuter prevalence by age band.
- No correlation, regression, cross-tabulation or plot of any mortality or PLACES variable against any commute variable in the national file.

## 1. Question, design and reading rule

Question: do county populations with more car-commute time per adult have higher cardiovascular mortality, and is any such association specific to driving (versus transit commuting) and to the working-age band?

Design: ecological, observational, US county units. All estimates are associations between county-level quantities. None is a causal effect and none describes individuals. Results are reported whatever their sign.

Three pre-specified tests of the primary hypothesis: (T1) 2015-2019 cross-section; (T2) change from 2006-2010 to 2015-2019; (T3) matched high- versus low-driving counties. Years from 2020 onward are not used.

## 2. Data, units, samples

- Units: the 3,136 CDC mortality county units (`fips`). Periods: `acs_vintage` 2010 (2006-2010), 2014 (2010-2014), 2019 (2015-2019).
- Cross-sectional sample (T1, T3, sensitivity): 2015-2019 rows with `complete_case_main` true (primary exposures, all-CVD mortality in both age bands and core covariates present; 3,024 units by the QC report). The same units are used for the 35-64 and 65+ outcomes so the two are comparable. Sex-specific outcomes use the subset with a published sex-specific rate. No imputation.
- Change sample (T2): units with `complete_case_main` true in both 2006-2010 and 2015-2019.
- The one row whose exposure was scaled with the period-median factor (Loving County TX, 2015-2019) is kept if it is in the sample.

## 3. Variables

**Outcomes** (period mean of five annual model-smoothed, within-band age-standardised rates per 100,000; natural log):
- Primary: log `mort_cvd_35_64` (all cardiovascular disease, ages 35-64, both sexes).
- Secondary: log `mort_cvd_65plus`; log `mort_chd_35_64`, `mort_chd_65plus`; log `mort_stroke_35_64`, `mort_stroke_65plus`; log `mort_cvd_35_64_men`, `mort_cvd_35_64_women`.

**Exposures** (entered jointly, linear, hours per week per resident aged 16+):
- Primary: `car_hours_wk_per_adult16` (car, truck or van; drove alone + carpooled).
- Comparison: `transit_hours_wk_per_adult16`.

**Reported scale**: 100 x (exp(b) - 1) = percent difference in the mortality rate per additional hour per week of commute per adult resident, with 95% confidence intervals transformed the same way.

**Covariate ladder** (cross-section):
- M0: car hours + transit hours only.
- M1: M0 + `share_age_18_34`, `share_age_35_64`, `share_age_65plus` (reference: under 18), `share_female`.
- M2: M1 + log `median_hh_income`, `poverty_rate`, `share_bachelors_plus`, `share_less_than_hs`, `unemployment_rate`, `share_nh_black`, `share_hispanic`, `share_nh_asian`, `share_nh_aian` (reference: non-Hispanic White and all other), `share_uninsured_18_64`.
- **M3 (primary)**: M2 + indicators for `nchs_ur_2013` (six classes), log `pop_density`, state fixed effects (50 states + DC).
- M4 (sensitivity only; possible mediators, model-based): M3 + `places_r2020_csmoking_aa`, `places_r2020_obesity_aa`, `places_r2020_diabetes_aa`, `places_r2020_lpa_aa`.

Not in the ladder: the share of households without a vehicle (a component of the exposure rather than a confounder) and the employment-to-population ratio. Car hours per adult is the product of workers per adult, car share and travel time, so employment is both a component of the exposure and a correlate of health (healthy-worker effect). This is handled by two pre-specified sensitivity analyses (S2 decomposition, S10 employment adjustment), and a sign difference between M3 and S10 will be reported as non-robustness to employment adjustment.

## 4. Estimation and inference (T1 cross-section)

- Estimator: linear regression of the log rate. **Primary weighting: population-weighted**, weight = `pop_35_64` for 35-64 outcomes and `pop_65plus` for 65+ outcomes (2015-2019 ACS). Unweighted estimates are reported beside every weighted estimate. A sign difference between weighted and unweighted primary estimates will be reported as non-robustness.
- **Primary inference**: cluster-robust (CR1) standard errors clustered by state (51 clusters), t reference with 50 degrees of freedom.
- **Spatially robust alternative**: Conley (1999) spatial HAC standard errors, Bartlett kernel, great-circle distance between county internal points, cutoff 200 km (100 km and 500 km also reported), normal reference. Applied to the same (weighted or unweighted) estimating equations with state effects as indicators.
- Diagnostic: Moran's I of the M3 residuals with row-standardised 8-nearest-neighbour weights, 999 permutations.
- **Car = transit**: Wald test of equal coefficients in each rung (state-clustered; Conley as alternative).
- **Primary test (T1)**: car coefficient in M3, population-weighted, log all-CVD mortality at 35-64, state-clustered, two-sided 5%.
- Functional form (descriptive, not a test): M3 with indicators for national population-weighted quintiles of car hours in place of the linear term.

**Falsification tests**
- (a) Negative-control outcome: the same ladder for log all-CVD mortality at 65+. The contrast b_car(35-64) - b_car(65+) in M3 is estimated with a state-clustered covariance across the two equations. People aged 65+ are imperfect negative controls: some still commute (national car-commuter prevalence in 2015-2019: 0.139 at 65+ versus 0.595 at 45-64, computed from the exposure columns) and past commuting may matter. Under a contemporaneous effect of driving, the 65+ coefficient should be roughly 0.139/0.595 = 0.23 of the 35-64 coefficient. A 65+ coefficient as large as, or larger than, the 35-64 coefficient points to confounding by place.
- (b) The car coefficient in M3 within metropolitan counties only (`nchs_ur_2013` 1-4). (Non-metropolitan counties are reported beside it for description.)
- (c) Negative-control exposure: the transit coefficient. Both exposures involve sitting and commute duration; only one involves driving. This contrast rests on few units (81 with at least 0.25 transit hours a week), so it is reported with that caveat and with S11.

## 5. Scale of the literature and minimum detectable effect

Fixed conversions (computed from `dose_response_parameters.csv` before fitting):
- **Generic sitting** (DR027, relative risk 1.02 (1.01-1.03) per additional hour a day of total sedentary time): one more commute hour a week adds f/7 hours a day of sitting, where f is the fraction of commute time that is net additional sitting. Expected difference per hour a week = 100 x (1.02^(f/7) - 1): **0.14% (0.07% to 0.21%) for f = 0.5; 0.28% (0.14% to 0.42%) for f = 1**.
- **Driving-specific** (DR001-DR003, one cohort of men; hazard ratios 1.09, 1.23, 1.50 for 4-7, 7-10 and >10 versus <4 hours a week riding in a car): category midpoints 2, 5.5, 8.5 and an assumed 12 hours a week for the open top category. (i) Single contrast DR003: ln(1.50)/10 per hour, **4.1% (0.8% to 7.6%) per hour a week**. (ii) Inverse-variance weighted slope through the reference over the three contrasts (their correlation through the shared reference group is ignored because it is not published): **3.8% (1.0% to 6.5%) per hour a week**. With 15 instead of 12 hours for the top category: 3.2% (0.6% to 5.8%) and 3.1% (0.9% to 5.4%).
- Assumptions of both conversions: log-linear individual risk; a county mean one hour higher acts like a uniform one-hour shift; commute car time adds one-for-one to total car time (driving-specific) or to total sitting times f (generic); the estimates apply to both sexes, to ages 35-64 and to deaths in the same five years; carpool passengers count as riding in a car.
- **Age concentration**: the exposure is averaged over all residents 16+, but car commuting is more common at 45-64 than at 16+ overall (prevalence ratio 1.185 in 2015-2019, the only age split available; equal travel times by age assumed). Benchmarks are reported both as above and multiplied by 1.185.
- **Minimum detectable effect** (80% power, two-sided 5%): (t_0.975,50 + t_0.80,50) x SE = 2.857 x state-clustered SE of the coefficient, on the log scale and converted to percent. The design is called able to detect an effect of a given size if the MDE is no larger than that effect.

## 6. T2: change-over-time model

- Outcome: log(mean rate 2015-2019) - log(mean rate 2006-2010). Primary: all-CVD at 35-64. Secondary: all-CVD at 65+ (falsification), CHD and stroke at 35-64.
- Regressors: change in car hours and change in transit hours (2015-2019 minus 2006-2010); changes in `share_age_18_34`, `share_age_35_64`, `share_age_65plus`, `share_female`, log `median_hh_income` (nominal; the constant and state effects absorb common inflation), `poverty_rate`, `share_bachelors_plus`, `share_less_than_hs`, `unemployment_rate`, `share_nh_black`, `share_hispanic`, `share_nh_asian`, `share_nh_aian`, log `pop_density`; baseline urban-rural class (`nchs_ur_2006`, six indicators); state fixed effects. Uninsured share is not available for 2006-2010 and is omitted. Baseline mortality is not a regressor.
- Weights: mean of `pop_35_64` (or `pop_65plus`) over the two periods (primary); unweighted beside it. State-clustered CR1 inference, t(50); Conley 200 km as alternative.
- **Primary test (T2)**: coefficient on the change in car hours, weighted, all-CVD 35-64.
- **Attenuation from sampling error**: sampling variance of each county's exposure change = (MOE_2006-10/1.645)^2 + (MOE_2015-19/1.645)^2 (the two samples do not overlap). Reliability = 1 - (weighted mean sampling variance) / (weighted variance of the exposure change), reported (i) raw and (ii) conditional on the other regressors (denominator = variance of the exposure change after partialling out all other regressors and fixed effects). The conditional reliability is the approximate multiplicative attenuation of the coefficient under classical error; coefficient / reliability is reported as an approximate corrected value when the reliability is positive. The published margins are conservative (and inflated for small counties in 2006-2010), so reliability is, if anything, understated.
- **Reliable-estimate restriction**: units with `pop_total` of at least 65,000 in both periods (the ACS threshold for 1-year estimates).
- MDE as in section 5.

## 7. T3: matched high- versus low-driving contrast (2015-2019)

- **Groups**: within each `nchs_ur_2013` class, counties in the top quartile of `car_hours_wk_per_adult16` are "high-driving" and counties in the bottom quartile are "low-driving" (quartiles computed among cross-sectional sample units of that class, unweighted). The middle half is not used.
- **Matching**: exact on urban-rural class and census region (4). Within these strata, optimal 1:1 matching without replacement (minimum total distance, linear assignment) on the Mahalanobis distance of: `share_age_35_64`, `share_age_65plus`, `share_female`, log `median_hh_income`, `poverty_rate`, `share_bachelors_plus`, `unemployment_rate`, `share_nh_black`, `share_hispanic`, `share_uninsured_18_64`, log `pop_density`. Caliper: pairs are allowed only if the two counties' logit propensity scores differ by at most 0.2 standard deviations of the logit propensity score (logistic regression of high versus low on the matching covariates, class and region indicators). Counties without an admissible partner are discarded and counted.
- **Balance**: standardised mean differences (difference in means / pooled SD of the two groups before matching) before and after, for the matching covariates and for covariates not matched on (`share_less_than_hs`, `share_nh_asian`, `share_nh_aian`, `share_no_vehicle_hh`, `workers_per_adult16`, PLACES smoking, obesity, diabetes, inactivity, latitude, longitude). Target: absolute SMD below 0.1 for every matching covariate.
- **Estimand and estimates**: mean within-pair difference (high minus low) in log all-CVD mortality at 35-64 (primary, T3) and at 65+ (falsification), unweighted over pairs. (i) Unadjusted pair difference. (ii) Regression-adjusted: pair difference regressed on pair differences in the matching covariates (intercept reported). If every matching covariate meets the balance target, (i) is the estimate to interpret; otherwise (ii).
- **Interval**: cluster-robust (CR1) by the state of the high-driving county, t reference with (clusters - 1) degrees of freedom; the ordinary paired-t interval is reported for comparison. The mean within-pair difference in car hours is reported so the contrast can be put on the per-hour scale (ratio of the two means, descriptive).
- **Sensitivity to unmeasured confounding**: E-value for the rate ratio exp(mean difference) and for the confidence limit nearer the null (VanderWeele and Ding); Rosenbaum bounds for the Wilcoxon signed-rank test on pair differences (Gamma from 1 to 3 in steps of 0.05; the largest Gamma at which the upper-bound two-sided p-value stays below 0.05). If the result is not significant at Gamma = 1 the bounds are reported as not applicable.

## 8. Sensitivity analyses (all M3, population-weighted, log all-CVD 35-64, 2015-2019, state-clustered, unless stated)

- S1: `drivealone_hours_wk_per_adult16` in place of car hours.
- S2: decomposition: `mean_tt_car_mid` (per 10 minutes one way) and `car_commuters_per_adult16` (per 10 percentage points) in place of car hours; the coefficient on mean car travel time is the sensitivity estimate.
- S3: `share_car_commuters_60plus` (per 10 percentage points) with `car_commuters_per_adult16`, in place of car hours.
- S4a: published car aggregate (`car_hours_wk_per_adult16_pub`) where published; S4b: published car and transit aggregates where both are published. Each compared with the primary measure on the same units.
- S5: excluding counties with `pop_total` under 20,000.
- S6: the 2010-2014 cross-section (2010-2014 exposure, covariates and mortality; uninsured band 18-64).
- S7: men and women separately (`mort_cvd_35_64_men`, `_women`).
- S8: five commute days a week instead of 4.5 (a rescaling of the coefficient by 4.5/5; verified numerically; not a separate test).
- S9: leaving out one census region at a time (four fits).
- S10: M3 + `workers_per_adult16`.
- S11: excluding the five New York City counties (36005, 36047, 36061, 36081, 36085), which hold the largest transit exposures.
- S12: car hours entered without the transit term.
- Ladder variants: M0, M1, M2, M4 weighted; M0-M4 unweighted; metropolitan counties only.

For each: estimate, interval, p, and flags for sign differing from the primary estimate, significance changing (crossing p = 0.05 either way) and ratio to the primary estimate where units are the same.

## 9. Multiplicity

- **Family A (confirmatory, 3 tests)**: the car coefficient for log all-CVD mortality at 35-64 in T1, T2 and T3. Benjamini-Hochberg q-values and Holm-adjusted p-values.
- **Family B (secondary outcomes, 7 tests)**: car coefficient in M3, weighted, for all-CVD 65+, CHD 35-64, CHD 65+, stroke 35-64, stroke 65+, all-CVD 35-64 men, all-CVD 35-64 women. Benjamini-Hochberg.
- **Family C (sensitivity, 26 tests)**: the driving-exposure coefficient on log all-CVD 35-64 in: M0, M1, M2, M4 weighted (4); M0-M4 unweighted (5); metropolitan only (1); S1, S2, S3 (3); S4a, S4b (2); S5 (1); S6 (1); S7 men, women (2); S9 (4); S10, S11, S12 (3). Benjamini-Hochberg. S8 is a rescaling and is not counted.
- Transit coefficients, the car = transit test, the 35-64 versus 65+ contrast, Conley intervals, the quintile model, non-metropolitan estimates and the T2 secondary outcomes are reported with unadjusted p-values and labelled as such.

## 10. What will count as what

Let b be the car coefficient for all-CVD mortality at 35-64.
- **Support** for the hypothesis in a given test: b > 0 with the 95% interval excluding zero under the primary inference (and, for T1 and T2, also under Conley 200 km). **Support specific to driving and working age** additionally requires, in T1: the 65+ coefficient smaller than the 35-64 coefficient with the interval of the difference excluding zero, and the weighted and unweighted estimates sharing the positive sign. **Consistent support** requires all three tests to have b > 0 and at least two with q < 0.05 in family A.
- **Positive but not specific** (reported as likely confounding by place, not as support): b > 0 and significant, but the 65+ coefficient is as large or larger, or the association disappears within metropolitan counties, or the transit coefficient is equally positive.
- **Null**: the 95% interval includes zero. A null is called *informative against the driving-specific estimate* if the upper confidence limit is below the DR003-based benchmark (4.1% per hour a week), and *uninformative about sitting-sized effects* if the MDE exceeds the f = 1 sitting benchmark (0.28%).
- **Evidence against**: b < 0 with the interval excluding zero under both inference methods. This will be reported as an inverse ecological association, not as a protective effect; the pre-specified candidates for explaining it are the employment component of the exposure (S2, S10) and urban form.
- Sign or significance that differs across weighting, inference method, S10, or the three tests will be reported as inconsistency, not resolved by choosing among them.

## 11. Outputs and software

Result files: `national_cross_section_models.csv`, `national_change_models.csv`, `national_matched_contrast.csv`, `national_matched_balance.csv`, `national_sensitivity.csv`, plot-ready tables, `national_bay_area_position.csv` (descriptive percentiles of the 15 Bay Area study counties), and `methods_results_national.md` generated from those files. Python 3.11.17; numpy 2.4.6, pandas 2.3.3, scipy 1.17.1, statsmodels 0.15.0. Seed 20261113 for permutations.
