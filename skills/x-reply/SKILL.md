---
name: x-reply
description: >-
  Write replies under other people's posts that read as a person with something
  to add: checked against an approximation of X's 0-3 reply rubric, with
  compliment-only openers refused and self-reply chains blocked. Use when the
  user pastes a post and says "reply to this", "what do I say here", "engage
  with this", or wants a batch of replies for a daily reply session. Never posts.
---

# x-reply

For a small free account, replies under larger accounts are the main growth
lever, and the easiest place to get filtered. `replylint.py` checks every draft.

```bash
python3 replylint.py reply.txt --parent parent.txt
python3 replylint.py reply.txt --parent parent.txt --prior-replies-in-thread 1
python3 replylint.py reply.txt --json
```

## What the source shows, and what it does not

From the open-sourced Grox code (`grox/flows/reply_spam/`, commit pinned in
`references/x-algorithm.md`):

- A Grok model scores replies **0 to 3** with a reason when the parent or root
  account has more than 250,000 followers. The prompt that defines the rubric is
  deliberately not published. **The bands in `replylint.py` are an approximation,
  not X's rubric.**
- Under smaller accounts, replies go through a different spam classifier.
- A multi-step filter looks at threads where the replier replies to their own
  reply, under a root account with 1,000 or more followers. It needs 2 or more
  flagged posts from that author. Flagged posts get a reply ranking score of 0.

## Before you write

1. Read `~/.claude/x/voice.md`. If missing, ask for three of the user's replies.
2. Ask for the parent post's text. Without it you cannot check on-topic.
3. Ask whether the user already replied in this thread. If yes, **edit the first
   reply; do not stack a second.** Pass `--prior-replies-in-thread N`.
4. **No invented numbers or experiences.** If the reply needs the user's own
   figure or story, ask for it. A reply that fakes experience is worse than none.

## The loop

1. **Read the parent for the one thing worth adding.** A fact, an example, a
   counter-case, a question that exposes a gap. If you have nothing, say so.
   Skipping a post is a valid answer.
2. **Draft 40 to 280 weighted characters.** Lead with the substance. No compliment
   opener. "Great point", "This!", "So true", "100%", "Well said" are refused.
3. **Lint it.** Fix every FAIL; a FAIL caps the band at 0.
4. **Humanize** with `/x-human`. Replies are short, so the checks that need more
   text return "too short" instead of a fake score.
5. **Print the block.**

Real output:

```
REPLY BAND 3/3  STRONG   (125 weighted)
  pass  no generic praise    ok
  pass  on topic             shares ['cold', 'dms', 'page'] with the parent
  pass  specific             has a number, a name or a first-person event
  pass  adds information     gives a reason, an example, a number or a counter-point

REPLY BAND 0/3  SPAM-LIKE   (12 weighted)      <- "Great point!"
  FAIL  no generic praise    reads as generic praise or agreement with nothing added
  FAIL  on topic             shares no content words with the parent post
```

## Rules

- **No generic praise.** Refuse it even when the user asks for it. Offer a version
  that adds something, or skip the post.
- **No links, no "check out my", no hashtags** in a reply under someone else's post.
- **Never AI-reply bots, never keyword-triggered replies.** X's automation rules
  forbid automated replies based on keyword searches. The human reads each post and
  types each reply.
- **Batch limit:** draft at most as many replies as the user will read the parent
  posts for. Ten thoughtful replies beat forty quick ones.
- **No self-reply chains** under other people's posts. One reply, edited.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block labelled "first reply".
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
