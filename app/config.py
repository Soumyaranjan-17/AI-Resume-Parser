import os
from typing import Dict, List

class Settings:
    # File settings
    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB
    SUPPORTED_FORMATS: List[str] = [".pdf", ".docx"]
    PROCESSING_TIMEOUT: int = 30  # seconds
    
    # Cache settings
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_MAXSIZE: int = 1000
    
    # Extraction settings
    SKILL_TAXONOMY: Dict[str, List[str]] = {
        "programming_languages": [
            "python", "java", "javascript", "c++", "c#", "go", "rust", "swift", 
            "kotlin", "typescript", "php", "ruby", "sql", "r", "matlab"
        ],
        "frameworks": [
            "react", "angular", "vue", "django", "flask", "fastapi", "spring",
            "node.js", "express", "laravel", "ruby on rails", "tensorflow",
            "pytorch", "keras", "scikit-learn", "pandas", "numpy"
        ],
        "tools": [
            "docker", "kubernetes", "aws", "azure", "gcp", "git", "jenkins",
            "linux", "unix", "windows", "macos", "jira", "confluence"
        ],
        "databases": [
            "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
            "cassandra", "elasticsearch"
        ],
        "soft_skills": [
            "leadership", "communication", "teamwork", "problem solving",
            "critical thinking", "time management", "adaptability", "creativity",
            "collaboration", "presentation", "negotiation"
        ]
    }
    
    # Date formats to try
    DATE_FORMATS: List[str] = [
        "%m/%Y", "%Y-%m", "%b %Y", "%B %Y", "%m-%Y", "%Y/%m"
    ]

settings = Settings()