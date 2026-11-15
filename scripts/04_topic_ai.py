"""
Step 2c (tool 2) - Topic with an AI prompt (Claude), in batches of 25 posts.

The AI itself is not called from this script. The script only prepares and collects:

  make     writes one text file per batch in prompts/batches/. Each file is the
           fixed prompt from prompts/topic_prompt.md followed by 25 posts.
           A fresh AI session reads one file and answers in prompts/answers/.
  collect  reads the answers and saves data/04_topic_ai.csv (id, label, reason).

Run from the ma1/ folder:
  .venv/bin/python scripts/04_topic_ai.py make
  .venv/bin/python scripts/04_topic_ai.py collect
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BATCH_SIZE = 25
LABELS = {"Informational", "Emotional", "Mixed"}
PLACEHOLDER = '{the 25 posts of the batch, one per line, as "id | text"}'

# Hand corrections to the AI labels (see decisions_log.md, Step 2c).
# The AI gave two different labels to posts built on the same sentence.
# We keep one label per template: the majority label, or our own choice when it was a tie.
TOPIC_CORRECTIONS = {
    "TRN-0056": "Mixed",          # "Behind the seams: our designers spent..."  4 of 5 were Mixed
    "BRW-0141": "Informational",  # "your app stars never expire during..."     3 of 4 were Informational
    "BRW-0110": "Emotional",      # "Meet the team behind our new menu..."      tie, a team story with nothing to act on
    "BRW-0158": "Informational",  # "Our beans are now sourced with..."         tie, a fact plus a catchy line
    "BRW-0193": "Informational",  # "our coffee grounds now become fertiliser"  tie, a fact plus a catchy line
}

df = pd.read_csv(ROOT / "data" / "01_selected.csv", dtype={"id": str})


def make():
    # the exact prompt is the ```text block of prompts/topic_prompt.md
    prompt_file = (ROOT / "prompts" / "topic_prompt.md").read_text(encoding="utf-8")
    prompt = re.search(r"```text\n(.*?)```", prompt_file, flags=re.S).group(1)

    # shuffle once (fixed seed) so that every batch mixes both brands
    posts = df.sample(frac=1, random_state=42)
    folder = ROOT / "prompts" / "batches"
    folder.mkdir(exist_ok=True)
    (ROOT / "prompts" / "answers").mkdir(exist_ok=True)
    for n, start in enumerate(range(0, len(posts), BATCH_SIZE), start=1):
        batch = posts.iloc[start:start + BATCH_SIZE]
        lines = "\n".join(f"{r.id} | {r.text}" for r in batch.itertuples())
        (folder / f"batch_{n:02d}.txt").write_text(prompt.replace(PLACEHOLDER, lines), encoding="utf-8")
    print(f"Wrote {n} batch files of up to {BATCH_SIZE} posts in prompts/batches/")


def collect():
    rows = []
    for file in sorted((ROOT / "prompts" / "answers").glob("batch_*.txt")):
        for line in file.read_text(encoding="utf-8").splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2 and re.match(r"(BRW|TRN)-\d{4}$", parts[0]):
                rows.append({"id": parts[0], "ai_topic": parts[1],
                             "ai_reason": " | ".join(parts[2:]), "ai_batch": file.stem})
    ai = pd.DataFrame(rows)

    # checks: every post answered exactly once, with a valid label (the AI may not invent anything)
    missing = sorted(set(df["id"]) - set(ai["id"]))
    unknown = sorted(set(ai["id"]) - set(df["id"]))
    twice = sorted(ai["id"][ai["id"].duplicated()])
    bad = ai[~ai["ai_topic"].isin(LABELS)]
    print(f"{len(ai)} answers for {len(df)} posts | missing: {missing} | not in our data: {unknown} "
          f"| answered twice: {twice} | invalid labels: {len(bad)}")
    if missing or unknown or twice or len(bad):
        print(bad.to_string())
        sys.exit("Fix the answers before going on.")

    ai.to_csv(ROOT / "data" / "04_topic_ai.csv", index=False, encoding="utf-8")
    print("Saved data/04_topic_ai.csv")

    # one file with everything so far: paralanguage, sentiment, zero-shot topic, AI topic
    full = pd.read_csv(ROOT / "data" / "04_topic_zeroshot.csv", dtype={"id": str}, keep_default_na=False)
    full = full.merge(ai, on="id", how="left")

    # "topic" is the label we use from here on: the AI label, with our hand corrections
    full["topic"] = full["ai_topic"]
    for post_id, label in TOPIC_CORRECTIONS.items():
        full.loc[full["id"] == post_id, "topic"] = label
    full["topic_corrected"] = (full["topic"] != full["ai_topic"]).astype(int)

    full.to_csv(ROOT / "data" / "04_topic.csv", index=False, encoding="utf-8")
    print(f"Saved data/04_topic.csv ({len(full)} posts, {full['topic_corrected'].sum()} corrected by hand)")
    print(pd.crosstab(full["topic"], full["brand"], margins=True).to_string())


if __name__ == "__main__":
    {"make": make, "collect": collect}[sys.argv[1]]()
