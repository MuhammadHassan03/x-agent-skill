---
name: x-article
description: >-
  Plan and draft a long-form X Article or a long Premium post: outline, draft,
  a first-screen hook, and an originality checklist. Premium feature, documented
  but not tested by the author. Use when the user says "write an article",
  "long post", "essay for X", or has material too long for a thread and has a
  Premium account. Offers the thread route for free accounts. Never posts.
---

# x-article

**Status of this skill: documented, not tested by the author.** The author runs
a free account. Articles and 25,000-character posts need Premium. Everything here
follows X's published pages (checked 2026-10-21, `references/x-rules.md`) and the
tools run, but the Articles editor itself has not been used. Say that to the
user in your first reply.

If the user is on a free account, stop and offer `/x-thread` instead. Do not
write a 3,000-word draft they cannot post.

```bash
python3 ../x-post/xcount.py article.txt --premium     # 25,000 limit for long posts
```

On Windows, where this says `python3`, use `python`.

## Before you write

1. Read `~/.claude/x/voice.md`. Confirm Premium. Ask what the article is for: a
   lead magnet for the newsletter, proof for a service, a stance.
2. Require **material**, not a topic: the user's own story, numbers, a project,
   a decision. An article without a first-hand fact is aggregation, which Original
   Content Rewards excludes. **No invented figures**: `{{your number}}` and flag it.

## The loop

1. **Outline in one screen.** Claim, three to five sections, each with the one
   specific fact that carries it. Show it and get a yes before drafting.
2. **The first screen.** The title and first two or three sentences decide whether
   anyone reads on. Where "Show more" truncates is **unverified: measure before
   shipping** (`references/stale.md`); do not state a character count for it.
   Write the opening so it works if cut anywhere.
3. **Draft** the sections in the user's voice. Short paragraphs. No section
   restates the one before.
4. **Count.** `xcount.py --premium`. Under 25,000 weighted characters.
5. **Originality checklist** (print it filled in):
   - [ ] Every claim of fact is the user's own experience or is sourced
   - [ ] No paragraph is mostly someone else's text, paraphrased or not
   - [ ] At least one number, name or event only this author has
   - [ ] No "monetization coaching" angle: an article that is only about maximising
         payouts is ineligible
   - [ ] No engagement ask ("like and repost if")
   - [ ] Written by the user's facts; the human reads and edits every line
6. **Humanize** with `/x-human`, section by section (the tools need a few
   sentences to score burstiness; very short sections return "too short").
7. **Plan the off-platform path.** One link, in the closing section or the first
   reply. Say which, and why.

## Rules

- No invented numbers, clients or results.
- No fake authority ("I studied 10,000 accounts"). Use only what the user did.
- If an Article is not available to the user in their country or tier, say so and
  fall back to a thread.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block labelled "first reply".
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
