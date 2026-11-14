suppressPackageStartupMessages({library(ggplot2); library(dplyr); library(readr); library(patchwork); library(ggtext); library(scales); library(jsonlite)})

dd <- "fig4_data"
fam <- "Arial"
col_cls <- c("Large metro, central"="#2F4B7C", "Large metro, suburban"="#6FA8DC",
             "Medium or small metro"="#9E9E9E", "Micropolitan"="#E8CF8F", "Rural (noncore)"="#C48E1E")
red <- "#C8402A"; blue <- "#1F4E9A"
fmt <- function(x) sub("-", "\u2212", formatC(x, format="f", digits=1))
ci  <- function(p, lo, hi) sprintf("%s (%s to %s)", fmt(p), fmt(lo), fmt(hi))

base <- theme_classic(base_size = 8.5, base_family = fam) +
  theme(axis.line = element_line(linewidth = 0.4), axis.ticks = element_line(linewidth = 0.4),
        plot.title = element_text(size = 9, face = "plain", hjust = 0, margin = margin(b = 4)),
        plot.title.position = "plot",
        legend.key.size = unit(3.2, "mm"), legend.text = element_text(size = 7.5),
        legend.title = element_blank(), legend.background = element_blank(),
        plot.tag = element_text(size = 12, face = "bold"))

## ---------------- panel a -------------------------------------------------
pa <- read_csv(file.path(dd, "panel_a.csv"), show_col_types = FALSE) |>
  mutate(cls = factor(cls, levels = names(col_cls)))
pam <- read_csv(file.path(dd, "panel_a_medians.csv"), show_col_types = FALSE) |>
  mutate(cls = factor(cls, levels = names(col_cls)))
p_a <- ggplot(pa, aes(car_hours_wk_per_adult16, mort_cvd_35_64)) +
  geom_point(aes(colour = cls, size = pop_35_64), alpha = 0.45, stroke = 0) +
  geom_point(data = pam, aes(x, y, fill = cls), shape = 21, size = 3.2, stroke = 1.1, colour = "black", show.legend = FALSE) +
  scale_colour_manual(values = col_cls, guide = guide_legend(override.aes = list(size = 2.6, alpha = 1), order = 1)) +
  scale_fill_manual(values = col_cls) +
  scale_size_area(max_size = 9, guide = "none") +
  scale_y_log10(breaks = c(50, 100, 200, 400), limits = c(28, 520)) +
  scale_x_continuous(breaks = seq(0.5, 3.5, 0.5), limits = c(0.4, 3.7)) +
  annotate("point", x = 0.55, y = 42, shape = 21, size = 3.2, stroke = 1.1, fill = "white") +
  annotate("text", x = 0.66, y = 42, label = "class median (population-weighted)", hjust = 0, size = 2.6, family = fam) +
  labs(x = "Car-commute hours per adult per week",
       y = "Cardiovascular deaths per 100,000,\nages 35\u201364 (log scale)",
       title = "Before adjustment: long-commute suburbs have the\nlowest working-age cardiovascular mortality") +
  base + theme(legend.position = c(0.80, 0.86), legend.key.spacing.y = unit(0.4, "mm"))

## ---------------- panel b -------------------------------------------------
pb  <- read_csv(file.path(dd, "panel_b.csv"), show_col_types = FALSE)
pbb <- read_csv(file.path(dd, "panel_b_bins.csv"), show_col_types = FALSE)
sl  <- fromJSON(file.path(dd, "slope.json"))
xl <- seq(-0.9, 0.9, length.out = 50)
p_b <- ggplot(pb, aes(resid_car_35_64_w, y_pct)) +
  geom_point(colour = "grey72", size = 0.5, alpha = 0.7, stroke = 0) +
  geom_hline(yintercept = 0, colour = "grey45", linewidth = 0.3) +
  geom_line(data = data.frame(x = xl, y = 100 * (exp(sl$b * xl) - 1)), aes(x, y), colour = red, linewidth = 0.9) +
  geom_point(data = pbb, aes(x, y), size = 2.3, colour = "black") +
  annotate("text", x = 0.88, y = 13, label = sprintf("slope %s%% per hour\n(95%% CI \u221211.1 to +2.4)", fmt(sl$pct)),
           colour = red, hjust = 1, size = 2.7, family = fam, lineheight = 0.95) +
  coord_cartesian(xlim = c(-1, 1), ylim = c(-60, 60)) +
  scale_y_continuous(breaks = seq(-60, 60, 20)) +
  labs(x = "Car-commute hours per week, residual after adjustment",
       y = "Mortality residual after\nadjustment (%, ages 35\u201364)",
       title = "After adjustment for socioeconomic composition,\nrurality, density and state: no gradient remains") +
  base

## ---------------- forest helpers ------------------------------------------
forest_theme <- base + theme(axis.title.y = element_blank(), axis.line.y = element_blank(), axis.ticks.y = element_blank(),
                             axis.text.y = element_markdown(size = 7.8, colour = "black", hjust = 1),
                             panel.grid.major.y = element_blank(),
                             legend.position = "none")
