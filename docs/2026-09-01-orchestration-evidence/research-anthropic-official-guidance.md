> UNAUDITED research sweep, captured 2026-09-01 — verify before relying.
> Produced by a parallel web-research fan-out on the night of 2026-09-01. Every claim carries the
> URL and the date the source itself showed; "undated" means the page displayed none. Source kinds are
> the researcher's own labels. The GAPS section at the end is as important as the findings: it records
> what could not be established. Nothing here has been re-checked since capture.

# Anthropic's own current, official guidance on agent and harness construction (docs.claude.com / code.claude.com, anthropic.com/engineering, claude.com/blog), focused on implementer-actionable specifics: exact flags, file conventions, topologies, and stated limits.

## F1 [high] [vendor-doc]
**CLAIM:** The Claude Code docs have MOVED off docs.claude.com. `docs.claude.com/en/docs/claude-code/*` now 301s to `code.claude.com/docs/en/*`, and `anthropic.com/engineering/claude-code-best-practices` 308s to `code.claude.com/docs/en/best-practices`. Any bookmarked docs URL or agent-fetching script pointed at the old paths needs updating; the canonical index is `https://code.claude.com/docs/llms.txt`.

**EVIDENCE:** WebFetch on https://docs.claude.com/en/docs/claude-code/sub-agents returned: "REDIRECT DETECTED... Redirect URL: https://code.claude.com/docs/en/sub-agents, Status: 301 Moved Permanently". WebFetch on the best-practices engineering post returned "Redirect URL: https://code.claude.com/docs/en/best-practices, Status: 308 Permanent Redirect". Every code.claude.com page opens with "Fetch the complete documentation index at: https://code.claude.com/docs/llms.txt".

**SRC:** https://code.claude.com/docs/en/sub-agents (undated (page); redirect observed 2026-09-01)

