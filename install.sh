#!/usr/bin/env bash
set -euo pipefail

REPO="Atypical-Consulting/claude-legends-review"
BRANCH="main"
SKILLS_DIR="${HOME}/.claude/skills"
SKILLS="elon-review jobs-review linus-review legends-review"

echo "Installing Legends Review skills..."

mkdir -p "$SKILLS_DIR"

for skill in $SKILLS; do
  mkdir -p "$SKILLS_DIR/$skill"
  url="https://raw.githubusercontent.com/$REPO/$BRANCH/skills/$skill/SKILL.md"
  if command -v curl &>/dev/null; then
    curl -fsSL "$url" -o "$SKILLS_DIR/$skill/SKILL.md"
  elif command -v wget &>/dev/null; then
    wget -qO "$SKILLS_DIR/$skill/SKILL.md" "$url"
  else
    echo "Error: curl or wget required" >&2
    exit 1
  fi
  echo "  Installed $skill"
done

echo ""
echo "Done! Skills installed to $SKILLS_DIR"
echo ""
echo "Usage:"
echo "  /elon-review      Elon Musk review"
echo "  /jobs-review      Steve Jobs review"
echo "  /linus-review     Linus Torvalds review"
echo "  /legends-review   All three debate to consensus"
