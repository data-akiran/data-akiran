# Claude Certified Architect – Foundations (CCAF)
## Task-by-Task Study Guide (All 30 Task Statements)

This guide walks through every task statement in the official Exam Guide (v1.0, July 2026), domain by domain. For each task statement you get: **what it tests**, a **worked example**, **step-by-step approach**, **sample code**, and **three practice questions** with explanations.

> **How to use this guide:** Read the worked example and steps first, study the sample code, then attempt each sample question *before* reading the explanation. Cover the answer with your hand/scroll position if you want a real test.

---

# DOMAIN 1: Agentic Architecture & Orchestration (27%)

## Task Statement 1.1 — Design and implement agentic loops for autonomous task execution

**What it tests:** Whether you understand the core agentic loop mechanics — sending a request, checking `stop_reason`, executing tools, feeding results back in — and can avoid termination anti-patterns.

**Worked example:** You build a research assistant. Each turn, you call the API, check the response's `stop_reason`. If it's `"tool_use"`, you execute the requested tool(s), append the tool result(s) to the conversation as a `tool_result` message, and call the API again. If it's `"end_turn"`, the loop stops and you return the final text to the user.

**Steps:**
1. Send the initial request with your tools defined.
2. Inspect `stop_reason` in the response.
3. If `"tool_use"`: extract the tool call(s), execute them, append results to conversation history, loop back to step 1.
4. If `"end_turn"`: exit the loop and surface the final response.
5. Never use natural-language text-matching (e.g., searching for the word "done") or a hardcoded max-iteration count as your *primary* stop signal — `stop_reason` is the authoritative signal.

**Sample Code:**
```python
import anthropic

client = anthropic.Anthropic()
messages = [{"role": "user", "content": "Research the top 3 renewable energy trends."}]

while True:
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=[web_search_tool],
        messages=messages,
    )
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        messages.append({"role": "user", "content": tool_results})
        continue  # loop back to call the API again

    if response.stop_reason == "end_turn":
        break  # authoritative signal to stop — not a text-matching heuristic
```

**Sample Question 1:**
Your team implemented an agentic loop that stops when the assistant's response text contains the word "complete." In production, the agent sometimes stops prematurely because it mentions "complete" mid-reasoning, and sometimes runs extra unnecessary turns. What is the correct fix?

- **A.** Switch the termination check to inspect `stop_reason`, continuing on `"tool_use"` and stopping on `"end_turn"`.
- **B.** Tighten the text-matching regex to require "task complete" as an exact phrase.
- **C.** Add a hard cap of 5 iterations regardless of loop state.
- **D.** Ask the model to always end its final message with a special token and match on that.

**Correct: A.** `stop_reason` is a structured, reliable signal set by the API — not a text pattern that can appear incidentally in reasoning. Options B and D are still text-matching anti-patterns; C treats a symptom (runaway loops) rather than the cause (wrong termination signal).

**Sample Question 2:**
A response comes back with `stop_reason: "max_tokens"` after the model was mid-way through a tool call's JSON arguments. What should your loop do?

- **A.** Treat it the same as `"end_turn"` and return the partial output to the user.
- **B.** Treat it as an incomplete turn — increase `max_tokens` and/or resend to let the model finish, since the tool call itself may be truncated and unusable.
- **C.** Treat it as `"tool_use"` and execute the tool call anyway with whatever partial arguments were captured.
- **D.** Discard the entire conversation and restart from the first user message.

**Correct: B.** `max_tokens` means the response was cut off before completion — a truncated tool call has malformed/partial arguments and should not be executed as-is; the correct move is to allow more room and retry, not silently treat it as done or run a broken call.

**Sample Question 3:**
Which of the following is the *safest* role for a hardcoded maximum iteration count in an agentic loop?

- **A.** The primary and only termination signal, replacing `stop_reason` checks entirely.
- **B.** A secondary safety net that stops runaway loops, used alongside — never instead of — the `stop_reason` check.
- **C.** A signal fed back into the prompt asking the model to "wrap up now."
- **D.** Irrelevant — iteration caps should never be used in production agentic loops.

**Correct: B.** Iteration caps are a reasonable *backstop* against genuinely runaway loops, but `stop_reason` remains the authoritative, primary signal for normal termination.

---

## Task Statement 1.2 — Orchestrate multi-agent systems with coordinator-subagent patterns

**What it tests:** Hub-and-spoke design, isolated subagent context, dynamic subagent selection, and avoiding overly narrow task decomposition.

**Worked example:** In a research pipeline, the coordinator receives "research the impact of remote work on urban commercial real estate." Rather than always invoking all four subagents (search, analysis, synthesis, report), it evaluates the query and decides that document analysis isn't needed (no documents provided), so it only invokes search and synthesis.

**Steps:**
1. Coordinator parses the query and identifies the scope/breadth needed.
2. Coordinator decides which subagents are relevant (not "always run the full pipeline").
3. Coordinator decomposes the topic into distinct, non-overlapping subtopics — broad enough to cover the full topic (avoid the "visual arts only" narrowing trap).
4. All subagent-to-subagent communication routes through the coordinator (no direct subagent-to-subagent calls) for observability and consistent error handling.
5. Coordinator evaluates synthesis output for coverage gaps and re-delegates with targeted follow-up queries if needed.

**Sample Code:**
```python
def coordinator_plan(query: str, has_documents: bool) -> list[str]:
    """Dynamically decide which subagents to invoke — never 'always run all'."""
    subagents = ["search"]
    if has_documents:
        subagents.append("document_analysis")
    subagents.append("synthesis")
    return subagents

# Hub-and-spoke: subagents never call each other directly.
def run_pipeline(query, has_documents):
    plan = coordinator_plan(query, has_documents)
    findings = {}
    for agent_name in plan:
        findings[agent_name] = invoke_subagent(agent_name, query, context=findings)
    return synthesize(findings)
```

**Sample Question 1:**
A multi-agent system researching "renewable energy adoption barriers" returns a report that only discusses solar panel costs, entirely missing policy, grid infrastructure, and public perception barriers. Subagent logs show each subagent executed its assigned task correctly. What is the most likely cause?

- **A.** The synthesis agent failed to identify gaps in the input it received.
- **B.** The coordinator's initial task decomposition was too narrow, assigning subagents only to cost-related subtopics.
- **C.** The web search subagent used a low-quality search query.
- **D.** The document analysis subagent applied overly strict relevance filtering.

**Correct: B.** As in the official sample question about creative industries, if every subagent did its assigned job correctly, the defect is upstream — in how the coordinator scoped the work.

**Sample Question 2:**
In a hub-and-spoke multi-agent system, the "analysis" subagent needs a piece of data that the "search" subagent already found. What is the correct communication pattern?

- **A.** The analysis subagent calls the search subagent directly to request the data.
- **B.** The search subagent proactively pushes updates to all other subagents whenever it finds something new.
- **C.** The coordinator receives the search subagent's output and explicitly passes the relevant data into the analysis subagent's prompt.
- **D.** Both subagents write to a shared global variable that either can read at any time.

**Correct: C.** Hub-and-spoke means all inter-agent data flow is routed through the coordinator — this preserves observability and consistent error handling, and avoids tightly-coupled direct subagent-to-subagent calls.

**Sample Question 3:**
A coordinator always spawns all four available subagents for every query, regardless of what the query actually needs. What is the main downside of this "always run everything" pattern?

- **A.** It guarantees more comprehensive coverage, so there's no real downside.
- **B.** It wastes resources/latency on irrelevant work and can dilute the final synthesis with irrelevant findings the coordinator then has to filter out.
- **C.** It violates the hub-and-spoke pattern.
- **D.** It causes `stop_reason` to never return `"end_turn"`.

**Correct: B.** Dynamic subagent selection based on the actual query scope is the documented best practice; running every subagent regardless of relevance costs time/tokens and can pollute synthesis with irrelevant material.

---

## Task Statement 1.3 — Configure subagent invocation, context passing, and spawning

**What it tests:** The `Task` tool mechanism, explicit context passing (no automatic inheritance), `AgentDefinition` configuration, parallel spawning, and `fork_session`.

**Worked example:** Your coordinator's `allowedTools` must include `"Task"` to spawn subagents at all. When the search subagent returns results, the coordinator must explicitly paste those results (or a structured summary with source metadata) into the synthesis subagent's prompt — the synthesis subagent has zero visibility into what the search subagent "saw."

**Steps:**
1. Confirm `"Task"` is included in the coordinator's `allowedTools`.
2. Define each subagent via `AgentDefinition` (description, system prompt, restricted tool set).
3. When delegating, explicitly embed prior findings in the subagent's prompt, using structured formats (e.g., JSON with `source_url`, `document_name`, `excerpt`) to preserve attribution separately from content.
4. To parallelize, emit multiple `Task` calls within a single coordinator turn rather than sequential turns.
5. Use `fork_session` when you want several agents to explore divergent strategies from one shared baseline (e.g., comparing two refactor approaches).

**Sample Code:**
```typescript
const synthesisAgent: AgentDefinition = {
  name: "synthesis",
  description: "Synthesizes findings from prior research into a coherent report.",
  systemPrompt: "You synthesize structured findings into a clear report...",
  allowedTools: ["Read"],
};

// Explicit context passing — the subagent has zero automatic visibility
// into what the coordinator or sibling agents saw.
const priorFindings = JSON.stringify([
  { source_url: "https://example.com/a", document_name: null, excerpt: "..." },
  { source_url: null, document_name: "report.pdf", excerpt: "..." },
]);

await Task({
  agent: synthesisAgent,
  prompt: `Synthesize the following findings into a report:\n${priorFindings}`,
});

// Parallel spawning: multiple Task calls emitted in the SAME coordinator turn
await Promise.all([
  Task({ agent: searchAgent, prompt: "Find sources on policy barriers." }),
  Task({ agent: searchAgent, prompt: "Find sources on grid infrastructure barriers." }),
]);
```

**Sample Question 1:**
Your coordinator spawns a synthesis subagent but the subagent's output ignores earlier findings from the search subagent, hallucinating generic information instead. What is the most likely root cause?

- **A.** The synthesis subagent's model is undersized for the task.
- **B.** The coordinator didn't include the search subagent's actual findings in the synthesis subagent's prompt, assuming automatic context inheritance.
- **C.** The `Task` tool wasn't included in `allowedTools`.
- **D.** `fork_session` should have been used instead of a fresh spawn.

**Correct: B.** Subagents never automatically inherit the coordinator's or siblings' conversation history — findings must be explicitly passed in the prompt.

**Sample Question 2:**
You want three subagents to each independently research a different, non-overlapping subtopic at the same time to minimize total latency. What is the correct implementation approach?

- **A.** Emit three separate `Task` calls sequentially across three separate coordinator turns.
- **B.** Emit all three `Task` calls within a single coordinator turn so they run in parallel.
- **C.** Use `fork_session` three times to branch off the coordinator's own session.
- **D.** Merge the three subtopics into one prompt and spawn a single subagent.

**Correct: B.** Parallel spawning is achieved by emitting multiple `Task` calls within one turn, not by sequential turns (which serializes them) or by conflating unrelated subtopics into a single agent.

**Sample Question 3:**
You want to compare two different refactoring strategies starting from the exact same point in an ongoing investigation, without re-doing the exploration work already completed. Which mechanism fits best?

- **A.** `Task`, spawning two fresh subagents with no prior context.
- **B.** `fork_session`, branching two divergent explorations off the same shared baseline session.
- **C.** `--resume`, resuming the same session twice in parallel.
- **D.** `AgentDefinition`, redefining the agent's system prompt twice.

**Correct: B.** `fork_session` is designed exactly for this: branching multiple agents off one shared baseline to explore divergent strategies without repeating prior work.

---

## Task Statement 1.4 — Implement multi-step workflows with enforcement and handoff patterns

**What it tests:** Programmatic vs. prompt-based enforcement, and structured handoff summaries for human escalation.

**Worked example:** A refund workflow requires identity verification before `process_refund` can run. Rather than instructing the model "always verify identity first" (probabilistic), you implement a programmatic gate that blocks the `process_refund` tool call unless a verified `customer_id` exists in state.

**Steps:**
1. Identify steps where non-compliance has real consequences (financial, legal, safety) — these need deterministic enforcement.
2. Implement a gate/hook that blocks the downstream tool call until the prerequisite tool has returned a valid result.
3. For multi-concern requests, decompose into distinct items, investigate each using shared context, then synthesize one unified response.
4. When escalating mid-process, compile a structured handoff summary: customer ID, root cause, relevant amounts, and recommended action — since the human agent has no access to the conversation transcript.

**Sample Code:**
```python
state = {"verified_customer_id": None}

def gate_process_refund(tool_name, tool_input, state):
    """Programmatic gate — deterministic, not probabilistic."""
    if tool_name == "process_refund" and not state.get("verified_customer_id"):
        return {
            "blocked": True,
            "reason": "Identity must be verified via get_customer before a refund can be processed.",
        }
    return {"blocked": False}

def build_handoff_summary(state, root_cause, recommended_action):
    return {
        "customer_id": state.get("verified_customer_id"),
        "root_cause": root_cause,
        "relevant_amounts": state.get("amounts", []),
        "recommended_action": recommended_action,
    }
```

**Sample Question 1:**
Despite system prompt instructions stating "always verify the customer's identity before issuing a refund," your agent occasionally issues refunds without verification in edge cases. What's the most reliable fix?

- **A.** Rewrite the instruction with stronger, more emphatic language.
- **B.** Add few-shot examples showing correct verification order.
- **C.** Implement a programmatic prerequisite that blocks `process_refund` until `get_customer` has returned a verified ID.
- **D.** Increase the model's temperature to zero for more deterministic behavior.

