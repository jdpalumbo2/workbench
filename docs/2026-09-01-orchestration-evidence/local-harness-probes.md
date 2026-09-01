> UNAUDITED evidence sweep, captured 2026-09-01 — verify before relying.
> Every number below came from a command run on this machine that night. Nothing here is
> cited from documentation, and nothing here has been re-run since capture.

# Local harness probes — what the two CLIs actually do on this machine

Machine: macOS 26.6.2 (arm64). Captured 2026-09-01 ~01:05–01:15 local.
Purpose: ground the orchestrator redesign in measured behavior instead of assumed behavior.

---

## 1. Codex CLI — installed version and model roster

```
$ codex --version
codex-cli 0.144.6            # `codex doctor` reports 0.152.0 available
$ codex login status
Logged in using ChatGPT
```

`~/.codex/models_cache.json`, `fetched_at: 2026-09-01T05:04:17Z`, `client_version: 0.144.6`.
Nine models offered; `context_window` is the default, `max_context_window` the ceiling.

| slug | vendor description | priority | ctx / max ctx | notes |
|---|---|---|---|---|
| `gpt-5.6-sol` | "Latest frontier agentic coding model." | 1 | 272k / 872k | default effort `low`; supports `max`; `multi_agent_version: v2` |
| `gpt-5.6-terra` | "Balanced agentic coding model for everyday work." | 2 | 272k / 872k | default effort `medium`; supports `max` |
| `gpt-5.6-luna` | "Fast and affordable agentic coding model." | 3 | 272k / 872k | default effort `medium`; `multi_agent_version: v1` |
| `gpt-reserve` | (hidden) same text as luna | 3 | 272k / 872k | `visibility: hide` |
| `gpt-5.5` | "Frontier model for complex coding, research, and real-world work." | 7 | 272k / 272k | no `max` effort |
| `gpt-5.4` | "Strong model for everyday coding." | 16 | 272k / 1M | **deprecating** → upgrade path names `gpt-5.6-terra` |
| `gpt-5.4-mini` | "Small, fast, and cost-efficient model for simpler coding tasks." | 23 | 272k / 272k | **deprecating** → upgrade path names `gpt-5.6-luna` |
| `gpt-5.3-codex-spark` | "Ultra-fast coding model." | 26 | 128k / 128k | `supported_in_api: false`; its own system prompt states ~1.5k tok/s sampling |
| `codex-auto-review` | "Automatic approval review model for Codex." | 43 | 272k / 872k | `visibility: hide` — the model behind Codex's own approval review |

Effort ladder on the 5.6 family: `low · medium · high · xhigh · max`. On 5.5/5.4: no `max`.

**Bearing on the current clodex runner.** `runner/run-codex.sh:103-108` picks
`gpt-5.6-luna` for the `implementer` role and `gpt-5.6-sol` for every review role. Against
the roster above, that puts the *cheapest* model on code-writing and the *frontier* model on
reading the result. That may well be deliberate (review is where a wrong call is most
expensive) but it is worth a decision rather than an inheritance.

---

## 2. Codex quota is machine-readable — and this is the single most useful find of the night

Every Codex session writes a rollout file under `~/.codex/sessions/<Y>/<M>/<D>/`. The
turn record carries a live quota meter:

```json
"rate_limits": {
  "limit_id": "codex", "limit_name": null,
  "primary": {"used_percent": 9.0, "window_minutes": 10080, "resets_at": 1788796390},
  "secondary": null,
  "credits": {"has_credits": false, "unlimited": false, "balance": "0"},
  "individual_limit": null, "plan_type": "prolite", "rate_limit_reached_type": null
}
```

Read as of 2026-09-01 01:14 local:

- **Window is 7 days** (`window_minutes: 10080`), resetting **2026-09-07 10:53 local**.
- **9% consumed** with six days left in the window.
- **No credit balance to fall back on** (`has_credits: false`, `balance: "0"`) — when the
  weekly window is spent, Codex stops. There is no overage to drift into.
- Plan tier reported as `prolite`.

Meter trajectory sampled from the last dozen rollouts: 7% → 8% at 23:36 on 08-31, 8% steady
through 00:04, 9% after the two probes below. The meter moves in whole percents, so it is a
coarse instrument at small volumes and a precise one at fan-out volumes.

