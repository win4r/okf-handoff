---
type: Verification
title: Verification Record
description: Commands run, real test results, CI evidence, live-resume transcript, and Do Not Assume notes.
timestamp: 2026-06-27T10:19:14Z
tests_status: passed
tags: [handoff, verification]
---

# Commands Run

Commands actually executed this session, with their purpose:

```
$ python3 tests/e2e.py                                   # deterministic suite (17 checks)
$ python3 scripts/okf_handoff.py validate handoffs/*     # OKF + handoff-quality conformance
$ gh run watch 28286285092 --exit-status                 # confirm GitHub Actions CI green on 9b0c0a8
$ gh run view 28286285092 --json jobs                    # per-job CI results
$ claude -p "<resume prompt>" --permission-mode bypassPermissions --model sonnet   # live fresh-session resume
```

# Test Results

> Test results MUST come from real runs.

**Status: PASSED**

`python3 tests/e2e.py` — all 17 checks passed (exit 0). Verbatim output, re-run at the
published HEAD with both shipped bundles present (the `shipped fixture(s)` line therefore
reads `2`; at the recorded commit `9b0c0a8`, before this bundle was committed, it read `1`
— the 17-check total is identical):

```
ok  create -> fresh bundle is rejected until filled
ok  filled bundle validates
ok  validator rejects invented test results
ok  validator rejects missing type
ok  validator rejects empty 'Do Not Assume'
ok  verify detects no-drift then drift
ok  verify detects working-tree-only change
ok  in-repo create -> no drift, but real change still flagged
ok  validator rejects empty-fence 'evidence'
ok  validator catches multi-line sentinels
ok  validator accepts '+' bullets
ok  validate survives a non-UTF-8 .md without crashing
ok  validate refuses a bundle-escaping symlink without reading it
ok  validate refuses an oversized document
ok  verify refuses a symlinked git-state.md
ok  2 shipped fixture(s) validate
ok  create refuses a non-git directory

all 17 checks passed
```

# Continuous Integration

GitHub Actions CI is **green on this exact commit** (`9b0c0a8`):

- Run: https://github.com/win4r/okf-handoff/actions/runs/28286285092 — conclusion `success`.
- Jobs: `test (3.8): success`, `test (3.11): success`, `test (3.13): success`,
  `install-smoke: success`.
- Each `test` job runs `python3 tests/e2e.py` and validates every shipped handoff
  bundle; `install-smoke` runs `install.sh` into a temp config dir and exercises the
  vendored engine. So the 3.8+ floor and the installer are both CI-enforced.

# Live Resume Evidence

A real fresh `claude -p` session (no chat history; read only `CLAUDE.md` + the build
snapshot bundle) was run at HEAD `9b0c0a8` and left the repo untouched
(`git status --porcelain` empty afterward). Verbatim transcript (outer fence is 4
backticks so the inner code block is preserved):

````
+ claude -p (model sonnet, bypassPermissions) at HEAD 9b0c0a8
----- BEGIN LIVE TRANSCRIPT -----

**(a) What the handoff recorded:** branch `main` @ commit `056e0ae`, with review-fix changes *uncommitted*. The handoff noted 14 tests passing and predicted drift was "expected."

**(b) Drift:** Yes — confirmed. HEAD is now `9b0c0a8` (3 commits ahead); working-tree fingerprint also differs. The "Do Not Assume" section explicitly warned this would happen after the fixes were committed.

**(c) Exact final line of test run:**
```
all 17 checks passed
```
(17 checks, up from 14 recorded — 3 new tests were added in the intervening commits.)

**(d) Trust level:** The handoff is **valid guidance, not ground truth.** The task description, decisions, and next-actions context remain accurate. The git state and test snapshot are stale (the commits it described as "pending fixes" are now merged, and the suite has grown). Safe to use for orientation and next-actions, but re-verify anything that touches specific line numbers or file states.

----- END -----
````

# Known Failures

None. CI is green on `9b0c0a8` (4/4 jobs) and the local suite is 17/17.

# Do Not Assume

* Do not assume these results still hold — **re-run** `python3 tests/e2e.py` and check
  the latest CI run for the current HEAD yourself.
* Do not assume this bundle verifies clean: it records `9b0c0a8` with a clean tree, but
  committing the bundle advances HEAD, so
  `python3 scripts/okf_handoff.py verify handoffs/2026-06-27-published-release-validation`
  will report **DRIFT (exit 3)** by design — that is the feature, not a failure.
* Do not assume the live-resume transcript is reproducible verbatim — `claude -p` is
  non-deterministic; it is a recorded transcript of one real run at `9b0c0a8`.
* Do not assume the audit caught everything — it confirmed 25 findings; LOW-severity
  community-health polish remains (see [Open Questions](open-questions.md)).
