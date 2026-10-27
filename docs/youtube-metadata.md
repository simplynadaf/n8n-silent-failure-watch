# YouTube metadata: Silent Failure Watch for n8n

## Title (pick one, keyword front-loaded, <=70 chars)

1. The n8n Failure Your Error Workflow Will NEVER Catch (Self-Hosted)   [63]
2. n8n Silent Failures: Catch the Workflow That Stopped Running         [57]
3. Your n8n Error Workflow Is Blind. Here's the Fix. (EC2 + Postgres)   [62]

Recommended: #1 (highest curiosity + keyword "n8n error workflow").

---

## Description

Your n8n error workflow fires only when an execution FAILS. But unpublish a
workflow and nothing runs. Nothing runs, so nothing fails. So no alert ever
fires, and your automation is dead while the dashboard looks calm.

In this video I prove that gap on a real stack (n8n 2.43.6 + PostgreSQL 16 on
an AWS EC2 box), then build a liveness check that reads what ACTUALLY ran and
emails you once when a workflow goes quiet. No paid tools: it runs on the free
n8n public API.

What you'll see:
- Why an error workflow structurally cannot catch an unpublished workflow
- Live proof: unpublish a workflow, 150 seconds, ZERO executions
- A "did it run?" check: exists? published? last run ok? ran in time?
- Email only on change (no spam), plus the one blind spot you must cover

⏱️ Timestamps
00:00  The failure nobody alerts on
00:08  Start the stack (Docker compose up)
00:14  Create the n8n API key (read-only scope)
00:34  Credentials: n8n API + SMTP
00:53  Import the workflow to watch
01:02  Import / run the "Did it run" check
01:28  Settings: who gets the alert
01:36  First run: the watch list
01:49  Add Order sync to the watch list
01:55  Break it: unpublish the workflow
02:08  The alert fires (the silent failure, caught)
02:13  Fix it: publish again, back to normal
02:18  Back to a 15-minute schedule

🔗 Code and full write-up
GitHub: https://github.com/simplynadaf/n8n-silent-failure-watch
Article: https://dev.to/sarvar_04

🧰 Tested on
n8n 2.43.6 · PostgreSQL 16.15 · Amazon Linux 2023 EC2 · Docker Compose v2

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

#n8n #aws #devops #automation #selfhosted #monitoring

---

## Tags (YouTube keywords)
n8n, n8n monitoring, n8n error workflow, n8n self hosted, n8n aws, n8n ec2,
n8n postgres, silent failure, workflow monitoring, n8n tutorial, n8n api,
devops, automation monitoring, n8n production, uptime monitoring

---

## Pinned comment
The error workflow catches FAILED runs. This catches the runs that never
HAPPEN. Run both. Code + the full written tutorial:
https://github.com/simplynadaf/n8n-silent-failure-watch
What's the sneakiest silent failure you've hit? 👇

---

## On-screen opening line (first 8 seconds, the hook)
"This workflow is broken. Look: no red, no error email, dashboard's green.
It just stopped running three minutes ago, and nothing told me."

## Closing line (call to action)
"The error workflow was never going to catch this. The check that does is in
the repo below, runs on the free n8n API. Comment the weirdest way one of your
workflows went quiet, like if it helped, and subscribe. See you in the next one."
