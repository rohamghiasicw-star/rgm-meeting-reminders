# Reminder email drafts (for approval before anything sends)

Voice matched to Roham's own sent reminder, 13 Nov 2023, subject "Meeting Link":
  "Hi Sue, / Just a reminder for the meeting today at 11:30 AM. / Here's the meeting
   link for today's call / <link> / Thanks, Roham Ghiasi"
Short, plain, no fluff, link on its own line. Kept exactly that shape.

---

## T-60 (one hour before)

**Subject:** Our call in 1 hour

Hi {{first_name}},

Just a reminder we've got our call today at {{time_uk}}.

Here's the link:

{{meet_link}}

I've had a look at {{company}} already, so we can get straight into it.

Thanks,
Roham

---

## T-30 (thirty minutes before)

**Subject:** 30 minutes

Hi {{first_name}},

We're on in 30 minutes, {{time_uk}}.

{{meet_link}}

Thanks,
Roham

---

## Notes
- {{time_uk}} renders in the INVITEE's timezone (Europe/London for all 3 so far),
  never Bali and never the America/New_York the Calendly app displays.
- The "I've had a look at X already" line in the T-60 is the one addition to his
  original template. It is the single highest-leverage sentence available: it converts
  the reminder from admin into a reason to turn up, and it is true.
- No emoji. His 2023 version had one; the 2026 landing page voice does not use them.
- Signature is just "Roham". The old signature block carried the Halifax 902 number
  and "Digital Expert Marketing", both stale now that NAP is "Canada".
