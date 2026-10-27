# Setup and test steps for the Watch · Did it run workflow (self-hosted n8n)

Steps 1 to 12 were run in this form on 26 October 2026 (UTC): n8n 2.43.6 and Mailpit v1.31.6 from the attached `docker-compose.yml`, Docker Desktop (engine 29.8.0, Compose 5.5.1) on an Apple Silicon Mac, with a script driving headless Chromium through the n8n and Mailpit pages; the same run recorded the demo video. The compose file was used unchanged; an override file on the test machine changed only the host ports (n8n on 5691, Mailpit on 8031, because 5678 and 8025 were taken) and where the volumes live. The 15-minute part of step 12 and the Execute-button note in step 7 come from a separate check right after, on the same stack, where Order sync was switched off and on through the n8n API instead of the UI. Below, the default ports 5678 and 8025 are used.

You need Docker with Compose v2, `openssl`, `did-it-run.json` from the product download, and `docker-compose.yml` and `order-sync.json` attached to the email. Each step says what to do and what you should see. Labels in **bold** are the exact labels n8n 2.43.6 and Mailpit showed during the test.

## 1. Start the stack

Do:

```bash
mkdir n8n-watch-test && cd n8n-watch-test
# copy docker-compose.yml and order-sync.json here
echo "N8N_ENCRYPTION_KEY=$(openssl rand -hex 24)" > .env
docker compose up -d
```

Expect:
- two containers running (`docker compose ps`): `n8n` and `mailpit`;
- http://localhost:5678 shows **Set up owner account**;
- http://localhost:8025 shows an empty Mailpit inbox.

Both ports listen on 127.0.0.1 only. On a remote host, use an SSH tunnel: `ssh -L 5678:localhost:5678 -L 8025:localhost:8025 <user>@<host>` (not tested).

## 2. Owner account

Do: fill in **Email**, **First Name**, **Last Name**, **Password** and click **Next**.

Expect: n8n opens. In the test it opened on the Assistant page; the steps below start from **Overview** or the **+** button (**Add new item**) in the sidebar.

## 3. API key

Do: **Settings** › **n8n API** › **Create API key**. **Label**: `Did it run`. **Expiration**: **Never** (the default is 30 days). Leave the scopes on **All**. **Save**. Click the copy button next to the key, then **Done**.

Expect: **API key created successfully** with "Make sure to copy your API key now as you will not be able to see this again." After the copy button, a notice **API Key copied to clipboard**.

The key field shows a shortened key with "..." in the middle. In the test, the text in that field got 401 Unauthorized from the API; the value from the copy button worked.

## 4. Credentials

Do, for the first one: **+** › **New credential** › type `n8n API` in **Search for app...** › **n8n API** › **Continue**. Click the name `n8n account` at the top and change it to `n8n API account`. **API Key**: paste. **Base URL**: `http://localhost:5678/api/v1`. **Save**.

Expect: **Connection tested successfully**.

Do, for the second one: **+** › **New credential** › **SMTP** › **Continue**. Keep the name `SMTP account`. Leave **User** and **Password** empty. **Host**: `mailpit`. **Port**: `1025`. Switch **SSL/TLS** off (a **Disable STARTTLS** switch appears; leave it as it is). **Save**.

Expect: **Connection tested successfully**.

The names must be exactly `n8n API account` and `SMTP account`: the workflow refers to them by name.

## 5. A workflow to watch

Do: **+** › **New workflow**. In the editor, the **···** menu (**More actions**) › **Import** › **From file** › `order-sync.json`. Click **Publish**; in the **Publish workflow** dialog the **Version name** is filled in; click **Publish**, then **Got it**.

Expect: the dialog **Workflow published**; the button now reads **Published**. Order sync runs every minute from now on.

## 6. Did it run

Do: **+** › **New workflow** › **···** › **Import** › **From file** › `did-it-run.json`.

Expect: the workflow **Watch · Did it run**. **Publish** is greyed out; hovering shows "2 nodes have issues, fix them before publishing."

Do: open **Last successful run**, check that the **n8n API** field shows `n8n API account`, close it. Same for **Last run**.

Expect: **Publish** is available.

Do: open the **Settings** node and set:
- `alert_to`: `oncall@example.test` (or your address on a real instance);
- `require_error_workflow`: `false` (for this test, so the emails are about the watch list only).

Leave `alert_from`, `api_url` (`http://localhost:5678/api/v1`) and `heartbeat_url` (empty) as they are.

## 7. One minute, for the test

Do: open **Every 15 minutes**, set **Minutes Between Triggers** to `1`, close the node, **Publish** › **Publish** › **Got it**.

Do not use the **Execute** button under the canvas (Execute workflow) to test this workflow. In the separate check, manual runs read the saved state but did not save their own result: with nothing changed two clicks sent nothing, and right after a change two clicks sent the same email twice, which the next scheduled run then reported again.

## 8. First run

Expect, within a minute, one email in Mailpit:
- Subject: `Did it run: 1 new, 0 back to normal, 1 open`
- Body line: `- (watch list): the watch_list table has no rows, so nothing is being watched`

**Overview** › **Data tables** now lists **watch_list**.

## 9. Watch list row

Do: **Overview** › **Data tables** › **watch_list** › **Add Row**. Type `Order sync`, press Tab, type `10`, press Enter.

Expect:
- next run: one email, `Did it run: 0 new, 1 back to normal, 0 open`, with `Back to normal (1):` and the `(watch list)` line;
- the run after that: no email.

In Did it run's **Executions** tab, every run shows as succeeded.

## 10. Break it

Do: open Order sync, click the arrow next to **Published** › **Unpublish**. The dialog says "This will prevent all production executions to this workflow until you publish again." Click **Unpublish**.

Expect:
- next run: one email, `Did it run: 1 new, 0 back to normal, 1 open`, with `- Order sync: switched off (unpublished), so its trigger starts nothing`;
- one run later: no email;
- Order sync starts no runs while it is unpublished (in the test, checked through the n8n API: 0 executions in 2 minutes).

## 11. Fix it

Do: **Publish** Order sync again.

Expect, next run: one email, `Did it run: 0 new, 1 back to normal, 0 open`, with `Back to normal (1):` and `- Order sync: switched off (unpublished), so its trigger starts nothing`.

## 12. Back to 15 minutes

Do: open Did it run's **Every 15 minutes**, set **Minutes Between Triggers** to `15`, **Publish**.

Expect: from now on, a run every 15 minutes that sends nothing while nothing changes. In the separate check, with Order sync switched off through the API a few minutes before a scheduled run, that run sent the same email as in step 10; after Order sync was published again, the run 15 minutes later sent the back-to-normal email.

## 13. Clean up

```bash
docker compose down -v
```

`-v` also deletes the two volumes with n8n's database and the Mailpit inbox.

## On an existing instance

- Use your own SMTP server in the `SMTP account` credential, with the same name.
- The base URL `http://localhost:5678/api/v1` assumes n8n listens on 5678 inside its container, which is the default. If you changed `N8N_PORT` or the path, adjust it (not tested).
- Keep successful production runs in the execution list for longer than your largest `max_quiet_minutes`.
- The EC2 notes sent with this package list the differences between your part 1 EC2 setup and this test.
