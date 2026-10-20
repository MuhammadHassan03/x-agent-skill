---
name: x-post
description: >-
  Turn one raw idea into an X post: three hooks off 19 formulas, scored offline,
  one humanized draft counted in weighted characters, ready to copy and post by
  hand. Use when the user says "write a post about X", "tweet this", "give me a
  hook", "turn this into a post", or has an idea and no first line. Free account
  by default (280 weighted characters, link in the first reply). Never posts.
---

# x-post

One idea in, one post out. Two tools live beside this file and both run. Use
them; do not eyeball the hook or the length. Run them from this skill's folder.

```bash
python3 xcount.py draft.txt                 # weighted length, the way X counts
python3 postscore.py draft.txt              # hook, specificity, reply pull, link, bait
python3 postscore.py --hooks hooks.txt      # rank three candidate first lines
```

## Before you write

1. Read `~/.claude/x/voice.md` (or `~/.claude/x/<handle>/voice.md`). If it does
   not exist, ask for three of the user's own posts, infer the voice, and write
   the file from `templates/voice.md`.
2. Default persona: a small account on the free tier, earning off-platform
   through clients, a product or a newsletter. 280 weighted characters. Do not
   assume Premium. Premium features are documented in `references/x-rules.md`,
   not tested by the author.
3. If the idea is thin, ask one batched question: what happened, to whom, what
   did it cost or return. A post needs one specific true thing.
4. **Never invent a number.** If the draft needs a figure the user did not give,
   write `{{your number}}` and say so. `postscore.py` blocks any draft that still
   contains a `{{...}}`.

## The loop

1. **Three hooks, not one.** Choose three formulas from `hooks.json` that fit the
   idea. Different formulas, not three rewrites. Put the first lines in a file.
2. **Score them.** `python3 postscore.py --hooks hooks.txt`. Show the ranking.
   If the best is under 50, you do not have the hook yet. Get a better fact from
   the user instead of editing.
3. **Write the draft** on the winning hook. One idea. Plain words. Fits 280
   weighted characters. The link, if there is one, does not go in the body.
4. **Count and score it:** `xcount.py` then `postscore.py`. Fix every flag.
5. **Humanize it:** run `/x-human` before showing anything.
6. **Print the block**, with the link as a separate first-reply block.

Real output (sample draft, free account):

```
POST SCORE  93.8  STRONG   (203/280 weighted)
----------------------------------------------------------------
  HOOK         ###################.  95.0  61 weighted characters
  SPECIFICITY  #################### 100.0  9 concrete markers in 42 words
  REPLY PULL   ###############.....  75.0  question present
  LINK         #################### 100.0  no link in body
  BAIT         #################### 100.0  none
```

A weak draft looks like this, and `postscore.py` exits non-zero on it:

```
POST SCORE  37.1  WEAK   (161/280 weighted)
  BAIT         ....................   0.0  like/repost solicitation, "RT/like if" bait, "follow for more"
               - engagement bait ... This is also an Original Content Rewards ineligibility problem
BLOCKING: engagement bait; hashtag wall (more than 2)
```

## Rules that matter

- **Link in the first reply, not the body.** Label it honestly: *observed, not
  coded*. The open-sourced ranking parameters contain no link penalty. Reach loss
  on link posts from non-Premium accounts was observed in March 2025 (Buffer,
  18.8M posts). It is a measurement from outside, not a coded rule.
- **No bait.** "Like and repost if", "follow for more", "bookmark this" are ranking
  risks and Original Content Rewards ineligibility problems. Cut them.
- **At most one hashtag.** Zero is normal.
- **The first line works alone.** No "A thread", no "Here's why", no "Let me explain".
- **Replies are cheap to earn with a real question.** End on something answerable
  in one line. "Thoughts?" is not that.
- **Weights scale predicted probabilities, not raw counts.** Never repeat the
  "one report cancels 468 likes" line. See `references/x-algorithm.md`.

## Fine print

`postscore.py` is five local heuristics. It does not know how a post will do.
Its measured accuracy is in the README. It never says a post is "undetectable"
or "will go viral".

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block labelled "first reply".
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
