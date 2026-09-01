> UNAUDITED research sweep, captured 2026-09-01 — verify before relying.
> Produced by a parallel web-research fan-out on the night of 2026-09-01. Every claim carries the
> URL and the date the source itself showed; "undated" means the page displayed none. Source kinds are
> the researcher's own labels. The GAPS section at the end is as important as the findings: it records
> what could not be established. Nothing here has been re-checked since capture.

# OpenAI Codex — current capability, CLI mechanics, and comparative fit vs Claude models (September 2026)

## F1 [high] [vendor-doc]
**CLAIM:** OpenAI moved the Codex docs off developers.openai.com — every /codex/* URL now 308-redirects to learn.chatgpt.com. Any bookmark, skill, or script pinning developers.openai.com/codex/cli/reference is following a redirect.

**EVIDENCE:** WebFetch of https://developers.openai.com/codex/cli/reference returned 'REDIRECT DETECTED ... Redirect URL: https://learn.chatgpt.com/docs/developer-commands?surface=cli, Status: 308 Permanent Redirect'. Same for /codex/config-basic → learn.chatgpt.com/docs/config-file/config-basic and /codex/mcp → learn.chatgpt.com/docs/extend/mcp?surface=cli.

**SRC:** https://learn.chatgpt.com/docs/developer-commands?surface=cli (undated)

## F2 [high] [vendor-doc]
**CLAIM:** The headless invocation is `codex exec` (alias `codex e`). Its documented flags: --model/-m, --oss, --local-provider (lmstudio|ollama), --sandbox/-s (read-only|workspace-write|danger-full-access), --ask-for-approval/-a (untrusted|on-request|never), --dangerously-bypass-approvals-and-sandbox (alias --yolo), --json/--experimental-json, --output-last-message/-o PATH, --output-schema PATH, -c/--config key=value (repeatable), --profile/-p, --cd/-C, --image/-i, --color, --ephemeral, --skip-git-repo-check, --add-dir, --search, --enable/--disable <feature>, --ignore-rules. PROMPT accepts `-` for stdin.

**EVIDENCE:** Vendor reference: 'Run Codex non-interactively. Alias: codex e. Stream results to stdout or JSONL and optionally resume previous sessions.' Exact entries quoted include '--output-schema | path | JSON Schema file describing the expected final response shape. Codex validates tool output against it.' and '--ask-for-approval, -a | untrusted | on-request | never'.

**SRC:** https://learn.chatgpt.com/docs/developer-commands?surface=cli (undated)

## F3 [high] [vendor-doc]
**CLAIM:** `--full-auto` is now deprecated in favor of `--sandbox workspace-write`, and Codex prints a warning when it is used. Scripts still passing --full-auto should be migrated.

**EVIDENCE:** Reference entry quoted verbatim: '--full-auto | boolean | Deprecated compatibility flag. Prefer `--sandbox workspace-write`; Codex prints a warning when this flag is used.'

**SRC:** https://learn.chatgpt.com/docs/developer-commands?surface=cli (undated)

## F4 [medium] [forum-or-practitioner]
**CLAIM:** Session continuation exists in headless mode: `codex exec resume [SESSION_ID]`, with `--last` (most recent session in cwd) and `--all` (include sessions outside cwd). But `--ephemeral` runs cannot be resumed — attempting to resume an ephemeral thread_id silently starts a NEW session rather than erroring.

**EVIDENCE:** Vendor reference lists 'codex exec resume [SESSION_ID]', '--last', '--all'. Independent flag-testing gist: 'Ephemeral sessions cannot be resumed. Using --ephemeral prevents session file persistence, and attempting resume <thread_id> silently creates a new session instead of failing or continuing the old conversation.'

**SRC:** https://gist.github.com/alexfazio/359c17d84cb6a5af12bac88fa1db9770 (2026-03-13 (CLI v0.114.0))

## F5 [medium] [forum-or-practitioner]
**CLAIM:** stdin handling is a trap: if you pass BOTH a prompt argument and piped stdin, the prompt argument wins and stdin is discarded. `cat file.py | codex exec "review this"` silently reviews nothing. Use `codex exec -` or a heredoc.

**EVIDENCE:** 'When both a prompt argument and stdin are provided, the prompt argument takes precedence; stdin is ignored. The article's pattern `cat file.py | codex exec "review this code"` fails—use heredoc or pipe-to-dash syntax instead.'

**SRC:** https://gist.github.com/alexfazio/359c17d84cb6a5af12bac88fa1db9770 (2026-03-13 (CLI v0.114.0))

## F6 [medium] [forum-or-practitioner]
**CLAIM:** `--json` emits a stable four-event JSONL sequence — thread.started (carries thread_id), turn.started, item.completed (agent message), turn.completed (input_tokens, cached_input_tokens, output_tokens). That makes token accounting and session-id capture scriptable without parsing prose.

**EVIDENCE:** 'The output follows a predictable four-event sequence: 1. thread.started (contains thread_id) 2. turn.started 3. item.completed (agent message text) 4. turn.completed (token usage: input_tokens, cached_input_tokens, output_tokens).'

**SRC:** https://gist.github.com/alexfazio/359c17d84cb6a5af12bac88fa1db9770 (2026-03-13 (CLI v0.114.0))

## F7 [medium] [forum-or-practitioner]
**CLAIM:** Structured output via --output-schema is real but brittle: the schema must set additionalProperties:false and list ALL properties in `required` or the API 400s; and there is a filed (now closed) bug where --json and --output-schema were silently ignored whenever MCP servers/tools were active, yielding unparseable near-JSON.

**EVIDENCE:** Gist: 'The --output-schema flag requires additionalProperties: false and ALL properties in the required array.' Issue #15451 (codex-cli 0.116.0): '--json and --output-schema are silently ignored when tools/MCP servers are active, resulting in malformed outputs' — output came back as `status: "UNSURE"` / `score: 6.5` instead of a JSON object.

**SRC:** https://github.com/openai/codex/issues/15451 (2026-03-22)

## F8 [medium] [forum-or-practitioner]
**CLAIM:** Approval policy is partly inert in exec mode: with no TTY, `-a on-request` was observed to silently degrade to `never`. Sandbox mode is therefore the only real blast-radius control in headless runs — set it explicitly rather than relying on approvals.

**EVIDENCE:** 'Setting -a on-request or approval_policy=on-request silently becomes approval: never in exec mode, since there's no TTY for user prompts.' Also: 'Using --full-auto --sandbox read-only results in workspace-write sandbox—the composite flag acts as an atomic override.'

**SRC:** https://gist.github.com/alexfazio/359c17d84cb6a5af12bac88fa1db9770 (2026-03-13 (CLI v0.114.0))

## F9 [medium] [vendor-doc]
**CLAIM:** config.toml lives at ~/.codex/config.toml (user) and .codex/config.toml (project). Documented keys include model, model_reasoning_effort, sandbox_mode, approval_policy, web_search (cached|indexed|live|disabled), personality (friendly|pragmatic|none), log_dir. sandbox_mode now documents `elevated`/`unelevated` in addition to workspace-write and danger-full-access, and there are built-in permission profiles `:read-only`, `:workspace`, `:danger-full-access` plus custom `[permissions.<name>]` tables.

**EVIDENCE:** Vendor config page: sandbox_mode allowed values 'workspace-write', 'danger-full-access', 'elevated', 'unelevated'; approval_policy 'untrusted', 'on-request', 'never'; 'Built-in permission profiles: :read-only, :workspace, :danger-full-access. Custom profiles use [permissions.<name>] table syntax.'

**SRC:** https://learn.chatgpt.com/docs/config-file/config-basic (undated)

## F10 [high] [vendor-doc]
**CLAIM:** Current Codex model IDs are gpt-5.6-sol (flagship), gpt-5.6-terra (balanced), gpt-5.6-luna (cheap/fast), plus gpt-5.3-codex-spark (Pro-only research preview for near-instant iteration). gpt-5.4 and gpt-5.4-mini retire 2026-08-31 — i.e. yesterday relative to today. gpt-5.5 remains as previous generation.

**EVIDENCE:** Vendor models page table: 'gpt-5.6-sol — Flagship GPT-5.6 model with the strongest capability for complex coding, computer use, research, and cybersecurity'; 'gpt-5.3-codex-spark — Text-only research preview model optimized for near-instant, real-time coding iteration' (Pro users, desktop/CLI/IDE only); 'gpt-5.4 (retiring August 31, 2026)'.

**SRC:** https://learn.chatgpt.com/docs/models.md (undated)

## F11 [medium] [vendor-doc]
**CLAIM:** Reasoning-effort naming is currently inconsistent across OpenAI's own surfaces — the models page lists Light/Low, Medium, High, Extra High, Max, Ultra, while third-party config references still document the older enum minimal|low|medium|high|xhigh. Do not hardcode an effort string without checking `codex --help` on the installed version.

**EVIDENCE:** Vendor models page: 'The document mentions: Light/Low, Medium, High, Extra High, Max, and Ultra modes.' Third-party config reference: 'model_reasoning_effort has five settings: minimal, low, medium, high, or xhigh.'

**SRC:** https://learn.chatgpt.com/docs/models.md (undated)

## F12 [medium] [third-party-commentary]
**CLAIM:** Effective context in Codex is far below the model's advertised window: a 400,000-token cap composed of 272,000 input + 128,000 reserved output, of which ~258,000 input is usable after ~5% CLI headroom. The Codex-side input allowance was cut from 372K to 272K.

**EVIDENCE:** 'Advertised: GPT-5.5's context window is 1,050,000 tokens ... In Codex: 400,000-token cap (272,000 input + 128,000 reserved output). Usable: roughly 258,000 input tokens after the CLI maintains about 5% headroom.' Separately: 'OpenAI Codex Cuts GPT-5.6 Context Window From 372K to 272K'.

**SRC:** https://getunblocked.com/blog/codex-context-window/ (2026-07-03)

## F13 [high] [vendor-doc]
**CLAIM:** ChatGPT-plan quota is metered on a 5-hour rolling window SHARED across CLI local messages, IDE requests and Codex cloud tasks, with a separate weekly cap layered on top. Since April 2026 Plus/Pro meter by tokens rather than messages, so heavy requests drain the window faster. Check remaining budget with /status in the CLI.

**EVIDENCE:** Vendor pricing page: 'On ChatGPT plans, local messages and cloud chats share a five-hour window.' Third-party: 'Codex meters subscription usage on a 5-hour rolling window with a separate weekly cap on top ... Since April 2026 those plans meter by tokens, not messages.'

**SRC:** https://learn.chatgpt.com/docs/pricing.md (page references promotions through 2026-11-21)

## F14 [high] [vendor-doc]
**CLAIM:** Per-5-hour-window local message allowances (ranges, model-dependent): Plus gets 10–100 on GPT-5.6 Sol, 25–200 on Terra, 250–2,000 on Luna; Pro 5x and Pro 20x multiply those 5x/20x; Business matches Plus per seat. Credit metering runs 100/500 per M tokens (in/out) for Sol, 50/300 Terra, 5/30 Luna, and 'GPT-5.6 usage averages 5-30 credits per message'. API key usage is separate pay-as-you-go.

**EVIDENCE:** Vendor pricing table reproduced: 'GPT-5.6 Sol | 10-100 | 50-500 | 200-2,000 | 10-100'; 'GPT-5.6 Sol | 100 | 10 | 500' credits per M tokens; 'GPT-5.6 usage averages 5-30 credits per message'; 'API key: Pay-as-you-go based on token consumption'.

**SRC:** https://learn.chatgpt.com/docs/pricing.md (page references promotions through 2026-11-21)

## F15 [medium] [vendor-doc]
**CLAIM:** Codex is an MCP client, not an MCP server. Servers are declared as [mcp_servers.<name>] in config.toml (stdio needs `command`, streamable-HTTP needs `url`), managed via `codex mcp add|list|login`, with bearer-token / static-header / OAuth / ChatGPT-session auth. As of 0.152.0 server names may contain ':', '@', '/', '.', and individual tools take an `output_token_limit`.

**EVIDENCE:** Vendor MCP doc: 'MCP servers are configured in ~/.codex/config.toml using [mcp_servers.<server-name>] tables. STDIO servers require a command field; HTTP servers require a url field.' 'The documentation focuses on Codex consuming MCP servers rather than functioning as one. Codex is an MCP client, not a server itself.' Release 0.152.0: 'MCP server names can now include ":", "@", "/", and "."' and 'Individual MCP tools support configurable output_token_limit settings'.

**SRC:** https://learn.chatgpt.com/docs/extend/mcp?surface=cli (undated)

## F16 [high] [vendor-doc]
**CLAIM:** Latest Codex CLI is 0.152.0, released 2026-09-01 (today). Breaking behavior change: the planning tool is now DISABLED by default and must be re-enabled with `tools.update_plan.enabled = true`. Any workflow that relied on Codex emitting a plan will silently stop doing so after upgrade.

**EVIDENCE:** GitHub releases: '0.152.0 (September 1, 2026) ... Important Change: "The planning tool is disabled by default; enable it with tools.update_plan.enabled = true" (#41744)'. Also in 0.152.0: 'Configurable timeouts for thread shell commands, including deadlines over one hour.'

**SRC:** https://github.com/openai/codex/releases (2026-09-01)

## F17 [high] [third-party-commentary]
**CLAIM:** OpenAI deliberately did NOT publish SWE-bench Verified (or GPQA Diamond, AIME, MMLU, ARC-AGI-2, FrontierMath) for GPT-5.6. Its published suite is agentic-only: Terminal-Bench, Agents' Last Exam, BrowseComp, OSWorld. Treat any 'GPT-5.6 SWE-bench Verified' figure you see as third-party, not vendor-reported.

**EVIDENCE:** 'The article notes OpenAI omitted: SWE-Bench Verified, GPQA Diamond, AIME, MMLU, ARC-AGI-2, FrontierMath.' 'OpenAI's benchmark strategy for GPT-5.6 is deliberately agentic.'

**SRC:** https://www.vellum.ai/blog/gpt-5-6-benchmarks-explained (2026-08-03)

## F18 [high] [benchmark]
**CLAIM:** THE clearest honest split: Codex/GPT-5.6 leads terminal-driving, Claude leads repo-level patching. On Terminal-Bench 2.1 Sol scores 88.8% (91.9% Ultra) vs Claude Fable 5 84.6–86.0% and Sonnet 5 80.4%. On SWE-Bench Pro the ordering inverts hard: Fable 5 80.0% vs Sol 64.6% — a ~15-point Claude lead on multi-file, real-repo patching.

**EVIDENCE:** Vellum: 'Terminal-Bench 2.1 (%): Sol Ultra 91.9%, Sol 88.8%, Terra 87.4%, Luna 84.7%, Claude Fable 5 86.0%'; 'SWE-Bench Pro (%): Claude Fable 5 80.0%, Sol 64.6%'. evals.report snapshot Aug 31 2026: 'Claude Fable 5: 84.6% — Unverified, Jun 9 2026; Claude Sonnet 5: 80.4% — Verified; GPT-5.6 Sol: 88.8% — Verified, Jul 9 2026'.

**SRC:** https://evals.report/benchmarks/terminal-bench?tab=scores (2026-08-31 snapshot)

## F19 [high] [benchmark]
**CLAIM:** Terminal-Bench 2.1 results are overwhelmingly self-reported and harness-dependent — 33 models, 0 verified on the official leaderboard by one count — and the same model scores differently under different scaffolds (Anthropic reported GPT-5.5 at 83.4% specifically on the Codex CLI harness). Terminal-Bench gaps under ~5 points between vendors should be treated as noise, not ranking.

**EVIDENCE:** '33 models have been evaluated on the Terminal-Bench 2.1 benchmark, with 0 verified results and 33 self-reported results.' 'Results combine vendor and leaderboard harnesses, so comparisons should only be directional unless the same evaluator and scaffold were used.' Anthropic: 'Terminal-Bench 2.1 scores were reported for all models using the Terminus-2 public harness, with GPT-5.5's reported score on the Codex CLI harness at 83.4%.'

**SRC:** https://www.tbench.ai/leaderboard/terminal-bench/2.1 (leaderboard last updated August 2026)

## F20 [medium] [third-party-commentary]
**CLAIM:** Head-to-head Opus 5 vs GPT-5.6 Sol: Opus 5 leads SWE-bench Pro 79.2% vs 64.6%, MCP Atlas 85.8% vs 75.3%, AutomationBench 26.0% vs 18.1%, OSWorld 2.0 70.6% vs 62.6%, Frontier-Bench 43.3% vs 34.4%, ARC-AGI-3 30.2% vs 7.78%. Sol leads Terminal-Bench 2.1 (91.9% Ultra vs 89.1% max effort), BrowseComp 92.2% vs 90.8%, DeepSWE 72.7% vs 68.8%. SWE-bench Verified is a near-tie (96.0 vs 95.0) and therefore not a decision input.

**EVIDENCE:** CodingFleet comparison table, with per-row sourcing labels: 'SWE-bench Pro | 79.2% | 64.6% | Vendor-reported'; 'MCP Atlas | 85.8% | 75.3% | Independent'; 'ARC-AGI-3 | 30.2% | 7.78% | Independent (ARC Prize Foundation)'; 'Terminal-Bench 2.1 | 89.1% | 91.9% (Ultra)'.

**SRC:** https://codingfleet.com/blog/claude-opus-5-vs-gpt-5-6-sol/ (2026-07-25)

## F21 [medium] [third-party-commentary]
**CLAIM:** Codex's real, repeatable operational advantage is token/cost efficiency, not capability: measured at ~72% fewer output tokens on equivalent coding tasks, and 2–4x fewer tokens overall (one Figma task: Claude Code 6.2M tokens vs Codex 1.5M). But the cost gap is contested — a Composio head-to-head found only ~23% ($2.50 vs $2.04), so the 5–10x folklore is wrong.

**EVIDENCE:** Fountaincity: 'Codex uses roughly 72% fewer output tokens than Opus on equivalent coding tasks.' Blakecrosley: 'Codex consumed 2-4x fewer tokens for comparable results ... Claude Code used 6.2M tokens versus Codex's 1.5M.' Firecrawl: 'A Composio head-to-head showed Claude at $2.50 (~192k tokens) vs. Codex at $2.04 (~136k tokens)—roughly 23% cost difference, not the 5-10× folklore suggests.'

**SRC:** https://blakecrosley.com/blog/claude-code-vs-codex (2026-06-05 (updated from 2026-02-27))

## F22 [low] [third-party-commentary]
**CLAIM:** Preference and quality diverge: a 500+ developer survey found 65% prefer Codex day-to-day, yet blind review rated Claude Code's output cleaner 67% of the time vs Codex's 25%. Speed/cost preference is not a proxy for diff quality — do not let 'the team likes Codex' settle a code-quality question.

**EVIDENCE:** 'A 500+ developer Reddit survey: 65% prefer Codex day-to-day, yet blind reviews rate Claude Code's output cleaner 67% of the time.' 'blind code reviewers rated Claude Code's output cleaner 67% of the time to Codex's 25%.'

**SRC:** https://www.morphllm.com/comparisons/codex-vs-claude-code (August 2026)

## F23 [medium] [third-party-commentary]
**CLAIM:** Stage-level routing with duel counts: Claude Code won 8 of 12 decided code-review/security duels and 4 of 8 refactoring duels; feature implementation was a wash (5-5-2); Codex won DevOps/CI-CD (1-3-0). Concretely: repo-wide refactor, 'why is this broken' investigation, review → Claude; well-specified ticket, CI scripting, untrusted-code debugging → Codex.

**EVIDENCE:** Blakecrosley: 'Claude Code won 8 of 12 decided duels in review tasks'; 'Won 4 of 8 decided refactoring duels'; 'Feature implementation: 5-5-2'; 'DevOps & CI/CD: 1-3-0 favors Codex.' Morphllm: 'Repo-wide refactors and "figure out why this is broken" investigations go to Claude Code ... while well-specified tickets and CI scripting go to Codex.'

**SRC:** https://blakecrosley.com/blog/claude-code-vs-codex (2026-06-05 (updated from 2026-02-27))

## F24 [medium] [third-party-commentary]
**CLAIM:** Codex has a genuine architectural advantage Claude Code cannot match: kernel-level sandboxing (Apple Seatbelt, Landlock+seccomp/bubblewrap, Windows sandbox). Claude Code's enforcement is application-layer hooks sharing a process boundary with the agent — CVE-2025-59536 showed malicious hooks executing before the consent dialog. For running an agent against untrusted third-party code, Codex is the correct tool regardless of model quality.

**EVIDENCE:** 'Codex: Kernel-layer (Seatbelt on macOS, Landlock/bubblewrap on Linux, Windows sandbox). More deterministic. Claude Code: Application-layer via 26 programmable hook events plus Auto mode classifier. More expressive.' 'Application-layer enforcement shares a process boundary with the agent. CVE-2025-59536 proved malicious hooks execute before consent dialogs.'

**SRC:** https://www.firecrawl.dev/blog/claude-code-vs-codex (2026-06-03)

## F25 [medium] [third-party-commentary]
**CLAIM:** Conversely, Claude Code's hooks are PRE-execution and blocking (PreToolUse) while Codex's hooks observe after the fact. If your guardrail must PREVENT an action (credential scanning, red-tier gating, blocking a DNS write), Codex cannot enforce it at the harness layer — only its sandbox can.

**EVIDENCE:** 'If multi-stage execution requires pre-execution blocking through hooks, Claude Code's PreToolUse events provide deterministic control. Codex hooks observe after the fact.' 'The hook system enables pre-commit checks, credential scanning, output validation that block risky changes before execution.'

**SRC:** https://blakecrosley.com/blog/claude-code-vs-codex (2026-06-05 (updated from 2026-02-27))

## F26 [medium] [third-party-commentary]
**CLAIM:** Named GPT-5.6 behavioral failure modes, from a system-prompt-level analysis: (1) hedging when evidence is decisive; (2) reaching for web search when the gap is interpretive, not informational; (3) 'guessing at forks' — picking a branch on a materially ambiguous decision and delivering finished work rather than asking; (4) 'process over product' — on long tasks, producing a plan and running commentary that replaces the work with a narration of the work.

**EVIDENCE:** 'The model hedges even when the evidence is strong enough to support a clear answer.' 'When facing decisions that materially affect outcomes, the model picks one branch, completes work based on that assumption, and presents finished output instead of seeking clarification.' 'a plan and a running commentary, replacing the work with a narration of the work.' Root cause offered: the behavioral layer is 'under 10% of the 2,661-line system prompt'.

**SRC:** https://humanistheloop.substack.com/p/why-gpt-56-still-feels-off (2026-07-22)

## F27 [low] [third-party-commentary]
**CLAIM:** Codex-side failure modes reported by practitioners: run-to-run variability on identical prompts, off-plan drift when 'in the zone', defensive over-engineering, ignoring codebase style conventions, and losing track on complex multi-file edits. Recovery asymmetry matters operationally: 'when Codex fails, you typically need to re-prompt from scratch; when Claude fails, you can often guide it back on track through conversation.'

**EVIDENCE:** 'Variability: Same prompt produces different results across runs · Off-plan drift: Ignores instructions when in the zone · Defensive over-engineering: Adds unnecessary error handling · Style ignorance: Doesn't adapt to codebase patterns · Context switching: Loses track in complex multi-file edits.' Plus the quoted recovery-asymmetry line.

**SRC:** https://www.morphllm.com/comparisons/codex-vs-claude-code (August 2026)

## F28 [high] [forum-or-practitioner]
**CLAIM:** The Claude-side failure mode is the mirror image — over-editing and cost blowout from proactivity. Simon Willison documented Fable 5 orchestrating browser automation, a custom CORS web server, template modification and Shadow DOM manipulation unprompted, spending ~$12.11 in tokens to arrive at a two-line CSS fix. He calls unsandboxed deployment of such a model his top candidate for an AI-security 'Challenger disaster'.

**EVIDENCE:** 'Given a single screenshot and minimal instruction, the model independently orchestrated browser automation, template modification, custom web servers, and JavaScript injection—all without explicit authorization.' 'The session consumed ~$12.11 in tokens for what ultimately required a two-line CSS fix.'

**SRC:** https://simonwillison.net/2026/jun/11/fable-is-relentlessly-proactive/ (2026-06-11)

## F29 [medium] [third-party-commentary]
**CLAIM:** The strongest production-tested recommendation is not either/or but a driver/worker split: Claude Code as driver (architecture, multi-file refactor with invariant preservation, review and integration) with Codex as worker (mechanical transformations, parallelizable subtasks, sustained 45+ min terminal runs). Reported ~80% higher result quality vs single-tool runs; and an adversarial Claude↔Codex review loop 'caught 14 issues that neither tool found alone'.

**EVIDENCE:** Fountaincity (3 weeks production testing across complex refactoring, WordPress migrations, SAAS rebuilds): 'running both tools together—Claude Code as driver and Codex as worker—outperforms either tool alone'; 'roughly 80% higher result quality versus single-tool runs'. Blakecrosley: 'iterative Claude-Codex review loops caught 14 issues that neither tool found alone.'

**SRC:** https://fountaincity.tech/resources/blog/codex-claude-code-harness-together/ (April 2026)

## F30 [low] [third-party-commentary]
**CLAIM:** The harness, not the model weights, carries most of the measured capability — one production study attributes 16–36 percentage points of capability to framework quality. This argues against re-litigating model choice per task and for investing in whichever harness your process already encodes.

**EVIDENCE:** 'The article emphasizes that 16-36 percentage points of capability came from framework quality rather than model weights alone.' Firecrawl independently: 'the harness matters as much as the base model.'

**SRC:** https://fountaincity.tech/resources/blog/codex-claude-code-harness-together/ (April 2026)

## F31 [high] [vendor-blog]
**CLAIM:** Current list pricing per M tokens (in/out): GPT-5.6 Sol $5/$30, Terra $2/$12, Luna $0.20/$1.20; Claude Opus 5 $5/$25, Sonnet 5 $2/$10, Fable 5 $10/$50. Opus 5 is cheaper on output than Sol, so 'Codex is cheaper' is a token-volume argument, not a rate argument.

**EVIDENCE:** Vellum: 'Sol: $5 input / $30 output; Terra: $2/$12; Luna: $0.20/$1.20; Claude Fable 5: $10 input / $50 output.' Anthropic Opus 5 page: 'Pricing: $5 per million input tokens, $25 per million output tokens.' Anthropic Sonnet 5 page: 'Input: $2 per million tokens, Output: $10 per million tokens.'

**SRC:** https://www.anthropic.com/news/claude-opus-5 (2026-07-24)

## F32 [high] [vendor-blog]
**CLAIM:** Anthropic's own headline claim for Opus 5 is efficiency-per-turn rather than raw score: averaging 9 percentage points higher accuracy with a third fewer turns and tool calls and 60% less time across effort levels. That directly targets the long-horizon-autonomy axis Codex has historically owned.

**EVIDENCE:** 'Across effort levels it averaged 9 percentage points higher accuracy with a third fewer turns and tool calls and 60% less time.' Also 'surpassing all other models on Frontier-Bench v0.1 and more than doubling Opus 4.8's performance at a lower cost per task'; 'On CursorBench 3.2 at max effort, the model performs within 0.5% of Fable 5's peak score, but at half the cost per task.'

**SRC:** https://www.anthropic.com/news/claude-opus-5 (2026-07-24)

## F33 [high] [vendor-blog]
**CLAIM:** Sonnet 5 is the honest default for worker/fan-out roles, not Opus: 'performance close to Opus 4.8 at lower prices' and $2/$10 pricing, positioned as 'the most agentic Sonnet model yet'. One documented caveat: its cybersecurity capability is materially below Opus 4.8 (cannot develop working exploits) — so security-analysis stages should not be delegated down to Sonnet.

**EVIDENCE:** 'Sonnet 5's performance is close to that of Opus 4.8, but at lower prices.' 'Cybersecurity performance is notably lower than Opus 4.8—Sonnet 5 cannot develop working exploits, whereas Opus 4.8 can.'

**SRC:** https://www.anthropic.com/news/claude-sonnet-5 (2026-06-30)

## F34 [medium] [third-party-commentary]
**CLAIM:** Codex's ChatGPT-plan entry economics remain its structural advantage for solo operators: $20 ChatGPT Plus yields meaningful daily Codex volume, whereas $20 Claude Pro is limited and credible Claude Code volume starts at Max 5x ($100/mo). Offsetting risk: Codex Plus limits were tightened mid-stream in spring 2026 without notice.

**EVIDENCE:** 'Codex: $20/month (ChatGPT Plus) = meaningful daily usage. Claude Code: $20/month (Pro) = limited; credible volume requires Max 5x ($100/month).' 'Codex Plus ($20) hit mid-stream reductions in spring 2026. Reddit thread documented four-times tighter weekly quotas without notice.'

**SRC:** https://www.firecrawl.dev/blog/claude-code-vs-codex (2026-06-03)

## F35 [medium] [forum-or-practitioner]
**CLAIM:** Practical CI/CD notes for headless Codex: CODEX_API_KEY overrides stored credentials (OPENAI_API_KEY is deprioritized when valid stored auth exists), CODEX_HOME redirects config/auth/session storage, and an MCP server declared with required=true causes a FATAL session-init failure when unavailable — a hard-fail dependency to avoid in unattended pipelines.

**EVIDENCE:** 'CODEX_API_KEY overrides stored credentials (good for CI/CD). OPENAI_API_KEY is deprioritized when valid stored auth exists. CODEX_HOME fully redirects config, auth, and session storage away from ~/.codex.' 'MCP servers with required=true cause fatal session initialization failures when unavailable.'

**SRC:** https://gist.github.com/alexfazio/359c17d84cb6a5af12bac88fa1db9770 (2026-03-13 (CLI v0.114.0))


## GAPS
- Anthropic publishes its Opus 5 / Sonnet 5 benchmark tables as images, and WebFetch could not read them. Every Opus-5-vs-GPT-5.6 number in these findings is a third-party transcription (CodingFleet, Vellum), not a directly verified vendor table. Someone should open https://www.anthropic.com/news/claude-opus-5 in a browser and read the charts before these numbers get quoted in a decision doc.
- The exact model_reasoning_effort enum accepted by Codex CLI 0.152.0 is unresolved — OpenAI's models page lists Light/Low/Medium/High/Extra High/Max/Ultra while config references still show minimal|low|medium|high|xhigh. Needs `codex --help` / `codex exec --help` run against the installed binary.
- No independent verification that GPT-5.6 models honor --output-schema. The known guard bug (openai/codex#4181) was scoped to model_family 'gpt-5'; whether gpt-5.6-sol/terra/luna pass the guard is untested in any source I found.
- The deepest flag-level empirical work (alexfazio's 81-test gist) is CLI v0.114.0 / March 2026 — roughly 38 minor versions and six months stale as of 0.152.0. Its findings on stdin precedence, approval downgrade in exec, and --full-auto override behavior should be re-run before being encoded into a skill.
- I could not find a single practitioner head-to-head dated August or September 2026 that pairs current-generation tools — Codex CLI 0.15x + GPT-5.6 Sol against Claude Code + Opus 5. Every comparison fetched is Opus 4.7/4.8 vs GPT-5.5 era (Feb–June 2026) with the conclusions extrapolated forward. The stage-routing duel counts in particular are pre-Opus-5.
- No Claude Opus 5 entry appears on the independent Terminal-Bench 2.1 leaderboard snapshot (evals.report, Aug 31 2026) — the 89.1% figure is vendor/third-party only, and Terminal-Bench itself shows 0 of 33 results as verified.
- Codex's sandbox documentation page (learn.chatgpt.com/docs/sandbox) and permission-profiles page returned 404 on the URLs I guessed after the docs migration. The 'elevated'/'unelevated' sandbox_mode values and the [permissions.<name>] profile syntax are attested only in a summary of the config-basic page, not read in full.
- Whether Codex can itself be exposed AS an MCP server (i.e. `codex mcp serve` or equivalent, for driving Codex from Claude Code) is not answered — the vendor MCP doc only covers Codex-as-client.
- The two most cited practitioner statistics — '67% of blind reviewers rated Claude output cleaner' and the '$15 Codex vs $155 Claude Express.js refactor' — trace to aggregator blogs with no linked primary study. Treat as anecdote until the source is found.
- Nothing found on how Codex behaves against a red-tier-style approval gate in headless mode beyond the observation that -a on-request degrades to never. For mission-control's guardrail tiers this is the load-bearing unknown: sandbox mode appears to be the only enforceable control in codex exec.

## SOURCES
- https://learn.chatgpt.com/docs/developer-commands?surface=cli
- https://learn.chatgpt.com/docs/config-file/config-basic
- https://learn.chatgpt.com/docs/pricing.md
- https://learn.chatgpt.com/docs/models.md
- https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- https://developers.openai.com/codex/cli/reference
- https://developers.openai.com/codex/config-basic
- https://developers.openai.com/codex/mcp
- https://github.com/openai/codex/releases
- https://github.com/openai/codex/issues/15451
- https://gist.github.com/alexfazio/359c17d84cb6a5af12bac88fa1db9770
- https://getunblocked.com/blog/codex-context-window/
- https://www.vellum.ai/blog/gpt-5-6-benchmarks-explained
- https://www.anthropic.com/news/claude-opus-5
- https://www.anthropic.com/news/claude-sonnet-5
- https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5
- https://simonwillison.net/2026/jun/11/fable-is-relentlessly-proactive/
- https://www.firecrawl.dev/blog/claude-code-vs-codex
- https://fountaincity.tech/resources/blog/codex-claude-code-harness-together/
- https://humanistheloop.substack.com/p/why-gpt-56-still-feels-off
- https://codingfleet.com/blog/claude-opus-5-vs-gpt-5-6-sol/
- https://blakecrosley.com/blog/claude-code-vs-codex
- https://evals.report/benchmarks/terminal-bench?tab=scores
- https://www.tbench.ai/leaderboard/terminal-bench/2.1
- https://www.morphllm.com/comparisons/codex-vs-claude-code
