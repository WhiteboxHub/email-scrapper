import imaplib
import email
import mysql.connector
import logging
import os
import time
from dotenv import load_dotenv
from utils import EmailParser

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class EmailScraper:
    def __init__(self):
        self.imap_host = os.getenv("IMAP_SERVER")
        self.imap_user = os.getenv("EMAIL")
        self.imap_password = os.getenv("PASSWORD")
        self.mail = None
        self.db_conn = None
        self.db_cursor = None
        self.rate_limit_seconds = 1.0  

    def connect_imap(self):
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_host)
            self.mail.login(self.imap_user, self.imap_password)
            self.mail.select("inbox")
            logging.info("Connected to IMAP server.")
            return True
        except Exception as e:
            logging.error(f"IMAP connection failed: {e}")
            return False

    def connect_db(self):
        try:
            self.db_conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                auth_plugin='mysql_native_password'
            )
            self.db_cursor = self.db_conn.cursor()
            logging.info("Connected to MySQL database.")
            return True
        except Exception as e:
            logging.error(f"DB connection failed: {e}")
            return False

    def is_email_processed(self, email):
        self.db_cursor.execute("SELECT 1 FROM contacts WHERE email = %s", (email,))
        return self.db_cursor.fetchone() is not None

    def save_contact(self, contact):
        try:
            self.db_cursor.execute(
                """
                INSERT INTO contacts (name, email, phone, fax, landline, role, linkedin_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    contact.get('name'),
                    contact.get('email'),
                    contact.get('phone'),
                    contact.get('fax'),
                    contact.get('landline'),
                    contact.get('role'),
                    contact.get('linkedin_url'),
                ),
            )
            self.db_conn.commit()
            logging.info(f"Saved contact: {contact.get('email')} with role: {contact.get('role')}")
        except mysql.connector.errors.IntegrityError:
            logging.info(f"Duplicate contact not inserted: {contact.get('email')}")
        except Exception as e:
            logging.error(f"Error saving contact to DB: {e}")

    def fetch_emails(self):
        contacts = []
        try:
            result, data = self.mail.search(None, 'ALL')
            if result != 'OK':
                logging.error("Failed to search inbox.")
                return []

            email_ids = data[0].split()
            logging.info(f"Found {len(email_ids)} emails in inbox.")

        except Exception as e:
            logging.error(f"Error fetching emails: {e}")
            return []

        for email_id in email_ids:
            try:
                res, msg_data = self.mail.fetch(email_id, "(RFC822)")
                if res != 'OK':
                    logging.warning(f"Failed to fetch email id {email_id}")
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                contact = EmailParser.extract_contact_info(msg)
                if not contact:
                    logging.info(f"Skipped non-recruiter/vendor or non-job email.")
                    continue

                # Uniqueness: skip if email already processed
                if self.is_email_processed(contact['email']):
                    logging.info(f"Skipping already processed contact: {contact['email']}")
                    continue

                self.save_contact(contact)
                contacts.append(contact)
                time.sleep(self.rate_limit_seconds)

            except Exception as e:
                logging.error(f"Error processing email {email_id}: {e}")

        return contacts

    def close(self):
        if self.mail:
            try:
                self.mail.logout()
            except Exception:
                pass
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_conn:
            self.db_conn.close()

def main():
    scraper = EmailScraper()

    if not scraper.connect_db():
        print("Failed to connect to MySQL. Exiting.")
        return

    if not scraper.connect_imap():
        print("Failed to connect to IMAP. Exiting.")
        return

    print("Fetching and processing recruiter/vendor emails for contacts...")
    contacts = scraper.fetch_emails()
    print(f"Processed {len(contacts)} new recruiter/vendor contacts.")
    scraper.close()

if __name__ == "__main__":
    main()