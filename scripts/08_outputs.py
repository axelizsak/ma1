"""
Step 4 - Files for the team: the data we used, slide-ready tables and charts.

  outputs/clean_data_used.xlsx    the 348 selected posts + every column we added (to upload on Canvas)
  outputs/tables_for_slides.xlsx  one sheet per table, easy to copy into PowerPoint
  outputs/fig_repertoire.png      the 10 most used emojis of each brand
  outputs/fig_paralanguage.png    cues and emoji usage per brand
  outputs/fig_tone_topic.png      tone and topic per brand

The regression tables and chart come from 06_regression.py (run it first).

Run from the ma1/ folder:  .venv/bin/python scripts/08_outputs.py
"""
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import Patch
from PIL import Image, ImageDraw, ImageFont

from chart_style import BRAND_COLOR, MUTED, SURFACE, TEXT, TEXT_SOFT, title, use_style

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
BRANDS = ["Brewhaus", "Trailnorth"]
TONE = "vader_label"       # tone used to describe the brands: VADER on the whole post, emojis included
EMOJI_FONT = "/System/Library/Fonts/Apple Color Emoji.ttc"   # macOS; without it the chart shows emoji names

df = pd.read_csv(ROOT / "data" / "04_topic.csv", dtype={"id": str}, keep_default_na=False)
for outcome in ["like", "reply", "retweet"]:
    df[outcome + "_rate"] = df[outcome] / df["view"]
df["log_like_rate"] = np.log(df["like_rate"].where(df["like"] > 0))   # empty for the one reply with 0 likes
reg = df[df["in_regression"]]


def pct(series):
    return (100 * series).round(1)


# =============================================================================
# 1. The data we used
# =============================================================================
COLUMNS = {
    # the raw columns come first, untouched
    "in_regression": "TRUE = used in the regression (original post, English, has words)",
    "in_robustness": "TRUE = used in the regression check that adds emoji-only posts",
    "emojis": "Every emoji in the post, in order (python emoji library)",
    "n_emoji": "Number of emojis (a combined emoji counts as one)",
    "n_face": "Number of face emojis (official Unicode subgroups 'face-...')",
    "n_nonface": "Number of other emojis (objects, hearts, hands, nature...)",
    "n_emoji_instead": "Number of emojis that stand where a word should be",
    "emoji_usage": "none / with text / instead of words / alone",
    "n_words": "Number of words (links, hashtags, @names and emojis are not words)",
    "n_exclam": "Number of exclamation marks",
    "n_caps_words": "Number of words in CAPITALS (AI, DM and PFC are not counted)",
    "n_hashtags": "Number of hashtags",
    "has_emoji": "1 = at least one emoji", "has_face": "1 = at least one face emoji",
    "has_nonface": "1 = at least one non-face emoji", "has_exclam": "1 = at least one '!'",
    "has_caps": "1 = at least one word in CAPITALS", "has_hashtag": "1 = at least one hashtag",
    "vader_compound": "VADER sentiment of the whole post, -1 to +1 (also reads emojis)",
    "vader_label": "positive (> 0.05) / neutral / negative (< -0.05), from vader_compound",
    "vader_text_only": "VADER on the post without its emojis = tone of the words. USED IN THE REGRESSION",
    "vader_text_only_label": "positive / neutral / negative, from vader_text_only",
    "textblob_polarity": "TextBlob polarity, -1 to +1 (words only)",
    "textblob_label": "positive / neutral / negative, from textblob_polarity",
    "roberta_score": "Twitter-RoBERTa: P(positive) - P(negative), -1 to +1",
    "roberta_label": "Twitter-RoBERTa: most likely label",
    "topic": "FINAL TOPIC: Informational / Emotional / Mixed (AI label + 5 hand corrections)",
    "topic_corrected": "1 = we changed the AI label by hand (see decisions_log.md, D8)",
    "ai_topic": "Topic given by the AI prompt (Claude), before corrections",
    "ai_reason": "The AI's one-line reason",
    "ai_batch": "Which batch of 25 posts the AI saw this post in",
    "zs_short": "Zero-shot topic (BART), labels = the short category names",
    "zs_short_score": "Zero-shot confidence for zs_short, 0 to 1",
    "zs_defined": "Zero-shot topic, labels = the full definitions",
    "zs_defined_score": "Zero-shot confidence for zs_defined, 0 to 1",
    "zs_info_score": "Zero-shot 'gives information' score, 0 to 1",
    "zs_emo_score": "Zero-shot 'uses humour, feelings or community' score, 0 to 1",
    "zs_two": "Zero-shot topic from the two scores above (Mixed when both are above 0.5)",
    "like_rate": "likes / views", "reply_rate": "replies / views", "retweet_rate": "retweets / views",
    "log_like_rate": "log(likes / views). WHAT THE REGRESSION EXPLAINS",
}
RAW = ["id", "created_at", "text", "lang", "post_type", "media", "like", "reply", "retweet", "view",
       "brand", "followers", "following", "total_tweets"]
