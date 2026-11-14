# Methods and results: ecological models track

Cardiovascular risk and lengthening car commutes in the San Francisco Bay Area: descriptive trends, tract-level cross-sectional association models, a county-year housing-commute-mortality panel, and sensitivity analyses.

**Reading rule.** Everything here is observational and ecological. Coefficients are associations between area-level quantities; none is a causal effect, and none describes individuals. The model set was fixed in `analysis_plan_prespecified.md` before any outcome model was fitted, and every model in it is reported. Every number below is formatted by `05_write_report.py` from the saved result files.

## 1. Summary of results

1. **Commutes lengthened substantially from 2010 to 2019.** Among commuters aged 16+ in the 14 counties with microdata, mean one-way travel time changed by +5.71 (95% CI +5.32 to +6.10) minutes (from 26.96 to 32.68) and the share with commutes of 60+ minutes by +6.41 (95% CI +5.89 to +6.92) percentage points (from 9.51% to 15.92%). The rise was larger in the nine core counties than in the adjacent counties and differed by age band for the 60+ minute share (largest in the 35-44 and 45-54 bands, smallest at 65+). Nominal Zillow home values roughly doubled over the same years.
2. **Tract-level models do not show the hypothesised positive association.** With the estimator favoured by the spatial diagnostics, the 60+ minute commute share was associated with LOWER modelled prevalence for 4 of 6 outcomes in the 2015-2019 cross-section after false-discovery-rate control (0 positive), and with none of 6 in the 2020-2024 cross-section (0 FDR-significant). Drive-alone share: 2 of 6 FDR-significant in 2015-2019 (2 negative, 0 positive) and 1 of 6 in 2020-2024 (1 negative, 0 positive). These are wrong-signed or null relative to the hypothesis. Because PLACES prevalences are built from tract demography, the covariates alone reproduce 81-97% of their variance, and the tract analysis has little ability to detect a commute effect in either direction.
3. **Housing-to-commute panel: positive but imprecise.** Within counties and net of year effects, a 10% higher lagged nominal home value went with +0.92 minutes of mean commute (wild-cluster 95% CI -0.05 to +1.79; p 0.056) and +0.66 percentage points of 60+ minute share (95% CI -1.12 to +2.34; p 0.373). With 14 clusters the intervals include zero.
4. **Commute-to-mortality panel: no positive association; the design cannot detect effects of plausible size.** Per 10-point higher 60+ minute share, all-cardiovascular mortality differed by -6.2% at ages 35-64 (95% CI -13.2% to +0.9%) and +1.1% at ages 65+ (95% CI -2.5% to +4.2%). The minimum detectable effect at ages 35-64 is 9.2% per 10 points, against about 3.4% implied by the only driving-specific cohort estimate under generous assumptions. The product-of-coefficients indirect paths are all indistinguishable from zero.
5. **Sensitivity analyses do not rescue the hypothesis.** Of 276 sensitivity estimates for a commute-duration exposure, 122 are nominally significant and negative and 5 nominally significant and positive (all for obesity; number surviving FDR control: 1, under OLS only). Signs and significance of the drive-alone coefficients are unstable across specifications (section 6).

## 2. Data, units and samples

- Study area: 15 California counties (9 core Bay Area, 6 adjacent). San Benito has no person-level (PUMS) data, so PUMS-based trends and the panel use 14 counties; tract models and the county mortality cross-section use all 15.
- Trends: ACS 1-year PUMS persons 16+, records with `puma_mixed_outside = False`; person weight `pwgtp`, 80 replicate weights. No 2020 file exists. 2010-2019 is the primary period; 2021-2024 is described separately because the work-from-home share rose sharply and commuters became a differently selected group.
- Tract models: ACS 5-year tract estimates paired with CDC PLACES crude model-based prevalences for adults 18+ (not age-specific). Two cross-sections, never pooled.
- Panel: county-year, 2010-2019, PUMS commute estimates, Zillow Home Value Index (nominal dollars), CDC model-smoothed mortality rates for ages 35-64 and 65+.
- All dollar values are nominal. ACS median household income is top-coded (handled with an indicator).

**Table 2.1 Tract estimation samples** (tracts with a PLACES estimate, at least 100 commuters, no missing covariate).

| Cross-section | Tracts in file | With PLACES | In model | Excluded | Population covered | Counties | Core-9 tracts | Income top-coded | Mean queen neighbours | Islands attached | Graph components | Correlation of the two exposures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ACS 2015-2019 / PLACES 2021 release (BRFSS 2019) | 2251 | 2240 | 2230 | 21 | 99.83% | 15 | 1571 | 19 | 6.23 | 0 | 1 | -0.103 |
| ACS 2020-2024 / PLACES 2025 release (BRFSS 2023) | 2566 | 2552 | 2535 | 31 | 99.70% | 15 | 1744 | 136 | 6.25 | 0 | 1 | +0.051 |

**Table 2.2 Tract-level means (SD), unweighted, percent.**

| Cross-section | 60+ min share | Drive-alone share | Coronary heart disease | Stroke | High blood pressure | Obesity | Physical inactivity | Diabetes |
|---|---|---|---|---|---|---|---|---|
| ACS 2015-2019 / PLACES 2021 release (BRFSS 2019) | 14.4 (7.9) | 68.1 (16.2) | 4.6 (1.3) | 2.7 (0.8) | 26.1 (4.4) | 24.6 (5.6) | 21.6 (6.5) | 9.2 (2.4) |
| ACS 2020-2024 / PLACES 2025 release (BRFSS 2023) | 11.9 (8.2) | 59.5 (16.4) | 5.2 (1.5) | 2.9 (0.8) | 29.2 (4.6) | 26.1 (6.2) | 22.5 (6.8) | 10.8 (2.7) |

## 3. Housing and commute trends (step 1)

### 3.1 Methods

Estimates are weighted ratios (for example, weighted minutes over weighted commuters). Standard errors use the 80 replicate weights: variance = (4/80) x sum of squared deviations of the replicate estimates from the full-sample estimate; negative replicate weights are kept as published. Annual ACS samples are treated as independent, so the variance of a change is the sum of the two year-specific variances; changes are tested with two-sided z-tests. Age-band heterogeneity of the change is tested with a 4-df Wald chi-square on the five bands 16-34, 35-44, 45-54, 55-64, 65+ using the full within-year replicate covariance matrix. The core-versus-adjacent contrast is (change in the nine core counties) minus (change in the five adjacent counties with microdata), with the within-year replicate covariance. The script reproduces the delivered county x year x age aggregates (maximum absolute difference 0.0e+00 in estimates and 1.8e-15 in standard errors over 3,672 of 3,672 cells compared). Travel time is top-coded in PUMS (observed maximum 141-146 minutes by year), which slightly understates means. Zillow values are annual means of a smoothed monthly index, in nominal dollars, with no published uncertainty; regional values are unweighted means of counties.

### 3.2 Regional changes

**Table 3.1 Change 2010 to 2019 (primary period), commuters/workers aged 16+. Level (SE); change (SE); p.**

| Measure | Region | 2010 | 2019 | Change |
|---|---|---|---|---|
| Mean one-way commute (min) | All 14 counties | 26.96 (0.12) | 32.68 (0.16) | +5.71 (0.20); p <0.001 |
| Mean one-way commute (min) | Core 9 | 27.20 (0.14) | 33.31 (0.18) | +6.11 (0.23); p <0.001 |
| Mean one-way commute (min) | Adjacent 5 | 26.33 (0.25) | 31.04 (0.36) | +4.71 (0.43); p <0.001 |
| Commuters at 45+ min (%) | All 14 counties | 17.74 (0.22) | 26.17 (0.26) | +8.43 (0.34); p <0.001 |
| Commuters at 45+ min (%) | Core 9 | 18.34 (0.27) | 27.96 (0.33) | +9.62 (0.42); p <0.001 |
| Commuters at 45+ min (%) | Adjacent 5 | 16.13 (0.41) | 21.56 (0.45) | +5.44 (0.61); p <0.001 |
| Commuters at 60+ min (%) | All 14 counties | 9.51 (0.17) | 15.92 (0.20) | +6.41 (0.26); p <0.001 |
| Commuters at 60+ min (%) | Core 9 | 9.48 (0.22) | 16.93 (0.22) | +7.45 (0.31); p <0.001 |
| Commuters at 60+ min (%) | Adjacent 5 | 9.61 (0.33) | 13.33 (0.40) | +3.72 (0.52); p <0.001 |
| Commuters at 90+ min (%) | All 14 counties | 2.67 (0.08) | 5.67 (0.14) | +3.00 (0.17); p <0.001 |
| Commuters at 90+ min (%) | Core 9 | 2.22 (0.10) | 5.24 (0.16) | +3.02 (0.19); p <0.001 |
| Commuters at 90+ min (%) | Adjacent 5 | 3.89 (0.23) | 6.77 (0.32) | +2.88 (0.39); p <0.001 |
| Workers driving alone (%) | All 14 counties | 69.87 (0.26) | 67.28 (0.24) | -2.59 (0.35); p <0.001 |
| Workers driving alone (%) | Core 9 | 67.52 (0.33) | 63.51 (0.29) | -4.02 (0.44); p <0.001 |
| Workers driving alone (%) | Adjacent 5 | 76.20 (0.53) | 77.06 (0.46) | +0.85 (0.70); p 0.224 |
| Workers working from home (%) | All 14 counties | 5.63 (0.14) | 6.28 (0.14) | +0.65 (0.20); p 0.001 |
| Workers working from home (%) | Core 9 | 5.80 (0.18) | 6.49 (0.17) | +0.69 (0.24); p 0.004 |
| Workers working from home (%) | Adjacent 5 | 5.18 (0.23) | 5.73 (0.25) | +0.55 (0.34); p 0.111 |

**Table 3.2 Change 2019 to 2024 (descriptive: post-2020 commuters are a differently selected group). Level (SE); change (SE); p.**

