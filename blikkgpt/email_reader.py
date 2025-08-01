import imaplib
import email
from email.header import decode_header
import re
import os

# Email account configurations
ACCOUNTS = [
    {
        "label": "Gmail",
        "IMAP_SERVER": "imap.gmail.com",
        "IMAP_PORT": 993,
        "EMAIL_ACCOUNT": os.getenv("EMAIL_ACCOUNT", "gaming.queue123@gmail.com"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", "qedv ienj pmmg nhyc"),
    },
    {
        "label": "Hostinger",
        "IMAP_SERVER": "imap.hostinger.com",
        "IMAP_PORT": 993,
        "EMAIL_ACCOUNT": "contact@conexzo.com",
        "EMAIL_PASSWORD": "Blikk@123444",
    },
]

# Define keywords that must be in the email for code extraction
VERIFICATION_PHRASES = [
    "please use the following code to help verify your identity",
    "we noticed a suspicious log-in on your account",
    "enter this code to verify it's you",
]

def extract_code_from_text(text):
    lower_text = text.lower()
    if any(phrase in lower_text for phrase in VERIFICATION_PHRASES):
        match = re.search(r"\b\d{6}\b", text)
        if match:
            return match.group(0)
    return None

def check_account_for_code(account):
    try:
        mail = imaplib.IMAP4_SSL(account["IMAP_SERVER"], account["IMAP_PORT"])
        mail.login(account["EMAIL_ACCOUNT"], account["EMAIL_PASSWORD"])
        
        folders = ["inbox", "[Gmail]/Spam", "Junk"] if account["label"] == "Gmail" else ["inbox", "Spam", "Junk"]
        for folder in folders:
            try:
                mail.select(folder, readonly=False)
                status, messages = mail.search(None, '(UNSEEN FROM "openai.com")')
                if status != "OK":
                    print(f"[{account['label']}] Failed to search emails in {folder}.")
                    continue

                email_ids = messages[0].split()
                if not email_ids:
                    print(f"[{account['label']}] No unread emails found in {folder}.")
                    continue

                latest_email_id = email_ids[-1]
                res, msg_data = mail.fetch(latest_email_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        subject = subject.decode(encoding or "utf-8") if isinstance(subject, bytes) else subject
                        print(f"[{account['label']}] Processing email with subject: {subject}")

                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode(errors="ignore")

                        # Fallback to HTML if plain not found
                        if not body.strip():
                            for part in msg.walk():
                                if part.get_content_type() == "text/html":
                                    html_body = part.get_payload(decode=True).decode(errors="ignore")
                                    body = re.sub('<[^<]+?>', ' ', html_body)
                                    break

                        code = extract_code_from_text(body)
                        if code:
                            print(f"[{account['label']}] Verification code found: {code}")
                            mail.store(latest_email_id, '+FLAGS', '\\Seen')
                            mail.logout()
                            return code
                        else:
                            print(f"[{account['label']}] No valid code found in: {body[:300]}...")

                mail.store(latest_email_id, '+FLAGS', '\\Seen')

            except Exception as e:
                print(f"[{account['label']}] Could not access folder {folder}: {e}")
                continue

        mail.logout()
        return None

    except Exception as e:
        print(f"[{account['label']}] Error: {e}")
        return None

def get_latest_chatgpt_code():
    for account in ACCOUNTS:
        code = check_account_for_code(account)
        if code:
            return code
    return None

if __name__ == "__main__":
    code = get_latest_chatgpt_code()
    if code:
        print(f"Verification code: {code}")
    else:
        print("No verification code found in Gmail or Hostinger.")
