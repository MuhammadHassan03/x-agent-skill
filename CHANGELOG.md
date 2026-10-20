# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-21

### Added
- Twelve skills: `x-post`, `x-thread`, `x-reply`, `x-viral`, `x-article`, `x-human`, `x-profile`,
  `x-plan`, `x-dm`, `x-audit`, `x-money`, `x-algo`, each ending in the same approval gate.
- Ten standard-library tools: `xcount.py`, `postscore.py`, `thread.py`, `replylint.py`, `swipe.py`,
  `xanalytics.py`, `humanize.py`, `detect.py`, `ocr.py`, `weights.py`.
- `references/x-algorithm.md` generated from `param.rs` at commit `74d49a4`, `references/x-rules.md`,
  `references/stale.md`.
- `measurement/validate.py`, the research script behind the README's measured numbers (needs pyarrow and
  numpy; not part of the plugin).
- CI on Python 3.9, 3.11, 3.13 across ubuntu and windows; repo hygiene tests (no em dashes, no network
  or browser imports in tools, identical approval gate in every skill).

### Changed
- Ranking weights come from the file as read, not from the brief: like 0.66, click 0.3, dwell 0.05,
  not-interested -52.272 (the brief had 0.5, 0.4, 0.004 and about -43).
- `/x-viral` is paste-in only. It never drives a browser.

### Fixed
- Tools force UTF-8 stdout so Python 3.9 on Windows does not crash on non-ASCII output.
