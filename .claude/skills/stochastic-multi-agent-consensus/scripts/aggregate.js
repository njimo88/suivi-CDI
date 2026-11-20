#!/usr/bin/env node
/**
 * Stochastic Multi-Agent Consensus — aggregator
 * Generates framing variants and writes consensus_report.md template.
 * The parent Claude instance spawns agents using these variants and
 * fills in responses before computing consensus.
 */

const fs = require("fs");
const path = require("path");

const [, , problem, nArg] = process.argv;

if (!problem) {
  console.error("Usage: aggregate.js \"<problem>\" [n]");
  process.exit(1);
}

const n = parseInt(nArg ?? "10", 10);
if (isNaN(n) || n < 3) {
  console.error("Agent count must be a number ≥ 3");
  process.exit(1);
}

const FRAMING_VARIANTS = [
  "neutral / objective analysis",
  "risk-averse / conservative lens",
  "growth / optimistic lens",
  "devil's advocate / contrarian lens",
  "user-centric / empathy lens",
  "data-driven / quantitative lens",
  "first-principles / fundamental lens",
  "pragmatic / implementation lens",
  "long-term / strategic lens",
  "short-term / tactical lens",
  "cost-focused / efficiency lens",
  "innovation / disruptive lens",
];

const variants = FRAMING_VARIANTS.slice(0, n);

const timestamp = new Date().toISOString();
const reportPath = path.join(process.cwd(), "consensus_report.md");

const sections = variants.map((framing, i) => {
  return `## Agent ${i + 1} — ${framing}\n\n> Prompt: Analyze the following problem from a ${framing}.\n>\n> PROBLEM: ${problem}\n\n[RESPONSE PENDING]\n`;
});

const report = [
  `# Consensus Report`,
  ``,
  `**Problem:** ${problem}`,
  `**Agents:** ${n}`,
  `**Generated:** ${timestamp}`,
  ``,
  `---`,
  ``,
  ...sections,
  `---`,
  ``,
  `## Aggregated Summary`,
  ``,
  `### Consensus (items ≥70% agreement)`,
  ``,
  `[TO BE FILLED BY AGGREGATOR]`,
  ``,
  `### Divergences (split 40/60 or 50/50)`,
  ``,
  `[TO BE FILLED BY AGGREGATOR]`,
  ``,
  `### Outliers (1-2 agents only)`,
  ``,
  `[TO BE FILLED BY AGGREGATOR]`,
].join("\n");

fs.writeFileSync(reportPath, report, "utf-8");

console.log(`Spawning ${n} agents for problem:`);
console.log(`  "${problem}"`);
console.log(``);
console.log(`Framing variants:`);
variants.forEach((v, i) => console.log(`  ${i + 1}. ${v}`));
console.log(``);
console.log(`Template written to: ${reportPath}`);
console.log(`Spawn agents in parallel, fill responses, then aggregate.`);

process.exit(0);
