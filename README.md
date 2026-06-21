# AI Business Agent

An AI-powered sales assistant that automates lead outreach. It generates personalized outreach emails using an LLM, manages leads through a local database, and handles incoming Gmail replies through an AI chatbot — turning raw leads into engaged conversations with minimal manual effort.

## What it does

- **Automated lead emails** — generates personalized outreach emails for each lead based on their profile, lead score, and message history, instead of using static templates
- **Gmail integration** — connects to Gmail via OAuth to send outreach emails and read/reply to incoming responses
- **AI reply agent** — uses an LLM to draft context-aware replies to customer emails automatically
- **Lead management** — stores and tracks leads in a local SQLite database, with lead scoring and status tracking
- **Chatbot interface** — a simple web-based chat widget for interacting with the agent directly

## Tech stack

- **Backend:** Python
- **AI / LLM:** Groq API (Llama 3.1) for email generation, OpenAI API for additional AI services
- **Email:** Gmail API (OAuth2) via `google-api-python-client`
- **Database:** SQLite
- **Frontend:** HTML/JS chat widget

## Project structure

```
app/
  agents/          # Reply generation logic
  database/        # Database models and access layer
  services/        # Gmail and OpenAI service integrations
  main.py          # Application entry point
frontend/
  services/        # Frontend-side service integrations
  chatbot.html     # Chat widget UI
ai_email_service.py  # Core email generation logic (Groq-powered)
gmail_auth.py         # Gmail OAuth authentication
chatbot_server.py     # Chatbot backend server
```

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/Varun2100/ai-business-agent.git
   cd ai-business-agent
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your own API keys:
   ```
   GROQ_API_KEY=your_groq_key_here
   OPENAI_API_KEY=your_openai_key_here
   ```

4. Set up Gmail OAuth credentials (`credentials.json`) by following the [Google API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python), and place the file in the project root. **Do not commit this file** — it's already excluded via `.gitignore`.

5. Run the application:
   ```bash
   python app/main.py
   ```

## Notes

- API keys and credentials are loaded from environment variables / a local `.env` file, never hardcoded — see `.gitignore` for excluded files.
- This project is a work in progress; contributions and suggestions are welcome.

## License

This project is for portfolio/educational purposes.
