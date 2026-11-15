"""
Step 1 - Select the rows we analyse.

Reads the raw CSV (never changes it), keeps our two brands and marks which
posts are used for which purpose:

  in_describe    originals + replies: everything the brand wrote itself.
                 Used to describe paralanguage (emojis, other cues).
  in_regression  original posts in English that contain words.
                 Used for the main regression (all tools can read them).
  in_robustness  in_regression + emoji-only originals (lang = zxx).
                 Used to re-run the regression as a check.

Retweets are dropped: the words and emojis were written by someone else.

Run from the ma1/ folder:  .venv/bin/python scripts/01_clean.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]          # the ma1/ folder
RAW = ROOT.parent / "Main_Assignment_1_Dataset_2026-27.csv"
BRANDS = ["Brewhaus", "Trailnorth"]

# id is a code like "BRW-0001": read it as text, as the codebook asks
raw = pd.read_csv(RAW, dtype={"id": str}, encoding="utf-8")
df = raw[raw["brand"].isin(BRANDS)].copy()

# --- the selection rules (see decisions_log.md, Step 1) ---------------------
is_original = df["post_type"] == "original"
is_reply = df["post_type"] == "reply"
is_english = df["lang"] == "en"
is_emoji_only = df["lang"] == "zxx"                  # no words: emojis, links, hashtags

df["in_describe"] = is_original | is_reply
df["in_regression"] = is_original & is_english
df["in_robustness"] = is_original & (is_english | is_emoji_only)

# --- before / after table, per brand ----------------------------------------
table = pd.DataFrame({
    "All posts in the raw file": df.groupby("brand").size(),
    "  of which retweets (dropped)": df[df["post_type"] == "retweet"].groupby("brand").size(),
    "(a) Describe paralanguage: originals + replies": df.groupby("brand")["in_describe"].sum(),
    "      originals": df[is_original].groupby("brand").size(),
    "      replies": df[is_reply].groupby("brand").size(),
    "      of which emoji-only (zxx)": df[df["in_describe"] & is_emoji_only].groupby("brand").size(),
    "      of which Dutch / German": df[df["in_describe"] & df["lang"].isin(["nl", "de"])].groupby("brand").size(),
    "(b) Regression: English originals with words": df.groupby("brand")["in_regression"].sum(),
    "(b) Robustness check: + emoji-only originals": df.groupby("brand")["in_robustness"].sum(),
}).T
table["Total"] = table.sum(axis=1)
print(table.to_string())

# --- save --------------------------------------------------------------------
selected = df[df["in_describe"]].copy()              # 348 rows: the posts we work with
selected.to_csv(ROOT / "data" / "01_selected.csv", index=False, encoding="utf-8")
table.to_csv(ROOT / "outputs" / "table_step1_rows_before_after.csv", encoding="utf-8")
print(f"\nSaved {len(selected)} posts to data/01_selected.csv")
