#!/usr/bin/env bash
# Install the OKF handoff workflow user-globally so /handoff and /resume (and the
# handoff-create / handoff-resume skills) work in EVERY project, not just this repo.
#
# It is self-contained: the engine is vendored into your Claude config dir, so the
# install keeps working even if you later move or delete this repo. Re-run any time to
# refresh. Honors $CLAUDE_CONFIG_DIR (defaults to ~/.claude). Idempotent.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
VEND_DIR="$DEST/okf-handoff"
VEND="$VEND_DIR/okf_handoff.py"

mkdir -p "$DEST/skills" "$DEST/commands" "$VEND_DIR"

# 1. Vendor the (dependency-free) engine.
cp "$SRC/scripts/okf_handoff.py" "$VEND"

# 2. Install the skills and commands.
cp -R "$SRC/.claude/skills/handoff-create" "$SRC/.claude/skills/handoff-resume" "$DEST/skills/"
cp "$SRC/.claude/commands/handoff.md" "$SRC/.claude/commands/resume.md" "$DEST/commands/"

# 3. Point the installed copies at the vendored engine (absolute path) instead of the
#    repo-relative `scripts/okf_handoff.py`. Portable across BSD (macOS) and GNU sed.
#    Escape sed-replacement metacharacters (&, the | delimiter, \) so a config path
#    containing them cannot corrupt or break the substitution.
REPL="python3 \"$VEND\""
REPL_ESC=$(printf '%s' "$REPL" | sed 's/[&|\\]/\\&/g')
for f in "$DEST/skills/handoff-create/SKILL.md" \
         "$DEST/skills/handoff-resume/SKILL.md" \
         "$DEST/commands/handoff.md" \
         "$DEST/commands/resume.md"; do
  sed "s|python[0-9]* scripts/okf_handoff\.py|$REPL_ESC|g" "$f" > "$f.tmp" || { rm -f "$f.tmp"; exit 1; }
  mv "$f.tmp" "$f"
  if grep -q 'scripts/okf_handoff\.py' "$f"; then
    echo "error: failed to rewrite engine path in $f" >&2; exit 1
  fi
done

# 4. Record provenance / refresh instructions next to the vendored engine.
COMMIT="$(git -C "$SRC" rev-parse HEAD 2>/dev/null || echo unknown)"
cat > "$VEND_DIR/SOURCE.md" <<EOF
# okf_handoff.py — vendored copy

Self-contained copy used by the user-global OKF handoff skills/commands. Vendored so the
install does not depend on the source repo continuing to exist.

- Source repo:   $SRC
- Public:        https://github.com/win4r/okf-handoff
- Copied commit: $COMMIT
- Dependencies:  none (Python 3.8+ stdlib only)

Refresh:   cp "$SRC/scripts/okf_handoff.py" "$VEND"
Drift check: diff "$VEND" "$SRC/scripts/okf_handoff.py"
Uninstall: "$SRC/uninstall.sh"
EOF

echo "Installed OKF handoff workflow into: $DEST"
echo "  engine:   $VEND"
echo "  skills:   handoff-create, handoff-resume"
echo "  commands: /handoff, /resume"
echo
echo "Use it in any project: type /handoff (or 'create a handoff'), and /resume in a"
echo "fresh session. New Claude Code sessions pick the skills/commands up automatically."
