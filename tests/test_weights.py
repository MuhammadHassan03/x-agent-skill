# Copyright (c) 2026 Muhammad Hassan. MIT License.
import json
import subprocess
import sys

import weights
from conftest import ROOT, fixture

SCRIPT = ROOT + "/skills/x-algo/weights.py"
SRC = open(fixture("param_excerpt.rs"), encoding="utf-8").read()
ARGS = ["--commit", "74d49a4", "--date", "2026-10-20", "--checked", "2026-10-21"]


def by_name(params):
    return {p["name"]: p["value"] for p in params}


def test_parses_single_and_multiline_params():
    v = by_name(weights.parse_params(SRC))
    assert v["ReplyWeight"] == 5.0 and v["BidirectionalFollowReplyWeightBoost"] == 15.0
    assert v["ReportWeight"] == -234.0 and v["NotInterestedWeight"] == -52.272


def test_ignores_non_weights_and_bools():
    v = by_name(weights.parse_params(SRC + '\nparam!(EnableX, bool, "rust_home_mixer_x_weight", true);\n'
                                     'param!(MaxPositionRatio, f64, "rust_home_mixer_ratio", 0.97);\n'))
    assert "EnableX" not in v and "MaxPositionRatio" not in v


def test_crlf_input():
    assert by_name(weights.parse_params(SRC.replace("\n", "\r\n")))["ReplyWeight"] == 5.0


def test_render_pins_commit_and_states_mutual_reply():
    md = weights.render(weights.parse_params(SRC), "74d49a4", "2026-10-20", "2026-10-21", weights.SOURCE_URL, None)
    assert "pinned commit: `74d49a4`" in md and "5 + 15 = 20" in md
    assert "one report cancels 468 likes" in md      # called out as wrong, not repeated as fact
    assert "observed, not coded" in md.lower()
    assert "not coded" in md


def test_diff_detects_changes():
    old = weights.render(weights.parse_params(SRC), "aaaaaaa", "2026-10-01", "2026-10-01", weights.SOURCE_URL, None)
    new_src = SRC.replace('"rust_home_mixer_favorite_weight", 0.66', '"rust_home_mixer_favorite_weight", 0.5')
    md = weights.render(weights.parse_params(new_src), "bbbbbbb", "2026-10-02", "2026-10-02", weights.SOURCE_URL,
                        weights.previous_values(old))
    assert "changed: `FavoriteWeight` 0.66 -> 0.5" in md


def test_cli_requires_commit_and_rejects_wrong_file(tmp_path):
    p = tmp_path / "param.rs"
    p.write_text(SRC, encoding="utf-8")
    assert subprocess.run([sys.executable, SCRIPT, str(p)], capture_output=True).returncode == 2   # argparse: no --commit
    assert subprocess.run([sys.executable, SCRIPT, str(p), "--commit", "zzz", "--date", "2026-10-20"],
                          capture_output=True).returncode == 2
    p.write_text("fn main() {}", encoding="utf-8")
    assert subprocess.run([sys.executable, SCRIPT, str(p)] + ARGS, capture_output=True).returncode == 2


def test_cli_write_and_check(tmp_path):
    p = tmp_path / "param.rs"
    p.write_text(SRC, encoding="utf-8")
    out = tmp_path / "x.md"
    assert subprocess.run([sys.executable, SCRIPT, str(p), "-o", str(out)] + ARGS, capture_output=True).returncode == 0
    assert subprocess.run([sys.executable, SCRIPT, str(p), "--check", str(out)] + ARGS, capture_output=True).returncode == 0
    p.write_text(SRC.replace("0.66", "0.7"), encoding="utf-8")
    assert subprocess.run([sys.executable, SCRIPT, str(p), "--check", str(out)] + ARGS, capture_output=True).returncode == 1


def test_committed_reference_matches_tool_output():
    md = open(ROOT + "/references/x-algorithm.md", encoding="utf-8").read()
    pin = json.load(open(ROOT + "/references/weights.json", encoding="utf-8"))["commit"]
    assert pin in md
    v = weights.previous_values(md)
    assert v["FavoriteWeight"] == 0.66 and v["ReplyWeight"] == 5.0
