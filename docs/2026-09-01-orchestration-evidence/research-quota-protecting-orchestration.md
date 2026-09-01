> UNAUDITED research sweep, captured 2026-09-01 — verify before relying.
> Produced by a parallel web-research fan-out on the night of 2026-09-01. Every claim carries the
> URL and the date the source itself showed; "undated" means the page displayed none. Source kinds are
> the researcher's own labels. The GAPS section at the end is as important as the findings: it records
> what could not be established. Nothing here has been re-checked since capture.

# "Downgraded but still effective" orchestration — protecting a premium-model quota as a first-class design constraint

## F1 [high] [vendor-doc]
**CLAIM:** The highest-leverage quota-protection pattern is not model tiering at all — it is run-cheap-then-retry-failures on the SAME model using the effort dial. Anthropic's own measurement: Opus 5 at `low` effort on SWE-bench Pro failed 16% of tasks; re-running only those failures at default effort reached ~93% pass at ~$0.70/task versus 91.7% at $1.39 running everything at default. Same pass rate, half the cost, counting the wasted cheap attempts.

**EVIDENCE:** Verbatim from the page: "With Claude Opus 5 at `low`, 16% of tasks failed; with those re-run at the default, about 93% passed for about $0.70 each, against 91.7% for $1.39 running everything at the default: the same pass rate for half the cost, counting the failed cheap attempts." Also: "Starting at `medium` instead solved about 94% for about $0.95."

**SRC:** https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence (undated (page displays no publication or last-updated date; internally references an August 13, 2026 benchmark run))

## F2 [high] [vendor-doc]
**CLAIM:** Orchestrator-with-cheap-workers buys its savings by capping the COST TAIL on routine work, not by being cheaper on average difficulty. Anthropic measured a Fable 5 coordinator + Sonnet 5 worker on 10 reliably-solved BrowseComp problems at about half the cost of Fable alone on average and about a third at p90 ($12 vs $33) at the same accuracy — but on the full, harder BrowseComp set the economics reversed.

**EVIDENCE:** "delegated runs cost about half of Fable alone on average and about a third at the 90th percentile ($12 compared with $33)" with accuracy unchanged; rationale: "A frontier model running alone occasionally spirals on a routine problem it would normally solve... a few such runs dominate the bill. A coordinator that hands routine work to a lower-cost worker caps that tail, because any spiraling now happens at worker rates." And verbatim: "On the full, harder BrowseComp set, the economics reversed. If your traffic has a long cost tail on routine tasks, this is the orchestrator case to measure first."

**SRC:** https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence (undated (references an August 13, 2026 run))

## F3 [high] [vendor-doc]
**CLAIM:** The vendor's own stated decision rule contradicts reflexive multi-agent design: split the work only when traffic MIXES routine and hard steps. For uniform difficulty or a single dependent chain, a single well-tuned model is the better choice.

**EVIDENCE:** Verbatim: "When your traffic mixes routine work that a smaller model handles reliably with harder steps that need frontier capability, splitting the work keeps frontier intelligence where it matters while most tokens bill at smaller-model rates. When a workload lacks that mix, because its difficulty is uniform or it is one dependent chain, a single well-tuned model is usually the better choice."

**SRC:** https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence (undated)

## F4 [high] [vendor-doc]
**CLAIM:** On a 21.6M-token corpus task, a Fable 5 coordinator driving 25 concurrent Sonnet 5 workers cost $263/$299/$261 per episode versus $720–$764 for Fable solo (>60% less) at F1 0.842/0.805/0.810 — 2–6 points below solo. The savings mechanism is that the bulk of the bill is corpus reading billed at the WORKER's cache-read rate, not at the frontier model's. That makes the pattern a caching-rate arbitrage, not a token-count reduction.

**EVIDENCE:** "The charted team configuration is an August 13, 2026, run in which the Claude Fable 5 coordinator ran the whole sweep inside the platform at its documented limit of 25 concurrent Claude Sonnet 5 workers; its three episodes scored F1 0.842, 0.805, and 0.810 for $263, $299, and $261." Mechanism: "Both bills are mostly corpus reading served from the cache... its reads were billed at Claude Sonnet 5's cache-read rate rather than Claude Fable 5's."

**SRC:** https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence (undated (run dated August 13, 2026))

