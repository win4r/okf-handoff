#!/usr/bin/env python3
"""Deterministic end-to-end test for the OKF session-handoff workflow.

Proves the whole loop with **no network, no LLM, and no paid service**: it builds
throwaway git repositories in a temp dir, drives the real `okf_handoff.py` CLI as a
subprocess, and asserts on its output and exit codes.

Run standalone (no pytest required):

    python tests/e2e.py            # exit 0 = all checks passed, 1 = a check failed

It is also pytest-compatible: each `test_*` function can be collected by pytest.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "scripts" / "okf_handoff.py"

# Deterministic git env so the test never depends on the developer's git config.
GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "E2E",
    "GIT_AUTHOR_EMAIL": "e2e@example.com",
    "GIT_COMMITTER_NAME": "E2E",
    "GIT_COMMITTER_EMAIL": "e2e@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,  # ignore the host's global git config
    "GIT_CONFIG_SYSTEM": os.devnull,
}


# --------------------------------------------------------------------------- #
# helpers                                                                     #
# --------------------------------------------------------------------------- #

def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, env=GIT_ENV, capture_output=True, text=True)


def git(repo: Path, *args):
    r = run(["git", *args], cwd=str(repo))
    assert r.returncode == 0, f"git {' '.join(args)} failed: {r.stderr}"
    return r.stdout


def tool(*args):
    return run([sys.executable, str(TOOL), *args])


def make_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    # `git init -q` + symbolic-ref works on every git (the `-b main` flag needs git>=2.28).
    git(repo, "init", "-q")
    git(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    (repo / "app.py").write_text("print('hello')\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "initial commit")
    # leave the working tree dirty, like a mid-task session
    (repo / "app.py").write_text("print('hello')\nprint('wip')\n")
    (repo / "untracked.txt").write_text("scratch\n")
    return repo


def fill_bundle(bundle: Path):
    """Simulate the human/agent filling the <<FILL>> sentinels with honest content.
    Mirrors what the handoff-create skill instructs, choosing the honest test path."""
    repl = {
        "manifest.md": [
            ("<<FILL: one sentence describing the task this handoff resumes>>",
             "Add a WIP print line to app.py."),
            ("<<FILL: what are we trying to accomplish? the original goal, in a few sentences>>",
             "Demonstrate the handoff workflow end to end."),
            ("<<FILL: one paragraph — where things stand right now>>",
             "app.py edited; not yet committed."),
        ],
        "progress.md": [
            ("<<FILL: bullet list of work actually finished this session>>",
             "- Edited app.py to add a WIP line."),
            ("<<FILL: what is partially done, and exactly where you stopped>>",
             "- untracked.txt is scratch and should be removed."),
            ("<<FILL: the first concrete next step a resuming session should take>>",
             "Decide whether to keep the WIP line, then commit."),
        ],
        "decisions.md": [
            ("<<FILL: short decision title>>", "Use print for the demo"),
            ("<<FILL: what was decided>>", "Keep it a plain print statement."),
            ("<<FILL: rationale>>", "Smallest possible change for the demo."),
            ("<<FILL: what was rejected, and why>>", "Logging — overkill here."),
        ],
        "verification.md": [
            ("<<FILL: $ command            # what it was for>>",
             "$ git status            # confirm working-tree state"),
            # honest path: tests were NOT run
            ("<<FILL: which tests to run to verify this work, e.g. `pytest -q`. OR, if you ran\n"
             "them, replace the Status line above with PASSED/FAILED/PARTIAL and paste the exact\n"
             "command and its result counts here.>>",
             "Run `python app.py` to confirm it still prints; no automated suite yet."),
            ("<<FILL: anything currently broken or expected to fail, or \"None known\">>",
             "None known."),
            ("<<FILL: something a resuming session must NOT take on faith — say how to verify it>>",
             "Do not assume app.py is committed — check `git status` (it is dirty)."),
        ],
        "open-questions.md": [
            ("<<FILL: an unresolved question, with context and who/what could answer it. Use \"None\" if there are none>>",
             "Should untracked.txt be deleted before commit?"),
        ],
    }
    for name, pairs in repl.items():
        p = bundle / name
        text = p.read_text()
        for old, new in pairs:
            assert old in text, f"sentinel not found in {name!r}: {old[:40]!r}"
            text = text.replace(old, new)
        p.write_text(text)
    # any sentinel left over is a bug in this filler
    for md in bundle.rglob("*.md"):
        assert "<<FILL:" not in md.read_text(), f"leftover sentinel in {md.name}"


# --------------------------------------------------------------------------- #
# tests                                                                       #
# --------------------------------------------------------------------------- #

def test_create_then_fresh_bundle_is_rejected():
    """A freshly scaffolded (unfilled) bundle MUST fail validation."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        r = tool("create", "--repo", str(repo), "--out", str(Path(d) / "b"),
                 "--title", "Demo task")
        assert r.returncode == 0, r.stderr
        bundle = Path(d) / "b"
        assert (bundle / "manifest.md").exists()
        assert (bundle / "git-state.md").exists()
        v = tool("validate", str(bundle))
        assert v.returncode == 1, f"fresh bundle should be INVALID:\n{v.stdout}"
        assert "sentinel" in v.stdout.lower()
    print("ok  create -> fresh bundle is rejected until filled")


