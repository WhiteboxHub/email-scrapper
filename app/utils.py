import email
import re
import phonenumbers

class EmailParser:

    @staticmethod
    def extract_contact_info(msg):
        contact = {
            'name': '',
            'email': '',
            'phone': '',
            'fax': '',
            'landline': '',
        }

        # Extract sender name and email
        from_header = msg.get('From', '')
        match = email.utils.parseaddr(from_header)
        contact['name'] = match[0]
        contact['email'] = match[1]

        # Get the body of the email
        body = EmailParser.get_body(msg)

        # Normalize text
        text = body.replace('\r', '').replace('\n', ' ').lower()

        # Extract phone numbers using phonenumbers
        numbers = phonenumbers.PhoneNumberMatcher(text, "US")  # or 'IN', depending on your region
        for num in numbers:
            raw = num.raw_string
            if 'fax' in text[num.start:num.end + 20]:
                contact['fax'] = raw
            elif 'landline' in text[num.start:num.end + 20] or 'land' in text[num.start:num.end + 20]:
                contact['landline'] = raw
            else:
                contact['phone'] = raw

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
