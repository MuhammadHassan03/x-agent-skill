---
name: x-human
description: >-
  Clean up a draft: strip invisible Unicode, em dashes, stock AI vocabulary and
  engagement-farm phrases like "let that sink in" and "a thread", then score it
  on a five-check panel. Use when the user says humanize, "does this sound like
  AI", "remove the em dashes" or "de-slop this". Local heuristics only; never
  claims a text is undetectable.
---

# x-human

Two tools run in this folder. Use them; do not eyeball it.

```bash
python3 humanize.py draft.txt --report        # clean it, show what changed
python3 detect.py draft.txt                    # five checks
python3 detect.py before.txt after.txt         # prove the delta
```

On Windows, where this says `python3`, use `python`.

Both read `slop.json`: stock words and phrases with plain replacements, invisible
character classes, typographic substitutions and structural tells. The
`x` family holds phrases from engagement-farming posts. It is meant to be edited.
If the user's own voice uses a word the lexicon strips, delete it from the file.

## What gets fixed automatically

1. **Invisible characters.** Zero-width spaces, word joiners, soft hyphens, BOMs,
   bidi controls, Unicode tag characters; non-breaking spaces become spaces. A
   zero-width joiner that glues an emoji family or skin tone is kept, because
   deleting it breaks the emoji.
2. **Typography.** Em dash to comma, en dash to hyphen, curly quotes to straight,
   ellipsis to three dots.
3. **Lexicon.** delve, leverage, robust, seamless, "it's important to note that",
   and the X block: "a thread", "let that sink in", "here's the kicker", "this is
   huge", "bookmark this", "RT if", "game-changer", "Great point!", "follow for
   more". URLs, @mentions and $cashtags are left alone.

## What is flagged, not rewritten

Shapes need judgement, so they are reported and **you** rewrite them:

- "Not just X, it's Y"
- rule-of-three lists of single words
- hashtag walls (3 or more)
- numbered-emoji bullets and emoji bullet lists
- engagement bait
- a thread opener as the hook
- a staircase of very short lines
- uniform sentence length

## The five checks

Each scores 0 to 100, higher is more human. BURSTINESS (sentence-length
variation), SPECIFICITY (numbers and names), SLOP DENSITY, FINGERPRINT (invisible
characters, dashes, curly quotes), VOICE (contractions, person, structural tells).

X posts are short. A check that needs more text than the draft has returns
"too short" and is **left out** of the verdict instead of scoring a fake 50, and
the output says how many of the five were scored. PASS needs 70 or more overall
and no scored check under 55.

Real before and after on a sample draft:

```
  17.8 FLAGGED  ->  50.1 REVIEW   (+32.3)
```

That is one mechanical pass: better, still not a pass. The structural tells are left for you to rewrite.

```
19 machine artefacts removed, 3 structural tells flagged for rewrite
  1x  in today's fast-paced world  -> (deleted)   [openers]
  1x  let that sink in  -> (deleted)   [x]
  1x  leverage  -> use   [verbs]
4. STRUCTURAL TELLS  (not auto-fixed, rewrite these yourself)
  1x  "Not just X, it's Y"
  2x  Numbered emoji bullets
```

## Say this honestly

These are five local heuristics. They are **not** GPTZero, Originality,
Copyleaks, Winston or Turnitin, they call none of them, and nothing is uploaded.
Fixing what they measure tends to move those numbers because they measure the
same underlying things. That is the whole claim. **Never tell the user a text is
undetectable.** Also: on X, "AI generated" can be given as a reason for a reply
downvote (reported, Premium users, March 2026), and automated posting is
ineligible for Original Content Rewards. A human reading and editing every post
is the point.

## Order of operations

1. `humanize.py draft.txt -o clean.txt --report`
2. Read the structural flags. Rewrite those lines yourself.
3. `detect.py draft.txt clean.txt` for the before and after.
4. Not PASS: fix the weakest check named in the output and go again. Two rounds
   is normal. Five means the draft was written by formula; the fix is a
   different draft.
5. Show the cleaned text and the score. Never the score alone.

## Without the tools

If you cannot run `humanize.py` and `detect.py`, edit by hand and say so: replace em dashes with a comma
or a full stop, straighten curly quotes, cut stock phrases ("let that sink in", "a thread", "delve",
"leverage", "it's important to note"), and rewrite flagged shapes ("not just X, it's Y", numbered-emoji
bullets, hashtag walls, bait). No score is available without the tools; do not invent one.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block titled FIRST REPLY.
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