**Correct: C.** Prompt instructions have a non-zero failure rate; only programmatic enforcement gives a deterministic guarantee for business-critical ordering.

**Sample Question 2:**
A support agent escalates a billing dispute to a human, but the human agent has no access to the underlying conversation transcript. What should the escalation payload contain at minimum?

- **A.** Just the customer's most recent message, verbatim.
- **B.** A structured handoff summary: customer ID, root cause, relevant amounts, and a recommended action.
- **C.** A full raw dump of the entire conversation history with no summarization.
- **D.** Nothing — the human agent should re-investigate from scratch for objectivity.

**Correct: B.** Since the human has no transcript access, a structured, information-dense summary (not a raw dump or a single message) is what makes the handoff actionable.

**Sample Question 3:**
A customer message raises two independent, non-interacting concerns: a shipping delay question and a separate billing question. What is the best decomposition approach?

- **A.** Address only the first concern mentioned and ask the customer to send a separate message for the second.
- **B.** Decompose into the two distinct items, investigate each (sharing relevant context), then synthesize a single unified response covering both.
- **C.** Escalate immediately since multi-concern messages always require a human.
- **D.** Randomly pick whichever concern seems more urgent and ignore the other.

**Correct: B.** Multi-concern requests should be decomposed into distinct items and investigated individually, then combined into one coherent response — not truncated, escalated by default, or arbitrarily prioritized.

---

## Task Statement 1.5 — Apply Agent SDK hooks for tool call interception and data normalization

**What it tests:** `PostToolUse` hooks for normalization, pre-call interception hooks for compliance, and choosing hooks over prompts for guaranteed behavior.

**Worked example:** Three different backend MCP tools return dates in three formats: Unix timestamp, ISO 8601, and a custom numeric code. A `PostToolUse` hook normalizes all of these into one consistent format before the model ever sees them, preventing reasoning errors from format confusion.

**Steps:**
1. Identify tool outputs with inconsistent formats/units across your MCP tools.
2. Write a `PostToolUse` hook to normalize/transform results before they reach the model.
3. Identify business rules that must never be violated (e.g., "no refund over $500 without human approval").
4. Write a pre-call interception hook that inspects outgoing tool calls, blocks violations, and redirects to an alternative workflow (e.g., escalation).
5. Reserve prompt instructions for guidance that doesn't require hard guarantees.

**Sample Code:**
```python
def post_tool_use_hook(tool_name, raw_result):
    """Normalize inconsistent date formats before the model ever sees them."""
    if tool_name in ("get_order_date", "get_shipment_date", "get_invoice_date"):
        raw_result["date"] = normalize_to_iso8601(raw_result["date"])
    return raw_result

def pre_tool_use_hook(tool_name, tool_input):
    """Deterministic compliance gate — not a prompt suggestion."""
    if tool_name == "process_refund" and tool_input.get("amount", 0) > 500:
        return {
            "action": "redirect",
            "redirect_to": "escalate_to_human",
            "reason": "Refunds over $500 require human approval.",
        }
    return {"action": "allow"}
```

**Sample Question 1:**
Your policy requires that refunds above $500 always route to human review, but the agent occasionally processes larger refunds directly despite explicit system prompt instructions forbidding this. What is the most effective fix?

- **A.** Add a stronger warning in all caps to the system prompt.
- **B.** Implement a tool call interception hook that blocks `process_refund` calls above $500 and redirects to the escalation tool.
- **C.** Lower the model's `max_tokens` to reduce reasoning drift.
- **D.** Add few-shot examples of the agent correctly escalating high-value refunds.

**Correct: B.** This is a case requiring guaranteed compliance — a hook enforces it deterministically, unlike prompt-based approaches (A, D) which remain probabilistic.

**Sample Question 2:**
Three MCP tools in your system return currency values in three different formats (cents as integer, dollar-string with `$`, and a float with no currency marker). Which mechanism should normalize these before the model reasons about them?

- **A.** A system prompt instruction asking the model to "watch out for different currency formats."
- **B.** A `PostToolUse` hook that transforms each tool's raw output into one consistent format.
- **C.** A `PreToolUse` hook that blocks any tool call returning currency data.
- **D.** Few-shot examples showing the model doing the conversion mentally each time.

**Correct: B.** `PostToolUse` hooks are the right mechanism for deterministic data normalization — this removes the burden (and error rate) of ad hoc format conversion from the model entirely.

**Sample Question 3:**
When should you rely on a prompt instruction rather than a hook to control agent behavior?

- **A.** Never — hooks should replace all prompt instructions.
- **B.** When the behavior is guidance/style-level and doesn't require a hard guarantee (e.g., tone preferences), as opposed to business-critical rules that must never be violated.
- **C.** Only when the hook mechanism is unavailable in the current SDK version.
- **D.** Only for read-only tools, never for tools with side effects.

**Correct: B.** Hooks are reserved for guarantees (compliance, business-critical enforcement); prompts remain appropriate for softer guidance that doesn't carry hard consequences if occasionally not followed.

---

## Task Statement 1.6 — Design task decomposition strategies for complex workflows

**What it tests:** Choosing prompt chaining (fixed sequential pipeline) vs. dynamic/adaptive decomposition, and avoiding attention dilution in large reviews.

**Worked example:** For a predictable, repeatable code review, you use prompt chaining: pass 1 analyzes each file individually, pass 2 does a separate cross-file integration analysis. For an open-ended task like "add comprehensive tests to a legacy codebase," you instead use dynamic decomposition: first map the codebase structure, then identify high-impact areas, then build a prioritized plan that adapts as dependencies emerge.

**Steps:**
1. Ask: is this task predictable and repeatable (→ prompt chaining) or open-ended and exploratory (→ dynamic decomposition)?
2. For large multi-file work, split into per-file local passes plus one cross-file integration pass to avoid diluting attention across too much content at once.
3. For open-ended investigation, generate the plan iteratively based on what's discovered, rather than fixing the plan upfront.

**Sample Code:**
```python
# Prompt chaining — fixed, predictable pipeline
def review_pull_request(files: list[str]):
    per_file_findings = [call_claude(f"Review this file:\n{f}") for f in files]
    integration_findings = call_claude(
        f"Given these per-file findings, identify cross-file issues:\n{per_file_findings}"
    )
    return per_file_findings, integration_findings

# Dynamic decomposition — plan adapts as discovery happens
def add_tests_to_legacy_codebase():
    structure = call_claude("Map the codebase structure and module boundaries.")
    high_impact_areas = call_claude(f"Given this structure, identify high-impact, low-coverage areas:\n{structure}")
    plan = call_claude(f"Build a prioritized testing plan for these areas:\n{high_impact_areas}")
    return plan  # plan is generated FROM discovery, not fixed upfront
```

**Sample Question 1:**
A code review over a 20-file pull request produces inconsistent quality — deep analysis on some files, superficial comments on others, and contradictory findings for identical patterns in different files. What is the best restructuring?

- **A.** Use a single pass with a bigger context window model.
- **B.** Split into individual per-file passes plus a separate cross-file integration pass.
- **C.** Require developers to submit smaller PRs.
- **D.** Run the same full-PR review three times and keep the majority result.

**Correct: B.** This directly addresses attention dilution — the root cause — rather than working around it (C) or masking it (A, D).

**Sample Question 2:**
Which task is the better fit for a fixed, prompt-chaining pipeline rather than dynamic decomposition?

- **A.** "Investigate why our checkout conversion dropped 15% last month" (open-ended, unknown cause).
- **B.** "Redesign our microservice architecture for better scalability" (many valid approaches).
- **C.** "For every PR, run a security scan pass, then a style-lint pass, then a test-coverage pass, in that fixed order."
- **D.** "Explore this unfamiliar legacy codebase and figure out where the bugs likely are."

**Correct: C.** A repeatable, predictable sequence of fixed steps is the signature of a good prompt-chaining use case; A, B, and D are all open-ended/exploratory and better suited to dynamic decomposition.

**Sample Question 3:**
For an open-ended investigation like "figure out why memory usage is climbing in production," what is the recommended decomposition approach?

- **A.** Fix the full investigation plan upfront before any exploration begins.
- **B.** Generate the plan iteratively, letting each discovery inform what to investigate next.
- **C.** Break the task into exactly three fixed phases regardless of findings.
- **D.** Skip decomposition and handle it in a single unstructured pass.

**Correct: B.** Open-ended, exploratory tasks call for dynamic/adaptive decomposition — the plan should evolve based on what's discovered, not be locked in before any investigation has happened.

---

## Task Statement 1.7 — Manage session state, resumption, and forking

**What it tests:** `--resume <session-name>`, `fork_session`, informing resumed sessions about file changes, and choosing resumption vs. fresh start with injected summary.

**Worked example:** You paused a multi-day codebase investigation. Before resuming with `--resume investigate-auth-flow`, you also inform the session that three files were modified since the last run, so it re-analyzes just those rather than assuming stale findings are still valid.

**Steps:**
1. Use `--resume <session-name>` to continue a named prior investigation.
2. If files have changed since the session was last active, explicitly tell the agent which files changed so it targets re-analysis rather than doing a full re-exploration.
3. Use `fork_session` when you want to branch off a shared analysis baseline to explore two or more divergent approaches independently (e.g., comparing testing strategies).
4. If a lot of the prior session's tool results are now stale/invalid, prefer starting a new session with a structured summary injected, rather than resuming with outdated context.

**Sample Code:**
```bash
# Resume a named session, then tell it what changed
claude --resume investigate-auth-flow \
  -p "Two files changed since we last worked: src/auth/token.ts and src/auth/session.ts. Re-analyze only those."

# Fork a shared baseline to compare two divergent strategies
claude --resume investigate-auth-flow --fork-session strategy-jwt
claude --resume investigate-auth-flow --fork-session strategy-session-cookie

# When too much prior context is stale, start fresh with an injected summary instead
claude -p "Here is a summary of prior findings: <structured-summary>. Continue from here."
```

**Sample Question 1:**
You paused a Claude Code investigation into a legacy billing module three days ago. Since then, two of the files you analyzed were significantly refactored by a teammate. What's the best way to resume?

- **A.** Start a completely new session and re-explore the entire codebase from scratch.
- **B.** Resume with `--resume`, and explicitly inform the agent which specific files changed so it can re-analyze those targeted files.
- **C.** Resume with `fork_session` to create a branch reflecting the new state.
- **D.** Resume normally and trust the agent to detect file changes automatically.

**Correct: B.** Resumption preserves valid prior context (efficient), but stale findings on changed files must be explicitly flagged — the agent doesn't automatically detect this.

**Sample Question 2:**
You've completed extensive exploration of a codebase and now want to try two genuinely different refactor strategies without repeating that exploration for each. What's the right tool?

- **A.** `--resume` twice in two separate terminal windows using the same session name.
- **B.** `fork_session`, to branch two independent explorations off the shared completed-exploration baseline.
- **C.** Two brand-new sessions with the exploration summary manually pasted into each.
- **D.** A single session that attempts both strategies interleaved in one conversation.

**Correct: B.** This is exactly the `fork_session` use case: divergent strategies from one shared baseline, explored independently.

**Sample Question 3:**
After a long pause, so much of a prior session's tool output is now stale (many files rewritten, dependencies upgraded) that most resumed context would be actively misleading. What's the better approach?

- **A.** Resume as normal — some stale context is always tolerable.
- **B.** Start a new session with a structured summary of what's still valid injected in, rather than resuming with mostly-outdated context.
- **C.** Use `fork_session` to preserve the stale context in a separate branch.
- **D.** Resume, then ask the agent to individually verify every prior finding one by one before continuing.

**Correct: B.** When most of the prior session's grounding is invalid, a fresh session seeded with a curated, structured summary is more reliable than resuming and dragging along outdated assumptions.

---

# DOMAIN 2: Tool Design & MCP Integration (18%)

## Task Statement 2.1 — Design effective tool interfaces with clear descriptions and boundaries

**What it tests:** Tool descriptions as the primary selection mechanism, avoiding overlap/ambiguity, and system-prompt keyword sensitivity.

**Worked example:** Two tools, `analyze_content` and `analyze_document`, have nearly identical one-line descriptions. The model frequently picks the wrong one. Renaming `analyze_content` to `extract_web_results` with a web-specific description (inputs: URL; use case: live web pages) eliminates the ambiguity.

**Steps:**
1. Write descriptions that state: purpose, expected inputs/formats, example queries, edge cases, and explicit "use this vs. that other tool when..." guidance.
2. Look for near-duplicate descriptions across your tool set — these are the most common cause of misrouting.
3. Split overly generic tools into purpose-specific ones with clear input/output contracts (e.g., `analyze_document` → `extract_data_points`, `summarize_content`, `verify_claim_against_source`).
4. Review your system prompt for keyword-heavy instructions that might bias tool selection unintentionally.

**Sample Code:**
```json
{
  "name": "extract_web_results",
  "description": "Extracts and summarizes content from a LIVE WEB PAGE given its URL. Use this when the user references an online article, a website, or a search result link. Do NOT use this for uploaded documents or local files — use extract_document_data for those. Example: 'summarize this article: https://...'",
  "input_schema": {
    "type": "object",
    "properties": {
      "url": { "type": "string", "description": "The full URL of the web page." }
    },
    "required": ["url"]
  }
}
```

**Sample Question 1:** *(See official Question 2 above)* — Improving minimal, overlapping tool descriptions with input formats, examples, and boundaries is the most effective **first step**, ahead of few-shot examples, routing layers, or consolidation.