| Measure | Region | 2019 | 2024 | Change |
|---|---|---|---|---|
| Mean one-way commute (min) | All 14 counties | 32.68 (0.16) | 30.43 (0.14) | -2.25 (0.21); p <0.001 |
| Mean one-way commute (min) | Core 9 | 33.31 (0.18) | 30.62 (0.16) | -2.69 (0.24); p <0.001 |
| Mean one-way commute (min) | Adjacent 5 | 31.04 (0.36) | 29.98 (0.32) | -1.05 (0.48); p 0.028 |
| Commuters at 45+ min (%) | All 14 counties | 26.17 (0.26) | 22.03 (0.22) | -4.15 (0.35); p <0.001 |
| Commuters at 45+ min (%) | Core 9 | 27.96 (0.33) | 22.99 (0.27) | -4.97 (0.42); p <0.001 |
| Commuters at 45+ min (%) | Adjacent 5 | 21.56 (0.45) | 19.79 (0.46) | -1.77 (0.65); p 0.006 |
| Commuters at 60+ min (%) | All 14 counties | 15.92 (0.20) | 13.08 (0.18) | -2.84 (0.27); p <0.001 |
| Commuters at 60+ min (%) | Core 9 | 16.93 (0.22) | 13.34 (0.22) | -3.59 (0.31); p <0.001 |
| Commuters at 60+ min (%) | Adjacent 5 | 13.33 (0.40) | 12.46 (0.39) | -0.87 (0.56); p 0.123 |
| Commuters at 90+ min (%) | All 14 counties | 5.67 (0.14) | 4.36 (0.13) | -1.30 (0.19); p <0.001 |
| Commuters at 90+ min (%) | Core 9 | 5.24 (0.16) | 3.67 (0.14) | -1.57 (0.21); p <0.001 |
| Commuters at 90+ min (%) | Adjacent 5 | 6.77 (0.32) | 5.96 (0.29) | -0.81 (0.43); p 0.059 |
| Workers driving alone (%) | All 14 counties | 67.28 (0.24) | 62.61 (0.27) | -4.67 (0.36); p <0.001 |
| Workers driving alone (%) | Core 9 | 63.51 (0.29) | 58.91 (0.31) | -4.60 (0.42); p <0.001 |
| Workers driving alone (%) | Adjacent 5 | 77.06 (0.46) | 71.69 (0.49) | -5.36 (0.67); p <0.001 |
| Workers working from home (%) | All 14 counties | 6.28 (0.14) | 15.58 (0.20) | +9.31 (0.25); p <0.001 |
| Workers working from home (%) | Core 9 | 6.49 (0.17) | 16.99 (0.28) | +10.50 (0.32); p <0.001 |
| Workers working from home (%) | Adjacent 5 | 5.73 (0.25) | 12.14 (0.38) | +6.41 (0.46); p <0.001 |

### 3.3 By age band, all 14 counties

**Table 3.3 Change 2010 to 2019 by age band (change with SE), and 2019 to 2024 change for two measures.**

| Age | Mean min 2010 | 2019 | Change | 60+ % 2010 | 2019 | Change (pts) | 90+ % 2010 | 2019 | Change (pts) | Drive alone % 2010 | 2019 | Change (pts) | Mean min change 2019-24 | 60+ change 2019-24 (pts) | Commuter records 2010 | 2019 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 16-34 | 25.61 | 31.24 | +5.63 (0.30) | 8.59 | 14.40 | +5.81 (0.41) | 2.22 | 4.96 | +2.73 (0.28) | 66.94 | 64.10 | -2.83 (0.63) | -2.30 (0.33) | -2.98 (0.42) | 12878 | 16150 |
| 35-44 | 28.31 | 34.66 | +6.35 (0.40) | 10.82 | 18.46 | +7.64 (0.58) | 2.85 | 6.61 | +3.76 (0.37) | 71.29 | 68.01 | -3.28 (0.80) | -2.65 (0.45) | -3.63 (0.64) | 9569 | 10918 |
| 45-54 | 27.73 | 33.85 | +6.13 (0.43) | 9.55 | 16.91 | +7.36 (0.57) | 2.98 | 6.12 | +3.14 (0.37) | 72.49 | 70.43 | -2.06 (0.73) | -2.32 (0.51) | -2.31 (0.68) | 10215 | 10478 |
| 55-64 | 27.09 | 32.54 | +5.45 (0.50) | 9.68 | 15.66 | +5.98 (0.64) | 2.88 | 5.73 | +2.85 (0.37) | 70.77 | 69.71 | -1.06 (0.85) | -1.83 (0.56) | -2.57 (0.69) | 6916 | 8673 |
| 65+ | 25.69 | 30.00 | +4.32 (0.78) | 8.83 | 12.58 | +3.75 (1.03) | 2.96 | 4.64 | +1.68 (0.64) | 67.41 | 66.05 | -1.36 (1.47) | -1.46 (0.78) | -1.69 (0.99) | 1814 | 3189 |

### 3.4 Heterogeneity tests, 2010 to 2019

| Measure | Test | Statistic | p |
|---|---|---|---|
| Mean one-way commute (min) | Age bands equal, ALL14 | chi-square(4) = 6.27 | 0.180 |
| Mean one-way commute (min) | Age bands equal, CORE9 | chi-square(4) = 10.72 | 0.030 |
| Mean one-way commute (min) | Age bands equal, EXT5 | chi-square(4) = 3.15 | 0.533 |
| Mean one-way commute (min) | Core 9 minus adjacent 5 (all ages) | difference +1.41 (SE 0.50); z = 2.82 | 0.005 |
| Mean one-way commute (min) | All 14 county changes equal (added, not pre-specified) | chi-square(13) = 141.58 | <0.001 |
| Commuters at 45+ min (%) | Age bands equal, ALL14 | chi-square(4) = 12.30 | 0.015 |
| Commuters at 45+ min (%) | Age bands equal, CORE9 | chi-square(4) = 10.50 | 0.033 |
| Commuters at 45+ min (%) | Age bands equal, EXT5 | chi-square(4) = 8.68 | 0.070 |
| Commuters at 45+ min (%) | Core 9 minus adjacent 5 (all ages) | difference +4.19 (SE 0.76); z = 5.54 | <0.001 |
| Commuters at 45+ min (%) | All 14 county changes equal (added, not pre-specified) | chi-square(13) = 188.17 | <0.001 |
| Commuters at 60+ min (%) | Age bands equal, ALL14 | chi-square(4) = 16.02 | 0.003 |
| Commuters at 60+ min (%) | Age bands equal, CORE9 | chi-square(4) = 18.36 | 0.001 |
| Commuters at 60+ min (%) | Age bands equal, EXT5 | chi-square(4) = 7.14 | 0.129 |
| Commuters at 60+ min (%) | Core 9 minus adjacent 5 (all ages) | difference +3.73 (SE 0.61); z = 6.13 | <0.001 |
| Commuters at 60+ min (%) | All 14 county changes equal (added, not pre-specified) | chi-square(13) = 258.46 | <0.001 |
| Commuters at 90+ min (%) | Age bands equal, ALL14 | chi-square(4) = 9.02 | 0.060 |
| Commuters at 90+ min (%) | Age bands equal, CORE9 | chi-square(4) = 14.13 | 0.007 |
| Commuters at 90+ min (%) | Age bands equal, EXT5 | chi-square(4) = 2.59 | 0.629 |
| Commuters at 90+ min (%) | Core 9 minus adjacent 5 (all ages) | difference +0.15 (SE 0.45); z = 0.32 | 0.748 |
| Commuters at 90+ min (%) | All 14 county changes equal (added, not pre-specified) | chi-square(13) = 120.46 | <0.001 |
| Workers driving alone (%) | Age bands equal, ALL14 | chi-square(4) = 4.60 | 0.331 |
| Workers driving alone (%) | Age bands equal, CORE9 | chi-square(4) = 7.12 | 0.130 |
| Workers driving alone (%) | Age bands equal, EXT5 | chi-square(4) = 1.74 | 0.784 |
| Workers driving alone (%) | Core 9 minus adjacent 5 (all ages) | difference -4.87 (SE 0.86); z = -5.66 | <0.001 |
| Workers driving alone (%) | All 14 county changes equal (added, not pre-specified) | chi-square(13) = 53.06 | <0.001 |
| Workers working from home (%) | Age bands equal, ALL14 | chi-square(4) = 2.02 | 0.732 |
| Workers working from home (%) | Age bands equal, CORE9 | chi-square(4) = 2.87 | 0.580 |
| Workers working from home (%) | Age bands equal, EXT5 | chi-square(4) = 2.40 | 0.662 |
| Workers working from home (%) | Core 9 minus adjacent 5 (all ages) | difference +0.15 (SE 0.42); z = 0.35 | 0.725 |
| Workers working from home (%) | All 14 county changes equal (added, not pre-specified) | chi-square(13) = 41.22 | <0.001 |

**Table 3.4 Core 9 minus adjacent 5: difference in the 2010-2019 change of the 60+ minute share (percentage points), by age band.**

| Age band | Difference (SE) | z | p | Component changes (proportions) |
|---|---|---|---|---|
| 16+ | +3.73 (0.61) | 6.13 | <0.001 | core9 change 0.0745; adjacent change 0.0372 |
| 16-34 | +4.60 (0.97) | 4.75 | <0.001 | core9 change 0.0715; adjacent change 0.0254 |
| 35-44 | +5.35 (1.32) | 4.04 | <0.001 | core9 change 0.0909; adjacent change 0.0374 |
| 45-54 | +2.61 (1.18) | 2.21 | 0.027 | core9 change 0.0809; adjacent change 0.0548 |
| 55-64 | +1.29 (1.42) | 0.91 | 0.365 | core9 change 0.0637; adjacent change 0.0508 |
| 65+ | +0.68 (2.32) | 0.29 | 0.770 | core9 change 0.0396; adjacent change 0.0329 |

### 3.5 By county

**Table 3.5 County home values (Zillow index, NOMINAL dollars) and commute changes (change with replicate-weight SE).**

