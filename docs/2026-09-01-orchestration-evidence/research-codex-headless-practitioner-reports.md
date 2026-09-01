> UNAUDITED research sweep, captured 2026-09-01 — verify before relying.
> Produced by a parallel web-research fan-out on the night of 2026-09-01. Every claim carries the
> URL and the date the source itself showed; "undated" means the page displayed none. Source kinds are
> the researcher's own labels. The GAPS section at the end is as important as the findings: it records
> what could not be established. Nothing here has been re-checked since capture.

# Practitioner reports on driving Codex CLI programmatically, and on Codex-plus-Claude hybrid workflows

## F1 [high] [forum-or-practitioner]
**CLAIM:** The single most common headless-Codex failure is a stdin deadlock: `codex exec "prompt"` hangs forever printing "Reading additional input from stdin..." whenever stdin is an inherited-but-unwritten pipe, even though the prompt was passed as an argument. Every programmatic caller must redirect stdin from /dev/null (or NUL on Windows).

**EVIDENCE:** Issue #20919: hang shows 0% CPU, only stderr output is "Reading additional input from stdin...", deterministic (not intermittent). Root cause: "the CLI appends stdin as a block after the prompt argument when stdin is detected as a non-TTY pipe. In inherited but unwritten pipes, read() blocks indefinitely because the writer side remains open without delivering EOF." Workarounds given: POSIX `codex exec "" < /dev/null`; Windows cmd `codex exec "" < NUL`; from PowerShell `cmd /c "codex exec "" < NUL"`. Affects codex-cli 0.128.0 and prior. Reporter notes it "affects all programmatic callers (CI runners, editors, agents)" and is "indistinguishable from network hangs," making timeouts/retries counterproductive.

**SRC:** https://github.com/openai/codex/issues/20919 (undated (issue page shows no date in fetched content; affected version 0.128.0))

## F2 [high] [forum-or-practitioner]
**CLAIM:** The stdin hang is not fixed by simply setting TERM or redirecting — a separate report on v0.133.0 (macOS) shows `TERM=dumb codex exec "hello"` hanging even with `< /dev/null`, `echo "" |`, `expect`, and `script -q`. So the /dev/null workaround is necessary but not always sufficient; there is still no `--no-stdin` flag.

**EVIDENCE:** Issue #27019: "Commands Attempted (All Hang): TERM=dumb codex exec "hello"; codex exec "hello" < /dev/null; echo "" | codex exec "hello"; expect script simulation; script -q /dev/null codex exec "hello"." Contrast: same command under TERM=xterm succeeds. Environment: macOS 25.2.0 arm64, Codex CLI v0.133.0, ChatGPT OAuth, gpt-5.4, HTTP proxy configured. Reporter requests "a --no-stdin flag" or auto-skip of stdin reads when a prompt argument is present. Impact areas listed: agent frameworks, CI/CD pipelines, scripted automation.

**SRC:** https://github.com/openai/codex/issues/27019 (undated (version v0.133.0))

## F3 [high] [forum-or-practitioner]
**CLAIM:** Directly relevant to driving Codex from Claude Code: `codex exec` silently exits 0 with completely empty stdout AND stderr when there is no controlling TTY and the prompt is non-trivial (~2KB+). This regressed in 0.124.0 and the report names Claude Code's Bash tool with `run_in_background: true` as an affected caller. Short prompts can succeed under identical conditions, which makes it look intermittent.

**EVIDENCE:** Issue #19945: "setsid codex exec "$(cat prompt.txt)" < /dev/null > out.log 2> err.log" → "exit=0, out=0 bytes, err=0 bytes"; the same command in the foreground → "exit=0, out=8804 bytes, err=491925 bytes". Broken in 0.124.0 (binary mtime ~2026-04-24) and 0.125.0; unaffected in 0.123.0. Affected contexts listed: "Claude Code's Bash tool with run_in_background: true", custom CI runners, MCP-based pipelines, SSH-spawned background processes. Effective workaround: keep in foreground with direct file redirect, or wrap with `script -qfc "codex exec ..." /dev/null` (which re-attaches a pseudo-TTY but logs a "failed to record rollout items" ERROR). Piping to tee/tail while detached via setsid does NOT work. Status: open, unassigned, no replies.

