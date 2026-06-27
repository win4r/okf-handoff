# OKF Session Handoff for Claude Code

[![ci](https://github.com/win4r/okf-handoff/actions/workflows/ci.yml/badge.svg)](https://github.com/win4r/okf-handoff/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![python: 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen.svg)

Hand off a long Claude Code session to a **fresh** one without losing context — and
without trusting hidden chat history or stale summaries.

When a session's context window fills up, you create a structured **handoff**, start a
clean session, and resume safely. The handoff is an [Open Knowledge Format
(OKF)][okf]-style bundle: plain markdown files with YAML frontmatter, living in your
git repo. OKF is used as a **design pattern, not a dependency** — no Gemini, Google
Cloud, BigQuery, or any paid service. Just Markdown, YAML, Git, and one stdlib-only
Python script.

The workflow is **verification-first**: handoffs record only what was actually
observed (real git state, real test results), and a resuming session **re-verifies the
repo before trusting anything**. The handoff is *guidance, not ground truth.*

## Why

A long session accumulates context the model can no longer hold reliably. Summaries
drift. Chat history is hidden from the next session. This gives you a portable,
diffable, verifiable snapshot of *where you are* that a fresh session can pick up.

## Layout

```
scripts/okf_handoff.py     # the whole engine: create | validate | verify (stdlib only)
.claude/skills/            # handoff-create, handoff-resume  (auto-triggered)
.claude/commands/          # /handoff, /resume               (explicit)
handoffs/                  # your handoff bundles live here
tests/e2e.py               # deterministic end-to-end test (no network, no LLM)
SPEC.md                    # the OKF-Handoff profile of OKF v0.1
CLAUDE.md                  # minimal instructions a fresh session reads
install.sh / uninstall.sh  # install the skills + commands user-globally
```

## Install (optional)

Out of the box the skills and `/handoff` `/resume` commands work whenever you run Claude
Code **inside this repo**. To make them available in **every** project, install them
user-globally:

```
./install.sh        # copies skills + commands into ~/.claude and vendors the engine
```

This is self-contained — it vendors the (dependency-free) engine into
`~/.claude/okf-handoff/`, so it keeps working even if you move or delete this repo.
Honors `$CLAUDE_CONFIG_DIR`. Re-run after `git pull` to refresh; `./uninstall.sh` removes
it. New Claude Code sessions auto-discover the skills and commands.

## Use it

### Create a handoff (running-low session)

```
/handoff Add OAuth refresh-token rotation
```

or directly:

```
python3 scripts/okf_handoff.py create --title "Add OAuth refresh-token rotation"
```

This inspects **real git state** (`git rev-parse`, `git status`, `git diff`) and
scaffolds `handoffs/<date>-<slug>/` with the git facts filled in and `<<FILL: ...>>`
sentinels for the parts only you know. Fill them in — task, progress, decisions,
commands run, **real** test results, known failures, open questions, next actions, and
"Do Not Assume" notes — then validate and commit:

```
python3 scripts/okf_handoff.py validate handoffs/<id>      # must pass (exit 0)
git add handoffs/<id> && git commit -m "handoff: ..."
```

> **Never invent test results.** Record a real run (command + counts) or mark
> `tests_status: not_run`. The validator rejects an unbacked "PASSED".

### Resume in a fresh session

```
/resume                      # picks the latest bundle, or: /resume handoffs/<id>
```

The fresh session reads only `CLAUDE.md` + the handoff, then **verifies before
building**:

```
python3 scripts/okf_handoff.py verify handoffs/<id>   # exit 0 = match, 3 = drift
```

It re-checks `git status`/`git diff`, re-runs the tests, reconciles any discrepancy
(the repo wins), and only then continues the **Next Actions**.

> **Note on the shipped examples.** A committed bundle records an *ancestor* commit (it
> cannot contain its own commit hash), so running `verify` on a shipped example reports
> `DRIFT DETECTED` (exit 3) on a fresh clone — that is the feature working, not a
> failure. The clean NO-DRIFT path (exit 0) is exercised by `python3 tests/e2e.py` and
> by running `create` then `verify` on your own not-yet-committed bundle.

## Commands

| Command | Exit codes | What it does |
|---------|-----------|--------------|
| `create [--title T] [--repo .] [--out DIR] [--id ID]` | 0 ok, 2 not a git repo / dir exists | Capture real git state, scaffold a bundle. |
| `validate <bundle> [--json]` | 0 valid, 1 problems | OKF conformance + handoff quality (see [SPEC.md](SPEC.md) §5). |
| `verify <bundle> [--repo .] [--json]` | 0 no drift, 3 drift, 2 error | Compare recorded git snapshot to the live repo. |

## What gets recorded

branch · commit · changed files · diffstat · completed work · in-progress work ·
decisions + rationale · commands run · **real** test results · known failures · open
questions · next actions · **Do Not Assume** notes — each in its own OKF concept
document. See [SPEC.md](SPEC.md).

## Test it

```
python3 tests/e2e.py        # deterministic: builds throwaway git repos, asserts behavior
```

No network, no LLM, no paid service. Exit 0 = all checks pass.

## Limitations

- Drift detection compares `HEAD` + a content hash of the working-tree changes (see
  [SPEC.md](SPEC.md) §3); it flags *that* the repo moved, not a semantic 3-way merge.
  Two blind spots: a file-mode (`chmod`) change to an already-modified file, and
  index-only staging churn, aren't in the fingerprint — the resume step's `git status`
  + test re-run covers them. Across machines with different ignore rules or EOL
  normalization it may *over*-report drift (the safe direction).
- The validator enforces that test results are backed by pasted output and are
  internally consistent — it makes casual invention fail, but it cannot detect a
  *deliberately* fabricated command transcript. That residual is why the resuming
  session **re-runs the tests itself.**
- The frontmatter parser supports the YAML subset this profile uses (scalars, inline
  and block lists, quotes, comments) — not arbitrary YAML — by design, so the validator
  behaves identically everywhere. Values containing `#` should be quoted.
- The script fills git facts; **you** fill judgment. Decision/next-action *quality* is
  only as good as what you write (the validator enforces presence and honesty about
  tests, not depth).
- A fresh session still has to *follow* the resume procedure; the skills/commands make
  that the default path but cannot force a model to re-verify.

## License

MIT — see [LICENSE](LICENSE).

[okf]: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
