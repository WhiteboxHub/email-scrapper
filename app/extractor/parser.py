import re
from models.contact import Contact
from datetime import datetime

def extract_contact(uid, msg):
    # Extract email
    from_email = re.findall(r'<(.+?)>', msg.get('From', ''))
    email_addr = from_email[0] if from_email else msg.get('From', '')
    # Extract name
    name = msg.get('From', '').split('<')[0].strip().replace('"', '')
    # Extract phone (simple regex)
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(errors='ignore')
    else:
        body = msg.get_payload(decode=True).decode(errors='ignore')
    phone = re.search(r'(\+?\d[\d\-\(\) ]{7,}\d)', body)
    phone = phone.group(0) if phone else ""
    # Company, website, priority, notes (stubbed, can be improved)
    company_name = ""
    website = ""
    priority = ""
    notes = ""
    # Source
    source = "email"
    extracted_date = datetime.now()
    return Contact(name, email_addr, phone, source, extracted_date, company_name, website, priority, notes, uid)