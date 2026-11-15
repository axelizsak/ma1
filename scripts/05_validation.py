"""
Step 2d - Check the automatic labels against 30 posts labelled by the team.

  make    picks 30 posts (15 per brand) and writes outputs/validation_30_posts.xlsx
          with empty columns team_topic, team_tone and comment. No tool label is in
          the file, so the team cannot be influenced.
  check   once the file is filled in: % agreement and Cohen's kappa between the
          team and each tool, for topic and for tone.

Run from the ma1/ folder:
  .venv/bin/python scripts/05_validation.py make
  .venv/bin/python scripts/05_validation.py check
"""
import sys
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation
from sklearn.metrics import cohen_kappa_score

from post_templates import template_of

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "outputs" / "validation_30_posts.xlsx"
KEY = ROOT / "data" / "05_validation_selection.csv"      # why each post was picked (not for the team)
PROMPT_EXAMPLES = {"BRW-0007", "TRN-0090", "BRW-0005"}   # their label is given in the AI prompt
SEED = 2026

TOPICS = ["Informational", "Emotional", "Mixed"]
TONES = ["positive", "neutral", "negative"]

# How many posts of each kind, per brand. "random" fills the brand up to 15.
PLAN = {
    "Brewhaus":   {"emoji only": 2, "topic tools opposite": 2, "tone tools opposite": 2, "AI unsure": 1, "reply": 1},
    "Trailnorth": {"emoji only": 1, "topic tools opposite": 2, "tone tools opposite": 2, "AI unsure": 1, "reply": 1, "mixed topic": 1},
}
PER_BRAND = 15

GUIDE = [
    ("HOW TO FILL THIS IN", ""),
    ("1", "Go to the sheet 'Posts'. Read each post as a follower would see it on X."),
    ("2", "Choose team_topic and team_tone from the drop-down lists. Use 'comment' when you hesitate."),
    ("3", "Do not look at any tool output first. We compare your labels with the tools afterwards."),
    ("", ""),
    ("TOPIC (team_topic)", ""),
    ("Informational", "The post gives the reader something to use or act on: facts, tips, product information, "
                      "opening hours, events with a date or place, offers, contests, service instructions."),
    ("Emotional", "The post is about humour, feelings, stories or community and gives no useful information: "
                  "jokes, moods, thank-yous, questions to the audience."),
    ("Mixed", "Both: it gives useful information AND the message itself also jokes, tells a story or appeals to feelings."),
    ("", ""),
    ("TOPIC RULES", ""),
    ("Rule 1", "Judge the message, not the decoration. Emojis, hashtags, CAPITALS and '!' never change the topic."),
    ("Rule 2", "Stock phrases do not count either: 'breaking:', 'psa:', 'not a drill:', 'hot take:', 'ok so', "
               "'Quiet reminder:', 'Field note:', 'see you at the counter', 'you know where to find us', "
               "'that's it. that's the post', 'See you out there', 'The trail is waiting'."),
    ("Rule 3", "'Useful information' = the reader learns something concrete: what, when, where, how much or how to."),
    ("Rule 4", "A post with only emojis (no words) is Emotional."),
    ("", ""),
    ("TONE (team_tone)", "How does the whole post sound to a reader, emojis included?"),
    ("positive", "Happy, warm, enthusiastic, funny in a friendly way, good news."),
    ("neutral", "Plain information, no clear feeling either way."),
    ("negative", "Apology, problem, complaint, bad news, worry."),
    ("Irony", "Judge what the brand means, not the literal words. A joke about being tired is usually positive."),
]