**SRC:** https://github.com/openai/codex/issues/19945 (binary mtime cited as ~2026-04-24; issue otherwise undated)

## F4 [high] [forum-or-practitioner]
**CLAIM:** The same stdin bug bites MCP bridges specifically because Node's `spawn` with `stdio: ['pipe','pipe','pipe']` never closes the child's stdin. If you wire Codex into Claude Code as an MCP server, the fix is `child.stdin.end()` or `stdio: ['ignore','pipe','pipe']` — not a wrapper script, which the reporter found fragile.

**EVIDENCE:** codex-mcp-server issue #153: "the spawned codex subprocess received stdio: ['pipe','pipe','pipe'] configuration but the MCP server implementation never invoked child.stdin.end(). Since stdin remained perpetually open without closure, Codex continued waiting for EOF." Proposed: add `child.stdin.end()` in `dist/utils/command.js`, or use `'ignore'` for stdin. "Workaround: Route codex invocations through a wrapper script redirecting stdin from /dev/null, though this approach proved fragile with MCP clients." Opened April 8, 2026; codex-mcp-server v1.4.2, Codex CLI v0.118.0, macOS arm64.

**SRC:** https://github.com/tuannvm/codex-mcp-server/issues/153 (2026-04-08)

## F5 [high] [vendor-doc]
**CLAIM:** Official guidance has moved away from `--full-auto` (now deprecated with a warning). For unattended runs the documented shape is explicit `--sandbox <mode>` plus `--ask-for-approval never`; `codex exec` defaults to a READ-ONLY sandbox, so an automation that forgets `--sandbox workspace-write` will silently fail to write rather than prompt.

**EVIDENCE:** OpenAI non-interactive docs: "By default, codex exec runs in a read-only sandbox"; modes are read-only / workspace-write / danger-full-access; "Note: --full-auto is deprecated with a warning." Also: "Git repository required to prevent destructive changes" (override with --skip-git-repo-check); "MCP servers configured with required = true cause exit on initialization failure"; `--output-schema` enforces JSON Schema but is "incompatible with codex exec resume" and requires gpt-5-family models. Third-party CI guide corroborates: "Add --ask-for-approval never for unattended runs."

**SRC:** https://learn.chatgpt.com/docs/non-interactive-mode.md (undated (no date shown on the doc page))

## F6 [medium] [third-party-commentary]
**CLAIM:** For parallel batch work you must pass `--ephemeral`; without it concurrent `codex exec` instances corrupt each other through shared session-restore files. Practical concurrency ceiling reported is 4–6 workers before 429s.

**EVIDENCE:** "Session conflicts: Parallel instances without --ephemeral interfere via shared restore files" and "Caveat: Four concurrent sessions is recommended; monitor for rate-limit 429 errors" / "Cap parallel concurrency at 4–6 sessions per API tier." Same page documents `--ephemeral` as "Skips session persistence; prevents parallel conflicts."

**SRC:** https://codex.danielvaughan.com/2026/04/18/codex-cli-headless-batch-mode-automation/ (2026-04-18 (updated 2026-09-01))

## F7 [high] [forum-or-practitioner]
**CLAIM:** On Linux, the recurring 'command failed; retry without sandbox?' prompt in automation is usually the bubblewrap sandbox failing to START, not a real policy denial. Ubuntu 24.04+ blocks unprivileged user namespaces by default and ships no bwrap AppArmor profile. Setting `sandbox_mode = "workspace-write"` does NOT fix it.

**EVIDENCE:** Issue #17337: exact error "bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted", user-facing "Reason: command failed; retry without sandbox?". Codex CLI 0.118.0 (also 0.117.0, 0.118.8), Ubuntu 24.04, kernel 6.8.0-100-generic. "Setting sandbox_mode = "workspace-write" alone does not resolve the issue." Successful fix: add `[features]\nuse_legacy_landlock = true` to ~/.codex/config.toml. Opened April 10, 2026; closed.

**SRC:** https://github.com/openai/codex/issues/17337 (2026-04-10)

