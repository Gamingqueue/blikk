import imaplib
import email
from email.header import decode_header

# Configuration — replace these with your actual info
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = 'gaming.queue123@gmail.com'
EMAIL_PASSWORD = 'qedv ienj pmmg nhyc'# Use App Password from Google if 2FA is enabled

def get_latest_netflix_code():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")

        # Search for emails from Netflix (broad search to ensure it matches)
        status, messages = mail.search(None, 'FROM "netflix"')
        if status != "OK":
            return "Error searching mailbox."

        message_ids = messages[0].split()
        if not message_ids:
            return "No Netflix emails found."

        latest_email_id = message_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        if status != "OK":
            return "Failed to fetch email."

        msg = email.message_from_bytes(msg_data[0][1])

        # Optional debug info: print subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")
        print("Email Subject:", subject)

        # Get the email content
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                body = part.get_payload(decode=True).decode(errors="ignore")
                return body.strip()

            elif content_type == "text/html" and "attachment" not in content_disposition:
                body = part.get_payload(decode=True).decode(errors="ignore")
                return body.strip()

        return "Could not find message body."
    except Exception as e:
        return f"Error: {str(e)}"