- **A.** Add a routing layer that picks the tool programmatically before the model sees either option.
- **B.** Rewrite both tool descriptions with explicit purpose, input formats, examples, and "use this vs. that" boundaries.
- **C.** Add 10+ few-shot examples demonstrating correct tool selection.
- **D.** Merge both tools into a single tool with a `mode` parameter.

**Correct: B.** Improving the descriptions themselves — the model's primary selection signal — is the most effective first step, ahead of routing layers, heavy few-shotting, or consolidation, all of which are more invasive workarounds.

**Sample Question 2:**
Two tools, `get_user_info` and `get_customer_details`, return overlapping but slightly different data, and the model picks inconsistently between them. What is the most direct fix?

- **A.** Randomly deprecate one of the two tools without investigation.
- **B.** Differentiate the descriptions clearly — state exactly what each returns and when to use one over the other — or consolidate them into one well-scoped tool if the overlap is total.
- **C.** Add a `PostToolUse` hook to merge their outputs after the fact.
- **D.** Increase the model's `max_tokens` so it can reason longer about which to pick.

**Correct: B.** Ambiguous, overlapping descriptions are the root cause of tool misrouting; clarifying boundaries (or consolidating truly redundant tools) addresses it directly.

**Sample Question 3:**
Your system prompt says "always prioritize search-based tools for factual questions." You notice the model now over-uses your `web_search` tool even for questions your `internal_kb_lookup` tool is clearly better suited for. What is the likely cause?

- **A.** The `internal_kb_lookup` tool's description is too long.
- **B.** The system prompt's keyword-heavy phrasing ("prioritize search-based tools") is biasing tool selection in an unintended way.
- **C.** `web_search` has too few input parameters.
- **D.** The model's context window is too small.

**Correct: B.** System prompt wording can bias tool selection just as strongly as tool descriptions — keyword-heavy instructions should be reviewed as a possible cause of misrouting, not just the tool descriptions themselves.

---

## Task Statement 2.2 — Implement structured error responses for MCP tools

**What it tests:** The `isError` flag, error categories (transient/validation/business/permission), retryable vs. non-retryable, and distinguishing access failures from valid empty results.

**Worked example:** Instead of returning `{"error": "Operation failed"}`, your `lookup_order` tool returns `{"isError": true, "errorCategory": "transient", "isRetryable": true, "message": "Order service timed out after 5s"}` for a timeout, vs. `{"isError": true, "errorCategory": "business", "isRetryable": false, "message": "Refunds cannot exceed original payment amount"}` for a policy violation.

**Steps:**
1. Classify every failure mode: transient, validation, business/policy, or permission.
2. Return structured metadata (`errorCategory`, `isRetryable`, human-readable message) rather than a generic string.
3. Distinguish "the query failed" (needs a retry decision) from "the query succeeded but found nothing" (a valid empty result) — don't conflate the two.
4. Let subagents attempt local recovery for transient errors; only propagate to the coordinator errors that couldn't be resolved locally, along with partial results and what was attempted.

**Sample Code:**
```json
// Transient failure — retryable
{ "isError": true, "errorCategory": "transient", "isRetryable": true,
  "message": "Order service timed out after 5s" }

// Business rule violation — NOT retryable
{ "isError": true, "errorCategory": "business", "isRetryable": false,
  "message": "Refunds cannot exceed original payment amount" }

// Valid empty result — NOT an error at all
{ "isError": false, "results": [], "message": "No orders found for this customer ID." }
```

**Sample Question 1:**
Your MCP tool currently returns `{"isError": true, "message": "Operation failed"}` for every failure type — timeouts, invalid input, and policy violations alike. The agent frequently retries policy-violation errors uselessly. What should you change?

- **A.** Add a global retry limit of 3 attempts for all errors.
- **B.** Return `errorCategory` and `isRetryable` fields so the agent can distinguish retryable transient errors from non-retryable business errors.
- **C.** Remove the `isError` flag and always return HTTP 200.
- **D.** Have the agent ask the user whether to retry on every error.

**Correct: B.** Structured metadata lets the agent make appropriate decisions per error type instead of blindly retrying everything.

**Sample Question 2:**
A `search_orders` tool returns `[]` (an empty array) when a customer genuinely has no orders, and also returns `[]` when the backend database connection fails. What's the problem with this design?

- **A.** There is no problem — an empty array is always a safe default.
- **B.** The agent cannot distinguish "the query succeeded and found nothing" from "the query failed to execute," which could lead it to incorrectly tell the customer they have no orders when the real issue was a system failure.
- **C.** Empty arrays should be replaced with `null` in all cases.
- **D.** The tool should throw an unhandled exception instead.

**Correct: B.** Conflating a valid empty result with an access/execution failure is a documented anti-pattern — these need distinct, explicit representations (e.g., `isError: true` for the failure case) so downstream logic and messaging are correct.

**Sample Question 3:**
A subagent's tool call fails with a `transient` error (e.g., a momentary network blip). What is the best first response?

- **A.** Immediately propagate the raw error to the coordinator and halt.
- **B.** Attempt local recovery (e.g., one quick retry) within the subagent first; only propagate to the coordinator if local recovery fails, including partial results and what was attempted.
- **C.** Silently return an empty success result to avoid alarming the coordinator.
- **D.** Kill the entire multi-agent workflow to prevent further errors.

**Correct: B.** Local recovery for transient issues should be attempted first; only genuinely unresolved errors should propagate upward, and always with structured context — never silently as a fake success, and never by terminating the whole workflow.

---

## Task Statement 2.3 — Distribute tools appropriately across agents and configure tool choice

**What it tests:** Tool-count limits per agent, scoped access by role, cross-role tools for high-frequency needs, and `tool_choice` options (`auto`/`any`/forced).

**Worked example:** Instead of giving every subagent all 18 available tools, you scope the synthesis subagent to only 2–3 tools relevant to synthesis, plus one narrow cross-role `verify_fact` tool for its most common cross-cutting need — routing anything more complex through the coordinator.

**Steps:**
1. Audit each agent's tool list; if it's in the double digits, look for tools outside that agent's core role.
2. Restrict each subagent's toolset to what its role actually needs.
3. For a specific high-frequency cross-role need, add one narrow, purpose-built tool rather than the whole other agent's toolkit.
4. Use `tool_choice: "any"` when you need to guarantee a tool call (any tool) rather than conversational text.
5. Use forced tool selection (`{"type": "tool", "name": "..."}`) when a specific tool must run first (e.g., `extract_metadata` before enrichment steps), then let follow-up turns handle the rest.

**Sample Code:**
```python
# Scoped tool access — synthesis agent gets only what it needs
synthesis_agent_tools = [summarize_findings_tool, verify_fact_tool]  # not all 12

# tool_choice: "auto" — model decides whether/which tool to use (default)
response = client.messages.create(..., tool_choice={"type": "auto"})

# tool_choice: "any" — guarantee SOME tool call happens, not free text
response = client.messages.create(..., tool_choice={"type": "any"})

# Forced selection — a specific tool must run first
response = client.messages.create(
    ..., tool_choice={"type": "tool", "name": "extract_metadata"}
)
```

**Sample Question 1:**
A synthesis subagent has been given all 12 of the system's tools "just in case," including web search and document-fetching tools meant for other subagents. You observe the synthesis agent occasionally attempting redundant web searches instead of focusing on synthesis. What's the best fix?

- **A.** Add a system prompt warning telling the synthesis agent not to use search tools.
- **B.** Restrict the synthesis agent's tool access to only synthesis-relevant tools, adding at most a narrow scoped tool for its most common cross-role need.
- **C.** Increase the synthesis agent's temperature to reduce erratic tool use.
- **D.** Remove all tools from the synthesis agent and have it work from text only.

**Correct: B.** Access to tools outside an agent's specialization tends to get misused; scoping access is the structural fix, not a prompt warning (which is probabilistic) or removing all tools (which may be too extreme if a narrow need is legitimate).

