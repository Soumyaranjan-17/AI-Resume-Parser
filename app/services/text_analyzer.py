import spacy
import re
from typing import List, Tuple, Dict, Any
from datetime import datetime
from app.utils.validators import validate_email_address, extract_phone_numbers
from app.config import settings

class TextAnalyzer:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp = None
        self.skill_patterns = self._build_skill_patterns()
    
    def _build_skill_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for skill extraction"""
        patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'url': re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'),
            'linkedin': re.compile(r'linkedin\.com/in/[\w-]+'),
            'github': re.compile(r'github\.com/[\w-]+'),
        }
        return patterns
    
    def extract_personal_info(self, text: str) -> Tuple[Dict[str, Any], float]:
        """Extract personal information with confidence score"""
        personal_info = {
            "first_name": "", "last_name": "", "full_name": "",
            "email": "", "phone": "", "location": "",
            "linkedin": "", "github": "", "portfolio": ""
        }
        confidence_factors = []
        
        try:
            # Extract email
            emails = self.skill_patterns['email'].findall(text)
            if emails:
                personal_info['email'] = emails[0]
                confidence_factors.append(0.3)
            
            # Extract phone numbers - improved pattern
            phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
            phones = phone_pattern.findall(text)
            if phones:
                # Take the first phone number that has proper length
                for phone in phones:
                    if isinstance(phone, tuple):
                        phone = ''.join(phone)
                    phone_clean = re.sub(r'[^\d+]', '', phone)
                    if len(phone_clean) >= 10:
                        personal_info['phone'] = phone
                        confidence_factors.append(0.2)
                        break
            
            # Extract URLs and social links
            urls = self.skill_patterns['url'].findall(text)
            linkedin_links = self.skill_patterns['linkedin'].findall(text)
            github_links = self.skill_patterns['github'].findall(text)
            
            if linkedin_links:
                personal_info['linkedin'] = f"https://{linkedin_links[0]}"
            if github_links:
                personal_info['github'] = f"https://{github_links[0]}"
            
            # Extract portfolio (other URLs that aren't social media)
            other_urls = [url for url in urls if not any(domain in url for domain in ['linkedin', 'github'])]
            if other_urls:
                personal_info['portfolio'] = other_urls[0]
            
            # Extract name from the beginning of the text
            lines = text.split('\n')
            for line in lines[:5]:  # Check first 5 lines for name
                line = line.strip()
                if line and not any(keyword in line.lower() for keyword in 
                                  ['phone', 'email', 'linkedin', 'github', 'summary', 'experience']):
                    # Simple name validation: 2-4 words, capitalized
                    words = line.split()
                    if 2 <= len(words) <= 4 and all(word[0].isupper() for word in words if word):
                        personal_info['full_name'] = line
                        name_parts = line.split()
                        personal_info['first_name'] = name_parts[0]
                        personal_info['last_name'] = name_parts[-1]
                        confidence_factors.append(0.3)
                        break
            
            # Extract location using simple pattern matching
            location_patterns = [
                r'(\w+,\s*\w+,\s*\w+,\s*\d+)',  # City, State, Country, Zip
                r'(\w+,\s*\w+,\s*\w+)',  # City, State, Country
                r'(\w+,\s*\w+)',  # City, State
            ]
            
            for pattern in location_patterns:
                locations = re.findall(pattern, text)
                if locations:
                    personal_info['location'] = locations[0]
                    confidence_factors.append(0.2)
                    break
            
        except Exception as e:
            print(f"Error in personal info extraction: {e}")
        
        confidence = sum(confidence_factors) if confidence_factors else 0.0
        return personal_info, confidence
    
    def extract_summary(self, text: str) -> Tuple[str, float]:
        """Extract professional summary with confidence"""
        try:
            # Find summary section
            sections = self._split_into_sections(text)
            
            # Look for summary section
            summary_keywords = ['summary', 'objective', 'about', 'profile']
            for section_title, section_content in sections.items():
                if any(keyword in section_title.lower() for keyword in summary_keywords):
                    # Take first paragraph of summary section
                    paragraphs = [p.strip() for p in section_content.split('\n') if p.strip()]
                    if paragraphs:
                        return paragraphs[0], 0.8
            
            # Fallback: find first meaningful paragraph after name
            lines = text.split('\n')
            found_name = False
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Assume we found name in previous lines
                if found_name and len(line) > 50 and not any(keyword in line.lower() for keyword in 
                                                           ['experience', 'education', 'skills', 'projects']):
                    return line, 0.6
                
                # Mark when we likely found the name section
                if any(word in line.lower() for word in ['@', 'phone', 'email', 'linkedin']):
                    found_name = True
            
            return "", 0.3
        except:
            return "", 0.0
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split resume text into sections"""
        sections = {}
        current_section = "header"
        current_content = []
        
        lines = text.split('\n')
        section_pattern = re.compile(r'^[A-Z][A-Z\s]{2,}$')  # ALL CAPS section headers
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            if (section_pattern.match(line) or 
                line.lower() in ['summary', 'experience', 'education', 'skills', 'projects', 'certifications']):
                
                # Save previous section
                if current_content and current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line.lower()
                current_content = []
            else:
                current_content.append(line)
        
        # Save the last section
        if current_content and current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def extract_work_experience(self, text: str) -> Tuple[List[Dict[str, Any]], float]:
        """Extract work experience with improved detection"""
        experiences = []
        
        try:
            sections = self._split_into_sections(text)
            
            # Look for experience section
            exp_keywords = ['experience', 'work', 'employment']
            exp_section = None
            
            for section_title, section_content in sections.items():
                if any(keyword in section_title for keyword in exp_keywords):
                    exp_section = section_content
                    break
            
            if not exp_section:
                # Try to find experience patterns in entire text
                exp_section = text
            
            # Improved job pattern matching
            job_patterns = [
                # Company - Title (Date - Date)
                r'(.+?)\s*[-–]\s*(.+?)\s*\((\w+\s*\d{4})\s*[-–]\s*(\w+\s*\d{4}|Present)\)',
                # Title at Company (Date - Date)
                r'(.+?)\s+at\s+(.+?)\s*\((\w+\s*\d{4})\s*[-–]\s*(\w+\s*\d{4}|Present)\)',
            ]
            
            for pattern in job_patterns:
                matches = re.finditer(pattern, exp_section, re.IGNORECASE)
                for match in matches:
                    if match.lastindex >= 4:
                        experience = {
                            "job_title": match.group(2).strip() if ' at ' in match.group(0) else match.group(1).strip(),
                            "company": match.group(1).strip() if ' at ' in match.group(0) else match.group(2).strip(),
                            "start_date": self._parse_date(match.group(3)),
                            "end_date": self._parse_date(match.group(4)) if match.group(4) != "Present" else "Present",
                            "type": self._detect_employment_type(match.group(2) if ' at ' in match.group(0) else match.group(1)),
                            "location": "",
                            "description": self._extract_job_description(exp_section, match.group(0)),
                            "skills_gained": []
                        }
                        experiences.append(experience)
            
        except Exception as e:
            print(f"Error in work experience extraction: {e}")
        
        confidence = min(len(experiences) * 0.3, 1.0)
        return experiences, confidence
    
    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats to MM/YYYY"""
        try:
            # Handle common date formats
            date_str = date_str.strip()
            if not date_str or date_str.lower() == 'present':
                return "Present"
            
            # Simple month-year parsing
            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            
            for month_name, month_num in month_map.items():
                if month_name in date_str.lower():
                    year_match = re.search(r'(\d{4})', date_str)
                    if year_match:
                        return f"{month_num}/{year_match.group(1)}"
            
            # Try to extract year
            year_match = re.search(r'(\d{4})', date_str)
            if year_match:
                return f"01/{year_match.group(1)}"
            
            return date_str
        except:
            return date_str
    
    def _extract_job_description(self, text: str, job_context: str) -> List[str]:
        """Extract job description bullets"""
        descriptions = []
        try:
            # Find the paragraph after the job entry
            lines = text.split('\n')
            found_job = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if job_context in line:
                    found_job = True
                    continue
                
                if found_job:
                    # Stop at next job entry or section
                    if re.match(r'.*[\(\)].*\d{4}.*', line) or len(line) < 10:
                        break
                    
                    # Add meaningful lines as descriptions
                    if len(line) > 20 and not line.startswith('-'):
                        descriptions.append(line)
                    
                    if len(descriptions) >= 3:  # Limit to 3 bullets
                        break
        
        except Exception as e:
            print(f"Error extracting job description: {e}")
        
        return descriptions
    
    def extract_education(self, text: str) -> Tuple[List[Dict[str, Any]], float]:
        """Extract education information with improved detection"""
        education = []
        
        try:
            sections = self._split_into_sections(text)
            
            # Look for education section
            edu_section = None
            for section_title, section_content in sections.items():
                if 'education' in section_title:
                    edu_section = section_content
                    break
            
            if not edu_section:
                edu_section = text
            
            # Improved education pattern matching
            edu_patterns = [
                # Institution - Degree (Year - Year)
                r'(.+?)\s*[-–]\s*(.+?)\s*\((\d{4})\s*[-–]\s*(\d{4}|Present)\)',
                # Degree from Institution (Year - Year)
                r'(.+?)\s+from\s+(.+?)\s*\(?\s*(\d{4})\s*[-–]\s*(\d{4})\s*\)?',
            ]
            
            for pattern in edu_patterns:
                matches = re.finditer(pattern, edu_section, re.IGNORECASE)
                for match in matches:
                    if match.lastindex >= 4:
                        edu_entry = {
                            "degree": match.group(2).strip() if ' from ' in match.group(0) else match.group(1).strip(),
                            "institution": match.group(1).strip() if ' from ' in match.group(0) else match.group(2).strip(),
                            "start_year": match.group(3),
                            "end_year": match.group(4),
                            "field_of_study": "",
                            "grade": self._extract_grade(edu_section, match.group(0))
                        }
                        education.append(edu_entry)
            
        except Exception as e:
            print(f"Error in education extraction: {e}")
        
        confidence = min(len(education) * 0.3, 1.0)
        return education, confidence
    
    def _extract_grade(self, text: str, context: str) -> str:
        """Extract grade/CGPA information"""
        try:
            # Look for grade patterns near the education entry
            grade_patterns = [
                r'(\d+\.\d+)\s*(?:CGPA|GPA)',
                r'(\d+)\s*%',
                r'Grade:\s*([A-B][+-]?)',
            ]
            
            for pattern in grade_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        except:
            pass
        
        return ""
    
    def _detect_employment_type(self, job_title: str) -> str:
        """Detect employment type from job title"""
        try:
            job_title_lower = job_title.lower()
            
            if 'intern' in job_title_lower:
                return 'internship'
            elif any(word in job_title_lower for word in ['freelance', 'contract', 'consultant']):
                return 'contract'
            elif 'part' in job_title_lower and 'time' in job_title_lower:
                return 'part-time'
            else:
                return 'full-time'
        except:
            return 'full-time'