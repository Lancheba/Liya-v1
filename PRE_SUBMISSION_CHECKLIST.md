# Pre-submission checklist (everything except the video)

## Done / in this pass
- [x] Live Cloud Run deployment proof captured — `evidence/cloud_run_deployment_proof.log`
      (real `.run.app` URL, real Cloud Build SUCCESS, a real task
      execution including a live failure-recovery sequence)
- [x] Devpost text description drafted — `DEVPOST_SUBMISSION.md`
      (paste directly into the submission form's text field)
- [x] BYOF-flavored second demo scenario written — `evidence/byof_demo_scenario.md`
      (no code changes needed, just say it into the mic during the video)
- [x] Bonus-point blog post drafted — `evidence/blog_post_draft.md`
- [x] Bonus-point social post drafted — `evidence/social_post_draft.md`
      (remember: must be public, not unlisted; must include
      #AllThingsAgenticHackathon)

## Still on you before Sep 1
- [ ] **Take a Cloud Run Console screenshot** (Console → Cloud Run →
      liya-backend → the green "healthy" revision + the request graph
      showing real traffic) — even stronger than the log text alone,
      and the rules explicitly list "Google Cloud Console" as
      acceptable proof
- [ ] Grab a screenshot of the Cloud Build success page too (you have
      the build ID: `d99dcd44-85e5-474b-a7bb-c291e42332fe`)
- [ ] Confirm the code repo (GitHub/GitLab/Bitbucket) is either public,
      or private with access already granted to
      `testing@devpost.com` and `cloudhackathons@google.com`
- [ ] Fill in the real repo URL and video URL into
      `evidence/social_post_draft.md` before posting
- [ ] Publish the blog post somewhere public (dev.to / Medium) —
      must state it was written for this hackathon (already included
      in the draft's byline)
- [ ] Post the social post with the exact hashtag `#AllThingsAgenticHackathon`
- [ ] Fix (or at least note in the writeup) that `_looks_like_failure()`
      in `agent/executor.py` doesn't currently catch "no results
      found" as a failure — the production log shows this step being
      logged as `step.success` when the search actually returned
      nothing. Not fatal, but worth a one-line mention in
      "known limitations" if you don't have time to patch it.
- [ ] Record and upload the demo video (≤4 min, YouTube/Vimeo, public,
      shows Cloud Run/Vertex proof) — not covered by this pass
- [ ] Paste `DEVPOST_SUBMISSION.md` into the actual Devpost submission
      form and select the **Taskmaster** category
- [ ] Double check README's architecture diagram renders on GitHub
      (Mermaid version — `diagrams/architecture.mmd`) in case judges
      view the repo directly instead of opening the PNG
