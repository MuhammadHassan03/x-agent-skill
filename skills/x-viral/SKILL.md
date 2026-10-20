---
name: x-viral
description: >-
  Find out what is working in the user's niche without scraping: the user notes
  down posts they found by hand, and this ranks them by outlier multiple over
  each account's own typical post, names the hook formula each one used, and
  writes a swipe file. Use when the user says "what's working in my niche",
  "research", "swipe file", "what should I copy", or "which hooks win". Offline.
  Never browses X, never scrapes.
---

# x-viral

Raw views are not evidence. A 2,000,000-follower account at 400,000 views had a
quiet day; a 4,000-follower account at 400,000 views found something. `swipe.py`
ranks on the **outlier multiple**: views divided by that account's own typical
post.

```bash
python3 swipe.py captured.tsv
python3 swipe.py captured.tsv --min-multiple 3 --top 15
python3 swipe.py captured.tsv --out ~/.claude/x/swipe.md
```

## How the data gets here (and how it does not)

The user browses X **themselves, by hand, at human speed**, in their own
browser. They write down what catches their eye. They paste or type it into a
TSV or CSV. That is the whole pipeline.

**This skill never opens X, never drives a browser, never scrapes, never runs a
script in the page.** X's automation rules say scripting the website can lead to
permanent suspension. If the user asks "can you just go and look", the answer is
no, and the reason is that rule. Offer to rank what they paste.

Columns (headers are matched flexibly): `account`, `views` (or `impressions`),
`hook` (the first line), and optionally `median` (the account's typical views).
Numbers like `12.4K` and `1.2M` work.

```
account	views	hook
@alpha_demo	1.2K	I sent 400 cold DMs in 30 days. 11 replied.
@alpha_demo	900	morning thoughts
@alpha_demo	1,100	shipped a small thing today
@alpha_demo	41K	Everyone says post daily. I posted 4x a week and replies went up.
```

## Telling the user how to capture well

- For each account, note **3 or more posts**, and include ordinary ones, not only
  the hits. With a hits-only sample the computed median is inflated and the
  multiple is understated. Or note the account's typical views in `median`.
- Accounts with neither a median nor 3 posts are listed as "no baseline" and never ranked.
- Prefer accounts near the user's size. A multiple at 4,000 followers transfers
  better than one at 400,000.

## The loop

1. Ask for the file. If they have not collected anything, tell them how to
   (above) and stop. Do not fill the gap with invented examples.
2. Run `swipe.py`. Show the ranking and the formulas among the outliers.
3. Read the top hooks with the user. Name what is actually shared: the claim
   shape, the specific number, the stance. A formula label is a label, not a cause.
4. Write `~/.claude/x/swipe.md` (`--out`). `/x-post` reads it and prefers formulas
   that are working in this niche.

Real output:

```
- **OUTLIER** 35.65x  @alpha_demo  (41,000 vs 1,150 computed)  [Contrarian Take]  Everyone says post daily. ...
- **OUTLIER** 7.38x  @beta_demo  (2,400 vs 325 computed)  [Price Reveal]  I charge $1,500 for a landing page. ...
- 1.04x  @alpha_demo  (1,200 vs 1,150 computed)  [unclassified]  I sent 400 cold DMs in 30 days. 11 replied.

## No baseline (not ranked)
- @lonely_demo: needs a median column or 3+ captured posts
```

## Rules

- **Never copy a post.** The swipe file is for the shape of the idea. Copied,
  minimally modified and aggregated content is ineligible for Original Content
  Rewards and reads as theft. Write the user's own post from their own facts.
- **Small n.** Say so every time. With under 30 captured posts, the formula
  summary is a prompt to test, not a finding.
- Post text and handles in the swipe file stay on the user's disk. Do not commit them.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block labelled "first reply".
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
