# OKF Session Handoff

When this session's context grows too large to continue reliably, hand off to a
fresh session instead of trusting stale summaries.

- **Create a handoff:** `/handoff` (or the `handoff-create` skill). Captures *real*
  git state into an OKF bundle under `handoffs/`. Fill the judgment sections from
  fact — **never invent test results.**
- **Resume:** in a fresh session, `/resume` (or the `handoff-resume` skill). Verify
  git state and re-run tests *before* trusting the handoff. It is **guidance, not
  ground truth.**
- **Validate:** `python scripts/okf_handoff.py validate handoffs/<id>` (must pass).
- **Check drift:** `python scripts/okf_handoff.py verify handoffs/<id>`.

Details: [README.md](README.md) · format: OKF v0.1 profile in [SPEC.md](SPEC.md).