## F2 [high] [vendor-doc]
**CLAIM:** Subagents CAN spawn subagents — 3 layers below the main conversation by default, capped by `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (1 = disable nesting, 2 = one layer, 3 = default two layers). At the depth limit the `Agent` tool is withheld entirely (forks keep it in the list but get an error). Concurrency is capped at 20 simultaneous subagents via `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`; exceeding it returns the literal error `Concurrent subagent limit reached`. Forks and message-resumptions do not count against the concurrency cap.

**EVIDENCE:** "By default (v2.1.219+): Subagents can spawn subagents up to 3 layers below the main conversation... At the depth limit, the Agent tool is withheld (except for forks, which keep it but see errors)"; "Default: 20 concurrent subagents. When reached, spawning fails with `Concurrent subagent limit reached`... Limits only subagents spawned via Agent tool. Forks and message resumptions don't check the limit."

**SRC:** https://code.claude.com/docs/en/sub-agents (undated (versioned to Claude Code v2.1.219+))

## F3 [high] [vendor-doc]
**CLAIM:** A non-fork subagent receives ONLY: its own system prompt (not Claude Code's), the delegating prompt string, the full CLAUDE.md hierarchy, a git-status snapshot, any skills named in its `skills:` frontmatter, and (v2.1.206+) a roster of sibling agent names. It does NOT receive the parent's conversation history, the parent's system prompt, the output style, or skills already invoked in the main conversation. Implication: everything the subagent needs — file paths, error text, decisions — must be inlined into the delegation prompt.

**EVIDENCE:** Sub-agents doc: "Does NOT reach subagents: Output style; Auto memory...; Parent conversation's context window size; Conversation history (except forks); Skills already invoked in the main conversation." Agent SDK doc states it more bluntly: "The only content you pass from parent to subagent is the Agent tool's prompt string, so include any file paths, error messages, or decisions the subagent needs directly in that prompt."

**SRC:** https://code.claude.com/docs/en/agent-sdk/subagents (undated)

## F4 [high] [vendor-doc]
**CLAIM:** Subagent frontmatter now supports far more than name/description/tools/model. The full documented field set: `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation: worktree`, `color`, `initialPrompt`, `experimental` (with `cacheTtl: 5m|1h`). `isolation: worktree` runs the subagent in a temporary git worktree with enforced working-directory checks on Bash/PowerShell/Monitor.

**EVIDENCE:** Frontmatter table lists each field; `isolation` — "Set to `worktree` to run in a temporary git worktree with isolated repository copy"; `memory` — "Persistent memory scope: `user`, `project`, or `local` for cross-session learning", with `MEMORY.md` first 200 lines / 25KB auto-included in the system prompt.

**SRC:** https://code.claude.com/docs/en/sub-agents (undated)

## F5 [high] [vendor-doc]
**CLAIM:** Background subagents (now the default) get a REDUCED tool set, which silently changes what a delegated agent can do. Background subagents are limited to Read, Grep, Glob, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact, plus all MCP tools. Foreground subagents keep the full set minus core removals. All subagents lose AskUserQuestion, EndConversation, EnterPlanMode, ExitPlanMode (unless permissionMode: plan), ScheduleWakeup, TaskOutput, WaitForMcpServers, and Workflow.

**EVIDENCE:** "All subagents have a core set of tools removed automatically: Agent (at depth limit)... AskUserQuestion, EndConversation, EnterPlanMode, ExitPlanMode (unless permissionMode: plan), ScheduleWakeup, TaskOutput, WaitForMcpServers, Workflow"; "Background subagents (the default) are further limited to: [list]... Foreground subagents keep the full tool set minus the core removals."

**SRC:** https://code.claude.com/docs/en/sub-agents (undated)

## F6 [high] [vendor-doc]
**CLAIM:** You can restrict WHICH subagent types a main-thread agent may spawn using the tool-allowlist syntax `tools: Agent(worker, researcher)`. Omitting the argument list allows all types; omitting `Agent` entirely prevents spawning. `disallowedTools` is applied first, then `tools` is resolved against what remains.

**EVIDENCE:** "# Restrict spawned subagents\ntools: Agent(worker, researcher), Read, Bash — This is an allowlist; the agent can only spawn `worker` and `researcher`. Omit `Agent(...)` to allow all types or omit `Agent` entirely to prevent spawning." and "If both are set, `disallowedTools` applies first, then `tools` is resolved against the remaining pool."

**SRC:** https://code.claude.com/docs/en/sub-agents (undated)

## F7 [high] [vendor-doc]
**CLAIM:** Subagent model resolution order (as of v2.1.251) is: per-invocation `model` parameter → subagent frontmatter `model` → `CLAUDE_CODE_SUBAGENT_MODEL` env var → main conversation model. This ORDER CHANGED: before v2.1.251 the env var came first and overrode both. Extended thinking has no per-subagent control — subagents inherit the main conversation's setting (v2.1.198+).

**EVIDENCE:** "Claude Code resolves a subagent's model in this priority: 1. Per-invocation `model` parameter 2. Subagent's `model` frontmatter... 3. `CLAUDE_CODE_SUBAGENT_MODEL`... 4. Main conversation's model. Note: Before v2.1.251, `CLAUDE_CODE_SUBAGENT_MODEL` came first..."; "As of v2.1.198, subagents inherit the main conversation's extended thinking setting. There is no per-subagent thinking control."

**SRC:** https://code.claude.com/docs/en/sub-agents (undated (versioned))

## F8 [high] [vendor-doc]
**CLAIM:** For scripted/CI invocation Anthropic now recommends `claude --bare -p`, and states `--bare` will become the default for `-p`. Without `--bare`, a `-p` run loads and EXECUTES the project's `.claude/settings.json` hooks and connects `.mcp.json` servers even in a folder you have never trusted, with no trust dialog and no per-server approval prompt. `--bare` also skips OAuth/keychain credentials, so you must set `ANTHROPIC_API_KEY`.

**EVIDENCE:** "`--bare` is the recommended mode for scripted and SDK calls, and will become the default for `-p` in a future release." and "Without `--bare`, a `-p` session runs the hooks in a project's `.claude/settings.json` and connects the servers in its `.mcp.json`, even in a folder you've never trusted. A `-p` session shows no workspace trust dialog and no per-server approval prompt."

**SRC:** https://code.claude.com/docs/en/headless (undated)

## F9 [high] [vendor-doc]
**CLAIM:** `claude -p` supports schema-validated structured output: `--output-format json --json-schema '<JSON Schema>'` puts the conforming object in a `structured_output` field alongside session metadata. Invalid schemas now hard-fail with `Error: --json-schema is not a valid JSON Schema` (before v2.1.205 they were silently ignored and returned unstructured text). `format` keywords are accepted as annotations but NOT enforced.

**EVIDENCE:** "To get output conforming to a specific schema, use `--output-format json` with `--json-schema`... The response includes metadata about the request (session ID, usage, etc.) with the structured output in the `structured_output` field." ... "Before v2.1.205, Claude Code silently ignored an invalid schema and returned unstructured text, and treated any schema containing `format` as invalid."

**SRC:** https://code.claude.com/docs/en/headless (undated (versioned to v2.1.205))

## F10 [high] [vendor-doc]
**CLAIM:** In `stream-json` output, subagent messages are identified by `parent_tool_use_id` (null for the main conversation). By default only subagent `tool_use`/`tool_result` blocks are emitted; pass `--forward-subagent-text` (or `CLAUDE_CODE_FORWARD_SUBAGENT_TEXT`) to also get subagent text and thinking blocks — required to reconstruct a full subagent transcript. Nested subagents' messages only appear from v2.1.219 onward.

**EVIDENCE:** "Messages from subagents appear in the stream as `assistant` and `user` messages whose `parent_tool_use_id` field is the ID of the tool call that spawned the subagent... By default, Claude Code emits only subagent `tool_use` and `tool_result` blocks. Pass `--forward-subagent-text`... Before v2.1.219, messages from nested subagents didn't appear in the stream."

**SRC:** https://code.claude.com/docs/en/headless (undated (versioned))

## F11 [high] [vendor-doc]
**CLAIM:** Permission modes are now a seven-value set: `default`, `manual`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`. For `-p` runs the built-in starting mode is Manual on every plan, so you must pass one explicitly. `dontAsk` is the documented locked-down-CI choice: it denies anything not in `permissions.allow` or the read-only command set. `auto` runs a separate classifier model that reviews actions; on Pro/Max/Team it is the default starting mode for interactive terminal/VS Code sessions.