## F8 [high] [forum-or-practitioner]
**CLAIM:** The cleaner root-cause fix for the bwrap failure on Ubuntu 24.04 is an AppArmor profile for bwrap, verified with a one-line reproducer — preferable to disabling the sandbox or falling back to legacy Landlock.

**EVIDENCE:** Practitioner reproduces with `bwrap --dev-bind / / --unshare-net echo ok` → "bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted". Cause: "Ubuntu 24.04 enables kernel.apparmor_restrict_unprivileged_userns=1 by default... but no bwrap profile ships by default." Fix: create /etc/apparmor.d/bwrap containing `abi <abi/4.0>, include <tunables/global>, profile bwrap /usr/bin/bwrap flags=(unconfined) { userns, include if exists <local/bwrap> }` then `sudo apparmor_parser -r /etc/apparmor.d/bwrap`; verify the reproducer returns `ok`.

**SRC:** https://www.jdhodges.com/blog/codex-sandbox-ubuntu-24-04-fix/ (2026-04-23)

## F9 [high] [vendor-doc]
**CLAIM:** Under ChatGPT-subscription auth, headless `codex exec` draws from the SAME rolling 5-hour window as interactive CLI use — there is no separate headless pool. Local CLI messages, cloud tasks, and Code Review all share one budget. The only way to isolate automation spend is the API-key path, which is pay-as-you-go with no fixed rate limits.

**EVIDENCE:** Vendor pricing doc: "Codex operates on rolling 5-hour windows for local messages and cloud chats. Additional weekly limits may apply"; "Local messages, cloud chats, and Code Review all draw from a shared usage budget across ChatGPT plans (Plus, Pro, Business)"; "API Key users operate on pay-as-you-go pricing — pay only for the tokens Codex uses, based on API pricing, with no fixed rate limits." Third-party CI guide states it plainly: "ChatGPT plan users should note that headless runs draw from the same 5-hour rolling message window as interactive sessions."

**SRC:** https://learn.chatgpt.com/docs/pricing (undated vendor doc (per-plan tables reference GPT-5.6 Sol/Terra/Luna, so current as of fetch 2026-09-01))

## F10 [medium] [third-party-commentary]
**CLAIM:** There is NO per-run cost cap in the Codex CLI itself. The only protection against a runaway scheduled job is a spending limit set in the OpenAI dashboard — set it before the first nightly cron, not after.

**EVIDENCE:** "There is no per-run cost cap in the CLI itself — your protection is a usage budget set in the OpenAI dashboard." Set spending limits before scheduling nightly jobs.

**SRC:** https://www.developersdigest.tech/blog/codex-exec-ci-headless-guide (2026-06-10 (updated 2026-06-28))

## F11 [high] [forum-or-practitioner]
**CLAIM:** A concrete and underappreciated cost blowout: verbose child-process stdout is fed straight into model context, so a single long-running noisy command can consume an entire token allowance with almost no reasoning happening. Anyone running codex exec over build/convert/rsync-style tools should redirect that output to a file, not let Codex observe it.

**EVIDENCE:** OpenAI community report: user processed a 33 GB file with an external conversion tool producing "tens of millions or potentially over 100 million lines" of progress output over ~35 minutes; Codex "continuously consumed and analyzed this repetitive output, exhausting the user's entire token allowance despite minimal actual reasoning occurring." Quote: "The amount of stdout generated by a child process should never translate directly into model token consumption." Requested mitigation: a configurable `max_command_output_tokens = 10000`. Posted August 25, 2026; no replies indicating an existing mitigation.

**SRC:** https://community.openai.com/t/codex-need-stdout-stderr-overflow-handling-all-my-credits-are-gone/1392556 (2026-08-25)

## F12 [medium] [forum-or-practitioner]
**CLAIM:** Quota can drain with no session running. One Pro user reported the 5-hour window at 100% drained, ~139,905 credits burned, and the weekly cap dropping 67%→45% with no active Codex session — suspected cause was the experimental `memory_tool` / `search_tool` features. Treat experimental `[features]` flags as a cost risk in unattended setups.

