---
name: x-money
description: >-
  Track Original Content Rewards eligibility against X's published thresholds
  and lint a batch of posts for the patterns that make content ineligible. Refuses
  to estimate earnings unless the user supplies their own rate. Use when the user
  says "am I eligible", "how close am I to monetization", "OCR", "creator
  payouts", or "will this get me demonetized". Premium-only program: documented,
  not tested by the author.
---

# x-money

**Status: documented, not tested by the author.** The program needs an active
Premium plan and the author is on a free account. The rules below come from X's
own help page (checked 2026-10-21, `references/x-rules.md`).

```bash
python3 ocr.py status --premium yes --verified-followers 310 --impressions-90d 120000 --age18 yes --country-listed yes
python3 ocr.py lint posts.txt              # posts separated by a line of ---
```

On Windows, where this says `python3`, use `python`.

The user reads their own numbers off their own Creator Studio screen and types
them in. Nothing is fetched or verified.

## What the thresholds are

Active Premium plan, at least 500 verified followers, at least 500,000 Home
Timeline impressions from verified users in the last 90 days (replies excluded),
18 or older, a listed country, original content. Payouts every two weeks, $30
minimum. X reviews each application, and meeting the criteria does not guarantee
admission.

Real output:

```
NOT ELIGIBLE
  MISS active Premium plan: no: enrollment needs an active Premium plan
  MISS 500 verified followers: 310 / 500 (62%), 190 to go
  MISS 500,000 verified-viewer Home impressions, 90 days, replies excluded: 120,000 / 500,000 (24%), 380,000 to go
  ok   18 or older: yes
  ok   listed country: yes
```

## The refusal

**X publishes no per-impression rate.** So:

- Never state what a number of impressions is "worth".
- `ocr.py status --estimate` exits with an error unless `--rate-per-1000` is given. If
  the user supplies a rate, the output labels it "YOUR rate; X publishes none" and
  is arithmetic on an assumption. Say so every time.
- Never repeat income claims from threads or screenshots.

## The linter

`ocr.py lint` flags what a pattern can see: engagement solicitation ("like and
repost if", "follow for more", "bookmark this"), monetization-coaching angles,
automation markers, and copied or aggregated markers ("RT @", "h/t", "source: @").
It cannot tell whether a post is original. For that, ask the user the one real
question: *did you create this from your own work, voice or expertise?*

```
post 2: engagement solicitation
    Like and repost if you want the template. Follow for more.
post 3: monetisation coaching
    How to make money on X with Original Content Rewards in 7 steps
```

## Be straight with the user

- Payout impressions are a different pool from the eligibility impressions: they
  are unique impressions from **Premium users** on Home with at least half the post
  visible. A big verified-viewer count does not tell them what a post pays.
- A free-account user cannot enroll. Do not advise buying Premium to chase a
  payout. That is the user's decision and a financial one; this tool gives
  thresholds, not advice.
- Do not tell anyone to farm impressions, buy followers, or use automation. Those
  breach continuous eligibility.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block labelled "first reply".
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
