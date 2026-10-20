---
name: x-plan
description: >-
  Plan the user's week on X: what to post, which format, when, and 10 accounts to
  reply to, built around reply-first growth and an off-platform goal. Use when the
  user says "plan my week", "what should I post", "content calendar", "I have
  nothing to post about", or wants a posting schedule. Free account by default.
  Plans only; never schedules or posts.
---

# x-plan

A small free account grows by being seen next to bigger accounts, then converting
a few of those people off-platform. The plan is built around that, not around
posting volume.

No tool here: this is a planning skill. Use `xcount.py`, `postscore.py` and
`replylint.py` from the other skills on the drafts it produces.

## Before you plan

1. Read `~/.claude/x/voice.md`, `~/.claude/x/log.md` (what was posted lately) and
   `~/.claude/x/swipe.md` if `/x-viral` wrote one.
2. If the user has a Creator Studio export, run `/x-audit` first and plan from what
   it shows about their own posts. Their data beats any default below.
3. Ask three things, batched: how many minutes a day they truly have, the one
   off-platform goal this month (newsletter signups, client calls, a product), and
   what happened in their work this week that could be a post. A plan with nothing
   true to post is padding. If they have nothing, say so.

## The week

Default shape for 30 to 45 minutes a day. Scale down, never up.

| slot | what | why |
|---|---|---|
| 3 to 4 days | one original post, from something that happened | original, specific, first-hand content is the only kind worth writing and the only kind that can ever be rewarded |
| 5 days | reply session: 10 accounts, 3 to 5 good replies | replies carry the most weight in the ranking weights and put you in front of other audiences |
| 1 day | one thread or one longer post if there is a story that needs steps | most weeks there is not |
| 1 day | review: what moved, what did nothing | feeds the next plan |
| any day | one first-reply link to the off-platform goal, under a post that already earned attention | free accounts keep links out of the body |

Do **not** pad with filler to hit a count. Do not schedule posts with a tool. If
the user wants X's native scheduler, how it behaves is **unverified: measure before
shipping** (`references/stale.md`); suggest they test it on one post, and note that
the human still has to set it up by hand.

## The 10 accounts

Ask the user to name them, or give a method for finding them by hand: accounts
about 5 to 50 times their size, in their niche, that post often and whose replies
are not already 400 deep. The user adds them to a list in the app and reads that
list. **Do not invent handles.** Never output a list of real accounts you have not
been given. Never script follows, lists or likes.

## Output

For each day: the slot, a one-line seed for the post (from the user's real
material), the format, and a suggested time window **marked as a guess** until the
user's own `/x-audit` data says otherwise. Then the reply session, then the one
metric to look at at the end of the week.

## Rules

- No "post 3 times a day". No volume targets the user did not choose.
- Times of day are a hypothesis. `xanalytics.py` compares hours on their own posts
  once they have 30 or more.
- Everything is a draft or a seed. The human writes, schedules and posts.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block labelled "first reply".
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
