"""
Step 2b - Sentiment (tone) of every selected post, with three tools.

  vader_compound     VADER, -1 to +1. Built for social media; also reads emojis, CAPITALS and "!".
  vader_text_only    VADER on the same post with the emojis removed (to see what the emojis add).
  textblob_polarity  TextBlob, -1 to +1. Words only, ignores emojis.
  roberta_score      Twitter-RoBERTa (cardiffnlp), P(positive) - P(negative), -1 to +1.
  ..._label          positive / neutral / negative version of each score.

Run from the ma1/ folder:  .venv/bin/python scripts/03_sentiment.py
"""
import re
from pathlib import Path

import emoji
import pandas as pd
import torch
from textblob import TextBlob
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

ROOT = Path(__file__).resolve().parents[1]
ROBERTA = "cardiffnlp/twitter-roberta-base-sentiment-latest"
CUT = 0.05   # usual VADER cut-off: above +0.05 positive, below -0.05 negative, else neutral

# keep_default_na=False: a post without emoji keeps "" in the emojis column, not NaN
df = pd.read_csv(ROOT / "data" / "02_paralanguage.csv", dtype={"id": str}, keep_default_na=False)


def to_label(score):
    return "positive" if score > CUT else "negative" if score < -CUT else "neutral"


# Links and @names say nothing about tone, so the tools do not get them.
no_links = df["text"].str.replace(r"https?://\S+", " ", regex=True)
plain = no_links.str.replace(r"@\w+", " ", regex=True).str.strip()

# --- VADER (with and without emojis) -----------------------------------------
vader = SentimentIntensityAnalyzer()
df["vader_compound"] = plain.map(lambda t: vader.polarity_scores(t)["compound"])
df["vader_text_only"] = plain.map(lambda t: vader.polarity_scores(emoji.replace_emoji(t, " "))["compound"])

# --- TextBlob ------------------------------------------------------------------
df["textblob_polarity"] = plain.map(lambda t: TextBlob(t).sentiment.polarity)

# --- Twitter-RoBERTa -------------------------------------------------------------
# The model card asks for "@user" and "http" in place of real names and links.
for_roberta = df["text"].str.replace(r"https?://\S+", "http", regex=True).str.replace(r"@\w+", "@user", regex=True)
device = "mps" if torch.backends.mps.is_available() else "cpu"
classifier = pipeline("sentiment-analysis", model=ROBERTA, top_k=None, device=device)
results = classifier(for_roberta.tolist(), batch_size=16)
probs = pd.DataFrame([{r["label"]: r["score"] for r in post} for post in results], index=df.index)
df["roberta_score"] = (probs["positive"] - probs["negative"]).round(4)
df["roberta_label"] = probs.idxmax(axis=1)

df["vader_label"] = df["vader_compound"].map(to_label)
df["vader_text_only_label"] = df["vader_text_only"].map(to_label)
df["textblob_label"] = df["textblob_polarity"].map(to_label)

df.to_csv(ROOT / "data" / "03_sentiment.csv", index=False, encoding="utf-8")
print(f"Saved data/03_sentiment.csv ({len(df)} posts)\n")

# --- Quick look -------------------------------------------------------------------
labels = ["vader_label", "vader_text_only_label", "textblob_label", "roberta_label"]
print("Labels per tool (number of posts):")
print(pd.DataFrame({c: df[c].value_counts() for c in labels}).fillna(0).astype(int).to_string(), "\n")
print("Correlation between the scores:")
print(df[["vader_compound", "vader_text_only", "textblob_polarity", "roberta_score"]].corr().round(2).to_string())
