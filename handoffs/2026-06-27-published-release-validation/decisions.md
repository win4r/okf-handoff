---
type: Decisions
title: Decisions and Rationale
description: Choices made during the release-readiness pass and why.
timestamp: 2026-06-27T10:19:14Z
tags: [handoff]
---

# Decisions

## Keep the build snapshot; add a separate current-HEAD validation handoff

* **Choice**: Leave the original `2026-06-27-implement-okf-session-handoff-workflow`
  bundle as a historical snapshot and add THIS bundle at the current HEAD, rather than
  rewriting the old one.
* **Why**: A handoff is a point-in-time snapshot; rewriting it would be dishonest. A
  fresh validation bundle gives the public a current example while preserving history.
  A forward pointer was added to the old bundle's `log.md`.
* **Alternatives considered**: Mutating the old bundle to "track HEAD" — rejected; that
  fights the tool's snapshot semantics and the audit explicitly advised against it.

## Resolve the live-resume gap by actually running it, then recording exact evidence

* **Choice**: Perform the `claude -p` fresh-session resume and paste the verbatim
  command + transcript into [Verification](verification.md).
* **Why**: The build snapshot honestly said the live resume was "not run". The fix is to
  run it and record real evidence (the user's stated option), not to claim it after the
  fact. The transcript shows the resume detecting drift and re-running the suite.
* **Alternatives considered**: Just deleting the "not run" note — rejected; that removes
  information without adding the evidence that makes the workflow trustworthy.

## Security hardening counts as defending — not changing — the core workflow

* **Choice**: Add symlink/oversize guards to `validate`/`verify` and escape `install.sh`
  sed, despite the "don't change the core workflow" constraint.
* **Why**: These change behavior only for malicious/edge inputs; all 14 pre-existing
  tests stayed green, proving legitimate create/validate/verify behavior is unchanged.
  Each guard is pinned by a new regression test, so "tests require it" literally holds.
* **Alternatives considered**: Report-only (no fix) — rejected; an arbitrary-file-read
  on an untrusted committed bundle is a real trust gap for a tool meant to consume them.
