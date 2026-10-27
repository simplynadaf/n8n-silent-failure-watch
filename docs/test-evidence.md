# Test evidence log — Sarvar's real run

Stack: n8n 2.43.6 on PostgreSQL 16.15 (amd64), Mailpit v1.32.0, Docker 25.0.14 +
Compose v2.39.1, Amazon Linux 2023 EC2. Date: 2026-10-27 (UTC).

This is the production-shaped stack (Postgres, not SQLite) that the vendor draft
explicitly did NOT test. Every number below is from this run.

## Facts captured
- n8n --version => 2.43.6
- postgres => PostgreSQL 16.15 on x86_64-pc-linux-musl
- Real n8n log line: "Postgres 16 is outside the supported range and receives
  compatibility support only. Upgrade to Postgres 17 or newer."
- Public API key with narrow scopes (workflow:read, workflow:list, execution:read,
  execution:list) works for the read-only checker. (Vendor listed narrow scopes as untested.)
- A write-scoped key returned {"message":"Forbidden"} on POST /workflows — scopes enforced.

## The core experiment (the whole article rests on this)
- Order sync (schedule trigger, every 1 min) active on Postgres.
- 2 scheduled executions observed, both mode=trigger, status=success (11:59:25, 11:00:25).
- Unpublished (deactivate via API) at 11:01:22 UTC.
- Waited 150s (>=2 missed scheduled runs).
- Executions before: 2. Executions after: 2. NEW EXECUTIONS WHILE UNPUBLISHED: 0.
  => No execution means no failure means an error workflow has nothing to fire on.
- Republished at 11:04:01 UTC. Within 70s a new execution appeared (count 2 -> 3). Runs resumed.

## Real API payload shapes used by the check
- GET /workflows -> {"id","name","active"}  (active=true/false is the published flag)
- GET /executions?workflowId=<id>&limit=1 -> {"id","mode":"trigger","status":"success",
  "finished":true,"startedAt","stoppedAt","workflowId"}
- GET /executions?workflowId=<id>&status=success&limit=1 -> filters to successful runs

## Open checker output (did_it_run_check.py), 3 states
State 1 healthy:    "All watched workflows are published and ran successfully in time. Nothing to report."
State 2 unpublished:"Open (1): - Order sync: switched off (unpublished), so its trigger starts nothing"
State 3 republished:"All watched workflows are published and ran successfully in time. Nothing to report."

## Email
- Sent a representative alert through Mailpit SMTP (1025); Mailpit inbox showed 1 message,
  subject "Did it run: 1 open". Email path works.

## Still NOT tested (be honest in the article)
- The heartbeat / external uptime monitor (the "n8n itself is down" blind spot).
- A real external SMTP provider (only Mailpit used).
- n8n 1.x -> 2.x upgrade on Postgres.
- Queue mode, n8n Cloud.
- Behind Caddy with `expose` instead of published port (part 1 hardening).
