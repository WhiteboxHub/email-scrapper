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
        if not self.is_vendor_recruiter_client(contact):
            return None
        return contact

    def is_vendor_recruiter_client(self, contact):
        role = (contact.get("role") or "").lower()
        source = (contact.get("source") or "").lower()
        email_addr = (contact.get("email") or "").lower()
        if any(kw in role for kw in self.role_keywords):
            return True
        if any(portal.lower() in source for portal in self.portal_domains.values()):
            return True
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