## F5 [high] [vendor-doc]
**CLAIM:** Anthropic shipped a first-class primitive for exactly this angle: the advisor tool (beta header `advisor-tool-2026-03-01`), where a cheap executor model consults an expensive advisor model mid-generation. Across pairings the advisor closed 50%–90% of the gap to the stronger model while you pay frontier rates only on consultations. Advisor tokens are billed separately, are NOT rolled into top-level usage, and do not draw from the executor's task budget.

**EVIDENCE:** "Across the pairings in the following chart, the advisor closed 50% to 90% of the gap to the stronger model and you pay for the stronger model only on the consultations, which is what makes the cost cases possible." From the advisor doc: "Advisor calls run as a separate sub-inference billed at the advisor model's rates... Top-level `usage` fields reflect executor tokens only." and "The advisor's tokens also do not draw from any task budget applied to the executor." Advisor output is "typically 400 to 700 text tokens, or 1,400 to 1,800 tokens total including thinking."

**SRC:** https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool (undated (beta header string is dated 2026-03-01))

## F6 [high] [vendor-doc]
**CLAIM:** The advisor/tiering benefit scales with the CAPABILITY GAP and collapses when the executor is already strong — the vendor publishes the negative case. On GPQA Diamond a Haiku 4.5 executor gained a great deal from an Opus 5 advisor, a Sonnet 5 executor gained a few points, and a frontier executor gained almost nothing. On SWE-bench Pro the executor stopped asking for advice, consult rate collapsed, and the pair scored BELOW the executor alone.

**EVIDENCE:** "The advisor can only hand over capability the executor lacks: on GPQA Diamond a Claude Haiku 4.5 executor gained a great deal from a Claude Opus 5 advisor, a Claude Sonnet 5 executor gained a few points, and a frontier executor almost nothing." On DeepSWE the same pairing consulted "about two consultations on every task" and "gained 23 points"; on SWE-bench Pro the consult rate collapsed and the result "scores below the executor alone."

**SRC:** https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence (undated)

## F7 [high] [paper]
**CLAIM:** A controlled experiment isolating orchestration strategy as the ONLY variable (models, prompts, tools, inputs held constant) found deterministic/code orchestration cut token consumption up to 3.5x versus LLM-controlled orchestration with comparable translation quality — but the tradeoff is real and two-sided: LLM-controlled orchestration achieved HIGHER success rate (more runnable, test-passing programs), while deterministic achieved higher accuracy and better worst-case robustness.

**EVIDENCE:** Abstract: "deterministic orchestration achieves comparable computational accuracy to LLM-controlled orchestration while improving worst-case robustness and reducing performance variability across runs. Deterministic execution also reduces token consumption by up to 3.5x." Results §5.1: "Deterministic orchestration achieves higher computational accuracy and stronger worst-case robustness, while LLM-controlled orchestration attains higher success rates across repeated runs." §5.3: LLM-controlled "often requires between 1.75 million and 2.25 million tokens" vs deterministic "approximately 400,000 to 700,000 tokens"; text claims SQ category cost ">$140 per successful translation" vs "approximately $40" deterministic.

**SRC:** https://arxiv.org/pdf/2605.09894 (11 May 2026 (arXiv:2605.09894v1 [cs.SE]))

## F8 [medium] [own-inference]
**CLAIM:** CAVEAT on the above paper's dollar figures: the text asserts $140 vs $40 per successful translation, but the reproduced Figure 4 axis runs 0.0–0.6 dollars. The token ratios (1.75–2.25M vs 400–700k) are internally consistent and are the number to trust; treat the dollar figures as unreliable.

**EVIDENCE:** Extracted text shows the cost-figure axis labels "0.6 0.5 0.4 0.3 0.2 0.1 0.0" under "Cost ($)" for Figure 4, while the prose in §5.3 states "LLM-controlled orchestration exceeds $140 per successful translation, while deterministic orchestration achieves the same result for approximately $40."

**SRC:** https://arxiv.org/pdf/2605.09894 (11 May 2026)

## F9 [high] [paper]
**CLAIM:** The strongest published critique of fan-out: on inputs a single model already handles well, multi-agent pipelines cost 5–6x for zero signal, and two pipelines actively DEGRADED quality. The Ranker+Evaluator pipeline dropped NDCG@10 from 0.7197 to 0.6922 (−3.8%, −7.2% at NDCG@3) while costing roughly 4x. The named mechanism is error propagation: an evaluator critiquing an already-correct output emits an ungrounded critique that the next stage incorporates.

