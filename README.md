# AI Resume Parser API

A FastAPI-based service that extracts structured information from resumes (PDF/DOCX) and returns standardized JSON with confidence scoring.

## Features

- 📄 **Multi-format Support**: PDF and DOCX files
- 🎯 **Structured Extraction**: Personal info, work experience, education, skills, projects
- 📊 **Confidence Scoring**: Individual section confidence scores
- ⚡ **Fast Processing**: Optimized text extraction and parsing
- 💾 **Smart Caching**: File hash-based caching for performance
- 🔒 **Validation**: File type and size validation
- 📝 **Auto Documentation**: Interactive API docs

## Quick Start

### Prerequisites

- Python 3.10+
- spaCy English model

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd resume-parser-api