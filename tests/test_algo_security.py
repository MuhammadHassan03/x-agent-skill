# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""Security regressions for the algo-watch tracker: hostile upstream input, token handling, workflow privilege."""
import io
import json
import os
import re
import shutil
import time
import urllib.request

import pytest

import algo_watch
from conftest import ROOT, fixture

WORKFLOWS = os.path.join(ROOT, ".github", "workflows")


def wf(name):
    return open(os.path.join(WORKFLOWS, name), encoding="utf-8").read()


def sha(n=1):
    return format(n, "x").rjust(40, "a")


# ---- hostile param.rs: parsing stays linear and fails closed
HOSTILE = {
    "unclosed-blocks": lambda: 'param!(A, f64, "k", 1\n' * 8000,
    "whitespace-run": lambda: "param!(A," + " " * 100000 + "x",
    "endless-type": lambda: "param!(A, " + "a" * 100000,
    "endless-value": lambda: 'param!(A, f64, "k", ' + "(" * 50000,
}


@pytest.mark.parametrize("case", sorted(HOSTILE))
def test_parse_is_linear_on_hostile_input(case):
    text = HOSTILE[case]()
    t = time.time()
    algo_watch.parse_all(text)
    assert time.time() - t < 5


def test_oversize_value_fails_closed_not_silently():
    text = 'param!(Big, f64, "k", ' + "9" * (algo_watch.MAX_VALUE + 50) + ");\n"
    parsed = algo_watch.parse_all(text)
    with pytest.raises(algo_watch.WatchError):
        algo_watch.check_complete(text, parsed)


def test_run_refuses_an_oversize_file(tmp_path):
    text = "// " + "x" * (algo_watch.MAX_BYTES + 10)
    with pytest.raises(algo_watch.WatchError):
        algo_watch.run(text, sha(), "2026-10-24T00:00:00Z", str(tmp_path), "2026-10-24", False)


# ---- the download
class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def test_download_is_capped(monkeypatch):
    monkeypatch.setattr(algo_watch, "_open", lambda req, timeout: FakeResponse(b"x" * (algo_watch.MAX_BYTES + 5)))
    with pytest.raises(algo_watch.WatchError):
        algo_watch._get("https://raw.githubusercontent.com/o/r/c/p", None)


def test_token_goes_to_the_api_host_only(monkeypatch):
    seen = []

    def fake_open(req, timeout):
        seen.append((req.full_url, req.get_header("Authorization")))
        u = req.full_url
        if u.endswith("/repos/xai-org/x-algorithm"):
            return FakeResponse(b'{"default_branch":"main"}')
        if "/commits?" in u:
            return FakeResponse(json.dumps([{"sha": sha(7), "commit": {"committer": {"date": "2026-10-24T01:02:03Z"}}}]).encode())
        return FakeResponse(b"param!(A, f64, \"a_weight\", 1);")

    monkeypatch.setattr(algo_watch, "_open", fake_open)
    text, commit, date = algo_watch.fetch("SECRET-TOKEN")
    assert commit == sha(7) and date == "2026-10-24T01:02:03Z"
    for url, auth in seen:
        if url.startswith("https://api.github.com/"):
            assert auth == "Bearer SECRET-TOKEN"
        else:
            assert auth is None, url


@pytest.mark.parametrize("bad_sha,bad_date", [("../../etc/passwd", "2026-10-24T01:02:03Z"), (sha(1), "yesterday [x](http://e.example)")])
def test_api_values_are_validated(monkeypatch, bad_sha, bad_date):
    def fake_open(req, timeout):
        if req.full_url.endswith("/repos/xai-org/x-algorithm"):
            return FakeResponse(b'{"default_branch":"main&path=other"}')
        return FakeResponse(json.dumps([{"sha": bad_sha, "commit": {"committer": {"date": bad_date}}}]).encode())

    monkeypatch.setattr(algo_watch, "_open", fake_open)
    with pytest.raises(algo_watch.WatchError):
        algo_watch.fetch(None)


