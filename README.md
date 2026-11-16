# ma1 · Emojis, tone and engagement on X

Code for a team assignment in Digital Marketing & Analytics (University of Amsterdam, 2026): how two brands, Brewhaus and Trailnorth, use emojis and tone on X, and what goes with more likes per view.

Browse the posts: https://axelizsak.github.io/ma1/

## Run it

```
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p data outputs
curl -o data/unicode_emoji_test.txt https://www.unicode.org/Public/18.0.0/emoji/emoji-test.txt
```

Put the course file `Main_Assignment_1_Dataset_2026-27.csv` one folder above `ma1/`, then run from `ma1/`:

```
.venv/bin/python scripts/01_clean.py
.venv/bin/python scripts/02_paralanguage.py
.venv/bin/python scripts/03_sentiment.py
.venv/bin/python scripts/04_topic_zeroshot.py
.venv/bin/python scripts/04_topic_ai.py make      # then an AI labels each batch file
.venv/bin/python scripts/04_topic_ai.py collect
.venv/bin/python scripts/05_validation.py make    # the 30 posts the team labels by hand
.venv/bin/python scripts/05_validation.py check   # after the team has labelled its 30 posts
.venv/bin/python scripts/06_regression.py
.venv/bin/python scripts/08_outputs.py
.venv/bin/python scripts/07_explorer.py
.venv/bin/python scripts/09_team_summary.py
```

The first run downloads two Hugging Face models (about 2 GB). The AI topic step reads `prompts/topic_prompt.md`, which is not in this repository yet.
