# Copyright (c) 2026 Muhammad Hassan. MIT License.
import json
import os
import subprocess
import sys
import urllib.error

import pytest

import algo_watch
from conftest import ROOT, fixture

SCRIPT = ROOT + "/tools/algo_watch.py"
TEXT = open(fixture("param_full.rs"), encoding="utf-8").read()
COMMIT = "74d49a4ffb398949a5f9312f828d7112d7d31f00"
FAV = '"rust_home_mixer_favorite_weight", '


def make_root(tmp_path):
    (tmp_path / "references").mkdir()
    (tmp_path / "README.md").write_text("# T\n\n" + algo_watch.START + "\n" + algo_watch.END + "\n\n## After\n", encoding="utf-8")
    return str(tmp_path)


def with_fav(v):
    return TEXT.replace(FAV + "0.66", FAV + v)


def test_parses_every_param_with_types():
    p = algo_watch.parse_all(TEXT)
    assert len(p) == TEXT.count("param!(") == 195
    assert p["ReplyWeight"] == {"key": "rust_home_mixer_reply_weight", "type": "f64", "value": 5.0}
    assert p["PhoenixMaxResults"]["value"] == 1000 and isinstance(p["PhoenixMaxResults"]["value"], int)
    assert p["EnablePhoenixSource"]["value"] is True
    assert p["ThunderAlgorithm"]["value"] == "default"
    assert p["TopicFilteringOverrides"]["value"] == ""
    assert p["ShadowTrafficPhoenixClustersList"]["value"] == "vec![]"
    assert "to_string()" in p["ShadowTrafficPhoenixClusterAggregationTypes"]["value"]


def test_crlf_input():
    assert algo_watch.parse_all(TEXT.replace("\n", "\r\n")) == algo_watch.parse_all(TEXT)


def test_compare_added_removed_changed_weights_first():
    old = algo_watch.parse_all(TEXT)
    new = json.loads(json.dumps(old))
    new["FavoriteWeight"]["value"] = 0.5
    new["BrandNewParam"] = {"key": "k", "type": "bool", "value": True}
    del new["PhoenixMaxResults"]
    ch = algo_watch.compare(old, new)
    assert [(c["change"], c["name"]) for c in ch] == [
        ("changed", "FavoriteWeight"), ("added", "BrandNewParam"), ("removed", "PhoenixMaxResults")]
    assert ch[0]["weight"] and not ch[1]["weight"]
    assert algo_watch.compare(old, old) == []


def test_validate_rejects_a_changed_format():
    with pytest.raises(algo_watch.WatchError):
        algo_watch.validate(algo_watch.parse_all("fn main() {}"))
    algo_watch.validate(algo_watch.parse_all(TEXT))


def test_diff_format():
    md = algo_watch.render_diff(
        [{"change": "changed", "name": "FavoriteWeight", "before": 0.66, "after": 0.5, "weight": True},
         {"change": "added", "name": "X", "before": None, "after": "", "weight": False}],
        "2026-10-28", COMMIT, "2026-10-27T00:00:00Z")
    assert md.startswith("## 2026-10-28, 2 changes (commit 74d49a4)")
    assert "| changed (weight) | `FavoriteWeight` | 0.66 | 0.5 |" in md
    assert '| added (param) | `X` |  | "" |' in md
    assert "1 of the changes are ranking weights" in md


def test_baseline_then_change_writes_everything(tmp_path):
    root = make_root(tmp_path)
    r1 = algo_watch.run(TEXT, COMMIT, "2026-10-20T04:32:20Z", root, "2026-10-21", True)
    assert r1["baseline"] and os.path.exists(root + "/references/weights.json")
    again = algo_watch.run(TEXT, COMMIT, "2026-10-20T04:32:20Z", root, "2026-10-22", True)
    assert again["n"] == 0 and not again["baseline"]
    diff = str(tmp_path / "d.md")
    r2 = algo_watch.run(with_fav("0.5"), "a" * 40, "2026-10-27T00:00:00Z", root, "2026-10-28", True, diff)
    assert r2["n"] == 1 and r2["weight_changes"] == 1
    snap = json.load(open(root + "/references/weights.json"))
    assert snap["commit"] == "a" * 40 and snap["params"]["FavoriteWeight"]["value"] == 0.5
    md = open(root + "/references/x-algorithm.md", encoding="utf-8").read()
    assert "pinned commit: `" + "a" * 40 in md and "changed: `FavoriteWeight` 0.66 -> 0.5" in md
    log = open(root + "/references/ALGO-CHANGELOG.md", encoding="utf-8").read()
    assert log.index("2026-10-28, 1 change") < log.index("2026-10-21, baseline")
    readme = open(root + "/README.md", encoding="utf-8").read()
    assert "#### 2026-10-28, 1 change" in readme and "## After" in readme
    assert "| changed (weight) | `FavoriteWeight` | 0.66 | 0.5 |" in open(diff, encoding="utf-8").read()


