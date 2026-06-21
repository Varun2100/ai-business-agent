import pickle
import base64
import json
import sqlite3
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from groq import Groq


GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"
GROQ_MODEL = "llama-3.1-8b-instant"

SKIP_KEYWORDS = [
    "noreply", "no-reply", "donotreply", "do-not-reply", "notification",
    "newsletter", "mailer", "alerts@", "info@", "naukri.com", "indeed.com",
    "internshala.com", "unstop.news", "zoom.us", "pinterest.com",
    "airtable.com", "hirist.com", "goatfundedtrader.com", "sportzcontests.com",
    "linkedin.com", "facebookmail.com", "accounts.google.com",
]


def is_real_person(email_addr: str) -> bool:
    if not email_addr or "@" not in email_addr:
        return False
    email_lower = email_addr.lower()
    return not any(skip in email_lower for skip in SKIP_KEYWORDS)


def _get_gmail():
    with open("token.pickle", "rb") as f:
        creds = pickle.load(f)
    return build("gmail", "v1", credentials=creds)


def _get_ai():
    return Groq(api_key=GROQ_API_KEY)


def generate_ai_reply(sender_name: str, sender_email: str, subject: str, body: str) -> str:
    client = _get_ai()
    prompt = f"""You are a professional AI assistant for AutoPilot AI CRM. 
Write a warm, professional reply to this email.

From: {sender_name} <{sender_email}>
Subject: {subject}
Message: {body}

Rules:
- Be friendly and professional
- Keep it concise (3-5 sentences)
- Sign off as "AutoPilot AI Team"
- Output ONLY the email body text, nothing else
"""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


def generate_lead_email(lead: dict, custom_context: str = "") -> dict:
    client = _get_ai()
    prompt = f"""You are a sales AI for AutoPilot AI CRM. Write a personalized outreach email for this lead.

Lead Info:
- Email: {lead.get('customer_email', '')}
- Status: {lead.get('status', 'New')}
- Lead Score: {lead.get('lead_score', 0)}/100
- Their Message: {lead.get('customer_message', 'No message')}

Additional Context: {custom_context if custom_context else 'Standard follow-up'}

Return ONLY valid JSON: {{"subject": "...", "body": "..."}}
Sign as "AutoPilot AI Team". JSON only, no markdown.
"""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])


def _send_raw(service, to, subject, body, thread_id=None, reply_to_msg_id=None):
    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    if reply_to_msg_id:
        msg["In-Reply-To"] = reply_to_msg_id
        msg["References"] = reply_to_msg_id
    msg.attach(MIMEText(body, "plain"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    payload = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id
    return service.users().messages().send(userId="me", body=payload).execute()


def get_unread_emails(max_results=10, filter_promotional=True):
    service = _get_gmail()
    results = service.users().messages().list(
        userId="me", maxResults=max_results, labelIds=["INBOX", "UNREAD"]
    ).execute()
    messages = results.get("messages", [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        from_header = headers.get("From", "")
        from_email = from_header.split("<")[-1].replace(">", "").strip()
        if filter_promotional and not is_real_person(from_email):
            continue
        body = ""
        payload = detail.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                        break
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        emails.append({
            "id": detail["id"], "thread_id": detail["threadId"],
            "message_id_header": headers.get("Message-ID", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "from": from_header, "from_name": from_header.split("<")[0].strip(),
            "from_email": from_email, "date": headers.get("Date", ""),
            "body": body[:1000], "snippet": detail.get("snippet", ""),
        })
    return emails


def mark_as_read(message_id):
    service = _get_gmail()
    service.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def run_auto_reply(interval_minutes=5, status_callback=None):
    results = {"checked": 0, "replied": 0, "skipped": 0, "errors": [], "details": []}
    try:
        service = _get_gmail()
        all_unread = service.users().messages().list(
            userId="me", maxResults=20, labelIds=["INBOX", "UNREAD"]
        ).execute().get("messages", [])
        emails = get_unread_emails(max_results=20, filter_promotional=True)
        results["checked"] = len(emails)
        results["skipped"] = len(all_unread) - len(emails)
        for email in emails:
            try:
                if status_callback:
                    status_callback(f"Generating reply for: {email['subject']}")
                reply_body = generate_ai_reply(
                    sender_name=email["from_name"], sender_email=email["from_email"],
                    subject=email["subject"], body=email["body"] or email["snippet"],
                )
                _send_raw(
                    service=service, to=email["from_email"], subject=f"Re: {email['subject']}",
                    body=reply_body, thread_id=email["thread_id"],
                    reply_to_msg_id=email["message_id_header"],
                )
                mark_as_read(email["id"])
                results["replied"] += 1
                results["details"].append({
                    "to": email["from_email"], "subject": email["subject"],
                    "status": "✅ Replied", "reply_preview": reply_body[:100] + "...",
                })
            except Exception as e:
                results["errors"].append(f"{email['subject']}: {str(e)}")
                results["details"].append({
                    "to": email.get("from_email", "?"), "subject": email["subject"],
                    "status": f"❌ Error: {str(e)[:80]}", "reply_preview": "",
                })
    except Exception as e:
        results["errors"].append(f"Fatal: {str(e)}")
    return results


def send_emails_to_leads(custom_context="", db_path="leads.db", status_filter="All", status_callback=None):
    results = {"sent": 0, "failed": 0, "details": []}
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        if status_filter == "All":
            leads = conn.execute("SELECT * FROM leads").fetchall()
        else:
            leads = conn.execute("SELECT * FROM leads WHERE status = ?", (status_filter,)).fetchall()
        conn.close()
    except Exception as e:
        results["details"].append({"email": "DB Error", "status": str(e)})
        return results
    service = _get_gmail()
    for row in leads:
        lead = dict(row)
        email_addr = lead.get("customer_email", "")
        if not email_addr or "@" not in email_addr:
            continue
        try:
            if status_callback:
                status_callback(f"Generating email for {email_addr}...")
            generated = generate_lead_email(lead, custom_context)
            subject = generated.get("subject", "Following up from AutoPilot AI")
            body = generated.get("body", "")
            _send_raw(service=service, to=email_addr, subject=subject, body=body)
            results["sent"] += 1
            results["details"].append({
                "email": email_addr, "subject": subject,
                "status": "✅ Sent", "preview": body[:120] + "...",
            })
            time.sleep(1)
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "email": email_addr, "subject": "",
                "status": f"❌ {str(e)[:80]}", "preview": "",
            })
    return results