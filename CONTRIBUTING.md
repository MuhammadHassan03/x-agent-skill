# Contributing

## The one rule

This repo writes, you post. A pull request that adds posting, liking,
following, DMing, scrolling, scraping, browser automation, an X API client, a
Playwright or Selenium recipe, an extension, or a "paste this in DevTools"
script is closed without review. X's Automation Rules say scripting the website
can mean permanent suspension, and human approval of each post does not change
that.

## Other rules

- Python 3.9+, standard library only, no network calls. The one exception is
  `measurement/validate.py`, a research script that needs pyarrow and numpy and
  is not part of the plugin. It prints aggregates only; never add code that
  writes tweet text, IDs or handles to disk.
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