**Sample Question 2:**
You need to guarantee that the model calls *some* tool on this turn (you don't care which one, but plain conversational text is not acceptable) — for example, a classification step that must always route to one of several handler tools. Which `tool_choice` setting fits?

- **A.** `{"type": "auto"}`
- **B.** `{"type": "any"}`
- **C.** `{"type": "tool", "name": "..."}`
- **D.** Omitting `tool_choice` entirely and relying on prompt instructions.

**Correct: B.** `tool_choice: "any"` forces a tool call (any of the available tools) rather than allowing a free-text response — exactly what's needed when you need *a* tool call but don't know which one in advance.

**Sample Question 3:**
A pipeline requires `extract_metadata` to run before any enrichment tools are called, on every single request, with no exceptions. What's the best way to enforce the ordering on that first turn?

- **A.** `tool_choice: "auto"` with a prompt reminder to call `extract_metadata` first.
- **B.** `tool_choice: "any"`, letting the model pick freely among all available tools.
- **C.** Forced selection: `{"type": "tool", "name": "extract_metadata"}` on the first turn, then normal `tool_choice` for subsequent turns.
- **D.** Remove all other tools from the toolset permanently.

**Correct: C.** Forced tool selection guarantees a *specific* tool runs — appropriate when a fixed step must always happen first; subsequent turns can then return to normal tool_choice behavior for the flexible enrichment steps.

---

## Task Statement 2.4 — Integrate MCP servers into Claude Code and agent workflows

**What it tests:** `.mcp.json` (project) vs. `~/.claude.json` (user) scoping, environment variable expansion, simultaneous multi-server tool discovery, and MCP resources for content catalogs.

**Worked example:** Your team's shared GitHub MCP server is configured in `.mcp.json` at the project root with `"GITHUB_TOKEN": "${GITHUB_TOKEN}"` so the token is pulled from each developer's environment rather than committed to the repo. You separately add an experimental personal MCP server in `~/.claude.json` to try out a new internal tool without affecting teammates.

**Steps:**
1. Put shared, team-wide MCP servers in project-scoped `.mcp.json`, using `${VAR}` syntax for secrets.
2. Put personal/experimental servers in user-scoped `~/.claude.json`.
3. Remember all configured servers' tools are discovered and available simultaneously — no explicit "activation" step needed.
4. If the agent keeps preferring a built-in tool (e.g., `Grep`) over a more capable MCP tool, improve the MCP tool's description rather than removing the built-in.
5. For existing standard integrations (e.g., Jira), prefer community MCP servers over building custom ones; reserve custom servers for team-specific workflows.
6. Expose static/browsable data (issue catalogs, schema listings) as MCP **resources** rather than requiring exploratory tool calls to discover them.

**Sample Code:**
```json
// .mcp.json — project root, version-controlled, shared by the whole team
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": { "DB_PASSWORD": "${DB_PASSWORD}" }
    }
  }
}
```
```json
// ~/.claude.json — user-scoped, personal/experimental, NOT shared with teammates
{
  "mcpServers": {
    "my-experimental-tool": {
      "command": "node",
      "args": ["/Users/me/experiments/mcp-server.js"]
    }
  }
}
```

**Sample Question 1:**
A new engineer joins the team and needs access to the shared Postgres MCP server that the rest of the team uses, without needing to reconfigure anything after cloning the repo. Where should this server be configured, and how should the database credential be handled?

- **A.** In `~/.claude.json`, with the credential hardcoded.
- **B.** In `.mcp.json` at the project root, with the credential referenced via environment variable expansion (e.g., `${DB_PASSWORD}`).
- **C.** In `CLAUDE.md`, with the credential in plaintext.
- **D.** In `.claude/rules/`, with the credential passed as a command-line flag.

**Correct: B.** Project-scoped `.mcp.json` is version-controlled and shared automatically; environment variable expansion keeps secrets out of the repo.

**Sample Question 2:**
You notice Claude Code keeps using the built-in `Grep` tool instead of your team's more capable MCP-based `semantic_code_search` tool, even though the MCP tool would give better results for the query at hand. What should you do first?

- **A.** Remove the built-in `Grep` tool entirely so there's no competing option.
- **B.** Improve the MCP tool's description so its purpose and advantages over `Grep` are clearer to the model.
- **C.** Move the MCP server from `.mcp.json` to `~/.claude.json`.
- **D.** Add a `paths` glob pattern rule forcing the MCP tool's use.
- **E.** *(not applicable — 4-option format)*

**Correct: B.** As with any tool-selection issue, improving the competing tool's description is the direct fix — the model chooses based on description quality, and removing a useful built-in tool is a more invasive workaround.

**Sample Question 3:**
Your team has a large, mostly-static catalog of internal API schemas that agents frequently need to reference. What is the most appropriate way to expose this via MCP?

- **A.** As an MCP tool that agents must call every time they want to browse the catalog.
- **B.** As an MCP **resource**, since it's static/browsable content rather than an action to perform.
- **C.** Pasted directly into every `CLAUDE.md` file across the repo.
- **D.** As a `.claude/rules/` file with a broad glob pattern.

**Correct: B.** MCP resources are designed for exposing static or browsable content (like a schema catalog) without requiring exploratory tool calls — tools are for actions/queries, resources are for content.

---

## Task Statement 2.5 — Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively

**What it tests:** Choosing the right built-in tool for the job, and the Edit → Read+Write fallback when anchor text isn't unique.

**Worked example:** To find every place a deprecated function `fetchLegacyOrder` is called, you use `Grep` for the function name across the codebase — not `Glob` (which only matches filenames, not content). When you need to update one specific line but `Edit` fails because the anchor text isn't unique, you fall back to `Read` (get full contents) + `Write` (rewrite the whole file with the change applied).

**Steps:**
1. Use `Grep` to search file *contents* (function calls, error strings, imports).
2. Use `Glob` to find files by *name/path pattern* (e.g., `**/*.test.tsx`).
3. Use `Read`/`Write` for whole-file operations; use `Edit` for small, targeted, uniquely-anchored changes.
4. When `Edit` fails due to non-unique matching text, fall back to `Read` + `Write`.
5. Build up codebase understanding incrementally: `Grep` to find entry points → `Read` to follow imports/trace flow — don't read everything upfront.

**Sample Code:**
```bash
# Grep: search file CONTENTS for a deprecated function call
grep -rn "fetchLegacyOrder(" src/

# Glob: find files by NAME/PATH pattern (not content)
# matches: src/components/Button.test.tsx, src/utils/date.test.tsx, ...
**/*.test.tsx

# Edit fails when the anchor text isn't unique -> fall back to Read + Write
# 1) Read the whole file
# 2) Programmatically/manually apply the change to the correct occurrence
# 3) Write the full corrected file back
```

**Sample Question 1:**
You need to change a specific line inside a 300-line configuration file, but the exact text you want to target appears three times in the file with different surrounding context each time, and `Edit` keeps failing due to ambiguous matching. What should you do?

- **A.** Use `Grep` with a regex to force a unique match.
- **B.** Use `Read` to load the full file, then `Write` the entire file back with the correct version of that line changed.
- **C.** Use `Glob` to locate the exact line number.
- **D.** Retry `Edit` repeatedly until it succeeds by chance.

**Correct: B.** This is the documented fallback pattern when `Edit`'s uniqueness requirement can't be satisfied.

**Sample Question 2:**
You need to find every file in the repository whose *filename* ends in `.config.js`, regardless of what's inside them. Which tool is correct?

- **A.** `Grep`, searching for the string `.config.js` in file contents.
- **B.** `Glob`, matching the pattern `**/*.config.js` against file paths.
- **C.** `Read`, opening every file in the repo to check its name.
- **D.** `Bash`, using `cat` recursively across the repo.

**Correct: B.** `Glob` matches file *names/paths* by pattern; `Grep` is for searching file *contents* — using `Grep` here would search inside files for a literal string, not filter by filename.

**Sample Question 3:**
You're exploring an unfamiliar 500-file codebase to understand how authentication works. What is the recommended approach to build understanding without consuming excessive context?

- **A.** `Read` every file in the repository upfront before forming any hypothesis.
- **B.** Use `Grep` to find likely entry points (e.g., search for "login" or "authenticate"), then `Read` selectively to follow imports and trace the flow incrementally.
- **C.** Use `Glob` to list all files, then process them in random order.
- **D.** Use `Bash` to `cat` the entire repository into a single buffer.

**Correct: B.** Incremental exploration — narrow with `Grep`, then follow the trail with targeted `Read` calls — avoids the context bloat of reading an entire large codebase upfront.

---

# DOMAIN 3: Claude Code Configuration & Workflows (20%)

## Task Statement 3.1 — Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization

**What it tests:** User/project/directory-level `CLAUDE.md` hierarchy, `@import`, and `.claude/rules/` as an alternative to a monolithic file.

**Worked example:** A new teammate reports "Claude doesn't follow our conventions" — investigation reveals the previous engineer had put all the team's conventions in their personal `~/.claude/CLAUDE.md`, which is never shared via version control. Moving those conventions to the project-root `.claude/CLAUDE.md` fixes it for everyone.

**Steps:**
1. Diagnose "it works for me but not my teammate" issues by checking whether instructions live in user-level (`~/.claude/CLAUDE.md`, personal only) vs. project-level (`.claude/CLAUDE.md`/root `CLAUDE.md`, shared) config.
2. Use `@import` to pull in specific standards files per package/module, based on what's relevant to that area.
3. For large, sprawling `CLAUDE.md` files, split by topic into `.claude/rules/` (e.g., `testing.md`, `api-conventions.md`, `deployment.md`).
4. Use `/memory` to inspect which memory files are actually loaded when debugging inconsistent behavior across sessions.

**Sample Code:**
```
project-root/
├── CLAUDE.md                  # project-wide, version-controlled, shared by all
├── packages/
│   └── billing/
│       └── CLAUDE.md          # @import ../../CLAUDE.md + billing-specific rules
└── .claude/
    └── rules/
        ├── testing.md
        ├── api-conventions.md
        └── deployment.md

~/.claude/CLAUDE.md            # PERSONAL ONLY — never shared, never version-controlled
```
```md
<!-- packages/billing/CLAUDE.md -->
@import ../../CLAUDE.md

## Billing-specific conventions
- All monetary values are stored as integer cents, never floats.
```

**Sample Question 1:**
A new team member's Claude Code sessions don't apply any of the team's established coding conventions, even though the conventions clearly exist somewhere in a senior engineer's setup. What is the most likely cause?

- **A.** The conventions are in `.claude/rules/` with incorrect glob patterns.
- **B.** The conventions are stored in the senior engineer's `~/.claude/CLAUDE.md`, which is personal and not shared via version control.
- **C.** The new team member needs to run `/memory` to activate the conventions.
- **D.** `CLAUDE.md` files require re-import after each `git pull`.

**Correct: B.** User-level config is per-user and never propagates to teammates automatically — this is a classic hierarchy misconfiguration.

**Sample Question 2:**
You have a monorepo with five packages, each needing the shared root conventions plus a handful of package-specific rules. What is the cleanest way to structure this?

- **A.** Duplicate the entire root `CLAUDE.md` content into each package's own `CLAUDE.md`.
- **B.** Give each package its own `CLAUDE.md` that uses `@import` to pull in the shared root file, plus its own package-specific additions.
- **C.** Put everything for all five packages into one enormous root `CLAUDE.md`.
- **D.** Store package-specific conventions in each developer's personal `~/.claude/CLAUDE.md`.

**Correct: B.** `@import` avoids duplication by letting package-level files pull in shared root conventions while adding only what's specific to that package — duplicating (A) or over-centralizing (C) both create maintenance problems, and D reintroduces the personal-config sharing problem.

**Sample Question 3:**
You suspect a session isn't picking up a rule you expect it to have loaded. What command helps you debug which memory files are actually in effect for that session?

- **A.** `/compact`
- **B.** `/memory`
- **C.** `--resume`
- **D.** `fork_session`

**Correct: B.** `/memory` inspects which memory files (CLAUDE.md hierarchy, rules, imports) are actually loaded for the current session — the right tool for diagnosing "why isn't this convention applying."

---

## Task Statement 3.2 — Create and configure custom slash commands and skills

**What it tests:** `.claude/commands/` (project) vs. `~/.claude/commands/` (personal), `SKILL.md` frontmatter (`context: fork`, `allowed-tools`, `argument-hint`), and skills vs. `CLAUDE.md`.

**Worked example:** *(See official Question 4 above)* — a `/review` command meant for the whole team goes in `.claude/commands/` in the repo. Separately, you build a `codebase-analysis` skill that produces very verbose output; you set `context: fork` in its `SKILL.md` frontmatter so that verbose exploration runs in an isolated sub-agent context and doesn't pollute the main conversation.

**Steps:**
1. Project-wide, team-shared commands → `.claude/commands/` (version-controlled).
2. Personal-only commands → `~/.claude/commands/`.
3. For skills that produce verbose or exploratory output, set `context: fork` to isolate them.
4. Use `allowed-tools` in a skill's frontmatter to restrict what it can do (e.g., limit to file-write-only to prevent destructive actions).
5. Use `argument-hint` to prompt for required parameters when a developer invokes the skill without arguments.
6. Choose skills for on-demand, task-specific workflows; choose `CLAUDE.md` for always-loaded universal standards.

**Sample Code:**
```md
---
name: code-audit
description: Runs an extensive, multi-step codebase exploration and produces a findings report.
context: fork
allowed-tools: [Read, Grep, Glob]
argument-hint: "<directory-to-audit>"
---

# Code Audit Skill
1. Map the target directory structure.
2. Identify code smells, dead code, and missing test coverage.
3. Produce a single summarized findings report (not the raw exploration trace).
```

**Sample Question 1:**
You built a `code-audit` skill that runs an extensive, multi-step codebase exploration and tends to flood the main conversation with dozens of intermediate findings before producing a final report. How should you configure the skill to prevent this from polluting the main session?

- **A.** Set `argument-hint` to warn users about verbosity.
- **B.** Set `context: fork` in the skill's frontmatter so exploration happens in an isolated sub-agent context.
- **C.** Move the skill to `~/.claude/skills/` instead of `.claude/skills/`.
- **D.** Restrict `allowed-tools` to only `Read`.

**Correct: B.** `context: fork` is specifically designed to isolate verbose/exploratory skill output from the main conversation.

**Sample Question 2:**
A `/deploy` slash command runs destructive infrastructure changes and must never be allowed to run arbitrary shell commands beyond a fixed, vetted set. What frontmatter field enforces this?

- **A.** `argument-hint`
- **B.** `context: fork`
- **C.** `allowed-tools`, scoped to only the specific vetted commands/tools the deploy step needs.
- **D.** `description`

**Correct: C.** `allowed-tools` restricts what a skill/command can actually do — the correct mechanism for preventing a destructive command from having broader tool access than it needs.

**Sample Question 3:**
Your team wants a `/review` command available to every developer on the team automatically after cloning the repo, with no per-developer setup. Where should it live?

- **A.** `~/.claude/commands/`, so each developer configures it individually.
- **B.** `.claude/commands/` in the repo, so it's version-controlled and shared automatically.
- **C.** Inside `CLAUDE.md` as a described workflow.
- **D.** In `.claude/rules/` with a glob pattern matching all files.

**Correct: B.** Project-scoped `.claude/commands/` is version-controlled and available to the whole team immediately after cloning — no manual per-developer setup needed, unlike the personal `~/.claude/commands/` location.

---

## Task Statement 3.3 — Apply path-specific rules for conditional convention loading

**What it tests:** `.claude/rules/` with YAML frontmatter `paths` glob patterns, and why this beats directory-level `CLAUDE.md` for cross-cutting conventions.

**Worked example:** *(See official Question 6 above)* — test files (`Button.test.tsx`) live next to their source files throughout the codebase rather than in one directory. A directory-scoped `CLAUDE.md` can't target them since they're scattered; a `.claude/rules/testing.md` with `paths: ["**/*.test.tsx"]` loads only when a matching file is being edited, regardless of location.

**Steps:**
1. Identify conventions that are tied to a *file type/pattern* rather than a *directory*.
2. Create a rule file in `.claude/rules/` with YAML frontmatter specifying `paths` glob patterns.
3. Confirm the rule only loads (and only adds token overhead) when a matching file is actually being edited.
4. Prefer this over subdirectory `CLAUDE.md` files whenever the convention doesn't map cleanly onto the directory tree.

**Sample Code:**
```md
<!-- .claude/rules/testing.md -->
---
paths:
  - "**/*.test.tsx"
  - "**/*.test.ts"
---

# Testing Conventions
- Use `@testing-library/react`, never `enzyme`.
- Every test file must include at least one accessibility assertion.
- Mock network calls with `msw`, not manual `fetch` stubs.
```

**Sample Question 1:** *(See official Question 6 above.)* Correct answer: create `.claude/rules/` files with `paths` glob patterns (Option A), not directory-level `CLAUDE.md` files, root-level headers, or manually-invoked skills.

- **A.** Create a `.claude/rules/testing.md` file with a `paths` glob pattern matching test files wherever they live.
- **B.** Create a `CLAUDE.md` file in every directory that happens to contain a test file.
- **C.** Add a root-level header in `CLAUDE.md` listing every test file location individually.
- **D.** Build a manually-invoked skill that developers must remember to run before editing tests.

**Correct: A.** Path-pattern rules target file *types* regardless of directory, which is exactly the cross-cutting case that directory-scoped `CLAUDE.md` files (B, C) can't handle cleanly, and doesn't rely on developers remembering to invoke anything (D).

**Sample Question 2:**
Your team wants a convention ("always use the internal `Logger` utility, never `console.log`") to apply to every `.ts`/`.tsx` source file across the entire monorepo, regardless of which package it's in. What's the best mechanism?

- **A.** A `.claude/rules/` file scoped with `paths: ["**/*.ts", "**/*.tsx"]`.
- **B.** A separate `CLAUDE.md` file placed in every single directory in the monorepo.
- **C.** A slash command developers must run manually before every commit.
- **D.** A `PostToolUse` hook that deletes any `console.log` calls after the fact.

**Correct: A.** A broad `paths` glob pattern in `.claude/rules/` cleanly covers a file-type-wide convention across the whole repo without needing per-directory duplication.

**Sample Question 3:**
What is the main advantage of `.claude/rules/` with `paths` glob patterns over a monolithic root `CLAUDE.md` containing all conventions?

- **A.** Rules files support `@import` while `CLAUDE.md` does not.
- **B.** Rules only load (and add token overhead) when a file matching their pattern is actually being edited, rather than always being loaded in full for every session.
- **C.** Rules files can only be edited by administrators.
- **D.** There is no real advantage — they are functionally identical.

**Correct: B.** Conditional loading based on the file being edited keeps context lean — a large monolithic `CLAUDE.md` is loaded in full every time, regardless of relevance to the current task.

---

## Task Statement 3.4 — Determine when to use plan mode vs direct execution

**What it tests:** Recognizing task complexity signals that call for plan mode vs. straightforward direct execution, and using the Explore subagent to preserve context during discovery.

**Worked example:** *(See official Question 5 above)* — restructuring a monolith into microservices (architectural decisions, many files, multiple valid approaches) calls for plan mode: explore first, design an approach, then execute. A single-file bug fix with a clear stack trace calls for direct execution — there's nothing to plan.

**Steps:**
1. Ask: does this task involve architectural decisions, multiple valid approaches, or many files? → Plan mode.
2. Ask: is this a simple, well-scoped, single-file change? → Direct execution.
3. For multi-phase work, use plan mode for the investigation phase, then switch to direct execution to implement the agreed plan.
4. During verbose discovery (e.g., mapping a large unfamiliar codebase), delegate to the Explore subagent so raw discovery noise doesn't consume your main context window — only summaries return.

**Sample Code:**
```bash
# Direct execution — simple, well-scoped, single-file change
claude -p "Fix the null pointer in src/utils/date.ts line 42 per this stack trace: ..."

# Plan mode — architectural decision, many files, multiple valid approaches
claude --plan "Restructure the monolith's order-processing module into a separate microservice"
# -> Claude explores, proposes a plan, you approve/adjust, THEN it executes
```

**Sample Question 1:**
You need to add a single null-check to one function based on a clear stack trace from a bug report. What is the appropriate approach?

- **A.** Enter plan mode to explore the codebase for related issues first.
- **B.** Use direct execution — the change is simple and well-scoped.
- **C.** Spawn a subagent for the investigation before making the change.
- **D.** Fork a session to try two different validation approaches.

**Correct: B.** Direct execution is appropriate for simple, well-understood, clearly-scoped changes; plan mode would be over-engineering here.

**Sample Question 2:**
You're asked to migrate an application's state management from one library to another across 40 files, with several architecturally valid ways to approach the migration. What is the appropriate approach?

- **A.** Direct execution, making changes file-by-file as you go without an upfront plan.
- **B.** Plan mode — explore the codebase, propose an approach given the multiple valid strategies, get it reviewed/approved, then execute.
- **C.** A single slash command that performs the entire migration atomically with no review step.
- **D.** Skip planning and ask the model to guess the best approach silently, mid-execution.

**Correct: B.** Many files plus multiple valid architectural approaches are the textbook signal for plan mode — explore and propose before committing to execution.

**Sample Question 3:**
During the exploration phase of a large, unfamiliar codebase (mapping hundreds of files before proposing a plan), how should you keep the main session's context from being overwhelmed by discovery noise?

- **A.** Read every file directly in the main session so nothing is missed.
- **B.** Delegate the verbose discovery work to the Explore subagent, so only summarized findings return to the main context.
- **C.** Skip exploration entirely and go straight to direct execution.
- **D.** Use `fork_session` to duplicate the exploration across multiple parallel main sessions.

**Correct: B.** The Explore subagent is designed to absorb verbose discovery work, returning only summaries — this keeps the main session's context focused and preserves budget for the actual planning/execution work.

---

## Task Statement 3.5 — Apply iterative refinement techniques for progressive improvement

**What it tests:** Concrete I/O examples, test-driven iteration, the "interview pattern," and batching interacting fixes vs. sequential fixes for independent issues.

**Worked example:** You ask Claude to "normalize phone numbers" and get inconsistent results across edge cases. Instead of refining the prose description further, you give 2–3 concrete input→output examples (e.g., `"(555) 123-4567" → "+15551234567"`), which resolves the ambiguity immediately.

**Steps:**
1. If prose instructions are producing inconsistent output, replace/supplement them with 2–3 concrete input/output examples.
2. For implementation tasks, write the test suite first (expected behavior, edge cases, performance requirements), then iterate by feeding back test failures.
3. In unfamiliar domains, use the "interview pattern" — have Claude ask you clarifying questions (e.g., about cache invalidation strategy) before it implements anything.
4. When multiple issues interact with each other, describe them together in one detailed message; when issues are independent, fix them one at a time sequentially.

**Sample Code:**
```
Instruction: "Normalize phone numbers to E.164 format."

Instead of more prose, give concrete examples:
  "(555) 123-4567"      -> "+15551234567"
  "555.123.4567 ext 22"  -> "+15551234567"   (extension dropped)
  "+1 555 123 4567"      -> "+15551234567"   (already normalized, idempotent)
  ""                     -> null              (empty input -> null, not error)
```

**Sample Question 1:**
You're asking Claude to migrate a legacy data format, but its handling of null values is inconsistent across runs despite detailed prose instructions describing the expected behavior. What is the most effective next step?

- **A.** Rewrite the prose instructions with even more detail.
- **B.** Provide 2-3 concrete input/output examples showing exactly how null values should be handled.
- **C.** Lower the temperature parameter.
- **D.** Split the migration into ten smaller sequential requests.

**Correct: B.** Concrete examples resolve ambiguity that prose descriptions, however detailed, tend to leave open to interpretation.

**Sample Question 2:**
You're implementing a caching layer in an unfamiliar part of the codebase and aren't sure how the team wants cache invalidation handled. What's the best approach before writing any code?

- **A.** Guess the most common industry-standard approach and implement it.
- **B.** Use the "interview pattern" — have Claude ask clarifying questions about invalidation strategy before implementing anything.
- **C.** Implement three different invalidation strategies and let the team pick later.
- **D.** Skip invalidation entirely and flag it as a known gap.

**Correct: B.** In unfamiliar domains with real ambiguity, having the model ask clarifying questions upfront (the "interview pattern") avoids costly rework compared to guessing.

**Sample Question 3:**
A PR has two issues: (1) a logging statement that leaks a password, and (2) a completely unrelated typo in a comment two files away. What's the best way to request fixes?

- **A.** Describe both issues together in one detailed message, since batching is always better.
- **B.** Fix the password leak first as its own request; the unrelated typo can be handled separately since the two issues don't interact.
- **C.** Ignore the typo since it's not urgent.
- **D.** Always fix issues in the order they appear in the diff, regardless of relationship.

**Correct: B.** The rule is to batch *interacting* issues together and handle *independent* issues separately/sequentially — these two issues don't interact, so there's no benefit (and some risk of conflating unrelated context) to batching them.

---

## Task Statement 3.6 — Integrate Claude Code into CI/CD pipelines

**What it tests:** `-p`/`--print` for non-interactive mode, `--output-format json` + `--json-schema`, using `CLAUDE.md` for CI context, and why self-review by the same session is weaker than independent review.

**Worked example:** *(See official Questions 10 & 11 above)* — a CI job hangs because it's missing `-p`. Once fixed, the job runs `claude -p "Review this PR for security issues" --output-format json --json-schema review-schema.json` to produce machine-parseable findings that get posted as inline PR comments automatically.

**Steps:**
1. Always run Claude Code with `-p`/`--print` in automated/non-interactive pipeline contexts.
2. Use `--output-format json` with `--json-schema` to get structured, parseable output for programmatic posting.
3. Document testing standards, fixture conventions, and review criteria in `CLAUDE.md` so CI-invoked runs have the same context a human reviewer would.
4. When re-running reviews after new commits, include prior findings in context and instruct Claude to report only new/unaddressed issues (avoid duplicate comments).
5. Use an *independent* review instance rather than having the same session that wrote the code review its own work — self-review retains generation-time reasoning and is less likely to catch its own mistakes.

**Sample Code:**
```bash
# CI job — non-interactive, structured, machine-parseable output
claude -p "Review this PR diff for security issues: $(git diff main...HEAD)" \
  --output-format json \
  --json-schema review-schema.json \
  > review-findings.json

# Post findings programmatically from the parsed JSON
python post_pr_comments.py review-findings.json
```
```json
// review-schema.json
{
  "type": "object",
  "properties": {
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "file": { "type": "string" },
          "line": { "type": "integer" },
          "severity": { "type": "string", "enum": ["low", "medium", "high"] },
          "issue": { "type": "string" }
        },
        "required": ["file", "line", "severity", "issue"]
      }
    }
  }
}
```

**Sample Question 1:** *(See official Question 10 above.)* Correct answer: the `-p` flag enables non-interactive mode; `CLAUDE_HEADLESS` and `--batch` are not real flags.

- **A.** `--batch`
- **B.** `CLAUDE_HEADLESS=1`
- **C.** `-p` / `--print`
- **D.** `--ci-mode`

**Correct: C.** `-p`/`--print` is the real flag that enables non-interactive, scriptable execution suitable for CI; the other options are not real Claude Code flags/env vars.

**Sample Question 2:**
Your CI pipeline needs to programmatically parse Claude's PR-review findings to post them as inline comments, but the current setup just captures Claude's free-text response. What should you add?

- **A.** `--verbose` for more detailed text output.
- **B.** `--output-format json` combined with `--json-schema` to get a machine-parseable, schema-validated response.
- **C.** A regex parser to extract findings from the free-text output.
- **D.** `--print` alone, without any format changes.

**Correct: B.** Structured JSON output validated against a schema is the reliable way to get machine-parseable findings, versus a fragile regex over free text.

**Sample Question 3:**
Your CI pipeline currently has the same Claude Code session that just generated a bug fix also perform the final review of that fix before merging. Reviewers later find issues that were missed. What is the recommended change?

- **A.** Add more emphatic review instructions to the same session's prompt.
- **B.** Use a separate, independent Claude instance with no memory of the original generation reasoning to perform the review.
- **C.** Increase `max_tokens` for the review step.
- **D.** Skip automated review entirely and rely solely on human reviewers.

**Correct: B.** Self-review by the generating session is weaker because it retains generation-time reasoning and is less likely to question its own decisions — an independent reviewing instance is the documented fix.

---

# DOMAIN 4: Prompt Engineering & Structured Output (20%)

## Task Statement 4.1 — Design prompts with explicit criteria to improve precision and reduce false positives

**What it tests:** Explicit, categorical criteria vs. vague confidence-based instructions ("be conservative"), and managing developer trust via false-positive rates.

**Worked example:** A code-review prompt that says "only flag high-confidence issues" still over-flags style nitpicks. Replacing it with an explicit rule — "flag a comment only when the claimed behavior contradicts the actual code behavior; do not flag style, naming, or local pattern deviations" — sharply reduces false positives because the criterion is checkable, not a vague confidence judgment.

**Steps:**
1. Replace vague qualifiers ("be careful," "only if confident") with concrete, checkable categorical rules.
2. Define explicitly what to report vs. what to skip.
3. If one category (e.g., style comments) has an especially high false-positive rate, consider temporarily disabling it to protect trust in the categories that work well, while you improve the prompt for that category.
4. Provide concrete code examples for each severity level to keep classification consistent.

**Sample Code:**
```
# Before — vague, confidence-based
"Only report high-confidence, important issues."

# After — explicit, categorical, checkable
"Report a finding ONLY if one of these is true:
  1. The code's actual behavior contradicts a docstring/comment's claimed behavior.
  2. A null/undefined value can reach a dereference without a guard.
  3. A resource (file handle, DB connection) is opened but never closed on an error path.
Do NOT report: style, naming conventions, or formatting deviations."
```

**Sample Question 1:**
A PR-review bot is instructed to "only report high-confidence, important issues," but developers report a high volume of low-value comments and have started ignoring the bot entirely. What change will most effectively reduce false positives?

- **A.** Increase the confidence threshold language to "only report very high-confidence issues."
- **B.** Replace the vague confidence instruction with explicit, categorical criteria defining exactly which issue types to report and which to skip.
- **C.** Switch to a larger model for better judgment.
- **D.** Reduce the number of files reviewed per run.

**Correct: B.** Vague confidence-based instructions ("be conservative," "high-confidence") don't reliably improve precision; specific, checkable criteria do.

**Sample Question 2:**
After tightening review criteria, one category — "potential race conditions" — still has a much higher false-positive rate than every other category, and it's damaging developer trust in the whole bot. What's the recommended interim step?

- **A.** Remove the bot entirely until it's perfect.
- **B.** Temporarily disable reporting for that specific high-false-positive category while you improve its criteria, keeping the well-performing categories active.
- **C.** Lower the confidence bar even further for that category.
- **D.** Merge that category's criteria into the general "style" category.

**Correct: B.** Selectively disabling the underperforming category protects trust in the categories that already work well, while giving you room to fix the specific problem area — rather than an all-or-nothing response.

**Sample Question 3:**
You want a severity-classification prompt ("low/medium/high") to be applied consistently across many PRs. What most directly improves consistency?

- **A.** A single adjective per severity level (e.g., "high = bad").
- **B.** Concrete code examples illustrating each severity level, alongside the categorical criteria.
- **C.** Asking the model to self-report its own confidence in the severity it picked.
- **D.** Randomizing which severity levels are shown in the prompt each run.

**Correct: B.** Concrete examples anchored to each severity level make the classification checkable and consistent, the same way examples resolve ambiguity elsewhere in prompt design.

---

## Task Statement 4.2 — Apply few-shot prompting to improve output consistency and quality

**What it tests:** Few-shot examples for format consistency, ambiguous-case handling, generalization, and hallucination reduction in extraction.

**Worked example:** *(See official Question 2 context)* — a tool-selection prompt with only prose instructions produces inconsistent routing on ambiguous requests. Adding 5–8 few-shot examples that each show the *reasoning* for why one tool was chosen over a plausible alternative teaches the model to generalize the underlying judgment, not just memorize the specific examples.

**Steps:**
1. Identify where detailed prose instructions alone still yield inconsistent output.
2. Write 2–4 targeted few-shot examples focused on the ambiguous/edge cases specifically, not just typical cases.
3. Include the *reasoning* in each example, not just input→output, so the model generalizes the judgment.
4. For extraction tasks, add examples covering varied document structures (e.g., inline citations vs. bibliographies) to reduce hallucinated/empty fields on structural variety the model hasn't seen before.

**Sample Code:**
```
Example 1
Input: "What's on my calendar tomorrow?"
Reasoning: This asks about scheduled events, not general knowledge — use get_calendar_events, not web_search.
Tool: get_calendar_events

Example 2
Input: "What's the capital of France and is it raining there right now?"
Reasoning: This has two parts — a static fact (no tool needed) and a live weather lookup (needs weather_tool). Answer the static part directly, call weather_tool for the second.
Tool: weather_tool (for the weather portion only)
```

**Sample Question 1:**
An extraction system correctly pulls data from documents with standard table formats but frequently returns null or hallucinated values for documents using narrative prose with embedded figures. What is the most effective fix?

- **A.** Add few-shot examples demonstrating correct extraction from narrative-style, non-tabular documents.
- **B.** Increase `max_tokens` for the extraction call.
- **C.** Add a post-processing regex to catch missed fields.
- **D.** Switch the required fields to optional across the board.

**Correct: A.** Few-shot examples covering the structural variety the model is failing on directly teaches the pattern it's missing.

**Sample Question 2:**
You're adding few-shot examples to a classification prompt that already has clear prose rules but still misclassifies edge cases. Which set of examples will help most?

- **A.** Ten examples of the most common, unambiguous, typical case.
- **B.** Two to four examples specifically targeting the ambiguous/edge cases the model is getting wrong, each including the reasoning behind the correct classification.
- **C.** Examples with only the correct label and no input context.
- **D.** As many examples as fit in the context window, regardless of relevance.

**Correct: B.** Targeted, reasoning-included examples on the specific ambiguous cases generalize the judgment; large volumes of only-typical examples don't address the actual failure mode.

**Sample Question 3:**
Why is it important to include the *reasoning* in a few-shot example, rather than just the raw input→output pair?

- **A.** It isn't important — input→output pairs alone are always sufficient.
- **B.** Including reasoning helps the model generalize the underlying judgment to new, unseen cases, rather than just pattern-matching to the literal examples given.
- **C.** Reasoning is only useful for the model's internal logging, not its output quality.
- **D.** It reduces the number of examples needed to zero.

**Correct: B.** Reasoning-included examples teach the *why*, which transfers to novel cases better than examples that only show input-output mappings without the underlying logic.

---

## Task Statement 4.3 — Enforce structured output using tool use and JSON schemas

**What it tests:** `tool_use` + JSON schema as the reliable path to schema compliance, `tool_choice` modes, syntax vs. semantic errors, and schema design (nullable/optional fields, enum + "other" patterns).

**Worked example:** *(See official Exercise 3 and Appendix)* — an invoice-extraction tool defines `line_items` as required but `discount_amount` as nullable, since not every invoice has a discount. Using `tool_use` guarantees the JSON is syntactically valid, but you still need semantic checks (do the line items sum to the stated total?) — schema compliance alone doesn't catch that.

**Steps:**
1. Define your target schema as a tool's input parameters; extract the structured result from the `tool_use` block of the response.
2. Use `tool_choice: "any"` when you have several possible extraction schemas and don't know upfront which document type you're dealing with.
3. Use forced tool selection (`{"type": "tool", "name": "extract_metadata"}`) when a specific extraction must run first, before enrichment steps.
4. Make fields nullable/optional when the source document may genuinely lack that information — this prevents the model from fabricating values just to satisfy a "required" constraint.
5. Use `enum` fields with an `"other"` + free-text detail pattern for categories that need to stay extensible.
6. Remember: `tool_use` schemas eliminate JSON *syntax* errors but not *semantic* errors (wrong field, numbers that don't add up) — you still need separate validation for those.

**Sample Code:**
```json
{
  "name": "extract_invoice",
  "description": "Extracts structured invoice data.",
  "input_schema": {
    "type": "object",
    "properties": {
      "line_items": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "description": { "type": "string" },
            "amount": { "type": "number" }
          },
          "required": ["description", "amount"]
        }
      },
      "discount_amount": { "type": ["number", "null"], "description": "Null if no discount applied." },
      "payment_method": {
        "type": "string",
        "enum": ["credit_card", "bank_transfer", "check", "other"],
        "description": "Use 'other' with a note in payment_method_detail if none of the standard options apply."
      },
      "payment_method_detail": { "type": ["string", "null"] }
    },
    "required": ["line_items", "payment_method"]
  }
}
```
```python
# Semantic validation — schema compliance alone doesn't catch this
extracted = get_tool_use_input(response)
calculated_total = sum(item["amount"] for item in extracted["line_items"]) - (extracted["discount_amount"] or 0)
if abs(calculated_total - extracted["stated_total"]) > 0.01:
    flag_for_review(extracted, reason="line items don't sum to stated total")
```

**Sample Question 1:**
An invoice extraction system using `tool_use` with a strict JSON schema never produces malformed JSON, but downstream systems still occasionally receive invoices where the summed line items don't match the stated total. What does this indicate?

- **A.** The schema needs `strict: true` mode enabled.
- **B.** Schema-enforced structured output eliminates syntax errors but not semantic errors — a separate validation step is needed to catch inconsistencies like this.
- **C.** The model should be switched to a higher-capability tier.
- **D.** `tool_choice` should be set to `"auto"` instead of forced selection.

**Correct: B.** This is exactly the syntax-vs-semantic distinction the exam tests — schema compliance is not the same as correctness.

**Sample Question 2:**
You're designing a schema for a `document_type` field, and you want it to stay useful even when a document doesn't fit any of your five known categories. What's the best pattern?

- **A.** Make `document_type` a free-text string field with no constraints at all.
- **B.** Use an `enum` of the five known categories plus `"other"`, paired with a free-text `document_type_detail` field for the unmatched case.
- **C.** Require the model to always pick one of the five categories, even if none truly fit.
- **D.** Split the schema into five separate tools, one per category.

**Correct: B.** The `enum` + `"other"` + free-text-detail pattern keeps the field both constrained (useful for downstream logic) and extensible (doesn't force a bad fit when a genuinely new category appears).

**Sample Question 3:**
A `tax_id` field is required in your extraction schema, but roughly 20% of source documents genuinely don't contain a tax ID anywhere. What's the effect of keeping this field strictly required?

- **A.** No effect — `tool_use` schemas handle missing data gracefully by default.
- **B.** The model is likely to fabricate a plausible-looking but incorrect value just to satisfy the required constraint, since it has no valid way to represent "genuinely absent."
- **C.** The API call will fail outright for those 20% of documents.
- **D.** The field will automatically default to an empty string.

**Correct: B.** Forcing a required field when the source data may genuinely lack that information invites fabrication — making it nullable/optional is the correct schema design to let the model represent "not present" honestly.

---

## Task Statement 4.4 — Implement validation, retry, and feedback loops for extraction quality

**What it tests:** Retry-with-error-feedback, recognizing when retries can't help (info genuinely absent from source), and tracking dismissal/false-positive patterns via structured fields.

**Worked example:** An extraction fails Pydantic validation because `total_amount` doesn't match the sum of `line_items`. You send a follow-up request that includes the original document, the failed extraction, and the specific validation error, letting the model self-correct. But when a required field (e.g., `vendor_tax_id`) simply doesn't appear anywhere in the source document, no amount of retrying will produce a correct value — that calls for marking the field `null`/unavailable instead.

**Steps:**
1. On validation failure, retry with a follow-up request containing: the original doc, the failed extraction, and the specific error message.
2. Distinguish failures that are format/structural (retry-fixable) from failures where the information simply isn't in the source (not retry-fixable — should resolve to null instead).
3. Add a `detected_pattern` field to structured findings so you can later analyze which code/document patterns trigger false positives or dismissed findings.
4. For numeric consistency checks, extract both a `calculated_total` and a `stated_total` and flag discrepancies; add `conflict_detected` booleans for inconsistent source data.

**Sample Code:**
```python
def extract_with_retry(document, max_retries=3):
    for attempt in range(max_retries):
        result = call_claude_extract(document)
        try:
            validated = InvoiceSchema.model_validate(result)
            return validated
        except ValidationError as e:
            if is_source_data_missing(e, document):
                # Retrying won't help — the info just isn't in the source
                result[e.field_name] = None
                return InvoiceSchema.model_validate(result)
            # Structural/format error — retry with the specific error as feedback
            document = augment_with_feedback(document, failed_extraction=result, error=str(e))
    raise ExtractionFailedError("Max retries exceeded")
```

**Sample Question 1:**
An extraction pipeline keeps failing validation on a specific field because the field's data genuinely does not appear anywhere in 15% of the source documents. Your current approach retries up to 3 times per document. What should change?

- **A.** Increase the retry count to 5.
- **B.** Recognize that retries won't help when information is absent from the source; mark the field as null/unavailable instead of continuing to retry.
- **C.** Switch the field from optional to required to force the model to try harder.
- **D.** Add a longer timeout per retry attempt.

**Correct: B.** Retries only help with format/structural errors, not with information that was never in the source document to begin with.

**Sample Question 2:**
A validation failure occurs because the extracted date is in `MM/DD/YYYY` format but your schema requires ISO 8601. What is the appropriate retry strategy?

- **A.** Mark the field null immediately, since this is unfixable.
- **B.** Retry with a follow-up request that includes the original document, the failed extraction, and the specific validation error, so the model can self-correct the format.
- **C.** Discard the entire document and skip it.
- **D.** Silently reformat the date programmatically without involving the model again.

**Correct: B.** This is a structural/format error (retry-fixable), unlike genuinely missing source data — including the specific error as feedback lets the model self-correct on the next attempt.

**Sample Question 3:**
Your team wants to later analyze which document patterns most often trigger false positives in an extraction/review pipeline. What should you add to your structured output now to enable that analysis later?

- **A.** Nothing — this can be reconstructed later from raw logs alone.
- **B.** A `detected_pattern` field on each structured finding, so patterns correlated with false positives/dismissals can be analyzed downstream.
- **C.** A single aggregate accuracy percentage per batch.
- **D.** A free-text `notes` field with no consistent structure.

**Correct: B.** A structured, consistently-populated field like `detected_pattern` enables systematic downstream analysis of which patterns drive false positives — an aggregate percentage (C) or unstructured notes (D) can't be queried the same way.

---

## Task Statement 4.5 — Design efficient batch processing strategies

**What it tests:** Message Batches API tradeoffs (cost vs. latency), matching batch/real-time to workload latency tolerance, `custom_id` correlation, and handling partial batch failures.

**Worked example:** *(See official Question 11 above)* — a blocking pre-merge check must stay on the real-time API (developers are waiting); an overnight technical-debt report is a perfect candidate for the Batch API's 50% cost savings, since nobody's blocked on it finishing within minutes.

**Steps:**
1. Classify each workload: is it blocking (needs an answer now) or latency-tolerant (can wait up to 24 hours)?
2. Route blocking workflows to the synchronous API; route latency-tolerant, high-volume workloads to the Batch API.
3. Use `custom_id` to correlate batch requests with their responses.
4. On partial batch failure, resubmit only the failed documents (identified by `custom_id`), with any needed modifications (e.g., chunking documents that exceeded context limits).
5. Test your prompt on a small sample before submitting a large batch, to maximize first-pass success and avoid costly resubmission cycles.
6. Remember: the Batch API doesn't support multi-turn tool calling within a single request.

**Sample Code:**
```python
# Batch API — latency-tolerant, high-volume workload (e.g., weekly report)
batch_requests = [
    {
        "custom_id": f"doc-{doc.id}",
        "params": {
            "model": "claude-sonnet-5",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": f"Summarize: {doc.text}"}],
        },
    }
    for doc in weekly_documents
]
batch = client.messages.batches.create(requests=batch_requests)

# On partial failure, resubmit only the failed custom_ids
failed_ids = [r.custom_id for r in batch_results if r.result.type == "errored"]
resubmit = [req for req in batch_requests if req["custom_id"] in failed_ids]

# Real-time API — blocking, developer-waiting workload (pre-merge check)
response = client.messages.create(
    model="claude-sonnet-5", max_tokens=1024,
    messages=[{"role": "user", "content": "Review this PR for security issues."}],
)
```

**Sample Question 1:**
Your team wants to cut costs on two workflows: (1) a pre-merge check developers wait on before merging, and (2) a weekly summary report reviewed the following Monday. Your manager suggests moving both to the Message Batches API for the 50% savings. What's the correct evaluation?

- **A.** Move both — the cost savings apply regardless of workflow type.
- **B.** Move only the weekly report to batch processing; keep the pre-merge check on the real-time API, since batch has no latency SLA and pre-merge checks are blocking.
- **C.** Keep both on real-time to avoid `custom_id` correlation complexity.
- **D.** Move both to batch with a real-time fallback if batch takes too long.

**Correct: B.** This matches the official Question 11 pattern exactly — batch processing is unsuitable for blocking, developer-waiting workflows regardless of the cost incentive.

**Sample Question 2:**
You submit a batch of 10,000 document-summarization requests, and 40 of them come back with an `errored` result type due to a formatting issue in those specific documents. What is the correct recovery approach?

- **A.** Discard the entire batch and resubmit all 10,000 requests.
- **B.** Use the `custom_id` values to identify the 40 failed requests, fix the underlying issue for just those documents, and resubmit only those.
- **C.** Ignore the 40 failures since they're a small percentage of the total.
- **D.** Switch the entire workload to the real-time API going forward.

**Correct: B.** `custom_id` correlation is exactly what enables targeted resubmission of only the failed items, rather than wastefully redoing the whole batch or the opposite extreme of abandoning the batch approach entirely.

**Sample Question 3:**
Before submitting a 50,000-request batch job overnight, what is the recommended practice to avoid a costly resubmission cycle the next day?

- **A.** Submit the full batch immediately — the Batch API's error handling makes pre-testing unnecessary.
- **B.** Test the prompt on a small sample first to maximize first-pass success before committing to the full-size batch.
- **C.** Split the batch into 50 separate batches of 1,000 each, submitted simultaneously.
- **D.** Add multi-turn tool calling to make each request more robust.

**Correct: B.** Validating the prompt against a small sample first catches systemic issues before they multiply across tens of thousands of requests — note also that the Batch API does not support multi-turn tool calling (D), which rules that option out entirely.

---

## Task Statement 4.6 — Design multi-instance and multi-pass review architectures

**What it tests:** Self-review limitations, independent review instances, and multi-pass (per-file + integration) review design.

**Worked example:** *(See official Question 12 above and Domain 1.6)* — a code-generation session that also reviews its own output tends to rubber-stamp its own decisions because it retains its generation-time reasoning. Spinning up a second, independent Claude instance (with no memory of *why* the code was written that way) catches issues the original session is structurally unlikely to flag.

**Steps:**
1. Never rely on the same session that generated code to also be its primary reviewer — use a second, independent instance without that reasoning context.
2. For large multi-file changes, split review into per-file local passes (depth) plus one cross-file integration pass (breadth), rather than one pass trying to do both.
3. Optionally, have the model self-report a confidence score per finding to enable calibrated routing (e.g., low-confidence findings go to a human).

**Sample Code:**
```python
# Generation happens in session A
generation_session = new_session()
code = generation_session.run("Implement the refactor described in TICKET-123.")

# Review happens in an INDEPENDENT session B — no shared reasoning context
review_session = new_session()  # fresh, no memory of session A's reasoning
findings = review_session.run(f"Review this code for correctness and security issues:\n{code}")
```

**Sample Question 1:**
Your team notices that when the same Claude Code session that generated a refactor is also asked to review it, it rarely flags any issues with its own decisions — even when a human later spots real problems. What's the best architectural fix?

- **A.** Ask the same session to review more critically using a stronger prompt.
- **B.** Add extended thinking to the same session before it reviews its own work.
- **C.** Use a second, independent Claude instance with no prior reasoning context to perform the review.
- **D.** Have the same session re-read its own code three times before finalizing.

**Correct: C.** A model that generated the code retains reasoning context that makes it less likely to question its own decisions — an independent instance without that context reviews more objectively.

**Sample Question 2:**
A 30-file refactor needs review. A single review pass across all 30 files at once tends to catch surface-level issues in each file but misses inconsistencies *between* files (e.g., two files handling the same edge case differently). What's the best restructuring?

- **A.** One larger single pass with a bigger context window.
- **B.** Per-file local review passes for depth, plus a separate cross-file integration pass specifically looking for inconsistencies between files.
- **C.** Skip cross-file concerns entirely and focus only on per-file correctness.
- **D.** Have the generating session review its own consistency across files.

**Correct: B.** Splitting into per-file (depth) and cross-file integration (breadth) passes is the documented multi-pass pattern — a single pass tends to dilute attention across both concerns.

**Sample Question 3:**
You want low-confidence review findings to be routed to a human reviewer while high-confidence findings are auto-applied. What should the independent review instance additionally produce?

- **A.** Nothing extra — route all findings to a human regardless.
- **B.** A self-reported confidence score per finding, enabling calibrated routing of low-confidence findings to human review.
- **C.** A single aggregate confidence score for the entire review, applied uniformly to all findings.
- **D.** No confidence signal — apply all findings automatically.

**Correct: B.** Per-finding confidence scores allow calibrated routing (only the uncertain findings go to a human), rather than an all-or-nothing approach that either wastes reviewer time or risks auto-applying uncertain findings.

---

# DOMAIN 5: Context Management & Reliability (15%)

## Task Statement 5.1 — Manage conversation context to preserve critical information across long interactions

**What it tests:** Progressive summarization risk, "lost in the middle," trimming verbose tool outputs, and preserving conversation history for coherence.

**Worked example:** A customer service agent's summarization step compresses "customer requested a refund of $247.83 for order #A19273, placed on March 3rd" down to "customer wants a refund" — losing the exact amount, order number, and date needed later. Instead, you extract these as a persistent "case facts" block (kept verbatim, outside the summarized history) that's included in every subsequent prompt.

**Steps:**
1. Identify transactional/numeric facts (amounts, dates, IDs, statuses) at risk of being blurred by summarization.
2. Extract them into a separate, persistent "facts" block included in every prompt, rather than relying on the summarized narrative to preserve them.
3. Watch for the "lost in the middle" effect on long inputs — place key findings at the beginning (and/or end) of aggregated content, with clear section headers, rather than burying them mid-document.
4. Trim verbose tool outputs (e.g., a 40-field order lookup) down to only the fields actually relevant to the task before they accumulate in context.
5. Require subagents to include metadata (dates, sources, methodology) directly in their structured outputs to support accurate downstream synthesis, especially when downstream agents have limited context budgets.

**Sample Code:**
```python
case_facts = {
    "order_id": "A19273",
    "refund_amount": 247.83,
    "requested_date": "2026-03-03",
}

def build_prompt(conversation_summary, case_facts, latest_message):
    return f"""
CASE FACTS (verbatim, always accurate):
{json.dumps(case_facts, indent=2)}

CONVERSATION SUMMARY (may be lossy):
{conversation_summary}

LATEST MESSAGE:
{latest_message}
"""
# case_facts is never re-derived from the lossy summary — it's tracked separately.
```

**Sample Question 1:**
A customer support agent progressively summarizes a long multi-turn conversation. By turn 15, the summary reads "customer had an issue with an order and wants resolution," but the customer originally stated an exact refund amount and order number in turn 2. What is the best fix?

- **A.** Increase the summarization frequency so information is compressed sooner.
- **B.** Extract transactional facts (amounts, order numbers, dates) into a persistent "case facts" block included verbatim in every prompt, separate from the summarized narrative.
- **C.** Stop summarizing entirely and always pass the full 15-turn transcript.
- **D.** Ask the customer to repeat their original request at turn 15.

**Correct: B.** This directly prevents the exact failure mode described — numeric/transactional facts getting lost through progressive summarization.

**Sample Question 2:**
A 40-field order-lookup tool result gets appended in full to the conversation on every turn, even though only 3 fields (status, ship date, tracking number) are actually relevant to the current task. What's the recommended fix?

- **A.** Leave it as-is — more context is always better.
- **B.** Trim the tool output down to only the fields actually relevant to the task before it accumulates in context.
- **C.** Summarize the entire 40-field result into one sentence using the model itself.
- **D.** Replace the tool call with a hardcoded static response.

**Correct: B.** Trimming verbose tool outputs to relevant fields before they accumulate is the documented practice — it keeps context lean without needing lossy re-summarization (C) or removing the real data source (D).

**Sample Question 3:**
You're aggregating findings from five subagents into one long document for a final synthesis step, and you notice the model tends to underweight findings placed in the middle of the document relative to the beginning and end. What is this phenomenon, and what's the mitigation?

- **A.** This is a hallucination issue; the fix is lowering temperature.
- **B.** This is the "lost in the middle" effect; mitigate by placing key findings near the start/end with clear section headers rather than burying them mid-document.
- **C.** This is a tool-selection issue; the fix is adding more few-shot examples.
- **D.** This is a schema-compliance issue; the fix is enforcing `tool_use`.

**Correct: B.** "Lost in the middle" is the documented term for this positional attention effect in long aggregated inputs — structuring content with key findings up front/at the end (and clear headers) counteracts it.

---

## Task Statement 5.2 — Design effective escalation and ambiguity resolution patterns

**What it tests:** Appropriate escalation triggers, honoring explicit customer requests, why sentiment/self-confidence are unreliable proxies, and handling multiple ambiguous matches.

**Worked example:** *(See official Question 3 above)* — an agent under-escalates policy-exception cases and over-escalates simple cases because it lacks explicit escalation criteria. Adding criteria plus few-shot examples ("escalate when: customer explicitly asks for a human; policy is silent/ambiguous on the request; you cannot make progress after 2 attempts. Resolve autonomously when: standard cases with clear policy coverage") recalibrates this.

**Steps:**
1. Add explicit escalation triggers to the system prompt: explicit customer request, policy gap/exception, inability to make progress — not "complexity" alone.
2. Honor an explicit "I want a human" request immediately, without first attempting investigation.
3. When a customer is frustrated but the issue is straightforward, acknowledge the frustration and offer to resolve it — escalate only if they reiterate their preference for a human.
4. Don't rely on sentiment analysis or self-reported model confidence as escalation triggers — both are unreliable proxies for actual case complexity.
5. When a lookup returns multiple matching customer records, ask the customer for an additional identifier rather than guessing via heuristics.

**Sample Code:**
```
ESCALATE TO HUMAN when any of the following is true:
  - The customer explicitly asks to speak with a human.
  - Company policy is silent or ambiguous on the customer's specific request.
  - You have attempted to resolve the issue twice and made no progress.

RESOLVE AUTONOMOUSLY when:
  - The case is standard and clearly covered by existing policy,
    even if the customer sounds frustrated — acknowledge the frustration,
    then offer the resolution. Escalate only if they still ask for a human.

Do NOT escalate based on: sentiment/tone alone, or your own self-reported confidence level.
```

**Sample Question 1:**
Your agent is programmed to escalate whenever it detects negative sentiment in the customer's message, and to resolve autonomously whenever its self-reported confidence is above 7/10. Escalation rates don't correlate well with actual case complexity — simple frustrated customers get escalated while the agent confidently mishandles genuinely complex policy-exception cases. What is the core issue?

- **A.** The confidence threshold should be raised to 9/10.
- **B.** Sentiment and self-reported confidence are unreliable proxies for case complexity; explicit criteria (customer request, policy gaps, inability to progress) should drive escalation instead.
- **C.** Sentiment analysis needs a more sophisticated model.
- **D.** The agent should escalate all cases above a certain conversation length.

**Correct: B.** Both signals used here are documented anti-patterns — the fix is switching to explicit, criteria-based escalation logic.

**Sample Question 2:**
A customer says "I'd like to speak to a human agent, please" in their very first message, before any investigation has happened. What is the correct agent behavior?

- **A.** Investigate the issue fully first, then escalate once findings are ready.
- **B.** Honor the explicit request and escalate immediately, without requiring an investigation attempt first.
- **C.** Ask the customer to explain why they don't want to work with the agent before escalating.
- **D.** Attempt autonomous resolution twice before honoring the request.

**Correct: B.** An explicit customer request for a human is one of the documented triggers that should be honored immediately — investigating first would go against the customer's stated preference.

**Sample Question 3:**
A phone-number lookup for "John Smith" returns three different customer records with that name. What's the correct next step?

- **A.** Guess based on which record was created most recently.
- **B.** Ask the customer for an additional identifying detail (e.g., order number, email, or zip code) rather than guessing via heuristics.
- **C.** Pick the record with the most complete data on file.
- **D.** Escalate to a human immediately without attempting clarification.

**Correct: B.** When a lookup returns multiple ambiguous matches, the correct pattern is to ask the customer for a disambiguating identifier — not to guess (risking acting on the wrong account) and not to over-escalate a resolvable ambiguity.

---

## Task Statement 5.3 — Implement error propagation strategies across multi-agent systems

**What it tests:** Structured error context for coordinator recovery, access failures vs. valid empty results, local recovery before propagation, and avoiding "swallow" or "kill everything" anti-patterns.

**Worked example:** *(See official Question 8 above)* — when a search subagent times out, it returns structured context (failure type: timeout; attempted query; partial results if any; suggested alternatives) rather than a generic "search unavailable" string or, worse, silently returning an empty result marked as success.

**Steps:**
1. When a subagent fails, return structured context: failure type, what was attempted, any partial results, and possible alternatives — not a generic status string.
2. Distinguish "the query failed to execute" from "the query executed successfully and found nothing" — these require different coordinator responses.
3. Have subagents attempt local recovery for transient issues first; only propagate errors they genuinely can't resolve.
4. Never silently convert a failure into an apparent success (empty result marked "success"), and never kill the entire multi-agent workflow over one subagent's failure — degrade gracefully with coverage annotations instead.

**Sample Code:**
```json
// Structured failure context returned to the coordinator — NOT a generic string
{
  "status": "failed",
  "failure_type": "timeout",
  "attempted_query": "renewable energy grid infrastructure barriers 2026",
  "partial_results": [],
  "suggested_alternatives": ["retry with a narrower query", "try an alternate source"]
}
```
```python
def coordinator_handle_subagent_result(result):
    if result["status"] == "failed":
        # Degrade gracefully — annotate coverage gap, don't kill the whole workflow
        report.add_coverage_gap(topic=result["attempted_query"], reason=result["failure_type"])
    elif result["status"] == "success" and not result["data"]:
        report.add_note("No results found for this subtopic (valid empty result, not a failure).")
    else:
        report.add_findings(result["data"])
```

**Sample Question 1:** *(See official Question 8 above.)* Correct answer: return structured error context (failure type, attempted query, partial results, alternatives) to the coordinator — not a generic status, a silently-suppressed empty success, or a full workflow termination.

- **A.** Return a generic `{"status": "error"}` with no further detail.
- **B.** Return structured context: failure type, the attempted query, any partial results, and suggested alternatives.
- **C.** Silently return an empty result marked as `"success"` to avoid alarming the coordinator.
- **D.** Terminate the entire multi-agent workflow immediately.

**Correct: B.** Structured, informative failure context lets the coordinator make an appropriate recovery decision — the other options either hide information (A, C) or overreact (D).

**Sample Question 2:**
A subagent's tool call fails once due to a brief network blip, but the same call would likely succeed on an immediate retry. What should the subagent do before involving the coordinator at all?

- **A.** Immediately escalate to the coordinator with full error details.
- **B.** Attempt local recovery (e.g., a quick retry) itself; only escalate to the coordinator if local recovery genuinely fails.
- **C.** Mark the task as permanently failed with no retry.
- **D.** Silently skip the task and report success anyway.

**Correct: B.** Local recovery for transient issues should happen at the subagent level first — escalating every transient blip to the coordinator adds unnecessary overhead and noise.

**Sample Question 3:**
One of four subagents in a research pipeline fails entirely (its data source is down for the day). What is the best coordinator behavior?

- **A.** Terminate the entire multi-agent workflow since one subagent failed.
- **B.** Degrade gracefully — proceed with the other three subagents' findings and annotate the final report with a clear coverage gap for the failed subagent's topic.
- **C.** Silently omit any mention of the gap and present the report as fully comprehensive.
- **D.** Retry the failed subagent indefinitely until it succeeds, blocking the rest of the pipeline.

**Correct: B.** Graceful degradation with explicit coverage annotations is the documented pattern — killing the whole workflow (A) or silently hiding the gap (C) are both anti-patterns, and indefinite blocking retries (D) ignore that some failures (a source being down) won't resolve via retry.

---

## Task Statement 5.4 — Manage context effectively in large codebase exploration

**What it tests:** Context degradation over long sessions, scratchpad files, subagent delegation for verbose exploration, crash-recovery manifests, and `/compact`.

**Worked example:** During an hours-long codebase investigation, the agent starts referencing "typical patterns" instead of the specific classes it discovered three hours earlier — a sign of context degradation. Maintaining a scratchpad file where key findings are recorded (and referenced on later questions) counteracts this drift. For a multi-phase investigation, spawning subagents to answer specific narrow questions (e.g., "find all test files") keeps verbose discovery output out of the main agent's context, which stays focused on high-level coordination.

**Steps:**
1. Watch for signs of context degradation in long sessions (vague "typical pattern" references instead of specifics) — this signals it's time to intervene.
2. Maintain scratchpad files that record key findings, and have the agent reference them on later questions instead of re-deriving from memory.
3. Delegate verbose, narrow exploration tasks to subagents so only summaries return to the main agent.
4. For crash recovery in long multi-agent workflows, have each agent export its state to a known location (a "manifest") that the coordinator loads and re-injects on resume.
5. Use `/compact` to reduce accumulated context when a session fills up with verbose discovery output.

**Sample Code:**
```md
<!-- .claude/scratchpad/auth-investigation.md — updated as findings accumulate -->
## Key Findings
- `AuthService` (src/auth/service.ts:42) handles token refresh via `refreshToken()`.
- Sessions expire after 24h, configured in `src/config/auth.ts`.
- `AuthService` is NOT thread-safe — see the race condition noted at line 88.
```
```json
// manifest.json — crash-recovery state each agent exports to a known location
{
  "agent": "search-subagent-3",
  "status": "completed",
  "findings_path": "results/search-3.json",
  "last_updated": "2026-08-12T14:03:00Z"
}
```
```bash
# Reduce accumulated context in a long, verbose session
/compact
```

**Sample Question 1:**
During a six-hour codebase exploration session, you notice the agent has started giving vague, generic answers about "typical authentication patterns" rather than referencing the specific `AuthService` class it identified and analyzed two hours earlier. What is the most effective fix?

- **A.** Restart the session from scratch immediately.
- **B.** Maintain a scratchpad file recording key findings (like the specific `AuthService` details) that the agent references on later questions.
- **C.** Increase `max_tokens` for each response.
- **D.** Switch to a model with a larger context window and continue as normal.

**Correct: B.** This is the documented pattern for counteracting context degradation in extended sessions — persisting and re-referencing key findings rather than relying on the model's degrading working memory.

**Sample Question 2:**
A multi-agent overnight workflow occasionally crashes partway through due to infrastructure issues. When it's restarted, work already completed by earlier agents is redone from scratch, wasting hours. What's the recommended fix?

- **A.** Run the entire workflow in a single agent to avoid multi-agent coordination overhead.
- **B.** Have each agent export its state/results to a known location (a manifest) that the coordinator loads and re-injects on resume, so completed work isn't redone.
- **C.** Increase the infrastructure's uptime SLA and do nothing else.
- **D.** Disable crash recovery entirely and always restart from the beginning.

**Correct: B.** Manifests recording each agent's completed state are the documented crash-recovery pattern — this lets a resumed workflow skip already-completed work instead of redoing it.

**Sample Question 3:**
A long investigation session's context window is filling up with verbose intermediate discovery output, but the key findings so far are still valid and needed. What's the appropriate action?

- **A.** Start an entirely new session, discarding all context including the valid findings.
- **B.** Use `/compact` to reduce accumulated context while retaining what's needed, rather than starting over or leaving the bloated context as-is.
- **C.** Manually delete random messages from the conversation history.
- **D.** Switch to a smaller, faster model to compensate for the large context.

**Correct: B.** `/compact` is the documented tool for reducing accumulated context in a session that's filled up with verbose output, without losing the session's continuity the way a full restart would.

---

## Task Statement 5.5 — Design human review workflows and confidence calibration

**What it tests:** Why aggregate accuracy can mask segment-level problems, stratified sampling, field-level confidence calibration, and routing low-confidence/ambiguous cases to review.

**Worked example:** An extraction system reports 97% overall accuracy, which looks great — but broken down by document type, accuracy on hand-scanned invoices is only 78%. Stratified random sampling across document types and fields catches this before you reduce human review based on the misleading aggregate number.

**Steps:**
1. Don't trust a single aggregate accuracy number — it can mask poor performance on specific segments (document types, fields).
2. Use stratified random sampling to measure error rates across segments, and to catch novel error patterns even in the "high-confidence" bucket.
3. Have the model output field-level confidence scores, then calibrate review thresholds using a labeled validation set (not arbitrary cutoffs).
4. Route low-confidence extractions and ambiguous/contradictory source documents to human review, prioritizing limited reviewer time on the cases that need it most.
5. Validate accuracy by document type and field segment *before* reducing human review for any given segment.

**Sample Code:**
```python
# Stratified sampling — measure accuracy PER SEGMENT, not just in aggregate
segments = group_by(all_extractions, key="document_type")
accuracy_by_segment = {
    doc_type: evaluate_accuracy(sample(items, n=100))
    for doc_type, items in segments.items()
}
# {"digital_invoice": 0.98, "hand_scanned_invoice": 0.78, "email_receipt": 0.94}
# The 97% aggregate hides that hand-scanned invoices are far below target.

# Field-level confidence -> calibrated routing
if extraction["vendor_name"]["confidence"] < calibrated_threshold("vendor_name"):
    route_to_human_review(extraction, field="vendor_name")
```

**Sample Question 1:**
Your extraction system reports 97% overall accuracy, and your team is about to eliminate human review entirely to cut costs. What should you do first?

- **A.** Trust the 97% figure and proceed with removing human review.
- **B.** Analyze accuracy broken down by document type and field via stratified sampling, since aggregate accuracy can mask poor performance on specific segments.
- **C.** Increase the confidence threshold for automatic acceptance.
- **D.** Switch to a higher-tier model to push accuracy above 99%.

**Correct: B.** Aggregate accuracy is documented as potentially misleading — segment-level validation is required before removing human oversight.

**Sample Question 2:**
Your model outputs a field-level confidence score for each extracted value. How should the review-routing threshold for "send to human" be determined?

- **A.** An arbitrary round number, like 80%, chosen without further analysis.
- **B.** Calibrated against a labeled validation set, so the threshold reflects actual observed accuracy at each confidence level.
- **C.** The same fixed threshold for every field, regardless of that field's typical difficulty.
- **D.** No threshold — route every extraction to human review regardless of confidence.

**Correct: B.** Calibrating thresholds against a labeled validation set ties the routing decision to actual measured accuracy, rather than an arbitrary cutoff (A) or a one-size-fits-all rule (C) that ignores per-field variation.

**Sample Question 3:**
With limited human reviewer time available, which cases should be prioritized for review?

- **A.** A random sample of all extractions, regardless of confidence.
- **B.** Low-confidence extractions and ambiguous/contradictory source documents, since these are the cases most likely to contain actual errors.
- **C.** Only the extractions the model is most confident about, to double-check the "easy" cases.
- **D.** Extractions from the largest documents, regardless of confidence.

**Correct: B.** Prioritizing low-confidence and ambiguous cases directs limited reviewer time to where errors are most likely to occur, maximizing the value of human review.

---

## Task Statement 5.6 — Preserve information provenance and handle uncertainty in multi-source synthesis

**What it tests:** Claim-source mapping preservation through summarization, handling conflicting statistics via annotation (not arbitrary selection), temporal data requirements, and content-type-appropriate rendering.

**Worked example:** *(See official Question 9-adjacent content and Exercise 4)* — two credible sources report different adoption-rate statistics for the same technology. Rather than picking one, the synthesis output preserves both values with source attribution ("Source A reports X%; Source B reports Y%"), and the report structure explicitly separates well-established findings from contested ones.

**Steps:**
1. Require subagents to output structured claim-source mappings (source URL/name, excerpt) alongside every finding, and have downstream agents preserve — not discard — this mapping through summarization/synthesis.
2. When sources conflict, annotate the conflict with both values and their sources rather than arbitrarily picking one.
3. Require publication/collection dates in structured outputs so temporal differences aren't misread as contradictions.
4. Structure the final report to explicitly separate well-established findings from contested ones.
5. Render different content types appropriately (financial data as tables, news as prose, technical findings as structured lists) rather than flattening everything into one uniform format.

**Sample Code:**
```json
// Claim-source mapping preserved through synthesis — not discarded
{
  "claim": "technology adoption rate",
  "conflicting_reports": [
    { "value": "34%", "source": "Source A", "published": "2026-02-01" },
    { "value": "41%", "source": "Source B", "published": "2026-05-15" }
  ],
  "note": "Values differ; Source B is more recent but methodology not confirmed identical — presented as an open discrepancy, not resolved."
}
```

**Sample Question 1:**
Two credible sources in your multi-agent research report state different adoption rates for a technology — one says 34%, the other says 41% — and both appear methodologically sound. How should the synthesis agent handle this?

- **A.** Average the two values and report 37.5%.
- **B.** Select the more recent source's figure and discard the other.
- **C.** Present both values with explicit source attribution, annotating the discrepancy rather than resolving it arbitrarily.
- **D.** Omit the statistic entirely to avoid presenting conflicting information.

**Correct: C.** The correct pattern is annotated preservation of conflicting credible data — not averaging, arbitrary selection, or omission, all of which lose information the reader should have.

**Sample Question 2:**
A synthesis agent combines findings from six subagents into one report, but the final report no longer indicates which subagent/source each claim came from. What was most likely done wrong?

- **A.** The report was too long and needed more aggressive summarization.
- **B.** The claim-source mapping (source name, URL, excerpt) wasn't preserved through the summarization/synthesis step, when it should have been carried forward from each subagent's structured output.
- **C.** Too many subagents were used for this task.
- **D.** The report should have used a single subagent instead of six.

**Correct: B.** Provenance should be preserved through every synthesis step — if it disappears, the synthesis step discarded structured attribution data it should have carried forward.

**Sample Question 3:**
One source's data was collected in January and another's in June of the same year, and they show different values for a metric that's known to fluctuate seasonally. How should this be handled in the synthesis?

- **A.** Treat it as a contradiction and pick the source with the higher perceived credibility.
- **B.** Include the publication/collection dates for both sources so the reader can see this may reflect genuine temporal change rather than a true contradiction.
- **C.** Omit both values since they don't agree.
- **D.** Average the two values as if they represented the same point in time.

**Correct: B.** Requiring temporal metadata (collection/publication dates) prevents legitimate time-based differences from being misread as contradictory data — this is a distinct case from a genuine same-time-period conflict.

---

# Quick-Reference: Domain Weights

| Domain | Weight | Task Statements |
|---|---|---|
| 1. Agentic Architecture & Orchestration | 27% | 1.1–1.7 (7) |
| 2. Tool Design & MCP Integration | 18% | 2.1–2.5 (5) |
| 3. Claude Code Configuration & Workflows | 20% | 3.1–3.6 (6) |
| 4. Prompt Engineering & Structured Output | 20% | 4.1–4.6 (6) |
| 5. Context Management & Reliability | 15% | 5.1–5.6 (6) |

**Recurring exam patterns worth internalizing:**
- **Programmatic (hooks/gates) beats prompt-based** whenever the consequence of failure is financial/business-critical.
- **Root-cause diagnosis over symptom patching** — several official questions test whether you can trace a downstream symptom (bad report, misrouted tool) back to an upstream cause (coordinator scoping, tool description quality).
- **Explicit, structured, and scoped beats generic** — explicit criteria over vague confidence language; structured error metadata over generic strings; scoped tool access over "give it everything."
- **Match the tool to the constraint** — batch vs. real-time API, plan mode vs. direct execution, hooks vs. prompts — nearly every domain has a "pick the right mechanism for this constraint" question type.

**This guide now contains 30 worked examples, 30 sample-code blocks, and 90 practice questions (3 per task statement) covering all five exam domains.**

