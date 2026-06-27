---
type: Handoff Manifest
title: Implement OKF session handoff workflow
description: Build an OKF-inspired, verification-first session handoff workflow for Claude Code.
status: ready_for_review
timestamp: 2026-06-27T08:57:24Z
handoff_id: 2026-06-27-implement-okf-session-handoff-workflow
branch: main
commit: 056e0ae890d08126740a6c3f78c4942f9bb91316
tags: [handoff, claude-code]
---

# Task

Research Google's Open Knowledge Format (OKF) and use it as a *design pattern* to build
a session-handoff workflow for Claude Code: when a long session fills its context, a
developer creates a structured handoff, starts a fresh session, and resumes safely
without relying on hidden chat history or stale summaries. No Gemini / Google Cloud /
BigQuery / paid services — just Markdown, YAML, Git, and one stdlib-only Python script.

# Status

The system is implemented. The engine (`scripts/okf_handoff.py`: `create` / `validate`
/ `verify`), two skills, two slash commands, the OKF-Handoff profile (`SPEC.md`),
`README.md`, minimal `CLAUDE.md`, and a deterministic E2E test (`tests/e2e.py`) all
exist. An adversarial code review was run against the engine; it found two HIGH issues
(an anti-invention bypass via an empty code fence, and a multi-line `<<FILL>>` sentinel
the per-line scan missed) plus several lesser ones — **all fixed**, each pinned by a
new regression test. The fixes are the uncommitted changes in [Git State](git-state.md).
The full suite passes (see [Verification](verification.md)). This bundle is the dogfood
example. Remaining: review, optional live-session validation, publish — see
[Next Actions](progress.md).

# How to resume (read this first)

A fresh session should, in order:

1. Read this manifest and [Verification](verification.md).
2. Detect git drift:
   `python3 scripts/okf_handoff.py verify <this-bundle>`
3. Re-run the tests yourself before trusting the recorded results.
4. Reconcile any discrepancies, then follow [Next Actions](progress.md).

Related: [Git State](git-state.md) · [Progress](progress.md) ·
[Decisions](decisions.md) · [Open Questions](open-questions.md)
