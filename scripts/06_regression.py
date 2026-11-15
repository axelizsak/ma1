"""
Step 3 - Link paralanguage, sentiment and topic to engagement.

Part 1 (this file, top): look at the engagement numbers before modelling.
Part 2 (below): the regression. Added once the outcome and predictors are decided.

Run from the ma1/ folder:  .venv/bin/python scripts/06_regression.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from chart_style import BRAND_COLOR, MUTED, SURFACE, TEXT_SOFT, title, use_style

ROOT = Path(__file__).resolve().parents[1]
BRANDS = ["Brewhaus", "Trailnorth"]

df = pd.read_csv(ROOT / "data" / "04_topic.csv", dtype={"id": str}, keep_default_na=False)
for outcome in ["like", "reply", "retweet"]:
    df[outcome + "_rate"] = df[outcome] / df["view"]          # engagement per view

reg = df[df["in_regression"]].copy()                           # 305 English originals with words
reg["log_like_rate"] = np.log(reg["like_rate"])                # no post in this set has 0 likes
reg["log_like"] = np.log(reg["like"])
reg["log_view"] = np.log(reg["view"])

# =============================================================================
# PART 1 - What does engagement look like?
# =============================================================================
print("PART 1 - ENGAGEMENT\n")
print("Median per post, with the middle half of the posts in brackets:")
rows = {}
for brand, posts in reg.groupby("brand"):
    def mid(col, pct=False):
        q1, med, q3 = posts[col].quantile([.25, .5, .75])
        return f"{med:.2%} ({q1:.2%} to {q3:.2%})" if pct else f"{med:,.0f} ({q1:,.0f} to {q3:,.0f})"
    rows[brand] = {"posts": len(posts), "views": mid("view"), "likes": mid("like"),
                   "like rate": mid("like_rate", True), "reply rate": mid("reply_rate", True),
                   "retweet rate": mid("retweet_rate", True)}
engagement = pd.DataFrame(rows)
print(engagement.to_string(), "\n")
engagement.to_csv(ROOT / "outputs" / "table_engagement.csv")

print("Shape of the distribution (skewness: 0 = symmetric, above 1 = a long tail of big values):")
print(reg.groupby("brand")[["like", "like_rate", "log_like_rate"]].skew().round(2).to_string(), "\n")

print("Do likes simply follow views? Slope of log(likes) on log(views); 1.00 = exactly proportional:")
for brand in BRANDS:
    fit = smf.ols("log_like ~ log_view", reg[reg["brand"] == brand]).fit()
    low, high = fit.conf_int().loc["log_view"]
    print(f"  {brand:<11} slope {fit.params['log_view']:.2f}  (95% CI {low:.2f} to {high:.2f})")

print("\nDo the three kinds of engagement move together? Correlation between the rates, within brand:")
for brand in BRANDS:
    c = reg[reg["brand"] == brand][["like_rate", "reply_rate", "retweet_rate"]].corr()
    print(f"  {brand:<11} likes-replies {c.iloc[0, 1]:+.2f}   likes-retweets {c.iloc[0, 2]:+.2f}   replies-retweets {c.iloc[1, 2]:+.2f}")

print("\nOutliers (like rate above the third quartile + 3 times the middle range, within brand):")
for brand in BRANDS:
    posts = reg[reg["brand"] == brand]
    q1, q3 = posts["like_rate"].quantile([.25, .75])
    far = posts[posts["like_rate"] > q3 + 3 * (q3 - q1)]
    for row in far.itertuples():
        print(f"  {row.id}  like rate {row.like_rate:.1%}  ({row.like:,} likes / {row.view:,} views)  {row.text[:90]}")

# --- Figure: like rate as it is, and on a log scale ---------------------------
use_style()
fig, axes = plt.subplots(2, 2, figsize=(10, 5.6), gridspec_kw={"hspace": 0.55, "wspace": 0.16})
for r, brand in enumerate(BRANDS):
    posts = reg[reg["brand"] == brand]
    panels = [(100 * posts["like_rate"], "Like rate (% of views)", False),
              (100 * posts["like_rate"], "Like rate (% of views, log scale)", True)]
    for c, (values, label, log) in enumerate(panels):
        ax = axes[r, c]
        bins = np.geomspace(values.min(), values.max(), 22) if log else np.linspace(0, values.max(), 22)
        ax.hist(values, bins=bins, color=BRAND_COLOR[brand], edgecolor=SURFACE, linewidth=1.5)
        if log:
            ax.set_xscale("log")
            ticks = [t for t in [0.5, 1, 2, 3, 5, 10] if values.min() * 0.9 <= t <= values.max() * 1.1]
            ax.set_xticks(ticks, [f"{t:g}%" for t in ticks])
            ax.minorticks_off()
        else:
            ax.xaxis.set_major_formatter(lambda v, _: f"{v:g}%")
        ax.set_title(f"{brand} ({len(posts)} posts)", loc="left", fontsize=11, color=TEXT_SOFT)
        ax.set_xlabel(label, fontsize=9.5, color=MUTED)
        ax.set_ylabel("posts" if c == 0 else "", fontsize=9.5, color=MUTED)
        ax.axvline(values.median(), color="#0b0b0b", linewidth=1)
        ax.annotate(f"median {values.median():.1f}%", (values.median(), ax.get_ylim()[1]), xytext=(4, -2),
                    textcoords="offset points", fontsize=9, color=TEXT_SOFT, va="top",
                    bbox={"facecolor": SURFACE, "edgecolor": "none", "pad": 1.5})
title(fig, "Like rates have a long tail; on a log scale they are symmetric",
      "Likes per view for the 305 posts in the regression. Left: as it is. Right: same data, log scale.", y=0.93)
fig.savefig(ROOT / "outputs" / "fig_engagement_like_rate.png")
plt.close(fig)
print("\nSaved outputs/fig_engagement_like_rate.png and outputs/table_engagement.csv")

# =============================================================================
# PART 2 - The regression
# =============================================================================
# Outcome: log of the like rate (likes / views). On the log scale a coefficient B
# reads as a percentage: 100 * (exp(B) - 1) = % more (or fewer) likes per view.
#
# Eight predictors (see decisions_log.md, Step 3):
#   trailnorth        1 = Trailnorth, 0 = Brewhaus (reference)
#   has_face          at least one face emoji
#   has_nonface       at least one non-face emoji
#   has_exclam        at least one "!"
#   vader_text_only   tone of the words, -1 to +1 (VADER on the text without emojis)
#   topic_emotional   topic Emotional   (reference = Informational)
#   topic_mixed       topic Mixed       (reference = Informational)
#   trailnorth:has_nonface   interaction: is the non-face effect different for Trailnorth?
from statsmodels.stats.outliers_influence import variance_inflation_factor

from chart_style import GRID, TEXT
from post_templates import template_of

MAIN =("trailnorth + has_face + has_nonface + has_exclam + vader_text_only"
        " + topic_emotional + topic_mixed + trailnorth:has_nonface")
NAMES = {
    "Intercept": "Baseline: Brewhaus, Informational, no emoji, no '!', neutral words",
    "trailnorth": "Trailnorth (vs Brewhaus), posts without non-face emoji",
    "has_face": "Face emoji (at least one)",
    "has_nonface": "Non-face emoji (at least one), for Brewhaus",
    "has_exclam": "Exclamation mark (at least one)",
    "vader_text_only": "Tone of the words (per +1 point of VADER)",
    "topic_emotional": "Topic Emotional (vs Informational)",
    "topic_mixed": "Topic Mixed (vs Informational)",
    "trailnorth:has_nonface": "Non-face emoji: extra effect for Trailnorth",
    "trailnorth:has_face": "Face emoji: extra effect for Trailnorth",
    "log_view": "log(views)",
}


def prepare(posts):
    posts = posts.copy()
    posts["trailnorth"] = (posts["brand"] == "Trailnorth").astype(int)
    posts["topic_emotional"] = (posts["topic"] == "Emotional").astype(int)
    posts["topic_mixed"] = (posts["topic"] == "Mixed").astype(int)
    for outcome in ["like", "reply", "retweet"]:
        posts[f"log_{outcome}_rate"] = np.log(posts[f"{outcome}_rate"])
    posts["log_like"], posts["log_view"] = np.log(posts["like"]), np.log(posts["view"])
    return posts


def fit(posts, formula):
    # HC3 = standard errors that stay valid when the spread of the outcome is uneven
    return smf.ols(formula, prepare(posts)).fit(cov_type="HC3")


def as_table(model):
    ci = model.conf_int()
    out = pd.DataFrame({
        "B": model.params, "CI low": ci[0], "CI high": ci[1], "p": model.pvalues,
        "% change": 100 * (np.exp(model.params) - 1),
        "% low": 100 * (np.exp(ci[0]) - 1), "% high": 100 * (np.exp(ci[1]) - 1),
    })
    out["reliable"] = np.where(out["p"] < 0.05, "yes", "no")
    out.loc["Intercept", ["% change", "% low", "% high"]] = np.nan     # the baseline is a level, not a change
    return out.rename(index=NAMES)


print("\n\nPART 2 - REGRESSION\n")
main = fit(reg, "log_like_rate ~ " + MAIN)
table = as_table(main)
print(f"Outcome: log(like rate). Posts: {int(main.nobs)}. R2 = {main.rsquared:.2f} (adjusted {main.rsquared_adj:.2f}).")
print(f"Baseline like rate: {np.exp(main.params['Intercept']):.2%}\n")
print(table.round(3).to_string())

# The non-face effect for each brand (for Trailnorth: main effect + interaction)
trail = main.t_test("has_nonface + trailnorth:has_nonface = 0")
b, (low, high) = trail.effect[0], trail.conf_int()[0]
brew_low, brew_high = main.conf_int().loc["has_nonface"]
by_brand = pd.DataFrame({
    "B": [main.params["has_nonface"], b], "CI low": [brew_low, low], "CI high": [brew_high, high],
    "p": [main.pvalues["has_nonface"], float(trail.pvalue)],
}, index=["Non-face emoji, Brewhaus", "Non-face emoji, Trailnorth"])
for col, src in [("% change", "B"), ("% low", "CI low"), ("% high", "CI high")]:
    by_brand[col] = 100 * (np.exp(by_brand[src]) - 1)
by_brand["reliable"] = np.where(by_brand["p"] < 0.05, "yes", "no")
print("\nNon-face emoji, brand by brand:")
print(by_brand.round(3).to_string())

# Is the pattern the same for both brands?  The simplest check: the same model for each brand alone.
PER_BRAND = "has_face + has_nonface + has_exclam + vader_text_only + topic_emotional + topic_mixed"
SHORT = {"has_face": "Face emoji", "has_nonface": "Non-face emoji", "has_exclam": "Exclamation mark",
         "vader_text_only": "Tone of the words (per +1 point of VADER)",
         "topic_emotional": "Topic Emotional (vs Informational)", "topic_mixed": "Topic Mixed (vs Informational)"}
columns = {}
for brand in BRANDS:
    posts = prepare(reg[reg["brand"] == brand])
    model = fit(posts, "log_like_rate ~ " + PER_BRAND)
    ci = 100 * (np.exp(model.conf_int()) - 1)
    cells = {"posts in the model": str(len(posts))}
    for term, label in SHORT.items():
        star = " *" if model.pvalues[term] < 0.05 else ""
        cells[label] = f"{100 * (np.exp(model.params[term]) - 1):+.0f}% ({ci.loc[term, 0]:+.0f} to {ci.loc[term, 1]:+.0f}){star}"
        cells[label + " - posts with it"] = str(int(posts[term].sum())) if term != "vader_text_only" else ""
    columns[brand] = cells
per_brand = pd.DataFrame(columns)
print("\nEach brand on its own (% difference in like rate, 95% interval; * = reliable):")
print(per_brand.to_string())
per_brand.to_csv(ROOT / "outputs" / "table_regression_per_brand.csv")

# --- Do the predictors overlap? -------------------------------------------------
design = pd.DataFrame(main.model.exog, columns=main.model.exog_names)
vif = pd.Series({NAMES[c]: variance_inflation_factor(design.values, i)
                 for i, c in enumerate(design.columns) if c != "Intercept"}).round(2)
print("\nVIF (1 = no overlap; above 5 = a problem):")
print(vif.to_string())
print("\nStrongest correlations between predictors:")
corr = design.drop(columns="Intercept").corr()
pairs = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1)).stack().sort_values(key=abs, ascending=False)
print(pairs.head(6).round(2).to_string())

# --- Does the result hold?  Same model, changed one thing at a time ---------------
no_outliers = reg[~reg["id"].isin(["BRW-0022", "TRN-0098"])]
with_emoji_only = df[df["in_robustness"]]
reg_media = reg.assign(has_media=(reg["media"] != "none").astype(int))
# posts built on the same template are not independent: let the standard errors know
prepared = prepare(reg)
template_id = pd.factorize(prepared["brand"] + "|" + prepared["text"].map(template_of))[0]
clustered = smf.ols("log_like_rate ~ " + MAIN, prepared).fit(cov_type="cluster", cov_kwds={"groups": template_id})
checks = {
    "Main model": main,
    "Standard errors grouped by template": clustered,
    "log(likes) with log(views) as control": fit(reg, "log_like ~ " + MAIN + " + log_view"),
    "Without the 2 outliers": fit(no_outliers, "log_like_rate ~ " + MAIN),
    "With the 21 emoji-only posts": fit(with_emoji_only, "log_like_rate ~ " + MAIN),
    "Adding: post has a photo, video or gif": fit(reg_media, "log_like_rate ~ " + MAIN + " + has_media"),
    "Adding: brand x face emoji (5 Trailnorth posts!)": fit(reg, "log_like_rate ~ " + MAIN + " + trailnorth:has_face"),
    "Outcome: reply rate": fit(reg, "log_reply_rate ~ " + MAIN),
    "Outcome: retweet rate": fit(reg, "log_retweet_rate ~ " + MAIN),
}
show = ["has_face", "has_nonface", "trailnorth:has_nonface", "has_exclam", "vader_text_only",
        "topic_emotional", "topic_mixed", "trailnorth:has_face", "log_view"]
rows = {}
for name, model in checks.items():
    cells = {"posts": int(model.nobs), "R2": round(model.rsquared, 2)}
    for term in show:
        if term in model.params:
            star = "*" if model.pvalues[term] < 0.05 else ""
            cells[NAMES[term]] = f"{model.params[term]:+.2f}{star}"
    rows[name] = cells
check_table = pd.DataFrame(rows).T.fillna("")
print("\nChecks (B for each predictor; * = p < 0.05):")
print(check_table.T.to_string())

table.round(4).to_csv(ROOT / "outputs" / "table_regression.csv")
by_brand.round(4).to_csv(ROOT / "outputs" / "table_regression_nonface_by_brand.csv")
check_table.to_csv(ROOT / "outputs" / "table_regression_checks.csv")
vif.to_csv(ROOT / "outputs" / "table_regression_vif.csv", header=["VIF"])

# --- Figure: the effects, in % of like rate ----------------------------------------
effects = pd.concat([
    table.loc[[NAMES["has_face"]]],
    by_brand,
    table.loc[[NAMES["has_exclam"], NAMES["vader_text_only"], NAMES["topic_emotional"], NAMES["topic_mixed"]]],
])
labels = ["Face emoji", "Non-face emoji, Brewhaus", "Non-face emoji, Trailnorth", "Exclamation mark",
          "More positive words (+1 VADER)", "Topic Emotional (vs Informational)", "Topic Mixed (vs Informational)"]
colors = [TEXT, BRAND_COLOR["Brewhaus"], BRAND_COLOR["Trailnorth"], TEXT, TEXT, TEXT, TEXT]

fig, ax = plt.subplots(figsize=(9.5, 4.6))
ax.grid(False)
ax.axvline(0, color=GRID, linewidth=1)
right = effects["% high"].max()
for y, (row, label, color) in enumerate(zip(effects.itertuples(), labels, colors)):
    pct, low, high, sure = row[5], row[6], row[7], row.reliable == "yes"
    ax.plot([low, high], [y, y], color=color, linewidth=2, solid_capstyle="round", alpha=1 if sure else 0.45)
    ax.plot(pct, y, "o", markersize=10, markeredgewidth=2, markeredgecolor=SURFACE if sure else color,
            markerfacecolor=color if sure else SURFACE)
    ax.text(right + 6, y, f"{pct:+.0f}%  ({low:+.0f} to {high:+.0f})", va="center", fontsize=10, color=TEXT)
ax.set_yticks(range(len(labels)), labels, fontsize=10.5, color=TEXT)
ax.invert_yaxis()
ax.set_xlim(effects["% low"].min() - 6, right + 6)
ax.xaxis.set_major_formatter(lambda v, _: f"{v:+.0f}%" if v else "0%")
ax.set_xlabel("Difference in like rate, other things equal (dot = estimate, line = 95% confidence interval)",
              fontsize=9.5, color=MUTED)
ax.plot([], [], "o", color=TEXT, markersize=8, markeredgecolor=SURFACE, label="reliable (interval does not cross 0)")
ax.plot([], [], "o", markerfacecolor=SURFACE, markeredgecolor=TEXT, markeredgewidth=2, markersize=8, label="not reliable")
ax.legend(loc="upper center", bbox_to_anchor=(0.4, -0.2), ncol=2, fontsize=9.5)
title(fig, "What goes with more likes per view", f"Regression on {int(main.nobs)} posts of Brewhaus and Trailnorth. "
      "Associations, not causes.", x=-0.2, y=0.9)
fig.savefig(ROOT / "outputs" / "fig_regression_effects.png")
plt.close(fig)
print("\nSaved outputs/table_regression*.csv and outputs/fig_regression_effects.png")
