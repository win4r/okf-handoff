# OKF-Handoff Profile (v0.1)

A **profile** of the [Open Knowledge Format (OKF) v0.1][okf] for one purpose:
handing off a long Claude Code session to a fresh one without losing context.

OKF is used here as a **design pattern, not a dependency**. There is no Google
Cloud, Gemini, BigQuery, or any paid/external service — a handoff is just markdown
files with YAML frontmatter in your git repo. If you can `cat` a file you can read
it; if you can `git clone` it you can ship it.

## 1. A handoff is an OKF bundle

A handoff bundle is a directory of markdown concept documents (OKF §3). Each concept
is one `.md` file with a YAML frontmatter block whose only required field is `type`
(OKF §4.1, §9). Concepts cross-link with standard markdown links (OKF §5). The
reserved files `index.md` and `log.md` keep their OKF meaning (OKF §6, §7).

```
handoffs/<date>-<slug>/
├── index.md           # OKF root index; carries okf_version: "0.1"
├── manifest.md        # type: Handoff Manifest  — entry point
├── git-state.md       # type: Git State         — real git snapshot + fingerprint
├── progress.md        # type: Progress          — completed work + next actions
├── decisions.md       # type: Decisions         — choices + rationale
├── verification.md    # type: Verification      — commands, real test results, Do Not Assume
├── open-questions.md  # type: Open Questions     — unresolved questions
└── log.md             # OKF reserved            — chronological history
```

## 2. Concept types

The OKF `type` field carries the profile's semantics. Types are descriptive strings
(OKF does not register types centrally); consumers tolerate unknown types.

| `type` | Required? | Purpose |
|--------|-----------|---------|
| `Handoff Manifest` | **required** | Entry point: task, status, how to resume. |
| `Git State` | **required** | Real branch/commit/changed-files snapshot + drift fingerprint. |
| `Progress` | **required** | Completed work, in-progress work, **Next Actions**. |
| `Verification` | **required** | Commands run, **real** test results, known failures, **Do Not Assume**. |
| `Decisions` | recommended | Decisions made and why. |
| `Open Questions` | recommended | Unresolved questions. |

### Profile-specific frontmatter keys
OKF permits producer-defined keys (OKF §4.1). This profile adds:

- `Handoff Manifest`: `status` ∈ {`in_progress`, `blocked`, `ready_for_review`, `done`},
  `branch`, `commit` (full SHA), `handoff_id`.
- `Git State`: `branch`, `commit`, `status_fingerprint` (see §3).
- `Verification`: `tests_status` ∈ {`passed`, `failed`, `partial`, `not_run`}.

## 3. Drift fingerprint (the verification anchor)

`git-state.md` records a `status_fingerprint` that is **content-sensitive**, so editing
an already-modified file still registers as drift. It is the sha256 of:

```
HEAD_sha
TRACKED
<sorted "status\tpath\tsha256(working-tree content)" for each change vs HEAD>
UNTRACKED
<sorted "sha256(content)\tpath" for each untracked file>
```

For a **deleted** tracked file there is no working-tree content, so the third field is
the literal token `DELETED` (e.g. `D\tpath\tDELETED`).

Changes vs HEAD come from `git -c diff.renames=false diff --name-status HEAD` (rename
detection is disabled so a rename hashes identically everywhere), and untracked files
from `git ls-files --others --exclude-standard`. The handoff bundle's **own** files are
excluded, so creating or committing the handoff is not itself reported as drift.

`verify` recomputes this against the live repo. A handoff is a **snapshot**; the repo
will move on — drift is expected, not a failure.

**Reproducibility.** The fingerprint does not depend on git diff/color/context/rename
config. It *can* differ across environments whose ignore rules (`core.excludesFile`) or
end-of-line normalization differ; that only ever **over**-reports drift (the safe
direction — a resuming session re-verifies anyway). Two known blind spots: a file-mode
(`chmod`) change to an already-modified file, and index-only staging churn, are not
reflected in the fingerprint (the working-tree bytes are unchanged). Re-running tests
and reading `git status` on resume covers these.

## 4. Verification-first contract (the point of the profile)

OKF says consumers must be permissive and tolerate stale/partial bundles (OKF §9).
This profile turns that ethos into an enforced workflow:

1. **Producers record only what they verified.** `git-state.md` is captured from real
   `git` commands. Test results in `verification.md` must be **real**: a claimed
   `PASSED`/`FAILED`/`PARTIAL` must show the command and counts, and must match the
   `tests_status` frontmatter. **Never invent test results.** Honest `not_run` is
   always acceptable.
2. **Consumers re-verify before trusting.** A resuming session runs `verify`, re-reads
   the changed files, and **re-runs the tests** before continuing. The handoff is
   guidance; the repo is ground truth.

## 5. Conformance

A bundle conforms to this profile if it conforms to OKF v0.1 (OKF §9) **and**:

1. The four **required** concept types above are present.
2. No `<<FILL: ...>>` sentinel remains (the bundle is fully authored).
3. `Handoff Manifest` has a valid `status`, a `branch`, and a SHA `commit`; its
   `# Task` section is non-empty.
4. `Git State` has `status_fingerprint`, `branch`, `commit`.
5. `Progress` has at least one concrete item under `# Next Actions`.
6. `Verification` has a valid `tests_status`, a `# Test Results` section whose
   `**Status: ...**` line is consistent with `tests_status` and (if not `NOT RUN`)
   backed by evidence, and a non-empty `# Do Not Assume` list.

`scripts/okf_handoff.py validate` checks all of the above. Broken cross-links are
reported as **warnings**, never errors (OKF §9 requires tolerating them).

## 6. Distribution & portability

A bundle is plain files: commit it to the repo (recommended — gives history and
diffs), tar it, or zip it. It renders on GitHub, opens in any editor, and is indexable
by any tool. No runtime, SDK, or account required.

[okf]: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