**EVIDENCE:** Verbatim: "the single shot LLM call is already strong, reaching an NDCG@10 of 0.7197, and no multi-agent pipeline meaningfully improves on it." "...five- to six-fold cost increase documented in Table 6, this is effectively a loss: the added structure purchases no useful signal." "The Ranker+Evaluator pipeline (RC) falls to an NDCG@10 of 0.6922, a relative drop of 3.8 percent... while costing roughly four times as much." "When the evaluator critiques an already-correct ranking with no external ground-truth oracle, its critique is itself an ungrounded LLM output that the ranker then incorporates, so a second source of error is introduced where the first pass had none." Summary: "on inputs a single model already handles well, additional agents add failure surface faster than they add signal."

**SRC:** https://arxiv.org/pdf/2507.02097 (ACM Trans. Recomm. Syst. publication date July 2026; PDF metadata date June 30, 2026)

## F10 [high] [paper]
**CLAIM:** Same paper, the inverting condition — and this is the design rule, not the headline: fan-out pays exactly where the single call is WEAK. On a high-diversity user sample the ordering reversed, with the planner+ensemble pipeline reaching NDCG@3 0.5202 vs 0.4898 single-shot (+6.2%). So gate fan-out on input difficulty, not on task type.

**EVIDENCE:** "here the pipelines that carry a planner or an ensemble lead the single shot LLM call. At NDCG@3 the combined pipeline (PPEns) reaches 0.5202 and the ensemble pipeline (PEns) reaches 0.5162, against 0.4898 for the single shot LLM call, a relative gain of 6.2 and 5.4 percent respectively." "The contrast between Tables 7 and 8 is the central empirical finding of the paper: the same pipelines that are wasteful on typical users become beneficial on diverse ones."

**SRC:** https://arxiv.org/pdf/2507.02097 (July 2026)

## F11 [high] [paper]
**CLAIM:** Parallelism recovers wall-clock but NOT budget — the paper measures the critical path explicitly and states dollar cost scales with number and size of calls regardless of scheduling. Relevant because parallel fan-out feels free when you are watching latency and are actually watching your quota drain.

**EVIDENCE:** "Crucially, parallel execution recovers a share of the wall-clock penalty but does not reduce token consumption or dollar cost, which scale with the number and size of calls regardless of how they are scheduled." Measured: PEns/PPEns at "roughly three times the Single-shot LLM call latency (34.1 s and 35.2 s against 11.8 s)" while costing 5-6x.

**SRC:** https://arxiv.org/pdf/2507.02097 (July 2026)

## F12 [high] [third-party-commentary]
**CLAIM:** There is a capability FLOOR on the orchestrator itself — you cannot downgrade the control plane if the control plane is an LLM. A Writer, Inc. panel found delegation worked reliably only on the two strongest models (~0.85) and fell to unusable (~0.45) on the fast tier. This is the argument for making the orchestrator deterministic CODE rather than a cheap model.

**EVIDENCE:** Laurie Voss: "They found delegation worked reliably only on the two strongest models in the panel, scoring around 0.85, and fell to unusable, around 0.45, on the fast tier." Same post cites "a Fable 5 orchestrator directing Sonnet 5 workers retained 96% of an all-Fable team's score on BrowseComp... at 46% of the cost", GLM 5.2 "statistically tied with Opus" at $1.28/task vs Opus 4.8 $1.94, and "MinionS recovered 97.9% of GPT-4o's quality at 5.7x less cloud spend, but it's not an apples-to-apples comparison."

**SRC:** https://arize.com/blog/how-cheap-models-changed-multi-agent-economics/ (August 2026 (byline Laurie Voss))

## F13 [medium] [paper]
**CLAIM:** Corroborating the code-orchestrator argument from the governance side: a June 2026 paper's explicit design principle is that the control plane must be ordinary testable code — hashing, regex, state machine, set arithmetic — and NOT delegated to further LLM orchestration.

**EVIDENCE:** Abstract: "Governance of this layer must be deterministic and tool-agnostic - not delegated to further LLM orchestration." The paper also cites empirical work that "LLM code debugging shows effectiveness decays sharply within 2–3 attempts", motivating "a hard cap on self-correction loops" — a direct quota-protection mechanism.

