import re
import phonenumbers
from email_validator import validate_email, EmailNotValidError

def validate_email_address(email: str) -> bool:
    """Validate email format"""
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    try:
        parsed = phonenumbers.parse(phone, None)
        return phonenumbers.is_valid_number(parsed)
    except:
        return False

def extract_phone_numbers(text: str) -> list:
    """Extract phone numbers from text"""
    phone_patterns = [
        r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\b\d{10}\b',
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    ]
    
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                match = ''.join(match)
            phones.append(match)
    
    return phones