from dataclasses import dataclass
from datetime import datetime

@dataclass
class Contact:
    name: str
    email: str
    phone: str
    source: str
    extracted_date: datetime
    company_name: str
    website: str
    priority: str
    notes: str
    email_uid: str  