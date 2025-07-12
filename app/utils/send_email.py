import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_reset_email(to_email: str, reset_link: str):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise Exception("EMAIL_ADDRESS or EMAIL_PASSWORD not set in .env")

    try:
        message = MIMEMultipart()
        message["From"] = EMAIL_ADDRESS
        message["To"] = to_email
        message["Subject"] = "Reset Your TalentTrack Password"

        body = f"""
        <p>Hello,</p>
        <p>You requested a password reset. Click the link below to reset it:</p>
        <a href="{reset_link}">{reset_link}</a>
        <p>This link will expire in 1 hour.</p>
        """
        message.attach(MIMEText(body, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(message)

    except Exception as e:
        print("Failed to send email:", e)
        raise
