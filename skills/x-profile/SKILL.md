---
name: x-profile
description: >-
  Score an X profile out of 100 against an 11-part rubric and rewrite the parts
  that lose points: bio (160 characters), pinned post, banner line, header link,
  name and handle. Use when the user says "optimize my profile", "rewrite my
  bio", "score my X profile", "what should I pin", or pastes their bio and asks
  how it reads. Free-tier default. Never edits the profile.
---

# x-profile

The profile is the page a stranger lands on after one good reply. It has one job:
make the right person follow, then take the one next step off X.

`rubric.json` in this folder is the scoring sheet: 11 items worth 100 points, each
with what a pass looks like, what a fail looks like, and the fix.

```bash
python3 ../x-post/xcount.py bio.txt     # bio must be 160 characters or fewer (weighted)
```

## Before you write

1. Read `~/.claude/x/voice.md` and `accounts.md` if several handles exist.
2. Ask for: the current bio, the pinned post, the banner text, the profile link,
   handle and display name, and **one real proof point** (a number, a named client
   type, a shipped thing). If they have none, the bio gets none. Never invent one.
3. Default persona: free account, small following, off-platform income. No
   Premium badge features are scored.

## The loop

1. **Score it.** Go through `rubric.json` item by item, award 0 to the item's points
   with a one-line reason each, and total it. Show the table. Bands: 85 to 100
   ready, 65 to 84 fixable in one sitting, under 65 rewrite the promise first.
2. **Fix the biggest losers first.** The bio promise (20) and the pinned post (20)
   are 40% of the score. Do those before the banner.
3. **Bio.** Three options, different angles, each counted with `xcount.py`. Shape:
   who you help, the result, one proof point. Adjectives lose to nouns. Run each
   through `/x-human`.
4. **Pinned post.** One strong post, not a thread teaser, that answers "why follow
   you". Write it with `/x-post`. The link goes in the first reply.
5. **Banner line.** Six words or fewer, away from where the avatar covers it,
   readable on a phone.
6. **One link, one promise** that matches the bio.
7. **Re-score** and show the before and after total.

## Rules

- No income claims in the bio. They are an Original Content Rewards risk and a trust
  loss.
- No "follow for more", no hashtag strings, no emoji padding.
- No invented credentials, clients or numbers. Placeholders: `{{your number}}`.
- The skill never opens the profile or edits it. The user changes it by hand.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block labelled "first reply".
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
