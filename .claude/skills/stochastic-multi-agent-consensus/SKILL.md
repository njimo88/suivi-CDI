---
name: stochastic-multi-agent-consensus
description: >
  Spawn N agents (default 10) with identical context and near-identical prompts.
  Each independently analyzes a problem and produces a structured response.
  Aggregate by finding consensus (mode), divergences (splits), and outliers
  (unique ideas). Use for decision-making, ranking options, strategic analysis,
  or any problem where you want to filter hallucinations and surface
  high-variance ideas. Triggers on "consensus", "poll agents", "stochastic
  consensus", "spawn N agents to analyze", "multi-agent vote",
  /stochastic-multi-agent-consensus, "what do 10 agents think",
  "get multiple opinions", or "poll on [topic]".
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Stochastic Multi-Agent Consensus

Spawn N agents (default 10) with identical context and near-identical prompts.
Each independently analyzes and produces a structured response. Aggregate by
finding consensus (mode), divergences (splits), and outliers (unique ideas).

**Why this works:** Exploits stochastic variation in LLM outputs. Like polling
10 experts instead of asking one. The mode filters out hallucinations and
individual biases. Divergences reveal genuine judgment calls. Outliers surface
creative ideas a single run would miss.

---

## When to use

Trigger when the user wants multiple independent perspectives on a problem:
- "consensus", "poll agents", "stochastic consensus"
- "spawn N agents to analyze", "multi-agent vote"
- "what do 10 agents think", "get multiple opinions", "poll on [topic]"
- `/stochastic-multi-agent-consensus`

---

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `problem` | yes | — | The question or problem to analyze |
| `n` | no | 10 | Number of agents to spawn |
| `output_format` | no | list | What each agent should produce (rankings, yes/no, recommendations, etc.) |
| `framing_variants` | no | auto | Whether to vary the framing slightly per agent (default: yes) |

---

## Execution

### 1. Parse the request

Extract from the user's message:
- **Problem/question** to analyze
- **Agent count N** — default 10, user can override ("spawn 5 agents", "use 7 agents")
- **Output format** — what each agent should produce (rankings, recommendations, yes/no)
- **Framing variants** — slight persona/angle variations per agent to maximize divergence

### 2. Generate N framing variants

Create N near-identical prompts, each with a slightly different framing lens.
Examples of framing variants:
- neutral / objective analysis
- risk-averse / conservative lens
- growth / optimistic lens
- devil's advocate / contrarian lens
- user-centric / empathy lens
- data-driven / quantitative lens
- first-principles / fundamental lens
- pragmatic / implementation lens
- long-term / strategic lens
- short-term / tactical lens

### 3. Spawn N agents in parallel

Run the aggregation script to orchestrate parallel spawning:

```bash
node .claude/skills/stochastic-multi-agent-consensus/scripts/aggregate.js "<problem>" <n>
```

Each agent receives:
- The full problem context
- Its specific framing variant
- The requested output format
- Instruction to produce a structured, numbered response

### 4. Aggregate results

After all N agents respond, analyze across their outputs:

**Consensus (mode):** Items that ≥70% of agents agreed on. These are the
high-confidence findings — hallucinations rarely survive across 10 independent
runs.

**Divergences (splits):** Items where agents split 40/60 or 50/50. These reveal
genuine judgment calls where reasonable minds differ — flag these explicitly.

**Outliers (unique ideas):** Items only 1-2 agents mentioned. May be creative
leaps or noise — present with lower confidence but don't discard.

### 5. Deliver the synthesis report

Format the final output as:

```
## Consensus (N/N agents agreed)
- [item 1]
- [item 2]
...

## Divergences (split opinions)
- [item]: X agents for, Y agents against — [why it's contested]
...

## Outliers (surfaced by 1-2 agents)
- [item]: mentioned by [n] agent(s) — [brief context]
...

## Raw agent count
N agents polled. Full report at consensus_report.md
```

---

## Scripts

### `scripts/aggregate.js`

Orchestrates the multi-agent run: generates framing variants, tracks results,
and writes the raw per-agent responses to `consensus_report.md`.

```bash
node .claude/skills/stochastic-multi-agent-consensus/scripts/aggregate.js "<problem>" [n]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `problem` | required | The problem/question string |
| `n` | 10 | Number of agents |

Output: `consensus_report.md` with all raw responses + aggregated summary.

---

## Outputs

- Inline synthesis with consensus / divergences / outliers clearly labeled
- `consensus_report.md` with all N raw agent responses for audit

---

## Error handling

| Situation | Action |
|-----------|--------|
| Agent count not specified | Default to 10 |
| Problem is ambiguous | Ask one clarifying question before spawning |
| All agents agree completely | Flag: unusually high consensus, may indicate an easy problem or identical framing — increase framing variance |
| All agents diverge completely | Flag: genuinely contested problem — surface top 3 camps with their reasoning |
| Script fails | Fall back to manually spawning agents sequentially in the conversation |

---

## Learnings / constraints

- Never synthesize from fewer than 3 agents — minimum viable consensus requires N≥3
- Framing variants must be semantically different, not just stylistically — vary the underlying analytical lens
- Report divergences honestly — do not flatten them into false consensus
- The aggregator is read-only: it collects, counts, and categorizes. It does not editorialize.
- Always state N explicitly in the output so the user knows the polling depth
