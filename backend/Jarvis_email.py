import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from livekit.agents import function_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@function_tool
async def send_email_notification(subject: str, body: str, recipient: str = None) -> str:
    """
    Sends an email notification. Use this when you need to send information, summaries, or files (as text) to the user.
    
    Args:
        subject: The subject line of the email.
        body: The main content of the email.
        recipient: (Optional) The email address to send to. Defaults to the user's configured email.
    """
    sender_email = os.getenv("EMAIL_SENDER", "").strip()
    sender_password = os.getenv("EMAIL_PASSWORD", "").strip()
    default_recipient = os.getenv("DEFAULT_RECIPIENT", "").strip()
    
    if not sender_email or not sender_password:
        return "❌ Email credentials not configured. Please set EMAIL_SENDER and EMAIL_PASSWORD in .env file."
        
    if not recipient:
        recipient = default_recipient
        
    if not recipient:
        return "❌ No recipient specified and no default found."

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to server (Gmail default)
        # Note: This requires an App Password if 2FA is on, or "Less Secure Apps" enabled (deprecated).
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient, text)
        server.quit()
        
        logger.info(f"Email sent to {recipient}")
        return f"✅ Email sent successfully to {recipient}"
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return f"❌ Failed to send email: {e}. (Check your password or App Password settings)"
