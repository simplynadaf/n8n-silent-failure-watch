# Reply to Ahmet + LinkedIn promo

====================================================================
PART 1: EMAIL REPLY TO AHMET
====================================================================

Subject: Re: 50% affiliate offer + an n8n tutorial idea

Hi Ahmet,

Thanks again for the full package. I went through everything and ran the setup
myself this week, so a few notes on where I landed.

I stood the stack up on a real self-hosted box (n8n 2.43.6 on PostgreSQL 16 on
an AWS EC2 instance, not the SQLite default) to test the exact case the tutorial
is about. It holds up: I unpublished a one-minute scheduled workflow, waited two
and a half minutes, and the execution count did not move by one. Zero runs, so
nothing for an error workflow to fire on. Republished, and runs resumed within a
minute. That is the whole premise, confirmed on the setup my readers actually run.

A couple of findings from the Postgres run worth flagging on your side:
- n8n 2.43.6 logs that Postgres 16 is "outside the supported range, compatibility
  support only, upgrade to 17 or newer." Worth noting in your docs for Postgres users.
- A read-only API key (workflow:read, execution:read and the list scopes) is enough
  for the check, and a key with no write scope is correctly refused on writes. Good
  for anyone nervous about the monitor's key leaking.

On the article itself: I'm going to publish it as my own production write-up,
framed around the "no execution means no alert" problem and tested on EC2 + Postgres.
To keep it clearly editorial rather than a product placement, the tutorial stands
on the free n8n public API (I wrote a small open check so readers aren't blocked),
and Silent Failure Watch gets an honest mention as the ready-made option for people
who'd rather import a file than maintain a script. As I said earlier, I'm not joining
the affiliate program, so there's no affiliate link, just a straight mention and a
link to your Gumroad page.

If that framing works for you, I'll move to publishing. If you'd prefer I hold the
mention until I've also tried your did-it-run.json import specifically (vs. my own
check), say the word and I'll add that pass.

Appreciate how clean and honest the package was, the "what we did not test" section
made my job a lot easier.

Regards,
Sarvar


====================================================================
PART 2: LINKEDIN POST (link goes in the FIRST COMMENT, not the body)
====================================================================

--- POST BODY ---

Your n8n error workflow has a blind spot, and it is the most common way a
workflow dies.

An error workflow fires when an execution fails. That is the one thing it does.

So what happens when a workflow gets unpublished during an edit and nobody
publishes it again? Or a schedule trigger stops firing on its own?

Nothing runs. Nothing runs, so nothing fails. So no alert ever fires.

The automation is dead and the dashboard is green.

I did not want to take that on faith, so I ran it. n8n 2.43.6 on PostgreSQL 16
on an EC2 box. I unpublished a one-minute scheduled workflow and watched the
execution list through the API:

  executions before: 2
  wait 150 seconds (two missed runs)
  executions after: 2
  new executions while unpublished: 0

Zero. Two and a half minutes, and not one run. Nothing an error workflow could
have caught.

The fix is to stop waiting for a failure and start checking what actually ran.
A small workflow, every 15 minutes, reads the n8n API and asks four questions
per workflow: does it still exist, is it published, did its last run fail, did
it succeed in time. It emails you once when the answer changes, and stays quiet
otherwise.

One catch I will not let you skip: that check runs inside n8n, so if n8n itself
is down, the check is down too. A monitor that dies with the thing it watches is
not a monitor. The second layer is a heartbeat to something outside the box.

Full write-up and the code (runs on the free n8n API, tested on EC2 + Postgres)
in the first comment.

What is the sneakiest way an n8n workflow has gone quiet on you in production?

#n8n #aws #devops #automation #selfhosted

--- FIRST COMMENT (post this yourself right after publishing) ---

Repo (compose file, sample workflow, the check, architecture diagram):
https://github.com/simplynadaf/n8n-silent-failure-watch

Full tutorial:
https://dev.to/sarvar_04

This is the monitoring follow-up to my n8n-on-AWS series.
