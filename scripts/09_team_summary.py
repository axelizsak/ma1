"""
A one-page summary for the team, in black and white, plus the technical regression output as an image.

  outputs/team_summary_one_page.pdf   how the analysis works and what it found, in simple words
  outputs/regression_output.png       the full statsmodels output of the regression

The numbers are read from the data and the regression tables, not typed by hand.
Run 06_regression.py first.

Run from the ma1/ folder:  .venv/bin/python scripts/09_team_summary.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
PAGE_URL = "https://axelizsak.github.io/ma1/"

# =============================================================================
# 1. The technical regression output, as an image
# =============================================================================
summary = (OUT / "regression_summary.txt").read_text(encoding="utf-8")
lines = summary.splitlines()
fig = plt.figure(figsize=(0.092 * max(len(line) for line in lines) + 0.4, 0.165 * len(lines) + 0.4), facecolor="white")
fig.text(0.02, 0.98, summary, family="monospace", fontsize=9, color="black", va="top", ha="left")
fig.savefig(OUT / "regression_output.png", dpi=200, facecolor="white", bbox_inches="tight", pad_inches=0.25)
plt.close(fig)

# =============================================================================
# 2. The numbers quoted on the page
# =============================================================================
df = pd.read_csv(ROOT / "data" / "04_topic.csv", dtype={"id": str}, keep_default_na=False)
reg = df[df["in_regression"]]
n = df.groupby("brand").size()
with_emoji = (100 * df.groupby("brand")["has_emoji"].mean()).round().astype(int)
trail_faces = int(reg[reg["brand"] == "Trailnorth"]["has_face"].sum())
corrected = int(df["topic_corrected"].sum())

main = pd.read_csv(OUT / "table_regression.csv", index_col=0)
nonface = pd.read_csv(OUT / "table_regression_nonface_by_brand.csv", index_col=0)
effects = pd.concat([main, nonface])
ROWS = {  # row in the regression tables -> wording on the page
    "Topic Emotional (vs Informational)": "Emotional topic",
    "Tone of the words (per +1 point of VADER)": "More positive words",
    "Face emoji (at least one)": "Face emoji",
    "Non-face emoji, Trailnorth": "Non-face emoji, Trailnorth",
    "Non-face emoji, Brewhaus": "Non-face emoji, Brewhaus",
    "Topic Mixed (vs Informational)": "Mixed topic",
    "Exclamation mark (at least one)": "Exclamation mark",
}
table_rows = sorted(((label, effects.loc[key, "% change"], effects.loc[key, "reliable"]) for key, label in ROWS.items()),
                    key=lambda row: -row[1])

# =============================================================================
# 3. The page
# =============================================================================
BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=9.6, leading=12.6, textColor=colors.black)
HEAD = ParagraphStyle("head", parent=BODY, fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=7, spaceAfter=3)
TITLE = ParagraphStyle("title", parent=BODY, fontName="Helvetica-Bold", fontSize=15, leading=18)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8.6, leading=11)


def bullets(items, numbered=False):
    return ListFlowable([ListItem(Paragraph(text, BODY), leftIndent=12) for text in items],
                        bulletType="1" if numbered else "bullet", bulletFontSize=9.6, leftIndent=12, start=None if numbered else "-")


story = [
    Paragraph("How our analysis works and what it found", TITLE),
    Paragraph("Main Data Assignment 1: Brewhaus vs Trailnorth on X. One page for the team, 16 November 2026.", SMALL),

    Paragraph("How it works", HEAD),
    Paragraph("Everything is done by short Python scripts, run one after the other.", BODY),
    bullets([
        f"<b>Select.</b> We keep the posts our two brands wrote themselves: {len(df)} posts "
        f"(Brewhaus {n['Brewhaus']}, Trailnorth {n['Trailnorth']}). Retweets are left out.",
        "<b>Count the cues.</b> A Python script reads every post and counts the emojis: face (a smiley) or non-face "
        "(a boot, a mountain), used with the text, instead of a word, or alone. It also counts exclamation marks, "
        "CAPITALS and hashtags.",
        "<b>Score the tone.</b> A sentiment tool (VADER, a Python library) scores how positive the words are.",
        "<b>Label the topic.</b> An AI (Claude) gives each post a topic with our definitions: Informational, Emotional "
        f"or Mixed. We checked it and corrected {corrected} labels.",
        "<b>Compare.</b> A regression, also run in Python, compares the posts: other things equal, which choices go "
        "with more likes per view?",
    ], numbered=True),

    Paragraph("What we found", HEAD),
    bullets([
        f"Brewhaus puts emojis in {with_emoji['Brewhaus']}% of its posts, mostly faces. Trailnorth in "
        f"{with_emoji['Trailnorth']}%, almost never faces: boots, mountains, trees.",
        "For both brands, Emotional posts and positive wording go with clearly more likes per view.",
        "For Brewhaus the face emoji goes with more likes. For Trailnorth it is the non-face emoji.",
        "Exclamation marks and Mixed posts make no reliable difference.",
    ]),

    Paragraph(f"Regression ({len(reg)} posts)", HEAD),
]

data = [["Compared with a similar post without it", "Effect on likes per view", "Sure?"]]
data += [[label, f"{effect:+.0f}%", sure] for label, effect, sure in table_rows]
table = Table(data, colWidths=[78 * mm, 44 * mm, 18 * mm], hAlign="LEFT")
table.setStyle(TableStyle([
    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9.6), ("FONT", (0, 1), (-1, -1), "Helvetica", 9.6),
    ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
    ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black), ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
    ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
    ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
]))
story += [
    table,
    Spacer(1, 4),
    Paragraph("How to read it: +39% is relative (a like rate of 1.00% becomes 1.39%). \"Sure? no\" means we cannot "
              "tell it apart from chance. \"More positive words\" is a big step, a full point on the VADER scale.", SMALL),

    Paragraph("Careful", HEAD),
    bullets([
        "These are links, not causes: each brand chose its own style.",
        f"Trailnorth has only {trail_faces} posts with a face emoji, so we cannot say faces would work for Trailnorth.",
    ]),

    Paragraph("Web page", HEAD),
    Paragraph(f"{PAGE_URL}<br/>Browse all {len(df)} posts and filter by brand, topic, emoji type and tone. Useful to "
              "find example posts for the slides and ideas for the two new posts. Its bars are simple medians, not the "
              "regression.", BODY),

    Paragraph("Charts", HEAD),
    Paragraph("Four images are ready for the slides: emoji repertoire, cues per brand, tone and topic, regression effects.", BODY),

    Paragraph("Still to do", HEAD),
    Paragraph("The 30 posts labelled by hand, to check the AI and the sentiment tool.", BODY),
]

pdf = OUT / "team_summary_one_page.pdf"
doc = SimpleDocTemplate(str(pdf), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=14 * mm,
                        title="How our analysis works and what it found", author="")
doc.build(story)
assert doc.page == 1, f"The summary no longer fits on one page ({doc.page} pages)"
print(f"Saved outputs/team_summary_one_page.pdf (1 page) and outputs/regression_output.png ({len(lines)} lines of output)")
