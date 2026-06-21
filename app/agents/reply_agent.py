from app.services.openai_service import generate_ai_reply

class ReplyAgent:

    def process_email(self, email_text):

        reply = generate_ai_reply(email_text)

        return reply