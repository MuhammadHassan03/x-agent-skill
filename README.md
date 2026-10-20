# The X agent skill

Twelve Claude Code skills that run an X (Twitter) account without ever touching X.
Free, MIT, no signup, no API key, nothing to connect.

**The skills write. You post.** There is no X API client, no browser automation,
no scraping, no extension and no "paste this in DevTools" script anywhere in this
repo. X's Automation Rules list "non-API-based forms of automation, such as
scripting the X website" under Don't and say it may lead to permanent suspension.
Having a human approve each post does not change who performs the action, so
nothing here performs it.

Every tool is Python standard library only, makes no network calls and uploads
nothing. They run on your machine, on your text.

## Why this one

Existing X skills either post through the paid API, run through a scraping proxy,
or are a prompt file with no measurement. This one is built around three things:

1. **Compliant.** Nothing acts on X. `/x-viral` works from posts you note down by
   hand. `/x-dm` drafts one message at a time for you to send.
2. **Measured.** The scorer and the outlier ranker were tested on a public corpus,
   and the result for the scorer is not flattering. It is below, in full.
3. **Tools that run.** Ten dependency-free tools, 136 tests, CI on Python 3.9, 3.11
   and 3.13 on Linux and Windows. A repo test fails the build on any em dash, any
   network or browser import in a tool, and any skill that lacks the approval gate.

Default persona: a small free account (280 weighted characters, link in the first
reply, reply-first growth) earning off-platform through clients, products or a
newsletter. Premium features are documented and labelled **documented, not tested
by the author**.

## Install

As a plugin:

```
/plugin marketplace add MuhammadHassan03/x-agent-skill
/plugin install x-agent
```

Or by hand:

```bash
git clone https://github.com/MuhammadHassan03/x-agent-skill.git
cp -r x-agent-skill/skills/x-* ~/.claude/skills/
```

Or with no Claude Code at all: paste one `SKILL.md` at the top of a chat and it runs as a
mode. You lose the Python tools, which is most of the point of `/x-post`, `/x-reply` and
`/x-human`, but the writing rules still apply.

Keep the `skills/` folders side by side: `x-thread`, `x-reply`, `x-viral` and
`x-article` import or read files from `x-post`.

Then copy `templates/voice.md` to `~/.claude/x/voice.md` and fill it in, or send
Claude three of your own posts and say "write my voice.md from these". For
several accounts see `templates/accounts.md`.

## The twelve

| command | what it does | tool |
| --- | --- | --- |
| `/x-post` | One idea into a post. Three hooks from [19 formulas](skills/x-post/hooks.json), scored, one humanized draft, counted the way X counts. | `postscore.py`, `xcount.py` |
| `/x-thread` | A long draft into a thread, 280 weighted characters per post, links gathered in the last post. | `thread.py` |
| `/x-reply` | Replies under other people's posts, checked against an approximation of the 0-3 reply rubric. Refuses compliment-only openers and self-reply chains. | `replylint.py` |
| `/x-viral` | Ranks posts you collected by hand by multiple over each account's own median. Never browses X. | `swipe.py` |
| `/x-article` | Long-form outline, draft, first-screen hook, originality checklist. Premium, not tested by the author. | `xcount.py` |
| `/x-human` | The humanizer and a five-check panel, with an X lexicon block. | `humanize.py`, `detect.py` |
| `/x-profile` | Bio, pinned post, banner, link, scored on a 100-point [rubric](skills/x-profile/rubric.json). | |
| `/x-plan` | The week: what to post, which format, when, 10 accounts to reply to. | |
| `/x-dm` | One first message and two follow-ups for a specific person. Then stop. | |
| `/x-audit` | Reads your own analytics CSV export and ranks your posts by outlier multiple. | `xanalytics.py` |
| `/x-money` | Original Content Rewards eligibility tracker and ineligible-content linter. Refuses earnings estimates without your own rate. | `ocr.py` |
| `/x-algo` | Regenerates the pinned ranking-weights reference from a `param.rs` you paste. | `weights.py` |

Every skill ends in the same gate: the finished text in a copy-ready block, then
"Reply yes to log it". A "yes" appends one line to a log file on your disk. It never posts.

## The tools, with real output

**Counting.** X counts weighted characters: most characters weigh 1, CJK and most
emoji weigh 2, every URL weighs 23. `xcount.py` vendors the public twitter-text
config and handles emoji sequences.

