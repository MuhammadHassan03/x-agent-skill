# Security

## What this repo does with your data

Nothing leaves your machine. Every tool the skills use is Python standard library only and
makes no network calls. The one exception is `tools/algo_watch.py`, a maintainer script that CI runs
weekly; it fetches one public file (`home-mixer/params/param.rs` from xai-org/x-algorithm) through the
GitHub API and sends nothing about you or your text. There is no telemetry, no analytics and no update
check. There are no secrets to configure and none should ever be committed.

Voice and log files live in `~/.claude/x/` on your own disk.

## The algorithm tracker's trust model

`tools/algo_watch.py` reads one file that someone else controls, and a weekly workflow can commit
the result to the default branch. Upstream text is therefore treated as hostile data:

- **Three jobs, three scopes.** `check` has `contents: read`, does not keep the checkout credential, and
  is the only job that parses upstream text or runs pytest. `commit` is the only job with
  `contents: write`; it runs no pip and no pytest, and copies the staged files only after
  `tools/algo_watch.py --verify-tree` accepts them (four generated files, no links, weights still valid,
  README unchanged outside the changelog markers). `report` has `issues: write` and no checkout.
- **Pinned.** Every action is pinned to a full commit SHA. The test dependencies of the tracker are
  installed with `--require-hashes` from `tools/algo-ci-requirements.txt`. Refresh both by hand when
  you want an update; nothing bumps them for you.
- **Bounded.** The download is capped at 1 MiB, the parser is linear-time on hostile input, and every
  job has a timeout.
- **Token.** The read-only token goes to `api.github.com` only, and a redirect to another host is refused.
- **Neutralised.** Upstream strings are wrapped in backticks, with backticks, pipes and angle brackets
  replaced, before they reach the README, a commit message or an issue. Commit hash and date from the API
  must match their exact shapes.
- **Fails loudly.** Any unexpected error exits 2 and opens an issue; nothing is written unless validation
  passes (weight keys present, numeric, none moved more than 10x).

Residual risk: the tracker pushes to the default branch with no pull request and the repository has no
branch protection, so the owner's own account, or a compromise of GitHub itself, is outside this model.

## Reporting a problem

Open a private security advisory on the GitHub repository, or email the
maintainer through the address on their GitHub profile. Please include the tool,
the input that triggers it and the Python version. Expect an acknowledgement
within seven days.

Anything that would make a tool open a socket, spawn a browser or call the X
API is a vulnerability for this project, not a feature request.