**EVIDENCE:** Headless doc: "For `-p`, the built-in starting permission mode is Manual on every plan, so pass the permission mode you want... `dontAsk`: Claude Code denies anything not in your `permissions.allow` rules or the read-only command set, which is useful for locked-down CI runs." Best-practices doc: "On Pro, Max, and Team plans, auto mode is the built-in starting permission mode... a separate classifier model reviews most actions instead of you and blocks only what looks risky."

**SRC:** https://code.claude.com/docs/en/headless (undated)

## F12 [high] [vendor-doc]
**CLAIM:** Dynamic Workflows are the officially recommended topology for orchestrating dozens-to-hundreds of agents, and they move the plan out of the context window into a JavaScript script the runtime executes. The script API is exactly three spawn primitives plus two display helpers: `agent(prompt, opts)` spawns one subagent, `pipeline(list, fn)` runs one per item, `parallel()` runs a set concurrently, `phase(title)` groups agents in the progress view, `log()` prints. Scripts live in `.claude/workflows/` (project) or `~/.claude/workflows/` (personal) and become `/<name>` commands; project wins on name collision.

**EVIDENCE:** "The body is plain JavaScript with top-level `await`. `agent()` spawns one subagent, `pipeline()` runs one per item in a list, and `parallel()` runs a set of agent tasks at the same time and waits for all of them." ... "A workflow script holds the loop, the branching, and the intermediate results itself, so Claude's context holds only the final answer." ... "If a project workflow and a personal workflow share a name, the project one runs."

**SRC:** https://code.claude.com/docs/en/workflows (undated (versioned to v2.1.248))

## F13 [high] [vendor-doc]
**CLAIM:** Hard, stated limits of the workflow runtime: max 16 concurrent agents (fewer on fewer CPUs), max 4,096 items per `parallel()`/`pipeline()` call (longer lists are rejected with an error, not truncated), 1,000 agents total per run, no mid-run user input, no filesystem/shell access from the script itself, and `import()` fails the run before it starts. `Date.now()`, `Math.random()`, and no-arg `new Date()` are made to THROW inside the script so a relaunched run reproduces the same agent calls — pass timestamps via `args`.

**EVIDENCE:** Behavior-and-limits table: "Up to 16 concurrent agents...", "Up to 4,096 items in a single `parallel()` or `pipeline()` call: the runtime rejects a longer list with an error", "1,000 agents total per run", "No module loading: a script that contains `import()` fails before the run starts". Plus: "Claude Code makes `Date.now()`, `Math.random()`, and a no-argument `new Date()` throw inside the script, so that a relaunched run repeats the same `agent()` calls."

**SRC:** https://code.claude.com/docs/en/workflows (undated)

## F14 [high] [vendor-doc]
**CLAIM:** Workflow resume semantics are a real footgun for cost: a failed agent mid-fan-out reruns EVERY agent that started after it, even completed ones. Stopping one agent alone (`x` in /workflows) counts as failing it. Stopping the whole run does not count any agent as failed.

**EVIDENCE:** "Failed: runs again, and so does every agent that started after it, even ones that completed. Stopping one agent alone... counts as failing. That last case means a failure in the middle of a fan-out reruns work that already finished. If a script starts A, B, C, and D in that order and B fails, relaunching returns A from cache and runs B, C, and D again."

**SRC:** https://code.claude.com/docs/en/workflows (undated)

## F15 [high] [vendor-doc]
**CLAIM:** In `claude -p` and the Agent SDK, the workflow-approval prompt never appears — the Workflow tool call goes through normal permission evaluation instead. To let a workflow launch headlessly you need one of: a `Workflow` (or `Workflow(<name>)`) allow rule, `auto` mode, `bypassPermissions`, a PreToolUse hook returning `allow`, `--permission-prompt-tool`, or an SDK `canUseTool` callback. Also: the `ultracode` keyword is deliberately INERT in `-p` prompts, SDK prompts not stamped as human, scheduled tasks, and webhook/PR-comment relays (a hardening change in v2.1.210).

**EVIDENCE:** "In `claude -p` and the Agent SDK, Claude Code never shows this prompt... **Permission rule**: `Workflow` in your allow rules approves every workflow, and `Workflow(<name>)` approves one saved workflow by name." and "It doesn't start a workflow when it reaches the session another way: a prompt passed with `-p`... a scheduled task prompt, a webhook payload or pull request comment relayed into the conversation. Before v2.1.210, the keyword started a workflow from any of these routes too."

**SRC:** https://code.claude.com/docs/en/workflows (undated (versioned to v2.1.210))

## F16 [high] [vendor-doc]
**CLAIM:** Model aliases and defaults have moved on substantially: aliases are now `fable` (Claude Fable 5 — largest, for long autonomous sessions), `best`, `opus` (Opus 5), `sonnet` (Sonnet 5), `haiku`, `opusplan` (Opus for planning, Sonnet for execution), `default`. Default model is Opus 5 on Max/Team Premium/Enterprise/API and Sonnet 5 on Pro/Team Standard. Fable 5 is NOT the default on any plan, requires v2.1.170+, is unavailable under zero data retention, and may bill to usage credits.

