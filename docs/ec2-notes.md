# Notes for testing on your EC2 setup

## Our test run

- When and where: 26 October 2026 (UTC), Docker Desktop (engine 29.8.0, Compose 5.5.1) on an Apple Silicon Mac, n8n 2.43.6 and Mailpit v1.31.6 from the draft's compose file. Host ports were 5691 and 8031 instead of 5678 and 8025, which were taken on that machine, and the volumes lived in a scratch folder; nothing else in the compose file changed.
- Recorded run: a script drove headless Chromium through steps 1 to 12 in the n8n and Mailpit pages and recorded the demo video. It checked each result against the n8n API and the Mailpit inbox: 17 checks, all passed. The times in the draft's sample emails (UTC) are from this run. Order sync was unpublished for about two minutes and started no runs in that time.
- Separate check right after, on the same stack: the 15-minute schedule and the Execute button. Order sync was switched off and on through the n8n API there, not through the UI. 7 checks, all passed.
- What was not covered is listed at the end of the draft. Replace the bracketed "What this test covered" section with your own run.

## Where your part 1 setup differs

These are the points where your part 1 setup ("I Followed the n8n AWS Docs and It Broke at the First Command") differs from the stack the draft was tested on. None of them were tested on EC2.

1. **n8n version.** The compose file in your part 1 pins `n8nio/n8n:1.123.64`. The watch workflow (Watch · Did it run) needs n8n 2.x; it was built and tested on 2.43.6. The UI steps in the draft (Publish, Unpublish, the Data tables tab, the Create API Key dialog) are what 2.43.6 shows. Nothing was run on 1.x, so the draft makes no claim about it. To follow the draft on your box, either:
   - run the draft's compose file as a separate test stack next to your existing one (it uses its own volumes; change its host port if 5678 is taken), or
   - move your stack to a 2.x image first. The 1.123.64 to 2.x upgrade on Postgres was not tested.

2. **Database.** Your stack runs n8n on Postgres 16. The test used n8n's default database (SQLite). Postgres was not tested with this workflow. The watch workflow only uses the public API and a data table, which is a reason to expect it to work, not a test.

3. **Ports, the base URL and the tunnel.** The credential's base URL `http://localhost:5678/api/v1` is n8n calling itself inside its own container. In the test, n8n was published on a different host port (5691) and the credential still used `localhost:5678` and passed its connection test. Two things to know for your setup (neither was tested):
   - The SSH tunnel in the draft (`ssh -L 5678:localhost:5678 ...`) needs n8n published on the host, as `127.0.0.1:5678:5678` in the draft's compose file. Your part 1 compose publishes `"5678:5678"` on all interfaces; with `127.0.0.1:` in front, the editor is reachable only through the tunnel.
   - Your hardening checklist replaces `ports` with `expose` for 5678. Then there is no host port, the tunnel cannot reach n8n, and access goes through Caddy instead. The base URL inside the container stays the same.

4. **Mailpit on EC2.** Two options for your own test:
   - add the `mailpit` service from the draft's compose file to your stack, together with its `mailpit_data` entry under `volumes:`, and keep 8025 on 127.0.0.1, reached through an SSH tunnel. Do not open 8025 in the security group, for the same reason your hardening checklist stops publishing 5678;
   - or point the `SMTP account` credential at a real mail service. That path was not tested: the test only sent mail to Mailpit.

5. **Secure cookie.** Your part 1 sets `N8N_SECURE_COOKIE=false` so the first login works over plain HTTP on the public IP. The draft's compose file does not set it: the test opened n8n at `http://localhost`, and the owner setup and login worked without it. Through an SSH tunnel you also open `localhost`, which should behave the same, but that was not tested.

6. **Saved executions.** The watch workflow reads past runs from the execution list. The draft's compose file sets `EXECUTIONS_DATA_SAVE_ON_SUCCESS: all` and `EXECUTIONS_DATA_SAVE_ON_ERROR: all` explicitly. Your part 1 compose does not set them; check that successful production runs are saved and not pruned before the limits you put in `watch_list` (`EXECUTIONS_DATA_MAX_AGE`, `EXECUTIONS_DATA_PRUNE_MAX_COUNT`). Also, importing `did-it-run.json` through the editor did not keep the file's own workflow settings (`saveDataSuccessExecution` and `saveDataErrorExecution`, both `all`); after the import the workflow followed the instance settings. With the compose file's values this made no difference in the test.

7. **Time zone.** The time in the emails is the instance's time zone. The draft's compose file sets `GENERIC_TIMEZONE` (UTC unless you set it in `.env`). Your part 1 compose does not set it.

8. **Instance architecture.** The n8n and Mailpit images in the draft's compose file are pinned to multi-platform image indexes; both list `amd64` and `arm64`, so they fit a `t3` and a Graviton instance. Only `arm64` was actually run (the test machine is an Apple Silicon Mac).

9. **The one-minute schedule.** Step 7 sets the watch workflow to run every minute for the test. Put it back to 15 (step 12) before you leave it running.

10. **Execute button.** Do not use the editor's **Execute** button (Execute workflow) to test the watch workflow. In the separate check, with nothing changed two clicks sent nothing; right after a change two clicks sent the same email twice and the next scheduled run reported the change again: manual runs read the saved state but do not save it. n8n's documentation says static data is saved only when the workflow is published and called by a trigger or webhook.

11. **The heartbeat** was not part of this test. The product's own test notes (LIMITS.md) say pings went out after every finished run and stopped when the workflow was switched off or the server was stopped; they did not test what a monitoring service does when the pings stop.

12. **API key scope.** The test used the default scope (All). Narrower scopes were not tested.
