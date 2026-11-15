"""
Step 2a - Paralanguage: emojis and other cues, for every selected post.

Adds these columns to the 348 selected posts:
  emojis, n_emoji, has_emoji          every emoji in the post, how many
  n_face, n_nonface, has_face, ...    face vs non-face (rule below)
  emoji_usage                         none / with text / instead of words / alone
  n_exclam, n_caps_words, n_hashtags  the other cues (+ has_... versions)

Rules (see decisions_log.md, Step 2a):
  FACE     = the emoji sits in an official Unicode subgroup that starts with "face-"
             (file data/unicode_emoji_test.txt, from unicode.org).
  ALONE    = the post has emojis but no words (hashtags and links are not words).
  INSTEAD  = at least one emoji stands where a word should be (function below).
  WITH TEXT= every other post that has an emoji.

Run from the ma1/ folder:  .venv/bin/python scripts/02_paralanguage.py
"""
import re
from collections import Counter
from pathlib import Path

import emoji
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "01_selected.csv", dtype={"id": str})

# --- 1. Which emojis are faces? ---------------------------------------------
# The Unicode file lists every emoji under a group and a subgroup,
# for example "Smileys & Emotion" > "face-smiling".
subgroup_of = {}
current = None
for line in open(ROOT / "data" / "unicode_emoji_test.txt", encoding="utf-8"):
    if line.startswith("# subgroup:"):
        current = line.split(":", 1)[1].strip()
    elif "qualified" in line and "#" in line and not line.startswith("#"):
        symbol = line.split("#", 1)[1].split()[0]
        subgroup_of[symbol] = current

def is_face(symbol):
    """Face = official Unicode subgroup "face-..." (so 💀 and 🤡 count, hearts and hands do not)."""
    return subgroup_of.get(symbol, "").startswith("face-")


# --- 2. Helpers --------------------------------------------------------------
LINK_OR_TAG = r"https?://\S+|[#@]\w+"          # links, hashtags, @mentions
ACRONYMS = {"AI", "DM", "PFC"}                  # capitals, but not "shouting"
DETERMINERS = {"the", "a", "an", "our", "your"}  # words that need a noun after them

# We read all 14 posts the "instead of words" rule flagged. One was wrong:
# in "The new Summit 2P ⛺ has been field-tested" the tent repeats the product name,
# it does not replace a word. We correct it by hand.
NOT_INSTEAD_OF_WORDS = {"TRN-0050"}


def count_words(text):
    """Words left once emojis, links, hashtags and mentions are removed."""
    plain = re.sub(LINK_OR_TAG, " ", emoji.replace_emoji(text, " "))
    return len(re.findall(r"[A-Za-zÀ-ÿ]{2,}", plain))


def emoji_runs(text):
    """Groups of neighbouring emojis, each with the text before and after it."""
    found = emoji.emoji_list(text)               # combined emojis count as one
    runs, k = [], 0
    while k < len(found):
        start, end = found[k]["match_start"], found[k]["match_end"]
        symbols = [found[k]["emoji"]]
        while k + 1 < len(found) and text[end:found[k + 1]["match_start"]].strip() == "":
            k += 1
            end = found[k]["match_end"]
            symbols.append(found[k]["emoji"])
        runs.append((symbols, text[:start].rstrip(), text[end:].lstrip()))
        k += 1
    return runs


def replaces_a_word(before, after):
    """True if an emoji group stands where a word should be.

    a) inside a sentence:  "Free ☕ for the first 50 guests", "borrow ⛺, bags and stoves"
    b) used like maths:    "🥐 + Hazelnut Latte = the only relationship"
    c) closes a sentence right after the/a/our/your:  "the best porridge on the 🏔️."
    """
    last = before.split()[-1] if before else ""
    first = after.split()[0] if after else ""
    last_is_text = bool(last) and not re.match(LINK_OR_TAG, last)
    first_is_text = bool(first) and not re.match(LINK_OR_TAG, first)

    left_open = last_is_text and re.search(r"[A-Za-zÀ-ÿ0-9,:”\"+=]$", last) is not None
    right_open = first_is_text and re.match(r"[A-Za-zÀ-ÿ0-9,+=]", first) is not None
    like_maths = first[:1] in ("+", "=")
    sentence_over = after == "" or re.match(r"[.!?…]|" + LINK_OR_TAG, after) is not None
    after_determiner = re.sub(r"\W", "", last).lower() in DETERMINERS and sentence_over
    return (left_open and right_open) or like_maths or after_determiner