def test_readme_keeps_only_last_three_entries(tmp_path):
    root = make_root(tmp_path)
    algo_watch.run(TEXT, COMMIT, "2026-10-20T00:00:00Z", root, "2026-10-01", True)
    for i, v in enumerate(["0.5", "0.4", "0.3", "0.2"], 1):
        algo_watch.run(with_fav(v), "%040x" % i, "2026-10-20T00:00:00Z", root, "2026-10-%d" % (10 + i), True)
    readme = open(root + "/README.md", encoding="utf-8").read()
    assert readme.count("#### 2026-10-") == 3 and "2026-10-14, 1 change" in readme and "baseline" not in readme


def test_parse_failure_raises_and_writes_nothing(tmp_path):
    root = make_root(tmp_path)
    with pytest.raises(algo_watch.WatchError):
        algo_watch.run("// moved to another file", COMMIT, "2026-10-20", root, "2026-10-21", True)
    assert not os.path.exists(root + "/references/weights.json")


def test_fetch_follows_default_branch_and_pins_last_touching_commit(monkeypatch):
    calls = []

    def fake(url, token):
        calls.append(url)
        if url.endswith("/repos/xai-org/x-algorithm"):
            return json.dumps({"default_branch": "trunk"}).encode()
        if "/commits?" in url:
            return json.dumps([{"sha": "b" * 40, "commit": {"committer": {"date": "2026-10-27T01:02:03Z"}}}]).encode()
        return b"param text"
    monkeypatch.setattr(algo_watch, "_get", fake)
    text, sha, date = algo_watch.fetch()
    assert (text, sha, date) == ("param text", "b" * 40, "2026-10-27T01:02:03Z")
    assert "sha=trunk" in calls[1] and ("/" + "b" * 40 + "/home-mixer/params/param.rs") in calls[2]


def test_fetch_reports_a_moved_file(monkeypatch):
    def fake(url, token):
        if url.endswith("/repos/xai-org/x-algorithm"):
            return b'{"default_branch": "main"}'
        return b"[]"
    monkeypatch.setattr(algo_watch, "_get", fake)
    with pytest.raises(algo_watch.WatchError) as e:
        algo_watch.fetch()
    assert "moved" in str(e.value)


def test_http_errors_become_watch_errors(monkeypatch):
    def boom(req, timeout=0):
        raise urllib.error.HTTPError("u", 404, "nf", {}, None)
    monkeypatch.setattr(algo_watch.urllib.request, "urlopen", boom)
    with pytest.raises(algo_watch.WatchError):
        algo_watch._get("https://example.invalid/x", None)


def test_cli_exit_codes(tmp_path):
    root = make_root(tmp_path)
    base = [sys.executable, SCRIPT, "--param-file", fixture("param_full.rs"), "--commit", COMMIT,
            "--date", "2026-10-20", "--root", root, "--today", "2026-10-21", "--write"]
    assert subprocess.run(base, capture_output=True).returncode == 10          # baseline written
    assert subprocess.run(base, capture_output=True).returncode == 0           # nothing changed
    bad = tmp_path / "bad.rs"
    bad.write_text("nope", encoding="utf-8")
    r = subprocess.run(base[:3] + [str(bad)] + base[4:], capture_output=True, text=True)
    assert r.returncode == 2 and r.stderr.startswith("FAILURE:")
    r2 = subprocess.run([sys.executable, SCRIPT, "--param-file", fixture("param_full.rs")], capture_output=True, text=True)
    assert r2.returncode == 2 and "--commit" in r2.stderr


def test_committed_snapshot_is_consistent():
    snap = json.load(open(ROOT + "/references/weights.json", encoding="utf-8"))
    assert len(snap["commit"]) == 40 and len(snap["params"]) >= algo_watch.MIN_PARAMS
    md = open(ROOT + "/references/x-algorithm.md", encoding="utf-8").read()
    assert snap["commit"] in md
    assert "<!-- algo-changelog:start -->" in open(ROOT + "/README.md", encoding="utf-8").read()
