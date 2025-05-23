import email
import re
import phonenumbers

class EmailParser:
    # Expandable keyword sets
    JOB_KEYWORDS = {
        'job', 'position', 'opening', 'requirement', 'resume',
        'interview', 'candidate', 'opportunity', 'hiring',
        'c2c', 'w2', 'corp to corp', 'contract role', 'full-time',
        'consultant', 'profile', 'submission', 'placement', 'resource'
    }

    ROLE_KEYWORDS = {
        'recruiter', 'talent acquisition', 'account manager', 'hr', 'staffing',
        'vendor', 'client', 'consultant', 'business development', 'sales',
        'talent', 'sourcing', 'delivery manager', 'resource manager'
    }

    LINKEDIN_REGEX = re.compile(
        r'(https?://(?:[a-z]{2,3}\.)?linkedin\.com/[^\s\'"<>]+)', re.IGNORECASE
    )

    @staticmethod
    def extract_contact_info(msg):
        contact = {
            'name': '',
            'email': '',
            'phone': '',
            'fax': '',
            'landline': '',
            'role': '',
            'linkedin_url': ''
        }

        from_header = msg.get('From', '')
        name, sender_email = email.utils.parseaddr(from_header)
        if not sender_email:
            return None

        # Extract body text
        body = EmailParser.get_body(msg)
        if not body:
            return None

        text = body.replace('\r', '').replace('\n', ' ').lower()

        # Check for job-related keywords
        is_job_related = any(keyword in text for keyword in EmailParser.JOB_KEYWORDS)

        # Check for role-related keywords in body or signature
        role_detected = next((keyword for keyword in EmailParser.ROLE_KEYWORDS if keyword in text), None)

        # Try to extract role from signature if not found in body
        if not role_detected:
            signature = EmailParser.extract_signature(body)
            role_detected = next((keyword for keyword in EmailParser.ROLE_KEYWORDS if keyword in signature.lower()), None)

        # Fallback: If job-related, but no explicit role, set role as 'unknown'
        if is_job_related and not role_detected:
            role_detected = 'unknown'

        # Only process if job-related and some role detected
        if not (is_job_related and role_detected):
            return None

        contact['name'] = name
        contact['email'] = sender_email
        contact['role'] = role_detected

        # Extract phone numbers
        numbers = phonenumbers.PhoneNumberMatcher(text, "US")
        for num in numbers:
            raw = num.raw_string
            context = text[num.start:num.end + 20]
            if 'fax' in context:
                contact['fax'] = raw
            elif 'landline' in context or 'land' in context:
                contact['landline'] = raw
            else:
                contact['phone'] = raw

        # Extract LinkedIn URL (prefer one with sender's name if possible)
        linkedin_urls = EmailParser.LINKEDIN_REGEX.findall(body)
        if linkedin_urls:
            name_parts = [p.lower() for p in name.split() if p]
            best_url = None
            for url in linkedin_urls:
                if any(part in url.lower() for part in name_parts):
                    best_url = url
                    break
            contact['linkedin_url'] = best_url or linkedin_urls[0]

        return contact

    @staticmethod
    def get_body(msg):
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    return part.get_payload(decode=True).decode(errors='ignore')
        else:
            return msg.get_payload(decode=True).decode(errors='ignore')
        return ''

    @staticmethod
    def extract_signature(body):
        # Heuristic: last 10 lines of the email
        lines = body.strip().split('\n')
        return '\n'.join(lines[-10:])