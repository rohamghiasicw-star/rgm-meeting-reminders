# RG Marketing meeting reminders

Emails every Calendly invitee **1 hour** and **30 minutes** before their call.
Free, and it runs in the cloud, so the laptop can be shut.

## How it works
Public repo, so GitHub Actions minutes are unlimited. Each run holds an **internal
loop** that checks every 3 minutes for 5.5 hours; the `*/30` schedule only has to
restart it. That matters because GitHub's bare cron is unreliable: a `*/15` schedule
on this repo fired **3 times in 20 hours**. Same pattern as `rgm-lead-watcher`.

`remind.py` reads a Google Calendar secret iCal feed, finds calls starting soon, and
emails the invitee from Roham's Gmail over SMTP.

## What it will and will not email
Only events **Calendly created** (matched on `calendly.com` in the description).
The live calendar carries 119 events; without that filter clients and internal
meetings would get prospect reminders. Cancelled events are skipped.

## Secrets
`ICS_URL`, `GMAIL_USER`, `GMAIL_APP_PASSWORD` in Actions secrets. Encrypted, and
fork PRs never receive them.

## Timing
| stage | window |
|---|---|
| T-60 | 30 to 75 minutes before |
| T-30 | 0 to 35 minutes before |

Wide on purpose. A late tick still catches the reminder; `state/sent.json` stops the
width causing duplicates. State keys are sha256 hashed, so this public repo reveals
nothing about the calendar.

## Test without sending
Actions -> meeting-reminders -> **Run workflow**, leave *dry run* ticked, set
*minutes* to 2. The log prints what it would have sent.

## Local fallback
`run-local.sh` + `com.rgm.reminders.plist` run the same engine under launchd, reading
`~/.rgm-reminders.env`. Currently **unloaded** so the two schedulers cannot double-send.
