#!/usr/bin/env bash
# Golden test for the report generator bundled with legends-review (mandatory tool -> mandatory test).
# Fixtures -> HTML + MD, then assertions on the produced content.
set -euo pipefail
cd "$(dirname "$0")/../.."

gen="skills/legends-review/scripts/generate_report.py"
tmp="$(mktemp -d)"

assert() { grep -qF -- "$2" "$1" || { echo "FAIL: \"$2\" missing from $1"; exit 1; }; }
refuse() { ! grep -qF -- "$2" "$1" || { echo "FAIL: \"$2\" present in $1 but should not be"; exit 1; }; }

# --- Solo report ---
python3 "$gen" tests/report-format/fixture-solo.json -o "$tmp/solo.html" 2>/dev/null
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
python3 "$gen" tests/report-format/fixture-legends.json -o "$tmp/legends.html" 2>/dev/null
assert "$tmp/legends.html" 'Consensus'
assert "$tmp/legends.html" 'Where they agreed'
assert "$tmp/legends.html" 'Linus won: it prevents a class of runtime errors.'
assert "$tmp/legends.html" 'This will break at 3 AM'
assert "$tmp/legends.html" 'championed by Elon Musk'

# --- Merge: two solos with distinct reviewers -> combined report ---
python3 - "$tmp" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path("tests/report-format/fixture-solo.json").read_text())
r["reviewers"] = [{"id": "linus", "name": "Linus Torvalds", "emoji": "🐧", "rating": 8,
                   "verdict": "Correct, surprisingly."}]
for f in r["findings"]:
    f["reviewer"] = "linus"
Path(sys.argv[1], "solo-linus.json").write_text(json.dumps(r))
PY
python3 "$gen" tests/report-format/fixture-solo.json "$tmp/solo-linus.json" -o "$tmp/merged.html" 2>/dev/null
assert "$tmp/merged.html" 'Elon Musk'
assert "$tmp/merged.html" 'Linus Torvalds'
assert "$tmp/merged.html" 'Average'
# Merging the SAME reviewer twice must fail
if python3 "$gen" tests/report-format/fixture-solo.json tests/report-format/fixture-solo.json -o "$tmp/dup.html" 2>/dev/null; then
  echo "FAIL: merging duplicate reviewer ids should be rejected"; exit 1
fi

# --- Without -o, output lands NEXT TO the report.json, never in the cwd ---
cp tests/report-format/fixture-solo.json "$tmp/report.json"
python3 "$gen" "$tmp/report.json" 2>/dev/null
[ -f "$tmp/report.html" ] || { echo "FAIL: without -o, report.html must land next to report.json"; exit 1; }
[ ! -f report.html ] || { echo "FAIL: without -o, nothing must be written in the cwd"; exit 1; }

# --- Resolved findings pre-check boxes; action-plan state derives from finding_ids ---
python3 - "$tmp" <<'PYEOF'
import json, sys
from pathlib import Path
r = json.loads(Path("tests/report-format/fixture-solo.json").read_text())
r["findings"][0]["resolved"] = True
ids = [f["id"] for f in r["findings"]]
r["actions"] = [
    {"rank": 1, "title": "Action fully resolved", "finding_ids": [r["findings"][0]["id"]]},
    {"rank": 2, "title": "Action still open", "finding_ids": ids},
]
Path(sys.argv[1], "resolved.json").write_text(json.dumps(r))
PYEOF
python3 "$gen" "$tmp/resolved.json" -o "$tmp/resolved.html" 2>/dev/null
assert "$tmp/resolved.html" 'data-resolved="1"'
assert "$tmp/resolved.html" 'class="box done"'
assert "$tmp/resolved.md" '- [x] **Exception details leak to the client**'
assert "$tmp/resolved.md" '1. [x] Action fully resolved'
assert "$tmp/resolved.md" '2. [ ] Action still open'
# Untouched fixture: nothing pre-checked
refuse "$tmp/solo.html" 'class="box done"'
refuse "$tmp/solo.md" '- [x]'

# --- French labels ---
python3 "$gen" tests/report-format/fixture-solo.json -o "$tmp/fr.html" --lang fr 2>/dev/null
assert "$tmp/fr.html" 'Revue de code'
assert "$tmp/fr.html" 'Copier le prompt de fix'

# --- Invalid severity is rejected ---
python3 - "$tmp" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path("tests/report-format/fixture-solo.json").read_text())
r["findings"][0]["severity"] = "catastrophic"
Path(sys.argv[1], "bad.json").write_text(json.dumps(r))
PY
if python3 "$gen" "$tmp/bad.json" -o "$tmp/bad.html" 2>/dev/null; then
  echo "FAIL: invalid severity should be rejected"; exit 1
fi

echo "OK report-format golden test ($tmp)"
