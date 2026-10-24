# Tutorial: your first post with /x-post, from install to the FIRST REPLY block

You will turn one idea into a post you can paste into X by hand, with the link moved into a first
reply. Along the way you run the same tools the `/x-post` skill runs, and you read their real output.
About ten minutes. Nothing here posts, likes or follows; at the end you copy two blocks and post them
yourself.

Everything below was run on 2026-10-24 with Python 3.15 on Windows. The sample idea, the numbers in it
and the link are invented. Replace them with your own; the tools only count and lint text, they do not
know whether it is true.

## What you need

- Python 3.9 or newer (`python --version` on Windows, `python3 --version` elsewhere).
- Git, or the ZIP from the repository's Code button.
- Optional: Claude Code, if you want the skill to drive this for you. The tools work without it.

## Step 1: Get the tools and prove they run

```bash
git clone https://github.com/MuhammadHassan03/x-agent-skill.git
cd x-agent-skill
python3 skills/x-post/xcount.py --help      # Windows: python
```

You should see a `usage:` line. If Windows answers `python3` with "Python was not found", that is
the Microsoft Store shortcut: use `python` (or `py`) instead, everywhere below.

To use the skill as well, install it (the full options are in the [README](../README.md#install)):

```
/plugin marketplace add MuhammadHassan03/x-agent-skill
/plugin install x-agent@x-agent-skill
```

Plugin skills are namespaced, so you type `/x-agent:x-post`. Then copy `templates/voice.md` to
`~/.claude/x/voice.md` and fill it in, so the skill writes like you.

## Step 2: Pick the first line

The first line decides whether anyone reads the rest. Put three candidates in a file, one per line, and
rank them. The sample file `hooks.txt`:

```
A thread on cold DMs
I used to open cold DMs with a pitch. Now I open with a question.
I sent 40 cold DMs in 30 days and 2 became clients.
```

```bash
python3 skills/x-post/postscore.py --hooks hooks.txt
```

```
1.  97.0  no formula matched       I sent 40 cold DMs in 30 days and 2 became clients.
2.  66.3  Reversal                 I used to open cold DMs with a pitch. Now I open with a question.
3.  40.0  no formula matched       A thread on cold DMs
        - thread opener as the hook
```

The number is a lint result, not a forecast. It rewards a concrete number and a line that works alone, and
it dings "A thread on...". On a public tweet corpus the score did not predict which posts beat their
account's median likes (see the README's measurement section), so use it to catch weak lines, not to pick
a winner. Here the numeric line is also the one with a specific claim, so it is the one to build on.

If your best line scores under 50, you do not have the hook yet. Get a better fact instead of polishing.

## Step 3: Write the draft, link and all

Save this as `draft.txt`. It is the natural way to write it: the link sits at the end of the post.

```
I sent 40 cold DMs in 30 days and 2 became clients.

The two who said yes both got a question about their pricing page, not a pitch.

What is the first line you send a stranger?

Write-up: https://example.com/cold-dm-notes
```

Count it the way X counts it (a URL always weighs 23, most characters 1, CJK and most emoji 2):

```bash
python3 skills/x-post/xcount.py draft.txt
```

```
212 / 280 weighted (free)  FITS
  remaining 68, urls 1 (each 23), weight-2 characters 0
```

## Step 4: Score it, and read the hard stop

```bash
python3 skills/x-post/postscore.py draft.txt
```

```
POST SCORE  49.0  WEAK   (212/280 weighted)
score capped at 49: link in root post
----------------------------------------------------------------
  HOOK         ###################.  95.0  51 weighted characters
  SPECIFICITY  #################### 100.0  9 concrete markers in 39 words
  REPLY PULL   #############.......  65.0  question present
  LINK         ....................   0.0  1 link(s) in root post
               - Link in root post. On free accounts, links in the root post were observed to cost reach (observed, not coded). Put it in the first reply.
  BAIT         #################### 100.0  none

BLOCKING: Link in root post. On free accounts, links in the root post were observed to cost reach (observed, not coded). Put it in the first reply.
```

The command exits with status 1. Two honest things to know about this stop:

- It rests on an outside observation (Buffer, 2025, 18.8 million posts), not on anything in X's published
  ranking code, which has no link penalty. That is why the wording says "observed, not coded".
- It is the repo's default for a free account, not a law. If you have a reason to keep the link in the post,
  `--allow-link` turns the stop into a warning. Use it on purpose, never by habit.

## Step 5: Move the link out

```bash
python3 skills/x-post/postscore.py draft.txt --split-link
```

```
POST (link removed)
I sent 40 cold DMs in 30 days and 2 became clients.

The two who said yes both got a question about their pricing page, not a pitch.

What is the first line you send a stranger?

FIRST REPLY
Write-up:
https://example.com/cold-dm-notes
```

That is the shape you will post: the root post has no link, and the link goes in the first reply you write
under it. The skill prints these as two blocks and, when there was a link, always prints the second one.

## Step 6: Edit it by hand until it sounds like you

Run the humanizer on the draft:

```bash
python3 skills/x-human/humanize.py draft.txt --report
```

```
HUMANIZE REPORT
---------------
0 machine artefacts removed, 0 structural tells flagged for rewrite

CLEAN
-----
  Nothing to strip.
```

Nothing mechanical to strip, so the rest is yours. Run the five-check panel to see what it would flag:

```bash
python3 skills/x-human/detect.py draft.txt
```

```
  BURSTINESS    ------------------------   n/a
                too short to judge (needs 4+ sentences)
  SPECIFICITY   ######################## 100.0
  SLOP DENSITY  ######################## 100.0
  FINGERPRINT   ######################## 100.0
  VOICE         ############............  48.8
                0.0 contractions, 4.8 personal pronouns per 100 words, 0 structural tell(s)
  HUMAN SCORE   #################.......  71.8   REVIEW
  4 of 5 checks scored.
```

(Lines trimmed for length.) These are local heuristics, not GPTZero or any third-party detector, and they
say nothing about how X will treat a post. They are a prompt to read your own text. Here the weakest signal
is voice: no contractions. A first hand edit, `post.txt`, adds them:

```
I sent 40 cold DMs in 30 days and 2 became clients.

The two who said yes didn't get a pitch. They got a question about their pricing page.

What's the first line you send a stranger?
```

```bash
python3 skills/x-human/detect.py post.txt
```

```
  BURSTINESS    ........................   0.0
                variation 0.18 across 4 sentences (want 0.55+)
  VOICE         #####################...  89.4
                5.9 contractions, 5.9 personal pronouns per 100 words, 0 structural tell(s)
  HUMAN SCORE   ###########.............  46.7   FLAGGED
  5 of 5 checks scored.
```

The score went down, and that is worth understanding rather than hiding. Voice improved from 48.8 to
89.4. But with four sentences there is now enough text to judge sentence-length variation, and every
sentence is about the same length, so BURSTINESS scores 0. The two panels are not comparable: the first
scored four checks, this one scores five. Read the weakest signal, not the total.

A second hand edit mixes short and long sentences, `post2.txt`:

```
I sent 40 cold DMs in 30 days. Two became clients.

Neither got a pitch. Both got one question about their pricing page, written for them, with nothing else attached.

What's the first line you send a stranger?
```

```bash
python3 skills/x-human/detect.py post2.txt
python3 skills/x-post/postscore.py post2.txt
```

```
  BURSTINESS    #################.......  69.9
                variation 0.56 across 5 sentences (want 0.55+)
  VOICE         ####################....  85.2
  HUMAN SCORE   ####################....  81.6   PASS
  5 of 5 checks scored.

POST SCORE  93.8  STRONG   (210/280 weighted)
```

Both pass. You made that change by reading the output and rewriting by hand, which is the point: the tools
point, you write. Never paste an unedited draft. X's rules and its Original Content Rewards programme both
treat content "created or posted using automated means" as a problem, so read and edit every post.

## Step 7: Check both blocks fit, then post them yourself

```bash
python3 skills/x-post/xcount.py post2.txt
python3 skills/x-post/xcount.py reply.txt
```

```
210 / 280 weighted (free)  FITS
  remaining 70, urls 0 (each 23), weight-2 characters 0
33 / 280 weighted (free)  FITS
  remaining 247, urls 1 (each 23), weight-2 characters 0
```

Here are the two blocks you copy.

Post:

```
I sent 40 cold DMs in 30 days. Two became clients.

Neither got a pitch. Both got one question about their pricing page, written for them, with nothing else attached.

What's the first line you send a stranger?
```

First reply, posted under it:

```
Write-up:
https://example.com/cold-dm-notes
```

When you run this through `/x-agent:x-post`, the skill ends with the finished text in these two blocks and
the line **Reply yes to log it**. A "yes" appends one line (date, skill, first line) to
`~/.claude/x/log.md` on your disk. That is all it does. It never posts; you open x.com, paste the post,
publish it, and paste the reply under it.

## What you built

You have a post that is counted the way X counts, has a first line that stands alone, has no link in the
root, and has been through your own edit, plus a first-reply block carrying the link. You also know what
each number does and does not mean.

Where to go next:

- The [README](../README.md) for the other eleven skills and the measurement behind the "lint, not
  forecast" warnings.
- `skills/x-post/SKILL.md` for the exact rules the skill follows (no bait, at most one hashtag,
  `{{your number}}` for any figure you did not give it).
- `skills/x-thread/SKILL.md` when the idea needs more than 280 characters: it splits a long draft and keeps
  the link in a first reply the same way.
