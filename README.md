# Legends Review

Code reviews by Elon Musk, Steve Jobs, and Linus Torvalds — powered by Claude Code Skills.

Four skills that bring legendary perspectives to your code reviews:

| Skill | Command | Perspective |
|-------|---------|-------------|
| **Elon Review** | `/elon-review` | Business value, first principles, speed, deletion |
| **Jobs Review** | `/jobs-review` | Design, developer experience, product vision, taste |
| **Linus Review** | `/linus-review` | Correctness, engineering rigor, abstractions, maintainability |
| **Legends Review** | `/legends-review` | All three debate until consensus (requires Agent Teams) |

## Install

One-liner — no cloning required:

```bash
curl -fsSL https://raw.githubusercontent.com/Atypical-Consulting/claude-legends-review/main/install.sh | bash
```

Or with `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/Atypical-Consulting/claude-legends-review/main/install.sh | bash
```

### Manual Install

Copy the `skills/` folders into `~/.claude/skills/`:

```bash
git clone https://github.com/Atypical-Consulting/claude-legends-review.git
cp -r claude-legends-review/skills/* ~/.claude/skills/
```

## Usage

After installing, use any skill as a slash command in Claude Code:

```
/elon-review      # "Should this exist? Could it be 10x simpler?"
/jobs-review      # "How does this feel? Does it earn its place?"
/linus-review     # "Is this correct? Does this abstraction earn its existence?"
/legends-review   # All three review, debate, and reach consensus
```

### Individual Reviews

Each reviewer produces a structured report with ratings, specific findings, and actionable recommendations in their unique voice.

### Legends Review (Team)

The full `/legends-review` spawns all three as an agent team:

1. **Phase 1** — Each reviewer works independently
2. **Phase 2** — They read each other's reviews and debate in character
3. **Phase 3** — Consensus on final rating and top actions
4. **Synthesis** — Lead produces a unified report with agreements, disagreements, and hard truths

> Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to be enabled in settings.json.

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- For `/legends-review`: Agent Teams experimental feature enabled

## License

[MIT](LICENSE)
