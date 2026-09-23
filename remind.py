#!/usr/bin/env python3
"""
Automatic meeting reminders for RG Marketing.
Reads a Google Calendar secret iCal feed, emails the invitee at T-60 and T-30.
No Calendly premium, no Zapier, no Claude. Runs on GitHub Actions cron.
"""
import os, re, ssl, json, smtplib, urllib.request, sys
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ICS_URL      = os.environ["ICS_URL"]
GMAIL_USER   = os.environ["GMAIL_USER"]
GMAIL_PASS   = os.environ["GMAIL_APP_PASSWORD"]
INVITEE_TZ   = os.environ.get("INVITEE_TZ", "Europe/London")
EVENT_MATCH  = os.environ.get("EVENT_MATCH", "")   # optional extra title filter
ONLY_CALENDLY = os.environ.get("ONLY_CALENDLY", "1") == "1"
DRY_RUN      = os.environ.get("DRY_RUN", "") == "1"
STATE_PATH   = "state/sent.json"

# Fire windows in minutes-before-start. Wide on purpose: GitHub Actions cron
# drifts, so a delayed run still catches the reminder instead of skipping it.
STAGES = [("T60", 30, 75), ("T30", 0, 35)]


def unfold(text):
    """RFC5545: continuation lines start with a space or tab."""
    return re.sub(r"\r?\n[ \t]", "", text)


def parse_dt(val, params):
    if params.get("VALUE") == "DATE":
        return None                      # all-day, never a booked call
    if val.endswith("Z"):
        return datetime.strptime(val, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    tzid = params.get("TZID")
    naive = datetime.strptime(val, "%Y%m%dT%H%M%S")
    return naive.replace(tzinfo=ZoneInfo(tzid) if tzid else timezone.utc)


def unesc(v, nl=False):
    """Undo RFC5545 text escaping: \\n newline, \\, comma, \\; semicolon, \\\\ backslash."""
    out = v.replace(chr(92) + "n", chr(10)).replace(chr(92) + "N", chr(10)) if nl else v
    out = out.replace(chr(92) + ",", ",").replace(chr(92) + ";", ";")
    return out.replace(chr(92) + chr(92), chr(92))


def parse_ics(raw):
    events, cur = [], None
    for line in unfold(raw).split("\n"):
        line = line.rstrip("\r")
        if line == "BEGIN:VEVENT":
            cur = {"attendees": []}
            continue
        if line == "END:VEVENT":
            if cur:
                events.append(cur)
            cur = None
            continue
        if cur is None or ":" not in line:
            continue
        head, _, val = line.partition(":")
        bits = head.split(";")
        name = bits[0].upper()
        params = {}
        for p in bits[1:]:
            k, _, v = p.partition("=")
            params[k.upper()] = v.strip('"')
        if name == "UID":
            cur["uid"] = val
        elif name == "SUMMARY":
            cur["summary"] = unesc(val)
        elif name == "DESCRIPTION":
            cur["description"] = unesc(val, nl=True)
        elif name == "LOCATION":
            cur["location"] = unesc(val)
        elif name == "DTSTART":
            cur["start"] = parse_dt(val, params)
        elif name == "STATUS":
            cur["status"] = val.upper()
        elif name == "ATTENDEE":
            email = val.split("mailto:")[-1].strip().lower()
            cur["attendees"].append({"email": email,
                                     "cn": params.get("CN", "").strip()})
    return events


MEET_RE = re.compile(r"https://meet\.google\.com/[a-z0-9-]+", re.I)
ZOOM_RE = re.compile(r"https://[a-z0-9.-]*zoom\.us/j/\S+", re.I)


def meeting_link(ev):
    blob = " ".join([ev.get("location", ""), ev.get("description", "")])
    for rx in (MEET_RE, ZOOM_RE):
        m = rx.search(blob)
        if m:
            return m.group(0).rstrip(">,.)")
    return ev.get("location", "").strip()


SELF = {e.strip().lower() for e in
        (os.environ.get("SELF_EMAILS", "") + "," + GMAIL_USER).split(",") if e.strip()}


def invitee(ev):
    """The attendee who is not Roham."""
    for a in ev["attendees"]:
        if a["email"] and a["email"] not in SELF:
            return a
    return None


def first_name(att, ev):
    if att.get("cn") and "@" not in att["cn"]:
        return att["cn"].split()[0]
    # Calendly titles its events "<Invitee> and <Host>"
    m = re.match(r"(.+?)\s+and\s+", ev.get("summary", ""))
    if m:
        return m.group(1).split()[0]
    return att["email"].split("@")[0].split(".")[0].title()


def company(ev):
    m = re.search(r"Company Website\s*[:\n]\s*(\S+)", ev.get("description", ""), re.I)
    if not m:
        return None
    host = re.sub(r"^https?://", "", m.group(1)).split("/")[0]
    return re.sub(r"^www\.", "", host).strip() or None


def invitee_tz(ev):
    m = re.search(r"\b([A-Za-z]+/[A-Za-z_+-]+)\b", ev.get("description", ""))
    if m:
        try:
            ZoneInfo(m.group(1))
            return m.group(1)
        except Exception:
            pass
    return INVITEE_TZ


def build(stage, ev, att):
    tz = invitee_tz(ev)
    when = ev["start"].astimezone(ZoneInfo(tz))
    t = when.strftime("%-I:%M%p").lower().replace(":00", "")
    name, link, co = first_name(att, ev), meeting_link(ev), company(ev)
    if stage == "T60":
        subject = "Our call in 1 hour"
        body = f"Hi {name},\n\nJust a reminder we've got our call today at {t}.\n\nHere's the link:\n\n{link}\n"
        if co:
            body += f"\nI've had a look at {co} already, so we can get straight into it.\n"
        body += "\nThanks,\nRoham\n"
    else:
        subject = "30 minutes"
        body = f"Hi {name},\n\nWe're on in 30 minutes, {t}.\n\n{link}\n\nThanks,\nRoham\n"
    return subject, body


def load_state():
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(st):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    st = {k: v for k, v in st.items() if v >= cutoff}
    with open(STATE_PATH, "w") as f:
        json.dump(st, f, indent=1, sort_keys=True)


def send(to_addr, subject, body):
    msg = EmailMessage()
    msg["From"] = GMAIL_USER
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)


