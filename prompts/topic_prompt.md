# Topic classification prompt

| | |
|---|---|
| Model | Claude Fable 5.2 (`claude-fable-5-2`), used through Claude Code |
| Date | 15 November 2026 |
| Type | Few-shot: 3 examples, one per category |
| Batch size | 25 posts per batch (14 batches for 348 posts) |
| How it is run | Each batch goes to a fresh AI session (a Claude Code sub-agent) that sees only the prompt below and the 25 posts. It does not see the zero-shot results, the sentiment scores or the engagement numbers. The posts are shuffled once (seed 42) so every batch mixes both brands. |
| Files | `prompts/batches/batch_01.txt` to `batch_14.txt` = exactly what the AI read. `prompts/answers/` = exactly what it answered. |
| Output | `data/04_topic_ai.csv` (id, label, short reason) |

The three example posts (BRW-0007, TRN-0090, BRW-0005) come from our data. Their label is
given in the prompt, so we leave them out when we check the AI against our own labels.

## The instruction given to each fresh session

Only the batch number changes:

```text
Read the file ".../ma1/prompts/batches/batch_01.txt". It contains a labelling task:
instructions followed by a list of posts. Do exactly what it says, using only that file:
do not open any other file in the project and do not search the web. Write your answer,
in the exact output format the file asks for and nothing else (one line per post, every
post exactly once, ids copied exactly), to ".../ma1/prompts/answers/batch_01.txt".
Then reply with the single word: done.
```

## The prompt (exact text, the same for every batch)

```text
You are labelling posts published on X by two brands: Brewhaus (a coffee house chain)
and Trailnorth (premium hiking and camping gear).

Give every post exactly one topic label: Informational, Emotional or Mixed.

CATEGORIES
- Informational: the post gives the reader something to use or act on. Facts, tips,
  product information, opening hours, events with a date or place, offers, contests,
  service instructions.
- Emotional: the post is about humour, feelings, stories or community and gives no
  useful information. Jokes, moods, thank-yous, questions to the audience.
- Mixed: the post does both. It gives useful information AND the message itself also
  jokes, tells a story or appeals to feelings.

RULES
1. Judge the message, not the decoration. Emojis, hashtags, capital letters and
   exclamation marks never change the label.
2. Stock phrases do not count either. Openers such as "breaking:", "psa:", "not a drill:",
   "hot take:", "ok so", "Quiet reminder:", "Field note:" and sign-offs such as
   "see you at the counter", "you know where to find us", "that's it. that's the post",
   "See you out there", "The trail is waiting" are the brand's habit, not the topic.
3. "Useful information" means the reader learns something concrete: what, when, where,
   how much or how to.
4. A post with only emojis (no words) is Emotional.
5. Posts can be in English, Dutch or German. Label them the same way.

EXAMPLES
Post: New on the menu: Pistachio Latte, made with two shots of our house blend and steamed whole milk. Available in all Leiden stores from 19 October. https://t.co/5VdBOWFTXs
Label: Informational
Reason: product, place and date, no joke or feeling

Post: At 05:40 the valley was still dark. By 07:10 the whole ridge glowed pink. Nobody spoke. Sometimes the 🏔️ say everything for you. #KeepWalking
Label: Emotional
Reason: a mood, nothing to use or act on

Post: stroopwafel + Pistachio Latte: the combo you did not know you needed. Available all day, but please don’t tell the 🥐 we said that. see you at the counter. https://t.co/aHy4yu45EI
Label: Mixed
Reason: says what is available and when, and jokes about the croissant

OUTPUT
One line per post and nothing else, in this format:
id | label | reason (10 words at most)

POSTS
{the 25 posts of the batch, one per line, as "id | text"}
```
