# Liya — Write-up

**Track: The Taskmaster** — Liya is not a chatbot that talks about a
chore, it's an agent that runs one: it plans the steps, calls the real
tools (files, apps, browser, reminders, web search, messaging), recovers
from failures by replanning, and reports back with an auditable trace of
what it actually did — with no hand-holding after the goal is handed to it.

## Problem statement

Most "AI assistant" demos are a chat window bolted onto a single LLM
call: the model answers, but a person still has to open the file, click
the button, or run the search themselves. Liya is built the other way
around — the model plans, and the agent actually carries out the plan
against real tools (files, apps, browser, reminders, web search,
messaging) on the user's machine, with failure recovery and governance
built in, not bolted on. The goal isn't a better chatbot; it's a system
that can be handed a multi-step goal and finish it unattended, while
staying auditable and safe to run with elevated local permissions.

## Why this architecture

**Plan → execute → recover, as separate concerns.** `agent/planner.py`
only turns a goal into a step list; `agent/executor.py` only runs steps;
`agent/error_handler.py` only decides what to do when a step fails
(retry / skip / replan / abort). Keeping these separate means a failure
in one step doesn't require re-deriving the whole plan, and the
replanning logic can see exactly what succeeded before it before
deciding what to do next.

**Governance is a policy table, not scattered `if` statements.**
`agent/governance.py` maps every tool to `allow` / `confirm` / `deny`
once, in one place, overridable per-deployment via
`config/api_keys.json`. Risky tools (arbitrary computer control, code
execution) default to `confirm`; read-only or low-risk tools (web
search, weather) default to `allow`. This is what makes it reasonable to
let the planner call these tools autonomously at all — the danger isn't
gated per-call by prompt engineering, it's gated structurally.

**Two execution engines, on purpose.** Liya ships both:

1. The original planner/executor path — a direct Gemini call producing
   a JSON step plan against a hand-maintained tool schema
   (`agent/planner.py`'s `PLANNER_PROMPT`). This is fast, cheap
   (`gemini-3.5-flash-lite` for planning), and was the whole system
   before this integration.
2. A Google ADK agent (`agent/adk_agent.py`) wrapping the *same* action
   modules as ADK `FunctionTool`s (`agent/adk_tools.py`), run through
   ADK's own agent loop and session management
   (`agent/adk_runner.py`), sharing the same underlying Gemini client
   (`agent/adk_model.py` → `config/ai_client.py`).

   The ADK path exists because ADK gives session/state management,
   structured tool-calling, and an agent runtime maintained by Google
   instead of hand-rolled JSON-plan parsing — but rewriting the entire
   executor around ADK in one pass, across ~16 action modules that
   already work in production, was a bigger risk than the benefit
   justified this cycle. Running both side by side (`POST /task` vs
   `POST /task/adk`) lets the ADK path be exercised, tested, and trusted
   incrementally rather than as a single risky cutover.

**One model client, everywhere.** `config/ai_client.py` is the only
place that constructs a `google.genai.Client` or names a model string.
Every action module, the legacy planner, and the ADK model subclass
(`LiyaGemini`) go through it. A model version bump is a one-line change,
not a repo-wide find-and-replace — which matters more as the ADK and
legacy paths both need to stay in sync on which model they call.

**Firestore is additive, not required.** `memory/memory_manager.py` and
`agent/task_queue.py` both check whether Firestore is configured and
fall back to local-file storage / in-memory state if not. This keeps
local desktop use (no GCP project needed) and Cloud Run deployment (full
persistence) on the same codebase without a feature flag maze.

## What's deliberately not in this codebase

A few production-agent concerns are real and worth naming even though
they're out of scope here: a durable/distributed task queue instead of
the in-process one, step-level checkpoint/resume, idempotency keys on
every write action, a prompt-injection defense pipeline around
untrusted tool output, and rate/cost limiting on model calls. None of
these were built for this submission - the in-process queue backed by
Firestore status writes, the existing tool governance table
(`agent/governance.py`), and the `MAX_REPLAN_ATTEMPTS` cap in
`agent/executor.py` are the scope-appropriate version of "safe to run
autonomously" for a hackathon build, not the enterprise-hardened one.

## What's next

The designated end-to-end demo scenario and the trace/observability
walkthrough for judges are documented separately — see the project
tracker for that work.

---

## Designated demo scenario

**Goal:** *"Search the web for the latest trends in electric vehicles,
save a short summary to a file called ev_trends.txt on the Desktop, and
set a reminder for tomorrow at 9:00 AM to review it."*

This is the one scenario used to demo Liya end-to-end. It's chosen
because it chains three independent tools (`web_search` →
`file_controller` → `reminder`) in a single autonomous run, which
exercises:

- **Multi-step planning** — the planner has to sequence three
  dependent actions from one sentence, not just route to a single tool.
- **Real execution, not simulation** — a file actually appears on the
  Desktop and a reminder actually gets scheduled; nothing is mocked.
- **Visible autonomy** — every step is logged through
  `observability/logger.py` as it happens, not just summarized at the
  end.

### Running it

```bash
python demo/run_demo.py
```

This submits the goal directly to the real `agent/task_queue.py` (no
server needed) and streams the execution trace live as JSON events are
emitted, formatted as a readable timeline: which step is running, which
tool it called, and its result — as it happens, not after the fact.

Against a running backend instead (local or deployed), including the
Google ADK path:

```bash
# legacy planner/executor path, via POST /task
python demo/run_demo_http.py --url http://localhost:8080 --key dev

# Google ADK agent path, via POST /task/adk
python demo/run_demo_http.py --url http://localhost:8080 --key dev --adk
```

### Where the trace comes from

`observability/logger.py` logs every planning and execution event
(`plan.created`, `step.start`, `step.success`, `step.failure`,
`task.completed`, etc.) to three places at once:

1. stdout, as a JSON line per event (always on)
2. Firestore, under `tasks/{task_id}/trace/` (when configured)
3. An in-memory ring buffer, queryable via `get_trace(task_id)` (always
   on — this is what makes the trace visible on a local run with no
   GCP project at all)

`GET /task/{task_id}/trace` uses Firestore when it's configured and
falls back to the in-memory buffer otherwise, so the same endpoint
works whether or not the deployment has Firestore enabled.
