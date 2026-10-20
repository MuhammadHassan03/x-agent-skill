# 30-day dogfood

One free account, one month, the skills used by hand the way a stranger would use them.
Start: 2026-10-21. Day 30: 2026-11-19. The numbers land in the README on that date, whatever they are.

Account: @mirza_hassan07, free tier. Goal: replies and DMs that turn into contract work. No newsletter, no product.

## Daily routine (about 40 minutes)

1. **One post** (`/x-post`). Something that happened in real work that day. Three hooks, score them,
   pick one, write it.
2. **Five to ten replies** (`/x-reply`) under accounts bigger than yours. Read the parent first. If you have
   nothing to add, skip it. One reply per thread; edit it instead of stacking a second.
3. **Link in the first reply**, never the body, and only when the post earned it.
4. **Make a real edit on every draft.** Change a word, cut a line, add a detail only you know. Run `/x-human`
   after your edit, not before. A draft you did not touch is not logged as edited.
5. **Say `yes` to log it.** The skill appends one line to `~/.claude/x/log.md`. Add `| edited: yes` or
   `| edited: no` at the end of the line.
6. **You post, by hand, on x.com.** Never a scheduler script, never a bot, never a browser extension.

## Rules for the month

- No invented numbers. Missing figure means `{{your number}}`, and you fill it or cut the line.
- No bait, no hashtags beyond one, no thread opener as the hook.
- DMs: only to a person you have a real reason to write to, one at a time, three messages at most (`/x-dm`).
- Do not change the routine halfway. If something breaks, write down what and why, then carry on.
- Count by hand once a week: followers, leads (a reply or DM about work), calls, clients. Write them in the log.

## Day 30 (2026-11-19)

1. Export your own post analytics from your account (Creator Studio or Analytics) as CSV. Keep it outside the
   repo. The export contains your post text and must not be committed.
2. Run:

```bash
python measurement/dogfood/report.py ~/Downloads/analytics.csv --start 2026-10-21 --end 2026-11-19 \
    --followers-start <day 1 count> --followers-end <day 30 count> \
    --leads <n> --calls <n> --clients <n> --log ~/.claude/x/log.md
```

3. Paste the markdown block it prints into the README section "30-day dogfood". It holds aggregates only:
   no post text, no post IDs.
4. Report what happened, including a flat or bad result. One account over one month shows nothing about cause.
   Say that in the section.
