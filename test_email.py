from app.services.gmail_service import send_email

send_email(
    "connect2varun21@gmail.com",
    "CRM Test Email",
    "Hello Varun, Gmail Integration is Working!"
)

print("Email Sent Successfully!")