**SRC:** https://arxiv.org/pdf/2606.26924 (25 June 2026 (arXiv:2606.26924v1))

## F14 [high] [vendor-doc]
**CLAIM:** Prompt-caching economics for long-running orchestration: reads are 0.1x base input, 5-minute cache writes 1.25x, 1-hour writes 2.0x. The 5-minute TTL refreshes free on every use. Critically, TTL is measured from the START of the request, so a 4-minute streaming response leaves only ~1 minute to re-hit — a real trap for slow agent turns.

**EVIDENCE:** "5-minute cache write tokens are 1.25 times the base input tokens price / 1-hour cache write tokens are 2 times the base input tokens price / Cache read tokens are 0.1 times the base input tokens price." "The cache is refreshed for no additional cost each time the cached content is used." "The lifetime is measured from the start of the request that writes or reads the cache entry, not from the end of its response... if a response takes 4 minutes to stream, a follow-up request that reuses the same cached prefix must start within about 1 minute of that response completing." Opus 5 example: base $5/MTok, 5m write $6.25, 1h write $10, reads $0.50.

**SRC:** https://platform.claude.com/docs/en/build-with-claude/prompt-caching (undated (lists Claude Opus 5 / Fable 5 / Mythos 5, so current as of 2026))

## F15 [high] [vendor-doc]
**CLAIM:** The vendor names the sub-agent case explicitly as the 1-hour-cache trigger: use 1h TTL "when an agentic side-agent will take longer than 5 minutes." Minimum cacheable prefix is 512 tokens for Opus 5 / Fable 5 / Mythos 5 (down from 1,024 for Sonnet 5 and 4,096 for Opus 4.5/4.6) — and under-minimum cache requests fail SILENTLY with no error.

**EVIDENCE:** "The 1-hour cache is best used in the following scenarios: When you have prompts that are likely used less frequently than 5 minutes, but more frequently than every hour. For example, when an agentic side-agent will take longer than 5 minutes..." Minimums: "512 tokens for Claude Opus 5, Claude Fable 5, and Claude Mythos 5... 1,024 tokens for Claude Opus 4.8, Claude Sonnet 5..." and "Any requests to cache fewer than this number of tokens will be processed without caching, and no error is returned."

**SRC:** https://platform.claude.com/docs/en/build-with-claude/prompt-caching (undated (2026-current model list))

## F16 [high] [vendor-doc]
**CLAIM:** The concrete Claude Code lever for tiering is per-subagent `model` frontmatter plus the `CLAUDE_CODE_SUBAGENT_MODEL` env var, resolved in a documented four-step precedence. One important gap: setting the env var alone does NOT change the model for the built-in Explore and Plan subagents.

**EVIDENCE:** Resolution order: "1. The per-invocation model parameter 2. The subagent definition's model frontmatter, where inherit selects the main conversation's model 3. The CLAUDE_CODE_SUBAGENT_MODEL environment variable 4. The main conversation's model." Values: "sonnet, opus, haiku, or fable" or full IDs, or "inherit". Explicit guidance: "Control costs by routing tasks to faster, cheaper models like Haiku." Caveat: "Setting CLAUDE_CODE_SUBAGENT_MODEL by itself doesn't change the model the built-in Explore and Plan subagents run on."

**SRC:** https://code.claude.com/docs/en/sub-agents (undated (references fable alias and claude-opus-5, so 2026-current))

## F17 [medium] [forum-or-practitioner]
**CLAIM:** Over-fragmenting into many small subagents destroys the savings: subagent initialization alone costs roughly 25–35k tokens, so batching related work into one agent beats spawning micro-agents. A practitioner reports a team cutting token spend 60% by setting two frontmatter fields.

**EVIDENCE:** "subagent initialization costs roughly 25–35k tokens, so over-fragmenting work negates savings. Batching related tasks into single agents proves more efficient than spawning multiple micro-agents." And: "One team cut token spend by 60% just by setting two fields" — attributed to routing rather than quality loss: "not because they downgraded quality, but because they stopped paying Opus prices for tasks that need Haiku-level work." Routing given as Haiku+low for lookups/extractions/file reads, Sonnet+medium for code generation and tool-heavy execution, Opus+high for security audits, architecture decisions, ambiguous multi-step reasoning.

