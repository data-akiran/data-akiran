# CCAF — Crisp Revision Sheet

One-line-per-concept quick review. Use the theory guide if you need the "why."

---

# DOMAIN 1: Agentic Architecture & Orchestration (27%)

**1.1 Agentic loops**
- `stop_reason` is authoritative, not text-matching ("done"/"complete").
- `"tool_use"` → execute + loop back. `"end_turn"` → exit.
- `"max_tokens"` → response truncated, possibly mid tool-call → don't execute partial call; retry/extend, don't discard.
- Iteration cap = secondary safety net only, never the primary stop signal.

**1.2 Coordinator–subagent orchestration**
- Dynamic subagent selection — don't always run every subagent.
- Decomposition must be broad enough to cover full scope (don't over-narrow).
- All subagents did their job correctly but output is incomplete → blame coordinator's scoping, not execution.
- Strict hub-and-spoke: no direct subagent↔subagent calls, no shared globals — everything routes through coordinator.

**1.3 Subagent invocation & context**
- `"Task"` must be in `allowedTools` to spawn subagents.
- No automatic context inheritance — coordinator must explicitly paste prior findings into subagent prompt.
- Parallel spawning = multiple `Task` calls in one turn (not sequential turns).
- `fork_session` = branch divergent strategies off one shared baseline (no repeated exploration).

**1.4 Workflow enforcement & handoff**
- Business-critical steps (financial/legal/safety) → programmatic gate, not just a prompt instruction.
- Human handoff needs a structured summary (ID, root cause, amounts, recommended action) — human has no transcript access.
- Multi-concern request → decompose, investigate each, synthesize one unified response.

**1.5 Agent SDK hooks**
- `PostToolUse` hook → normalize inconsistent tool output formats before model sees them.
- `PreToolUse`/interception hook → block/redirect calls that violate hard business rules.
- Hooks = guarantees (compliance-critical). Prompts = soft guidance (style/tone), not hard guarantees.

**1.6 Task decomposition strategy**
- Predictable/repeatable task → prompt chaining (fixed pipeline).
- Open-ended/exploratory task → dynamic decomposition (plan evolves with discovery).
- Large multi-file review → split into per-file passes + separate cross-file integration pass (avoids attention dilution).

**1.7 Session state, resume, fork**
- `--resume <name>` = continue named session; if files changed, explicitly tell it what changed (no auto-detection).
- `fork_session` = branch off shared baseline for divergent approaches.
- Mostly-stale prior context → start fresh session + inject curated summary, don't resume.

---

# DOMAIN 2: Tool Design & MCP Integration (18%)

**2.1 Tool interface design**
- Tool descriptions = primary signal for tool selection.
- Near-duplicate descriptions = most common cause of misrouting → fix via clearer/renamed descriptions.
- Split overly generic tools into purpose-specific ones with narrow contracts.
- Check system prompt for keyword bias affecting tool choice.

**2.2 Structured MCP error responses**
- Categorize errors: transient / validation / business / permission + `isRetryable` flag + message.
- Never conflate "query failed" with "query succeeded, found nothing" — use `isError` distinctly.
- Attempt local recovery for transient errors before propagating to coordinator.

**2.3 Tool distribution & tool_choice**
- Scope each subagent's tools to its role; add narrow cross-role tool only if needed (not the whole other agent's kit).
- `tool_choice: "auto"` = model decides freely (default).
- `tool_choice: "any"` = force *some* tool call, no free text.
- `tool_choice: {"type":"tool","name":...}` = force a *specific* tool (e.g., must run first).

**2.4 MCP server integration**
- `.mcp.json` (project root) = shared, version-controlled; use env var expansion for secrets.
- `~/.claude.json` = personal/experimental only, not shared.
- Model ignoring your MCP tool for a built-in one → improve the MCP tool's description first.
- Static/browsable content (e.g., schema catalog) → expose as an MCP **resource**, not a tool.

