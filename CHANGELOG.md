# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com); the tool version is SemVer and is
distinct from the OKF **bundle-format** version (`OKF_VERSION`, currently 0.1).

## [0.1.0] — 2026-06-27

### Added
- OKF-inspired, verification-first session handoff workflow: `scripts/okf_handoff.py`
  (`create` / `validate` / `verify`), zero third-party dependencies (Python 3.8+ stdlib).
- Claude Code integration: `handoff-create` / `handoff-resume` skills and `/handoff` /
  `/resume` commands.
- Self-contained user-global installer (`install.sh` / `uninstall.sh`).
- Deterministic end-to-end test suite (`tests/e2e.py`) — no network, no LLM.
- GitHub Actions CI: runs the E2E suite and validates the shipped handoff bundles across
  Python 3.8 / 3.11 / 3.13, plus an installer smoke job.
- MIT `LICENSE`; `--version` flag.

### Security
- `validate` / `verify` refuse bundle-escaping symlinks and oversized documents, so a
  malicious committed bundle cannot make the tool read arbitrary local files or exhaust
  memory (untrusted-bundle hardening).
- `install.sh` sed replacement is now metacharacter-safe (`&`, `|`, `\` in the config
  path can no longer silently corrupt the install).

### Fixed
- All documentation uses `python3` (some hosts have no `python` on PATH).
- `tests/e2e.py` no longer requires git ≥ 2.28.
- Removed a developer home-path string from a shipped example bundle.