**SRC:** https://byteiota.com/claude-code-subagent-model-routing/ (August 5, 2026)

## F18 [medium] [third-party-commentary]
**CLAIM:** Input tokens, not output, are where agent spend lives — one worked example shows cache reads at ~94.5% of tokens and output at ~0.5%, and an OpenRouter study found 99% of spend was input accumulated in agent trajectories. Implication for quota protection: context hygiene and cache-prefix stability matter more than shortening model responses.

**EVIDENCE:** July 24, 2026 page: cache reads "~94.5% of tokens, with output at only ~0.5%"; OpenRouter study "99% were input tokens accumulated in agent trajectories." A documented Bun migration cost $165K with "5.9B uncached input, 690M output, 72B cached reads" — output outnumbered by cached reads "roughly 100:1." Also cites "Aider architect mode: 14x cheaper than o1 solo ($13.29 vs. $186.50)" as a tiering result.

**SRC:** https://www.augmentcode.com/guides/ai-coding-cost-analysis-agent-token-spend (July 24, 2026)

## F19 [medium] [forum-or-practitioner]
**CLAIM:** Cross-vendor quota telemetry is a solved, documented practitioner problem: Claude Code exposes an undocumented OAuth usage endpoint (api.anthropic.com/api/oauth/usage with header anthropic-beta: oauth-2025-04-20) returning utilization percent and reset times for BOTH the 5-hour rolling and 7-day windows; Codex exposes account/rateLimits/read over JSON-RPC via `codex app-server`; Gemini has no API and requires parsing ~/.gemini/tmp session JSON. Claude's weekly window resets Thursdays 8pm PT, not midnight UTC.

**EVIDENCE:** Post documents each endpoint by name, and describes threshold-driven queue draining: "when Codex weekly usage drops below 60 percent, a cron pulls a maintenance task off the queue" and "when Gemini comes in under 900 sessions for the day, a research queue does the same" — the explicit goal being that "unused budget gets used instead of expiring." Collector writes latest.json plus daily JSONL.

**SRC:** https://ianlpaterson.com/blog/tracking-claude-codex-gemini-quotas-from-one-script/ (Published March 19, 2026; updated May 30, 2026)

## F20 [medium] [third-party-commentary]
**CLAIM:** NEGATIVE RESULT on external-CLI-as-labor-pool: the tooling to make Codex CLI a delegated worker for Claude Code is mature and multiple (Codex CLI ships `codex mcp-server` natively, exposing `codex` and `codex-reply` tools; community wrappers codex-as-mcp, tuannvm/codex-mcp-server, denysvitali/codex-mcp), but NONE of the published documentation states quota arbitrage as the motivation. The stated motivation is capability integration, and the auth path documented is an OpenAI API key, i.e. metered billing, not a subscription quota.

**EVIDENCE:** Codex CLI natively exposes MCP tools "codex: Initiates new coding sessions with parameters like prompt, model, approval-policy, and sandbox" and "codex-reply: Continues existing sessions using a threadId." tuannvm server: "uses API key authentication, not subscriptions... codex login --api-key"; motivation is "capability integration" with no stated cost/quota savings. Practical config: client_session_timeout_seconds=360000 because "coding tasks can run for minutes rather than seconds."

**SRC:** https://codex.danielvaughan.com/2026/05/18/codex-cli-as-mcp-server-exposing-agent-capabilities-agents-sdk-multi-agent-delegation/ (May 18, 2026 (page shows updated September 1, 2026))

## F21 [medium] [third-party-commentary]
**CLAIM:** Worse for the quota-shifting thesis: MCP-delegated Codex sessions are documented as costing MORE in total tokens, not less — expect roughly 3x the token usage of a single Codex session, because each MCP-invoked session carries its own context independently. Offloading to a second vendor's CLI shifts WHOSE quota burns but increases total tokens burned.

**EVIDENCE:** "Each MCP-invoked Codex session consumes tokens independently... expect 3x the token usage compared to a single Codex session." Also documented limitations that matter for unattended orchestration: "No streaming to the MCP client" (long tasks appear to hang), single-process concurrency serializing CPU-bound work, and "No resume after crash" — in-flight sessions are lost.

**SRC:** https://codex.danielvaughan.com/2026/05/18/codex-cli-as-mcp-server-exposing-agent-capabilities-agents-sdk-multi-agent-delegation/ (May 18, 2026)

