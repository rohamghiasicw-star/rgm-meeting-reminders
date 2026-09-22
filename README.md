# RG Marketing meeting reminders

Emails every Calendly invitee **1 hour** and **30 minutes** before their call.
Free. No Calendly premium, no Zapier, no Claude, no server to maintain.

## How it works
GitHub Actions runs `remind.py` every 15 minutes during UK business hours.
The script reads a Google Calendar secret iCal feed, finds calls starting soon,
and emails the invitee from Roham's own Gmail over SMTP.

`state/sent.json` records what has already gone out (keyed by event UID + stage)
so nothing is ever sent twice, even if a run is delayed or retried.

## The three secrets
Set at **Settings -> Secrets and variables -> Actions**:

| `ICS_URL` | Google Calendar -> Settings -> *Settings for my calendars* -> your calendar -> **Integrate calendar** -> **Secret address in iCal format** |
| `GMAIL_USER` | `rohamghiasicw@gmail.com` |
| `GMAIL_APP_PASSWORD` | myaccount.google.com/apppasswords (needs 2FA on). 16 characters. NOT the normal Gmail password |

## Timing
| stage | fires when the call is | window |
|---|---|---|
| T-60 | about an hour out | 30-75 min before |
| T-30 | about half an hour out | 0-35 min before |

Windows are deliberately wide. GitHub's scheduler drifts under load, so a late
run still catches the reminder instead of skipping it. The state file stops
the wide window causing duplicates.

## Test it without sending anything
Actions -> meeting-reminders -> **Run workflow** -> leave *dry run* ticked.
The log prints the emails it would have sent.

## Knobs
- `INVITEE_TZ` in the workflow: fallback timezone when the calendar event does
  not name one. Currently `Europe/London`.
- `EVENT_MATCH` env var: only remind for events whose title contains this string.
  Unset, so every calendar event with an outside attendee gets a reminder.
