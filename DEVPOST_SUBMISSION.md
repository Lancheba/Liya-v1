# Devpost submission text — paste into the "Text description" field

## Inspiration

Most "AI assistant" demos are a chat window bolted onto a single LLM
call — the model answers, but a person still has to open the file,
click the button, or run the search themselves. We wanted an agent
that actually finishes the chore, not one that talks about it.

## What it does

Liya takes a single messy, multi-step goal in plain language — e.g.
*"search the web for the latest EV trends, save a summary to a file on
my Desktop, and remind me tomorrow at 9am to review it"* — and runs it
to completion without further input:

- **Plans** the goal into a sequence of concrete tool calls
  (`agent/planner.py`)
- **Executes** each step against real tools: web search, file I/O,
  app launching, browser control, messaging, reminders, and more
  (`actions/*.py`)
- **Recovers from failure** by classifying the error and deciding to
  retry, skip, replan, or abort — live, not scripted
  (`agent/error_handler.py`)
- **Enforces governance** on every tool call through a single
  allow/confirm/deny policy table, so autonomy is safe by structure,
  not by prompt engineering (`agent/governance.py`)
- **Remembers** long-term preferences across sessions and feeds them
  back into future planning (`memory/memory_manager.py`)
- Runs identically as a **local desktop app** (voice, via Gemini Live)
  or as a **Cloud Run backend** that any client can call over HTTP

## How we built it

Two execution paths share the same underlying tool implementations:

1. A direct Gemini-driven planner/executor loop that produces a JSON
   step plan and runs it with retry/replan logic.
2. A **Google ADK agent** (`agent/adk_agent.py`) wrapping 8 of the
   same action modules as ADK `FunctionTool`s, run through ADK's own
   agent loop and session management (`agent/adk_runner.py`).

Both paths go through one governance layer and one shared Gemini
client (`config/ai_client.py`), so a model version bump or a policy
change is a single edit, not a repo-wide hunt. The backend
(`backend/server.py`, FastAPI) is deployed to Cloud Run via
`cloudbuild.yaml`, backed by Firestore for task state and long-term
memory, with a local-file fallback so the same code runs with zero GCP
setup during development.

**Technologies used:** Gemini 3.5 Flash / Flash-Lite (via the
`google-genai` SDK), Google ADK, Google Cloud Run, Google Cloud
Firestore, Google Cloud Build, FastAPI, PyQt6 (desktop UI), Playwright
(browser control).

**Other data sources used:** live web search results (Gemini
search-grounding, with DuckDuckGo and Bing as fallback backends).

## Challenges we ran into

- **Governance parity across two execution paths.** The first version
  of the ADK integration called straight into action functions with no
  policy gate — a `confirm`-tier tool like `send_message` could run
  unchecked through the ADK agent. We caught this and added
  `_governed()` in `agent/adk_tools.py` so both paths enforce the exact
  same `check_tool_permission()` check.
- **Free-tier search quota exhaustion in production.** During our own
  Cloud Run deployment, `web_search`'s Gemini backend hit a real `429
  RESOURCE_EXHAUSTED` under normal use. We watched our own documented
  fallback chain (Gemini → DuckDuckGo → Bing) and retry logic
  (`error_handler.py`) handle it live rather than crash the task — see
  `evidence/cloud_run_deployment_proof.log` for the actual production
  log.
- **Keeping local dev and Cloud Run on one codebase.** Firestore is
  additive rather than required: `memory_manager.py` and
  `task_queue.py` both fall back to local JSON / in-memory state when
  Firestore isn't configured, so the same code works with no GCP
  project at all during iteration.

## What we learned

- Structural governance (one policy table, enforced identically on
  every code path) is a much smaller surface to audit than scattered
  permission checks — and it's the difference between "an agent that
  is probably safe" and one you can actually point to and say why.
- Running the same tool implementations under two different agent
  runtimes (hand-rolled vs. ADK) surfaced a real security gap we
  wouldn't have found by testing either path alone.
- Free-tier API quotas are a production concern, not a demo
  afterthought — our fallback chain existed on paper before it was
  ever exercised for real, which is exactly what happened during our
  own Cloud Run testing.

## What's next for Liya

Extending ADK coverage to the remaining 8 action modules (browser
control, computer control, desktop control, screen analysis) that
currently only run on the legacy path; a durable/distributed task
queue in place of the in-process one; step-level checkpoint/resume;
and a prompt-injection defense layer around untrusted tool output.
