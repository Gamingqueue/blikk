import imaplib
import email
import os
from email.header import decode_header
import re

class EmailCodeReader:
    def __init__(self):
        # Netflix email configuration
        self.netflix_config = {
            "IMAP_SERVER": os.getenv("IMAP_SERVER", "imap.gmail.com"),
            "EMAIL_ACCOUNT": os.getenv("EMAIL_ACCOUNT", "gaming.queue123@gmail.com"),
            "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", "qedv ienj pmmg nhyc"),
        }
        
        # ChatGPT email configurations (multiple accounts)
        self.chatgpt_accounts = [
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
        
        # ChatGPT verification phrases
        self.chatgpt_verification_phrases = [
            "please use the following code to help verify your identity",
            "we noticed a suspicious log-in on your account",
            "enter this code to verify it's you",
        ]

    def get_latest_netflix_code(self):
        """
        Fetches the latest Netflix verification code from the inbox.
        Returns the 4-digit code or an error message.
        """
        try:
            # Connect to the mail server
            mail = imaplib.IMAP4_SSL(self.netflix_config["IMAP_SERVER"])
            mail.login(self.netflix_config["EMAIL_ACCOUNT"], self.netflix_config["EMAIL_PASSWORD"])
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
            print(f"Netflix email reading error: {str(e)}")
            return f"Error: {str(e)}"
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass

    def extract_chatgpt_code_from_text(self, text):
        """Extract 6-digit code from email text if it contains verification phrases"""
        lower_text = text.lower()
        if any(phrase in lower_text for phrase in self.chatgpt_verification_phrases):
            match = re.search(r"\b\d{6}\b", text)
            if match:
                return match.group(0)
        return None

    def check_chatgpt_account_for_code(self, account):
        """Check a specific email account for ChatGPT verification codes"""
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

                            code = self.extract_chatgpt_code_from_text(body)
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

    def get_latest_chatgpt_code(self):
        """
        Fetches the latest ChatGPT verification code from configured email accounts.
        Returns the 6-digit code or None if not found.
        """
        for account in self.chatgpt_accounts:
            code = self.check_chatgpt_account_for_code(account)
            if code:
                return code
        return None

# Global instance
email_reader = EmailCodeReader()

# Convenience functions for backward compatibility
def get_latest_netflix_code():
    return email_reader.get_latest_netflix_code()

def get_latest_chatgpt_code():
    return email_reader.get_latest_chatgpt_code()
