---
name: handoff-create
description: Create a verification-first OKF session handoff so a fresh Claude Code session can resume safely. Use when the session's context is getting long/full, before /clear or /compact, when the user says "create a handoff", "hand off this session", "save state before I restart", "wrap up so I can continue tomorrow", or when you sense you're losing earlier context. Captures REAL git state and never invents test results.
---

# Create an OKF session handoff

A handoff is an OKF v0.1 knowledge bundle (a directory of markdown files) that lets
a **fresh** session resume this work without relying on hidden chat history. The
golden rule: **record only what you can verify. Never invent test results.**

## Procedure

1. **Scaffold from real git state.** From the root of the project you are handing off
   (the bundle is created in *that* project's `handoffs/`), run:

   ```
   python scripts/okf_handoff.py create --title "<short task title>"
   ```

   This inspects the live repo (`git rev-parse`, `git status`, `git diff`) and writes
   a bundle under `handoffs/<date>-<slug>/` with the deterministic git facts already
   filled in and a `status_fingerprint` for later drift detection. The judgment
   sections are left as `<<FILL: ...>>` sentinels.

2. **Fill every `<<FILL: ...>>` sentinel from the REAL session.** Edit the bundle:
   - `manifest.md` — the task, current status, one-line description.
   - `progress.md` — what is actually **done**, what is **in progress** (and exactly
     where you stopped), and the concrete **Next Actions**.
   - `decisions.md` — decisions made and *why* (so they aren't relitigated).
   - `verification.md` — **Commands Run**, **Test Results**, **Known Failures**, and
     **Do Not Assume**.
   - `open-questions.md` — anything unresolved (write "None" if there are none).

3. **Be honest about tests — this is enforced.** In `verification.md`:
   - If you ran tests, set frontmatter `tests_status:` to `passed`/`failed`/`partial`,
     set the body `**Status: ...**` line to match, and **paste the exact command and
     its result counts** (e.g. ```pytest -q``` → `42 passed in 1.2s`).
   - If you did **not** run them, leave `tests_status: not_run` / `**Status: NOT RUN**`
     and say which command would verify the work. Do **not** claim a result you don't
     have — the validator rejects a "PASSED" with no evidence or a status that
     contradicts the frontmatter.

4. **Write Do Not Assume notes.** List things the next session must *not* take on
   faith, each with how to verify it (e.g. "Do not assume the migration ran — check
   `SELECT version FROM schema_migrations`").

5. **Validate until green.**

   ```
   python scripts/okf_handoff.py validate handoffs/<id>
   ```

   Fix every `ERROR`. Warnings are advisory. The bundle is not done until validation
   passes.

6. **Commit the bundle** so the next session reads it from git, then append a line to
   the bundle's `log.md` if you made notable edits.

   ```
   git add handoffs/<id> && git commit -m "handoff: <title>"
   ```

## Notes
- The script fills *git facts*; you fill *judgment*. Keep entries terse and structural
  (lists, tables, fenced commands) — they are read by another agent.
- This bundle is **guidance, not ground truth.** Write it so a skeptical reader can
  re-verify everything. See the `handoff-resume` skill for the consuming side.
