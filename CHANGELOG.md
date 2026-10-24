# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Security
- algo-watch is three jobs with separate scopes: `check` (read-only, no stored credential, hash-pinned
  pytest), `commit` (the only `contents: write`, no pip or pytest, verifies the staged files against an
  allowlist) and `report` (issues only). All actions are pinned to commit SHAs and every job has a timeout.
- The `param.rs` parser is linear-time on hostile input (a 176 KB crafted file took 60 s before and
  0.3 s after), the download is capped at 1 MiB, the token goes to `api.github.com` only, cross-host
  redirects are refused, API-supplied hash and date are validated, and any unexpected error opens an
  issue instead of exiting silently.

### Changed
- Site: copy buttons fall back when the clipboard API rejects, install box matches the README, 24 px
  footer link targets, wrapped commands on phones; removed the decorative glows, section numbers and
  per-card entrances.
- README install: Python prerequisite, PowerShell and ZIP routes, plugin command names
  (`/x-agent:x-post`), the Windows `python3` Store-shortcut failure, and a 60-second first run.
- Docs: README, CONTRIBUTING and SECURITY describe the workflow split, pinning and the maintainer scripts.

### Fixed
- Every tool now reads a UTF-16 file with a BOM, which is what Windows PowerShell 5.1 writes for `>`
  and `Out-File`. Before, it stopped with a utf-8 codec error.

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