| County | Group | ZHVI 2010 | ZHVI 2019 | Change 2010-19 | ZHVI 2024 | Change 2019-24 | Mean commute min 2010 -> 2019; change | 60+ % 2010 -> 2019; change (pts) | Drive-alone % 2010 -> 2019; change (pts) | Mean min change 2019-24 | 60+ change 2019-24 (pts) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Alameda | core | 435,942 | 836,870 | +92.0% | 1,103,864 | +31.9% | 27.2 -> 35.8; +8.68 (0.44) | 8.8 -> 20.6; +11.77 (0.59) | 66.9 -> 60.5; -6.39 (0.97) | -2.93 (0.49) | -4.35 (0.74) |
| Contra Costa | core | 315,631 | 621,640 | +97.0% | 811,537 | +30.5% | 32.5 -> 39.7; +7.13 (0.86) | 17.5 -> 27.5; +10.00 (1.15) | 68.9 -> 67.8; -1.11 (1.23) | -1.57 (0.95) | -3.27 (1.37) |
| Marin | core | 657,194 | 1,104,258 | +68.0% | 1,448,749 | +31.2% | 28.1 -> 33.9; +5.86 (1.43) | 10.5 -> 21.9; +11.35 (2.21) | 66.5 -> 57.8; -8.65 (2.68) | -4.96 (1.51) | -9.19 (2.11) |
| Merced | adjacent | 126,025 | 285,716 | +126.7% | 419,131 | +46.7% | 24.1 -> 31.6; +7.53 (1.92) | 11.3 -> 18.0; +6.71 (2.54) | 79.9 -> 78.4; -1.47 (3.04) | +0.85 (2.12) | +0.45 (2.77) |
| Napa | core | 405,786 | 707,447 | +74.3% | 913,807 | +29.2% | 24.4 -> 27.4; +2.98 (1.77) | 10.7 -> 11.5; +0.81 (2.04) | 78.6 -> 75.8; -2.84 (2.74) | -0.52 (1.57) | -0.95 (2.06) |
| Sacramento | adjacent | 202,014 | 386,893 | +91.5% | 537,017 | +38.8% | 25.9 -> 28.2; +2.32 (0.52) | 7.3 -> 8.0; +0.73 (0.65) | 74.8 -> 75.9; +1.08 (0.97) | -0.38 (0.55) | -0.22 (0.71) |
| San Benito | adjacent | 327,950 | 605,036 | +84.5% | 773,785 | +27.9% | no microdata | no microdata | no microdata | no microdata | no microdata |
| San Francisco | core | 663,667 | 1,287,750 | +94.0% | 1,248,045 | -3.1% | 29.9 -> 35.4; +5.46 (0.65) | 10.0 -> 16.3; +6.31 (0.92) | 35.2 -> 29.4; -5.77 (1.28) | -3.11 (0.70) | -2.61 (0.98) |
| San Joaquin | adjacent | 180,165 | 390,354 | +116.7% | 546,363 | +40.0% | 28.7 -> 36.5; +7.79 (1.23) | 14.4 -> 22.4; +8.04 (1.43) | 76.8 -> 78.3; +1.49 (1.59) | -2.28 (1.25) | -2.90 (1.40) |
| San Mateo | core | 630,697 | 1,290,111 | +104.6% | 1,505,773 | +16.7% | 24.4 -> 29.8; +5.36 (0.50) | 5.6 -> 12.1; +6.55 (0.71) | 70.5 -> 66.7; -3.80 (1.46) | -2.65 (0.61) | -4.00 (0.87) |
| Santa Clara | core | 516,463 | 1,127,600 | +118.3% | 1,556,017 | +38.0% | 24.2 -> 30.1; +5.86 (0.38) | 5.7 -> 11.1; +5.38 (0.50) | 78.2 -> 74.3; -3.92 (0.88) | -2.93 (0.42) | -3.35 (0.54) |
| Santa Cruz | adjacent | 476,410 | 791,928 | +66.2% | 1,103,954 | +39.4% | 25.4 -> 30.0; +4.69 (1.31) | 8.5 -> 13.8; +5.29 (1.50) | 72.9 -> 69.2; -3.71 (2.73) | -2.94 (1.23) | -3.90 (1.46) |
| Solano | core | 219,989 | 451,860 | +105.4% | 592,200 | +31.1% | 28.8 -> 34.4; +5.60 (1.16) | 13.2 -> 21.0; +7.72 (1.69) | 76.3 -> 76.6; +0.33 (1.98) | -4.12 (1.18) | -5.38 (1.74) |
| Sonoma | core | 386,011 | 656,248 | +70.0% | 802,291 | +22.3% | 25.6 -> 26.1; +0.49 (0.89) | 10.2 -> 10.0; -0.27 (1.20) | 76.8 -> 75.1; -1.74 (1.80) | -0.79 (0.80) | -0.92 (1.00) |
| Stanislaus | adjacent | 150,609 | 320,691 | +112.9% | 460,898 | +43.7% | 26.2 -> 32.5; +6.35 (1.51) | 10.0 -> 14.7; +4.71 (1.63) | 79.8 -> 83.1; +3.27 (1.75) | -2.21 (1.56) | -0.61 (1.64) |
| CORE9 (unweighted county mean) |  | 470,153 | 898,198 | +91.5% | 1,109,143 | +25.3% |  |  |  |  |  |
| EXT6 (unweighted county mean) |  | 243,862 | 463,436 | +99.8% | 640,191 | +39.4% |  |  |  |  |  |
| EXT5 (unweighted county mean) |  | 227,045 | 435,116 | +102.8% | 613,473 | +41.7% |  |  |  |  |  |
| ALL15 (unweighted county mean) |  | 379,637 | 724,293 | +94.8% | 921,562 | +30.9% |  |  |  |  |  |
| ALL14 (unweighted county mean) |  | 383,329 | 732,812 | +95.5% | 932,118 | +31.2% |  |  |  |  |  |

County changes in mean commute, 2010-2019, range from +0.49 minutes (Sonoma) to +8.68 (Alameda); 12 of 14 county increases are individually significant at 0.05 (unadjusted). For the 60+ minute share the range is -0.27 (Sonoma) to +11.77 points (Alameda). The full table (every county x age band x measure x period, plus 2019-2021 and 2010-2024 rows) is in `trends_table.csv`; levels for 2010, 2019, 2021 and 2024 are in `trends_levels.csv`.

## 4. Tract-level association models (step 2)

### 4.1 Specification (fixed in advance)

For each cross-section c and outcome y (PLACES crude prevalence, percent):

`y_i = a_county(i) + b1 * share_commute_60plus_i + b2 * share_drive_alone_i + g' * X_i + e_i`

- Both exposures are entered jointly. `share_commute_60plus` is the share of commuters with travel time of 60+ minutes; `share_drive_alone` is the share of all workers who drove alone. Coefficients are reported per 10-percentage-point difference in the exposure, in percentage points of prevalence.
- X: shares aged 18-34, 35-64, 65+ (under 18 is the reference); log median household income and an indicator for the top-coded value; poverty rate; share with a bachelor's degree or more; shares non-Hispanic Black, non-Hispanic Asian, Hispanic (reference: non-Hispanic White and all other); share of households with no vehicle; county fixed effects.
- Spatial weights: queen contiguity from TIGER/Line tract polygons (TIGER2019 for 2010-boundary tracts, TIGER2024 for 2020-boundary tracts), built on the estimation sample, row-standardised; tracts without a neighbour are joined to the nearest sample tract. TIGER/Line polygons extend over water, so tracts on opposite shores of the Bay can be neighbours.
- Estimators: (1) OLS with HC1 standard errors, with Moran's I of the residuals and Lagrange-multiplier tests; (2) spatial error model by maximum likelihood, `y = Xb + u, u = lambda*W*u + e`; (3) spatial lag model by maximum likelihood, `y = rho*W*y + Xb + e`. For the lag model the reported quantity is the average total impact `b/(1-rho)` with a 95% interval from 2,000 draws of the asymptotic distribution of (b, rho); its p-value is the z-test of b. Raw b and the average direct impact are in `tract_models.csv`.
- Favoured model (rule fixed in advance): OLS if neither LM test is significant at 0.05; the single significant alternative if only one is; otherwise the alternative with the larger robust LM statistic. AIC is a cross-check.
- Multiplicity: Benjamini-Hochberg q-values within each family of 12 tests (6 outcomes x 2 exposures) per cross-section and estimator.

### 4.2 Diagnostics

**Table 4.1 Model diagnostics.** LM = Lagrange multiplier statistic (1 df) / robust form. Residual Moran's I after the spatial models uses spatially filtered residuals (error model) and ordinary residuals (lag model).

| ACS period | Outcome | n | OLS R2 | R2 covariates only | Partial R2 of the 2 exposures | Moran's I, OLS residuals | LM error / robust | LM lag / robust | lambda (SE) | rho (SE) | AIC OLS / error / lag | Residual Moran's I error / lag | Favoured (LM rule) | Lowest AIC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2015-2019 | Coronary heart disease | 2230 | 0.832 | 0.830 | 0.0149 | 0.152 (z 13.3; perm. p 0.001) | 151.0 / 48.1 | 146.0 / 43.2 | 0.362 (0.030) | 0.206 (0.018) | 3725 / 3596 / 3593 | -0.009 / +0.056 | error | lag |
| 2015-2019 | Stroke | 2230 | 0.843 | 0.841 | 0.0139 | 0.149 (z 13.1; perm. p 0.001) | 146.2 / 48.0 | 142.1 / 43.9 | 0.373 (0.030) | 0.201 (0.017) | 1167 / 1036 / 1037 | -0.011 / +0.056 | error | error |
| 2015-2019 | High blood pressure | 2230 | 0.848 | 0.846 | 0.0166 | 0.168 (z 14.6; perm. p 0.001) | 184.5 / 43.6 | 245.8 / 104.9 | 0.451 (0.028) | 0.255 (0.016) | 8758 / 8576 / 8529 | -0.014 / +0.054 | lag | lag |
| 2015-2019 | Obesity | 2230 | 0.966 | 0.966 | 0.0017 | 0.189 (z 16.4; perm. p 0.001) | 235.2 / 144.6 | 123.8 / 33.1 | 0.465 (0.027) | 0.149 (0.013) | 6526 / 6315 / 6404 | -0.014 / +0.131 | error | error |
| 2015-2019 | Physical inactivity | 2230 | 0.961 | 0.960 | 0.0337 | 0.216 (z 18.6; perm. p 0.001) | 306.5 / 216.0 | 123.0 / 32.6 | 0.517 (0.026) | 0.121 (0.011) | 7466 / 7188 / 7351 | -0.022 / +0.145 | error | error |
| 2015-2019 | Diabetes | 2230 | 0.866 | 0.863 | 0.0195 | 0.170 (z 14.8; perm. p 0.001) | 188.6 / 61.0 | 202.1 / 74.5 | 0.460 (0.027) | 0.226 (0.016) | 5816 / 5629 / 5628 | -0.013 / +0.066 | lag | lag |
| 2020-2024 | Coronary heart disease | 2535 | 0.807 | 0.807 | 0.0008 | 0.087 (z 8.3; perm. p 0.001) | 56.7 / 0.2 | 161.0 / 104.5 | 0.256 (0.030) | 0.224 (0.017) | 4962 / 4904 / 4811 | -0.002 / +0.001 | lag | lag |
| 2020-2024 | Stroke | 2535 | 0.813 | 0.813 | 0.0004 | 0.097 (z 9.2; perm. p 0.001) | 70.7 / 3.2 | 152.7 / 85.2 | 0.284 (0.030) | 0.219 (0.017) | 2000 / 1927 / 1856 | -0.003 / +0.012 | lag | lag |
| 2020-2024 | High blood pressure | 2535 | 0.826 | 0.826 | 0.0002 | 0.094 (z 9.0; perm. p 0.001) | 66.4 / 0.7 | 268.2 / 202.6 | 0.310 (0.029) | 0.272 (0.016) | 10600 / 10523 / 10347 | -0.007 / -0.017 | lag | lag |
| 2020-2024 | Obesity | 2535 | 0.953 | 0.953 | 0.0028 | 0.097 (z 9.2; perm. p 0.001) | 70.0 / 3.3 | 242.8 / 176.0 | 0.331 (0.029) | 0.221 (0.014) | 8780 / 8697 / 8537 | -0.011 / +0.010 | lag | lag |
| 2020-2024 | Physical inactivity | 2535 | 0.924 | 0.924 | 0.0099 | 0.132 (z 12.3; perm. p 0.001) | 129.9 / 42.0 | 172.3 / 84.4 | 0.364 (0.028) | 0.176 (0.014) | 10461 / 10332 / 10296 | -0.010 / +0.050 | lag | lag |
| 2020-2024 | Diabetes | 2535 | 0.824 | 0.824 | 0.0011 | 0.137 (z 12.7; perm. p 0.001) | 139.5 / 8.8 | 297.5 / 166.7 | 0.399 (0.027) | 0.283 (0.016) | 7801 / 7654 / 7521 | -0.011 / +0.011 | lag | lag |