**EVIDENCE:** Issue #11508 (BjornMelin, 2026-02-12, closed): "5 hour limit...100% drained"; "139.905 credits...all burned through"; weekly "from 67%...to now down to 45%" with no active codex session. Config: `[features] memory_tool = true, search_tool = true`. codex-cli 0.99.0, Pro tier, gpt-5.3-codex, WSL2. No maintainer resolution documented.

**SRC:** https://github.com/openai/codex/issues/11508 (2026-02-12)

## F13 [medium] [forum-or-practitioner]
**CLAIM:** Practitioner-reported burn rate on the ChatGPT plan: roughly 6–7 fully-used 5-hour windows exhausts the weekly cap, after which lockouts of 3–5 days are reported. Several practitioners' documented fallback is switching to the API key during the lockout at roughly a couple of euros/day.

**EVIDENCE:** openai/codex Discussion #2251: "Hit the weekly cap after ~6–7 full sessions. One 'session' = fully using the 5-hour cap"; messages like "try again in 3 days 13 hours 6 minutes" and "wait for 5 days". Token figures reported: ~1.5M input in one conversation; another "2249742 input + 35030528 cached". API fallback: "when I ran out of limits, I used the API and consumed about €2 per day." Also reported: "limits in web codex and codex cli are totally separate."

**SRC:** https://github.com/openai/codex/discussions/2251 (undated in fetched content (ongoing discussion thread))

## F14 [high] [vendor-doc]
**CLAIM:** For CI, the documented-secure pattern is a two-job split: job one runs Codex read-only with the API key and emits a patch as an artifact; job two applies the patch with write permissions and NO API key in scope. Never set OPENAI_API_KEY/CODEX_API_KEY as a job-level env var in a job that also checks out untrusted code.

**EVIDENCE:** Vendor doc warning: "Never set OPENAI_API_KEY or CODEX_API_KEY as job-level environment variables in workflows checking out untrusted code. Build scripts, tests, dependency lifecycle hooks, or a compromised action in the same job can read those environment variables." Documented GH Actions example: "(1) detect CI failure, (2) run Codex with read-only permissions, (3) serialize diff as artifact, (4) apply patch in separate job with write permissions — separating credential exposure from code execution." Third-party guide gives the action form: `uses: openai/codex-action@v1` with `openai-api-key: ${{ secrets.OPENAI_API_KEY }}`.

**SRC:** https://learn.chatgpt.com/docs/non-interactive-mode.md (undated vendor doc)

## F15 [high] [vendor-doc]
**CLAIM:** For headless machines that must use subscription auth rather than an API key, the supported path is `codex login --device-auth`; otherwise you copy `~/.codex/auth.json` from a logged-in machine. That file is a live credential and the vendor explicitly says to treat it as a password.

**EVIDENCE:** Auth doc: "For environments without browser access, use codex login --device-auth. You'll receive a code to enter in a browser on another machine — useful for remote or CI environments." "If device code isn't available, complete login elsewhere and copy ~/.codex/auth.json to your headless machine via SSH or Docker." Warning: "Treat ~/.codex/auth.json like a password: it contains access tokens. Don't commit it, paste it into tickets, or share it in chat." API key form: `printenv OPENAI_API_KEY | codex login --with-api-key`. Storage configurable via `cli_auth_credentials_store = "keyring"` or `"file"`.

**SRC:** https://learn.chatgpt.com/docs/auth.md (undated vendor doc)

## F16 [high] [forum-or-practitioner]
**CLAIM:** The most rigorous published Claude-drives-Codex pattern shells out to a WRAPPER SCRIPT rather than using the Codex MCP server, precisely to get supervision the MCP path doesn't give: a 5-minute idle-output watchdog, session-ID capture for cheap multi-turn follow-ups, and a pinned read-only sandbox. The agent's instructions hard-forbid the MCP route.

**EVIDENCE:** Steve Kinney (2026-06-04): shells out to `codex-review.sh` which invokes `codex exec`; agent instruction is "Always use codex-review.sh. Never call the Codex MCP tools directly." Three supervision layers: "Idle-timeout watcher — terminates Codex if output stalls for five minutes, preventing hung sessions"; "Session ID capture — enables multi-turn consultations without resending full context"; "Read-only sandbox — process-level constraint pinning the model profile (gpt-5.4 at xhigh reasoning) while preventing file modifications." Also uses "doghouse sentinel files to back off automatically for one hour" on rate limits, and fail-warn semantics so a Codex outage degrades rather than blocks.

