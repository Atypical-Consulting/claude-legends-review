---
name: review-report
description: >
  Render, regenerate, or merge legends-review reports. Use whenever the user wants an HTML report
  from an existing review report.json, wants to merge several individual persona reviews (elon,
  jobs, linus) into one combined report, wants to re-export a review as markdown, or asks to
  "regenerate the review report", "combine the reviews", or "make an HTML report of the review".
  Also the reference for the shared report.json schema used by elon-review, jobs-review,
  linus-review, and legends-review.
---

# Review Report

## Overview

This is the shared reporting layer for the Legends Review skills. A review produces **data**
(`report.json`); this skill's script renders that data into a **self-contained, actionable HTML
report** plus a diffable `report.md`. The HTML is never written or edited by hand — regenerate it
from the JSON. That's what keeps the reports consistent across reviewers and across time.

The same schema handles an individual review (one persona) and a common one (the three legends
with consensus). The script also merges several individual `report.json` files into one combined
report — so two solo reviews run on the same change can become a single common report after the fact.

## The generator

```bash
python3 <this-skill-dir>/scripts/generate_report.py <report.json> [more.json ...] [-o out.html] [--lang en|fr]
```

- One JSON → individual or consensus report. Several JSONs → merged report (reviewers combined,
  findings renumbered; duplicate reviewer ids are rejected).
- Output lands **next to the first `report.json`** (never the cwd) unless `-o` is given.
  A `report.md` (grep/diff-friendly checklist) lands next to the HTML unless `--no-md`.
- The HTML is standalone — inline CSS/JS, no external requests, light/dark theme — and actionable:
  - a done-checkbox per finding, persisted in `localStorage`, with a progress bar
  - filters by severity, reviewer, and category, plus "hide done"
  - a **Copy fix prompt** button per finding — a ready-to-paste Claude Code prompt with the file,
    line, description, and recommendation
  - a markdown export of the remaining (unchecked) findings

After generating, open the report for the user (`open` on macOS, `xdg-open` on Linux).

## Where reports live

Write each review under `reviews/<yyyy-mm-dd>-<reviewers>/` at the root of the reviewed repo
(e.g. `reviews/2026-07-23-elon/report.json`). The reports archive next to the code they judge;
the user decides whether to commit them or add `reviews/` to `.gitignore`.

## The report.json schema

Required at the top level: `date`, `repo`, `reviewers`, `findings`. Everything else is optional —
omit what doesn't apply rather than inventing empty values.

```json
{
  "schema": "legends-review/1",
  "date": "2026-07-23",
  "repo": "my-app",
  "branch": "feature/checkout",
  "commit": "abc1234",
  "review_type": "solo",
  "change_summary": "One sentence on what changed — becomes the report headline.",
  "scope": "What was reviewed: the diff, the files, the surface.",
  "reviewers": [
    {
      "id": "elon", "name": "Elon Musk", "emoji": "🔥",
      "rating": 7,
      "verdict": "One-line verdict, in the persona's voice.",
      "hard_truth": "The one uncomfortable sentence.",
      "assessment": [
        { "area": "Complexity", "rating": "yellow", "notes": "short note" }
      ]
    }
  ],
  "consensus": {
    "rating": 7,
    "agreements": ["Finding all three converged on — highest-confidence items."],
    "disagreements": [
      { "topic": "Delete the validation layer?", "resolution": "Linus won: it prevents a class of runtime errors." }
    ]
  },
  "findings": [
    {
      "id": 1,
      "reviewer": "elon",
      "agreed_by": ["linus"],
      "severity": "major",
      "category": "security",
      "title": "Exception details leak to the client",
      "file": "src/Api/ErrorHandler.cs",
      "line": 42,
      "description": "Why this matters — the concrete failure, not a vague concern.",
      "recommendation": "The specific change to make.",
      "fix_hint": "optional code or diff snippet",
      "effort": "S"
    }
  ],
  "actions": [
    { "rank": 1, "title": "Top action, ordered by impact", "champion": "elon", "supported_by": ["linus"], "effort": "M", "finding_ids": [1] }
  ],
  "praise": ["What's genuinely well-crafted — reviews that only find flaws lose trust."]
}
```

Field rules that make the report actionable rather than decorative:

- **severity** is one of `critical | major | minor | info` — the script rejects anything else.
  Critical = wrong/insecure/will break in production. Major = real problem, fix before merge.
  Minor = worth fixing, not blocking. Info = observation or suggestion.
- **category** is free-form but stick to a small vocabulary so filters stay useful:
  `security`, `correctness`, `performance`, `observability`, `error-handling`, `dx`, `naming`,
  `documentation`, `testing`, `architecture`, `simplicity`.
- **description** answers "why is this a problem"; **recommendation** answers "what exactly do I
  do about it". A finding without a concrete recommendation is an opinion, not a finding.
- **file`/`line** whenever the finding points at code — they feed the copy-paste fix prompt.
- **effort** is `S | M | L` (under an hour / a session / a project).
- `consensus` exists only for legends (team) reviews. `agreed_by` marks findings that several
  reviewers converged on — they render with multiple reviewer badges and deserve priority.
- The persona's voice lives in `verdict`, `hard_truth`, and assessment `notes`. Keep `description`
  and `recommendation` professional — they're what gets pasted into fix prompts and issues.

## Common Mistakes

- **Writing the HTML by hand.** The JSON is the source of truth; the HTML is generated. If the
  report looks wrong, fix the JSON or the generator, then regenerate.
- **Findings in the JSON that differ from the review.** The terminal review and the report must
  tell the same story: same problems, same severities, same count.
- **Vague recommendations.** "Improve error handling" helps nobody. "Return a ProblemDetails
  without the stack trace and log the full exception at Error level" is actionable.
- **Merging two reports of different changes.** Merge combines perspectives on the *same* change;
  merging unrelated reviews produces a report whose header lies.