```
76 / 280 weighted (free)  FITS
  remaining 204, urls 1 (each 23), weight-2 characters 0
```

**Scoring a post.** Five checks: hook, specificity, reply pull, link, bait.

```
POST SCORE  37.1  WEAK   (161/280 weighted)
  LINK         #######.............  35.0  1 link(s) in body
  BAIT         ....................   0.0  like/repost solicitation, "RT/like if" bait, "follow for more"
BLOCKING: engagement bait; hashtag wall (more than 2)
```

Anything that needs a number you did not give is written `{{your number}}`, and
the scorer refuses to pass a draft that still contains one.

**Replies.**

```
REPLY BAND 0/3  SPAM-LIKE   (12 weighted)      <- "Great point!"
  FAIL  no generic praise    reads as generic praise or agreement with nothing added
  FAIL  on topic             shares no content words with the parent post
```

**The humanizer.** Strips invisible Unicode, dashes, stock vocabulary and X
phrases like "let that sink in", flags structural tells for you to rewrite, then scores.

```
  17.8 FLAGGED  ->  78.9 PASS   (+61.0)
```

X posts are short, so a check that needs more text than the draft has returns "too
short" and is left out of the verdict instead of scoring a made-up 50.

**Outlier ranking.** Raw views are not evidence; the multiple over the account's own
median is.

```
- **OUTLIER** 35.65x  @alpha_demo  (41,000 vs 1,150 computed)  [Contrarian Take]
- **OUTLIER** 7.38x  @beta_demo  (2,400 vs 325 computed)  [Price Reveal]
```

## What I actually measured, which is the part worth reading

Method: `measurement/validate.py` on the public
`enryu43/twitter100m_tweets` corpus joined to `enryu43/twitter100m_users`. Three of
its 41 shards, 6.4M tweet rows, tweets from 2019-01-01 to 2022-12-31, originals
only, accounts with at least 50 originals and a median of at least 5 likes. 1,500
accounts, 270,880 tweets scored. Every comparison is **within one account**, which
removes account size. A "hit" is a tweet with 3x or more its account's median likes
(37,861 of them); a "miss" is under 1x (131,549). The corpus has no licence and
X's Developer Policy forbids redistributing content, so I ran it locally and the
repo holds [aggregates only](measurement/results.json): no tweet text, IDs or handles.

**Does the scorer predict hits? No.** Within-account AUC, hits vs misses, macro-averaged
over 1,402 accounts with 95% bootstrap intervals:

| predictor | AUC |
| --- | --- |
| hook score | 0.500 (0.494 to 0.506) |
| full `postscore.py` total | 0.475 (0.469 to 0.482) |
| baseline: tweet length alone | 0.592 (0.584 to 0.600) |
| baseline: number in first line | 0.527 (0.521 to 0.532) |

0.50 is a coin flip. The score does not forecast likes, and a trivial length feature
beats it. I did not tune it on this data afterwards, because that would just fit the
test set. So `postscore.py` is a lint for the problems it names (unfilled
placeholders, bait, thread openers, links in the body, being over length), not a
prediction, and the SKILL.md says so.