**Why this matters:** a quota constraint that a script can *read* is a tier-3 control. An
orchestrator can refuse to launch invocation N+1 when `used_percent` crosses a line, and can
report spend as a measured delta rather than an estimate. Contrast the premium-Claude
constraint that motivated this whole exercise, which had no such meter in front of it.

Extraction one-liner (no secrets touched — the meter lives in the rollout, not in `auth.json`):

```bash
python3 - <<'PY'
import glob, json, os, re
f = max(glob.glob(os.path.expanduser("~/.codex/sessions/**/*.jsonl"), recursive=True),
        key=os.path.getmtime)
for line in open(f):
    if '"rate_limits"' in line:
        frag = line[line.find('"rate_limits"'):]
        print(re.search(r'"used_percent":\s*([\d.]+)', frag).group(1))
        break
PY
```

---

## 3. The mixed-auth warning is real but benign — verified, not assumed

`codex doctor` reports:

```
⚠ auth   mixed auth signals: ChatGPT login plus API key env var;
         HTTP reachability uses API-key mode
```

`OPENAI_API_KEY` is exported from `~/.zshenv`; `~/.codex/auth.json` has `auth_mode: chatgpt`
and no stored API key. The live question was whether headless Codex runs bill metered API
usage instead of the subscription — which would make a Codex-heavy orchestrator quietly
expensive.

Probe: the same trivial prompt run twice, once with the env var present and once with
`env -u OPENAI_API_KEY`.

| probe | command | rc | result |
|---|---|---|---|
| A | `codex exec --json --sandbox read-only -m gpt-5.6-luna` (env var present) | 0 | `CODEX_PROBE_OK` |
| B | same, under `env -u OPENAI_API_KEY` | 0 | `CODEX_PROBE_OK` |

**Both rollouts recorded the `plan_type: prolite` subscription meter, and both moved it.**
So model calls go to the ChatGPT subscription in either case; the doctor warning is about the
reachability probe, not about billing. Good news — but it was worth ninety seconds to
establish rather than assume, and the check belongs in preflight because the answer could
change with a CLI upgrade.

## 4. `codex exec` event stream — what a caller can and cannot read back

Event types emitted for a one-turn run: `thread.started`, `turn.started`, `item.completed`,
`turn.completed`.

```json
{"type": "thread.started", "thread_id": "01a05b9a-6ebb-7391-a634-b34c481b8577"}
{"type": "turn.completed", "usage": {"input_tokens": 14510, "cached_input_tokens": 8960,
                                     "output_tokens": 9, "reasoning_output_tokens": 0}}
```

- **The stream is live.** During the 12-minute plan-review round in the plan's section C, the
  `--json` event file was 490 KB and growing while the process was still running. So a caller can
  read partial progress and a liveness signal; an orchestrator does not have to budget for an
  all-or-nothing timeout. (`run-codex.sh` already exploits this — its heartbeat tails the event
  file for the last event type.)
- Token usage **is** readable per turn, cached input broken out separately.
- The **model that actually ran is not echoed** anywhere in the event stream. A caller knows
  which model it *requested*; the transcript does not confirm which model *answered*. The
  rollout file under `~/.codex/sessions/` does carry richer turn metadata — that is where a
  verification check has to look, not the `--json` stream.

`codex exec` also exposes two subcommands worth noting for the redesign: `codex exec resume`
(session continuation, already used by the clodex runner) and `codex exec review` (a
first-party non-interactive code review). `codex mcp-server` runs Codex as a stdio MCP
server, which is a second integration route entirely.

---

## 5. Claude Code headless — the JSON envelope is a real arithmetic surface

```
$ claude --version
2.1.224 (Claude Code)
```

`claude -p --output-format json` returns a machine-readable envelope. Fields that matter for
orchestration, from a live probe:

```json
{"is_error": false, "subtype": "success", "terminal_reason": "completed",
 "session_id": "b93ad07f-...", "num_turns": 1, "stop_reason": "end_turn",
 "total_cost_usd": 0.0314988,
 "modelUsage": {"claude-haiku-4-5-20251001": {"inputTokens": 10, "outputTokens": 64,
   "cacheReadInputTokens": 18048, "cacheCreationInputTokens": 14682,
   "costUSD": 0.0314988, "contextWindow": 200000, "canonicalModel": "claude-haiku-4-5"}},
 "permission_denials": [], "result": "PROBE_OK"}
```