OLS residuals are spatially autocorrelated for every outcome in both cross-sections (Moran's I 0.087 to 0.216; all permutation p-values 0.001 with 999 permutations, the smallest attainable), so OLS standard errors are not trustworthy and OLS is never favoured. By the pre-specified LM rule the spatial error model is favoured for 4 of 6 outcomes in 2015-2019 and 0 of 6 in 2020-2024; the spatial lag model for 2 and 6. The lowest-AIC model agrees with the LM rule in 11 of 12 cases. The error model removes residual autocorrelation (filtered-residual Moran's I -0.022 to -0.002); the lag model leaves some in 2015-2019 (up to +0.145). The covariates and county effects alone explain 80.7% to 96.6% of the variance of the PLACES outcomes; the two exposures add a partial R2 of 0.0002 to 0.0337. This is the expected signature of outcomes that are themselves predictions from tract demography.

### 4.3 Coefficients (all 72 pre-specified estimates)

**Table 4.2 ACS 2015-2019 / PLACES 2021 release (BRFSS 2019); n = 2230 tracts.** Difference in prevalence (percentage points) per 10-point higher exposure, (95% CI); q = Benjamini-Hochberg q-value in the family of 12; **F** = estimator favoured by the diagnostics for that outcome.

| Exposure | Outcome | OLS (HC1) | Spatial error (ML) | Spatial lag (ML), total impact |
|---|---|---|---|---|
| 60+ min commute share | Coronary heart disease | -0.113 (-0.156, -0.070); q <0.001 | -0.084 (-0.127, -0.042); q <0.001 **F** | -0.123 (-0.169, -0.074); q <0.001 |
| 60+ min commute share | Stroke | -0.063 (-0.087, -0.039); q <0.001 | -0.043 (-0.067, -0.019); q 0.002 **F** | -0.068 (-0.094, -0.041); q <0.001 |
| 60+ min commute share | High blood pressure | -0.375 (-0.508, -0.242); q <0.001 | -0.212 (-0.345, -0.079); q 0.005 | -0.415 (-0.565, -0.258); q <0.001 **F** |
| 60+ min commute share | Obesity | +0.057 (-0.026, +0.140); q 0.269 | +0.042 (-0.039, +0.122); q 0.466 **F** | +0.009 (-0.074, +0.094); q 0.868 |
| 60+ min commute share | Physical inactivity | -0.196 (-0.296, -0.097); q <0.001 | -0.101 (-0.200, -0.003); q 0.076 **F** | -0.231 (-0.330, -0.129); q <0.001 |
| 60+ min commute share | Diabetes | -0.149 (-0.219, -0.079); q <0.001 | -0.083 (-0.152, -0.015); q 0.035 | -0.173 (-0.248, -0.094); q <0.001 **F** |
| Drive-alone share | Coronary heart disease | +0.012 (-0.026, +0.050); q 0.583 | +0.004 (-0.029, +0.038); q 0.896 **F** | +0.031 (-0.006, +0.070); q 0.175 |
| Drive-alone share | Stroke | -0.004 (-0.027, +0.018); q 0.701 | -0.002 (-0.021, +0.017); q 0.896 **F** | +0.006 (-0.015, +0.028); q 0.704 |
| Drive-alone share | High blood pressure | -0.065 (-0.185, +0.055); q 0.388 | -0.006 (-0.111, +0.098); q 0.903 | +0.010 (-0.108, +0.138); q 0.868 **F** |
| Drive-alone share | Obesity | -0.032 (-0.112, +0.048); q 0.515 | -0.026 (-0.089, +0.038); q 0.568 **F** | -0.029 (-0.094, +0.039); q 0.526 |
| Drive-alone share | Physical inactivity | -0.299 (-0.385, -0.214); q <0.001 | -0.205 (-0.283, -0.128); q <0.001 **F** | -0.309 (-0.387, -0.228); q <0.001 |
| Drive-alone share | Diabetes | -0.131 (-0.195, -0.067); q <0.001 | -0.070 (-0.124, -0.016); q 0.028 | -0.118 (-0.178, -0.056); q <0.001 **F** |

**Table 4.3 ACS 2020-2024 / PLACES 2025 release (BRFSS 2023); n = 2535 tracts.** Difference in prevalence (percentage points) per 10-point higher exposure, (95% CI); q = Benjamini-Hochberg q-value in the family of 12; **F** = estimator favoured by the diagnostics for that outcome.

| Exposure | Outcome | OLS (HC1) | Spatial error (ML) | Spatial lag (ML), total impact |
|---|---|---|---|---|
| 60+ min commute share | Coronary heart disease | -0.014 (-0.058, +0.030); q 0.679 | -0.013 (-0.052, +0.027); q 0.776 | -0.021 (-0.068, +0.027); q 0.501 **F** |
| 60+ min commute share | Stroke | -0.008 (-0.033, +0.016); q 0.679 | -0.005 (-0.027, +0.017); q 0.776 | -0.012 (-0.038, +0.015); q 0.501 **F** |
| 60+ min commute share | High blood pressure | -0.037 (-0.163, +0.089); q 0.679 | -0.031 (-0.152, +0.090); q 0.776 | -0.077 (-0.224, +0.075); q 0.501 **F** |
| 60+ min commute share | Obesity | +0.069 (-0.017, +0.154); q 0.460 | +0.045 (-0.040, +0.130); q 0.776 | +0.021 (-0.075, +0.121); q 0.808 **F** |
| 60+ min commute share | Physical inactivity | -0.073 (-0.202, +0.055); q 0.549 | -0.056 (-0.174, +0.062); q 0.776 | -0.117 (-0.247, +0.016); q 0.282 **F** |
| 60+ min commute share | Diabetes | +0.008 (-0.067, +0.083); q 0.840 | +0.012 (-0.058, +0.081); q 0.811 | -0.012 (-0.097, +0.076); q 0.859 **F** |
| Drive-alone share | Coronary heart disease | -0.021 (-0.060, +0.017); q 0.549 | -0.024 (-0.057, +0.009); q 0.592 | -0.031 (-0.069, +0.010); q 0.318 **F** |
| Drive-alone share | Stroke | -0.007 (-0.029, +0.015); q 0.679 | -0.007 (-0.025, +0.011); q 0.776 | -0.010 (-0.031, +0.012); q 0.501 **F** |
| Drive-alone share | High blood pressure | +0.013 (-0.099, +0.125); q 0.840 | +0.024 (-0.075, +0.123); q 0.776 | -0.003 (-0.124, +0.127); q 0.967 **F** |
| Drive-alone share | Obesity | -0.067 (-0.142, +0.009); q 0.460 | -0.077 (-0.146, -0.008); q 0.178 | -0.089 (-0.169, -0.006); q 0.208 **F** |
| Drive-alone share | Physical inactivity | -0.240 (-0.343, -0.136); q <0.001 | -0.169 (-0.265, -0.074); q 0.006 | -0.284 (-0.392, -0.172); q <0.001 **F** |
| Drive-alone share | Diabetes | -0.046 (-0.113, +0.022); q 0.549 | -0.007 (-0.063, +0.049); q 0.811 | -0.063 (-0.134, +0.011); q 0.282 **F** |

**Table 4.4 Count of estimates by sign and significance (6 outcomes each).** The q-values in the "Favoured" row are those computed within each estimator's own family of 12.

| ACS period | Estimator | 60+ share: negative / positive | p < 0.05 | FDR q < 0.05 | Drive alone: negative / positive | p < 0.05 | FDR q < 0.05 |
|---|---|---|---|---|---|---|---|
| 2015-2019 | OLS (HC1) | 5 / 1 | 5 | 5 neg, 0 pos | 5 / 1 | 2 | 2 neg, 0 pos |
| 2015-2019 | Spatial error (ML) | 5 / 1 | 5 | 4 neg, 0 pos | 5 / 1 | 2 | 2 neg, 0 pos |
| 2015-2019 | Spatial lag (ML), average total impact | 5 / 1 | 5 | 5 neg, 0 pos | 3 / 3 | 2 | 2 neg, 0 pos |
| 2015-2019 | Favoured per outcome | 5 / 1 | 5 | 4 neg, 0 pos | 4 / 2 | 2 | 2 neg, 0 pos |
| 2020-2024 | OLS (HC1) | 4 / 2 | 0 | 0 neg, 0 pos | 5 / 1 | 1 | 1 neg, 0 pos |
| 2020-2024 | Spatial error (ML) | 4 / 2 | 0 | 0 neg, 0 pos | 5 / 1 | 2 | 1 neg, 0 pos |
| 2020-2024 | Spatial lag (ML), average total impact | 5 / 1 | 0 | 0 neg, 0 pos | 6 / 0 | 2 | 1 neg, 0 pos |
| 2020-2024 | Favoured per outcome | 5 / 1 | 0 | 0 neg, 0 pos | 6 / 0 | 2 | 1 neg, 0 pos |

**Reading of the result.**

- 2015-2019 (favoured estimator per outcome): a 10-point higher 60+ minute commute share went with coronary heart disease prevalence -0.084 points (95% CI -0.127 to -0.042; q <0.001), stroke -0.043 points (95% CI -0.067 to -0.019; q 0.002), high blood pressure -0.415 points (95% CI -0.565 to -0.258; q <0.001), diabetes -0.173 points (95% CI -0.248 to -0.094; q <0.001), physical inactivity -0.101 points (95% CI -0.200 to -0.003; q 0.076) and obesity +0.042 points (95% CI -0.039 to +0.122; q 0.466). The significant associations are inverse, opposite to the hypothesis.
- 2020-2024: no association of the 60+ minute share with any outcome under any estimator (largest absolute favoured estimate 0.117 points; smallest q 0.282).
- Drive-alone share: inversely associated with modelled physical inactivity in both cross-sections (-0.205 points (95% CI -0.283 to -0.128; q <0.001) and -0.284 points (95% CI -0.392 to -0.172; q <0.001)) and with diabetes in 2015-2019 (-0.118 points (95% CI -0.178 to -0.056; q <0.001)); no association with coronary heart disease, stroke or high blood pressure in either cross-section.
- Magnitudes are small relative to between-tract variation: the outcome standard deviations are in Table 2.2, and a 10-point exposure difference is a little over one standard deviation of the 60+ share and about 0.6 standard deviations of the drive-alone share.
- A plausible, untested reading of the inverse 2015-2019 associations is residual composition: long-commute tracts are worker-dense, and the three broad age shares used here do not capture the finer demographic cells from which PLACES builds the outcome (PLACES method as summarised in the project data dictionary; not re-verified from CDC documentation here). That is an interpretation, not a finding.

## 5. Housing to commute to mortality: county-year panel (step 3)