**Rule effects, within account** (mean difference in log2 of the multiple; positive means
more likes than that account's norm):

| rule | effect | accounts |
| --- | --- | --- |
| link in the post | +0.59 (+0.53 to +0.65) | 1,398 |
| hashtag wall (3+) | +0.40 (+0.32 to +0.47) | 627 |
| number in the first line | +0.16 (+0.13 to +0.20) | 1,493 |
| question | +0.01 (-0.04 to +0.06) | 887 |
| thread opener | +0.33 (-0.10 to +0.76) | 19, too few |
| engagement bait | +0.73 (-1.00 to +2.33) | 7, too few |

Read this carefully. In 2019-2022 data, **posts with links and hashtag walls got more
likes than the same account's other posts**, the opposite of what the scorer penalises.
That does not make the scorer's link penalty wrong for X today: the corpus ends in April
2023, before Premium reach changes, before the open-sourced ranking code and before
Original Content Rewards; likes are not reach; and links in that era were often
news or brand posts. It does mean the link advice rests on a 2025 outside observation
(Buffer, 18.8M posts), which is labelled "observed, not coded", and not on anything I measured.
Bait and thread openers were too rare in this corpus to say anything.

**Does the outlier multiple do its job? Yes, and it shows why you need it.**

| | Spearman with follower count |
| --- | --- |
| raw likes | 0.566 |
| outlier multiple | 0.025 |

Raw likes mostly measure account size. The multiple removes that.

**How many posts is "enough" for a baseline?** The tools require 3. That is a floor, not
accuracy. Median absolute error of a baseline built from k random posts, in log2 units
(0.59 means off by about 1.5x):

| k posts | median error | 90th percentile |
| --- | --- | --- |
| 3 | 0.59 | 1.81 (about 3.5x) |
| 5 | 0.49 | 1.38 |
| 10 | 0.32 | 0.97 |
| 20 | 0.23 | 0.68 |

So a 3-post multiple of 3x can be an ordinary post. Capture 10 per account if you can, or
supply the account's typical views yourself.

**Match rate:** 100%, but that is trivial: each shard holds whole accounts, and every account
was in the users file. It says nothing about coverage of the 88M-row corpus, of which I used about 7%.

## 30-day dogfood: in progress, numbers land on 2026-11-19

One free account (@mirza_hassan07), 2026-10-21 to 2026-11-19: one post a day, 5 to 10 replies,
link in the first reply, a real hand edit on every draft, goal is client work. The routine is in
[DOGFOOD.md](DOGFOOD.md). On day 30 the author exports their own analytics CSV and runs
[`measurement/dogfood/report.py`](measurement/dogfood/report.py), which prints aggregates only
(no post text) and goes here unedited, good or bad. One account over one month shows nothing
about cause, and the section will say so. Until then there are no dogfood numbers, and none are
implied anywhere above.

## The fine print, which is the honest part

- **It does not post, like, follow, reply, DM or scroll, and never will.** A pull request
  that adds any of that is closed.
- **It cannot know how a post will perform.** The measurement above says so.
- **Nothing is undetectable.** `/x-human` runs five local heuristics. They are not GPTZero,
  Originality, Copyleaks, Winston or Turnitin, and call none of them. Reply downvotes on X can
  list "AI generated" as a reason (reported, Premium users, March 2026, unverified here), and
  posts "created or posted using automated means" are ineligible for Original Content Rewards.
  Read and edit every post.
- **The reply rubric is not published.** The open-sourced code scores replies 0 to 3 with a
  Grok model when the parent or root has over 250,000 followers, but the prompt is excluded
  "to reduce gameability". `replylint.py` is an approximation of it. Smaller accounts go
  through a different spam classifier.
- **No coded link penalty was found** in the ranking parameters. Link advice is "observed, not coded".
- **Weights scale predicted probabilities, not counts.** The file's own comments call "one
  report cancels 468 likes" wrong. This repo never says it. The weights in this repo are the
  ones in the file at the pinned commit (like 0.66, click 0.3, dwell 0.05, not-interested
  -52.272), not the older figures many guides quote.
- **No earnings estimates.** X publishes no per-impression rate. `/x-money` refuses to
  estimate unless you supply your own rate, and labels the result as your assumption.
- **Premium features are untested.** Articles, 25,000-character posts, Original Content
  Rewards and Subscriptions are documented from X's pages, last checked 2026-10-21. The
  Subscriptions gate (2,000 verified followers, 5M impressions, about 97% share) is
  **unverified**; check the app.
- **Numbers go stale.** Every one is in [references/stale.md](references/stale.md) with its
  date and source. The weights table is regenerated by `/x-algo` and pinned to a commit.
- **Tested** locally on Python 3.15 and 3.9.25 on Windows, and in CI on 3.9, 3.11 and 3.13 on
  both ubuntu and windows. The scorer and tools were not tested on macOS.

## Files

```
.claude-plugin/        plugin.json, marketplace.json
skills/x-*/            SKILL.md plus the tools beside it
templates/             voice.md, accounts.md
references/            x-algorithm.md (pinned), x-rules.md, stale.md
measurement/           validate.py (needs pyarrow, numpy), results.json (aggregates)
measurement/dogfood/   report.py: day-30 numbers from your own analytics CSV
DOGFOOD.md             the 30-day routine
tests/                 one test file per tool, invented fixtures
```

## License

MIT. Copyright (c) 2026 Muhammad Hassan.