**SRC:** https://stevekinney.com/writing/codex-as-a-second-opinion (2026-06-04)

## F17 [high] [forum-or-practitioner]
**CLAIM:** The stated reason for the cross-family split (Claude implements, Codex reviews) is correlated blind spots, not raw capability: a model reviewing its own work is confidently wrong in the same direction. The operational payoff is the agree/disagree signal, and the reviewer's output should be SYNTHESIZED by the caller, never forwarded verbatim, to avoid laundering unexamined confidence.

**EVIDENCE:** Kinney: "When Claude reviews its own work while confidently wrong, it remains confidently wrong in the same direction. A differently-trained model encounters different failure modes." "When the two of them agree I trust the answer more, and when they disagree I've learned something about where the hard part actually lives." Gotcha named: "Outsourcing judgment — the agent synthesizes Codex's response rather than forwarding it verbatim." Prompt pattern: every consultation includes guardrail language making Codex a "text-only advisory" that must not read files, run commands, or make changes, and must ASK for context rather than explore the codebase itself.

**SRC:** https://stevekinney.com/writing/codex-as-a-second-opinion (2026-06-04)

## F18 [high] [forum-or-practitioner]
**CLAIM:** A widely-installed Claude Code skill encodes the exact invocation contract for driving Codex, including three non-obvious rules: suppress stderr with `2>/dev/null` (thinking tokens otherwise bloat Claude's context), always close stdin, and pass NO flags on `resume`. It also publishes per-reasoning-effort timeouts (low 150s → max/ultra 1800s).

**EVIDENCE:** skill-codex SKILL.md. New session: `codex exec -m <MODEL> --config model_reasoning_effort="<EFFORT>" --sandbox <MODE> --skip-git-repo-check "prompt" 2>/dev/null`. Resume: `echo "prompt" | codex exec --skip-git-repo-check resume --last 2>/dev/null`. Gotchas verbatim: "If stdin is not closed, codex blocks forever" (append `</dev/null`); "Append 2>/dev/null to suppress thinking tokens"; on resume "no flags allowed"; "No intermediate output: Codex produces results only at completion; early termination leaves output silently empty"; "Always use --skip-git-repo-check." Default sandbox read-only; default model gpt-5.6-sol at high effort. Timeouts: low 150s, medium 300s, high 600s, xhigh 1200s, max/ultra 1800s.

**SRC:** https://raw.githubusercontent.com/skills-directory/skill-codex/main/plugins/skill-codex/skills/codex/SKILL.md (undated (repo file; model list includes gpt-5.6 tiers, so current as of fetch 2026-09-01))

## F19 [medium] [own-inference]
**CLAIM:** The 'no intermediate output' property is the deciding constraint for orchestration design: `codex exec` emits nothing until completion, so a killed or timed-out run yields an EMPTY result, not a partial one. Any orchestrator must budget the full timeout and treat empty output as failure, not as 'no findings'.

**EVIDENCE:** skill-codex SKILL.md: "No intermediate output: Codex produces results only at completion; early termination leaves output silently empty." This compounds with issue #19945 where a detached-TTY crash also produces exit=0 with 0 bytes — the same observable signature as a successful-but-empty run.

**SRC:** https://raw.githubusercontent.com/skills-directory/skill-codex/main/plugins/skill-codex/skills/codex/SKILL.md (undated (repo file, fetched 2026-09-01))

## F20 [high] [forum-or-practitioner]
**CLAIM:** The mature parallel-Codex pattern is external orchestration, not Codex-internal subagents: build the queue outside Codex, give each worker its own git worktree, run workers as `codex exec` with explicit non-interactive flags, have workers emit PATCHES, and let a supervisor merge sequentially with tests. Do not let two workers edit one working tree, and do not keep task state in a model-edited JSON file.

**EVIDENCE:** openai/codex Discussion #3898, answer dated 2026-06-14 by hoodrichpirobo. Worker command: `codex exec --cd "$WORKTREE" --sandbox workspace-write --ask-for-approval never --json -o "$OUT/result.md" "$PROMPT"`. Lessons: "Do not let multiple workers edit the same working tree at the same time"; "Use transactional databases (SQLite/Postgres/Redis) rather than model-edited JSON"; track `queued | running | done | failed` with "leases/expiry, not locks"; "Workers produce patches; supervisor merges sequentially with tests." What didn't work: "Expecting MCP alone to handle locking, retries, or conflict resolution." (Original question posted 2025-09-19.)

**SRC:** https://github.com/openai/codex/discussions/3898 (answer 2026-06-14; question 2025-09-19)

## F21 [medium] [third-party-commentary]
**CLAIM:** Codex's own in-session subagents default to `max_threads = 6` and `max_depth = 1`, and the docs warn that raising max_depth causes recursive fan-out with runaway token/latency cost. Practitioner guidance converges on 3–5 parallel agents because the real bottleneck is human review throughput, not agent throughput.

**EVIDENCE:** Firecrawl (2026-06-08): `.codex/config.toml` `[agents] max_threads = 6, max_depth = 1`; docs warn raising max_depth "can turn broad delegation instructions into repeated fan-out, which increases token usage, latency, and local resource consumption." "Subagents consume more tokens than comparable single-agent runs" because each keeps its own context window. "Three to five teammates" recommended: "three focused teammates consistently outperform five scattered ones." Cited practitioner constraint: "the natural bottleneck on all of this is how fast I can review the results." Worktree fan-out example given: `git worktree add "../$task" -b "$task"` then `codex exec --sandbox workspace-write "Implement the $task ticket. Run the tests before finishing." &` in a loop with `wait`. Noted new failure mode: "Dependencies are missing unless you actively set them up."

**SRC:** https://www.firecrawl.dev/blog/codex-multi-agent-orchestration (2026-06-08)

## F22 [low] [third-party-commentary]
**CLAIM:** The dominant community split is Claude Code for architecture/scaffolding/vague-brief planning, Codex for debugging/review/atomic fine-detail fixes — with the stated reason being task specification granularity, not model quality: Codex needs tasks broken into atomic steps, Claude tolerates vague larger tasks.

**EVIDENCE:** Reddit-corpus analysis: "The most-upvoted workflow in 2026 is Claude Code for architecture, scaffolding and UI, then Codex for debugging, review and fine-detail fixes"; quoted patterns "Codex is precise and fast, but it needs you break down task into atomic steps" vs Claude handles work that is "vague and needs an agent that plans and restructures"; Codex reported at "50–75% of the token spend" for equivalent output; Claude stronger in "long, tool-heavy sessions." Caveat the source itself raises: "r/codex threads trend pro-Codex, r/ClaudeCode threads trend pro-Claude, and each accuses the other of astroturfing." Sentiment shift noted: 2026 threads moved from code-quality debates to "subscription math, rate limits and dollars per task."

**SRC:** https://duply.ai/blog/claude-code-vs-codex-reddit (undated aggregation page (content references July 2026 shifts))

## F23 [medium] [forum-or-practitioner]
**CLAIM:** The cost of the Codex-as-reviewer split is a real false-positive rate: practitioners report Codex confidently inventing plausible concurrency/edge-case bugs in Claude's code that don't exist. The practical mitigation reported is not picking a winner but forcing adjudication — making them argue and writing tests to settle it.

**EVIDENCE:** HN thread 46391391. veidr: "Codex sometimes flags nonexistent bugs in Claude's code — less annoying... I just let them duke it out, writing tests"; and "Codex comes up with plausible edge-case database query concurrency bugs... only to conclude yeah, not true, you're hallucinating." dworks describes the reverse order: Codex implements, "Then I ask Opus to take a pass and clean up to match codebase specs." oldandboring on automation friction: "no amount of prompting could get it to stop aggressively asking me for permission to do things." pitched on why the split is stable: "With Codex, the limits are higher than my own usage so I never see them."

**SRC:** https://news.ycombinator.com/item?id=46391391 (undated in fetched content (HN item 46391391))

## F24 [medium] [forum-or-practitioner]
**CLAIM:** A published two-agent handoff pattern uses a shared append-only coordination file (`changes.log`) that both agents read before and write after each turn, recording what changed, which agent changed it, which files were touched, and context for the next agent. The authors' conclusion is that the file, not the tool choice, was the load-bearing part.

**EVIDENCE:** aimaker (2026-06-14, Wyndo and Dheeraj Sharma): both tools read/write `changes.log` before and after work; Claude Code uses CLAUDE.md, Codex imports these into AGENTS.md; handoff contents are "what changed and which agent made changes / which files were touched / context for the next agent." Worked example alternates Claude (backend/feature) → Codex (UI + browser verification) → Claude (rebrand). Key finding quoted: "The useful part was not choosing one tool, it was giving both tools a simple way to stay in sync."

**SRC:** https://aimaker.substack.com/p/claude-code-vs-codex (2026-06-14)

## F25 [low] [third-party-commentary]
**CLAIM:** A symmetric adversarial-review pattern exists in both directions and is packaged as a skill: Claude spawns Codex reviewers via `codex exec`, Codex spawns Claude reviewers via `claude -p`, 1–3 independent reviewers on the opposing family review a diff, then attempt to refute each other's findings, and only survivors are reported with confidence levels. Billing note: Codex calls from Claude draw on the Plus/Pro plan, separate from Anthropic's Max allowance.

**EVIDENCE:** Search-surfaced description of the adversarial-review skill: "spawns 1–3 independent reviewers on the opposing model (Claude spawns Codex via codex exec; Codex spawns Claude via claude -p)... Two different model families review the diff independently, then try to refute each other's findings; survivors are reported by confidence." Also: "as of June 5th 2026, Anthropic started charging for CLI- and SDK-invoked sessions separately from what's included in your Max plan, but calls to Codex come out of your normal Plus or Pro plan." Repo: github.com/robertoecf/adversarial-review.

**SRC:** https://github.com/robertoecf/adversarial-review (undated (billing detail cited as 2026-06-05); NOTE: surfaced via search result text, repo page not fetched in full)

## F26 [medium] [forum-or-practitioner]
**CLAIM:** Multi-agent bridge tooling that manages separate authenticated homes per provider is real but operationally fragile — the leading example has repeatedly withdrawn releases over session/state regressions, socket-path-length failures, and provider auth timeout restart loops. Session/state loss is a first-class risk when you persist agent sessions across providers.

**EVIDENCE:** claude_codex_bridge changelog: v8.5.5 "Withdrawn on August 5, 2026, due to 'legacy-session migration regression made existing managed conversations unavailable to native resume'"; v8.1.6–8.1.5 also withdrawn; "Socket path length issues requiring automatic relocation to short paths"; "Provider authentication timeouts and restart loops addressed in v8.2.1." Architecture: "separate managed homes for each provider with isolated authentication, session state, and storage", plus for Codex specifically "bounded terminal error evidence" and "reconnect supervision."

**SRC:** https://github.com/SeemSeam/claude_codex_bridge (2026-08-05 (v8.5.5 withdrawal))

## F27 [low] [forum-or-practitioner]
**CLAIM:** Codex's output truncation is itself a documented source of corruption and lost signal in automated pipelines: token-aware truncation elides the middle of command output, truncation framing text has leaked into adjacent payloads corrupting API requests, and critical markers like 'panic'/'abort' get truncated away rather than preserved.

**EVIDENCE:** Issue #24582 title: "code-mode rollout: exec_command stdout framing leaks into input_image base64, corrupting Responses API requests" — the "…N tokens truncated…" header gets injected into an input_image.image_url payload in the same buffer flush. Issue #9502 title: "Critical Error Messages Get Truncated During Output Truncation" — requests that truncation preserve "panic"/"abort" patterns. Truncation behavior described as preserving beginning and end while eliding the middle.

**SRC:** https://github.com/openai/codex/issues/24582 (undated; NOTE: these two issues were surfaced via search-result titles/snippets and were not fetched in full)


## GAPS
- NEGATIVE RESULT — nobody has a good answer for measuring per-run headless Codex quota burn. There is no per-run cost cap in the CLI, no documented way to preflight 'will this exec exhaust my window', and the only control is a dashboard-level spend limit that applies to the API-key path, not the ChatGPT-subscription path. Practitioners cope with sentinel-file backoff (Kinney's 'doghouse') and rotating subscriptions, not measurement.
- NEGATIVE RESULT — no quantified false-positive rate for Codex-as-reviewer. Every account of the Claude-implements/Codex-reviews split is anecdotal ('Codex finds real bugs', 'Codex hallucinates plausible concurrency bugs'). No benchmark, no precision/recall numbers, no published count of findings-per-review that survived adjudication. The best available adjudication method is 'make them argue and write a test'.
- NEGATIVE RESULT — the stdin/TTY class of bugs (#20919, #27019, #19945, codex-mcp-server #153) is still open and unassigned as of the fetched content, spanning versions 0.118 through 0.133 and at least five months. There is no `--no-stdin` flag despite repeated requests, and no maintainer statement of a canonical fix. Automation authors are carrying the `</dev/null` + foreground-TTY workaround indefinitely.
- Could not verify whether the detached-TTY silent-crash regression (#19945, introduced 0.124.0) was ever fixed in a later release — the issue shows no replies and I found no changelog entry either way. This matters most for anyone spawning codex exec from Claude Code with run_in_background: true.
- No dated vendor statement found on whether `codex exec` runs are metered identically to interactive turns (e.g. whether the reasoning/thinking tokens suppressed by 2>/dev/null still bill). The 'same shared pool' claim is documented; token-for-token equivalence is not.
- Two potentially strong practitioner sources returned 403 and could not be read: littlemight.com's Codex second-opinion skill writeup, and Balazs Kocsis's Medium piece on automating Codex CLI on a ChatGPT Plus subscription (the most on-point source found for headless subscription auth in cron). Their claims are unverified here.
- Could not find a 2026 conference talk on this topic. All substantive material is GitHub issues, personal blogs, HN, and skill repos.
- Codex-spawned-from-within-Codex is reported to enter an infinite hyper_util connection-reuse loop (openai/codex issue #3216), which would matter for recursive orchestration, but I could not fetch the issue or establish its date/status — treat as unverified.
- The whole class of SEO-generated 'Codex Knowledge Base' sites (codex.danielvaughan.com and similar) dominates search results for these queries and is difficult to distinguish from real practitioner writing. Where their claims are load-bearing above I flagged them third-party-commentary at medium/low confidence; several could not be corroborated against a primary source.

## SOURCES
- https://learn.chatgpt.com/docs/non-interactive-mode.md
- https://learn.chatgpt.com/docs/pricing
- https://learn.chatgpt.com/docs/auth.md
- https://github.com/openai/codex/issues/20919
- https://github.com/openai/codex/issues/27019
- https://github.com/openai/codex/issues/19945
- https://github.com/openai/codex/issues/17337
- https://github.com/openai/codex/issues/11508
- https://github.com/openai/codex/discussions/2251
- https://github.com/openai/codex/discussions/3898
- https://github.com/tuannvm/codex-mcp-server/issues/153
- https://github.com/SeemSeam/claude_codex_bridge
- https://raw.githubusercontent.com/skills-directory/skill-codex/main/plugins/skill-codex/skills/codex/SKILL.md
- https://stevekinney.com/writing/codex-as-a-second-opinion
- https://community.openai.com/t/codex-need-stdout-stderr-overflow-handling-all-my-credits-are-gone/1392556
- https://www.jdhodges.com/blog/codex-sandbox-ubuntu-24-04-fix/
- https://www.developersdigest.tech/blog/codex-exec-ci-headless-guide
- https://www.firecrawl.dev/blog/codex-multi-agent-orchestration
- https://aimaker.substack.com/p/claude-code-vs-codex
- https://news.ycombinator.com/item?id=46391391
- https://duply.ai/blog/claude-code-vs-codex-reddit
- https://codex.danielvaughan.com/2026/04/18/codex-cli-headless-batch-mode-automation/
- https://pablostanley.substack.com/p/a-heated-rivalry-claude-code-openai
- https://www.littlemight.com/claude-code-second-opinion-codex-skill/
- https://medium.com/@balazskocsis/automate-with-codex-cli-on-chatgpt-plus-subscription-d4f5c1e0c9a9