**EVIDENCE:** Model-config table: "`fable` | Claude Fable 5 | Largest, most complex tasks; long autonomous sessions"; "Default Model by Plan — Max, Team Premium, Enterprise, API: Opus 5; Pro, Team Standard: Sonnet 5"; "Fable 5 Availability — Not the default on any plan; Requires Claude Code v2.1.170+; Not available under zero data retention."

**SRC:** https://code.claude.com/docs/en/model-config (undated)

## F17 [high] [vendor-doc]
**CLAIM:** Effort is a first-class control with five levels (`low`, `medium`, `high`, `xhigh`, `max`) on Fable 5 / Opus 5 / Sonnet 5 / Opus 4.7-4.8, plus a sixth pseudo-level `ultracode` (= xhigh + automatic workflow orchestration). It is settable at every scope: `--effort` at launch, `/effort` in session, `CLAUDE_CODE_EFFORT_LEVEL` env, `{"effortLevel": ...}` in settings, per-model via `{"modelSettings": {"claude-opus-5": {"effortLevel": "xhigh"}}}`, per-subagent via the `effort:` frontmatter field, and per-skill via the skill's `effort:` field.

**EVIDENCE:** Model-config: "| Fable 5, Opus 5, Sonnet 5, Opus 4.8, Opus 4.7 | `low`, `medium`, `high`, `xhigh`, `max` |" and the setting examples including `{"modelSettings": {"claude-opus-5": {"effortLevel": "xhigh"}}}`. Workflows doc: "Ultracode is a Claude Code setting that combines `xhigh` reasoning effort with automatic workflow orchestration."

**SRC:** https://code.claude.com/docs/en/model-config (undated)

## F18 [high] [vendor-doc]
**CLAIM:** Anthropic explicitly tells you to REMOVE verification and re-check scaffolding from prompts when running Opus 5, because it over-verifies. Quote: "If your prompt contains explicit verification instructions ('include a final verification step for any non-trivial task,' 'use a subagent to verify'), remove them: instructions like these cause over-verification on Claude Opus 5, and removing them reduces wasted tokens with no loss in quality. The same applies to legacy harness scaffolding that adds separate verification steps." This directly contradicts harness patterns built for earlier models.

**EVIDENCE:** Direct quote from the "Task scope and over-verification" section of the Opus 5 prompting guide. Also: "Avoid instructing re-checks it already performs ('double-check your answer,' 're-verify before responding'); like verification instructions, these compound with the model's own behavior and add cost without improving results."

**SRC:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 (undated)

## F19 [high] [vendor-doc]
**CLAIM:** Opus 5 delegates to subagents MORE readily than prior models, so Anthropic ships a copy-pasteable delegation-suppression instruction plus deterministic caps. Claude Code adds its own suppression line automatically ONLY when you use the `claude_code` system-prompt preset; with `--system-prompt` (custom) or no systemPrompt in the SDK, that line is absent and you must add it yourself. Caps require Claude Code 2.1.217+.

**EVIDENCE:** Verbatim recommended instruction: "Delegate to a subagent only for large tasks that are genuinely independent and parallelizable, such as a wide multi-file investigation. Do not delegate work you can finish yourself in a handful of tool calls, and do not use subagents to verify or double-check your own work. If one subagent can complete the task, use one rather than several, and keep spawn counts low." Plus: "Claude Code adds a delegation instruction of its own on Claude Opus 5 only when you use its `claude_code` system prompt preset; with a custom or omitted system prompt, add a delegation instruction such as the example in this section yourself."

**SRC:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 (undated)

## F20 [high] [vendor-doc]
**CLAIM:** For Opus 5 with thinking disabled, Anthropic documents two concrete failure artifacts that break agent loops: (1) the model writes a tool call as user-facing TEXT instead of a `tool_use` block — the call never runs and the leaked text poisons subsequent turns; (2) `<thinking>` or other internal XML tags leak into visible output, made WORSE by system-prompt rules telling the model not to think. Recommended mitigation is to keep thinking on and use low effort instead: "for most tasks, thinking enabled at `low` effort performs better than thinking disabled at similar cost."

**EVIDENCE:** "**Tool calls as text.** With thinking disabled, the model occasionally writes a tool call into its user-facing text instead of emitting a structured `tool_use` block. The turn completes normally and the call never runs, and in agentic loops the leaked text stays in the conversation history... If your system prompt contains a rule instructing the model not to think or not to reason, remove it; that kind of instruction increases tag leakage."

**SRC:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 (undated)

## F21 [high] [vendor-doc]
**CLAIM:** Skill frontmatter has grown well past name/description. Documented fields include `when_to_use`, `arguments`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context: fork`, `agent`, `background`, `hooks`, `paths` (globs limiting auto-activation), `shell`, `user-invocable`, `disable-model-invocation`, `metadata`, `license`, `compatibility`. Hard limit worth designing around: the combined `description` + `when_to_use` text is TRUNCATED AT 1,536 CHARACTERS in the skill listing — put the key use case first.

**EVIDENCE:** "`description` ... Put the key use case first: the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing to reduce context usage." `context` — "Set to `fork` to run in a forked subagent context." `paths` — "Glob patterns that limit when this skill is activated... Claude loads the skill automatically only when working with files matching the patterns."

**SRC:** https://code.claude.com/docs/en/skills (undated (versioned to v2.1.248))

## F22 [high] [vendor-doc]
**CLAIM:** Skill precedence is the OPPOSITE of subagent precedence, which is an easy estate-wide bug: for skills, personal `~/.claude/skills/` beats project `.claude/skills/`; for subagents, project `.claude/agents/` beats user `~/.claude/agents/`. Also: custom commands have been MERGED into skills — `.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both create `/deploy`, and on a name collision the skill wins.

