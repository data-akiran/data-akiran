# Claude Certified Architect – Foundations (CCAF)
## Theory-Only Study Guide (All 30 Task Statements)

This is a theory-focused companion to the full task-by-task study guide. It keeps the concept explanations and the underlying reasoning for every task statement across all five domains, but strips out the sample questions and answer-choice walkthroughs so you can study the *why* behind each pattern without question-format noise.

---

# DOMAIN 1: Agentic Architecture & Orchestration (27%)

## 1.1 — Design and implement agentic loops for autonomous task execution

An agentic loop is the basic control structure behind any tool-using AI system: send a request, inspect the response, act on it, and repeat until the model signals it is actually done. The core mechanic to understand is the `stop_reason` field returned by the API. This field is a *structured, deterministic* signal — it tells you precisely why the model stopped generating, rather than requiring you to infer intent from the content of the text itself.

Two values matter most in everyday loop design:
- `"tool_use"` — the model wants to call one or more tools. Your code should extract each tool call, execute it, feed the result(s) back into the conversation as `tool_result` blocks, and call the API again.
- `"end_turn"` — the model believes its response is complete. This is the authoritative signal to exit the loop and return the final output to the user.

A recurring anti-pattern the exam probes is using *natural-language text matching* as your primary stop signal — for example, scanning the model's output for the word "done" or "complete." This is unreliable because such words can appear incidentally, mid-reasoning, without indicating actual completion. The structural fix is always to rely on `stop_reason`, not text heuristics.

A second important edge case is `stop_reason: "max_tokens"`. This means the response was truncated before the model finished — including, potentially, in the middle of a tool call's JSON arguments. A truncated tool call has malformed or incomplete arguments and must not be executed as-is. The correct handling is to treat this as an *incomplete* turn: increase the token budget and/or resend the request to let the model finish, rather than either discarding the whole conversation or naively executing a broken tool call.

Finally, hardcoded maximum-iteration counts do have a legitimate role, but only as a *secondary safety net* against genuinely runaway loops — never as the primary or sole termination mechanism. The `stop_reason` check remains authoritative; the iteration cap exists purely to prevent worst-case infinite loops from consuming unbounded resources.

## 1.2 — Orchestrate multi-agent systems with coordinator-subagent patterns

Multi-agent systems typically follow a **hub-and-spoke** topology: a central coordinator decomposes a task, dispatches work to specialized subagents, and synthesizes their outputs into a final result. Two design principles recur throughout this task statement.

**Dynamic subagent selection.** A coordinator should evaluate each incoming query and decide *which* subagents are actually relevant to it, rather than reflexively invoking the full available set every time ("always run everything"). Running unnecessary subagents wastes latency and token budget, and — worse — can dilute the final synthesis with irrelevant findings that then have to be filtered back out. The correct pattern is for the coordinator to reason about scope first: does this query involve documents? Does it need live web data? Only invoke the subagents whose specialty actually matches.

**Non-overlapping, sufficiently broad decomposition.** When a coordinator breaks a topic into subtopics for parallel investigation, the decomposition must be broad enough to cover the full scope of the original request. A classic failure mode is narrowing too aggressively — for instance, decomposing "renewable energy adoption barriers" into only cost-related subtopics while missing policy, infrastructure, and public-perception barriers entirely. When every subagent executed its individually assigned task correctly but the aggregate output still misses major dimensions of the original question, the defect is almost always upstream, in the coordinator's initial scoping — not in any individual subagent's execution.

**Strict hub-and-spoke communication.** All inter-agent data flow should route *through* the coordinator. Subagents should never call each other directly, and should never communicate via shared global state that any agent can read or write at will. Routing everything through the coordinator preserves observability (you can see and log every piece of information moving through the system) and ensures consistent, centralized error handling. If the "analysis" subagent needs data the "search" subagent already found, the coordinator receives that output and explicitly passes the relevant portion into the analysis subagent's prompt.

## 1.3 — Configure subagent invocation, context passing, and spawning

This task statement is about the actual mechanics of spawning and feeding subagents.

**The `Task` tool and explicit context passing.** A coordinator can only spawn subagents if `"Task"` is included in its `allowedTools`. Critically, subagents have *zero automatic visibility* into anything the coordinator or their sibling subagents have seen — there is no implicit context inheritance. If a synthesis subagent's output ignores earlier findings and instead hallucinates generic content, the near-universal root cause is that the coordinator failed to explicitly embed those findings into the subagent's prompt, incorrectly assuming the subagent would "just know." The fix is always to explicitly paste prior findings — ideally in a structured format (e.g., JSON with fields like `source_url`, `document_name`, `excerpt`) — into the new subagent's prompt text.

**`AgentDefinition`.** Each subagent is configured via an `AgentDefinition`: a name, a description, a system prompt, and a restricted tool set appropriate to its role.

**Parallel spawning.** To run multiple subagents concurrently and minimize total latency, you emit multiple `Task` calls *within a single coordinator turn* — not across sequential turns, which would serialize the work, and not by merging unrelated subtopics into one combined subagent prompt.

