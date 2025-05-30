import re
from models.contact import Contact
from datetime import datetime
import phonenumbers
from utils import ContactExtractor
import email as email_lib
import yaml


with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
contact_extractor = ContactExtractor('config.yaml')

def extract_contact(uid, msg):
    scrapped_date = datetime.now()
    contact_info = contact_extractor.extract_contact_info(msg, scrapped_date)
    if not contact_info:
        return None
    name = contact_info.get('name', '')
    email_addr = contact_info.get('email', '')
    phone = contact_info.get('phone_number', '')
    company_name = '' 
    website = ''       
    priority = ''
    notes = ''
    source = contact_info.get('source', 'email')
    extracted_date = scrapped_date
    notes_parts = []
    if contact_info.get('linkedin_url'):
        notes_parts.append(f"LinkedIn: {contact_info['linkedin_url']}")
    if contact_info.get('role'):
        notes_parts.append(f"Role: {contact_info['role']}")
    if notes_parts:
        notes = ' | '.join(notes_parts)
    return Contact(name, email_addr, phone, source, extracted_date, company_name, website, priority, notes, uid)