**EVIDENCE:** Skills doc: "For example, with a `deploy` skill in both `~/.claude/skills/` and your project's `.claude/skills/`, `/deploy` runs the personal one." Sub-agents doc priority order: "3. `.claude/agents/` - Current project; 4. `~/.claude/agents/` - All your projects (user-level)... Claude Code uses the one from the highest-priority location." Skills doc: "Custom commands have been merged into skills... if a skill and a command share the same name, the skill takes precedence."

**SRC:** https://code.claude.com/docs/en/skills (undated)

## F23 [high] [vendor-doc]
**CLAIM:** Hooks are now a ~33-event lifecycle, far beyond the classic PreToolUse/PostToolUse/Stop set — including `PermissionRequest`, `PermissionDenied`, `PostToolUseFailure`, `PostToolBatch`, `StopFailure`, `SubagentStart`/`SubagentStop`, `PreModelSwitch`/`PostModelSwitch`, `PreCompact`/`PostCompact`, `InstructionsLoaded`, `ConfigChange`, `WorktreeCreate`/`WorktreeRemove`, `TeammateIdle`. Handlers are no longer shell-only: types are `command`, `http`, `mcp_tool`, `prompt` (LLM evaluation), and `agent` (subagent evaluation, experimental). Exit code 2 blocks — but explicitly does NOT block on PermissionRequest, StopFailure, PostToolUse, or PostToolUseFailure.

**EVIDENCE:** Hook events table lists all events with cadence; handler-type table lists "`command` | Shell command", "`http` | HTTP POST endpoint", "`mcp_tool` | MCP server tool call", "`prompt` | LLM evaluation", "`agent` | Subagent evaluation (experimental)". Exit-code table: "`2` | Blocking error | Blocks the action (except on PermissionRequest, StopFailure, PostToolUse, PostToolUseFailure)".

**SRC:** https://code.claude.com/docs/en/hooks (undated)

## F24 [high] [vendor-doc]
**CLAIM:** A Stop hook is the documented deterministic gate for unattended runs, but it has a stated escape hatch: "Claude Code overrides the hook and ends the turn after 8 consecutive blocks." So a Stop-hook verification gate cannot hold a turn open indefinitely — design for at most 8 forced iterations.

**EVIDENCE:** Best-practices doc, 'Give Claude a way to verify its work': "**As a deterministic gate**: a Stop hook runs your check as a script and blocks the turn from ending until it passes. Claude Code overrides the hook and ends the turn after 8 consecutive blocks."

**SRC:** https://code.claude.com/docs/en/best-practices (undated)

## F25 [high] [vendor-doc]
**CLAIM:** Subagent output is now sanitized against prompt injection (v2.1.210+): Claude Code inserts backslashes into imitation control tags (`<system-reminder>`, `Human:`, `Assistant:`) and prepends a `[harness: ...]` marker line for control-tag or permission-config matches. Nothing is removed or reworded. If you parse subagent output programmatically, expect these mutations.

**EVIDENCE:** "Subagent output is scanned for instruction-shaped content. Backslashes inserted into imitation tags (`<system-reminder>`, `Human:`, `Assistant:`). Marker lines prepended for instruction-like content. No content is removed or reworded; changes are preventive only."

**SRC:** https://code.claude.com/docs/en/sub-agents (undated (versioned to v2.1.210))

## F26 [high] [vendor-blog]
**CLAIM:** Anthropic's own long-running-agent harness convention is concrete and copyable: an INITIALIZER prompt (different from the continuation prompt) that creates `init.sh`, `claude-progress.txt`, an initial git commit, and a JSON feature list with fields `category`/`description`/`steps`/`passes`; then a CODING-AGENT continuation prompt that runs `pwd`, reads git log + progress file, picks ONE incomplete feature, starts the dev server via init.sh, smoke-tests, implements, browser-tests, commits, updates the progress file. Stated rule: "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality." Their claude.ai-clone example needed "over 200 features."

**EVIDENCE:** "The initial prompt creates foundational infrastructure: init.sh script; claude-progress.txt file; Initial git commit; Feature list (JSON) — comprehensive requirements marked initially as 'failing'." JSON structure listed as category / description / steps / passes.

**SRC:** https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents (November 26, 2025)

