# We found a real security hole in our own agent by running it two ways

*This post was written for the All Things Agentic Hackathon.*

Most agent demos pick one framework and build around it. We built
Liya's tool layer once and ran it through two different agent
runtimes on purpose — and that decision caught a bug neither path
would have surfaced alone.

## The setup

Liya plans a multi-step goal, then executes it against real tools:
web search, file I/O, messaging, reminders, browser control, and more.
We built this two ways on top of the same action modules:

1. A hand-rolled planner/executor loop: Gemini produces a JSON step
   plan, our executor runs it with retry/replan logic.
2. A real Google ADK agent, wrapping the same actions as ADK
   `FunctionTool`s, run through ADK's own agent loop.

Both call into the exact same `actions/*.py` implementations — no
logic duplicated, no logic forked.

## What we assumed

We had a single governance policy table (`agent/governance.py`)
mapping every tool to `allow` / `confirm` / `deny`. Risky tools like
`send_message` and computer control default to `confirm` — meaning
they need explicit consent before they're allowed to run, especially
in a headless/cloud context. We'd wired this into the legacy executor
from day one and assumed "the tools are gated" was just true of the
system as a whole.

## What we found

It wasn't. The first version of the ADK tool wrappers
(`agent/adk_tools.py`) called straight into the action functions with
no permission check at all. A `confirm`-tier tool like `send_message`
would run through the ADK agent with nothing stopping it — the
governance table existed, but only one of our two execution paths was
actually reading it.

This is the kind of gap that's invisible if you only ever test one
path. The legacy executor looked completely correct in isolation. It
was only running the *same goal* through both engines side by side
that made the asymmetry obvious.

## The fix

We added a single `_governed()` wrapper that every ADK
`FunctionTool` now routes through, calling the identical
`check_tool_permission()` the legacy executor uses. Same policy table,
same enforcement, both paths. `demo/demo_governance.py` now runs the
same goal through the ADK agent twice — once with no consent
(`send_message` blocked) and once with `auto_approve=True` (it runs)
— so the fix is something you can watch happen, not just read about.

## The takeaway

If you're building an agent that's going to run tools autonomously,
the interesting security bugs aren't usually in the tools themselves
— they're in the seams between however many ways your system can call
them. We only had two execution paths and still found a real gap.
Worth remembering before adding a third.

---
*Built for the All Things Agentic Hackathon — read more or try it at
https://github.com/Lancheba/Liya-v1.*