def test_branch_name_is_url_encoded(monkeypatch):
    urls = []

    def fake_open(req, timeout):
        urls.append(req.full_url)
        if req.full_url.endswith("/repos/xai-org/x-algorithm"):
            return FakeResponse(b'{"default_branch":"a&path=b"}')
        return FakeResponse(b"[]")

    monkeypatch.setattr(algo_watch, "_open", fake_open)
    with pytest.raises(algo_watch.WatchError):
        algo_watch.fetch(None)
    assert any("sha=a%26path%3Db" in u for u in urls)


def test_cross_host_redirect_is_refused():
    handler = algo_watch._SameHostRedirect()
    req = urllib.request.Request("https://api.github.com/repos/x/y", headers={"Authorization": "Bearer t"})
    with pytest.raises(algo_watch.WatchError):
        handler.redirect_request(req, None, 302, "Found", {}, "https://evil.example/steal")


def test_unexpected_exception_exits_2_not_1(monkeypatch, capsys):
    def boom(token=None):
        raise KeyError("shape changed")

    monkeypatch.setattr(algo_watch, "fetch", boom)
    assert algo_watch.main([]) == 2
    assert "FAILURE: unexpected KeyError" in capsys.readouterr().err


def test_non_numeric_message_is_short_and_has_no_backticks():
    new = {"XWeight": {"key": "k", "type": "f64", "value": "`" * 500}}
    msg = algo_watch.validate_update(None, new)[0]
    assert "`" not in msg and len(msg) < 140


# ---- the staged update is data: the commit job verifies it before copying anything
def make_stage(tmp_path, readme_edit=None, extra=None):
    base = tmp_path / "base"
    shutil.copytree(os.path.join(ROOT, "references"), base / "references")
    shutil.copy(os.path.join(ROOT, "README.md"), base / "README.md")
    stage = tmp_path / "stage"
    (stage / "references").mkdir(parents=True)
    for f in ("weights.json", "x-algorithm.md", "ALGO-CHANGELOG.md"):
        shutil.copy(base / "references" / f, stage / "references" / f)
    readme = (base / "README.md").read_text(encoding="utf-8")
    if readme_edit:
        readme = readme_edit(readme)
    (stage / "README.md").write_text(readme, encoding="utf-8")
    (stage / "commit-msg.txt").write_text("weights: 2026-10-24, 0 changes (upstream aaaaaaa, 2026-10-24T00:00:00Z)\n\nbody\n", encoding="utf-8")
    snap = json.loads((stage / "references" / "weights.json").read_text(encoding="utf-8"))
    return base, stage, snap


def test_stage_that_matches_the_base_is_accepted(tmp_path):
    base, stage, _ = make_stage(tmp_path)
    assert algo_watch.verify_tree(str(base), str(stage)) == []


def test_stage_with_an_extra_file_is_rejected(tmp_path):
    base, stage, _ = make_stage(tmp_path)
    (stage / ".github").mkdir()
    (stage / ".github" / "evil.yml").write_text("x", encoding="utf-8")
    assert any("not an allowed file" in p for p in algo_watch.verify_tree(str(base), str(stage)))


def test_stage_with_a_missing_file_is_rejected(tmp_path):
    base, stage, _ = make_stage(tmp_path)
    (stage / "references" / "ALGO-CHANGELOG.md").unlink()
    assert any("missing" in p for p in algo_watch.verify_tree(str(base), str(stage)))


def test_stage_readme_changed_outside_the_markers_is_rejected(tmp_path):
    base, stage, _ = make_stage(tmp_path, readme_edit=lambda t: t.replace("# The X agent skill", "# The X agent skill\n\n[click](https://evil.example)", 1))
    assert any("outside the changelog markers" in p for p in algo_watch.verify_tree(str(base), str(stage)))


def test_stage_readme_changed_inside_the_markers_is_accepted(tmp_path):
    edit = lambda t: t.replace(algo_watch.END, "extra line\n" + algo_watch.END, 1)  # noqa: E731
    base, stage, _ = make_stage(tmp_path, readme_edit=edit)
    assert algo_watch.verify_tree(str(base), str(stage)) == []


