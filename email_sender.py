"""
Email Sender via Gmail SMTP
Sends the HTML digest email using Gmail's SMTP server.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENTS, EMAIL_SUBJECT


def send_digest(html_body: str, text_body: str) -> bool:
    """
    Send the digest email.
    Returns True on success, False on failure.
    """
    if not EMAIL_PASSWORD or EMAIL_PASSWORD == "YOUR_APP_PASSWORD_HERE":
        print("\n⚠️  Email not sent: EMAIL_PASSWORD secret is not set.")
        print("   GitHub Actions: Settings → Secrets and variables → Actions → New repository secret")
        print("   Locally: export EMAIL_PASSWORD='your-gmail-app-password'")
        print("   App Password guide: https://myaccount.google.com/apppasswords")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = EMAIL_SUBJECT
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = ", ".join(EMAIL_RECIPIENTS)

        # Attach plain-text first, HTML second (preferred)
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        print(f"  Connecting to Gmail SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_string())

        print(f"  ✅ Digest sent to: {', '.join(EMAIL_RECIPIENTS)}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("\n❌ Authentication failed. Make sure you're using a Gmail App Password.")
        print("   Your regular Gmail password will NOT work.")
        print("   Get an App Password at: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"\n❌ Failed to send email: {e}")
        return False