**`fork_session`.** This mechanism branches multiple agents off a single, already-established shared baseline session, so that each branch can pursue a divergent strategy without repeating exploration work already completed. The canonical use case is comparing two different valid approaches (e.g., two refactor strategies) starting from an identical point of prior investigation — as opposed to `Task`, which spawns a subagent with no prior context at all.

## 1.4 — Implement multi-step workflows with enforcement and handoff patterns

This task statement distinguishes **probabilistic enforcement** (prompt instructions) from **deterministic enforcement** (programmatic gates), and covers how to structure information for human handoff.

**Programmatic gates for business-critical steps.** Any step where non-compliance carries real financial, legal, or safety consequences should not rely solely on an instruction like "always verify identity before issuing a refund." Prompt instructions have a non-zero failure rate, especially in edge cases. The reliable fix is a programmatic gate or hook that blocks the downstream tool call (e.g., `process_refund`) unless a verified prerequisite (e.g., a confirmed `customer_id`) already exists in state. This guarantees the ordering deterministically, rather than merely making it statistically likely.

**Structured handoff summaries.** When an interaction escalates from an automated agent to a human, the human agent frequently has *no access* to the underlying conversation transcript. A single raw message, or a full unsummarized transcript dump, is not actionable. The correct payload is a structured, information-dense handoff summary — for example: customer ID, root cause, relevant amounts, and a recommended next action. This is what makes the escalation genuinely usable by the receiving human.

**Multi-concern decomposition.** When a single request raises multiple independent, non-interacting concerns (e.g., a shipping question and a separate billing question), the correct approach is to decompose the request into its distinct items, investigate each one (sharing relevant context across them where useful), and then synthesize a single unified response that addresses both — rather than answering only one, escalating by default, or arbitrarily prioritizing one concern over the other.

## 1.5 — Apply Agent SDK hooks for tool call interception and data normalization

Hooks are code that runs at defined points in the tool-calling lifecycle, and they exist specifically to provide guarantees that prompt instructions cannot.

**`PostToolUse` hooks for normalization.** When multiple backend tools return the same conceptual data (e.g., dates, currency values) in inconsistent formats — Unix timestamps vs. ISO 8601 vs. custom codes; cents-as-integer vs. dollar-strings vs. bare floats — asking the model to "watch out for different formats" via prompt instruction is unreliable and pushes error-prone reasoning onto the model. The correct mechanism is a `PostToolUse` hook that deterministically transforms every tool's raw output into one consistent format *before* the model ever reasons about it. This removes an entire class of reasoning errors caused by format confusion.

**Pre-call interception hooks for compliance.** For business rules that must never be violated under any circumstance (e.g., "refunds over $500 require human approval"), a `PreToolUse`-style interception hook inspects outgoing tool calls, blocks any that violate the rule, and redirects execution to an alternative workflow (such as an escalation tool). This is the deterministic counterpart to a prompt instruction forbidding the same behavior — the hook guarantees compliance, while the prompt instruction only makes compliance likely.

**When to still use prompts.** Hooks are reserved for genuine guarantees — compliance rules and business-critical enforcement. Softer, style-level or preference-level guidance (e.g., tone) that doesn't carry hard consequences if occasionally not followed remains appropriately handled via prompt instructions. Hooks are not meant to replace all prompt instructions — only the subset where a probabilistic outcome is unacceptable.

## 1.6 — Design task decomposition strategies for complex workflows

Two decomposition strategies suit two different kinds of tasks.

**Prompt chaining** (fixed, sequential pipeline) fits tasks that are predictable and repeatable — for example, a fixed review pipeline that always runs a security-scan pass, then a style-lint pass, then a test-coverage pass, in that order, for every pull request. The signature of a good prompt-chaining use case is that the sequence of steps is known in advance and doesn't need to adapt based on what's discovered along the way.

**Dynamic (adaptive) decomposition** fits open-ended, exploratory tasks where the right next step depends on what's found during earlier steps — for example, "figure out why memory usage is climbing in production" or "investigate why conversion dropped 15% last month." For these, the plan should be generated *iteratively*, with each discovery informing what to investigate next, rather than being fixed upfront before any exploration has happened.

**Avoiding attention dilution in large multi-file work.** A single review pass across many files at once (e.g., a 20-file pull request) tends to produce inconsistent depth — deep analysis on some files, superficial comments on others — and can even produce contradictory findings for identical patterns appearing in different files. The fix is to restructure into per-file local passes (for depth) plus one separate cross-file integration pass (for breadth/consistency), rather than trying to do both within a single undifferentiated pass.

## 1.7 — Manage session state, resumption, and forking

This task statement covers three related mechanisms for managing long-running or paused work.

**`--resume <session-name>`.** Continues a previously paused, named session, preserving its accumulated context. This is efficient when most of the prior context remains valid. However, if files or other underlying state have changed since the session was last active, the agent will not automatically detect this — you must explicitly inform the resumed session which specific files or facts changed, so it targets re-analysis at just those items rather than either assuming stale findings are still valid or blindly re-exploring everything.

**`fork_session`.** Used when you want to branch off a shared, already-explored baseline into two or more independent, divergent paths — for example, comparing two different testing or refactor strategies without repeating the exploration work that's common to both. Each fork proceeds independently from that shared starting point.

