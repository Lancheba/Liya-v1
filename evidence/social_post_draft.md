# Social post draft (X / LinkedIn) — remember the hashtag

## Short version (X)

Built Liya for #AllThingsAgenticHackathon — an agent that actually
*does* the chore instead of just describing it. Give it "search EV
trends, save a summary, remind me tomorrow" and it plans it, runs it
against real tools, recovers from real failures live, and reports
back. Built on Gemini 3.5 + Google ADK, deployed on Cloud Run.

[repo link] [video link]

## Longer version (LinkedIn)

I just submitted Liya to Google's All Things Agentic Hackathon
(#AllThingsAgenticHackathon) — an autonomous agent built on Gemini 3.5
and Google's ADK that plans a multi-step goal, executes it against
real tools (web search, files, messaging, reminders, browser control),
recovers from failures by replanning, and reports back with a full
execution trace — no hand-holding after the goal is handed to it.

The most interesting part of building it: I ran the same tool layer
through two different agent runtimes (a hand-rolled planner/executor
and a real Google ADK agent) and found a governance gap that only
showed up when I compared the two side by side — a `confirm`-tier tool
was running unchecked through one of the two paths. Fixing it, and
being able to demo the fix live, turned out to be one of the more
useful things running two engines in parallel bought us.

Deployed on Cloud Run, backed by Firestore, with a full failure-
recovery and tool-governance layer built in from the start rather than
bolted on after.

Repo: [link] | Demo: [link]

#AllThingsAgenticHackathon #GoogleCloud #Gemini #AIAgents