def test_filled_bundle_validates():
    """After filling the sentinels honestly, the bundle MUST validate."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        assert tool("create", "--repo", str(repo), "--out", str(bundle),
                    "--title", "Demo task").returncode == 0
        fill_bundle(bundle)
        v = tool("validate", str(bundle))
        assert v.returncode == 0, f"filled bundle should be VALID:\n{v.stdout}"
        assert "VALID" in v.stdout
    print("ok  filled bundle validates")


def test_validator_rejects_invented_test_results():
    """Claiming PASSED while tests_status=not_run MUST be rejected."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        fill_bundle(bundle)
        vf = bundle / "verification.md"
        text = vf.read_text().replace("**Status: NOT RUN**", "**Status: PASSED**")
        vf.write_text(text)  # tests_status frontmatter is still not_run -> contradiction
        v = tool("validate", str(bundle))
        assert v.returncode == 1, "invented PASSED must be rejected"
        assert "never invent test results" in v.stdout.lower()
    print("ok  validator rejects invented test results")


def test_validator_rejects_missing_type():
    """A concept doc with no `type` MUST be rejected (OKF §9.2)."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        fill_bundle(bundle)
        man = bundle / "manifest.md"
        man.write_text(re.sub(r"(?m)^type:.*$", "type:", man.read_text(), count=1))
        v = tool("validate", str(bundle))
        assert v.returncode == 1
        assert "type" in v.stdout.lower()
    print("ok  validator rejects missing type")


def test_validator_rejects_empty_do_not_assume():
    """An empty 'Do Not Assume' section MUST be rejected."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        fill_bundle(bundle)
        vf = bundle / "verification.md"
        text = vf.read_text()
        text = text.replace(
            "* Do not assume app.py is committed — check `git status` (it is dirty).",
            "")
        vf.write_text(text)
        v = tool("validate", str(bundle))
        assert v.returncode == 1
        assert "do not assume" in v.stdout.lower()
    print("ok  validator rejects empty 'Do Not Assume'")


def test_verify_no_drift_then_drift():
    """verify: exit 0 right after create; exit 3 after the repo moves."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")

        v0 = tool("verify", str(bundle), "--repo", str(repo))
        assert v0.returncode == 0, f"expected NO DRIFT:\n{v0.stdout}"
        assert "NO DRIFT" in v0.stdout

        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "second commit")
        v1 = tool("verify", str(bundle), "--repo", str(repo))
        assert v1.returncode == 3, f"expected DRIFT (exit 3):\n{v1.stdout}"
        assert "DRIFT DETECTED" in v1.stdout
    print("ok  verify detects no-drift then drift")


def test_verify_detects_worktree_change_only():
    """A working-tree change with the same HEAD still counts as drift."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        # same HEAD, but change the working tree
        (repo / "app.py").write_text("print('hello')\nprint('changed again')\n")
        v = tool("verify", str(bundle), "--repo", str(repo))
        assert v.returncode == 3, f"working-tree change should drift:\n{v.stdout}"
        assert "fingerprint" in v.stdout.lower()
    print("ok  verify detects working-tree-only change")


