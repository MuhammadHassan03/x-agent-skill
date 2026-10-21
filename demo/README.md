# Demo

`x-agent-skill.gif` shows the real tools running on the invented sample drafts in `samples/`:
`postscore.py` on a bait draft, `thread.py` on a long draft, and `humanize.py` then `detect.py` on a
draft full of stock phrases (the before and after score comes from running `detect.py` on the original
and on the cleaned copy of the same file).

## How the committed GIF was made

It was drawn by `render_fallback.py`, **not** by VHS. When this GIF was made, VHS 0.12.1 started
Chrome and then hung on Windows, so it never produced a frame. `render_fallback.py` reads the visible
commands from `x-agent-skill.tape`, runs them for real in the repo root, and draws the typed commands
and their actual output as a dark terminal animation at 1200px wide (Pillow; about 120 KB). It is a
drawing of a terminal, not a screen recording. The tape has not been confirmed to render on this
machine; it should work with a working VHS, and `render.sh` is there for that.

## Re-render

```bash
make demo-fallback        # Pillow, no VHS needed: python demo/render_fallback.py
make demo                 # VHS (needs vhs, ttyd and ffmpeg on PATH): sh demo/render.sh
PY=python make demo       # on Windows, where Python 3 is called python
```

Neither render runs in CI (VHS needs a browser and a terminal emulator), so the GIF is committed.
Re-render after any change to those tools' output. Both scripts warn if the GIF goes over 3 MB.