> **This is not causal identification.** Two-way fixed effects remove fixed county differences and common year shocks only. Home values, commuting, the age and occupational mix of residents, migration and mortality all trend together within counties, and nothing here isolates exogenous variation in housing costs. **The mortality rates are model-smoothed** (age-standardised and spatiotemporally smoothed by CDC): smoothing borrows strength across neighbouring counties and adjacent years, which removes exactly the within-county year-to-year variation that fixed-effects models use, induces serial and spatial correlation, and makes the stated uncertainty too small. **Sample size:** 14 counties x 10 years = 140 county-years, 14 clusters.

### 5.1 Specification

- Model H: `commute_ct = a_c + d_t + beta * log(ZHVI_c,t-1) + e_ct`; outcomes: mean one-way commute and 60+ minute share (commuters 16+; also the 35-64 band, which is the a-path for the 35-64 decomposition). Lag 1 is primary; lags 0 and 2 are secondary. The 2008 and 2009 index values come from `zillow_county_annual.parquet` of this project. Year effects absorb common inflation. Coefficients are scaled to a 10% higher home value (beta x ln 1.10).
- Model M: `log(mortality_ct, band) = a_c + d_t + gamma * commute_ct + e_ct`, all-cardiovascular mortality (primary), coronary heart disease and stroke (secondary), ages 35-64 (with the commute measure of commuters aged 35-64) and 65+ (with the measure for all commuters 16+, because people aged 65+ are mostly not commuters). Contemporaneous. Coefficients per 5 minutes or per 10 points of 60+ share; x100 is an approximate percent difference in the rate.
- Decomposition: a = home value -> commute; b = commute -> log mortality given home value; indirect = a x b; direct = home value -> log mortality given commute; total = home value -> log mortality. Percentile intervals from 4,999 county-cluster pairs bootstrap draws (seed 20261113).
- Inference: clustered by county. CR1 standard errors with a t(13) reference; primary intervals from the wild cluster restricted bootstrap-t (null imposed, Rademacher weights, all 2^14 = 16,384 sign vectors enumerated, so no simulation error) inverted for the 95% CI. Unweighted.
- Minimum detectable effect (MDE): (t_0.975,13 + t_0.80,13) x CR1 SE = 3.03 x SE, the true coefficient that would be detected with 80% power at two-sided 5%.
- Sampling error in the PUMS county-year commute estimates is not modelled. The column "noise share" is mean(SE^2) x (1-1/T)(1-1/G) divided by the within-county, within-year variance of the measure: the approximate fraction of the identifying variation that is sampling noise (added diagnostic, not pre-specified).

### 5.2 Housing to commute

**Table 5.1 Model H: difference in the commute measure per 10% higher nominal home value (n = 140 county-years, 14 clusters).**

| Outcome | Home value lag | Role | Estimate | CR1 SE | 95% CI, t(13) | p, t(13) | 95% CI, wild cluster | p, wild cluster | Width of wild CI | MDE (80% power) | Noise share of outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Mean one-way commute, commuters 16+ | lag 1 y | primary | +0.917 min | 0.372 | +0.113 to +1.721 | 0.028 | -0.049 to +1.789 | 0.056 | 1.839 | 1.127 | 0.47 |
| Share of commuters 16+ with 60+ min commute | lag 1 y | primary | +0.656 pts | 0.685 | -0.823 to +2.135 | 0.355 | -1.116 to +2.337 | 0.373 | 3.453 | 2.075 | 0.39 |
| Mean one-way commute, commuters 35-64 | lag 1 y | primary | +0.868 min | 0.467 | -0.141 to +1.877 | 0.086 | -0.351 to +1.933 | 0.115 | 2.284 | 1.415 | 0.61 |
| Share of commuters 35-64 with 60+ min commute | lag 1 y | primary | +0.388 pts | 0.839 | -1.425 to +2.201 | 0.651 | -1.774 to +2.357 | 0.646 | 4.131 | 2.543 | 0.45 |
| Mean one-way commute, commuters 16+ | lag 0 y | secondary | +0.863 min | 0.443 | -0.095 to +1.820 | 0.074 | -0.249 to +1.932 | 0.105 | 2.181 | 1.344 | 0.47 |
| Share of commuters 16+ with 60+ min commute | lag 0 y | secondary | +0.534 pts | 0.792 | -1.177 to +2.246 | 0.512 | -1.520 to +2.367 | 0.526 | 3.886 | 2.401 | 0.39 |
| Mean one-way commute, commuters 35-64 | lag 0 y | secondary | +0.658 min | 0.553 | -0.536 to +1.852 | 0.255 | -0.770 to +1.927 | 0.286 | 2.697 | 1.675 | 0.61 |
| Share of commuters 35-64 with 60+ min commute | lag 0 y | secondary | +0.088 pts | 0.918 | -1.895 to +2.072 | 0.925 | -2.286 to +2.209 | 0.925 | 4.495 | 2.783 | 0.45 |
| Mean one-way commute, commuters 16+ | lag 2 y | secondary | +0.454 min | 0.248 | -0.082 to +0.991 | 0.090 | -0.052 to +1.057 | 0.078 | 1.109 | 0.753 | 0.47 |
| Share of commuters 16+ with 60+ min commute | lag 2 y | secondary | +0.441 pts | 0.331 | -0.273 to +1.156 | 0.205 | -0.228 to +1.210 | 0.196 | 1.438 | 1.002 | 0.39 |
| Mean one-way commute, commuters 35-64 | lag 2 y | secondary | +0.277 min | 0.263 | -0.291 to +0.844 | 0.311 | -0.260 to +0.910 | 0.307 | 1.170 | 0.796 | 0.61 |
| Share of commuters 35-64 with 60+ min commute | lag 2 y | secondary | +0.138 pts | 0.399 | -0.724 to +1.000 | 0.735 | -0.745 to +1.010 | 0.727 | 1.756 | 1.210 | 0.45 |

How wide the intervals are: for the primary mean-commute model the wild-cluster interval spans 1.84 minutes around an estimate of +0.92, i.e. it is 2.0 times the estimate; for the 60+ share it spans 3.45 points around +0.66 (5.3 times the estimate). The MDE is 1.13 minutes and 2.07 points per 10% of home value. The within-county, within-year standard deviation of log home value is only 0.038 (about 3.9%), because home values rose together across the region; year effects absorb the common rise, which is most of the story told by the raw trends. All twelve point estimates are positive; none of the wild-cluster intervals excludes zero.

### 5.3 Commute to mortality

**Table 5.2 Model M: approximate percent difference in the model-smoothed mortality rate per 5 more minutes of mean commute or per 10-point higher 60+ share (100 x log-rate coefficient; n = 140, 14 clusters).**

| Mortality (cause, ages) | Commute measure | Role | Estimate | CR1 SE (x100) | 95% CI, wild cluster | p, wild cluster | p, t(13) | MDE (80% power) | Noise share of regressor |
|---|---|---|---|---|---|---|---|---|---|
| all cardiovascular disease, ages 35-64 | mean commute minutes (35-64 commuters) | primary | -1.54% | 1.88 | -6.30% to +2.68% | 0.429 | 0.427 | 5.70% | 0.61 |
| all cardiovascular disease, ages 35-64 | 60+ min share (35-64 commuters) | primary | -6.25% | 3.02 | -13.25% to +0.86% | 0.090 | 0.059 | 9.15% | 0.45 |
| all cardiovascular disease, ages 65+ | mean commute minutes (16+ commuters) | primary | +1.35% | 1.33 | -1.64% to +4.41% | 0.328 | 0.330 | 4.05% | 0.47 |
| all cardiovascular disease, ages 65+ | 60+ min share (16+ commuters) | primary | +1.08% | 1.59 | -2.53% to +4.18% | 0.505 | 0.509 | 4.82% | 0.39 |
| coronary heart disease, ages 35-64 | mean commute minutes (35-64 commuters) | secondary | -7.15% | 2.81 | -14.81% to -1.33% | 0.010 | 0.025 | 8.52% | 0.61 |
| coronary heart disease, ages 35-64 | 60+ min share (35-64 commuters) | secondary | -10.51% | 3.83 | -18.95% to -1.94% | 0.013 | 0.017 | 11.61% | 0.45 |
| coronary heart disease, ages 65+ | mean commute minutes (16+ commuters) | secondary | -5.18% | 2.32 | -11.26% to -0.36% | 0.037 | 0.044 | 7.03% | 0.47 |
| coronary heart disease, ages 65+ | 60+ min share (16+ commuters) | secondary | -8.25% | 2.88 | -15.58% to -2.34% | 0.011 | 0.013 | 8.72% | 0.39 |
| stroke, ages 35-64 | mean commute minutes (35-64 commuters) | secondary | -0.52% | 2.70 | -7.08% to +5.98% | 0.857 | 0.851 | 8.17% | 0.61 |
| stroke, ages 35-64 | 60+ min share (35-64 commuters) | secondary | -3.90% | 3.44 | -11.55% to +4.60% | 0.305 | 0.278 | 10.43% | 0.45 |
| stroke, ages 65+ | mean commute minutes (16+ commuters) | secondary | +6.32% | 4.05 | -4.24% to +14.60% | 0.176 | 0.142 | 12.27% | 0.47 |
| stroke, ages 65+ | 60+ min share (16+ commuters) | secondary | +11.71% | 6.01 | -3.24% to +23.76% | 0.095 | 0.073 | 18.22% | 0.39 |

Primary outcome (all cardiovascular disease): 0 of 4 coefficients are significant at 0.05; point estimates are negative at ages 35-64 and positive but small at 65+. Secondary outcomes: all 4 coronary heart disease coefficients are NEGATIVE with wild-cluster p from 0.010 to 0.037 (counties whose commutes lengthened most had larger declines in smoothed coronary mortality), not adjusted for multiplicity across the 12 models; the 4 stroke coefficients are not significant. None supports a positive commute-mortality association. The MDEs range from 4.0% to 18.2%. Benchmark (illustrative): if every commuter with a 60+ minute commute carried the hazard ratio of 1.5 (1.08 to 2.09) reported for men riding in a car more than 10 versus under 4 hours a week (dose-response row DR003, Warren 2010; the only driving-specific cardiovascular mortality estimate), and commuters are 68.5% of people aged 35-64 (all 14 counties, 2019), a 10-point higher 60+ share would raise mortality at 35-64 by about 3.4%. The MDE for that model is 9.2%, 2.7 times larger, before allowing for attenuation: 39% to 61% of the within-county variation in the commute regressors is PUMS sampling noise, which biases these coefficients towards zero. A null here is therefore uninformative about effects of the size the literature suggests; it rules out only large effects.

### 5.4 Product-of-coefficients decomposition (descriptive)

**Table 5.3 Decomposition of the association between lagged log home value and log all-cardiovascular mortality (estimate, 95% percentile interval from 4,999 county-cluster bootstrap draws).** Mortality entries are approximate percent differences in the rate.