clean = df[RAW + list(COLUMNS)]
rows_table = pd.read_csv(OUT / "table_step1_rows_before_after.csv", index_col=0)
guide = pd.DataFrame(
    [(c, "Raw column, unchanged (see the Codebook sheet of the original file)") for c in RAW]
    + list(COLUMNS.items()), columns=["column", "what it is"])
with pd.ExcelWriter(OUT / "clean_data_used.xlsx", engine="openpyxl") as writer:
    clean.to_excel(writer, sheet_name="Data", index=False)
    guide.to_excel(writer, sheet_name="Columns", index=False)
    rows_table.to_excel(writer, sheet_name="Rows before and after")
print(f"clean_data_used.xlsx: {len(clean)} posts, {clean.shape[1]} columns ({len(COLUMNS)} added)")

# =============================================================================
# 2. Tables for the slides
# =============================================================================
tables = {}
tables["Rows"] = rows_table

by_brand = df.groupby("brand")
para = pd.DataFrame({
    "Posts": by_brand.size(),
    "% posts with an emoji": pct(by_brand["has_emoji"].mean()),
    "% posts with a face emoji": pct(by_brand["has_face"].mean()),
    "% posts with a non-face emoji": pct(by_brand["has_nonface"].mean()),
    "Emojis per post": by_brand["n_emoji"].mean().round(2),
    "% posts with '!'": pct(by_brand["has_exclam"].mean()),
    "% posts with a word in CAPITALS": pct(by_brand["has_caps"].mean()),
    "% posts with a hashtag": pct(by_brand["has_hashtag"].mean()),
}).T
usage = pct(pd.crosstab(df["emoji_usage"], df["brand"], normalize="columns")).reindex(
    ["with text", "instead of words", "alone", "none"])
usage.index = ["% emoji with the text", "% emoji instead of a word", "% emoji alone (no words)", "% no emoji"]
tables["Paralanguage"] = pd.concat([para, usage])

tables["Repertoire"] = pd.read_csv(OUT / "table_repertoire.csv", index_col=0)

tone_rows = {}
for label, col, score in [("whole post (VADER)", "vader_label", "vader_compound"),
                          ("words only (VADER without emojis)", "vader_text_only_label", "vader_text_only")]:
    share = pct(pd.crosstab(df[col], df["brand"], normalize="columns"))
    for tone in ["positive", "neutral", "negative"]:
        tone_rows[f"% {tone}, {label}"] = share.loc[tone]
    tone_rows[f"Mean score, {label}"] = by_brand[score].mean().round(2)
tables["Tone"] = pd.DataFrame(tone_rows).T

topic_count = pd.crosstab(df["topic"], df["brand"]).reindex(["Informational", "Emotional", "Mixed"])
topic_share = pct(topic_count / topic_count.sum())
tables["Topic"] = pd.concat([topic_count.add_suffix(" (posts)"), topic_share.add_suffix(" (%)")], axis=1)

# how posts differ inside a brand, by topic (English originals, so the like rates are comparable)
g = reg.groupby(["brand", "topic"])
tables["Within brand by topic"] = pd.DataFrame({
    "Posts": g.size(),
    "% with a face emoji": pct(g["has_face"].mean()),
    "% with a non-face emoji": pct(g["has_nonface"].mean()),
    "Emojis per post": g["n_emoji"].mean().round(2),
    "% with '!'": pct(g["has_exclam"].mean()),
    "Mean tone of the words": g["vader_text_only"].mean().round(2),
    "Median like rate (%)": (100 * g["like_rate"].median()).round(2),
}).reindex([(b, t) for b in BRANDS for t in ["Informational", "Emotional", "Mixed"]])

