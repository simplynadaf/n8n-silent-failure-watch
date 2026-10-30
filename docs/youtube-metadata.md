# YouTube metadata: the n8n silent-failure video

## Title (data-backed pick)

**USE THIS:** `The n8n Failure Your Error Workflow Will NEVER Catch`  [52 chars]

Why this one (YouTube, not Dev.to):
- Keyword "n8n" is the FIRST word -> search + suggested pick it up.
- Pure curiosity gap: "what failure? why never?" The thumbnail (green dashboard
  + a dead workflow) closes the visual loop, so the title can stay a question.
- ONE emphasized power word (NEVER, caps) is fine on YouTube (not on Dev.to/HN).
- 52 chars, well under the 70-char mobile truncation limit.

Alternates (A/B test candidates):
2. `I Broke My Own n8n to Prove This Monitoring Blind Spot`              [54]
3. `Your n8n Dashboard Is Green. The Workflow Died Days Ago.`           [56]
4. `n8n Silent Failures: Catch the Workflow That Stopped Running`       [60]

Note: the Dev.to article uses a DIFFERENT title on purpose (starts with "I" for
3.2x engagement in the feed). YouTube favors keyword-front curiosity, so the two
are intentionally not the same.

---

## Description

Your n8n error workflow fires only when an execution FAILS. But unpublish a
workflow and nothing runs. Nothing runs, so nothing fails. So no alert ever
fires, and your automation is dead while the dashboard looks calm.

I hit this on my own self-hosted n8n, lost half a day to it, and then tested the
whole thing on a real stack (n8n 2.43.6 + PostgreSQL 16 on an AWS EC2 box) to be
sure. In this video I prove the gap, then build a small liveness check that reads
what ACTUALLY ran and emails you once when a workflow goes quiet. It runs on the
free n8n public API, no extra tools.

What you'll see:
- Why an error workflow structurally cannot catch an unpublished workflow
- Live proof: unpublish a workflow, wait 150 seconds, ZERO executions
- A "did it run?" check: exists? published? last run ok? ran in time?
- Email only on change (no spam), plus the one blind spot you must cover
  (the check runs inside n8n, so if n8n is down, the check is down too)

⏱️ Timestamps
00:00  The failure nobody alerts on (green dashboard, dead workflow)
00:20  Why your error workflow is structurally blind
00:45  The stack: n8n 2.43.6 + Postgres 16 on EC2 (not the SQLite demo)
01:05  Create a READ-ONLY n8n API key (can't change anything if it leaks)
01:30  The check: exists? published? last run failed? ran in time?
01:55  Publish Order sync, confirm it's healthy
02:15  Break it: unpublish the workflow
02:35  Proof: 150 seconds, zero new executions
02:55  The alert fires, the silent failure caught
03:10  Fix it: publish again, back to normal
03:25  The one blind spot: a heartbeat outside n8n

(Adjust timestamps to the final edit before upload.)

🔗 Code and full write-up
GitHub: https://github.com/simplynadaf/n8n-silent-failure-watch
Article: https://dev.to/sarvar_04   (swap for the exact article URL after publishing)

🧰 Tested on
n8n 2.43.6 · PostgreSQL 16.15 · Amazon Linux 2023 EC2 · Docker Compose v2

🙏 Credit: I first came across this "did it run?" approach through Krafera Silent
Failure Watch, a packaged set of importable n8n monitoring workflows by
Ahmet at Krafera. The entry tier is the same check this video builds, set up to
email once and stay quiet until the state changes, send a "back to normal", and
ping an outside heartbeat (the gap my script leaves open); higher tiers add a
daily order count-check, an error alert with secrets masked, plus webhook
de-dup, a retry queue, nightly backups and a weekly report. Krafera tested it on
the same n8n version I used, 2.43.6 in Docker (on SQLite, not my Postgres/EC2 run).
Disclosure: Ahmet gave me a copy to try. I'm not an affiliate and earn nothing
either way; I use it and genuinely rate it. Have a look: https://krafera.gumroad.com/l/lltue

👇 Tell me in the comments: what's the sneakiest way an n8n workflow has gone
quiet on you in production? I collect these.

👍 If this saved you a debugging session, like + subscribe for more AWS, DevOps,
and AI infrastructure.

--
Follow:
🌐 https://sarvarnadaf.com
💼 https://www.linkedin.com/in/sarvar04/
✍️ https://dev.to/sarvar_04
🐦 https://x.com/SarvarN_04

#n8n #aws #devops #automation #selfhosted

---

## Tags (YouTube keywords, keyword-front order)
n8n, n8n error workflow, n8n monitoring, n8n self hosted, n8n aws, n8n ec2,
n8n postgres, n8n api, silent failure, workflow monitoring, n8n tutorial,
devops monitoring, automation monitoring, n8n production, uptime monitoring

---

## Pinned comment
The error workflow catches runs that FAIL. This catches the runs that never
HAPPEN. Run both. Code + the full written tutorial:
https://github.com/simplynadaf/n8n-silent-failure-watch
What's the sneakiest silent failure you've hit in production? 👇

---

## Thumbnail brief (1280x720)
- Left: a green "all healthy" dashboard / green check.
- Right: the same workflow greyed out / a flatline, "0 runs".
- Text, max 3 words, high contrast: "DEAD. NO ALERT." or "GREEN. BUT DEAD."
- Accent: amber/green on dark (green is rare on YouTube = stands out).
- No face. Show the RESULT (the silent gap), not code.

---

## On-screen opening line (first 8 seconds, the hook)
"This workflow is broken. Look: no red, no error email, dashboard's green.
It stopped running three minutes ago, and nothing told me."

## Closing line (call to action)
"The error workflow was never going to catch this. The check that does is in
the repo below, runs on the free n8n API. Comment the weirdest way one of your
workflows went quiet, like if it helped, and subscribe. See you in the next one."