| Outcome | Commute measure (mediator) | Path | Estimate (95% bootstrap interval) |
|---|---|---|---|
| All CVD, 35-64 | mean commute (min) | a: log home value (lag 1) -> commute | +0.868 (-0.097 to +1.775) min per 10% home value |
| All CVD, 35-64 | mean commute (min) | b: commute -> log mortality given home value | -0.70% (-1.31% to +0.01%) per minute |
| All CVD, 35-64 | mean commute (min) | indirect a x b | -0.611% (-1.530% to +0.136%) per 10% home value |
| All CVD, 35-64 | mean commute (min) | direct: home value -> log mortality given commute | +4.105% (+0.782% to +6.835%) per 10% home value |
| All CVD, 35-64 | mean commute (min) | total: home value -> log mortality | +3.494% (+0.445% to +6.526%) per 10% home value |
| All CVD, 35-64 | 60+ share | a: log home value (lag 1) -> commute | +0.388 (-1.341 to +2.019) pts per 10% home value |
| All CVD, 35-64 | 60+ share | b: commute -> log mortality given home value | -6.97% (-11.07% to -1.46%) per 10 pts |
| All CVD, 35-64 | 60+ share | indirect a x b | -0.271% (-1.384% to +0.991%) per 10% home value |
| All CVD, 35-64 | 60+ share | direct: home value -> log mortality given commute | +3.765% (+0.907% to +6.083%) per 10% home value |
| All CVD, 35-64 | 60+ share | total: home value -> log mortality | +3.494% (+0.445% to +6.526%) per 10% home value |
| All CVD, 65+ | mean commute (min) | a: log home value (lag 1) -> commute | +0.917 (+0.150 to +1.676) min per 10% home value |
| All CVD, 65+ | mean commute (min) | b: commute -> log mortality given home value | +0.01% (-0.41% to +0.42%) per minute |
| All CVD, 65+ | mean commute (min) | indirect a x b | +0.007% (-0.420% to +0.353%) per 10% home value |
| All CVD, 65+ | mean commute (min) | direct: home value -> log mortality given commute | +1.998% (-0.073% to +3.817%) per 10% home value |
| All CVD, 65+ | mean commute (min) | total: home value -> log mortality | +2.005% (-0.052% to +3.842%) per 10% home value |
| All CVD, 65+ | 60+ share | a: log home value (lag 1) -> commute | +0.656 (-0.752 to +2.029) pts per 10% home value |
| All CVD, 65+ | 60+ share | b: commute -> log mortality given home value | +0.11% (-3.84% to +3.84%) per 10 pts |
| All CVD, 65+ | 60+ share | indirect a x b | +0.007% (-0.476% to +0.329%) per 10% home value |
| All CVD, 65+ | 60+ share | direct: home value -> log mortality given commute | +1.997% (-0.208% to +3.983%) per 10% home value |
| All CVD, 65+ | 60+ share | total: home value -> log mortality | +2.005% (-0.052% to +3.842%) per 10% home value |

All four indirect (home value -> commute -> mortality) products have intervals that include zero (estimates -0.611% to +0.007% per 10% of home value). The total within-county association of home value with all-cardiovascular mortality at ages 35-64 is +3.49% per 10% of home value (interval +0.44% to +6.53%). The total within-county association of home value with all-cardiovascular mortality at ages 65+ is +2.00% per 10% of home value (interval -0.05% to +3.84%). At ages 35-64 this positive total association is essentially all 'direct', that is, not passing through the commute measures; it is a within-county co-trend (counties with faster home-value growth had slower declines in smoothed mortality) with many non-commute explanations, including the smoothing model, and is not evidence of an effect of housing cost. A pairs cluster bootstrap with 14 clusters is known to be unreliable (intervals tend to be too narrow); these intervals should be read as optimistic. The decomposition assumes linearity, no exposure-mediator interaction and no unmeasured confounding of any path, none of which is defensible here.

## 6. Sensitivity analyses (step 4)

All specifications were fixed in advance. Each is compared with the primary estimate for the same outcome, exposure, cross-section and estimator. "Sign differs" compares point estimates regardless of significance; "significance changes" means crossing nominal p = 0.05 in either direction. For S3 the alternative commute measure is compared with the primary 60+ share coefficient on sign and significance only (units differ). S6 is compared with the 2015-2019 cross-sectional estimate.

**Table 6.1 Where sign, size or significance change (tract models; rows pool the estimators run for the specification: OLS, spatial error and spatial lag, 6 outcomes each).**

| Specification | Cross-section | n tracts | Exposure | Models | Sign differs from primary | Significance changes | Sign reversal, both significant | p < 0.05: sensitivity vs primary | Significant AND positive | Median ratio to primary |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 Nine core counties only | 2015-2019 | 1571 | commute 60plus | 18 | 1 | 0 | 0 | 15 vs 15 | 0 | 1.13 |
| S1 Nine core counties only | 2015-2019 | 1571 | drive alone | 18 | 5 | 0 | 0 | 6 vs 6 | 0 | 1.02 |
| S1 Nine core counties only | 2020-2024 | 1744 | commute 60plus | 18 | 4 | 6 | 0 | 6 vs 0 | 0 | 2.68 |
| S1 Nine core counties only | 2020-2024 | 1744 | drive alone | 18 | 2 | 2 | 0 | 3 vs 5 | 0 | 0.73 |
| S2 Excluding top decile of transit share | 2015-2019 | 2007 | commute 60plus | 18 | 0 | 0 | 0 | 15 vs 15 | 0 | 1.05 |
| S2 Excluding top decile of transit share | 2015-2019 | 2007 | drive alone | 18 | 6 | 0 | 0 | 6 vs 6 | 0 | 0.80 |
| S2 Excluding top decile of transit share | 2020-2024 | 2281 | commute 60plus | 18 | 2 | 1 | 0 | 1 vs 0 | 0 | 1.50 |
| S2 Excluding top decile of transit share | 2020-2024 | 2281 | drive alone | 18 | 2 | 1 | 0 | 6 vs 5 | 0 | 0.47 |
| S3a Mean commute minutes (per 5 min) as exposure | 2015-2019 | 2230 | mean commute min | 18 | 0 | 2 | 0 | 15 vs 15 | 1 |  |
| S3a Mean commute minutes (per 5 min) as exposure | 2015-2019 | 2230 | drive alone | 18 | 0 | 0 | 0 | 6 vs 6 | 0 | 0.94 |
| S3a Mean commute minutes (per 5 min) as exposure | 2020-2024 | 2534 | mean commute min | 18 | 4 | 1 | 0 | 1 vs 0 | 1 |  |
| S3a Mean commute minutes (per 5 min) as exposure | 2020-2024 | 2534 | drive alone | 18 | 1 | 0 | 0 | 5 vs 5 | 0 | 0.96 |
| S3b 45+ minute share as exposure | 2015-2019 | 2230 | commute 45plus | 18 | 0 | 0 | 0 | 15 vs 15 | 0 |  |
| S3b 45+ minute share as exposure | 2015-2019 | 2230 | drive alone | 18 | 1 | 0 | 0 | 6 vs 6 | 0 | 1.02 |
| S3b 45+ minute share as exposure | 2020-2024 | 2535 | commute 45plus | 18 | 2 | 1 | 0 | 1 vs 0 | 0 |  |
| S3b 45+ minute share as exposure | 2020-2024 | 2535 | drive alone | 18 | 0 | 0 | 0 | 5 vs 5 | 0 | 1.00 |
| S3c 90+ minute share as exposure | 2015-2019 | 2230 | commute 90plus | 18 | 2 | 0 | 0 | 15 vs 15 | 0 |  |
| S3c 90+ minute share as exposure | 2015-2019 | 2230 | drive alone | 18 | 1 | 0 | 0 | 6 vs 6 | 0 | 0.97 |
| S3c 90+ minute share as exposure | 2020-2024 | 2535 | commute 90plus | 18 | 4 | 1 | 0 | 1 vs 0 | 1 |  |
| S3c 90+ minute share as exposure | 2020-2024 | 2535 | drive alone | 18 | 1 | 0 | 0 | 5 vs 5 | 0 | 0.97 |
| S4 Adding PLACES smoking prevalence | 2015-2019 | 2230 | commute 60plus | 18 | 0 | 1 | 0 | 16 vs 15 | 1 | 0.98 |
| S4 Adding PLACES smoking prevalence | 2015-2019 | 2230 | drive alone | 18 | 6 | 2 | 0 | 6 vs 6 | 1 | 0.69 |
| S4 Adding PLACES smoking prevalence | 2020-2024 | 2535 | commute 60plus | 18 | 1 | 1 | 0 | 1 vs 0 | 1 | 0.61 |
| S4 Adding PLACES smoking prevalence | 2020-2024 | 2535 | drive alone | 18 | 12 | 7 | 0 | 6 vs 5 | 4 | -0.33 |
| S5 Adult-population-weighted (WLS) vs unweighted OLS | 2015-2019 | 2230 | commute 60plus | 6 | 0 | 0 | 0 | 5 vs 5 | 0 | 1.06 |
| S5 Adult-population-weighted (WLS) vs unweighted OLS | 2015-2019 | 2230 | drive alone | 6 | 1 | 0 | 0 | 2 vs 2 | 0 | 0.59 |
| S5 Adult-population-weighted (WLS) vs unweighted OLS | 2020-2024 | 2535 | commute 60plus | 6 | 1 | 1 | 0 | 1 vs 0 | 0 | 2.25 |
| S5 Adult-population-weighted (WLS) vs unweighted OLS | 2020-2024 | 2535 | drive alone | 6 | 0 | 0 | 0 | 1 vs 1 | 0 | 0.90 |
| S6 First difference, boundary-stable tracts | 2015-19 to 2020-24 | 1514 | commute 60plus | 12 | 1 | 5 | 0 | 5 vs 10 | 0 | 0.42 |
| S6 First difference, boundary-stable tracts | 2015-19 to 2020-24 | 1514 | drive alone | 12 | 9 | 4 | 2 | 4 vs 4 | 4 | -0.55 |
| S8a 60+ share entered alone | 2015-2019 | 2230 | commute 60plus | 18 | 0 | 1 | 0 | 14 vs 15 | 0 | 1.00 |
| S8a 60+ share entered alone | 2020-2024 | 2535 | commute 60plus | 18 | 0 | 0 | 0 | 0 vs 0 | 0 | 0.93 |
| S8b Drive-alone share entered alone | 2015-2019 | 2230 | drive alone | 18 | 3 | 1 | 0 | 7 vs 6 | 1 | 0.96 |
| S8b Drive-alone share entered alone | 2020-2024 | 2535 | drive alone | 18 | 1 | 0 | 0 | 5 vs 5 | 0 | 0.98 |

**S1 (core counties).** In 2015-2019 the inverse associations of the 60+ share persist in the nine core counties. In 2020-2024, restricting to the core counties turns 6 of 18 previously null 60+ share coefficients nominally significant, all of them negative (6 negative, 0 positive); 2 of 18 survive FDR control within their family.

**Table 6.2 S1, nine core counties, 2020-2024.** Estimate (95% CI); p; primary estimate.