g = df.groupby(["brand", "post_type"])
tables["Originals vs replies"] = pd.DataFrame({
    "Posts": g.size(),
    "% with an emoji": pct(g["has_emoji"].mean()),
    "% with a face emoji": pct(g["has_face"].mean()),
    "Emojis per post": g["n_emoji"].mean().round(2),
    "% with '!'": pct(g["has_exclam"].mean()),
    "Mean tone, whole post (VADER)": g["vader_compound"].mean().round(2),
    "Median like rate (%)": (100 * g["like_rate"].median()).round(2),
})

originals = df[df["in_robustness"]]          # original posts, English or emoji-only
g = originals.groupby(["brand", "emoji_usage"])
tables["Like rate by emoji usage"] = pd.DataFrame({
    "Posts": g.size(), "Median like rate (%)": (100 * g["like_rate"].median()).round(2),
}).reindex([(b, u) for b in BRANDS for u in ["none", "with text", "instead of words", "alone"]])

tables["Regression"] = pd.read_csv(OUT / "table_regression.csv", index_col=0)
tables["Regression per brand"] = pd.read_csv(OUT / "table_regression_per_brand.csv", index_col=0)
tables["Regression checks"] = pd.read_csv(OUT / "table_regression_checks.csv", index_col=0).T

with pd.ExcelWriter(OUT / "tables_for_slides.xlsx", engine="openpyxl") as writer:
    for name, table in tables.items():
        table.to_excel(writer, sheet_name=name)
        writer.sheets[name].column_dimensions["A"].width = 46
        for col in "BCDEFGHIJ":
            writer.sheets[name].column_dimensions[col].width = 22
for name in ["Paralanguage", "Tone", "Topic", "Within brand by topic", "Originals vs replies", "Like rate by emoji usage"]:
    print(f"\n--- {name} ---")
    print(tables[name].to_string())

# =============================================================================
# 3. Charts
# =============================================================================
use_style()


def emoji_picture(symbol, size=160):
    """Draw one emoji in colour (matplotlib cannot do it by itself)."""
    font = ImageFont.truetype(EMOJI_FONT, size)
    image = Image.new("RGBA", (size + 60, size + 60), (0, 0, 0, 0))
    ImageDraw.Draw(image).text((30, 30), symbol, font=font, embedded_color=True)
    return image.crop(image.getbbox())


# --- Chart 1: repertoire -------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(10, 4.9), gridspec_kw={"wspace": 0.22})
for ax, brand in zip(axes, BRANDS):
    uses = Counter(s for e in df[df["brand"] == brand]["emojis"] if e for s in e.split(" "))
    top = uses.most_common(10)
    total, counts = sum(uses.values()), [n for _, n in top]
    ax.barh(range(10), counts, height=0.6, color=BRAND_COLOR[brand])
    for y, (symbol, n) in enumerate(top):
        ax.text(n + max(counts) * 0.02, y, str(n), va="center", fontsize=10, color=TEXT)
        if Path(EMOJI_FONT).exists():
            ax.add_artist(AnnotationBbox(OffsetImage(emoji_picture(symbol), zoom=0.105), (0, y), xybox=(-15, 0),
                                         boxcoords="offset points", frameon=False, annotation_clip=False))
    ax.set_yticks([])
    ax.invert_yaxis()
    ax.set_xlim(0, max(counts) * 1.12)
    ax.set_xticks([])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    faces = pd.to_numeric(df[df["brand"] == brand]["n_face"]).sum() / total
    ax.set_title(f"{brand}\n{len(uses)} different emojis, {total} uses, {faces:.0%} are faces",
                 loc="left", fontsize=10.5, color=TEXT_SOFT, x=-0.07)
title(fig, "Brewhaus speaks in faces, Trailnorth in objects and landscapes",
      "The 10 most used emojis of each brand (number of uses in original posts and replies)", x=0.07, y=0.97)
fig.savefig(OUT / "fig_repertoire.png")
plt.close(fig)

