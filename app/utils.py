# import email
# import re
# import phonenumbers
# from datetime import datetime
# from email.header import decode_header

# import csv
# import os

# class ContactExtractor:
#     """
#     Automation utility to extract contact info from emails.
#     Extracts: name, email, linkedin_url, phone_number, scrapped_date, role, source.
#     """

#     # Regex for LinkedIn URLs
#     LINKEDIN_REGEX = re.compile(
#         r'(https?://(?:[a-z]{2,3}\.)?linkedin\.com/[^\s\'"<>]+)', re.IGNORECASE
#     )
#     # Regex for Dice URLs
#     DICE_REGEX = re.compile(
#         r'(https?://(?:[a-z]{2,3}\.)?dice\.com/[^\s\'"<>]+)', re.IGNORECASE
#     )
#     # Regex for Naukri URLs
#     NAUKRI_REGEX = re.compile(
#         r'(https?://(?:[a-z]{2,3}\.)?naukri\.com/[^\s\'"<>]+)', re.IGNORECASE
#     )
#     # Regex for Indeed URLs
#     INDEED_REGEX = re.compile(
#         r'(https?://(?:[a-z]{2,3}\.)?indeed\.com/[^\s\'"<>]+)', re.IGNORECASE
#     )

#     # Regex for phone numbers (fallback if phonenumbers fails)
#     SIMPLE_PHONE_REGEX = re.compile(
#         r'(\+?\d[\d\-\(\) ]{7,}\d)'
#     )

#     @staticmethod
#     def decode_header_value(header_val):
#         """Decode email headers to unicode."""
#         if not header_val:
#             return ""
#         decoded_parts = decode_header(header_val)
#         return ' '.join([
#             part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
#             for part, encoding in decoded_parts
#         ])

#     @staticmethod
#     def extract_contact_info(msg, scrapped_date, source=None):
#         """
#         Extracts contact info from an email.message.Message object.
#         Returns a dict with all required fields.
#         If source is not provided, it will be detected heuristically.
#         """
#         # Extract sender name and email
#         from_header = msg.get('From', '')
#         name, sender_email = email.utils.parseaddr(from_header)
#         name = ContactExtractor.decode_header_value(name)
#         sender_email = sender_email.strip()

#         # Extract body text
#         body = ContactExtractor.get_body(msg)
#         if not body:
#             return None

#         # Lowercase for easier searching
#         text = body.replace('\r', '').replace('\n', ' ').lower()

#         # Extract LinkedIn URL from signature or body
#         signature = ContactExtractor.extract_signature(body)
#         linkedin_urls = ContactExtractor.LINKEDIN_REGEX.findall(signature)
#         if not linkedin_urls:
#             linkedin_urls = ContactExtractor.LINKEDIN_REGEX.findall(body)
#         linkedin_url = linkedin_urls[0] if linkedin_urls else ""

#         # Extract phone number (prefer phonenumbers, fallback to regex)
#         phone = ""
#         try:
#             numbers = list(phonenumbers.PhoneNumberMatcher(body, "US"))
#             if numbers:
#                 phone = phonenumbers.format_number(numbers[0].number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
#         except Exception:
#             pass
#         if not phone:
#             match = ContactExtractor.SIMPLE_PHONE_REGEX.search(body)
#             if match:
#                 phone = match.group(1)

#         # Try to extract role from signature or body (simple heuristics)
#         role = ContactExtractor.extract_role(signature) or ContactExtractor.extract_role(body)

#         # Heuristically detect source if not provided
#         detected_source = source or ContactExtractor.detect_source_from_body(body)

#         # Compose contact dict
#         contact = {
#             'name': name,
#             'email': sender_email,
#             'linkedin_url': linkedin_url,
#             'phone_number': phone,
#             'scrapped_date': scrapped_date,
#             'role': role,
#             'source': detected_source
#         }
#         # Only return if at least name and email are present
#         if not sender_email:
#             return None
#         return contact

#     @staticmethod
#     def detect_source_from_body(body):
#         """
#         Heuristically detect the source of the contact from the email body.
#         Looks for known portal URLs, otherwise returns 'Email' or 'Unknown'.
#         """
#         if not body:
#             return "Unknown"
#         body_lower = body.lower()
#         if "linkedin.com" in body_lower or ContactExtractor.LINKEDIN_REGEX.search(body):
#             return "LinkedIn"
#         if "dice.com" in body_lower or ContactExtractor.DICE_REGEX.search(body):
#             return "Dice"
#         if "naukri.com" in body_lower or ContactExtractor.NAUKRI_REGEX.search(body):
#             return "Naukri"
#         if "indeed.com" in body_lower or ContactExtractor.INDEED_REGEX.search(body):
#             return "Indeed"
#         # Add more heuristics for other portals as needed
#         # If the sender's email domain is a known company, use that
#         match = re.search(r'@([a-zA-Z0-9\-\.]+)', body_lower)
#         if match:
#             domain = match.group(1)
#             if any(portal in domain for portal in ['monster', 'glassdoor', 'ziprecruiter', 'workday']):
#                 return domain.split('.')[0].capitalize()
#         # Fallback: if the body contains "resume", "cv", "profile", etc.
#         for kw, label in [
#             ("resume", "Resume"),
#             ("cv", "CV"),
#             ("profile", "Profile"),
#             ("application", "Application"),
#             ("job", "Job Board"),
#         ]:
#             if kw in body_lower:
#                 return label
#         # Default fallback
#         return "Email"