## F22 [low] [forum-or-practitioner]
**CLAIM:** Explicit subscription-quota arbitrage tooling does exist (CLIProxyAPI wraps Claude Code, Codex, Gemini/Antigravity, Grok Build and Kimi subscription logins into OpenAI/Gemini/Claude-compatible API endpoints, with multi-account round-robin load balancing), but its self-description is openly about consuming subscription/free quota through an API surface. Flag this as terms-of-service grey, not a sanctioned pattern.

**EVIDENCE:** Repo describes itself as providing "OpenAI/Gemini/Claude/Codex compatible API interfaces for CLI" so users can "enjoy the free Gemini 3.1 Pro, GPT 5.6 Series, Grok 4.5, Claude model through API", and supports "multiple accounts with round-robin load balancing" across providers. ~3,586 commits on main, actively maintained; no release date shown on the landing page.

**SRC:** https://github.com/router-for-me/CLIProxyAPI (undated (repo landing page shows no release date))

## F23 [high] [vendor-doc]
**CLAIM:** Two cheap non-model levers with measured returns that most tiering discussions miss. (1) Output FORMAT: three formats equally accurate on a triage agent — one-line $0.49/78%, two-line $0.57/80%, five-section memo $1.40/85%; the memo costs 6x baseline output tokens. (2) Prompt staleness: prompts written for Opus 4.8 cost 36% more per ticket on Opus 5 for no accuracy change; auditing the prompt gave 97% accuracy at 14% LOWER cost.

**EVIDENCE:** "The three formats are equally accurate; they differ in what you pay. Ask for the answer you will read, not the one that looks thorough." And: "prompts written for Claude Opus 4.8 cost 36% more per ticket on Claude Opus 5 for no change in accuracy"; audited prompt moved Opus 5 from 92% baseline to 97% at −14% cost across a 44-ticket support-desk set.

**SRC:** https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence (undated)

## F24 [high] [vendor-doc]
**CLAIM:** Capping max_tokens is a FALSE economy for quota protection — measured cost per solved task was identical. At a 16,384-token cap, 15% of Opus 5 attempts and 33% of Fable 5 attempts ended prematurely and solved zero; the cheaper attempts bought proportionally fewer solves.

**EVIDENCE:** "Capped runs spent less per attempt but bought proportionally fewer solves, so cost per solved task was the same as at 64,000." Contrast with task budgets, which did work as an efficiency lever: on SWE-bench Pro a generous budget cost −2.7 points pass@1 for 18% reduction, a tight budget −4.4 points for 47% reduction — described as "Budgets bought efficiency here, not accuracy."

**SRC:** https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence (undated)

## F25 [high] [vendor-doc]
**CLAIM:** Quantified quality cost of dropping effort a tier, by workload class — the cleanest 2026 answer to 'how much do I actually lose'. Knowledge work (WideSearch, DeepWideSearch, BrowseComp, GDPval): medium effort = 15–30% cheaper for 1–3 points; low = one-third to one-half cost for the same 1–3 points. Long-horizon coding (SWE-bench Pro): medium = ~50% cheaper for ~2 points; low = ~75% cheaper for ~8 points. Deep research: no free lunch — every effort step bought ~2.4 rubric points.

**EVIDENCE:** Knowledge tasks described as "nearly flat on four research tasks" at reduced effort. Coding: low effort ~75% cost reduction with ~8 points loss, called "a real tradeoff, which [re-running failures at higher effort] turns back into a saving." Deep research: "every effort step bought about 2.4 points of rubric score; there is no free cost cut on that curve."

**SRC:** https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence (undated)

## F26 [medium] [third-party-commentary]
**CLAIM:** The widely-cited '15x tokens' multi-agent figure is now STALE and should not anchor 2026 design. It comes from Anthropic's June 2025 multi-agent research post (Opus 4 lead + Sonnet 4 subagents beating single-agent Opus 4 by 90.2%; agents ~4x chat tokens, multi-agent ~15x chat) — roughly 15 months old, predating the effort dial, the advisor tool, and current cache-rate economics documented above.

**EVIDENCE:** Reported figures: "a multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on internal research evaluation"; "agents typically use about 4x more tokens than chat interactions, and multi-agent systems use about 15x more tokens than chats"; token usage alone explained 80% of BrowseComp performance variance. Simon Willison's writeup is dated June 14, 2025.

