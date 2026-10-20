# Rules for working in this repo

- Commits: one author and committer, Muhammad Hassan, using the GitHub noreply address. Never add a
  trailer, footer or line that credits an AI tool or a session (no co-author lines, no "generated with"
  lines, no session ids), in commit messages or pull request descriptions. `.claude/settings.json`
  turns the tool's own attribution off; keep it that way. Sign off with `git commit -s` (DCO).
- Read CONTRIBUTING.md first. This repo writes text; it never posts, likes, follows, DMs or scrapes.
- Python 3.9+, standard library only in `skills/`. No em dashes anywhere (a test enforces it).
- Run `python -m pytest` before every commit.