#     @staticmethod
#     def extract_role(text):
#         """
#         Heuristic: Look for lines with 'Role:', 'Title:', or common role words.
#         """
#         if not text:
#             return ""
#         lines = text.split('\n')
#         for line in lines:
#             l = line.lower()
#             if 'role:' in l or 'title:' in l:
#                 return line.split(':', 1)[-1].strip()
#             # Common role keywords
#             for kw in [
#                 'recruiter', 'talent acquisition', 'account manager', 'hr', 'staffing',
#                 'vendor', 'client', 'consultant', 'sourcing', 'delivery manager', 'resource manager',
#                 'business development', 'sales', 'technical lead', 'project manager', 'director', 'founder'
#             ]:
#                 if kw in l:
#                     return kw
#         return ""

#     @staticmethod
#     def get_body(msg):
#         """
#         Extracts the plain text body from an email message.
#         """
#         if msg.is_multipart():
#             for part in msg.walk():
#                 content_type = part.get_content_type()
#                 content_disposition = str(part.get("Content-Disposition"))
#                 if content_type == 'text/plain' and 'attachment' not in content_disposition:
#                     try:
#                         return part.get_payload(decode=True).decode(errors='ignore')
#                     except Exception:
#                         continue
#         else:
#             try:
#                 return msg.get_payload(decode=True).decode(errors='ignore')
#             except Exception:
#                 return ""
#         return ""

#     @staticmethod
#     def extract_signature(body):
#         """
#         Heuristic: last 10 lines of the email as signature.
#         """
#         lines = body.strip().split('\n')
#         return '\n'.join(lines[-10:])

#     @staticmethod
#     def write_contacts_to_csv(contacts, output_dir="output"):
#         """
#         Writes a list of contact dicts to a CSV file with today's date.
#         """
#         if not contacts:
#             return None
#         os.makedirs(output_dir, exist_ok=True)
#         today = datetime.now().strftime("%Y-%m-%d")
#         filename = os.path.join(output_dir, f"contacts_{today}.csv")
#         fieldnames = ['name', 'email', 'linkedin_url', 'phone_number', 'scrapped_date', 'role', 'source']
#         write_header = not os.path.exists(filename)
#         with open(filename, "a", newline='', encoding='utf-8') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#             if write_header:
#                 writer.writeheader()
#             for contact in contacts:
#                 writer.writerow(contact)
#         return filename

# # NOTE:
# # The logic for "scrap all emails not previously scrapped, starting from the last scrapped date"
# # should be handled in your main scraping logic, not here.
# # This utility is stateless and only processes/extracts info from a given email/message.

# # Example table schema for storing contacts (for MySQL or SQLite):
# """
# CREATE TABLE contacts (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     name VARCHAR(255),
#     email VARCHAR(255) NOT NULL,
#     linkedin_url VARCHAR(512),
#     phone_number VARCHAR(64),
#     scrapped_date DATE NOT NULL,
#     role VARCHAR(128),
#     source VARCHAR(128),
#     UNIQUE(email, scrapped_date)
# );
# """

# # Example usage (to be placed in your main scraping logic):
# #
# # from datetime import datetime, timedelta
# # # ... connect to IMAP and DB ...
# # # Get last scrapped date from DB (or None if never scrapped)
# # last_scrapped_date = get_last_scrapped_date_from_db()
# # if last_scrapped_date:
# #     # Start from the day after last scrapped date
# #     start_date = last_scrapped_date + timedelta(days=1)
# # else:
# #     # If never scrapped, start from 30 days ago (or as needed)
# #     start_date = datetime.now() - timedelta(days=30)
# # # Fetch all emails since start_date (inclusive)
# # email_ids = fetch_email_ids_since(start_date)
# # contacts = []
# # for email_id in email_ids:
# #     res, msg_data = mail.fetch(email_id, "(RFC822)")
# #     if res != 'OK':
# #         continue
# #     msg = email.message_from_bytes(msg_data[0][1])
# #     # Extract the date of the email
# #     msg_date = msg.get('Date')
# #     try:
# #         msg_datetime = email.utils.parsedate_to_datetime(msg_date)
# #         scrapped_date = msg_datetime.strftime("%Y-%m-%d")
# #     except Exception:
# #         scrapped_date = datetime.now().strftime("%Y-%m-%d")
# #     contact = ContactExtractor.extract_contact_info(
# #         msg,
# #         scrapped_date=scrapped_date
# #     )
# #     if contact:
# #         contacts.append(contact)
# # ContactExtractor.write_contacts_to_csv(contacts)




