---
name: x-audit
description: >-
  Post-mortem on what the user already published: read their own analytics CSV
  export, rank posts by outlier multiple over their own median, compare link vs
  no link, length, question, weekday and hour, and say what to repeat and what to
  stop. Use when the user says "what's working", "why did this flop", "audit my
  posts", "read my analytics", or shares a Creator Studio export. Offline.
---

# x-audit

The user exports their own post analytics from their own account and gives the
file to this skill. It reads the file. It never touches X.

```bash
python3 xanalytics.py analytics.csv
python3 xanalytics.py analytics.csv --top 10 --json
python3 xanalytics.py analytics.csv --include-replies
```

On Windows, where this says `python3`, use `python`.

X does not document the organic export's columns, so headers are matched
flexibly. If `xanalytics.py` says it found no impressions column, it prints the
headers it did find; show them to the user, do not guess a mapping.

## Method (say this to the user)

- Replies are dropped by default (a reply flag, an "in reply to" value, or text
  starting with `@`).
- The baseline is the **median impressions of the user's own posts**, so it needs
  3 or more. Every post is shown as a multiple of it. Raw impressions never rank anything.
- Feature comparisons (link in body, length, question, weekday, hour) show the median
  multiple per group, and only for groups of 3 or more posts.
- **These are correlations on a small sample.** Under 30 posts the tool says so,
  and so must you. A comparison is a prompt for a test, not a finding.

Real output (sample file of 22 invented rows):

```
X ANALYTICS  20 posts, baseline 996 median impressions

TOP (outlier multiple)
    5.49x      5,465  eng 2.7%  Everyone says post daily. I do not.
    3.95x      3,930  eng 3.0%  I charge $1,500 for a page. Here is how I got there.

FEATURES (median multiple, groups of 3+ only)
  link in body       link: 0.33x (n=4)  |  no link: 1.64x (n=16)
  question           question: 2.12x (n=4)  |  statement: 0.41x (n=16)

Note: fewer than 30 posts: treat comparisons as prompts to test, not findings.
Note: 2 reply row(s) dropped (use --include-replies to keep them)
```

## The loop

1. Ask for the CSV path. If none, tell them where to look in their own analytics
   page and stop. Do not paste invented numbers.
2. Run the tool. Show the table.
3. Read the **top three** posts with the user: what is the claim, the specific
   number, the stance, the format? Say what they share. Then read the **bottom
   three** the same way.
4. Give at most three actions: one to repeat, one to stop, one to test. Each names a
   post as evidence. Do not generalise from one post.
5. If link posts are low, repeat the honest framing: *observed, not coded*, and the
   move is a link in the first reply, which the user can test on their own account.
6. Offer to feed the result to `/x-plan`.

## Rules

- Never compare the user to other accounts here. That is `/x-viral`.
- Never state an engagement-rate benchmark you cannot source.
- Post text from the export stays on the user's disk. Do not paste it into the repo.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block labelled "first reply".
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