table_theme <- theme_void(base_family = fam) +
  theme(plot.title = element_text(size = 7.8, hjust = 0.5, face = "plain", margin = margin(b = 4)),
        plot.title.position = "plot")

## ---------------- panel c: adjustment ladder ------------------------------
pc <- read_csv(file.path(dd, "panel_c.csv"), show_col_types = FALSE)
pc$label <- sub("^\\+ ", "&#43; ", pc$label)
lev_c <- unique(pc$label)
pc <- pc |> mutate(label = factor(label, levels = rev(lev_c)),
                   yb = as.numeric(label), ypos = yb + ifelse(weighting == "pop_weighted", 0.18, -0.18),
                   wt = factor(ifelse(weighting == "pop_weighted", "Population-weighted", "Unweighted"),
                               levels = c("Population-weighted", "Unweighted")),
                   txt = ci(pct, pct_lo, pct_hi))
ylab_c <- setNames(ifelse(lev_c == "&#43; rurality, density, state (primary)",
                          "**&#43; rurality, density, state**<br><span style='font-size:6.5pt'>(primary model)</span>", lev_c), lev_c)
nrow_c <- length(lev_c)
p_c <- ggplot(pc) +
  annotate("rect", xmin = -Inf, xmax = Inf, ymin = nrow_c - which(lev_c == "&#43; rurality, density, state (primary)") + 1 - 0.5,
           ymax = nrow_c - which(lev_c == "&#43; rurality, density, state (primary)") + 1 + 0.5, fill = "grey93") +
  annotate("rect", xmin = 0, xmax = Inf, ymin = -Inf, ymax = Inf, fill = red, alpha = 0.06) +
  geom_vline(xintercept = 0, linewidth = 0.5, colour = "grey30") +
  geom_errorbar(aes(y = ypos, xmin = pct_lo, xmax = pct_hi, group = wt), width = 0.22, linewidth = 0.55, colour = "black",
                orientation = "y") +
  geom_point(aes(y = ypos, x = pct, fill = wt), shape = 21, size = 2.5, stroke = 0.7, colour = "black") +
  scale_fill_manual(values = c("Population-weighted" = "black", "Unweighted" = "white")) +
  annotate("text", x = -0.8, y = nrow_c + 0.78, label = "\u2190 lower mortality where commutes are longer", hjust = 1, size = 2.6, family = fam, colour = "grey25") +
  annotate("text", x = 0.8, y = nrow_c + 0.78, label = "higher \u2192", hjust = 0, size = 2.6, family = fam, colour = red) +
  annotate("point", x = -36, y = 0.42, shape = 21, size = 2.3, fill = "black") +
  annotate("text", x = -35, y = 0.42, label = "population-weighted", hjust = 0, size = 2.6, family = fam) +
  annotate("point", x = -36, y = -0.03, shape = 21, size = 2.3, fill = "white") +
  annotate("text", x = -35, y = -0.03, label = "unweighted", hjust = 0, size = 2.6, family = fam) +
  scale_y_continuous(breaks = seq_len(nrow_c), labels = ylab_c[rev(lev_c)], expand = c(0, 0)) +
  scale_x_continuous(breaks = seq(-40, 10, 10), labels = function(x) sub("-", "\u2212", x)) +
  coord_cartesian(xlim = c(-38, 8), ylim = c(-0.35, nrow_c + 1.1), clip = "off") +
  labs(x = "Difference in cardiovascular mortality, ages 35\u201364 (% per extra car-commute hour per adult per week)",
       title = "The raw inverse association largely disappears once socioeconomic composition is adjusted for") +
  forest_theme
t_c <- ggplot(pc) +
  geom_text(aes(x = 0, y = ypos, label = txt), hjust = 0, size = 2.55, family = fam) +
  scale_y_continuous(expand = c(0, 0)) + coord_cartesian(ylim = c(-0.35, nrow_c + 1.1), clip = "off") +
  scale_x_continuous(limits = c(0, 1), expand = c(0, 0)) +
  labs(title = "% (95% CI)") + table_theme
row_c <- (p_c | t_c) + plot_layout(widths = c(1, 0.30))

## ---------------- panel d: pre-specified tests ----------------------------
pd <- read_csv(file.path(dd, "panel_d.csv"), show_col_types = FALSE)
bm <- read_csv(file.path(dd, "benchmarks.csv"), show_col_types = FALSE)
sit <- bm |> filter(grepl("sitting", benchmark)); drv <- bm |> filter(benchmark == "driving_DR003_top12")
pd <- pd |> mutate(grp = factor(ifelse(group == "test", "Pre-specified tests, ages 35\u201364 (working age)",
                                       "Falsification: ages 65+ (few commuters; no effect expected)"),
                                levels = c("Pre-specified tests, ages 35\u201364 (working age)",
                                           "Falsification: ages 65+ (few commuters; no effect expected)")))
