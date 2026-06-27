---
type: Open Questions
title: Open Questions
description: Unresolved questions blocking or shaping the next steps.
timestamp: 2026-06-27T08:57:24Z
tags: [handoff]
---

# Open Questions

1. Should the skills/commands ship per-repo (current: `.claude/` in this repo) or be
   installed user-globally in `~/.claude/` so every project gets `/handoff` + `/resume`?
   Per-repo keeps it self-contained and testable; global is more convenient. Decide
   based on how the user wants to adopt it.
2. Should we add an optional, non-deterministic live test that runs `claude -p` against
   only `CLAUDE.md` + a bundle to prove a real fresh session resumes correctly? It would
   strengthen confidence but is non-deterministic and is excluded from the E2E gate by
   design.
   - **Resolved later (annotation):** the live `claude -p` resume was performed at HEAD
     `9b0c0a8`; exact command + transcript are in the
     [published-release validation handoff](../2026-06-27-published-release-validation/verification.md).
     It remains excluded from the deterministic E2E gate by design.
3. Do we want a `prune`/`archive` command for old handoffs under `handoffs/`, or is git
   history enough?
