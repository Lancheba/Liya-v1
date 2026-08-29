# Testing Liya live — for hackathon judges

Liya is deployed on Google Cloud Run. You don't need to clone or run
anything locally to see it work — the commands below hit the live
service directly.

**Live service URL:** `https://liya-backend-250703517715.us-central1.run.app`
**Judge test key:** `judge-liya-2026-test`

> Before pasting your key here: create a **second** value in Secret
> Manager (or just a second accepted key if `backend/server.py` checks
> against a list) specifically for judges, separate from your own
> `LIYA_API_KEY`. That way you can revoke/rotate the judge key after
> the Judging Period ends without touching your own deployment.

---

## 1. Health check (no auth needed)

```bash
curl https://liya-backend-250703517715.us-central1.run.app/health
```

Expected: `{"status": "ok", ...}` — confirms the service is live on
Cloud Run right now, not just in a screenshot.

## 2. Submit the designated demo goal

```bash
curl -X POST https://liya-backend-250703517715.us-central1.run.app/task \
  -H "Content-Type: application/json" \
  -H "X-Liya-Key: judge-liya-2026-test" \
  -d '{
    "goal": "Search the web for what judges say separates a winning hackathon submission from an average one, save the findings as a submission-readiness checklist to a file called hackathon_checklist.txt on the Desktop, and set a reminder for tonight at 8:00 PM to do a final pass against it."
  }'
```

This returns immediately with a `task_id` — the task itself keeps
running in the background on Cloud Run after the HTTP response comes
back, which is the "async background execution" claim, live.

## 3. Poll the task and watch the trace

```bash
curl https://liya-backend-250703517715.us-central1.run.app/task/TASK_ID \
  -H "X-Liya-Key: judge-liya-2026-test"

curl https://liya-backend-250703517715.us-central1.run.app/task/TASK_ID/trace \
  -H "X-Liya-Key: judge-liya-2026-test"
```

The trace endpoint returns every `plan.created` / `step.start` /
`step.success` / `step.failure` / `task.completed` event for that
task — the same live execution log shown in the demo video, queryable
directly.

## 4. Try the Google ADK path

```bash
curl -X POST https://liya-backend-250703517715.us-central1.run.app/task/adk \
  -H "Content-Type: application/json" \
  -H "X-Liya-Key: judge-liya-2026-test" \
  -d '{"goal": "What is the weather in London today?"}'
```

Runs the same goal through `agent/adk_runner.py`'s real ADK
`InMemoryRunner` session, not the legacy planner.

## 5. Interactive API docs

Open `https://liya-backend-250703517715.us-central1.run.app/docs` in a
browser (FastAPI's built-in Swagger UI) to see and try every endpoint
without curl.

---

## What NOT to expect from the live endpoint

A few actions are `confirm`-tier under `agent/governance.py`
(`send_message`, `computer_control`, `code_helper`, `dev_agent`, etc.)
and are blocked by design when running headless in the cloud unless the
request sets `"auto_approve": true` — this is the governance system
working as intended, not a bug. Add `"auto_approve": true` to the
`/task` body above to see one of those run instead of getting blocked,
or see `demo/demo_governance.py` for that exact contrast shown live.

Desktop-only tools (`browser_control`, `desktop_control`,
`screen_processor`, voice via Gemini Live) only run in the local
desktop app (`python main.py`), not on this Cloud Run deployment — see
the demo video for those.

---

## If the live URL is down when you read this

Cloud Run is scaled to zero when idle (`--min-instances=0`) to control
cost, so the first request after a period of inactivity may take a few
seconds (cold start) rather than fail. If it's genuinely unreachable,
fall back to:
- `evidence/cloud_run_deployment_proof.log` — a real production log
  from this same deployment
- `evidence/cloud_run_console.png` / `evidence/cloud_build_success.png`
  — screenshots of the deployed, healthy service
- Running it yourself locally: `LIYA_API_KEY=dev python backend/server.py`
  (see `backend/README_DEPLOY.md`)