def measure(post):
    text = post["text"]
    runs = emoji_runs(text)
    symbols = [s for run, _, _ in runs for s in run]
    n_face = sum(is_face(s) for s in symbols)
    n_instead = sum(len(run) for run, before, after in runs if replaces_a_word(before, after))
    if post["id"] in NOT_INSTEAD_OF_WORDS:
        n_instead = 0
    n_words = count_words(text)

    if not symbols:
        usage = "none"
    elif n_words == 0:
        usage = "alone"
    elif n_instead > 0:
        usage = "instead of words"
    else:
        usage = "with text"

    plain = re.sub(LINK_OR_TAG, " ", text)
    caps = [w for w in re.findall(r"\b[A-Z]{2,}\b", plain) if w not in ACRONYMS]
    return {
        "emojis": " ".join(symbols),
        "n_emoji": len(symbols),
        "n_face": n_face,
        "n_nonface": len(symbols) - n_face,
        "n_emoji_instead": n_instead,
        "emoji_usage": usage,
        "n_words": n_words,
        "n_exclam": text.count("!"),
        "n_caps_words": len(caps),
        "n_hashtags": len(re.findall(r"#\w+", text)),
    }


# --- 3. Measure every post ----------------------------------------------------
df = pd.concat([df, df.apply(measure, axis=1).apply(pd.Series)], axis=1)
for cue in ["emoji", "face", "nonface", "exclam", "caps_words", "hashtags"]:
    df["has_" + cue.replace("_words", "").replace("hashtags", "hashtag")] = (df["n_" + cue] > 0).astype(int)

df.to_csv(ROOT / "data" / "02_paralanguage.csv", index=False, encoding="utf-8")

# every post where the rule says "instead of words", to read and check by hand
check = df[df["n_emoji_instead"] > 0][["id", "brand", "emojis", "text"]]
check.to_csv(ROOT / "outputs" / "check_emoji_instead_of_words.csv", index=False, encoding="utf-8")

# --- 4. Brand tables -----------------------------------------------------------
print("EMOJI USAGE per brand (posts)")
usage = pd.crosstab(df["emoji_usage"], df["brand"])
print(usage.to_string(), "\n")

print("CUES per brand (% of posts that have the cue, and mean count per post)")
cues = df.groupby("brand").agg(
    posts=("id", "size"),
    pct_emoji=("has_emoji", "mean"), pct_face=("has_face", "mean"), pct_nonface=("has_nonface", "mean"),
    pct_exclam=("has_exclam", "mean"), pct_caps=("has_caps", "mean"), pct_hashtag=("has_hashtag", "mean"),
    emojis_per_post=("n_emoji", "mean"),
).T.round(3)
print(cues.to_string(), "\n")

# repertoire: which emojis, how many, how varied
rows = []
for brand, posts in df.groupby("brand"):
    uses = Counter(s for e in posts["emojis"] if e for s in e.split(" "))
    total = sum(uses.values())
    rows.append({
        "brand": brand,
        "emoji uses": total,
        "distinct emojis": len(uses),
        "distinct per 100 uses": round(100 * len(uses) / total, 1),
        "share of faces": round(sum(n for s, n in uses.items() if is_face(s)) / total, 3),
        "share of top 5": round(sum(n for _, n in uses.most_common(5)) / total, 3),
        "top 10": "  ".join(f"{s} {n}" for s, n in uses.most_common(10)),
    })
repertoire = pd.DataFrame(rows).set_index("brand").T
print("REPERTOIRE per brand")
print(repertoire.to_string())

usage.to_csv(ROOT / "outputs" / "table_emoji_usage.csv")
cues.to_csv(ROOT / "outputs" / "table_cues.csv")
repertoire.to_csv(ROOT / "outputs" / "table_repertoire.csv")
print(f"\nSaved data/02_paralanguage.csv ({len(df)} posts) and 3 tables in outputs/")