## F27 [high] [vendor-blog]
**CLAIM:** Anthropic's own 2026 harness experiment landed on a three-agent planner/generator/evaluator topology with file-based handoffs and negotiated 'sprint contracts' (generator and evaluator agree on testable done-criteria BEFORE coding), the evaluator driving the running app via Playwright MCP. Measured cost/quality delta on the same task: solo agent 20 min / $9 with broken input wiring vs full harness 6 hours / $200 producing a working game. A DAW build ran 3h50m / $124.70 (planner 4.7 min / $0.46). Critically, they report that upgrading the model from Opus 4.5 to Opus 4.6 let them DELETE sprint decomposition and context resets entirely — "harness complexity should decrease as model capabilities improve."

**EVIDENCE:** "Retro Game Maker Example: Solo agent: 20 minutes, $9 cost; Full harness: 6 hours, $200 cost... The original harness (Opus 4.5) required context resets between sessions due to 'context anxiety.' The updated version using Opus 4.6 eliminated sprint decomposition entirely, maintaining coherence for 2+ hours without resets."

**SRC:** https://www.anthropic.com/engineering/harness-design-long-running-apps (March 24, 2026)

## F28 [high] [vendor-blog]
**CLAIM:** Anthropic's newest architectural position (April 2026) is that harnesses are the thing that goes stale, and the durable abstraction is a decoupled brain (Claude + harness) / hands (sandboxes + tools) / session (durable event log). The named interfaces are `emitEvent(id, event)`, `getSession(id)`, `getEvents()` (positional slices of the event stream), `wake(sessionId)`, `execute(name, input) -> string` for all container tools, and `provision({resources})`. Deferring container provisioning until actually needed improved TTFT ~60% at p50 and >90% at p95. The session log is explicitly "a context object external to Claude's context window."

**EVIDENCE:** "Session Management: `emitEvent(id, event)` – write durable records; `getSession(id)`; `getEvents()`... `wake(sessionId)` – restart a harness from stored state; Container tools: `execute(name, input) → string`... time-to-first-token (TTFT) improved by roughly 60% at p50 and over 90% at p95 by deferring container provisioning until actually needed."

**SRC:** https://www.anthropic.com/engineering/managed-agents (April 8, 2026)

## F29 [medium] [vendor-blog]
**CLAIM:** The canonical multi-agent research numbers, still the only published Anthropic figures for orchestrator-worker research: agents use ~4x the tokens of chat, multi-agent systems ~15x; token usage alone explains 80% of performance variance and token count + tool-call count + model choice explain 95%; Opus 4 orchestrator with Sonnet 4 subagents beat single-agent Opus 4 by 90.2% on their internal research eval. Subagents return condensed summaries of ~1,000–2,000 tokens. Note this is dated June 2025 — 15 months stale as of Sept 2026 and predates Opus 5, so treat the ratios as directional.

**EVIDENCE:** "Standard agent interactions consume approximately 4× more tokens than chat interactions; Multi-agent systems use roughly 15× more tokens than standard chats; Token usage alone explains 80% of performance variance... achieved 90.2% performance gains over single-agent Claude Opus 4." The 1,000–2,000 token figure is from the context-engineering post (Sept 29, 2025).

**SRC:** https://www.anthropic.com/engineering/multi-agent-research-system (June 13, 2025)

## F30 [high] [vendor-blog]
**CLAIM:** The MCP tool-definition bloat problem has an official answer: expose MCP servers as a FILESYSTEM of typed code modules (`servers/<service>/<tool>.ts` + `index.ts`) that the agent discovers and imports on demand, writing code to orchestrate calls and filter data in the execution environment rather than passing every intermediate result through context. Anthropic's worked example: 150,000 tokens down to 2,000 — a claimed 98.7% saving.

**EVIDENCE:** "This reduces the token usage from 150,000 tokens to 2,000 tokens—a time and cost saving of 98.7%." Directory shape given as servers/google-drive/getDocument.ts, servers/salesforce/updateRecord.ts, with "a shared `callMCPTool` function".

**SRC:** https://www.anthropic.com/engineering/code-execution-with-mcp (November 4, 2025)

## F31 [high] [vendor-blog]
**CLAIM:** Concrete tool-writing rules an implementer can apply directly: consolidate rather than wrap APIs (ship `schedule_event` instead of `list_users` + `list_events` + `create_event`); namespace by service and resource (`asana_search`, `asana_projects_search`); expose a `response_format` enum with `"concise"` / `"detailed"`; implement pagination/filtering/truncation with sane defaults — Claude Code itself caps tool responses at 25,000 tokens; return semantic identifiers not opaque IDs; make errors actionable instructions rather than tracebacks; use unambiguous parameter names (`user_id`, not `user`).

**EVIDENCE:** "Instead of implementing a `list_users`, `list_events`, and `create_event` tools, consider implementing a `schedule_event` tool which finds availability and schedules an event." ... "You can enable both by exposing a simple `response_format` enum parameter in your tool, allowing your agent to control whether tools return `"concise"` or `"detailed"` responses." ... "Claude Code restricts responses to 25,000 tokens by default."

**SRC:** https://www.anthropic.com/engineering/writing-tools-for-agents (September 11, 2025)

## F32 [high] [vendor-doc]
**CLAIM:** Prompt caching is a real lever in fan-outs and has a non-obvious default: workflow/subagent requests fall OUTSIDE the main conversation's cache TTL bucket and hold for only 5 minutes by default, even on a subscription. Set `subagentPromptCacheTtl: "1h"` to extend it (billed at a higher 1-hour write rate). Claude Code also staggers matching sibling agents up to `CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS` (default 5000) so all but the first read the shared cached prefix; set 0 to disable. Two agents share a prefix only when model, effort, agent type, tools, output schema, and working directory all match.