def test_shipped_fixture_validates():
    """The committed example bundle (if present) must be conformant."""
    fixtures = sorted((REPO_ROOT / "handoffs").glob("*/manifest.md"))
    if not fixtures:
        print("--  no shipped fixture present, skipping")
        return
    for manifest in fixtures:
        bundle = manifest.parent
        v = tool("validate", str(bundle))
        assert v.returncode == 0, f"shipped fixture {bundle.name} must validate:\n{v.stdout}"
    print(f"ok  {len(fixtures)} shipped fixture(s) validate")


def test_in_repo_bundle_no_drift_but_real_change_flagged():
    """Regression (review #6): with the documented in-repo layout, `verify` right after
    `create` reports NO DRIFT (the bundle's own files are excluded), yet a real change to
    the underlying work is still flagged."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        r = tool("create", "--repo", str(repo), "--title", "In repo")
        assert r.returncode == 0, r.stderr
        bundles = list((repo / "handoffs").glob("*"))
        assert len(bundles) == 1, bundles
        bundle = bundles[0]
        v0 = tool("verify", str(bundle), "--repo", str(repo))
        assert v0.returncode == 0, f"in-repo create should leave NO DRIFT:\n{v0.stdout}"
        # exclusion must NOT hide a real change to the work itself
        (repo / "app.py").write_text("print('hello')\nprint('different wip')\n")
        v1 = tool("verify", str(bundle), "--repo", str(repo))
        assert v1.returncode == 3, f"a real work change must still drift:\n{v1.stdout}"
    print("ok  in-repo create -> no drift, but real change still flagged")


def test_validator_rejects_empty_fence_evidence():
    """Regression (review #1): a fabricated PASSED whose only 'evidence' is an empty
    code fence (or prose) must be rejected."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        fill_bundle(bundle)
        vf = bundle / "verification.md"
        text = vf.read_text().replace("tests_status: not_run", "tests_status: passed")
        text = text.replace("**Status: NOT RUN**", "**Status: PASSED**\n\n```\n```\n")
        vf.write_text(text)
        v = tool("validate", str(bundle))
        assert v.returncode == 1, f"empty-fence PASSED must be rejected:\n{v.stdout}"
        assert "never invent" in v.stdout.lower()
    print("ok  validator rejects empty-fence 'evidence'")


def test_validator_catches_multiline_sentinel():
    """Regression (review #2): a <<FILL>> sentinel split across lines must be caught."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        fill_bundle(bundle)
        p = bundle / "progress.md"
        p.write_text(p.read_text() + "\n<<FILL: still need\nto finish this>>\n")
        v = tool("validate", str(bundle))
        assert v.returncode == 1, "multi-line sentinel must fail validation"
        assert "sentinel" in v.stdout.lower()
    print("ok  validator catches multi-line sentinels")


def test_validator_accepts_plus_bullets():
    """Regression (review #3): '+' is a valid CommonMark bullet and must be accepted."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        fill_bundle(bundle)
        p = bundle / "progress.md"
        p.write_text(p.read_text().replace(
            "Decide whether to keep the WIP line, then commit.",
            "+ Decide whether to keep the WIP line, then commit."))
        v = tool("validate", str(bundle))
        assert v.returncode == 0, f"'+' bullets must be accepted:\n{v.stdout}"
    print("ok  validator accepts '+' bullets")


def test_validate_survives_non_utf8_md():
    """Regression (review #8): a non-UTF-8 .md must produce a clean error, not a crash."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        fill_bundle(bundle)
        (bundle / "blob.md").write_bytes(b"\xff\xfe\x00\x01 not utf8 \x80")
        v = tool("validate", str(bundle))
        assert "Traceback" not in (v.stdout + v.stderr), f"must not crash:\n{v.stderr}"
        assert v.returncode == 1
        assert "utf-8" in v.stdout.lower()
    print("ok  validate survives a non-UTF-8 .md without crashing")


def test_validate_refuses_symlink_escape():
    """Security (audit): a .md that symlinks outside the bundle must be REFUSED, and its
    target content must NOT be read/echoed."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        fill_bundle(bundle)
        secret = Path(d) / "secret.txt"
        secret.write_text("TOPSECRET marker [x](pointer.md)\n")
        (bundle / "leak.md").symlink_to(secret)
        v = tool("validate", str(bundle))
        assert v.returncode == 1, "a symlinked .md must make validation fail"
        assert "symlink" in v.stdout.lower(), v.stdout
        assert "TOPSECRET" not in (v.stdout + v.stderr), "must not read/echo the symlink target"
    print("ok  validate refuses a bundle-escaping symlink without reading it")


def test_validate_refuses_oversize_doc():
    """Security (audit): an oversized .md must be refused, not slurped into memory."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        fill_bundle(bundle)
        (bundle / "huge.md").write_text("a" * (5 * 1024 * 1024))
        v = tool("validate", str(bundle))
        assert v.returncode == 1
        assert "exceeds" in v.stdout.lower() or "too large" in v.stdout.lower(), v.stdout
        assert "Traceback" not in (v.stdout + v.stderr)
    print("ok  validate refuses an oversized document")


def test_verify_refuses_symlinked_git_state():
    """Security (audit): verify must not follow a symlinked git-state.md out of the bundle."""
    with tempfile.TemporaryDirectory() as d:
        repo = make_repo(Path(d))
        bundle = Path(d) / "b"
        tool("create", "--repo", str(repo), "--out", str(bundle), "--title", "Demo")
        outside = Path(d) / "outside-git-state.md"
        outside.write_text("---\ntype: Git State\nbranch: x\ncommit: deadbeef\nstatus_fingerprint: abc\n---\n")
        (bundle / "git-state.md").unlink()
        (bundle / "git-state.md").symlink_to(outside)
        v = tool("verify", str(bundle), "--repo", str(repo))
        assert v.returncode == 2, f"symlinked git-state.md must be refused (exit 2):\n{v.stdout}\n{v.stderr}"
    print("ok  verify refuses a symlinked git-state.md")


def test_create_refuses_non_git_dir():
    with tempfile.TemporaryDirectory() as d:
        plain = Path(d) / "plain"
        plain.mkdir()
        r = tool("create", "--repo", str(plain), "--out", str(Path(d) / "b"),
                 "--title", "x")
        assert r.returncode == 2, "create must refuse a non-git dir"
        assert "not a git repository" in r.stderr.lower()
    print("ok  create refuses a non-git directory")


ALL_TESTS = [
    test_create_then_fresh_bundle_is_rejected,
    test_filled_bundle_validates,
    test_validator_rejects_invented_test_results,
    test_validator_rejects_missing_type,
    test_validator_rejects_empty_do_not_assume,
    test_verify_no_drift_then_drift,
    test_verify_detects_worktree_change_only,
    test_in_repo_bundle_no_drift_but_real_change_flagged,
    test_validator_rejects_empty_fence_evidence,
    test_validator_catches_multiline_sentinel,
    test_validator_accepts_plus_bullets,
    test_validate_survives_non_utf8_md,
    test_validate_refuses_symlink_escape,
    test_validate_refuses_oversize_doc,
    test_verify_refuses_symlinked_git_state,
    test_shipped_fixture_validates,
    test_create_refuses_non_git_dir,
]


def main() -> int:
    if not shutil.which("git"):
        print("SKIP: git not available", file=sys.stderr)
        return 0
    failed = 0
    for t in ALL_TESTS:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print()
    if failed:
        print(f"{failed}/{len(ALL_TESTS)} checks FAILED")
        return 1
    print(f"all {len(ALL_TESTS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
