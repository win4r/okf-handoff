---
description: Create a verification-first OKF session handoff from real git state
argument-hint: [short task title]
---

Create an OKF session handoff so a fresh session can resume this work safely.

Follow the **handoff-create** skill exactly. In short:

1. Run `python scripts/okf_handoff.py create --title "$ARGUMENTS"` (uses cwd if no
   title is given — pick a sensible one) to capture REAL git state into a bundle under
   `handoffs/`.
2. Fill every `<<FILL: ...>>` sentinel from what actually happened **this session** —
   task, progress, decisions, commands run, known failures, open questions, next
   actions, and "Do Not Assume" notes.
3. **Never invent test results.** Record real runs with their command and counts, or
   leave `tests_status: not_run` and say what to run.
4. Run `python scripts/okf_handoff.py validate handoffs/<id>` and fix every ERROR.
5. Commit the bundle.

Report the bundle path and the validation result.