**EVIDENCE:** "A workflow agent's requests fall outside the main conversation's cache TTL bucket, so its cache holds for five minutes by default, including on a Claude subscription. To keep it for an hour, set `subagentPromptCacheTtl` to `1h`." ... "Claude Code caps the hold at `CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS` milliseconds, `5000` by default."

**SRC:** https://code.claude.com/docs/en/workflows (undated)

## F33 [high] [vendor-doc]
**CLAIM:** Output styles are current, not deprecated — but the `/output-style` command was removed in v2.1.91; you now set `outputStyle` in a settings file or via `/config`. There are five built-ins (Default, Proactive, Concise, Explanatory, Learning). Key harness fact: a custom output style REMOVES Claude Code's built-in software-engineering instructions unless you set `keep-coding-instructions: true`, and output styles apply to the main conversation only — subagents run their own system prompt and are unaffected (forks are the exception).

**EVIDENCE:** "The standalone `/output-style` command was deprecated in v2.1.73 and removed in v2.1.91." ... "Custom output styles leave out Claude Code's built-in software engineering instructions... unless `keep-coding-instructions` is set to `true`." ... "Output styles apply to the main conversation only: a subagent runs its own system prompt, so styles don't change how subagents respond. A fork is the exception."

**SRC:** https://code.claude.com/docs/en/output-styles (undated (versioned to v2.1.237))

## F34 [high] [vendor-doc]
**CLAIM:** The Agent SDK's documented cost/blast-radius controls for a spawning tree are exactly three: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (default 3), `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (default 20), and `maxBudgetUsd` / `max_budget_usd` (no default). At the budget cap the SDK refuses new spawns with `Budget limit reached`, stops running background subagents, and ends the query with result subtype `error_max_budget_usd`. TypeScript's `env` option REPLACES the subprocess environment (spread `process.env`); Python's MERGES into it.

**EVIDENCE:** Limits table plus: "Enforces the cap in three ways: refuses to spawn more subagents, returning `Budget limit reached`, stops background subagents that are still running, and ends the query with the `error_max_budget_usd` result subtype." And "the TypeScript SDK replaces the subprocess environment with it, so spread `process.env` into it to keep variables like `PATH`, while the Python SDK merges it into the inherited environment."

**SRC:** https://code.claude.com/docs/en/agent-sdk/subagents (undated (TS SDK v0.3.219 / Python v0.2.127 and later))

## F35 [high] [vendor-doc]
**CLAIM:** The Agent SDK is Python + TypeScript ONLY; Anthropic's official cross-language answer is to shell out to the CLI: "To drive the same agent loop from another language, run the CLI as a subprocess with the `-p` flag and `--output-format json`." It also carries a licensing constraint most implementers miss: "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK" — use API keys. And branding: "Claude Code" / "Claude Code Agent" are not permitted product names.

**EVIDENCE:** Direct quotes from the Agent SDK overview page, sections 'Compare the Agent SDK to other Claude tools', the authentication Note, and 'Branding guidelines'.

**SRC:** https://code.claude.com/docs/en/agent-sdk/overview (undated)

## F36 [high] [vendor-blog]
**CLAIM:** Anthropic's own agent-loop framing for SDK builders is gather context → take action → verify work, with a stated tool-selection hierarchy: custom TOOLS for primary/frequent actions (most prominent in context), BASH for ad-hoc general-purpose access, CODE GENERATION when precision and reuse matter ("Code is precise, composable, and infinitely reusable"), MCP for standardized third-party integrations. On verification they rank rules-based feedback (linting) and visual feedback above LLM-as-judge, which they call "generally not very robust." They also advise starting with agentic search (grep/tail) over semantic search, which is "less accurate, more difficult to maintain, and less transparent."

**EVIDENCE:** "Semantic search... is 'less accurate, more difficult to maintain, and less transparent.' The SDK recommends starting with agentic search first." And the verification list: "Rules-based feedback: 'Code linting is an excellent form of rules-based feedback'... LLM-as-judge: Another model evaluates output against fuzzy criteria (though 'generally not very robust')."

**SRC:** https://claude.com/blog/building-agents-with-the-claude-agent-sdk (September 29, 2025)

## F37 [medium] [vendor-blog]
**CLAIM:** The original 'Building Effective AI Agents' taxonomy (prompt chaining, routing, parallelization/sectioning+voting, orchestrator-workers, evaluator-optimizer; workflows = predefined code paths, agents = model directs itself) is now 20+ months old (Dec 19, 2024) and predates every current Anthropic harness position. Its core advice still holds and is echoed in the 2026 posts — start simple, add complexity only when it demonstrably improves outcomes, spend more time on the agent-computer interface than the prompt — but treat its patterns as vocabulary, not as current architecture guidance; the 2026 successor positions are the dynamic-workflow patterns (classify-and-act, fan-out-and-synthesize, adversarial verification, generate-and-filter, tournament, loop-until-done).

