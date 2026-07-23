#!/usr/bin/env bash
# Golden test for the review report generator (mandatory tool -> mandatory test).
# Fixtures -> HTML + MD, then assertions on the produced content.
set -euo pipefail
cd "$(dirname "$0")/../.."

gen="skills/review-report/scripts/generate_report.py"
tmp="$(mktemp -d)"

assert() { grep -qF -- "$2" "$1" || { echo "FAIL: \"$2\" missing from $1"; exit 1; }; }
refuse() { ! grep -qF -- "$2" "$1" || { echo "FAIL: \"$2\" present in $1 but should not be"; exit 1; }; }

# --- Solo report ---
python3 "$gen" tests/review-report/fixture-solo.json -o "$tmp/solo.html" 2>/dev/null
assert "$tmp/solo.html" '<title>Code review FixtureApp — 2026-01-01</title>'
assert "$tmp/solo.html" 'Fixture solo review'
assert "$tmp/solo.html" 'Elon Musk'
assert "$tmp/solo.html" 'Exception details leak to the client'
assert "$tmp/solo.html" 'src/Api/ErrorHandler.cs'
assert "$tmp/solo.html" 'sev-critical'
assert "$tmp/solo.html" 'Copy fix prompt'
assert "$tmp/solo.html" 'The test naming is genuinely clear.'
# Solo: no consensus/average tile
refuse "$tmp/solo.html" 'Average'
# Standalone and themed: no external resource, dark theme present
refuse "$tmp/solo.html" 'http://'
refuse "$tmp/solo.html" 'https://'
assert "$tmp/solo.html" 'data-theme="dark"'
# The diffable markdown lands next to the HTML
assert "$tmp/solo.md" '# Code review — FixtureApp (2026-01-01)'
assert "$tmp/solo.md" '- [ ] **Exception details leak to the client** — `src/Api/ErrorHandler.cs:42` (S)'

# --- Legends (consensus) report ---
python3 "$gen" tests/review-report/fixture-legends.json -o "$tmp/legends.html" 2>/dev/null
assert "$tmp/legends.html" 'Consensus'
assert "$tmp/legends.html" 'Where they agreed'
assert "$tmp/legends.html" 'Linus won: it prevents a class of runtime errors.'
assert "$tmp/legends.html" 'This will break at 3 AM'
assert "$tmp/legends.html" 'championed by Elon Musk'

# --- Merge: two solos with distinct reviewers -> combined report ---
python3 - "$tmp" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path("tests/review-report/fixture-solo.json").read_text())
r["reviewers"] = [{"id": "linus", "name": "Linus Torvalds", "emoji": "🐧", "rating": 8,
                   "verdict": "Correct, surprisingly."}]
for f in r["findings"]:
    f["reviewer"] = "linus"
Path(sys.argv[1], "solo-linus.json").write_text(json.dumps(r))
PY
python3 "$gen" tests/review-report/fixture-solo.json "$tmp/solo-linus.json" -o "$tmp/merged.html" 2>/dev/null
assert "$tmp/merged.html" 'Elon Musk'
assert "$tmp/merged.html" 'Linus Torvalds'
assert "$tmp/merged.html" 'Average'
# Merging the SAME reviewer twice must fail
if python3 "$gen" tests/review-report/fixture-solo.json tests/review-report/fixture-solo.json -o "$tmp/dup.html" 2>/dev/null; then
  echo "FAIL: merging duplicate reviewer ids should be rejected"; exit 1
fi

# --- Without -o, output lands NEXT TO the report.json, never in the cwd ---
cp tests/review-report/fixture-solo.json "$tmp/report.json"
python3 "$gen" "$tmp/report.json" 2>/dev/null
[ -f "$tmp/report.html" ] || { echo "FAIL: without -o, report.html must land next to report.json"; exit 1; }
[ ! -f report.html ] || { echo "FAIL: without -o, nothing must be written in the cwd"; exit 1; }

# --- French labels ---
python3 "$gen" tests/review-report/fixture-solo.json -o "$tmp/fr.html" --lang fr 2>/dev/null
assert "$tmp/fr.html" 'Revue de code'
assert "$tmp/fr.html" 'Copier le prompt de fix'

# --- Invalid severity is rejected ---
python3 - "$tmp" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path("tests/review-report/fixture-solo.json").read_text())
r["findings"][0]["severity"] = "catastrophic"
Path(sys.argv[1], "bad.json").write_text(json.dumps(r))
PY
if python3 "$gen" "$tmp/bad.json" -o "$tmp/bad.html" 2>/dev/null; then
  echo "FAIL: invalid severity should be rejected"; exit 1
fi

echo "OK review-report golden test ($tmp)"