Per-invocation cost, per-model attribution, permission denials, and a resumable
`session_id` — all without parsing prose. A budget ceiling enforced against `total_cost_usd`
is arithmetic, not exhortation.

### 5a. Slash-invoked skills work headlessly — confirmed

```
$ claude -p --model haiku --output-format json \
    "/empirical-falsification Do no work. Reply with exactly PROBE4."
result: PROBE4 | models: ['claude-haiku-4-5-20251001'] | cost: 0.0246715
```

An earlier probe of the same shape returned `# Empirical Falsification` — the skill file's
first heading — when asked to echo what it had loaded. So a script can invoke a named skill
in a fresh headless session. That is the mechanism a programmatic QA gate needs.

### 5b. `--permission-mode plan` has a capability floor and silently upgrades below it

Six probes, run 01:05 and 01:47 local. All used `-p --output-format json`; the model column is
read back from `modelUsage`, not from the flag.

| # | flags | model requested | model that ran | cost |
|---|---|---|---|---|
| 1 | `--model haiku` | haiku | claude-haiku-4-5 | $0.0315 |
| 2 | `--model haiku --permission-mode plan` + slash skill | haiku | **claude-sonnet-5** | $0.2841 |
| 3 | `--model haiku --permission-mode plan` | haiku | **claude-sonnet-5** | $0.1038 |
| 4 | `--model haiku` + slash skill | haiku | claude-haiku-4-5 | $0.0247 |
| 5 | `--model sonnet --permission-mode plan` | sonnet | claude-sonnet-5 | $0.3026 |
| 6 | `--model opus --permission-mode plan` | opus | claude-opus-5 | $0.3923 |

Probes 5 and 6 were added after an adversarial reviewer pointed out that the first four did not
isolate the cause and that my stated hypothesis contradicted my own observation. They settle it:

- **Plan mode honors `sonnet` and `opus`.** It does not honor `haiku`.
- So the mechanism is **a capability floor in plan mode**, with a silent upgrade to the account
  default below it — not the `opusplan` alias routing, which was my first guess and which would
  have produced Opus, not Sonnet, on a planning turn.
- The first draft's "four times the cost" line compared probe 3 against probe 4, which changed two
  variables. Against the correct baseline (probe 1 vs probe 3) the upgrade costs **3.3x**.

The design lesson is unchanged and is the whole point of an arithmetic gate: **do not trust the
flag you passed. Read `modelUsage` back and fail the step when the model that ran is not the model
that was asked for.** Scope: six probes, one machine, CLI 2.1.224. A reproduced local observation,
not a documented contract.

### 5c. `--bare` cannot run on the subscription — it fails outright

Anthropic recommends `claude --bare -p` for scripted invocation and says it will become the `-p`
default. Its help text carries a consequence that is easy to read past:

```
--bare   Minimal mode: skip hooks, LSP, plugin sync, attribution, auto-memory,
         background prefetches, keychain reads, and CLAUDE.md auto-discovery.
         Sets CLAUDE_CODE_SIMPLE=1. Anthropic auth is strictly ANTHROPIC_API_KEY
         or apiKeyHelper via --settings (OAuth and keychain are never read).
```

Probed on this machine, which has no `ANTHROPIC_API_KEY` in the environment:

```
$ claude -p --bare --model haiku --output-format json "Reply with exactly: PD"
rc=1
{"is_error":true, "terminal_reason":"api_error", "total_cost_usd":0,
 "modelUsage":{}, "result":"Not logged in · Pl…"}
```

So `--bare` does not merely shift billing from the subscription to the API — **without an API key
it does not run at all.** Any design that adopts `--bare` for unattended work is choosing metered
API billing, and should say so out loud. This was caught by two independent reviewers reading the
same help text I had quoted half of.

## 6. Housekeeping surfaced in passing (not acted on)

- `codex doctor`: 1,357 active rollout files, 812.93 MB on disk, 0 archived.
- `codex doctor`: CLI 0.144.6 installed, 0.152.0 available.
- `~/code/personal/tools/workbench` is **1 commit ahead of `origin/main`** — the
  2026-08-28 clodex process-revamp commit (`1f6b1b2`) has not been pushed.
- Two untracked `__pycache__/*.pyc` files sit under `skills/clodex/state/`.
