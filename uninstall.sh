#!/usr/bin/env bash
# Remove the user-global OKF handoff workflow installed by install.sh.
# Honors $CLAUDE_CONFIG_DIR (defaults to ~/.claude). Leaves your handoffs/ bundles and
# this repo untouched.
set -euo pipefail

DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

rm -rf "$DEST/okf-handoff" \
       "$DEST/skills/handoff-create" \
       "$DEST/skills/handoff-resume" \
       "$DEST/commands/handoff.md" \
       "$DEST/commands/resume.md"

echo "Removed the OKF handoff skills, commands, and vendored engine from: $DEST"
echo "(Your handoffs/ bundles and this repo are untouched.)"
