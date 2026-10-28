---
title: "I lost half a day to an n8n workflow that was \"working.\" It never ran."
published: false
description: "An n8n error workflow fires only when an execution fails. Unpublish a workflow and nothing runs, so nothing fails, so no alert. Here is the liveness check I run on EC2."
tags: n8n, aws, devops, discuss
cover_image: https://raw.githubusercontent.com/simplynadaf/n8n-silent-failure-watch/main/assets/cover-devto.png
---

Last month I lost half a day to a workflow that was working perfectly. It just was not running.

An order-sync job on my self-hosted n8n had been switched off during an unrelated edit. No red execution. No error email. The dashboard was calm. The only reason I found it: someone asked why a downstream report looked stale.

That is the gap. Every monitoring guide for n8n starts with an error workflow. An error workflow is good at one job, and only that job: it fires when an execution fails. It does nothing when an execution never starts.

This post is about that second case, the one most setups never alert on. I will show you why your error workflow is blind to it, then build a small liveness check that catches it, and I tested the whole thing on a production-shaped stack: n8n 2.43.6 on PostgreSQL 16 on an Amazon Linux 2023 EC2 box. Not the default SQLite demo. The same shape you actually run.

This is a follow-up to my earlier post on [securing self-hosted n8n on AWS](https://dev.to/aws-builders/secure-self-hosted-n8n-on-aws-the-2026-hardening-checklist-4jkk). If you followed that one, this plugs the monitoring hole it leaves open.

---

## Table of Contents

- [Why the error workflow is blind](#why-the-error-workflow-is-blind)
- [I proved it: zero executions while unpublished](#i-proved-it-zero-executions-while-unpublished)
- [The fix: check what ran, not what failed](#the-fix-check-what-ran-not-what-failed)
- [Build it step by step on EC2 + Postgres](#build-it-step-by-step-on-ec2--postgres)
- [The one blind spot even this check has](#the-one-blind-spot-even-this-check-has)
- [Day 2: tuning, cost, and what I would not do](#day-2-tuning-cost-and-what-i-would-not-do)
- [Credit where it is due: the packaged version](#credit-where-it-is-due-the-packaged-version)
- [What I tested and what I did not](#what-i-tested-and-what-i-did-not)
- [Code](#code)

---

## Why the error workflow is blind

Here is n8n's own line on when an error workflow runs. It runs if an execution fails. Read that again. It needs an execution to exist before it can judge it failed.

Now think about how a scheduled workflow actually dies in production. It rarely throws. It goes quiet:

- Someone unpublishes it during an edit and forgets to publish again.
- The schedule trigger gets changed and never fires.
- You restored a backup and the workflow came back inactive.
- A deploy script re-imported it and left it off.

In every one of those, the trigger never fires. No execution record is created. There is no failed run for the error workflow to catch, because there is no run at all.

So the alerting you trust most is structurally incapable of seeing the most common way a cron job dies. It is not misconfigured. It is pointed at the wrong thing.

When you unpublish a workflow, n8n even tells you what happens next, in the confirmation dialog: it will prevent all production executions until you publish again. Prevent all executions. That is the whole problem in n8n's own words.

---

## I proved it: zero executions while unpublished

I did not want to take this on faith, so I ran it.

I stood up n8n 2.43.6 against PostgreSQL 16 on an EC2 instance, imported a tiny workflow called `Order sync` on a one-minute schedule trigger, and published it. Two scheduled runs showed up right away through the public API, both with `mode: trigger` and `status: success`.

Then I unpublished it and watched the execution list through the API.

```bash
# before: Order sync is published and has 2 scheduled runs on record
executions BEFORE unpublish: 2

# deactivate (unpublish) via the public API at 11:01:22 UTC, then wait 150 seconds
Order sync active after unpublish: False

# 150s later = at least two missed one-minute runs
executions AFTER 150s unpublished: 2
=> new executions while unpublished: 0
```

Zero. Two and a half minutes, at least two scheduled runs missed, and the execution count did not move by one.

No execution means no status to read. No status means nothing an error workflow could fire on. I republished, and within 70 seconds a new run appeared and the count went from 2 to 3. The trigger resumed exactly where it left off, and for those 150 seconds, every internal error alert I could have wired up would have stayed silent.

That is the silent failure. Not a red run you missed. A run that never happened.

---

## The fix: check what ran, not what failed

If waiting for a failure cannot work, the check has to invert the question. Instead of "did anything fail," it asks "did the thing I expect actually run, and is it still able to run."

A separate scheduled workflow, every 15 minutes, reads the n8n public API and answers four questions for each workflow on a watch list:

1. Does a workflow with that exact name still exist? (catches deleted or renamed)
2. Is it published? (catches the unpublish case above)
3. Did its last run fail? (catches the ordinary error too)
4. Did it have a successful run inside a time limit you set? (catches a trigger that silently stopped firing)

Three API calls do all of it. These are the real response shapes from my run, not docs:

```text
GET /workflows
  -> {"id":"EgNOLmmZq9YsVhIM","name":"Order sync","active":true}

GET /executions?workflowId=<id>&limit=1
  -> {"id":"3","mode":"trigger","status":"success","finished":true,
      "startedAt":"2026-10-27T11:04:25.014Z","stoppedAt":"2026-10-27T11:04:25.032Z"}

GET /executions?workflowId=<id>&status=success&limit=1
  -> the last run that actually succeeded
```

The `active` field is the published flag. When I unpublished `Order sync`, `active` flipped to `false`, and that one boolean is the whole detection. No execution needed.

![Architecture of the did-it-run check: n8n on EC2 and Postgres, a watch workflow reading the public API, and two outputs, an email on change and an external heartbeat](https://raw.githubusercontent.com/simplynadaf/n8n-silent-failure-watch/main/assets/architecture.png)

Two design rules make this usable instead of annoying:

**Only email on change.** A problem that stays open gives you one email, not one every 15 minutes. The check keeps the last state and compares. New problem opened, send once. Problem cleared, send a "back to normal." Nothing changed, stay silent. A monitor that cries every cycle gets filtered to a folder you never open, and then it is not a monitor.

**Keep one check outside n8n.** More on that below, because it is the part people skip and then regret.

I wrote the check as a plain Python script so this whole tutorial is free and reproducible with nothing but the n8n API. You can run it from cron, a Lambda, or wrap the same logic in an n8n workflow. Here is the core of it:

```python
WATCH = {"Order sync": 10}   # name -> max_quiet_minutes (0 = no time limit)

workflows = {w["name"]: w for w in get("/workflows")["data"]}
for name, max_quiet in WATCH.items():
    wf = workflows.get(name)
    if wf is None:
        problem(f"{name}: no workflow with this exact name (deleted or renamed)")
    elif not wf["active"]:
        problem(f"{name}: switched off (unpublished), so its trigger starts nothing")
    else:
        last = get(f"/executions?workflowId={wf['id']}&limit=1")["data"]
        if last and last[0]["status"] == "error":
            problem(f"{name}: last run failed")
        # ... then the max_quiet_minutes freshness check
```

Running it against my real stack, across the three states:

```text
# healthy (Order sync published)
All watched workflows are published and ran successfully in time. Nothing to report.

# after I unpublish Order sync
Open (1):
- Order sync: switched off (unpublished), so its trigger starts nothing

# after I publish it again
All watched workflows are published and ran successfully in time. Nothing to report.
```

That middle state is the one your error workflow never prints.

---

## Build it step by step on EC2 + Postgres

Here is the setup I actually ran. It uses a small test stack so you can prove the behaviour safely before you point it at real workflows. The one real external dependency is Mailpit, a throwaway mail server so you can see the alert without a real SMTP account.

A note on versions, because it bit me and will bite you. On n8n 2.43.6, Postgres 16 logs this on boot:

```text
Postgres 16 is outside the supported range and receives compatibility support
only. Upgrade to Postgres 17 or newer.
```

Everything in this post worked fine on 16.15. But if you are standing up a fresh box, start on Postgres 17 so you are not on compatibility-only support.

### Step 1: Start the stack

Put the `docker-compose.yml` from the repo in an empty folder. It runs n8n 2.43.6 on Postgres 16 and Mailpit, all bound to `127.0.0.1` only.

```bash
mkdir n8n-watch && cd n8n-watch
# copy docker-compose.yml and order-sync.json here
printf "N8N_ENCRYPTION_KEY=%s\nPOSTGRES_PASSWORD=%s\nGENERIC_TIMEZONE=UTC\n" \
  "$(openssl rand -hex 24)" "$(openssl rand -hex 16)" > .env
docker compose up -d
```

Expect three containers. Postgres becomes healthy, then n8n runs its migrations against it. Wait for the health check:

```bash
curl -s http://localhost:5678/healthz    # {"status":"ok"}
```

On a real EC2 box, do not open 5678 or 8025 in the security group. Keep them on localhost and reach them over an SSH tunnel:

```bash
ssh -L 5678:localhost:5678 -L 8025:localhost:8025 ec2-user@<PUBLIC_IP>
```

### Step 2: Owner account and API key

Open `http://localhost:5678`, create the owner account. Then **Settings** -> **n8n API** -> **Create API key**. Give it an expiration you will actually renew (a long-lived key is one more secret to rotate; set a calendar reminder rather than "Never"). Copy it with the copy button, because n8n shows the full key only once.

One thing worth knowing that the usual guides do not test: a narrow-scoped key is enough. I ran the check with a key scoped to `workflow:read`, `workflow:list`, `execution:read`, `execution:list` and nothing else, and it worked. A key with no write scope got a clean `{"message":"Forbidden"}` on any write. So the monitor key cannot change anything even if it leaks. Give it read scopes only.

### Step 3: A workflow to watch

Import `order-sync.json` (in the repo). It is a schedule trigger plus a code node that returns two fake orders. It does nothing outside n8n, so it is safe to publish and break. Publish it.

### Step 4: Point the check at it

Add `Order sync` to the watch list with a `max_quiet_minutes` of 10, which means "shout if there has been no successful run in 10 minutes." Run the check (or set the watch workflow to every 15 minutes). First healthy run says nothing is wrong.

### Step 5: Break it on purpose

Unpublish `Order sync`. The next check prints:

```text
Open (1):
- Order sync: switched off (unpublished), so its trigger starts nothing
```

That is the alert your error workflow cannot produce. Publish it again and the next check clears to "back to normal." Then set your real interval to 15 minutes and add every workflow you care about to the `WATCH` list in the script.

### Step 6: Clean up the test

```bash
docker compose down -v
```

The `-v` removes the Postgres, n8n, and Mailpit volumes. On your real instance you obviously keep them, and you keep the check running on 15 minutes.

---

## The one blind spot even this check has

Here is the uncomfortable part, and it is the reason I will not tell you this check is enough on its own.

The check runs inside n8n. If n8n itself is down, out of memory, mid-restart, or the EC2 instance is stopped, the check does not run either. A monitor that lives inside the thing it watches dies with it, with no noise, and the dashboard stays calm because there is no dashboard.

This is the single blind spot no amount of internal instrumentation closes. You need one thing outside the box.

The pattern is a heartbeat. After every check, the workflow pings an external uptime or cron-monitoring service. You tell that service to expect a ping every 15 minutes. When the pings stop, the outside service alerts you, because the absence of a ping is the signal. The workflow going quiet is exactly what you want to hear about.

I have not wired the heartbeat into my own run yet, so I am not going to pretend I measured it. I am flagging it as the required second layer, because leaving it out is how people end up with a monitor that was itself dead for a week. Treat the in-n8n check and the external heartbeat as one system, not two options.

---

## Day 2: tuning, cost, and what I would not do

**Set `max_quiet_minutes` to the rhythm, not a guess.** My rule: about 3x the schedule interval. Every 15 minutes gets 45. Hourly gets 130. Daily gets 1500. For event-driven workflows (webhooks with no schedule), set it to 0, so you only check "exists and published," because there is no expected rhythm to be late against.

**Keep executions long enough to read.** The check reads past runs from the execution list. If your pruning deletes successful runs faster than your `max_quiet_minutes` window, the freshness check goes blind. Set `EXECUTIONS_DATA_SAVE_ON_SUCCESS: all` and make sure `EXECUTIONS_DATA_MAX_AGE` and `EXECUTIONS_DATA_PRUNE_MAX_COUNT` keep runs around longer than your largest quiet window.

**Cost: effectively zero.** This is a few API reads every 15 minutes on a box you already pay for. The external heartbeat service has a free tier that covers a handful of monitors. There is no new infrastructure here, which is the point. Monitoring that needs its own cluster never gets installed.

**What I would not do:** reach for Prometheus and Grafana just for this. If you already run them, `N8N_METRICS=true` exposes a metrics endpoint and that is a fine path. But standing up a metrics stack to answer "did my workflow run" is a lot of moving parts to watch a boolean. Match the tool to the question.

I built this for my own n8n setup after getting bitten by exactly this blind spot, ran it on my real stack, and liked it enough to write it up. Everything here runs on the free n8n API alone, so you can take the check as-is or adapt it to your own workflows.

---

## Credit where it is due: the packaged version

I did not arrive at this idea cold. I first came across the "did it run?" approach through **Silent Failure Watch**, a packaged n8n version of this logic that Ahmet put together and shared with me. His package is what made me sit up and realise my own setup had this exact hole, so the honest thing is to say so.

What I liked about it: instead of a script you maintain, it is a ready-made n8n workflow you import and point at your watch list, the same four checks (exists, published, last run, ran in time) wired up inside n8n with the email and heartbeat already built. If you would rather import a file than keep a Python script running, it genuinely saves you the afternoon I spent building and testing mine. It is the easier on-ramp, and for a lot of people that is the right call.

I wrote my own open check for this post so the tutorial stays free and reproducible on the public API, and because I wanted to understand the mechanism end to end rather than just install it. Both get you to the same place. If the packaged route fits how you work, Ahmet's Silent Failure Watch is worth a look. No affiliate, no code on my end, just an honest pointer to the thing that put me onto the problem.

---

## What I tested and what I did not

I am specific about this because "tested" should mean tested.

**Verified on my stack (2026-10-27, UTC):** n8n 2.43.6 on PostgreSQL 16.15, amd64, Amazon Linux 2023 EC2, Docker 25.0.14, Compose v2.39.1. The unpublish produces zero executions (measured over 150s). The three API shapes above. The three-state check output. A test alert delivered through SMTP to Mailpit. A read-only scoped API key working, and a write attempt correctly forbidden.

**Not tested, so not claimed:** the external heartbeat end to end, a real SMTP provider (I only used Mailpit), the n8n 1.x to 2.x upgrade on Postgres, queue mode, and n8n Cloud. If you run any of those, treat the relevant step as "should work, verify on your side."

That is the honest line between what I ran and what I am reasoning about.

---

## Code

Everything here, the compose file, the sample workflow, the standalone check, the EC2 and Postgres notes, and the architecture diagram, is in the repo:

{% embed https://github.com/simplynadaf/n8n-silent-failure-watch %}

Clone and run:

```bash
git clone https://github.com/simplynadaf/n8n-silent-failure-watch
cd n8n-silent-failure-watch
```

{% embed https://www.youtube.com/@sarvar-nadaf %}

The 3-minute walkthrough (break it, watch the alert fire, fix it) is on the channel. If this saved you a stale-report debugging session, the comment box is open: what is the sneakiest way an n8n workflow has gone quiet on you in production? I collect these.

---

*Follow me for more on AWS architecture, DevOps, and AI Infrastructure:*
*[Portfolio](https://sarvarnadaf.com) | [LinkedIn](https://www.linkedin.com/in/sarvar04/) | [Dev.to](https://dev.to/sarvar_04) | [YouTube](https://www.youtube.com/@sarvar-nadaf) | [Email](mailto:simplynadaf@gmail.com) | [AWS Builder Center](https://builder.aws.com/community/@sarvar) | [X](https://x.com/SarvarN_04)*