**Starting fresh with an injected summary.** When enough time has passed, or enough underlying state has changed, that most of a prior session's tool results are now stale or actively misleading (e.g., many files rewritten, dependencies upgraded), resuming and dragging along outdated context is worse than starting a new session seeded with a curated, structured summary of what's still valid. This avoids both the cost of full re-exploration and the risk of reasoning from invalidated assumptions.

---

# DOMAIN 2: Tool Design & MCP Integration (18%)

## 2.1 — Design effective tool interfaces with clear descriptions and boundaries

The model's tool descriptions are the *primary* mechanism by which it decides which tool to use for a given request — there is no other signal it relies on more heavily for routing. This makes description quality a first-order design concern, not an afterthought.

**Near-duplicate descriptions are the most common cause of tool misrouting.** If two tools (e.g., `analyze_content` and `analyze_document`) have nearly identical one-line descriptions, the model will frequently pick the wrong one. The fix is to write descriptions that clearly state: the tool's purpose, expected inputs/formats, example queries it should handle, relevant edge cases, and — critically — explicit "use this vs. that other tool when..." disambiguation guidance. Renaming a tool to be more specific (e.g., `analyze_content` → `extract_web_results`, scoped explicitly to live web pages via URL) can eliminate ambiguity that a description tweak alone might not fully resolve.

**Splitting overly generic tools.** A tool with a broad, vague purpose (e.g., a catch-all `analyze_document`) is a common source of routing confusion. Splitting it into purpose-specific tools with clear, narrow input/output contracts (e.g., `extract_data_points`, `summarize_content`, `verify_claim_against_source`) makes each tool's applicability unambiguous.

**System prompt sensitivity.** Because tool selection can be influenced by keyword-heavy language elsewhere in the system prompt, it's worth reviewing your system prompt for instructions that might unintentionally bias tool selection in ways you didn't intend.

## 2.2 — Implement structured error responses for MCP tools

Generic error strings like `{"error": "Operation failed"}` give an agent no way to reason about *how* to respond to a failure. Effective MCP tool design requires structured error metadata.

**Error categorization.** Every failure mode should be classified into a category — commonly: transient (e.g., a network timeout), validation (malformed input), business/policy (a rule violation, like a refund exceeding the allowed amount), or permission (an access failure). Alongside the category, the response should include an explicit `isRetryable` boolean and a human-readable message. Without this distinction, an agent might uselessly retry a policy-violation error that will never succeed no matter how many times it's attempted, or fail to retry a genuinely transient failure that would likely succeed on a second attempt.

**Distinguishing failure from valid emptiness.** A subtle but important anti-pattern: a tool that returns an empty result (e.g., `[]`) both when a query genuinely finds nothing *and* when the underlying system call itself fails (e.g., a database connection error) conflates two fundamentally different situations. The agent cannot tell "the query succeeded and found nothing" from "the query failed to execute" — which could lead it to confidently report an incorrect conclusion (e.g., telling a customer they have no orders, when the real issue was a system failure). These cases need distinct, explicit representations, typically via an `isError` flag.

**Local recovery before propagation.** When a subagent's tool call fails with a transient error, the subagent should attempt local recovery (e.g., a quick retry) itself before escalating anything to the coordinator. Only errors that genuinely cannot be resolved locally should propagate upward — and when they do, they should include partial results and a record of what was attempted, not just a bare failure notice.

## 2.3 — Distribute tools appropriately across agents and configure tool choice