**EVIDENCE:** Building Effective Agents (Dec 19, 2024): "You should consider adding complexity only when it demonstrably improves outcomes" and "actually spent more time optimizing our tools than the overall prompt." Dynamic workflows post (June 2, 2026) enumerates "six composable patterns: Classify-and-act, Fan-out-and-synthesize, Adversarial verification, Generate-and-filter, Tournament, Loop until done."

**SRC:** https://www.anthropic.com/engineering/building-effective-agents (December 19, 2024)

## F38 [high] [vendor-doc]
**CLAIM:** For an implementer choosing a topology, the docs give an explicit four-way decision table keyed on WHO HOLDS THE PLAN: subagents (Claude decides turn by turn, results in context, a few per turn), skills (Claude follows instructions, results in context), agent teams (a lead agent supervising peer sessions, shared task list, a handful of long-running peers), workflows (a script decides, results in script variables, dozens-to-hundreds of agents per run, resumable). Interruption behavior differs too: subagents/skills restart the turn; teammates keep running; workflows resume in the same session.

**EVIDENCE:** The comparison table in the workflows doc, columns 'Who decides what runs next', 'Where intermediate results live', 'Scale', 'Interruption' — e.g. "Workflows | A script the runtime executes | The script | Script variables | The orchestration itself | Dozens to hundreds of agents per run | Resumable in the same session".

**SRC:** https://code.claude.com/docs/en/workflows (undated)

## F39 [high] [vendor-blog]
**CLAIM:** Anthropic's current context-engineering doctrine names six named techniques an implementer can implement directly: system-prompt 'altitude' (between brittle hardcoded logic and vague guidance), lean self-contained tools, a few canonical few-shot examples rather than exhaustive edge cases, just-in-time retrieval via lightweight identifiers (file paths, queries, links) instead of pre-loading, compaction (preserve architectural decisions / unresolved bugs / implementation details; discard redundant tool output), and structured note-taking to a file outside the context window. The motivating mechanism is 'context rot' — recall degrades as the window fills, because n tokens create n² pairwise relationships.

**EVIDENCE:** "context rot: as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases" ... transformers create "n² pairwise relationships for n tokens"; just-in-time retrieval keeps "lightweight identifiers (file paths, stored queries, web links, etc.)"; compaction preserves "architectural decisions, unresolved bugs, and implementation details."

**SRC:** https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (September 29, 2025)


## GAPS
- Almost every code.claude.com doc page is UNDATED — they carry Claude Code version stamps (v2.1.xxx) instead. I could not establish a last-updated date for the subagents, skills, hooks, workflows, model-config, headless, or best-practices pages, so 'currency' is inferred from the version numbers they cite (up to v2.1.251), not from a stated date.
- No published Anthropic benchmark or token-cost figure for the CURRENT (Opus 5 / Fable 5 / dynamic workflow) multi-agent topology. The only quantified multi-agent numbers (4x / 15x tokens, 90.2% gain, 80% variance) are from June 2025 and describe Opus 4 + Sonnet 4 — 15 months stale and pre-dating both the Workflow tool and Opus 5's changed delegation behavior.
- Anthropic gives no guidance on when a dynamic workflow beats an agent team beats plain subagents in terms of COST for a given task size — only a qualitative 'who holds the plan' table and a soft `workflowSizeGuideline` (small <5 / medium <15 / large <50 agents). No published cost-per-topology comparison.
- The exact semantics of Fable 5 vs Opus 5 for agentic coding are thinly documented: model-config says Fable is for 'long autonomous sessions' and 'sustains context', and that its thinking cannot be disabled, but there is no published Fable 5 prompting guide equivalent to the Opus 5 one, and no benchmark comparison I could fetch.
- I did not verify the `--advisor`, `--teammate-mode`, `--channels`, or agent-teams surfaces beyond the CLI flag table; agent teams are described as 'experimental and disabled by default' with no fetched detail page, so their topology, messaging protocol, and limits are unresolved here.
- No official guidance found on evaluating or testing a harness itself (as opposed to tools or skills). The multi-agent post's eval advice (start with ~20 queries, LLM-as-judge on a 0.0-1.0 rubric) is the only published methodology and it is from June 2025; the 2026 harness posts describe evaluator agents but publish no eval harness.
- Whether the `claude_code` system-prompt preset's automatic Opus 5 delegation-suppression line is present in `--bare -p` runs, and what it says verbatim, is not documented on any page I fetched.

## SOURCES
- https://www.anthropic.com/engineering/building-effective-agents
- https://www.anthropic.com/engineering/writing-tools-for-agents
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- https://www.anthropic.com/engineering/harness-design-long-running-apps
- https://www.anthropic.com/engineering/managed-agents
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- https://www.anthropic.com/engineering/code-execution-with-mcp
- https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code
- https://claude.com/blog/building-agents-with-the-claude-agent-sdk
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/cli-reference
- https://code.claude.com/docs/en/model-config
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/best-practices
- https://code.claude.com/docs/en/workflows
- https://code.claude.com/docs/en/output-styles
- https://code.claude.com/docs/en/agent-sdk/overview
- https://code.claude.com/docs/en/agent-sdk/subagents
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5