| Exposure | Outcome | OLS (HC1) | Spatial error (ML) | Spatial lag (ML), average total impact |
|---|---|---|---|---|
| commute 60plus | Coronary heart disease | -0.029 (-0.079, +0.021); p 0.251; primary -0.014 | -0.038 (-0.086, +0.010); p 0.118; primary -0.013 | -0.055 (-0.113, +0.004); p 0.061; primary -0.021 |
| commute 60plus | Stroke | -0.022 (-0.051, +0.006); p 0.126; primary -0.008 | -0.025 (-0.051, +0.002); p 0.070; primary -0.005 | -0.038 (-0.070, -0.005); p 0.022; primary -0.012 |
| commute 60plus | High blood pressure | -0.116 (-0.274, +0.041); p 0.147; primary -0.037 | -0.128 (-0.277, +0.021); p 0.092; primary -0.031 | -0.240 (-0.425, -0.049); p 0.012; primary -0.077 |
| commute 60plus | Obesity | +0.007 (-0.090, +0.105); p 0.887; primary +0.069 | -0.000 (-0.096, +0.096); p 0.997; primary +0.045 | -0.058 (-0.168, +0.056); p 0.312; primary +0.021 |
| commute 60plus | Physical inactivity | -0.177 (-0.325, -0.029); p 0.019; primary -0.073 | -0.168 (-0.304, -0.032); p 0.015; primary -0.056 | -0.250 (-0.404, -0.092); p 0.002; primary -0.117 |
| commute 60plus | Diabetes | -0.057 (-0.152, +0.038); p 0.241; primary +0.008 | -0.063 (-0.148, +0.023); p 0.151; primary +0.012 | -0.122 (-0.231, -0.009); p 0.031; primary -0.012 |
| drive alone | Coronary heart disease | -0.016 (-0.060, +0.028); p 0.481; primary -0.021 | -0.014 (-0.052, +0.023); p 0.454; primary -0.024 | -0.019 (-0.063, +0.027); p 0.403; primary -0.031 |
| drive alone | Stroke | -0.003 (-0.028, +0.022); p 0.828; primary -0.007 | -0.001 (-0.021, +0.020); p 0.961; primary -0.007 | -0.002 (-0.027, +0.024); p 0.848; primary -0.010 |
| drive alone | High blood pressure | +0.051 (-0.079, +0.181); p 0.442; primary +0.013 | +0.086 (-0.031, +0.203); p 0.148; primary +0.024 | +0.061 (-0.080, +0.212); p 0.415; primary -0.003 |
| drive alone | Obesity | -0.052 (-0.130, +0.027); p 0.197; primary -0.067 | -0.056 (-0.131, +0.020); p 0.147; primary -0.077 | -0.065 (-0.148, +0.024); p 0.148; primary -0.089 |
| drive alone | Physical inactivity | -0.262 (-0.379, -0.145); p <0.001; primary -0.240 | -0.152 (-0.259, -0.046); p 0.005; primary -0.169 | -0.287 (-0.406, -0.164); p <0.001; primary -0.284 |
| drive alone | Diabetes | -0.054 (-0.135, +0.027); p 0.193; primary -0.046 | +0.015 (-0.051, +0.082); p 0.652; primary -0.007 | -0.056 (-0.140, +0.032); p 0.207; primary -0.063 |

**S4 (smoking).** Adding modelled smoking prevalence changes the sign of 6 of 18 drive-alone coefficients in 2015-2019 and 12 of 18 in 2020-2024, and changes nominal significance for 2 and 7; the 60+ share coefficients are little affected. Smoking prevalence is itself a PLACES model output built from the same demographic predictors, so this adjustment partly re-enters the outcome model on the right-hand side and is not a clean confounder adjustment. The drive-alone associations should be regarded as not robust.

**S6 (first difference).** 1514 boundary-stable tracts present in both samples. Changes in modelled prevalence between the PLACES 2021 release (BRFSS 2019) and the 2025 release (BRFSS 2023) regressed on changes in the exposures and covariates, with county effects. For the 60+ share, 5 of 12 coefficients are nominally significant and negative and 0 positive; 5 of these are OLS estimates and 0 are spatial error estimates. For drive-alone share, 4 of 12 are significant and positive (physical inactivity and obesity, both estimators), the opposite sign to the cross-sectional estimates for inactivity. The two PLACES releases differ in BRFSS year, population base and modelling details, the period spans the pandemic shift to remote work (which changes who is counted as a commuter and as driving alone), and income is nominal; the differenced outcome therefore mixes real change with method change, and these estimates carry little evidential weight in either direction.

**Table 6.3 S6, first-difference models.** Estimate per 10-point change in exposure (95% CI); p; primary = 2015-2019 cross-sectional estimate, same estimator.

| Exposure | Outcome | OLS (HC1) | Spatial error (ML) |
|---|---|---|---|
| commute 60plus | Coronary heart disease | -0.060 (-0.104, -0.016); p 0.007; primary -0.113 | -0.037 (-0.076, +0.002); p 0.062; primary -0.084 |
| commute 60plus | Stroke | -0.028 (-0.053, -0.004); p 0.025; primary -0.063 | -0.015 (-0.038, +0.007); p 0.176; primary -0.043 |
| commute 60plus | High blood pressure | -0.150 (-0.294, -0.007); p 0.040; primary -0.375 | -0.053 (-0.169, +0.062); p 0.367; primary -0.212 |
| commute 60plus | Obesity | +0.009 (-0.080, +0.098); p 0.841; primary +0.057 | -0.019 (-0.102, +0.064); p 0.652; primary +0.042 |
| commute 60plus | Physical inactivity | -0.127 (-0.250, -0.005); p 0.042; primary -0.196 | -0.088 (-0.214, +0.038); p 0.170; primary -0.101 |
| commute 60plus | Diabetes | -0.094 (-0.168, -0.019); p 0.014; primary -0.149 | -0.033 (-0.100, +0.034); p 0.331; primary -0.083 |
| drive alone | Coronary heart disease | +0.012 (-0.019, +0.042); p 0.455; primary +0.012 | +0.010 (-0.019, +0.038); p 0.508; primary +0.004 |
| drive alone | Stroke | +0.010 (-0.009, +0.028); p 0.301; primary -0.004 | +0.009 (-0.007, +0.025); p 0.291; primary -0.002 |
| drive alone | High blood pressure | -0.001 (-0.094, +0.092); p 0.978; primary -0.065 | +0.015 (-0.070, +0.100); p 0.728; primary -0.006 |
| drive alone | Obesity | +0.127 (+0.060, +0.193); p <0.001; primary -0.032 | +0.092 (+0.031, +0.154); p 0.003; primary -0.026 |
| drive alone | Physical inactivity | +0.156 (+0.061, +0.251); p 0.001; primary -0.299 | +0.119 (+0.028, +0.210); p 0.011; primary -0.205 |
| drive alone | Diabetes | +0.053 (-0.001, +0.107); p 0.054; primary -0.131 | +0.037 (-0.013, +0.086); p 0.145; primary -0.070 |

**S7 (county mortality in place of modelled prevalence).** Fifteen counties; log model-smoothed mortality rate on each ACS 5-year county exposure, alone and with log median household income. With n = 15 nothing more can be adjusted for, and the estimates are dominated by between-county socioeconomic differences.

**Table 6.4 S7: approximate percent difference in county mortality rate per 10-point higher exposure (HC3 95% CI, t reference); Spearman rank correlation.** "Classical p" uses ordinary least-squares standard errors and was added after seeing that one county has very high leverage (not pre-specified).

| Outcome | Exposure | Unadjusted | Adjusted for log median household income | Spearman rho | Max leverage (unadjusted) |
|---|---|---|---|---|---|
| All CVD mortality 35-64, mean 2015-2019 | 60+ min commute share | +2.3% (-32.7% to +37.2%); p 0.891; classical p 0.903 | +3.7% (-13.3% to +20.8%); p 0.640; classical p 0.725 | +0.27 (p 0.328) | 0.34 |
| All CVD mortality 35-64, mean 2015-2019 | Drive-alone share | +10.8% (-47.5% to +69.2%); p 0.694; classical p 0.156 | -3.7% (-33.4% to +26.1%); p 0.793; classical p 0.506 | +0.64 (p 0.011) | 0.76 |
| All CVD mortality 65+, mean 2015-2019 | 60+ min commute share | -2.3% (-15.9% to +11.2%); p 0.714; classical p 0.771 | -1.6% (-7.8% to +4.5%); p 0.573; classical p 0.624 | -0.04 (p 0.889) | 0.34 |
| All CVD mortality 65+, mean 2015-2019 | Drive-alone share | +7.2% (-14.5% to +28.9%); p 0.489; classical p 0.021 | +1.2% (-7.2% to +9.7%); p 0.759; classical p 0.482 | +0.79 (p <0.001) | 0.76 |
| CHD mortality 35-64, mean 2015-2019 | 60+ min commute share | -9.0% (-45.1% to +27.1%); p 0.601; classical p 0.652 | -7.3% (-24.4% to +9.8%); p 0.372; classical p 0.452 | -0.03 (p 0.919) | 0.34 |
| CHD mortality 35-64, mean 2015-2019 | Drive-alone share | +15.8% (-42.3% to +73.9%); p 0.567; classical p 0.046 | +1.0% (-26.9% to +29.0%); p 0.937; classical p 0.839 | +0.75 (p 0.001) | 0.76 |
| CHD mortality 65+, mean 2015-2019 | 60+ min commute share | -14.1% (-33.9% to +5.8%); p 0.149; classical p 0.293 | -13.0% (-23.0% to -2.9%); p 0.016; classical p 0.038 | -0.25 (p 0.376) | 0.34 |
| CHD mortality 65+, mean 2015-2019 | Drive-alone share | +10.4% (-29.0% to +49.9%); p 0.577; classical p 0.056 | +0.2% (-18.0% to +18.4%); p 0.981; classical p 0.956 | +0.75 (p 0.001) | 0.76 |
| Heart disease mortality 35+, pooled 3-year rates (midpoints 2022, 2023 averaged) | 60+ min commute share | +5.3% (-21.1% to +31.8%); p 0.671; classical p 0.600 | -5.2% (-16.6% to +6.2%); p 0.340; classical p 0.384 | +0.29 (p 0.302) | 0.40 |
| Heart disease mortality 35+, pooled 3-year rates (midpoints 2022, 2023 averaged) | Drive-alone share | +8.3% (-15.0% to +31.7%); p 0.454; classical p 0.047 | -2.1% (-18.5% to +14.3%); p 0.782; classical p 0.547 | +0.70 (p 0.003) | 0.59 |
| Stroke mortality 35+, pooled 3-year rates (midpoints 2022, 2023 averaged) | 60+ min commute share | +11.4% (-7.8% to +30.6%); p 0.223; classical p 0.173 | +4.7% (-8.4% to +17.8%); p 0.448; classical p 0.476 | +0.46 (p 0.084) | 0.40 |
| Stroke mortality 35+, pooled 3-year rates (midpoints 2022, 2023 averaged) | Drive-alone share | +7.3% (-4.4% to +19.0%); p 0.200; classical p 0.039 | +1.1% (-6.0% to +8.1%); p 0.750; classical p 0.788 | +0.68 (p 0.005) | 0.59 |

