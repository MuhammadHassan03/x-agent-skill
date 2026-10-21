# Security

## What this repo does with your data

Nothing leaves your machine. Every tool the skills use is Python standard library only and
makes no network calls. The one exception is `tools/algo_watch.py`, a maintainer script that CI runs
weekly; it fetches one public file (`home-mixer/params/param.rs` from xai-org/x-algorithm) through the
GitHub API and sends nothing about you or your text. There is no telemetry, no analytics and no update
check. There are no secrets to configure and none should ever be committed.

Voice and log files live in `~/.claude/x/` on your own disk.

## Reporting a problem

Open a private security advisory on the GitHub repository, or email the
maintainer through the address on their GitHub profile. Please include the tool,
the input that triggers it and the Python version. Expect an acknowledgement
within seven days.

Anything that would make a tool open a socket, spawn a browser or call the X
API is a vulnerability for this project, not a feature request.
