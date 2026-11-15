"""
Step 2c (tool 1) - Topic with zero-shot classification (facebook/bart-large-mnli).

The model has never seen our categories. For each post it checks how well a
sentence such as "This post is informational." fits, for every label, and we
keep the best one. The wording of the labels matters, so we test three versions:

  zs_short     the bare category names (informational / emotional / mixed)
  zs_defined   each category written out as its definition
  zs_two       only two labels (information, emotion), scored separately;
               "Mixed" when the model says yes to both

Run from the ma1/ folder:  .venv/bin/python scripts/04_topic_zeroshot.py
"""
from pathlib import Path

import pandas as pd
import torch
from transformers import pipeline

ROOT = Path(__file__).resolve().parents[1]
MODEL = "facebook/bart-large-mnli"

df = pd.read_csv(ROOT / "data" / "03_sentiment.csv", dtype={"id": str}, keep_default_na=False)

# Links and @names carry no topic, so the model does not get them.
posts = (df["text"].str.replace(r"https?://\S+", " ", regex=True)
                   .str.replace(r"@\w+", " ", regex=True).str.strip().tolist())

device = "mps" if torch.backends.mps.is_available() else "cpu"
zero_shot = pipeline("zero-shot-classification", model=MODEL, device=device)

# --- Wording 1: the bare category names ----------------------------------------
SHORT = {"informational": "Informational", "emotional": "Emotional", "mixed": "Mixed"}
out = zero_shot(posts, list(SHORT), hypothesis_template="This post is {}.", batch_size=8)
df["zs_short"] = [SHORT[o["labels"][0]] for o in out]
df["zs_short_score"] = [round(o["scores"][0], 3) for o in out]

# --- Wording 2: the definitions -------------------------------------------------
DEFINED = {
    "gives facts, tips, product information or an offer": "Informational",
    "is about humour, feelings or community and gives no useful information": "Emotional",
    "gives useful information and also uses humour or feelings": "Mixed",
}
out = zero_shot(posts, list(DEFINED), hypothesis_template="This post {}.", batch_size=8)
df["zs_defined"] = [DEFINED[o["labels"][0]] for o in out]
df["zs_defined_score"] = [round(o["scores"][0], 3) for o in out]

# --- Wording 3: two separate yes/no questions -------------------------------------
INFO = "gives facts, tips, product information or an offer"
EMO = "uses humour, feelings or community"
out = zero_shot(posts, [INFO, EMO], hypothesis_template="This post {}.", multi_label=True, batch_size=8)
df["zs_info_score"] = [round(dict(zip(o["labels"], o["scores"]))[INFO], 3) for o in out]
df["zs_emo_score"] = [round(dict(zip(o["labels"], o["scores"]))[EMO], 3) for o in out]


def two_label_topic(row):
    info, emo = row["zs_info_score"] > 0.5, row["zs_emo_score"] > 0.5
    if info and emo:
        return "Mixed"
    return "Informational" if row["zs_info_score"] >= row["zs_emo_score"] else "Emotional"


df["zs_two"] = df.apply(two_label_topic, axis=1)

df.to_csv(ROOT / "data" / "04_topic_zeroshot.csv", index=False, encoding="utf-8")
print(f"Saved data/04_topic_zeroshot.csv ({len(df)} posts)\n")

for col in ["zs_short", "zs_defined", "zs_two"]:
    print(pd.crosstab(df[col], df["brand"], margins=True).to_string(), "\n")
print("Same label with wording 1 and wording 2:", round(100 * (df["zs_short"] == df["zs_defined"]).mean(), 1), "%")
print(pd.crosstab(df["zs_short"], df["zs_defined"]).to_string())
