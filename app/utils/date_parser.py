from datetime import datetime
from dateutil import parser
from typing import Optional

def parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats to MM/YYYY"""
    if not date_str or date_str.lower() == 'present':
        return "Present"
    
    try:
        # Try common date formats
        date_formats = [
            "%m/%Y", "%Y-%m", "%b %Y", "%B %Y", "%m-%Y", "%Y/%m",
            "%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%m/%Y")
            except ValueError:
                continue
        
        # Try dateutil as fallback
        dt = parser.parse(date_str)
        return dt.strftime("%m/%Y")
    except:
        return date_str  # Return original if parsing fails