import pdfplumber
from docx import Document
import os
import tempfile
from typing import Tuple, Optional
import hashlib
from fastapi import UploadFile, HTTPException
import io

class FileProcessor:
    @staticmethod
    def validate_file(file: UploadFile) -> Tuple[str, str]:
        """Validate file and return file extension and content hash"""
        # Read file content once
        file_content = file.file.read()
        
        # Check file size
        if len(file_content) > 20 * 1024 * 1024:  # 20MB
            raise HTTPException(status_code=400, detail="File too large")
        
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.pdf', '.docx']:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Generate file hash for caching
        file_hash = hashlib.md5(content).hexdigest()
        
        # Reset file pointer for future reads
        file.file.seek(0)
        
        return file_extension, file_hash
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF processing failed: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"DOCX processing failed: {str(e)}")
    
    @staticmethod
    def extract_text(file: UploadFile) -> Tuple[str, str]:
        """Main method to extract text from uploaded file"""
        file_content = file.file.read()
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Validate file size
        if len(file_content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Validate file extension
        if file_extension not in ['.pdf', '.docx']:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Generate file hash for caching
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Extract text based on file type
        if file_extension == '.pdf':
            text = FileProcessor.extract_text_from_pdf(file_content)
        elif file_extension == '.docx':
            text = FileProcessor.extract_text_from_docx(file_content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        return text, file_hash