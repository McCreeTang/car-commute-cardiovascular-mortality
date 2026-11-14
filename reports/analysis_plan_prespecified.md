# Pre-specified analysis plan: ecological models track

Written and saved BEFORE any outcome model was fitted (only row counts, column lists and covariate missingness had been inspected).
All models listed here are reported whatever their result. Nothing is added or dropped on the basis of significance.
Random seed for every stochastic step: 20261113.

## A. Trends (step 1)
- Source: pums_commuters.parquet, records with puma_mixed_outside = False (14 counties). Weights pwgtp; variance from the 80 replicate weights, var = (4/80) * sum_r (theta_r - theta_0)^2; negative replicate weights not clipped.
- Measures: mean one-way travel time among commuters (jwmnp; top-coded by Census); share of commuters at 45+, 60+, 90+ minutes; drive-alone share of workers (mode_cat = car_alone / worker_at_work); work-from-home share of workers.
- Groups: each of 14 counties, CORE9, EXT5 (adjacent counties without San Benito), ALL14; age bands 16+, 16-34, 35-44, 45-54, 55-64, 65+ (plus 16-24, 25-34, 35-64 for completeness).
- Changes: 2010->2019 (primary) and 2019->2024 (descriptive; commuters are differently selected after 2020). Annual ACS samples are treated as independent, so var(change) = var(year 1) + var(year 2); z-tests, two-sided.
- Heterogeneity tests (2010->2019): (i) Wald chi-square (4 df) that the change is equal across the five age bands 16-34, 35-44, 45-54, 55-64, 65+, with the full replicate covariance matrix of the five band estimates within each year; run for ALL14, CORE9, EXT5; (ii) z-test of (change in CORE9) - (change in EXT5), with the within-year replicate covariance of the two regional estimates. Both for all six measures; mean commute and 60+ share are the primary two.
- Zillow ZHVI (nominal dollars, smoothed mid-tier index): county 2010, 2019, 2024 annual means, absolute and percent change; region summaries are unweighted means of counties. No uncertainty is published for ZHVI.

## B. Tract cross-sectional models (step 2) -- primary model set
- Two cross-sections, never pooled: (1) ACS 2015-2019 with PLACES 2021 release (BRFSS 2019; 2010 tracts); (2) ACS 2020-2024 with PLACES 2025 release (BRFSS 2023; 2020 tracts).
- Sample: tracts with a PLACES estimate, at least 100 commuters (commuters_total >= 100; below that the ACS commute shares are too noisy), and no missing covariate.
- Outcomes (6; percent, crude adults 18+): chd_prev, stroke_prev, bphigh_prev, obesity_prev, lpa_prev, diabetes_prev.
- Exposures (2), entered JOINTLY in the same model: share_commute_60plus (share of commuters) and share_drive_alone (share of workers). Coefficients reported per 10-percentage-point difference in the exposure (coefficient on the 0-1 share x 0.1), in percentage points of prevalence.
- Covariates: share_age_18_34, share_age_35_64, share_age_65plus (under 18 is the reference); log(median_hh_income) plus an indicator for the top-coded value; poverty_rate; share_bachelors_plus; share_nh_black, share_nh_asian, share_hispanic (reference: non-Hispanic White and all other); share_no_vehicle_hh; county fixed effects (dummies).
- Spatial weights: queen contiguity from TIGER/Line tract polygons (TIGER2019 for the 2010-boundary cross-section, TIGER2024 for the 2020-boundary cross-section), built on the estimation-sample tracts only, row-standardised. Tracts with no queen neighbour in the sample are attached to their single nearest sample tract by centroid distance (symmetrised). TIGER/Line polygons extend over water, so tracts facing each other across the Bay can be contiguous; accepted and stated.
- Estimators (3): (1) OLS with HC1 standard errors, Moran's I of residuals (analytic normal approximation, and 999 permutations), LM-lag, LM-error and their robust forms; (2) spatial error model, maximum likelihood (spreg.ML_Error); (3) spatial lag model, maximum likelihood (spreg.ML_Lag). For the lag model the row in tract_models.csv is the AVERAGE TOTAL IMPACT beta/(1-rho) (95% CI from 2,000 draws of the asymptotic normal distribution of (beta, rho)); the raw beta and the average direct impact are stored alongside.
- Which model the diagnostics favour (decision rule fixed now): if neither LM-error nor LM-lag is significant at 0.05, OLS; if only one, that one; if both, the one with the larger robust LM statistic. AIC of the two ML models is reported as a cross-check. One 'favoured' flag per outcome x cross-section.
- 95% CIs: estimate +/- 1.96 SE. Multiple testing: Benjamini-Hochberg q-values within each family of 12 tests (6 outcomes x 2 exposures) per cross-section x estimator. 'FDR-significant' means q < 0.05.
- 72 rows in tract_models.csv (6 x 2 x 2 x 3).

