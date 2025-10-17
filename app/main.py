from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
from datetime import datetime
from typing import Dict, Any
import traceback

from app.services.file_processor import FileProcessor
from app.services.text_analyzer import TextAnalyzer
from app.services.skill_extractor import SkillExtractor
from app.services.cache_manager import cache_manager
from app.models.schemas import (
    ResumeResponse, ResumeData, PersonalInfo, WorkExperience, 
    Education, Skills, Project, Certification, SectionConfidence, ExtractionMetadata, HealthResponse
)

app = FastAPI(
    title="AI Resume Parser API",
    description="Extract structured information from resumes with confidence scoring",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
file_processor = FileProcessor()
text_analyzer = TextAnalyzer()
skill_extractor = SkillExtractor()

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Resume Parser API. Visit /docs for API documentation."}

@app.post("/parse-resume", response_model=ResumeResponse)
async def parse_resume(file: UploadFile = File(...)):
    """
    Parse resume from PDF or DOCX file and return structured data
    """
    start_time = time.time()
    
    try:
        print(f"Processing file: {file.filename}")
        
        # Extract text and get file hash
        text, file_hash = file_processor.extract_text(file)
        print(f"Extracted text length: {len(text)}")
        
        # Check cache first
        cached_result = cache_manager.get(file_hash)
        if cached_result:
            print("Cache hit!")
            cached_result['metadata']['extraction_details']['cache_hit'] = True
            return ResumeResponse(**cached_result)
        
        if not text.strip():
            print("No text extracted")
            return create_empty_response(0.1, "No text extracted from file")
        
        # Extract all sections with confidence scores
        print("Extracting personal info...")
        personal_info, personal_confidence = text_analyzer.extract_personal_info(text)
        
        print("Extracting summary...")
        summary, summary_confidence = text_analyzer.extract_summary(text)
        
        print("Extracting work experience...")
        work_experience, work_confidence = text_analyzer.extract_work_experience(text)
        
        print("Extracting education...")
        education, education_confidence = text_analyzer.extract_education(text)
        
        print("Extracting skills...")
        skills, skills_confidence = skill_extractor.extract_skills(text)
        
        print("Extracting projects...")
        projects, projects_confidence = skill_extractor.extract_projects(text)
        
        # Create response data
        resume_data = ResumeData(
            personal_info=PersonalInfo(**personal_info),
            summary=summary,
            work_experience=[WorkExperience(**exp) for exp in work_experience],
            education=[Education(**edu) for edu in education],
            skills=Skills(**skills),
            projects=[Project(**proj) for proj in projects],
            certifications=[],
            languages=[],
            interests=[]
        )
        
        # Calculate overall confidence
        section_confidences = SectionConfidence(
            personal_info=personal_confidence,
            summary=summary_confidence,
            work_experience=work_confidence,
            education=education_confidence,
            skills=skills_confidence,
            projects=projects_confidence,
            certifications=0.0,
            languages=0.0,
            interests=0.0
        )
        
        overall_confidence = calculate_overall_confidence(section_confidences)
        
        processing_time = time.time() - start_time
        
        metadata = ExtractionMetadata(
            processing_time=processing_time,
            overall_confidence=overall_confidence,
            section_confidence=section_confidences,
            extraction_details={
                "file_type": file.filename.split('.')[-1] if '.' in file.filename else "unknown",
                "file_size": len(text),
                "text_length": len(text),
                "cache_hit": False
            }
        )
        
        response = ResumeResponse(data=resume_data, metadata=metadata)
        
        # Cache the result
        cache_manager.set(file_hash, response.dict())
        
        print(f"Processing completed in {processing_time:.2f}s")
        return response
        
    except HTTPException as he:
        print(f"HTTP Exception: {he}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now()
    )

@app.get("/supported-formats")
async def supported_formats():
    """Get supported file formats"""
    return {
        "supported_formats": [".pdf", ".docx"],
        "max_file_size": "20MB",
        "processing_timeout": "30 seconds"
    }

def calculate_overall_confidence(section_confidences: SectionConfidence) -> float:
    """Calculate weighted overall confidence score"""
    weights = {
        'personal_info': 0.15,
        'work_experience': 0.25,
        'education': 0.20,
        'skills': 0.20,
        'summary': 0.05,
        'projects': 0.10,
        'certifications': 0.03,
        'languages': 0.01,
        'interests': 0.01
    }
    
    total_confidence = 0.0
    total_weight = 0.0
    
    for section, confidence in section_confidences.dict().items():
        total_confidence += confidence * weights.get(section, 0)
        total_weight += weights.get(section, 0)
    
    return total_confidence / total_weight if total_weight > 0 else 0.0

def create_empty_response(confidence: float, reason: str) -> ResumeResponse:
    """Create empty response for failed extraction"""
    empty_data = ResumeData(
        personal_info=PersonalInfo(),
        skills=Skills(),
        work_experience=[],
        education=[],
        projects=[],
        certifications=[],
        languages=[],
        interests=[],
        summary=""
    )
    
    empty_confidence = SectionConfidence()
    
    metadata = ExtractionMetadata(
        processing_time=0.0,
        overall_confidence=confidence,
        section_confidence=empty_confidence,
        extraction_details={
            "error_reason": reason,
            "cache_hit": False
        }
    )
    
    return ResumeResponse(data=empty_data, metadata=metadata)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000, reload=True)