# --- Chart 2: cues and emoji usage ------------------------------------------------
left = tables["Paralanguage"].loc[["% posts with an emoji", "% posts with a face emoji", "% posts with a non-face emoji",
                                   "% posts with '!'", "% posts with a word in CAPITALS", "% posts with a hashtag"]]
left.index = ["Any emoji", "Face emoji", "Non-face emoji", "Exclamation mark", "Word in CAPITALS", "Hashtag"]
right = usage.copy()
right.index = ["Emoji with the text", "Emoji instead of a word", "Emoji alone (no words)", "No emoji"]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"wspace": 0.55, "width_ratios": [6, 4.6]})
for ax, data, heading in [(axes[0], left, "Posts that contain..."), (axes[1], right, "How the emoji is used")]:
    y = np.arange(len(data))
    for k, brand in enumerate(BRANDS):
        values = data[brand].astype(float).values
        ax.barh(y + (k - 0.5) * 0.36, values, height=0.32, color=BRAND_COLOR[brand])
        for yy, v in zip(y + (k - 0.5) * 0.36, values):
            ax.text(v + 1.5, yy, f"{v:.0f}%", va="center", fontsize=9.5, color=TEXT)
    ax.set_yticks(y, data.index, fontsize=10.5, color=TEXT)
    ax.set_ylim(5.5, -0.5)                       # same six slots in both panels, so all bars are equally thick
    ax.set_xlim(0, 108)
    ax.set_xticks([])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_title(heading, loc="left", fontsize=10.5, color=TEXT_SOFT)
fig.legend(handles=[Patch(color=BRAND_COLOR[b], label=f"{b} ({(df['brand'] == b).sum()} posts)") for b in BRANDS],
           loc="lower left", bbox_to_anchor=(0.0, -0.04), ncol=2, fontsize=10)
title(fig, "Brewhaus uses almost every cue more, except hashtags", "Share of each brand's posts (originals and replies)",
      x=0.01, y=0.95)
fig.savefig(OUT / "fig_paralanguage.png")
plt.close(fig)

# --- Chart 3: tone and topic --------------------------------------------------------
# Each bar is 100% of a brand's posts, split into parts. Labels inside are white, or black on light fills.
PARTS = {
    "Tone of the post (VADER, emojis included)": (TONE, [("positive", "#2a78d6", "white"), ("neutral", "#c9c7be", TEXT),
                                                         ("negative", "#e34948", "white")]),
    "Topic (AI labels, checked by hand)": ("topic", [("Informational", "#1baf7a", "white"), ("Mixed", "#eda100", TEXT),
                                                     ("Emotional", "#6250d6", "white")]),
}
fig, axes = plt.subplots(2, 1, figsize=(9.5, 4.8), gridspec_kw={"hspace": 0.85})
for ax, (heading, (column, parts)) in zip(axes, PARTS.items()):
    share = pd.crosstab(df[column], df["brand"], normalize="columns") * 100
    for y, brand in enumerate(BRANDS):
        start = 0
        for name, color, ink in parts:
            width = share.loc[name, brand]
            ax.barh(y, width, left=start, height=0.62, color=color, edgecolor=SURFACE, linewidth=2)
            if width >= 5:
                ax.text(start + 1.2, y, f"{width:.0f}%", va="center", fontsize=10.5, color=ink, fontweight="bold")
            start += width
    ax.set_yticks(range(2), BRANDS, fontsize=11, color=TEXT)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_title(heading, loc="left", fontsize=10.5, color=TEXT_SOFT, pad=26)
    ax.legend(handles=[Patch(color=c, label=n) for n, c, _ in parts], loc="lower left", bbox_to_anchor=(-0.01, 1.0),
              ncol=3, fontsize=9.5, handlelength=1, columnspacing=1.4)
title(fig, "Brewhaus sounds more positive and spreads its topics; Trailnorth mostly informs",
      "Share of each brand's posts (203 Brewhaus, 145 Trailnorth; originals and replies)", x=0.01, y=0.99)
fig.savefig(OUT / "fig_tone_topic.png")
plt.close(fig)
print("\nSaved clean_data_used.xlsx, tables_for_slides.xlsx and 3 charts in outputs/")
