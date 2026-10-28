#!/usr/bin/env python3
"""
did-it-run check, standalone proof.

Implements a 4-step liveness check in plain Python against the n8n public
API, so the tutorial is fully reproducible with nothing but the API. This is
the script I actually run in the article.

For each workflow on the watch list it checks:
  1. a workflow with that exact name exists
  2. it is published (active=true)
  3. its last run did not fail
  4. it had a successful run within max_quiet_minutes (0 = no limit)

It prints one plain-text report, the same shape as the email body.
"""
import os, sys, json, urllib.request, urllib.parse
from datetime import datetime, timezone

API = os.environ.get("N8N_API_URL", "http://localhost:5678/api/v1")
KEY = os.environ["N8N_API_KEY"]

# watch list: workflow name -> max_quiet_minutes (0 = no time limit)
WATCH = {
    "Order sync": 10,
}

def get(path):
    req = urllib.request.Request(API + path, headers={"X-N8N-API-KEY": KEY})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)

def minutes_since(ts):
    if not ts:
        return None
    t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - t).total_seconds() / 60.0

def check():
    workflows = {w["name"]: w for w in get("/workflows").get("data", [])}
    problems = []
    for name, max_quiet in WATCH.items():
        wf = workflows.get(name)
        if wf is None:
            problems.append(f"- {name}: no workflow with this exact name exists (deleted or renamed)")
            continue
        if not wf.get("active"):
            problems.append(f"- {name}: switched off (unpublished), so its trigger starts nothing")
            continue
        wid = wf["id"]
        last = get(f"/executions?workflowId={wid}&limit=1").get("data", [])
        if last and last[0].get("status") == "error":
            problems.append(f"- {name}: last run failed")
            continue
        if max_quiet and max_quiet > 0:
            succ = get(f"/executions?workflowId={wid}&status=success&limit=1").get("data", [])
            if not succ:
                problems.append(f"- {name}: no successful run on record")
                continue
            mins = minutes_since(succ[0].get("startedAt"))
            if mins is not None and mins > max_quiet:
                problems.append(f"- {name}: no successful run in {int(mins)} min (limit {max_quiet})")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    active = sum(1 for w in workflows.values() if w.get("active"))
    print(f"Checked {len(WATCH)} watched workflow(s) and {active} active workflow(s) at {now} UTC.\n")
    if problems:
        print(f"Open ({len(problems)}):")
        print("\n".join(problems))
    else:
        print("All watched workflows are published and ran successfully in time. Nothing to report.")

if __name__ == "__main__":
    check()