def test_stage_with_a_weight_that_moved_ten_times_is_rejected(tmp_path):
    base, stage, snap = make_stage(tmp_path)
    name = next(n for n, v in snap["params"].items() if n.endswith("Weight") and isinstance(v["value"], (int, float)) and v["value"] > 0)
    snap["params"][name]["value"] *= 50
    (stage / "references" / "weights.json").write_text(json.dumps(snap), encoding="utf-8")
    assert any("more than 10x" in p for p in algo_watch.verify_tree(str(base), str(stage)))


def test_stage_with_a_link_is_rejected(tmp_path):
    base, stage, _ = make_stage(tmp_path)
    try:
        os.symlink(os.path.join(ROOT, "README.md"), stage / "link.md")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available here")
    assert algo_watch.verify_tree(str(base), str(stage))


def test_verify_tree_cli_exit_codes(tmp_path):
    base, stage, _ = make_stage(tmp_path)
    assert algo_watch.main(["--root", str(base), "--verify-tree", str(stage)]) == 0
    (stage / "evil.txt").write_text("x", encoding="utf-8")
    assert algo_watch.main(["--root", str(base), "--verify-tree", str(stage)]) == 3


# ---- workflow hygiene: pinned actions, bounded jobs, least privilege
WORKFLOW_FILES = ["algo-watch.yml", "test.yml", "pages.yml"]


@pytest.mark.parametrize("name", WORKFLOW_FILES)
def test_every_action_is_pinned_to_a_full_sha(name):
    uses = re.findall(r"^\s*-?\s*uses:\s*(\S+)", wf(name), re.M)
    assert uses
    for u in uses:
        assert re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", u), (name, u)


@pytest.mark.parametrize("name", WORKFLOW_FILES)
def test_every_job_has_a_timeout_and_checkouts_do_not_persist_credentials(name):
    text = wf(name)
    jobs = re.findall(r"^  [\w-]+:\n(?:(?!^  [\w-]+:\n).*\n?)*", text.split("\njobs:\n", 1)[1], re.M)
    assert jobs
    for j in jobs:
        assert "timeout-minutes:" in j, (name, j.splitlines()[0])
    if name != "algo-watch.yml":
        for co in re.findall(r"actions/checkout@[^\n]*\n(?:\s+with:\n(?:\s+[^\n]+\n)*)?", text):
            assert "persist-credentials: false" in co, (name, co)


def split_jobs(text):
    body = text.split("\njobs:\n", 1)[1]
    parts = re.split(r"(?m)^  ([\w-]+):\n", body)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def test_algo_watch_has_no_workflow_wide_grant_and_no_job_combines_write_scopes():
    text = wf("algo-watch.yml")
    assert re.search(r"(?m)^permissions: \{\}\s*$", text)
    jobs = split_jobs(text)
    assert set(jobs) == {"check", "commit", "report"}
    for name, j in jobs.items():
        assert not ("contents: write" in j and "issues: write" in j), name
    assert "contents: write" in jobs["commit"] and "issues: write" in jobs["report"]
    assert "contents: read" in jobs["check"] and "write" not in jobs["check"].split("steps:")[0]


def test_the_job_that_can_push_runs_no_pip_and_no_pytest():
    commit = split_jobs(wf("algo-watch.yml"))["commit"]
    assert "pip" not in commit and "pytest" not in commit
    assert "--verify-tree" in commit


def test_the_job_that_runs_third_party_code_cannot_push_and_does_not_keep_the_credential():
    check = split_jobs(wf("algo-watch.yml"))["check"]
    assert "persist-credentials: false" in check
    assert "git push" not in check and "gh issue" not in check
    assert "--require-hashes" in check


def test_algo_ci_requirements_are_hash_pinned():
    lines = [l for l in open(os.path.join(ROOT, "tools", "algo-ci-requirements.txt"), encoding="utf-8").read().splitlines() if l and not l.startswith("#")]
    assert lines and all(re.fullmatch(r"[\w.-]+==[\w.]+ --hash=sha256:[0-9a-f]{64}", l) for l in lines)


def test_test_workflow_is_read_only():
    assert re.search(r"(?m)^permissions:\n  contents: read\s*$", wf("test.yml"))
