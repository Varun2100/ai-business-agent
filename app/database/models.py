from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    customer_email = Column(String)

    customer_message = Column(String)

    ai_reply = Column(String)

    status = Column(
        String,
        default="New"
    )

    lead_score = Column(
        Integer,
        default=0
    )

    lead_type = Column(
        String,
        default="Cold"
    )

    estimated_value = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )