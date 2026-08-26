# A second, personal demo scenario (BYOF)

The designated demo (`demo/run_demo.py`) proves the mechanism — three
independent tools chained from one sentence, live trace, real recovery.
It's a good *capability* demo but a generic one. The rubric specifically
credits Taskmaster submissions for solving "a unique, personal problem"
(BYOF — Bring Your Own Friction). Use this as a second scenario in the
video, right after the designated one, to hit that criterion directly.

No new code is needed — this runs on the exact same tools already
wired up (`web_search`, `file_controller`, `reminder`, `send_message`).

## Suggested goal

> "Check the weather for tomorrow in [your city], and if it looks like
> rain, save a reminder note to bring an umbrella and message my
> [partner/roommate/team] to let them know we should leave earlier."

Or, closer to actual hackathon-prep friction:

> "Search for the submission deadline and requirements for the All
> Things Agentic Hackathon, save a checklist file to my Desktop of
> everything still missing from our submission, and set a reminder for
> tonight at 8pm to review it."

This second one is worth seriously considering for the video: it's
literally true (this conversation), it's a genuinely messy multi-step
chore you actually have right now, it chains `web_search` →
`file_controller` → `reminder` exactly like the designated demo but
the *content* is unmistakably personal rather than a stock example
topic, and it doubles as an authentic screen-recording moment — the
judges watch the agent do actual submission prep, which quietly also
reinforces "this team eats their own dog food."

## Why this matters for scoring

The Innovation & Operational Utility criterion (40% weight) explicitly
asks: *"Did the team successfully utilize the Bring Your Own Friction
(BYOF) mandate to solve a unique, personal problem?"* Running the
designated demo alone answers "does the mechanism work" but not this
question. A 30-45 second second scenario in the video, using a problem
that's visibly yours, closes that gap without touching the codebase.
