import re
from typing import List, Dict, Tuple, Set
from app.config import settings

class SkillExtractor:
    def __init__(self):
        self.skill_taxonomy = settings.SKILL_TAXONOMY
        self.skill_aliases = self._build_skill_aliases()
    
    def _build_skill_aliases(self) -> Dict[str, str]:
        """Build mapping from aliases to standardized skill names"""
        aliases = {}
        for category, skills in self.skill_taxonomy.items():
            for skill in skills:
                # Add the skill itself
                aliases[skill.lower()] = skill
                
                # Add common aliases
                if skill == "javascript":
                    aliases.update({"js": "javascript", "es6": "javascript"})
                elif skill == "python":
                    aliases.update({"py": "python"})
                elif skill == "node.js":
                    aliases.update({"node": "node.js", "nodejs": "node.js"})
                elif skill == "c++":
                    aliases.update({"cpp": "c++"})
                elif skill == "c#":
                    aliases.update({"csharp": "c#"})
                elif skill == "react":
                    aliases.update({"reactjs": "react", "react.js": "react"})
                elif skill == "aws":
                    aliases.update({"amazon web services": "aws"})
                elif skill == "express":
                    aliases.update({"expressjs": "express", "express.js": "express"})
        
        return aliases
    
    def extract_skills(self, text: str) -> Tuple[Dict[str, List[str]], float]:
        """Extract and categorize skills from text"""
        text_lower = text.lower()
        found_skills = set()
        
        # Look for skills in taxonomy
        for category, skills in self.skill_taxonomy.items():
            for skill in skills:
                skill_lower = skill.lower()
                # Check for exact matches with word boundaries
                if re.search(r'\b' + re.escape(skill_lower) + r'\b', text_lower):
                    found_skills.add(self.skill_aliases.get(skill_lower, skill))
        
        # Look for skill aliases
        for alias, standardized in self.skill_aliases.items():
            if alias != standardized and re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                found_skills.add(standardized)
        
        # Categorize skills
        categorized_skills = {"technical": [], "soft": []}
        
        for skill in found_skills:
            skill_lower = skill.lower()
            
            # Check if it's a soft skill
            is_soft_skill = False
            soft_skills_list = self.skill_taxonomy.get("soft_skills", [])
            if isinstance(soft_skills_list, list):
                is_soft_skill = any(skill_lower == s.lower() for s in soft_skills_list)
            
            if is_soft_skill:
                categorized_skills["soft"].append(skill)
            else:
                categorized_skills["technical"].append(skill)
        
        # Calculate confidence based on number of skills found
        total_skills_in_taxonomy = sum(len(skills) for skills in self.skill_taxonomy.values() if isinstance(skills, list))
        confidence = min(len(found_skills) / max(total_skills_in_taxonomy, 1) * 2, 1.0)
        
        return categorized_skills, confidence
    
    def extract_projects(self, text: str) -> Tuple[List[Dict[str, any]], float]:
        """Extract project information with improved detection"""
        projects = []
        
        try:
            # Look for projects section
            sections = self._split_into_sections(text)
            projects_section = None
            
            for section_title, section_content in sections.items():
                if 'project' in section_title:
                    projects_section = section_content
                    break
            
            if not projects_section:
                projects_section = text
            
            # Improved project detection
            project_patterns = [
                # Project Name - Description (Date - Date)
                r'^(.+?)\s*[-–]\s*(.+?)\s*\((\w+\s*\d{4})\s*[-–]\s*(\w+\s*\d{4})\)',
                # Project Name, Tech Stack
                r'^(.+?)\s*[,:\-]\s*(.+?)$',
            ]
            
            lines = projects_section.split('\n')
            current_project = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line starts a new project
                project_found = False
                for pattern in project_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        if current_project and current_project['name']:
                            projects.append(current_project)
                        
                        project_name = match.group(1).strip()
                        project_desc = match.group(2).strip() if match.lastindex >= 2 else ""
                        
                        # Validate project name (not too short, not a sentence)
                        if (len(project_name) > 2 and len(project_name) < 50 and 
                            not project_name.endswith('.') and not any(word in project_name.lower() for word in 
                            ['the', 'and', 'with', 'for', 'using'])):
                            
                            current_project = {
                                "name": project_name,
                                "description": project_desc,
                                "tech_stack": self._extract_tech_from_description(project_desc),
                                "project_url": self._extract_project_url(line)
                            }
                            project_found = True
                            break
                
                # If no new project found, add to current project description
                if not project_found and current_project and len(line) > 10:
                    if len(current_project['description']) < 200:  # Limit description length
                        current_project['description'] += " " + line
            
            # Add the last project
            if current_project and current_project['name']:
                projects.append(current_project)
            
        except Exception as e:
            print(f"Error extracting projects: {e}")
        
        # Filter out poor quality projects
        quality_projects = [
            proj for proj in projects 
            if len(proj['name']) > 2 and not proj['name'].isdigit()
        ]
        
        confidence = min(len(quality_projects) * 0.4, 1.0)
        return quality_projects, confidence
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split text into sections (copied from text_analyzer for consistency)"""
        sections = {}
        current_section = "header"
        current_content = []
        
        lines = text.split('\n')
        section_pattern = re.compile(r'^[A-Z][A-Z\s]{2,}$')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if (section_pattern.match(line) or 
                line.lower() in ['summary', 'experience', 'education', 'skills', 'projects', 'certifications']):
                
                if current_content and current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                current_section = line.lower()
                current_content = []
            else:
                current_content.append(line)
        
        if current_content and current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_tech_from_description(self, description: str) -> List[str]:
        """Extract technologies from project description"""
        if not description:
            return []
        
        tech_skills, _ = self.extract_skills(description)
        return tech_skills["technical"]
    
    def _extract_project_url(self, text: str) -> str:
        """Extract project URL from text"""
        url_pattern = re.compile(r'https?://[^\s]+')
        urls = url_pattern.findall(text)
        return urls[0] if urls else ""