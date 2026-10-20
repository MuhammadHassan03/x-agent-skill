---
name: x-thread
description: >-
  Turn a long draft into an X thread: split at paragraph and sentence
  boundaries into posts of 280 weighted characters or fewer, links pulled out of
  the body and gathered in the last post, hook post checked. Use when the user
  says "turn this into a thread", "split this up", "this is too long for one
  post", or pastes an essay, notes or a transcript. Never posts.
---

# x-thread

`thread.py` does the splitting so the arithmetic is right. You do the editing.

```bash
python3 thread.py draft.txt                # posts with weighted counts
python3 thread.py draft.txt --number       # prefix 1/N, counted in the budget
python3 thread.py draft.txt --pack         # merge short paragraphs
python3 thread.py draft.txt --json
```

On Windows, where this says `python3`, use `python`.

It imports `../x-post/xcount.py`, so keep the plugin folder intact.

## Before you write

1. Read `~/.claude/x/voice.md` (or the handle's). Free account by default, so every
   post is 280 weighted characters. URLs weigh 23. CJK and most emoji weigh 2.
2. Ask whether it should be a thread at all. If it fits one post, say so and send
   it to `/x-post`. A thread is for something that needs steps.
3. **No invented numbers.** Missing figure: `{{your number}}`, and say so.

## The loop

1. **Find the hook.** The first post must work alone. Run `postscore.py --hooks`
   on two or three candidate openers, pick the best, put it first.
2. **One idea per post.** A blank line in the draft is a post boundary. Cut
   filler until each paragraph earns its own post.
3. **Run `thread.py`.** Read the warnings; each one is a decision for you:
   - a link was removed and the sentence now dangles: reword it
   - a sentence was split mid-sentence: rewrite it shorter
   - the hook post scores under 55: fix the opener, not the rest
4. **Links go last.** `thread.py` moves every link to the final post under the
   line that introduced it. Observed, not coded: link posts from free accounts
   were seen to reach less. The thread's hook never carries a link.
5. **Humanize each post** with `/x-human`. Then re-run `thread.py` so counts stay true.
6. **Print the block** as numbered posts.

Real output (sample draft with a link):

```
--- post 1/4  (52/280)
I sent 400 cold DMs in 30 days and 2 became clients.
--- post 2/4  (239/280)
Here is the pattern. The two who said yes got a question about their pricing page. ...
--- post 3/4  (153/280)
The question was always specific. ...
--- post 4/4  (103/280)
What is the first line you send to a stranger?

Full breakdown of the messages:
https://example.com/dm-breakdown
---
1 link(s) moved to the last post.
```

## Rules

- No "A thread", no "🧵", no "1/ Let's dive in". The first post is a claim.
- No "RT the first post", no "follow for more". Bait is a ranking risk and an
  Original Content Rewards ineligibility problem. `thread.py` warns on it.
- Long threads lose readers. `thread.py` warns past 12 posts. Cut to the strongest.
- Posts in your own thread are your replies to yourself. That is normal. What to
  avoid is stacking several replies under someone else's post: see `/x-reply`.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block labelled "first reply".
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
