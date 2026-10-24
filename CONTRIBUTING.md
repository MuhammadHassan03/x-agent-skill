# Contributing

## The one rule

This repo writes, you post. A pull request that adds posting, liking,
following, DMing, scrolling, scraping, browser automation, an X API client, a
Playwright or Selenium recipe, an extension, or a "paste this in DevTools"
script is closed without review. X's Automation Rules say scripting the website
can mean permanent suspension, and human approval of each post does not change
that.

## Other rules

- Python 3.9+, standard library only, no network calls, in `skills/`. Three maintainer
  scripts sit outside the plugin: `measurement/validate.py` (needs pyarrow and numpy; prints
  aggregates only, so never add code that writes tweet text, IDs or handles to disk),
  `tools/algo_watch.py` (fetches one public file; standard library) and the demo and icon
  renderers (need Pillow). Their tests skip when the packages are missing.
- Every tool has `--help`, `--json`, reads a file or `-` for stdin, handles UTF-8
  and CRLF, exits non-zero on bad input, and has tests with fixtures.
- Copyright header on every source file:
  `# Copyright (c) 2026 Muhammad Hassan. MIT License.`
- No em dashes anywhere. A test enforces it.
- Never commit post text, tweet IDs or handles from real accounts. Fixtures are
  invented.
- Any number that goes stale goes in `references/stale.md` with a date and a
  source URL.
- Conventional commits, one change per commit, a CHANGELOG entry per change.

## DCO

Sign off every commit with `git commit -s`. That adds a
`Signed-off-by:` line certifying the
[Developer Certificate of Origin](https://developercertificate.org/).

## Running the tests

```bash
python -m pip install pytest
python -m pytest
```

## Changing a workflow

- Every action is pinned to a full commit SHA with the version in a comment. To update one, look up
  the tag's SHA (`gh api repos/<owner>/<action>/git/ref/tags/<tag>`, and dereference it if the tag is
  annotated), change the line and the comment together. Nothing bumps these for you.
- The algo-watch test dependencies are hash-pinned in `tools/algo-ci-requirements.txt`; refresh it by
  hand (the header says how).
- Keep the scopes apart: the job that parses upstream text or runs pytest never gets a write token,
  and the job that can push runs no pip and no pytest. Tests in `tests/test_algo_security.py` fail the
  build if that changes.