def make():
    if FILE.exists() and "--force" not in sys.argv:
        sys.exit(f"{FILE.name} already exists. The team may have started filling it in. Add --force to replace it.")

    df = pd.read_csv(ROOT / "data" / "04_topic.csv", dtype={"id": str}, keep_default_na=False)
    df = df[~df["id"].isin(PROMPT_EXAMPLES)].copy()
    df["template"] = df["text"].map(template_of)

    # templates where the AI gave different labels to near-identical posts
    labels_per_template = df[df["template"] != ""].groupby(["brand", "template"])["ai_topic"].transform("nunique")
    df["ai_unsure"] = labels_per_template.reindex(df.index).fillna(1) > 1

    opposite = lambda a, b, x, y: ((a == x) & (b == y)) | ((a == y) & (b == x))
    pools = {
        "emoji only": df["emoji_usage"] == "alone",
        "topic tools opposite": opposite(df["ai_topic"], df["zs_short"], "Informational", "Emotional"),
        "tone tools opposite": opposite(df["vader_label"], df["roberta_label"], "positive", "negative"),
        "AI unsure": df["ai_unsure"],
        "reply": df["post_type"] == "reply",
        "mixed topic": df["ai_topic"] == "Mixed",
        "random": df["in_regression"],
    }

    picked = []                                           # (id, why)
    for brand, plan in PLAN.items():
        used_templates = set()
        steps = list(plan.items()) + [("random", PER_BRAND - sum(plan.values()))]
        for why, how_many in steps:
            pool = df[pools[why] & (df["brand"] == brand)].sample(frac=1, random_state=SEED)
            taken = 0
            for row in pool.itertuples():
                if taken == how_many:
                    break
                already = row.id in [p[0] for p in picked]
                same_template = row.template != "" and row.template in used_templates
                if already or same_template:
                    continue
                picked.append((row.id, why))
                used_templates.add(row.template)
                taken += 1
            if taken < how_many:
                print(f"  note: only {taken} of {how_many} '{why}' posts available for {brand}")

    key = pd.DataFrame(picked, columns=["id", "why_picked"]).merge(df[["id", "brand"]], on="id")
    key.to_csv(KEY, index=False, encoding="utf-8")

    # the sheet the team sees: shuffled, with no hint of why a post was picked
    sheet = (df[df["id"].isin(key["id"])][["id", "brand", "text"]]
             .sample(frac=1, random_state=SEED).sort_values("brand", kind="stable"))
    sheet["team_topic"] = ""
    sheet["team_tone"] = ""
    sheet["comment"] = ""
    with pd.ExcelWriter(FILE, engine="openpyxl") as writer:
        sheet.to_excel(writer, sheet_name="Posts", index=False)
        pd.DataFrame(GUIDE, columns=["", "Guide"]).to_excel(writer, sheet_name="Guide", index=False)

    # make it pleasant to fill in: column widths, wrapped text, drop-down lists
    book = load_workbook(FILE)
    posts = book["Posts"]
    for column, width in {"A": 11, "B": 12, "C": 90, "D": 16, "E": 13, "F": 40}.items():
        posts.column_dimensions[column].width = width
    for row in posts.iter_rows(min_row=2):
        row[2].alignment = Alignment(wrap_text=True, vertical="top")
    last = posts.max_row
    for column, choices in {"D": TOPICS, "E": TONES}.items():
        rule = DataValidation(type="list", formula1='"' + ",".join(choices) + '"', allow_blank=True)
        posts.add_data_validation(rule)
        rule.add(f"{column}2:{column}{last}")
    posts.freeze_panes = "A2"
    guide = book["Guide"]
    guide.column_dimensions["A"].width = 22
    guide.column_dimensions["B"].width = 110
    for row in guide.iter_rows(min_row=2):
        row[1].alignment = Alignment(wrap_text=True, vertical="top")
        if row[1].value in ("", None) or str(row[0].value).isupper():
            row[0].font = Font(bold=True)
    book.save(FILE)

    print(f"Saved {FILE.relative_to(ROOT)} ({len(sheet)} posts) and {KEY.relative_to(ROOT)}")
    print(pd.crosstab(key["why_picked"], key["brand"], margins=True).to_string())


def tidy(value, choices):
    """Accept 'pos', 'Positive ', 'INFO' ...: match on the first letters."""
    v = str(value).strip().lower()
    for choice in choices:
        if v and choice.lower().startswith(v[:3]):
            return choice
    return ""


def check():
    team = pd.read_excel(FILE, sheet_name="Posts", dtype=str).fillna("")
    team["team_topic"] = team["team_topic"].map(lambda v: tidy(v, TOPICS))
    team["team_tone"] = team["team_tone"].map(lambda v: tidy(v, TONES))
    empty = team[(team["team_topic"] == "") | (team["team_tone"] == "")]
    if len(empty):
        sys.exit(f"{len(empty)} of {len(team)} posts are not fully labelled yet: {', '.join(empty['id'])}")

    tools = pd.read_csv(ROOT / "data" / "04_topic.csv", dtype={"id": str}, keep_default_na=False)
    key = pd.read_csv(KEY, dtype={"id": str})
    d = team[["id", "team_topic", "team_tone", "comment"]].merge(tools, on="id").merge(key[["id", "why_picked"]], on="id")
    d["kind"] = d["why_picked"].map(lambda w: "random" if w == "random" else "hard case")

    comparisons = {
        "team_topic": {"AI prompt (final topic)": "topic", "AI prompt (before corrections)": "ai_topic",
                       "Zero-shot, short labels": "zs_short", "Zero-shot, definitions": "zs_defined",
                       "Zero-shot, two questions": "zs_two"},
        "team_tone": {"VADER": "vader_label", "VADER without emojis": "vader_text_only_label",
                      "TextBlob": "textblob_label", "Twitter-RoBERTa": "roberta_label"},
    }
    rows = []
    for team_col, tool_cols in comparisons.items():
        for name, col in tool_cols.items():
            for part, sub in [("all 30", d), ("random", d[d["kind"] == "random"]), ("hard cases", d[d["kind"] == "hard case"])]:
                rows.append({"label": team_col.replace("team_", ""), "tool": name, "posts": part, "n": len(sub),
                             "agreement_pct": round(100 * (sub[team_col] == sub[col]).mean(), 1),
                             "kappa": round(cohen_kappa_score(sub[team_col], sub[col]), 2) if sub[team_col].nunique() > 1 else None})
    results = pd.DataFrame(rows)
    print(results.to_string(index=False))

    print("\nTeam topic vs final topic:")
    print(pd.crosstab(d["team_topic"], d["topic"]).to_string())
    print("\nTeam tone vs VADER without emojis (the score used in the regression):")
    print(pd.crosstab(d["team_tone"], d["vader_text_only_label"]).to_string())

    wrong = d[(d["team_topic"] != d["topic"]) | (d["team_tone"] != d["vader_text_only_label"])]
    wrong = wrong[["id", "brand", "why_picked", "team_topic", "topic", "ai_reason", "team_tone", "vader_label",
                   "vader_text_only_label", "roberta_label", "textblob_label", "comment", "text"]]
    results.to_csv(ROOT / "outputs" / "validation_results.csv", index=False)
    wrong.to_csv(ROOT / "outputs" / "validation_disagreements.csv", index=False, encoding="utf-8")
    print(f"\nSaved outputs/validation_results.csv and outputs/validation_disagreements.csv ({len(wrong)} posts to look at)")


if __name__ == "__main__":
    {"make": make, "check": check}[sys.argv[1]]()
