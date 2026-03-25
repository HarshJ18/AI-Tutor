"""
FastAPI Server for AI Tutor Application
Provides REST API endpoints for all application functionalities
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import shutil
from pathlib import Path
import uvicorn

# Import local modules
import api_handler
from rag_advanced import build_index, retrieve, get_available_subjects, get_subject_stats
from quiz_generator import QuizGenerator

# Initialize FastAPI app
app = FastAPI(
    title="AI Tutor API",
    description="REST API for AI Tutor - Educational Platform with RAG and Quiz Generation",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize quiz generator
quiz_generator = QuizGenerator()


# ==================== Request/Response Models ====================

class ChatRequest(BaseModel):
    api_key: str
    question: str
    model: Optional[str] = "llama-3.1-70b-versatile"
    subject_filter: Optional[str] = "all"
    k: Optional[int] = 5  # Number of context chunks to retrieve


class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    model_used: Optional[str] = None


class BuildIndexRequest(BaseModel):
    api_key: str
    pdf_dir: Optional[str] = "pdf"
    upload_dir: Optional[str] = "uploads"


class BuildIndexResponse(BaseModel):
    success: bool
    chunks: int
    dim: int
    subjects: List[str]
    subject_stats: Dict[str, Dict[str, int]]
    message: str


class RetrieveRequest(BaseModel):
    api_key: str
    query: str
    k: Optional[int] = 5
    subject_filter: Optional[str] = "all"


class RetrieveResponse(BaseModel):
    results: List[Dict[str, Any]]


class QuizGenerateRequest(BaseModel):
    api_key: str
    content: str
    num_questions: Optional[int] = 5
    difficulty: Optional[str] = "medium"
    quiz_type: Optional[str] = "Mixed"


class QuizGenerateResponse(BaseModel):
    success: bool
    quiz: Dict[str, Any]
    message: str


class QuizGradeRequest(BaseModel):
    quiz: Dict[str, Any]
    answers: Dict[int, Any]


class QuizGradeResponse(BaseModel):
    success: bool
    results: Dict[str, Any]
    message: str


class HealthResponse(BaseModel):
    status: str
    message: str
    version: str


# ==================== API Endpoints ====================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint - API information"""
    return {
        "message": "AI Tutor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="AI Tutor API is running",
        version="1.0.0"
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a question to the AI tutor and get a response with RAG context
    
    Request Body:
    {
        "api_key": "your_groq_api_key",
        "question": "What is natural language processing?",
        "model": "llama-3.1-70b-versatile",  # optional
        "subject_filter": "all",  # optional, filter by subject
        "k": 5  # optional, number of context chunks
    }
    
    Response:
    {
        "response": "AI generated response...",
        "sources": [
            {
                "file": "document.pdf",
                "page": 1,
                "text": "context text...",
                "score": 0.85,
                "subject": "computer_science"
            }
        ],
        "model_used": "llama-3.1-70b-versatile"
    }
    """
    try:
        # Retrieve context with subject filtering
        sources = retrieve(
            request.api_key,
            request.question,
            k=request.k,
            subject_filter=request.subject_filter
        )
        
        # Build enhanced prompt with context
        if sources:
            context = "\n\n".join([
                f"Source: {s['file']} (Page {s['page']}) - Subject: {s.get('subject', 'general')}\n{s['text']}"
                for s in sources
            ])
            enhanced_prompt = f"Context from documents (Subject: {request.subject_filter}):\n{context}\n\nUser question: {request.question}"
        else:
            enhanced_prompt = request.question
        
        # Get AI response
        response_text = api_handler.send_query_get_response(
            request.api_key,
            enhanced_prompt,
            ""
        )
        
        return ChatResponse(
            response=response_text,
            sources=sources,
            model_used=request.model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.post("/api/build-index", response_model=BuildIndexResponse)
async def build_rag_index(request: BuildIndexRequest):
    """
    Build or refresh the RAG index from documents
    
    Request Body:
    {
        "api_key": "your_groq_api_key",
        "pdf_dir": "pdf",  # optional
        "upload_dir": "uploads"  # optional
    }
    
    Response:
    {
        "success": true,
        "chunks": 150,
        "dim": 128,
        "subjects": ["computer_science", "general"],
        "subject_stats": {
            "computer_science": {"chunks": 100, "files": 5},
            "general": {"chunks": 50, "files": 2}
        },
        "message": "Index built successfully"
    }
    """
    try:
        result = build_index(
            request.api_key,
            pdf_dir=request.pdf_dir,
            upload_dir=request.upload_dir
        )
        
        return BuildIndexResponse(
            success=True,
            chunks=result.get("chunks", 0),
            dim=result.get("dim", 0),
            subjects=result.get("subjects", []),
            subject_stats=result.get("subject_stats", {}),
            message=f"Index built successfully with {result.get('chunks', 0)} chunks"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building index: {str(e)}")


@app.post("/api/retrieve", response_model=RetrieveResponse)
async def retrieve_documents(request: RetrieveRequest):
    """
    Retrieve relevant document chunks for a query
    
    Request Body:
    {
        "api_key": "your_groq_api_key",
        "query": "natural language processing",
        "k": 5,  # optional, number of results
        "subject_filter": "all"  # optional
    }
    
    Response:
    {
        "results": [
            {
                "file": "document.pdf",
                "page": 1,
                "text": "relevant text chunk...",
                "score": 0.85,
                "subject": "computer_science"
            }
        ]
    }
    """
    try:
        results = retrieve(
            request.api_key,
            request.query,
            k=request.k,
            subject_filter=request.subject_filter
        )
        
        return RetrieveResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@app.get("/api/subjects")
async def get_subjects():
    """
    Get list of available subjects in the index
    
    Response:
    {
        "subjects": ["computer_science", "mathematics", "physics"],
        "count": 3
    }
    """
    try:
        subjects = get_available_subjects()
        return {
            "subjects": subjects,
            "count": len(subjects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting subjects: {str(e)}")


@app.get("/api/subject-stats")
async def get_subject_statistics():
    """
    Get statistics about subjects in the index
    
    Response:
    {
        "computer_science": {
            "chunks": 100,
            "files": 5
        },
        "mathematics": {
            "chunks": 50,
            "files": 2
        }
    }
    """
    try:
        stats = get_subject_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting subject stats: {str(e)}")


@app.post("/api/quiz/generate", response_model=QuizGenerateResponse)
async def generate_quiz(request: QuizGenerateRequest):
    """
    Generate a quiz from content
    
    Request Body:
    {
        "api_key": "your_groq_api_key",
        "content": "Study material text here...",
        "num_questions": 5,  # optional
        "difficulty": "medium",  # optional: easy, medium, hard
        "quiz_type": "Mixed"  # optional: Mixed, Multiple Choice, True/False, etc.
    }
    
    Response:
    {
        "success": true,
        "quiz": {
            "title": "Quiz - Medium Difficulty",
            "difficulty": "medium",
            "questions": [...],
            "total_questions": 5
        },
        "message": "Quiz generated successfully"
    }
    """
    try:
        quiz = quiz_generator.generate_quiz(
            request.content,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            api_key=request.api_key
        )
        
        return QuizGenerateResponse(
            success=True,
            quiz=quiz,
            message="Quiz generated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")


@app.post("/api/quiz/grade", response_model=QuizGradeResponse)
async def grade_quiz(request: QuizGradeRequest):
    """
    Grade a completed quiz
    
    Request Body:
    {
        "quiz": {
            "title": "Quiz - Medium Difficulty",
            "questions": [
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "question": "What is...?",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0
                }
            ]
        },
        "answers": {
            1: 0,  # question_id: answer
            2: true,
            3: "short answer text"
        }
    }
    
    Response:
    {
        "success": true,
        "results": {
            "total_questions": 5,
            "correct_answers": 4,
            "score_percentage": 80.0,
            "grade": "B",
            "detailed_results": [...]
        },
        "message": "Quiz graded successfully"
    }
    """
    try:
        results = quiz_generator.grade_quiz(request.quiz, request.answers)
        
        return QuizGradeResponse(
            success=True,
            results=results,
            message="Quiz graded successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error grading quiz: {str(e)}")


@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    api_key: str = Form(...)
):
    """
    Upload a document (PDF, DOCX, or TXT)
    
    Request: multipart/form-data
    - file: The document file
    - api_key: Your Groq API key
    
    Response:
    {
        "success": true,
        "filename": "document.pdf",
        "size": 1024000,
        "message": "File uploaded successfully",
        "path": "uploads/document.pdf"
    }
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Also save to pdf directory for RAG processing
        pdf_dir = Path("pdf")
        pdf_dir.mkdir(exist_ok=True)
        
        # Save file to uploads
        upload_path = upload_dir / file.filename
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Also save to pdf directory if it's a PDF
        if file_ext == '.pdf':
            pdf_path = pdf_dir / file.filename
            with open(pdf_path, "wb") as f:
                f.write(open(upload_path, "rb").read())
        
        file_size = upload_path.stat().st_size
        
        return {
            "success": True,
            "filename": file.filename,
            "size": file_size,
            "message": "File uploaded successfully",
            "path": str(upload_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.delete("/api/index/clear")
async def clear_index():
    """
    Clear the RAG index
    
    Response:
    {
        "success": true,
        "message": "Index cleared successfully"
    }
    """
    try:
        index_dir = Path(".rag_index")
        if index_dir.exists():
            shutil.rmtree(index_dir)
        
        return {
            "success": True,
            "message": "Index cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing index: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

