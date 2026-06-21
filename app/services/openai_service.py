import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("models/gemini-2.5-flash")

def generate_ai_reply(email_text):

    prompt = f"""
    You are a professional business assistant.

    Reply professionally to this customer email:

    {email_text}
    """

    response = model.generate_content(prompt)

    return response.text