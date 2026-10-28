# Notes for testing on your EC2 setup

## How this was verified

The numbers in this repo come from a real run on n8n 2.43.6 + PostgreSQL 16.15 on an Amazon Linux 2023 EC2 box (2026-10-27 UTC). The full traceable log is in [`test-evidence.md`](test-evidence.md): `did_it_run_check.py` run against the live API across three states (healthy, unpublished, republished), zero new executions during 150s unpublished, and an alert delivered over SMTP to Mailpit.

## Where your part 1 setup differs

These are the points where your part 1 setup ("I Followed the n8n AWS Docs and It Broke at the First Command") differs from the stack I tested on. None of them were tested on EC2.

1. **n8n version.** The compose file in your part 1 pins `n8nio/n8n:1.123.64`. The check needs the n8n 2.x public API; it was built and tested on 2.43.6. The UI steps (Publish, Unpublish, the Create API Key dialog) are what 2.43.6 shows. Nothing was run on 1.x, so I make no claim about it. To run this on your box, either:
   - run this repo's compose file as a separate test stack next to your existing one (it uses its own volumes; change its host port if 5678 is taken), or
   - move your stack to a 2.x image first. The 1.123.64 to 2.x upgrade on Postgres was not tested.

2. **Database.** Your stack runs n8n on Postgres 16. The test used n8n's default database (SQLite). Postgres was not tested with this workflow. The check only uses the public API, which is a reason to expect it to work, not a test.

3. **Ports, the base URL and the tunnel.** The credential's base URL `http://localhost:5678/api/v1` is n8n calling itself inside its own container. In the test, n8n was published on a different host port (5691) and the credential still used `localhost:5678` and passed its connection test. Two things to know for your setup (neither was tested):
   - The SSH tunnel (`ssh -L 5678:localhost:5678 ...`) needs n8n published on the host, as `127.0.0.1:5678:5678` in this repo's compose file. Your part 1 compose publishes `"5678:5678"` on all interfaces; with `127.0.0.1:` in front, the editor is reachable only through the tunnel.
   - Your part 1 hardening checklist replaces `ports` with `expose` for 5678. Then there is no host port, the tunnel cannot reach n8n, and access goes through Caddy instead. The base URL inside the container stays the same.

4. **Mailpit on EC2.** Two options for your own test:
   - add the `mailpit` service from this repo's compose file to your stack, together with its `mailpit_data` entry under `volumes:`, and keep 8025 on 127.0.0.1, reached through an SSH tunnel. Do not open 8025 in the security group, for the same reason your hardening checklist stops publishing 5678;
   - or point the `SMTP account` credential at a real mail service. That path was not tested: the test only sent mail to Mailpit.

5. **Secure cookie.** Your part 1 sets `N8N_SECURE_COOKIE=false` so the first login works over plain HTTP on the public IP. This repo's compose file does not set it: the test opened n8n at `http://localhost`, and the owner setup and login worked without it. Through an SSH tunnel you also open `localhost`, which should behave the same, but that was not tested.

6. **Saved executions.** The check reads past runs from the execution list. This repo's compose file sets `EXECUTIONS_DATA_SAVE_ON_SUCCESS: all` and `EXECUTIONS_DATA_SAVE_ON_ERROR: all` explicitly. Your part 1 compose does not set them; check that successful production runs are saved and not pruned before the limits you watch for (`EXECUTIONS_DATA_MAX_AGE`, `EXECUTIONS_DATA_PRUNE_MAX_COUNT`), or the freshness check goes blind.

7. **Time zone.** The time in the emails is the instance's time zone. This repo's compose file sets `GENERIC_TIMEZONE` (UTC unless you set it in `.env`). Your part 1 compose does not set it.

8. **Instance architecture.** The n8n and Mailpit images in this repo's compose file are pinned to multi-platform image indexes; both list `amd64` and `arm64`, so they fit a `t3` and a Graviton instance.

9. **The heartbeat** was not tested end to end. Wire it to an external uptime monitor and confirm the monitor alerts when the pings stop.

10. **API key scope.** Use a read-only key (`workflow:read`, `workflow:list`, `execution:read`, `execution:list`). On the real run a write attempt from a read-only key returned `{"message":"Forbidden"}`, so the key cannot change anything if it leaks.