**2.5 Built-in tools**
- `Grep` = search file *contents*. `Glob` = find files by *name/path pattern*.
- `Read`/`Write` = whole-file ops. `Edit` = small unique-anchor changes.
- `Edit` fails on non-unique anchor → fallback: `Read` full file → apply fix → `Write` back.
- Explore large unfamiliar codebase incrementally: `Grep` for entry points → `Read` selectively (don't read everything upfront).

---

# DOMAIN 3: Claude Code Configuration & Workflows (20%)

**3.1 CLAUDE.md hierarchy**
- `~/.claude/CLAUDE.md` = personal, never shared. Project `CLAUDE.md`/`.claude/CLAUDE.md` = shared, version-controlled.
- "Works for me, not my teammate" → conventions likely stuck in someone's personal file.
- `@import` = pull shared root conventions into package-level files (avoid duplication).
- Sprawling `CLAUDE.md` → split into `.claude/rules/` by topic.
- `/memory` = inspect which memory files are actually loaded (debugging tool).

**3.2 Slash commands & skills**
- `.claude/commands/` = shared/project (auto after clone). `~/.claude/commands/` = personal only.
- `context: fork` = isolate verbose skill output in sub-agent context (keeps main session clean).
- `allowed-tools` = restrict what a skill/command can do (e.g., lock down a destructive `/deploy`).
- `argument-hint` = prompt for required params.
- Skills = on-demand task-specific workflows. `CLAUDE.md` = always-loaded universal standards.

**3.3 Path-specific rules**
- `.claude/rules/*.md` with YAML `paths:` glob → loads only when a matching file is being edited.
- Best for conventions tied to *file type*, not directory (e.g., scattered `*.test.tsx` files).
- Advantage over monolithic `CLAUDE.md`: conditional loading = lower constant token overhead.

**3.4 Plan mode vs direct execution**
- Simple, well-scoped, single-file, clear spec → direct execution.
- Architectural decisions / many files / multiple valid approaches → plan mode (explore → propose → approve → execute).
- Verbose discovery phase → delegate to Explore subagent (keeps main context clean, only summaries return).

**3.5 Iterative refinement**
- Inconsistent output despite detailed prose → give 2–3 concrete input→output examples instead.
- Implementation tasks → write tests first, iterate on failures.
- Unfamiliar domain/real ambiguity → "interview pattern" (Claude asks clarifying Qs before implementing).
- Interacting issues → batch together in one message. Independent issues → fix separately/sequentially.

**3.6 CI/CD integration**
- `-p`/`--print` required for non-interactive/CI runs (else it hangs).
- `--output-format json` + `--json-schema` → machine-parseable structured findings (not regex over free text).
- `CLAUDE.md` should hold CI-relevant context (testing standards, review criteria).
- Self-review (same session) is weak — use an independent second instance for review.

---

# DOMAIN 4: Prompt Engineering & Structured Output (20%)

**4.1 Explicit criteria for precision**
- Replace vague qualifiers ("be conservative," "high-confidence") with concrete, checkable categorical rules.
- One category has high false-positive rate → temporarily disable just that category, keep others active.
- Concrete examples per severity/category level → improves classification consistency.

**4.2 Few-shot prompting**
- Target few-shot examples (2–4) at ambiguous/edge cases, not typical/easy cases.
- Include *reasoning* in examples, not just input→output — helps generalization to new cases.
- Extraction failing on structural variety (e.g., prose vs. tables) → add examples covering that variety.

**4.3 Structured output via tool use / schemas**
- `tool_use` + JSON schema → guarantees syntax validity, not semantic correctness — still need separate semantic checks (e.g., totals match).
- Nullable/optional fields when source data may genuinely be missing → prevents fabrication to satisfy "required."
- `enum` + `"other"` + free-text detail = extensible categorical field pattern.

**4.4 Validation, retry, feedback loops**
- Retry with specific error feedback (original doc + failed extraction + error message) for structural/format failures.
- Info genuinely absent from source → retrying won't help → resolve field to `null` instead.
- Add structured fields (e.g., `detected_pattern`) to enable later false-positive/error-pattern analysis.

**4.5 Batch processing strategy**
- Batch API: ~50% cheaper, no latency SLA (up to 24h) → good for latency-tolerant/high-volume workloads only.
- Real-time API → required for blocking/developer-waiting workflows, regardless of cost savings.
- `custom_id` → correlate + resubmit only failed items on partial batch failure.
- Test on a small sample before submitting a huge batch. Batch API doesn't support multi-turn tool calling.

**4.6 Multi-instance / multi-pass review**
- Never let the generating session also be the primary reviewer — use an independent instance.
- Large multi-file change → per-file passes (depth) + separate cross-file integration pass (breadth).
- Per-finding confidence scores → enables calibrated routing (low confidence → human, high confidence → auto-apply).

---

# DOMAIN 5: Context Management & Reliability (15%)

**5.1 Preserving critical info across long conversations**
- Extract transactional facts (amounts, IDs, dates) into a persistent verbatim "facts" block — don't rely on lossy summaries.
- "Lost in the middle" → place key info near start/end with clear headers, not buried mid-document.
- Trim verbose tool outputs to only relevant fields before they accumulate in context.

**5.2 Escalation & ambiguity resolution**
- Explicit triggers: customer asks for human / policy silent-ambiguous / no progress after N attempts.
- Honor explicit "I want a human" immediately — don't investigate first.
- Sentiment and self-reported confidence = unreliable escalation proxies — use explicit criteria instead.
- Multiple ambiguous record matches → ask for an extra identifier, don't guess.

**5.3 Error propagation in multi-agent systems**
- Subagent failure → return structured context (failure type, attempted action, partial results, alternatives) to coordinator.
- Attempt local recovery for transient errors before escalating.
- Never silently convert failure → fake "success." Never kill the whole workflow for one subagent failure — degrade gracefully + annotate coverage gap.

**5.4 Context management in large codebase exploration**
- Watch for vague "typical pattern" language replacing specific earlier findings = context degradation signal.
- Scratchpad files = persist and re-reference key findings to counter drift.
- Delegate narrow verbose exploration to subagents — keep main context lean.
- Crash recovery → each agent exports state to a manifest; coordinator reloads on resume (avoid redoing work).
- `/compact` → reduce accumulated context while retaining valid findings.

**5.5 Human review & confidence calibration**
- Aggregate accuracy can hide segment-level weak spots (e.g., 97% overall hides 78% on one document type).
- Use stratified sampling — measure accuracy per segment, not just in aggregate.
- Calibrate confidence thresholds against a labeled validation set, not arbitrary cutoffs; per-field, not one-size-fits-all.
- Prioritize human review time on low-confidence + ambiguous/contradictory cases.

**5.6 Provenance & uncertainty in multi-source synthesis**
- Preserve claim-source mapping (source, excerpt) through every summarization/synthesis step — don't discard it.
- Conflicting credible sources → present both + annotate discrepancy (never average, arbitrarily pick one, or omit).
- Include publication/collection dates → avoids misreading legitimate temporal change as contradiction.
- Render content type-appropriately: financial → tables, news → prose, technical → structured lists.

---

# Cross-Cutting Patterns (memorize these — they resolve most "which option is correct" judgment calls)

1. **High-stakes step → hook/gate, not prompt.** Prompts are probabilistic; hooks are deterministic.
2. **Symptom vs. root cause** → trace the failure upstream (coordinator scoping, tool description, review design) — don't patch the visible symptom.
3. **Explicit/structured/scoped > vague/generic/broad** — in criteria, error metadata, and tool access alike.
4. **Independent review > self-review**, always.
5. **Match mechanism to constraint** — Batch vs. real-time, plan mode vs. direct execution, `Grep` vs. `Glob`, `fork_session` vs. fresh `Task`, hooks vs. prompts.

| Domain | Weight |
|---|---|
| 1. Agentic Architecture & Orchestration | 27% |
| 2. Tool Design & MCP Integration | 18% |
| 3. Claude Code Configuration & Workflows | 20% |
| 4. Prompt Engineering & Structured Output | 20% |
| 5. Context Management & Reliability | 15% |
