#!/usr/bin/env bash
set -euo pipefail

REPO="Atypical-Consulting/claude-legends-review"
BRANCH="main"
SKILLS_DIR="${HOME}/.claude/skills"
SKILLS="elon-review jobs-review linus-review legends-review"
BASE_URL="https://raw.githubusercontent.com/$REPO/$BRANCH/skills"

# Colors (disable if not a terminal)
if [ -t 1 ]; then
  GREEN='\033[0;32m'
  DIM='\033[0;90m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  GREEN='' DIM='' BOLD='' RESET=''
fi

echo ""
echo -e "${BOLD}Installing Legends Review skills...${RESET}"
echo ""

mkdir -p "$SKILLS_DIR"

download() {
  local url="$1" dest="$2"
  if command -v curl &>/dev/null; then
    curl -fsSL "$url" -o "$dest"
  elif command -v wget &>/dev/null; then
    wget -qO "$dest" "$url" || { rm -f "$dest"; return 1; }
  else
    echo "Error: curl or wget required" >&2
    exit 1
  fi
}

for skill in $SKILLS; do
  mkdir -p "$SKILLS_DIR/$skill"

  # Download SKILL.md (required)
  if download "$BASE_URL/$skill/SKILL.md" "$SKILLS_DIR/$skill/SKILL.md"; then
    echo -e "  ${GREEN}✓${RESET} $skill"
  else
    echo "  ✗ $skill (download failed)" >&2
    exit 1
  fi

  # Download evals if available (optional, don't fail)
  mkdir -p "$SKILLS_DIR/$skill/evals" 2>/dev/null || true
  download "$BASE_URL/$skill/evals/evals.json" "$SKILLS_DIR/$skill/evals/evals.json" 2>/dev/null || true
done

echo ""
echo -e "${BOLD}Done!${RESET} Skills installed to ${DIM}$SKILLS_DIR${RESET}"
echo ""
echo "Usage:"
echo "  /elon-review      Elon Musk — first principles, business value, speed"
echo "  /jobs-review      Steve Jobs — design, DX, product vision"
echo "  /linus-review     Linus Torvalds — correctness, security, engineering rigor"
echo "  /legends-review   All three debate to consensus (requires Agent Teams)"
echo ""
echo -e "${DIM}Uninstall: rm -rf ~/.claude/skills/{elon,jobs,linus,legends}-review${RESET}"