# y positions with a gap between groups
pd <- pd |> mutate(idx = rev(seq_len(n())), ypos = ifelse(group == "test", idx + 1.0, idx), col = ifelse(group == "test", "black", "grey50"),
                   txt = ci(pct, pct_lo, pct_hi))
lab_d <- pd$label; lab_d[pd$primary] <- paste0("**", lab_d[pd$primary], "**")
ytop <- max(pd$ypos)
p_d <- ggplot(pd) +
  annotate("rect", xmin = -Inf, xmax = Inf, ymin = pd$ypos[pd$primary] - 0.5, ymax = pd$ypos[pd$primary] + 0.5, fill = "grey93") +
  annotate("rect", xmin = 0, xmax = Inf, ymin = -Inf, ymax = Inf, fill = red, alpha = 0.06) +
  annotate("rect", xmin = drv$pct_lo, xmax = drv$pct_hi, ymin = -Inf, ymax = Inf, fill = red, alpha = 0.16) +
  geom_vline(xintercept = drv$pct, colour = red, linewidth = 0.6, linetype = "22") +
  geom_vline(xintercept = mean(c(min(sit$pct_lo), max(sit$pct_hi))), colour = blue, linewidth = 0.6, linetype = "22") +
  geom_vline(xintercept = 0, linewidth = 0.5, colour = "grey30") +
  geom_errorbar(aes(y = ypos, xmin = pct_lo, xmax = pct_hi, colour = col), width = 0.22, linewidth = 0.55, orientation = "y") +
  geom_point(aes(y = ypos, x = pct, fill = col), shape = 21, size = 2.5, stroke = 0.7, colour = "black") +
  scale_colour_identity() + scale_fill_identity() +
  # benchmark labels
  annotate("label", x = 1.1, y = ytop + 2.75, label = sprintf("expected if driving time carried the\ncohort-study risk: +%s%% (%s to %s)", fmt(drv$pct), fmt(drv$pct_lo), fmt(drv$pct_hi)),
           hjust = 0, size = 2.5, family = fam, colour = red, fill = "white", linewidth = 0, lineheight = 0.95) +
  annotate("label", x = -0.5, y = ytop + 2.75, label = "expected from the extra\nsitting alone: +0.1 to +0.3%", hjust = 1, size = 2.5, family = fam, colour = blue, fill = "white", linewidth = 0, lineheight = 0.95) +
  annotate("text", x = -0.7, y = ytop + 1.7, label = "\u2190 lower mortality where commutes are longer", hjust = 1, size = 2.6, family = fam, colour = "grey25") +
  annotate("text", x = 0.7, y = ytop + 1.7, label = "higher \u2192", hjust = 0, size = 2.6, family = fam, colour = red) +
  scale_y_continuous(breaks = c(pd$ypos, ytop + 0.72, max(pd$ypos[pd$group == "fals"]) + 0.85),
                     labels = c(lab_d, "**Pre-specified tests, ages 35\u201364**",
                                "<span style='color:#595959'>**Falsification, ages 65+**<br><span style='font-size:6.5pt'>(few commuters, so no effect expected)</span></span>"), expand = c(0, 0)) +
  scale_x_continuous(breaks = seq(-15, 10, 5), labels = function(x) sub("-", "\u2212", x)) +
  coord_cartesian(xlim = c(-15.5, 9.5), ylim = c(0.4, ytop + 3.4), clip = "off") +
  labs(x = "Difference in cardiovascular mortality (% per extra car-commute hour per adult per week)",
       title = "No pre-specified test finds higher working-age mortality where car-commute time is longer") +
  forest_theme
t_d <- ggplot(pd) +
  geom_text(aes(x = 0, y = ypos, label = txt, colour = col), hjust = 0, size = 2.55, family = fam) +
  scale_colour_identity() +
  scale_y_continuous(expand = c(0, 0)) + coord_cartesian(ylim = c(0.4, ytop + 3.4), clip = "off") +
  scale_x_continuous(limits = c(0, 1), expand = c(0, 0)) +
  labs(title = "% (95% CI)") + table_theme
row_d <- (p_d | t_d) + plot_layout(widths = c(1, 0.30))

## ---------------- assemble --------------------------------------------------
top <- wrap_elements(full = ((p_a + labs(tag = "a")) | (p_b + labs(tag = "b"))) & theme(plot.tag = element_text(size = 12, face = "bold", family = fam)))
fig <- (top / row_c / row_d) + plot_layout(heights = c(1.25, 0.78, 1.05)) +
  plot_annotation(tag_levels = list(c("", "c", "", "d", ""))) &
  theme(plot.tag = element_text(size = 12, face = "bold", family = fam), plot.margin = margin(4, 4, 4, 4))
ragg::agg_png("fig4_national_v3.png", width = 185, height = 235, units = "mm", res = 300, background = "white")
print(fig); invisible(dev.off())
cairo_pdf("fig4_national_v3.pdf", width = 185/25.4, height = 235/25.4, family = fam)
print(fig); invisible(dev.off())
cat("done\n")

