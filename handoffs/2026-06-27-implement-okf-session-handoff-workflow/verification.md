---
type: Verification
title: Verification Record
description: Commands run, real test results, known failures, and Do Not Assume notes.
timestamp: 2026-06-27T08:57:24Z
tests_status: passed
tags: [handoff, verification]
---

# Commands Run

Commands actually executed this session, with their purpose:

```
$ gh api .../okf/SPEC.md | base64 -d          # fetch the raw OKF spec to verify details
$ python3 scripts/okf_handoff.py create ...    # smoke-test create on throwaway repos
$ python3 scripts/okf_handoff.py verify ...    # smoke-test drift detection (exit 0 / 3)
$ python3 tests/e2e.py                          # run the deterministic E2E suite
```

# Test Results

> Test results MUST come from real runs. If you did not run them, say so.
> Set `tests_status` in the frontmatter to one of: passed | failed | partial | not_run,
> and make the Status line below match.

**Status: PASSED**

`python3 tests/e2e.py` — all 14 checks passed (exit 0):

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
ok  1 shipped fixture(s) validate
ok  create refuses a non-git directory

all 14 checks passed
```

# Known Failures

None outstanding. During development two tests earned their keep by failing first and
exposing real bugs, both now fixed: (1) a working-tree-only edit was not detected as
drift — the fingerprint ignored content of an already-modified file; (2) the adversarial
review's empty-fence and multi-line-sentinel cases. Each has a regression test.

# Do Not Assume

* Do not assume these tests still pass — **re-run** `python3 tests/e2e.py` yourself.
* Do not assume the repo matches this snapshot — it was captured at commit `056e0ae`
  with the review fixes uncommitted. After those are committed, HEAD advances; run
  `python3 scripts/okf_handoff.py verify <this-bundle>` — **DRIFT is expected here.**
* Do not assume the validator stops *deliberate* test-result fabrication — it only
  blocks casual invention. That is why resume re-runs the tests.
* Do not assume PyYAML is installed — the tool uses a stdlib-only frontmatter parser.
  Check `scripts/okf_handoff.py` has no third-party imports.
* Do not assume `claude -p` live-resume was run **as of this snapshot** — it was not.
  (It was performed later, at HEAD `9b0c0a8`; the exact command + transcript are recorded
  in the [published-release validation handoff](../2026-06-27-published-release-validation/verification.md).)