For the 60+ minute share, 1 of 12 county regressions is nominally significant under HC3 (CHD mortality 65+, mean 2015-2019, adjusted for log median household income: -13.0%); rank correlations range from -0.25 to +0.46 with none significant at 0.05. For drive-alone share the rank correlations with mortality are strongly positive (+0.64 to +0.79; 6 of 6 with p < 0.05), but the regression slopes are imprecise under HC3 because San Francisco is a high-leverage point (leverage up to 0.82), and they shrink towards zero once median household income is included (largest adjusted estimate 3.7% per 10 points). The positive unadjusted rank correlation is what would be expected from the Central Valley counties being both more car-dependent and poorer; it does not survive the single adjustment available. The within-county panel models in section 5 are the counterpart that removes fixed county differences.

**Overall.** Across specifications the commute-duration exposure (60+ share or its alternatives) is either inversely associated with modelled prevalence (2015-2019; core counties in 2020-2024) or not associated. Of 276 sensitivity estimates for a commute-duration exposure, 122 are nominally significant and negative and 5 nominally significant and positive. The positive ones are all for obesity (S3a 2015-2019 obesity, Spatial error: +0.054, p 0.044, q 0.075; S4 2015-2019 obesity, OLS: +0.069, p 0.034, q 0.052; S3a 2020-2024 obesity, OLS: +0.057, p 0.047, q 0.281; S3c 2020-2024 obesity, OLS: +0.170, p 0.033, q 0.201; S4 2020-2024 obesity, OLS: +0.090, p 0.003, q 0.027); the number that survive FDR control within their family is 1 (S4 2020-2024 obesity, OLS: +0.090, p 0.003, q 0.027), under OLS only and not under either spatial estimator for the same specification, where OLS residuals are spatially autocorrelated. No positive association with coronary heart disease, stroke, high blood pressure, diabetes or inactivity appears in any specification. The alternative thresholds (45+, 90+, mean minutes) behave like the 60+ share. Single-exposure models and population weighting change little. Drive-alone share coefficients change sign under smoking adjustment and in first differences and should not be interpreted. Full results: `sensitivity_models.csv`; counts: `sensitivity_change_summary.csv`.

## 7. Departures from and additions to the pre-specified plan

No pre-specified model was dropped or altered. Additions, all reported: (1) a 13-df Wald test of equal change across the 14 counties, and descriptive 2019-2021 and 2010-2024 change rows in `trends_table.csv`; (2) Model H was also run for the 35-64 commuter band because it is the a-path of the 35-64 decomposition; (3) the sampling-noise share diagnostic in the panel; (4) covariates-only R2, partial R2 and Moran's I of the spatial-model residuals in the tract diagnostics; (5) classical standard errors and leverage for the 15-county regressions; the plan did not name a variance estimator for S7, HC3 was coded first and is the reported interval. One API test fit was run before the primary run, on short-sleep prevalence, which is not among the six outcomes.

## 8. Assumptions

1. ACS samples in different years are independent (variance of a change = sum of variances). Successive-difference replication variance with factor 4/80.
2. PUMS travel time is top-coded; means are computed on the top-coded values.
3. Regional Zillow values are unweighted means of county index values; the index is nominal, smoothed, and has no uncertainty estimate.
4. Tract sample restricted to tracts with at least 100 commuters; median household income top-codes are handled with an indicator rather than a censored-data model.
5. Queen contiguity on TIGER/Line polygons (which extend over water); nearest-neighbour link for tracts with no sample neighbour; row-standardised weights.
6. The two exposures are mutually adjusted in the primary models; reference categories are under-18 (age) and non-Hispanic White plus other (race/ethnicity).
7. Spatial models are estimated by maximum likelihood assuming normal, homoskedastic innovations; lag-model p-values are those of the raw coefficient; total-impact intervals come from 2,000 parametric draws.
8. False discovery rate controlled by Benjamini-Hochberg within families of 12 (6 outcomes x 2 exposures) per cross-section and estimator.
9. Panel models are unweighted and linear; log mortality rates; contemporaneous commute; one-year lag of home value; CR1 uses the convention that county effects nested in clusters are not counted in the degrees-of-freedom correction.
10. The 65+ mortality models use the commute measure of all commuters, a proxy for area-level commuting conditions rather than the exposure of the people who died.
11. The MDE uses the estimated CR1 standard error as if known. The literature benchmark assumes every 60+ minute commuter carries the hazard ratio reported for men riding in a car more than 10 hours a week, that it applies to both sexes and to mortality within the same year, and that non-commuters are unaffected; it is an upper-end illustration, not an estimate.
12. Applying sitting or driving dose-response estimates to commute time is an assumption; car time does not add one-for-one to total sitting (Ding 2014), and no study has linked road rage to cardiovascular events.

## 9. Limitations

This analysis is ecological and observational, and its associations cannot be read as effects of commuting on individuals. The tract outcomes are CDC PLACES estimates: crude, model-based prevalences for all adults 18+, produced by multilevel regression and poststratification from tract demographic composition. They are not measurements, are not age-specific, and regressing them on the same demographics is partly circular; here the covariates alone reproduce 81-97% of their variance, so the commute coefficients mostly reflect how commuting correlates with the parts of the PLACES prediction model that the covariates miss, and the model-based uncertainty of the outcomes is ignored. Exposure and outcome refer to different people: commute measures describe workers, whereas cardiovascular prevalence and mortality are dominated by older and often retired residents, and current commute is not lifetime exposure; residential sorting, the healthy-worker effect and migration (people who move outward for cheaper housing are not a random sample) can all produce inverse associations like those seen in 2015-2019. Commute duration is self-reported, top-coded travel time for all modes; it is not time spent driving, total sitting time or driving stress, and no measure of road rage enters any model. Age-specific mortality exists only for ages 35-64 and 65+, ends in 2019, and is model-smoothed, which removes within-county variation, understates uncertainty and distorts fixed-effects inference; the panel has only 14 clusters, wide intervals, minimum detectable effects several times larger than literature-implied effects, and commute regressors of which roughly half the identifying variation is sampling noise. The housing variable is a nominal, smoothed home-value index; year effects absorb common inflation in the panel, but tract-level income is nominal and top-coded, and the home-value-to-commute coefficients rest on small relative differences in county growth rates. The decomposition is a product of coefficients, not causal mediation. The 2020-2024 cross-section mixes pre- and post-pandemic commuting, with work-from-home shares several times the 2019 level, so its commuters are a differently selected group; the two PLACES releases differ in method, and only 1,523 of 2,251 2010-vintage tracts have stable boundaries, so cross-period tract comparisons are weak. Spatial weights treat over-water adjacency as contiguity, the spatial models assume a single spatial parameter for the whole region, and San Benito has no person-level data. Finally, half of the literature parameters behind the benchmark comparisons were read from abstracts only and are provisional, and the single driving-specific cardiovascular mortality estimate comes from one cohort of men.

## 10. Files

- [trends_table.csv]({{artifact:0f9636a7-3a05-4d9c-9360-45a376d309cf}}): changes 2010-2019, 2019-2024 (plus 2019-2021, 2010-2024) by county/region x age band x measure, with replicate-weight SEs; Zillow rows
- [trends_levels.csv]({{artifact:93f5d5ac-2e16-4d85-a1d7-9866dc2a6381}}): levels with SEs for 2010, 2019, 2021, 2024
- [trends_heterogeneity_tests.csv]({{artifact:97f27f26-8d87-4404-8edb-b728a6bdd9a3}}): age-band, core-vs-adjacent and county heterogeneity tests
- [tract_models.csv]({{artifact:a267e63f-1b60-46ee-9004-a247ec441467}}): 72 primary estimates: outcome x exposure x cross-section x estimator
- [tract_model_diagnostics.csv]({{artifact:3f4d6caa-f046-460b-8934-04ffa5d6bc90}}): Moran's I, LM tests, spatial parameters, AIC, favoured model
- [tract_sample_description.csv]({{artifact:ce478045-d55c-41fd-9808-c5728125f276}}): sample sizes, weights-matrix summary, means and SDs
- [panel_models.csv]({{artifact:123924fc-313d-4c3b-aa5f-e906c3dfe4b2}}): Model H, Model M and decomposition rows with CR1, wild-cluster and bootstrap intervals and MDEs
- [panel_analysis_data.csv]({{artifact:013bc315-8294-43be-bb49-2d3cc5ea308b}}): the 140 county-year analysis rows
- [panel_mde_benchmark.json]({{artifact:a0412222-71c3-42e7-909c-e9138faba5ac}}): literature benchmark used for the MDE comparison
- [trends_crosscheck.json]({{artifact:72283f02-0092-4039-b6e5-534e16c0ab08}}): agreement of the trend estimates with the delivered aggregate file
- [sensitivity_models.csv]({{artifact:3a6f8dba-50c1-423c-a77a-d926365bca04}}): all sensitivity estimates with comparison flags
- [sensitivity_change_summary.csv]({{artifact:07f22cea-6be6-4391-9abc-a720d04e995d}}): counts of sign and significance changes
- [sensitivity_samples.csv]({{artifact:4cf54509-2140-45a8-bc7e-12f0fdf98d9f}}): sample sizes per sensitivity specification
- [first_difference_tract_data.csv]({{artifact:46df2f9e-9a03-4068-a865-708d874ee533}}): differenced tract data used in S6
- [analysis_plan_prespecified.md]({{artifact:dfa921d6-6e33-4cbb-89ec-f160c7791a9b}}): the plan saved before fitting
- [01_trends.py]({{artifact:5c9fd94d-2beb-45a7-908b-2fe1e27c25d5}}), [tract_common.py]({{artifact:e6a2e054-630e-4c9f-9d1c-d714e2c41c2e}}), [02_tract_models.py]({{artifact:72c3040c-fb1f-4716-b3f1-b990724a6396}}), [03_panel_models.py]({{artifact:934d6c7e-be71-433a-ab43-275acd68adbc}}), [04_sensitivity.py]({{artifact:5f64840d-65c2-43df-82a6-efe900a42525}}), [05_write_report.py]({{artifact:f4de3db9-88bd-4cb5-ac3f-afcd94a9cbf4}}): analysis scripts (run in this order; 01, 03 and 05 need pandas/scipy/statsmodels, tract_common/02/04 also geopandas, libpysal, spreg, esda; resolved input paths are read from handoff/input_paths.json with keys tract, panel, pums, pcya, mort, rel, dose, zillow; TIGER/Line tl_2019_06_tract.zip and tl_2024_06_tract.zip from www2.census.gov/geo/tiger in tiger/)

Software: Python 3.11; pandas, numpy, scipy, statsmodels 0.15.0, geopandas 1.2.0, libpysal 4.14.1, spreg 1.9.0, esda 2.9.0. Seed 20261113.
