<p align="center">
  <br>
  <strong>&#x1F525; &#x1F34E; &#x1F427;</strong>
  <br><br>
</p>

<h1 align="center">Legends Review</h1>

<p align="center">
  <strong>Code reviews by Elon Musk, Steve Jobs, and Linus Torvalds.</strong><br>
  They argue until they agree.<br><br>
  <a href="https://github.com/Atypical-Consulting/claude-legends-review/stargazers"><img src="https://img.shields.io/github/stars/Atypical-Consulting/claude-legends-review?style=flat&color=fbbf24&labelColor=0d1117" alt="Stars"></a>
  <a href="https://github.com/Atypical-Consulting/claude-legends-review/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Atypical-Consulting/claude-legends-review?style=flat&color=2dd4a8&labelColor=0d1117" alt="License"></a>
  <a href="https://atypical-consulting.github.io/claude-legends-review/"><img src="https://img.shields.io/badge/docs-website-b48cff?style=flat&labelColor=0d1117" alt="Website"></a>
</p>

<br>

> **One command. Three legendary perspectives. Zero mercy.**
>
> Powered by [Claude Code](https://docs.anthropic.com/en/docs/claude-code) Skills.

<br>

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/Atypical-Consulting/claude-legends-review/main/install.sh | bash
```

That's it. No cloning, no config, no dependencies.

<br>

## The Reviewers

### &#x1F525; Elon Review &nbsp;`/elon-review`

First-principles thinking. Business value. Speed. Deletion.

> *"Delete the abstraction layer. Ship without it. If someone screams, add it back."*

Reviews through: complexity, performance, security, maintainability, test coverage.
Asks: Should this exist? Could it be 10x simpler? What's the opportunity cost?

---

### &#x1F34E; Jobs Review &nbsp;`/jobs-review`

Design obsession. Developer experience. Product vision. Taste.

> *"The API does what it's supposed to. It just doesn't sing."*

Reviews through: API elegance, naming, DX, defaults, the last 10%.
Asks: How does this feel? Would you be proud to demo this? Say no.

---

### &#x1F427; Linus Review &nbsp;`/linus-review`

Engineering rigor. Correctness. Abstractions. Maintainability.

> *"You've built an abstraction layer that adds complexity without removing any. Delete it."*

Reviews through: correctness, abstractions, error handling, performance, readability, naming.
Asks: Is this actually correct? What breaks at 3 AM? Show me the code.

---

### &#x1F3DB;&#xFE0F; Legends Review &nbsp;`/legends-review`

**All three.** They review independently, then debate in character until consensus.

```
Phase 1 → Solo review (no groupthink)
Phase 2 → Cross-review & debate (challenges, defenses, concessions)
Phase 3 → Consensus (unified rating, top actions, hard truths)
```

Produces a final report with:
- Individual ratings and verdicts
- Where they agreed (highest-confidence items)
- Where they fought (and who won)
- Top 5 unified actions
- Three hard truths — one from each legend

> Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` enabled in settings.json.

<br>

## Sample Output

```
🏛️ LEGENDS REVIEW — CONSENSUS REPORT

Reviewed by: Elon Musk 🔥 · Steve Jobs 🍎 · Linus Torvalds 🐧

┌──────────┬────────┬──────────────────────────────────────────────────┐
│ Reviewer │ Rating │ Verdict                                          │
├──────────┼────────┼──────────────────────────────────────────────────┤
│ 🔥 Elon  │  7/10  │ "Ship it, but delete the middleware layer."      │
│ 🍎 Steve │  6/10  │ "Someone cared about this. Now care about the    │
│          │        │  error messages too."                             │
│ 🐧 Linus │  8/10  │ "The error handling is correct. That's rarer     │
│          │        │  than you think."                                 │
└──────────┴────────┴──────────────────────────────────────────────────┘

Consensus Rating: 7/10

Where They Agreed:
  • Delete the middleware abstraction — it creates complexity without removing any
  • Error messages need a complete rewrite for developer experience
  • Add integration tests before shipping

Where They Fought:
  • Elon wanted to delete the validation layer; Linus insisted it prevents
    a class of runtime errors. Linus won.

The Hard Truths:
  🔥 "The architecture is fine. The velocity is not."
  🍎 "This is a collection of endpoints, not a product."
  🐧 "This will break at 3 AM and whoever is on call will curse your name."
```

<br>

## Manual Install

```bash
git clone https://github.com/Atypical-Consulting/claude-legends-review.git
cp -r claude-legends-review/skills/* ~/.claude/skills/
```

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- For `/legends-review`: Agent Teams experimental feature enabled

## License

[MIT](LICENSE) — do whatever you want.

<br>

<p align="center">
  <sub>Built with obsession by <a href="https://github.com/Atypical-Consulting">Atypical Consulting</a> and Claude.</sub>
</p>
