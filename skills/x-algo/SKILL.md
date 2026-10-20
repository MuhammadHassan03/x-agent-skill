---
name: x-algo
description: >-
  Refresh the pinned X ranking-weights reference from the user's own copy of
  home-mixer/params/param.rs: parse it, stamp it with the commit hash and date, and
  show what changed since the last version. Use when the user says "update the
  algorithm notes", "what changed in the weights", "regenerate x-algorithm",
  or pastes param.rs. Offline; the user fetches the file, the tool parses it.
---

# x-algo

The weights in `xai-org/x-algorithm` change often. A weights table without a
commit pin is how wrong numbers spread. `weights.py` refuses to run without one.

```bash
python3 weights.py param.rs --commit <sha> --date <commit date> -o ../../references/x-algorithm.md
python3 weights.py param.rs --commit <sha> --date <commit date> --check ../../references/x-algorithm.md
```

It does **not** fetch anything. The user opens
`home-mixer/params/param.rs` on GitHub, saves it (or pastes it), and copies the
commit hash and commit date from the page.

## The loop

1. Ask for the file and the commit hash and date. Do not guess a hash.
2. Run with `-o references/x-algorithm.md`. The tool diffs against the file that
   is already there and prints a "Changed since the previous version" section.
3. Show the user the changes, not the whole table: which weights moved, by how much.
4. If a changed weight affects advice in another skill (reply, share, link, report),
   name the skill and the sentence to review. Do not silently rewrite advice.
5. Update the `checked` dates in `references/stale.md` for the rows this touched.

Real output (excerpt):

```
| param | value | what it scales |
| `ReportWeight` | -234 | viewer reports the post |
| `ShareViaCopyLinkWeight` | 20 | someone copies the link to the post |
| `BidirectionalFollowReplyWeightBoost` | 15 | added to the reply weight when author and viewer follow each other |
| `ReplyWeight` | 5 | reply |
| `FavoriteWeight` | 0.66 | like |

A reply from someone who follows the author and is followed back scales with 5 + 15 = 20.
```

## Rules

- **Weights scale predicted probabilities, not raw counts.** The file's own
  comments say so and call "one report cancels 468 likes" wrong. Never write it.
- Do not extrapolate. The weights say what the model values, not what a post will do.
- The static sections of the output (how to read, reply handling, link posts)
  carry their own verified-at commit and are **not** re-verified by a run. If the
  reply or filter code changed, the user must re-read it and edit `weights.py`.
- Numbers from 2023 blogs are wrong for this snapshot. The output has a "Numbers to
  stop quoting" section; keep it.

## Approval gate

1. Show the finished text in one fenced block, ready to copy. If there is a link,
   show it in a second block labelled "first reply".
2. End the message with: Reply yes to log it.
3. On "yes", append one line to `~/.claude/x/log.md` (or the handle's folder):
   date, skill, first line. That is all "yes" does.
4. Never post, like, follow, reply, DM or scroll. You write; the human posts, by
   hand, on x.com.
