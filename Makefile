# Copyright (c) 2026 Muhammad Hassan. MIT License.
.PHONY: test demo demo-fallback
test:
	python -m pytest -q

# Re-render the README demo GIF. Needs vhs, ttyd and ffmpeg. On Windows: PY=python make demo
demo:
	sh demo/render.sh

# Same GIF without VHS, drawn from the tape's real commands. Needs Pillow.
demo-fallback:
	python demo/render_fallback.py

