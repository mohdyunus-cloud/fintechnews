"""
Email Sender via Gmail SMTP
Sends the HTML digest email using Gmail's SMTP server.
Uses port 587 + STARTTLS (more reliable on cloud runners than port 465 SSL).
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

    if not EMAIL_RECIPIENTS:
        print("\n⚠️  Email not sent: EMAIL_RECIPIENTS secret is not set.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = EMAIL_SUBJECT
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = ", ".join(EMAIL_RECIPIENTS)

        # Attach plain-text first, HTML second (preferred)
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        print(f"  Connecting to Gmail SMTP (smtp.gmail.com:587)...")
        # Port 587 + STARTTLS is more reliable on cloud/CI runners than 465 SSL
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_string())

        print(f"  ✅ Digest sent to: {', '.join(EMAIL_RECIPIENTS)}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Gmail authentication failed (code {e.smtp_code}): {e.smtp_error.decode(errors='replace')}")
        print("   Checklist:")
        print("   1. Is 2-Step Verification ON at myaccount.google.com/security ?")
        print("   2. Is the password a Gmail App Password (not your login password)?")
        print("      → myaccount.google.com/apppasswords — create a new one if unsure")
        print("   3. Is IMAP enabled in Gmail settings?")
        print("      → Gmail → Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP")
        return False
    except Exception as e:
        print(f"\n❌ Failed to send email: {e}")
        return False
