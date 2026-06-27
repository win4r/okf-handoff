---
type: Decisions
title: Decisions and Rationale
description: Choices made this session and why, so they are not relitigated.
timestamp: 2026-06-27T08:57:24Z
tags: [handoff]
---

# Decisions

## A handoff IS an OKF bundle

* **Choice**: Model each session-state slice (manifest, git state, progress, decisions,
  verification, open questions) as an OKF *concept* document with a `type`, in one
  bundle directory.
* **Why**: Directly reuses OKF v0.1 (typed frontmatter, reserved `index.md`/`log.md`,
  cross-links, permissive consumption). The handoff is then portable, diffable, and
  renders on GitHub with no tooling.
* **Alternatives considered**: A single monolithic `HANDOFF.md` — rejected; loses OKF's
  progressive disclosure and per-concept validation.

## Standalone repo, not the home directory

* **Choice**: Build in a dedicated git repo (`~/okf-handoff`) instead of the cwd.
* **Why**: The invocation cwd was `~` (the home dir — not a git repo,
  full of unrelated work). The workflow needs a real git repo for its git-state
  features and E2E test, and must not pollute or overwrite unrelated user files.
* **Alternatives considered**: `git init` the home dir — rejected as destructive and out
  of scope.

## Content-sensitive, config-independent drift fingerprint

* **Choice**: `status_fingerprint = sha256(HEAD + content hash of every change vs HEAD +
  untracked file hashes)`, via `git -c diff.renames=false diff --name-status` plus
  per-file hashing, with the handoff bundle's own files excluded.
* **Why**: An early version hashed only `git status --porcelain` status lines; the E2E
  test proved that editing an already-modified file left the status line (` M file`)
  unchanged, so drift went undetected. Hashing content fixes it. Using name-status +
  content hashes (not raw diff text) and disabling rename detection keeps it independent
  of git diff/color/context/rename config. Excluding the bundle's own files means
  creating/committing the handoff is not mistaken for drift in the underlying work.
* **Alternatives considered**: Hashing raw `git diff` output — rejected (sensitive to
  local git config). Porcelain-only — rejected (content-blind, proven by a failing test).

## Sentinels force authoring; the validator enforces honesty

* **Choice**: `create` leaves `<<FILL>>`-style sentinels in judgment sections; `validate`
  treats any leftover sentinel (even multi-line) as an error, cross-checks the Test
  Results `**Status**` line against the `tests_status` frontmatter, and requires *real
  evidence* (pasted output / a command + counts) for any non-`NOT RUN` claim.
* **Why**: Encodes "never invent test results" as a mechanical gate — you cannot claim
  PASSED without showing the run, and an unfilled handoff cannot pass.
* **Alternatives considered**: Trusting the author to fill things in — rejected; the
  whole point is verification-first.

## Stdlib-only Python, custom frontmatter-subset parser

* **Choice**: No third-party deps; a small in-house YAML-subset parser instead of PyYAML.
* **Why**: Deterministic, identical behaviour on every machine; nothing to install;
  satisfies "lightweight scripts, no paid/external dependency". We control the bundle
  format, so the subset (scalars, inline/block lists, quotes, comments) is sufficient.
* **Alternatives considered**: PyYAML (adds a dep + cross-machine parsing drift),
  bash/awk (harder to keep the validation logic clear and portable).

## Adversarial review before shipping

* **Choice**: After the suite was green, run an independent adversarial review of the
  engine and fix every confirmed finding before committing.
* **Why**: Passing tests share blind spots with their author. The review found two HIGH
  guarantee-breaking bugs the green suite missed (empty-fence anti-invention bypass;
  multi-line sentinel). Each fix now has a regression test.
* **Alternatives considered**: Ship on green tests alone — rejected; would have shipped
  two real holes in the core guarantees.
