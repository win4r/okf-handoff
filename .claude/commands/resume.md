---
description: Resume from an OKF session handoff, verifying repo state before continuing
argument-hint: [handoff bundle path, default: latest under handoffs/]
---

Resume work from an OKF session handoff, **verification-first**.

Follow the **handoff-resume** skill exactly. In short:

1. Pick the handoff bundle: `$ARGUMENTS` if given, otherwise the most recent under
   `handoffs/`. Read `manifest.md` then the rest of the bundle.
2. Detect drift: `python scripts/okf_handoff.py verify <bundle>` (exit 3 = drift; that
   is expected, not an error — read the differences).
3. Re-establish ground truth yourself: `git status`, `git log --oneline -5`,
   `git diff HEAD`, and open the files the handoff claims it changed.
4. **Re-run the tests** named in `verification.md` — do not trust recorded results.
5. Tell the user what matches, what drifted, and any handoff claim the repo
   contradicts (the repo wins).
6. Only then continue with the **Next Actions**, honoring recorded **Decisions** and
   outstanding **Open Questions**.

The handoff is guidance, not ground truth.
