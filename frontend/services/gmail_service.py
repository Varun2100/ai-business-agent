import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send",
          "https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.modify"]

def _get_service():
    with open("token.pickle", "rb") as token:
        creds = pickle.load(token)
    return build("gmail", "v1", credentials=creds)

def send_email(sender_email=None, to="", subject="", body="", body_type="plain", cc=None, **kwargs):
    service = _get_service()
    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    msg.attach(MIMEText(body, body_type))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"success": True, "message_id": result.get("id"), "thread_id": result.get("threadId"), "error": None}

def reply_to_email(sender_email=None, thread_id="", message_id="", to="", subject="", body="", body_type="plain"):
    service = _get_service()
    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
    msg["In-Reply-To"] = message_id
    msg["References"] = message_id
    msg.attach(MIMEText(body, body_type))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = service.users().messages().send(userId="me", body={"raw": raw, "threadId": thread_id}).execute()
    return {"success": True, "message_id": result.get("id"), "thread_id": result.get("threadId"), "error": None}

def get_recent_emails(sender_email=None, max_results=10):
    service = _get_service()
    results = service.users().messages().list(userId="me", maxResults=max_results, labelIds=["INBOX"]).execute()
    messages = results.get("messages", [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["Subject", "From", "Message-ID", "Date"]).execute()
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        emails.append({
            "id": detail["id"],
            "thread_id": detail["threadId"],
            "message_id_header": headers.get("Message-ID", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "from": headers.get("From", ""),
            "date": headers.get("Date", ""),
            "snippet": detail.get("snippet", ""),
        })
    return emails