## C. County-year panel (step 3)
- Panel: 14 counties x 2010-2019 (140 county-years). Commute measures: PUMS county-year estimates (all commuters 16+; age-matched 35-64 band used where stated). Home value: Zillow ZHVI annual mean, nominal; log-transformed; lag 1 year is primary (2009 value taken from zillow_county_annual.parquet of this project), lags 0 and 2 reported as secondary.
- Model H (housing -> commute): y_ct = a_c + d_t + beta * log(ZHVI_c,t-1) + e_ct, y = mean commute minutes (16+) and 60+ minute share (16+). Unweighted. Year effects absorb common inflation and region-wide shocks.
- Inference: cluster by county (G = 14). Reported: CR1 cluster-robust SE with t(13) interval; wild cluster bootstrap-t with the null imposed (WCR), Rademacher weights, ALL 2^14 = 16,384 sign vectors enumerated (no simulation error); 95% CI by test inversion. The WCR interval is the primary interval.
- Model M (commute -> mortality): log(mortality rate_ct, band b) = a_c + d_t + gamma * commute_ct + e_ct, for b in {35-64, 65+}; causes: all cardiovascular disease (mort_cvd, primary), coronary heart disease, stroke (secondary). Commute measure: mean commute minutes (per 5 minutes) and 60+ share (per 10 points); for 35-64 mortality the 35-64 commuter band is used (age-matched), for 65+ mortality the all-commuter 16+ measure (65+ decedents are mostly not commuters; stated). Contemporaneous. Same inference.
- Pathway decomposition (product of coefficients), for mort_cvd in each age band and each of the two commute measures: a = coefficient of log(ZHVI_t-1) on commute; b = coefficient of commute on log mortality conditional on log(ZHVI_t-1); indirect = a*b; direct = coefficient of log(ZHVI_t-1) in the outcome model with the commute measure; total = coefficient without it. Intervals: county-cluster pairs bootstrap (resampling 14 counties with replacement, 4,999 draws, percentile), acknowledged to be unreliable with 14 clusters. Labelled descriptive; NOT causal mediation.
- Minimum detectable effect for each panel coefficient: MDE = (t_0.975,13 + t_0.80,13) x CR1 SE (80% power, two-sided 5%).
- Sampling error in the PUMS county-year commute measures is ignored in the panel models (it attenuates gamma and b towards zero when commute is the regressor); stated.

## D. Sensitivity analyses (step 4) -- all with the same covariates unless stated; estimators: OLS(HC1), ML error, ML lag (total impact) unless stated
- S1 core9: nine core counties only.
- S2 no-transit-top-decile: exclude tracts in the top decile of share_transit within the cross-section sample.
- S3 alternative exposure: replace share_commute_60plus by (a) mean_commute_min (per 5 minutes), (b) share_commute_45plus, (c) share_commute_90plus (per 10 points); share_drive_alone stays in the model.
- S4 smoking: add csmoking_prev (itself a PLACES model-based estimate) as a covariate.
- S5 weighting: WLS weighted by adult population (pop_total x (1 - share_age_under18)) vs unweighted OLS; HC1; no spatial estimator (weighted spatial ML is not standard).
- S6 first difference: tracts with boundary_stable_99 present in both samples; (outcome 2023 - outcome 2019) on differences of both exposures and of all covariates (log income differenced; top-code indicators for each period), county effects (county-specific change); OLS(HC1) and ML error with the 2020-vintage queen weights. Caveat stated: the two PLACES releases use different BRFSS years, different population bases and methodology, so differences include method change; nominal income change.
- S7 county mortality in place of prevalence: 15 counties, ACS 5-year county exposures; outcome = mean 2015-2019 model-smoothed cardiovascular mortality (all CVD; ages 35-64 and 65+) for the 2015-2019 cross-section, and pooled 3-year heart-disease mortality 35+ (2022 and 2023 midpoints averaged) for the 2020-2024 cross-section; OLS of log rate on each exposure singly and with log median household income (n = 15, no further adjustment possible), plus Spearman correlation. The panel models in C are the within-county counterpart.
- S8 single-exposure models: each exposure entered without the other (OLS, error, lag).
- sensitivity_models.csv has one row per specification x outcome x exposure x cross-section x estimator, with flags for sign change, change in nominal significance (p < 0.05) and ratio to the primary estimate.

## E. Interpretation rules
- Associations only. PLACES tract outcomes are model-based and built from tract demography; a null or wrong-signed coefficient is reported as such.
- Primary period 2010-2019; 2021-2024 descriptive.
