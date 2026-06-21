from app.database.db import SessionLocal
from app.database.models import Lead
from app.database.db import engine
from app.database.models import Base
from fastapi import FastAPI
from pydantic import BaseModel

from app.agents.reply_agent import ReplyAgent

def calculate_lead_score(message):
    message = message.lower()

    score = 20

    if "urgent" in message:
        score += 30

    if "budget" in message:
        score += 20

    if "$" in message:
        score += 20

    if "ecommerce" in message:
        score += 10

    if score >= 80:
        lead_type = "Hot"
        value = 10000

    elif score >= 50:
        lead_type = "Warm"
        value = 5000

    else:
        lead_type = "Cold"
        value = 1000

    return score, lead_type, value

app = FastAPI()

Base.metadata.create_all(bind=engine)

reply_agent = ReplyAgent()

class EmailRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {
        "message": "AI Business Automation Agent Running"
    }

@app.post("/generate-reply")
def generate_reply(request: EmailRequest):

    reply = reply_agent.process_email(
        request.message
    )

    score, lead_type, value = calculate_lead_score(
        request.message
    )

    db = SessionLocal()

    new_lead = Lead(
        customer_email="client@example.com",
        customer_message=request.message,
        ai_reply=reply,
        lead_score=score,
        lead_type=lead_type,
        estimated_value=value
    )

    db.add(new_lead)
    db.commit()
    db.close()

    return {
            "reply": reply
        }
 