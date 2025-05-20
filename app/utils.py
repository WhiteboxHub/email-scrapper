import re
from email.header import decode_header
from email.message import Message 
from typing import Dict, List, Tuple
import phonenumbers


class EmailParser:
    @staticmethod
    def parse_sender(sender: str) -> Tuple[str, str]:
        """Extract name and email from sender string"""
        decoded = decode_header(sender)[0]
        if isinstance(decoded[0], bytes):
            sender_str = decoded[0].decode(decoded[1] or 'utf-8')
        else:
            sender_str = decoded[0]
        
        # Extract name and email
        name_match = re.match(r'(.*?)<.*?>', sender_str)
        if name_match:
            name = name_match.group(1).strip(' "\'')
            email_match = re.search(r'<(.+?)>', sender_str)
            email = email_match.group(1) if email_match else ''
        else:
            name = ''
            email = sender_str.strip(' "\'')
        
        return name, email

    @staticmethod
    def get_email_body(email_message: Message) -> str:
        """Extract plain text body from email"""
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
        return body

    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers from text with enhanced US and India support"""
        # Common patterns for US numbers
        # 123-456-7890 or 123.456.7890 or 1234567890
        # (123) 456-7890
        # 123 456 7890
        # 1234567890
        us_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  
            r'\b\d{3}\s\d{3}\s\d{4}\b',       
            r'\b\d{10}\b'                      
        ]
        
        # Common patterns for Indian numbers
        # 10 digits starting with 6-9
        # +91 12345 67890
        # 01234567890 (with leading 0)
        # 12345-67890 or 12345 67890
        india_patterns = [
            r'\b[6789]\d{9}\b',               
            r'\b\+91[- ]?\d{5}[- ]?\d{5}\b',   
            r'\b0[6789]\d{9}\b',              
            r'\b\d{5}[- ]?\d{5}\b'            
        ]
        
        # International format patterns
        international_patterns = [
            r'\b\+\d{1,3}[- ]?\d{1,4}[- ]?\d{3,4}[- ]?\d{3,4}\b',
            r'\b\d{2,4}[- ]?\d{3,4}[- ]?\d{3,4}\b'
        ]
        
        # Combine all patterns
        all_patterns = us_patterns + india_patterns + international_patterns
        
        found_numbers = set() 
        
        # First pass with regex patterns
        for pattern in all_patterns:
            found_numbers.update(re.findall(pattern, text))
        
        # Second pass with phonenumbers library for more sophisticated parsing
        try:
            for match in phonenumbers.PhoneNumberMatcher(text, None):
                num = phonenumbers.format_number(
                    match.number,
                    phonenumbers.PhoneNumberFormat.E164
                )
                found_numbers.add(num)
        except:
            pass
        
        # Clean and format numbers
        formatted_numbers = []
        for num in found_numbers:
            # Remove all non-digit characters except leading +
            cleaned = re.sub(r'(?!^\+)[^\d]', '', num)
            
            # Special handling for India numbers
            if cleaned.startswith('91') and len(cleaned) == 12:
                cleaned = '+' + cleaned  
            elif cleaned.startswith('0') and len(cleaned) == 11:
                cleaned = '+91' + cleaned[1:]  
            
            formatted_numbers.append(cleaned)
        
        return sorted(list(set(formatted_numbers))) 

    @classmethod
    def extract_contact_info(cls, email_message: Message) -> Dict[str, str]: 
        """Extract contact info from email message"""
        contact_info = {
            'name': '',
            'phone': '',
            'email': ''
        }
        
        # Extract sender information
        sender = email_message.get('From', '')
        name, email_address = cls.parse_sender(sender)
        contact_info['name'] = name
        contact_info['email'] = email_address
        
        # Extract phone numbers from email body
        body = cls.get_email_body(email_message)
        phone_numbers = cls.extract_phone_numbers(body)
        if phone_numbers:
            contact_info['phone'] = ', '.join(phone_numbers)
        
        return contact_info