# new

import email
import re
import phonenumbers
from datetime import datetime
from email.header import decode_header
import csv
import os
import yaml

class ContactExtractor:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.role_keywords = self.config["role_keywords"]
        self.portal_domains = self.config["portal_domains"]
        self.linkedin_regex = re.compile(self.config["linkedin_regex"], re.IGNORECASE)
        self.dice_regex = re.compile(self.config["dice_regex"], re.IGNORECASE)
        self.naukri_regex = re.compile(self.config["naukri_regex"], re.IGNORECASE)
        self.indeed_regex = re.compile(self.config["indeed_regex"], re.IGNORECASE)
        self.simple_phone_regex = re.compile(self.config["simple_phone_regex"])

    @staticmethod
    def decode_header_value(header_val):
        if not header_val:
            return ""
        decoded_parts = decode_header(header_val)
        return ' '.join([
            part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
            for part, encoding in decoded_parts
        ])

    def extract_contact_info(self, msg, scrapped_date, source=None):
        from_header = msg.get('From', '')
        name, sender_email = email.utils.parseaddr(from_header)
        name = self.decode_header_value(name)
        sender_email = sender_email.strip()
        body = self.get_body(msg)
        if not body:
            return None
        text = body.replace('\r', '').replace('\n', ' ').lower()
        signature = self.extract_signature(body)
        linkedin_urls = self.linkedin_regex.findall(signature) or self.linkedin_regex.findall(body)
        linkedin_url = linkedin_urls[0] if linkedin_urls else ""
        phone = ""
        try:
            numbers = list(phonenumbers.PhoneNumberMatcher(body, "US"))
            if numbers:
                phone = phonenumbers.format_number(numbers[0].number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except Exception:
            pass
        if not phone:
            match = self.simple_phone_regex.search(body)
            if match:
                phone = match.group(1)
        role = self.extract_role(signature) or self.extract_role(body)
        detected_source = source or self.detect_source_from_body(body)
        contact = {
            'name': name,
            'email': sender_email,
            'linkedin_url': linkedin_url,
            'phone_number': phone,
            'scrapped_date': scrapped_date,
            'role': role,
            'source': detected_source
        }
        if not sender_email:
            return None
        # Only return if this is a vendor/recruiter/client (not a candidate)
        if not self.is_vendor_recruiter_client(contact):
            return None
        return contact

    def is_vendor_recruiter_client(self, contact):
        # Check role or source for recruiter/vendor/client keywords
        role = (contact.get("role") or "").lower()
        source = (contact.get("source") or "").lower()
        email_addr = (contact.get("email") or "").lower()
        # Check role keywords
        if any(kw in role for kw in self.role_keywords):
            return True
        # Check source
        if any(portal.lower() in source for portal in self.portal_domains.values()):
            return True
        # Check email domain
        for domain in self.portal_domains:
            if domain in email_addr:
                return True
        return False

    def detect_source_from_body(self, body):
        if not body:
            return "Unknown"
        body_lower = body.lower()
        for domain, label in self.portal_domains.items():
            if domain in body_lower:
                return label
            regex = getattr(self, f"{label.lower()}_regex", None)
            if regex and regex.search(body):
                return label
        return "Email"

    def extract_role(self, text):
        if not text:
            return ""
        lines = text.split('\n')
        for line in lines:
            l = line.lower()
            if 'role:' in l or 'title:' in l:
                return line.split(':', 1)[-1].strip()
            for kw in self.role_keywords:
                if kw in l:
                    return kw
        return ""

    @staticmethod
    def get_body(msg):
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == 'text/plain' and 'attachment' not in content_disposition:
                    try:
                        return part.get_payload(decode=True).decode(errors='ignore')
                    except Exception:
                        continue
        else:
            try:
                return msg.get_payload(decode=True).decode(errors='ignore')
            except Exception:
                return ""
        return ""

    @staticmethod
    def extract_signature(body):
        lines = body.strip().split('\n')
        return '\n'.join(lines[-10:])

    @staticmethod
    def write_contacts_to_csv(contacts, output_dir="output"):
        if not contacts:
            return None
        os.makedirs(output_dir, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(output_dir, f"contacts_{today}.csv")
        fieldnames = ['name', 'email', 'linkedin_url', 'phone_number', 'scrapped_date', 'role', 'source']
        write_header = not os.path.exists(filename)
        with open(filename, "a", newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            for contact in contacts:
                writer.writerow(contact)
        return filename