**SRC:** https://simonwillison.net/2025/Jun/14/multi-agent-research-system/ (June 14, 2025 (summarizing an Anthropic post of the same month) — ~15 months stale as of 2026-09-01)

## F27 [low] [third-party-commentary]
**CLAIM:** Batch API is a 50% discount on both input and output with no quality difference, but is structurally incompatible with most orchestration: no streaming, no real-time tool use, up-to-24-hour turnaround. It is only a quota lever for the leaf stages that are genuinely fire-and-forget (bulk classification, extraction, eval scoring) — not for the interactive loop.

**EVIDENCE:** Multiple secondary sources agree the Message Batches API returns results within 24 hours at 50% off standard token prices on both input and output, with "no quality difference between batch and real-time responses — only timing", and that for most agent use cases the absence of streaming and real-time tool use "is a dealbreaker." I did not fetch an Anthropic first-party batch page in this pass, so the 50%/24h figures are corroborated secondary rather than vendor-confirmed here.

**SRC:** https://dev.to/mukundakatta/when-and-how-to-use-the-anthropic-batch-api-in-your-agent-5fgn (undated (surfaced in a September 2026 search; no date shown in results))


## GAPS
- SUBSCRIPTION quota accounting is undocumented. Every measured cost/quality number found is in API dollars. Nobody publishes how Claude Code's 5-hour and 7-day subscription windows are debited per model tier — i.e. whether a Haiku subagent consumes ~1/15th of a weekly quota unit or is metered on some other basis. This is the single biggest gap for the stated angle: all the tiering evidence optimizes dollars, and the binding constraint here is a quota.
- No controlled study of cross-vendor CLI delegation economics. The Codex-as-MCP tooling is mature but every published writeup frames it as capability integration; the one cost statement found says MCP-delegated Codex costs ~3x MORE total tokens. No 2026 benchmark compares 'Claude orchestrator + Codex workers' against a single-vendor baseline on quality or on quota preserved.
- Terms-of-service status of subscription-quota proxying (CLIProxyAPI-style multi-account round-robin) is entirely unaddressed by any source found. Nobody credible has published on whether this is permitted, and no vendor page was located that speaks to it.
- Re-priming vs keeping a session warm has no published empirical comparison. The vendor caching doc gives the raw multipliers (1.25x/2.0x write, 0.1x read) and the 1h-TTL guidance for side-agents, and one secondary source computes a break-even at ~2.3 reuses within the hour window, but I found no measured study of the actual crossover for a long-running orchestrator with intermittent turns.
- No first-party Anthropic batch API page was fetched, so the 50%/24h batch figures rest on secondary sources only and several of those were undated.
- The advisor-tool and optimizing-for-cost pages carry NO publication or last-updated date, so their currency can only be inferred from the model families they list. The COBOL orchestration paper's dollar figures contradict its own figure axis and could not be reconciled.
- Almost all measured evidence is on benchmarkable, verifiable tasks (SWE-bench, BrowseComp, GPQA, NDCG ranking). There is no 2026 data found on quality loss from downgrading a tier for open-ended writing, synthesis, or judgment stages — precisely the stages people most want to reserve for the expensive model.

## SOURCES
- https://arxiv.org/pdf/2605.09894
- https://arxiv.org/pdf/2606.26924
- https://arxiv.org/pdf/2507.02097
- https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://code.claude.com/docs/en/sub-agents
- https://arize.com/blog/how-cheap-models-changed-multi-agent-economics/
- https://www.augmentcode.com/guides/ai-coding-cost-analysis-agent-token-spend
- https://www.cockroachlabs.com/blog/agentic-ai-costs-at-scale/
- https://byteiota.com/claude-code-subagent-model-routing/
- https://ianlpaterson.com/blog/tracking-claude-codex-gemini-quotas-from-one-script/
- https://codex.danielvaughan.com/2026/05/18/codex-cli-as-mcp-server-exposing-agent-capabilities-agents-sdk-multi-agent-delegation/
- https://github.com/tuannvm/codex-mcp-server
- https://github.com/router-for-me/CLIProxyAPI
- https://simonwillison.net/2025/Jun/14/multi-agent-research-system/
- https://dev.to/mukundakatta/when-and-how-to-use-the-anthropic-batch-api-in-your-agent-5fgn