def main():
    raw = urllib.request.urlopen(ICS_URL, timeout=45).read().decode("utf-8", "replace")
    now = datetime.now(timezone.utc)
    state = load_state()
    sent = 0

    for ev in parse_ics(raw):
        if not ev.get("start") or ev.get("status") == "CANCELLED":
            continue
        summary = ev.get("summary", "")
        if summary.lower().startswith(("canceled:", "cancelled:")):
            continue
        # Only Calendly-created bookings. Everything else on this calendar is a
        # client meeting or an internal call and must never get a reminder.
        if ONLY_CALENDLY and "calendly.com" not in ev.get("description", "").lower():
            continue
        if EVENT_MATCH and EVENT_MATCH.lower() not in summary.lower():
            continue
        mins = (ev["start"] - now).total_seconds() / 60.0
        att = invitee(ev)
        if not att:
            continue
        for stage, lo, hi in STAGES:
            if not (lo < mins <= hi):
                continue
            key = f"{ev.get('uid','?')}:{stage}"
            if key in state:
                continue
            subject, body = build(stage, ev, att)
            print(f"[{stage}] {att['email']} in {mins:.0f}m -> {subject}")
            if DRY_RUN:
                print("---\n" + body + "---")
            else:
                send(att["email"], subject, body)
            state[key] = now.isoformat()
            sent += 1

    save_state(state)
    print(f"done. {sent} reminder(s) sent." if sent else "done. nothing due.")


if __name__ == "__main__":
    sys.exit(main())