**Scoped tool access.** Giving every subagent access to the system's entire tool set "just in case" tends to produce misuse — for example, a synthesis subagent with access to web-search tools may attempt redundant searches instead of focusing on its actual synthesis role. The structural fix is to restrict each subagent's tool access to what its specific role actually requires, adding at most one narrow, purpose-built tool for a specific high-frequency cross-role need (rather than granting the whole neighboring agent's toolkit). A prompt-level warning telling the model "don't use search tools" is a weaker, probabilistic substitute for this structural restriction.

**`tool_choice` modes.** The API supports several tool-choice configurations:
- `{"type": "auto"}` — the default; the model decides freely whether to call a tool and which one.
- `{"type": "any"}` — guarantees that *some* tool call happens on this turn (as opposed to a free-text conversational response), without constraining which tool is chosen. This fits scenarios like a mandatory classification/routing step that must always dispatch to one of several handler tools.
- `{"type": "tool", "name": "..."}` — forces a *specific* named tool to be called. This fits scenarios where a fixed step must run first, every time, with no exceptions (e.g., `extract_metadata` must always run before enrichment steps). Typically this forced setting is used only for that first required turn, with subsequent turns reverting to normal `tool_choice` behavior for the remaining flexible steps.

## 2.4 — Integrate MCP servers into Claude Code and agent workflows

**Configuration scoping.** MCP servers can be configured at two different scopes:
- `.mcp.json` at the project root — version-controlled and automatically shared with the whole team. This is the correct location for any server the whole team needs (e.g., a shared Postgres server), with credentials referenced via environment variable expansion (e.g., `${DB_PASSWORD}`) rather than hardcoded into the file, keeping secrets out of the repository.
- `~/.claude.json` — user-scoped, personal, and *not* shared with teammates. Appropriate for personal or experimental servers only.

**Tool-selection competition.** If Claude Code keeps favoring a built-in tool (e.g., `Grep`) over a more capable custom MCP tool (e.g., a semantic code search server) even when the MCP tool would give better results, the first thing to check — consistent with the general tool-description principle from 2.1 — is whether the MCP tool's description clearly communicates its purpose and advantages. Improving the description is the direct fix; removing the competing built-in tool entirely is a more invasive and generally unnecessary workaround.

**MCP resources vs. tools.** For large, mostly-static, browsable content that agents frequently need to reference — such as a catalog of internal API schemas — the appropriate MCP primitive is a **resource**, not a tool. Tools represent actions or queries to be actively invoked; resources represent static or browsable content that doesn't require an exploratory tool call each time it's needed.

## 2.5 — Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively

Each built-in tool has a distinct purpose, and choosing the wrong one for the task is a common inefficiency.

- **`Grep`** searches file *contents* — use it to find every place a specific string or pattern appears inside files (e.g., a deprecated function call, an error string, an import).
- **`Glob`** finds files by *name/path pattern* — use it when you need to locate files based on their filename or location (e.g., every file matching `**/*.test.tsx`), regardless of what's inside them.
- **`Read`/`Write`** operate on whole files, while **`Edit`** is designed for small, targeted, uniquely-anchored changes. `Edit` requires its anchor text to match a unique location in the file; when the same text appears multiple times with different surrounding context, `Edit` will fail on ambiguity. The documented fallback in that case is to `Read` the full file, apply the correct change programmatically or manually to the correct occurrence, and `Write` the full corrected file back.
- **Incremental exploration.** For understanding an unfamiliar, large codebase, the recommended approach is not to read every file upfront (which wastes context on mostly-irrelevant content), but to build understanding incrementally: use `Grep` to locate likely entry points, then use `Read` selectively to follow imports and trace the relevant flow as it's discovered.

---

# DOMAIN 3: Claude Code Configuration & Workflows (20%)

## 3.1 — Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization

`CLAUDE.md` files exist at multiple levels, and understanding the hierarchy is essential for diagnosing "it works on my machine" problems.

**User vs. project scope.** `~/.claude/CLAUDE.md` is personal and never shared via version control — anything placed there is invisible to teammates. Project-level configuration (root `CLAUDE.md`, or `.claude/CLAUDE.md`) is version-controlled and automatically shared with the whole team. A classic diagnostic pattern: a new team member's session doesn't follow established conventions even though "the conventions clearly exist somewhere" — this almost always means those conventions were placed in a senior engineer's personal user-level file rather than the shared project-level one.

**`@import` for modular organization.** In a monorepo or multi-package project, each package can have its own `CLAUDE.md` that uses `@import` to pull in the shared root conventions, plus its own package-specific additions — avoiding both the duplication of copy-pasting the root file into every package and the over-centralization of cramming everything into one giant root file.

**`.claude/rules/` for large or sprawling configuration.** When a single `CLAUDE.md` grows unwieldy, splitting it by topic into separate files under `.claude/rules/` (e.g., `testing.md`, `api-conventions.md`, `deployment.md`) keeps configuration organized and maintainable.

**`/memory` for debugging.** When you suspect a session isn't picking up a rule you expect, the `/memory` command inspects which memory files (the full `CLAUDE.md` hierarchy, imports, and rules) are actually loaded and in effect for that specific session — the direct tool for diagnosing "why isn't this convention applying."

## 3.2 — Create and configure custom slash commands and skills

**Command scoping.** Like `CLAUDE.md`, custom slash commands have two locations: `.claude/commands/` (project-level, version-controlled, automatically shared with the whole team after cloning — no per-developer setup needed) and `~/.claude/commands/` (personal-only).

**Skill frontmatter fields:**
- `context: fork` — isolates a skill's execution in a separate sub-agent context, so that skills producing verbose or exploratory output (e.g., a multi-step codebase audit that would otherwise flood the main conversation with dozens of intermediate findings) don't pollute the main session. Only the skill's final output returns to the main context.
- `allowed-tools` — restricts exactly which tools a skill or command is permitted to use. This is the correct mechanism for constraining a destructive command (e.g., a `/deploy` command) to only a fixed, vetted set of operations, preventing it from having broader tool access than its task actually requires.
- `argument-hint` — prompts for required parameters when a skill is invoked without arguments.

**Skills vs. `CLAUDE.md`.** Skills are appropriate for on-demand, task-specific workflows invoked when needed. `CLAUDE.md` is appropriate for universal standards that should be loaded for every session regardless of the specific task at hand.

## 3.3 — Apply path-specific rules for conditional convention loading

`.claude/rules/` files can carry YAML frontmatter with a `paths` field specifying glob patterns. A rule scoped this way loads — and only adds token overhead — when a file matching its pattern is actually being edited, rather than being loaded in full for every single session regardless of relevance.

This mechanism is specifically valuable for conventions tied to a *file type/pattern* rather than to a *directory location*. For example, test files (e.g., `Button.test.tsx`) often live scattered throughout a codebase, next to their corresponding source files, rather than confined to one directory. A directory-scoped `CLAUDE.md` cannot cleanly target such scattered files. A `.claude/rules/testing.md` with `paths: ["**/*.test.tsx", "**/*.test.ts"]` applies uniformly regardless of location, and only when relevant. This is the general pattern to reach for whenever a convention doesn't map cleanly onto the directory tree — e.g., "always use the internal `Logger` utility, never `console.log`," applied to every `.ts`/`.tsx` file across an entire monorepo.

## 3.4 — Determine when to use plan mode vs direct execution

**Direct execution** is appropriate for simple, well-scoped, single-file changes with a clear specification — for example, fixing a null pointer based on a specific stack trace. There is nothing meaningful to plan; planning here would be over-engineering.

**Plan mode** is appropriate when a task involves architectural decisions, spans many files, or has multiple genuinely valid approaches — for example, restructuring a monolith into microservices, or migrating state-management libraries across dozens of files. In plan mode, Claude explores the problem space first, proposes an approach, and only executes after that plan has been reviewed and approved (or adjusted).

For multi-phase work, it's common to use plan mode for the investigation/design phase and then switch to direct execution once a concrete plan has been agreed upon.

**The Explore subagent.** During verbose discovery — for instance, mapping the structure of a large, unfamiliar codebase before proposing a plan — delegating that discovery work to the Explore subagent keeps the raw exploration noise out of the main session's context. Only summarized findings return to the main agent, preserving its context budget for the actual planning and execution work.

## 3.5 — Apply iterative refinement techniques for progressive improvement

**Concrete examples over more prose.** When detailed prose instructions still produce inconsistent output (e.g., a "normalize phone numbers" instruction handling edge cases unpredictably), the most effective next step is usually not to write even more detailed prose, but to supply 2–3 concrete input→output examples. Concrete examples resolve ambiguity that prose, however thorough, tends to leave open to interpretation.

**Test-driven iteration.** For implementation tasks, writing the test suite first — capturing expected behavior, edge cases, and performance requirements — and then iterating by feeding back test failures gives the model a precise, checkable target rather than a purely descriptive one.

**The "interview pattern."** In genuinely unfamiliar domains where real ambiguity exists (e.g., how a specific team wants cache invalidation handled), it's more effective to have Claude ask clarifying questions *before* implementing anything, rather than guessing at an industry-standard default and risking costly rework later.

**Batching interacting vs. independent fixes.** When multiple issues genuinely interact with each other, describing them together in one detailed message lets the model reason about them jointly. When issues are independent of one another (e.g., a security fix in one file and an unrelated typo two files away), they should be addressed as separate, sequential requests — batching unrelated issues together offers no benefit and risks conflating unrelated context.

## 3.6 — Integrate Claude Code into CI/CD pipelines

**Non-interactive mode.** Automated pipeline contexts must run Claude Code with the `-p`/`--print` flag to enable non-interactive, scriptable execution. Without it, a CI job invoking Claude Code will hang, waiting for interactive input that will never arrive.

**Structured, machine-parseable output.** For CI steps that need to programmatically parse Claude's findings (e.g., to post inline PR comments), `--output-format json` combined with `--json-schema` produces schema-validated, structured JSON — a reliable alternative to writing a fragile regex parser over free-text output.

**`CLAUDE.md` as CI context.** Documenting testing standards, fixture conventions, and review criteria in `CLAUDE.md` ensures CI-invoked runs operate with the same context a human reviewer would have, rather than reviewing "blind."

**Independent review over self-review.** A Claude Code session that generated a piece of code and is then also asked to review that same code tends to be a weak reviewer of its own work — it retains its generation-time reasoning, making it structurally less likely to question or flag its own decisions. The documented fix is to use a second, genuinely independent Claude instance — with no memory of *why* the original code was written that way — to perform the review. This independent-instance pattern recurs throughout the exam wherever self-review is discussed.

---

# DOMAIN 4: Prompt Engineering & Structured Output (20%)

## 4.1 — Design prompts with explicit criteria to improve precision and reduce false positives

Vague, confidence-based qualifiers — "only report high-confidence issues," "be conservative" — do not reliably improve precision, because "confidence" is not a checkable criterion; different runs (or different contexts within the same run) can interpret it inconsistently. The reliable fix is to replace such qualifiers with concrete, categorical, checkable rules that explicitly state what should be reported and what should be skipped (e.g., "flag a finding only if X, Y, or Z is true; do not flag style or naming deviations").

**Protecting trust through selective disabling.** If, after tightening criteria, one specific category still has a disproportionately high false-positive rate and is damaging overall trust in the system, the recommended interim step is to temporarily disable reporting for that specific category while improving its criteria — keeping the well-performing categories active rather than either removing the whole system or further loosening the confidence bar for the problem category.

**Consistency via anchored examples.** Concrete code examples illustrating each severity or classification level (alongside the categorical criteria themselves) make classification decisions checkable and consistent across many separate invocations, in the same way examples generally resolve ambiguity elsewhere in prompt design.

## 4.2 — Apply few-shot prompting to improve output consistency and quality

Few-shot examples are most valuable where detailed prose instructions alone still leave the model inconsistent — particularly on ambiguous or edge cases, rather than the typical/unambiguous cases the model likely already handles well. A small number of well-targeted examples (2–4) focused specifically on the difficult cases tends to outperform a much larger number of examples covering only the easy, typical case.

**Including reasoning, not just input→output.** Each few-shot example should ideally include the *reasoning* behind the correct answer, not merely the raw mapping from input to output. Reasoning-included examples teach the underlying judgment, which generalizes to novel, unseen cases — whereas bare input→output pairs risk the model simply pattern-matching to the literal examples given, without transferring the logic behind them.

**Structural variety for extraction tasks.** When an extraction system handles one document structure well (e.g., tables) but fails on another (e.g., narrative prose with embedded figures), producing null or hallucinated fields, the fix is to add few-shot examples covering that specific structural variety the model is failing on — directly teaching the pattern it's currently missing.

## 4.3 — Enforce structured output using tool use and JSON schemas

Defining your target output shape as a tool's `input_schema`, and extracting the result from the response's `tool_use` block, is the reliable mechanism for guaranteeing *syntactically* valid structured output — the JSON will always conform to the declared schema shape.

**Syntax compliance is not semantic correctness.** This is the central distinction this task statement tests. A schema-enforced extraction can be syntactically perfect (all required fields present, correct types) while still being wrong in substance — for example, line items that don't actually sum to the stated invoice total. Schema enforcement via `tool_use` eliminates an entire category of *syntax* errors, but a separate validation step is still required to catch *semantic* errors.

**Schema design for genuine absence.** Fields should be made nullable/optional whenever the source data may genuinely lack that information (e.g., a discount that doesn't apply to every invoice). Marking such a field strictly `required` when the underlying information is sometimes genuinely absent invites the model to fabricate a plausible-but-incorrect value simply to satisfy the schema constraint — because it has no valid way to represent "this information isn't in the source."

**`enum` + "other" pattern.** For categorical fields that need to stay extensible (e.g., `document_type`, `payment_method`), pairing a fixed `enum` of known values with an `"other"` option plus a free-text detail field keeps the schema both constrained (useful for downstream logic) and flexible enough to represent genuinely novel cases without forcing a bad fit.

## 4.4 — Implement validation, retry, and feedback loops for extraction quality

**Retry with specific error feedback.** When an extraction fails validation, the correct retry strategy is to send a follow-up request that includes the original source document, the failed extraction, and the *specific* validation error message — letting the model self-correct with concrete, targeted feedback, rather than simply asking it to try again blindly.

**Recognizing when retries can't help.** A crucial distinction is between *structural/format* failures, which are retry-fixable (e.g., a date returned in the wrong format), and failures caused by information that genuinely does not appear anywhere in the source document, which are *not* retry-fixable. No number of retries will produce a correct value for information that was never present in the source — continuing to retry in that case is wasted effort. The correct handling is to resolve the field to `null`/unavailable instead.

**Structured fields for downstream analysis.** Adding fields like `detected_pattern` to structured findings — rather than relying only on raw logs or free-text notes — enables systematic downstream analysis of which document or code patterns most often correlate with false positives or dismissed findings. Similarly, extracting both a `calculated_total` and a `stated_total` (and flagging discrepancies) supports numeric consistency checking, and `conflict_detected` booleans help surface inconsistent source data explicitly.

## 4.5 — Design efficient batch processing strategies

**Matching API choice to latency tolerance.** The core tradeoff is cost versus latency. The Message Batches API offers substantial cost savings (roughly 50%) but has no latency guarantee — results may take up to 24 hours. This makes it well-suited to latency-tolerant, high-volume workloads (e.g., an overnight or weekly report nobody is actively waiting on), but fundamentally unsuitable for blocking workflows where a developer or user is waiting for an immediate answer (e.g., a pre-merge CI check) — regardless of how attractive the cost savings look on paper.

**`custom_id` correlation.** Each request in a batch carries a `custom_id`, which is what allows you to match responses back to their originating requests. When a batch partially fails, this correlation lets you resubmit *only* the specific failed items (identified by their `custom_id`s) after fixing the underlying issue, rather than either discarding and resubmitting the entire batch or ignoring the failures outright.

**Testing before committing to scale.** Before submitting a very large batch (e.g., tens of thousands of requests), testing the prompt against a small sample first catches systemic issues early, avoiding a costly full-scale resubmission cycle. It's also worth remembering that the Batch API does not support multi-turn tool calling within a single request — a structural limitation to account for when designing batch workloads.

## 4.6 — Design multi-instance and multi-pass review architectures

**Independent review over self-review** (restated and reinforced from 3.6). A session that generated a piece of code retains its generation-time reasoning, which makes it structurally biased against flagging problems with its own decisions — it tends to rubber-stamp its own work even under a stronger review prompt. The architectural fix is a second, genuinely independent Claude instance with no memory of the original generation reasoning, reviewing the output fresh.

**Multi-pass review for large changes.** A single review pass across many files at once tends to catch surface-level, per-file issues but misses cross-file inconsistencies — for example, two files handling the same edge case differently. The fix is the same per-file-plus-integration pattern seen in task 1.6: per-file local passes for depth, plus a separate cross-file integration pass specifically looking for inconsistencies *between* files.

**Confidence-calibrated routing.** Having the independent review instance produce a self-reported confidence score per individual finding (not a single aggregate score for the whole review) enables calibrated routing — low-confidence findings can be sent to a human reviewer while high-confidence findings are auto-applied, rather than an all-or-nothing approach that either wastes reviewer time on everything or risks auto-applying uncertain findings.

---

# DOMAIN 5: Context Management & Reliability (15%)

## 5.1 — Manage conversation context to preserve critical information across long interactions

**The risk of progressive summarization.** As a long conversation gets repeatedly compressed into shorter summaries, precise transactional details — exact amounts, order numbers, dates — are exactly the kind of information at risk of being blurred or dropped (e.g., "customer requested a refund of $247.83 for order #A19273" degrading over several rounds of summarization into "customer wants a refund"). The fix is to extract such facts into a separate, persistent "facts" block that is included *verbatim* in every subsequent prompt, entirely outside the lossy summarized narrative — rather than trusting that the exact values will survive repeated compression.

**"Lost in the middle."** This is the documented term for the phenomenon where a model tends to underweight information placed in the middle of a long aggregated document relative to information near the beginning or end. The mitigation is structural: place key findings near the start and/or end of the content, with clear section headers, rather than burying them mid-document.

**Trimming verbose tool outputs.** A tool result with many fields (e.g., a 40-field order lookup) should be trimmed down to only the fields actually relevant to the current task *before* it accumulates in the conversation history — rather than appending the full raw result on every turn, which bloats context with irrelevant data.

**Metadata in subagent outputs.** Requiring subagents to include metadata (dates, sources, methodology) directly within their structured outputs supports accurate downstream synthesis, particularly for downstream agents operating with limited context budgets that can't afford to re-derive this information from scratch.

## 5.2 — Design effective escalation and ambiguity resolution patterns

**Explicit escalation triggers.** Rather than relying on a vague notion of "complexity," escalation logic should be built on explicit, checkable triggers: the customer explicitly asks for a human; company policy is silent or ambiguous on the specific request; or the agent has attempted resolution multiple times without making progress. Cases that are standard and clearly covered by existing policy should generally be resolved autonomously — including cases where the customer sounds frustrated, in which case the agent should acknowledge the frustration and still offer resolution, escalating only if the customer reiterates a preference for a human.

**Honoring explicit requests immediately.** When a customer explicitly states a preference to speak with a human, that request should be honored right away, without first requiring an investigation attempt — investigating first would run counter to the customer's clearly stated preference.

**Why sentiment and self-confidence are unreliable escalation proxies.** Using detected negative sentiment as an automatic escalation trigger, or using the model's own self-reported confidence score as a threshold for autonomous resolution, are both documented anti-patterns. Neither signal reliably correlates with actual case complexity — a simple case can produce a frustrated-sounding message, and a genuinely complex policy-exception case can be handled by the model with high (but misplaced) self-reported confidence. Explicit, criteria-based logic is the more reliable substitute for both.

**Handling multiple ambiguous matches.** When a lookup (e.g., searching by name) returns several plausible matching records, the correct response is to ask the customer for an additional identifying detail (order number, email, zip code) rather than guessing via a heuristic (most recent record, most complete record) — guessing risks acting on the wrong account entirely.

## 5.3 — Implement error propagation strategies across multi-agent systems

**Structured failure context.** When a subagent fails, it should return structured context to the coordinator — failure type, what was attempted, any partial results obtained, and possible alternatives — rather than a bare generic status string. This structured information is what allows the coordinator to make an appropriately calibrated recovery decision.

**Distinguishing execution failure from valid emptiness** (echoing 2.2). "The query failed to execute" and "the query executed successfully and found nothing" require different coordinator responses and must be represented distinctly.

**Local recovery before escalation.** A subagent facing a transient failure (e.g., a brief network blip) should attempt local recovery — such as an immediate retry — itself, before involving the coordinator at all. Escalating every transient hiccup up the chain adds unnecessary coordination overhead; only genuinely unresolved failures should propagate.

**Avoiding the "swallow" and "kill everything" anti-patterns.** Two failure modes to avoid: silently converting a failure into an apparent success (e.g., returning an empty result marked as "success," hiding the fact that something actually went wrong), and terminating the entire multi-agent workflow because a single subagent failed. The correct pattern is graceful degradation — proceed with the subagents that succeeded, and annotate the final output with an explicit coverage gap describing what the failed subagent was unable to contribute, rather than either hiding the gap or discarding all the successful work alongside it.

## 5.4 — Manage context effectively in large codebase exploration

**Recognizing context degradation.** In long, hours-long investigation sessions, a telling sign that context quality is degrading is when the model starts referencing "typical patterns" in vague, generic terms instead of the specific classes, functions, or files it identified and analyzed earlier in the same session. This drift signals that intervention is needed.

**Scratchpad files.** Maintaining a scratchpad file that records key findings as they accumulate — and having the agent explicitly reference that file on later questions rather than relying on its own degrading working memory — is the documented countermeasure to this drift.

**Subagent delegation for verbose exploration.** For narrow, verbose exploration sub-tasks within a larger multi-phase investigation (e.g., "find all test files"), delegating to subagents keeps that raw discovery output out of the main agent's context entirely; only a summary returns, and the main agent stays focused on high-level coordination.

**Crash-recovery manifests.** In long-running, multi-agent workflows that may crash partway through (e.g., due to infrastructure issues), having each agent export its state/results to a known location — a manifest — that the coordinator can load and re-inject upon resume prevents already-completed work from being wastefully redone from scratch after a restart.

**`/compact`.** When a session's context window fills up with verbose intermediate output but the key findings so far remain valid and needed, `/compact` reduces accumulated context while retaining what's necessary — a middle path between discarding everything via a full restart and leaving the bloated context to accumulate indefinitely.

## 5.5 — Design human review workflows and confidence calibration

**Aggregate accuracy can mask segment-level problems.** A single overall accuracy figure (e.g., "97% accurate") can look reassuring while hiding much lower performance on a specific segment — for example, an extraction system might perform excellently on digital invoices but poorly on hand-scanned ones, a gap the aggregate number completely obscures. Before making any decision based on an accuracy figure (such as reducing or eliminating human review), that figure should be broken down and validated per segment.

**Stratified sampling.** Measuring accuracy separately across meaningful segments (document type, field, source type, etc.) via stratified random sampling — rather than relying on one pooled aggregate number — is the correct methodology for surfacing these hidden weak spots before they cause downstream harm.

**Calibrated confidence thresholds.** When a model outputs field-level confidence scores, the threshold used to decide "send to human review" should be calibrated against a labeled validation set, so the threshold reflects observed accuracy at each confidence level — not chosen arbitrarily (e.g., "80% sounds reasonable") and not applied uniformly across all fields regardless of their individual typical difficulty.

**Prioritizing limited reviewer time.** With finite human review capacity, the highest-value use of that time is on low-confidence extractions and ambiguous or internally contradictory source documents — these are the cases statistically most likely to contain actual errors, as opposed to a random sample or, worse, focusing review effort on the cases the model is already most confident about.

## 5.6 — Preserve information provenance and handle uncertainty in multi-source synthesis

**Preserving claim-source mapping through synthesis.** When multiple subagents each produce findings, their structured outputs should include claim-source mappings (source URL/name, excerpt) alongside every finding — and this mapping must be explicitly carried forward, not discarded, as findings pass through summarization and synthesis steps. If a final report no longer indicates which source or subagent a given claim came from, the synthesis step failed to preserve attribution data it should have carried forward.

**Handling conflicting statistics via annotation, not resolution.** When two credible sources report genuinely different values for the same metric, the correct synthesis behavior is to present both values with explicit source attribution, annotating the discrepancy as an open point — rather than averaging the values, arbitrarily picking one source's figure and discarding the other, or omitting the statistic entirely to sidestep the conflict. All of those alternatives lose information the reader should actually have.

**Temporal metadata prevents false contradictions.** When two sources' data was collected at different times and the underlying metric is known to fluctuate (e.g., seasonally), a difference between the two values may reflect genuine change over time rather than a true contradiction. Requiring publication/collection dates in structured outputs, and surfacing them in the final synthesis, lets the reader distinguish a legitimate temporal difference from an actual same-period conflict — rather than the two being misread as contradictory data and resolved (incorrectly) by picking whichever source seems more credible.

**Content-appropriate rendering.** Different content types should be rendered in the format that suits them — financial data as tables, news as prose, technical findings as structured lists — rather than flattening every kind of content into one uniform presentation style.

---

# Quick-Reference: Domain Weights

| Domain | Weight | Task Statements |
|---|---|---|
| 1. Agentic Architecture & Orchestration | 27% | 1.1–1.7 (7) |
| 2. Tool Design & MCP Integration | 18% | 2.1–2.5 (5) |
| 3. Claude Code Configuration & Workflows | 20% | 3.1–3.6 (6) |
| 4. Prompt Engineering & Structured Output | 20% | 4.1–4.6 (6) |
| 5. Context Management & Reliability | 15% | 5.1–5.6 (6) |

## Recurring Themes Across the Exam

Several conceptual threads reappear across nearly every domain, and are worth internalizing as general principles rather than memorizing per task statement:

**Programmatic enforcement beats prompt-based enforcement whenever failure has real consequences.** Wherever the stakes are financial, legal, or safety-critical (refund gates, compliance rules, forced tool ordering), a deterministic hook or gate is the correct mechanism — prompt instructions, however strongly worded, remain inherently probabilistic and are reserved for softer, style-level guidance.

**Root-cause diagnosis over symptom patching.** Many scenarios present a downstream symptom (an incomplete report, a misrouted tool call, missed cross-file issues) that traces back to an upstream cause (coordinator scoping, tool description quality, single-pass review design). The correct fix addresses the upstream cause rather than patching around the visible symptom.

**Explicit, structured, and scoped beats generic.** This shows up repeatedly: explicit categorical criteria over vague confidence language; structured error metadata over generic error strings; scoped, role-appropriate tool access over granting an agent "everything, just in case."

**Independent review beats self-review.** A model reviewing its own generated output retains generation-time reasoning that biases it against catching its own mistakes — a second, independent instance is structurally better suited to genuine review.

**Match the mechanism to the constraint.** Batch API vs. real-time API, plan mode vs. direct execution, hooks vs. prompts, `Grep` vs. `Glob`, `fork_session` vs. fresh `Task` spawn — a large share of the exam's judgment calls come down to correctly matching an available mechanism to the specific constraint of the situation at hand, rather than defaulting to the same tool for every case.
