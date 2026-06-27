---
name: handoff-resume
description: Resume work in a fresh Claude Code session from an OKF handoff bundle, verification-first. Use at the start of a session when the user says "resume from the handoff", "continue where the last session left off", "pick up the previous session", "read the handoff", or when a handoffs/ bundle exists and you are starting fresh. Verifies real git state and tests BEFORE trusting the handoff — treats it as guidance, not ground truth.
---

# Resume from an OKF session handoff

A handoff tells you what a previous session *believed*. The repo is the truth. Your
job is to **re-verify before you build**, detect anything that drifted, and only then
continue. Treat the handoff as guidance, **not ground truth.**

## Procedure

1. **Find the handoff.** It lives under `handoffs/`. If the user named one, use it;
   otherwise pick the most recent. Read `index.md`, then `manifest.md` first.

2. **Read the whole bundle.** `manifest.md` → `git-state.md` → `progress.md` →
   `decisions.md` → `verification.md` → `open-questions.md`. Note especially the
   **Do Not Assume** list and **Next Actions**.

3. **Detect git drift — before doing anything else.**

   ```
   python3 scripts/okf_handoff.py verify handoffs/<id>
   ```

   - Exit `0` (NO DRIFT): the working tree still matches the snapshot.
   - Exit `3` (DRIFT): branch/commit/working-tree changed since the handoff. This is
     **expected, not an error.** Read the reported differences carefully.

4. **Re-establish ground truth yourself.** Regardless of drift, run:
   - `git status` and `git log --oneline -5` — where is HEAD really?
   - `git diff` / `git diff HEAD` — what is actually changed?
   - Open the files the handoff says it touched and confirm their real content.

5. **Re-run the tests.** Do **not** trust the recorded results. Run the command from
   `verification.md` (or the project's test command) yourself and compare to what the
   handoff claimed. If they disagree, the repo wins — investigate the gap.

6. **Reconcile discrepancies out loud.** Briefly tell the user what matches, what
   drifted, and anything in the handoff that the current repo contradicts. If a
   "Do Not Assume" item turns out false, flag it.

7. **Only now continue.** Work the **Next Actions** from `progress.md`, honoring the
   **Decisions** already made and the **Open Questions** still outstanding.

## If the handoff is wrong
Drift and stale claims are normal — that's why this is verification-first. When the
handoff contradicts the repo, prefer the repo, state the discrepancy, and (optionally)
note it in the bundle's `log.md` before continuing.
