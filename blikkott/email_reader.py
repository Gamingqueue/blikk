import imaplib
import email
import os
from email.header import decode_header
import re

# Configuration — use environment variables with fallbacks
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT", "gaming.queue123@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "qedv ienj pmmg nhyc")  # Use App Password from Google if 2FA is enabled

def get_latest_netflix_code():
    """
    Fetches the latest Netflix verification code from the inbox.
    Returns the 4-digit code or an error message.
    """
    try:
        # Connect to the mail server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")

        # Search for emails from Netflix
        status, messages = mail.search(None, 'FROM "netflix"')
        if status != "OK":
            return "Error searching mailbox."

        message_ids = messages[0].split()
        if not message_ids:
            return "No Netflix emails found."

        # Get the latest email
        latest_email_id = message_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        if status != "OK":
            return "Failed to fetch email."

        msg = email.message_from_bytes(msg_data[0][1])

        # Get the email content
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type in ["text/plain", "text/html"] and "attachment" not in content_disposition:
                body = part.get_payload(decode=True).decode(errors="ignore")

                # Find a 4-digit number (commonly used for verification codes)
                match = re.search(r"\b\d{4}\b", body)
                if match:
                    return match.group(0)
                else:
                    return "No 4-digit code found in the email."

        return "Could not find message body."

    except Exception as e:
        print(f"Email reading error: {str(e)}")
        return f"Error: {str(e)}"
    finally:
        try:
            mail.close()
            mail.logout()
        except:
            pass
