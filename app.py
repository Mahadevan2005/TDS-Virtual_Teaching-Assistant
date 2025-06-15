from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
from dotenv import load_dotenv

from models.request_models import QuestionRequest
from models.response_models import AnswerResponse, LinkResponse
from services.question_processor import QuestionProcessor
from services.answer_generator import AnswerGenerator

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="TDS Virtual TA",
    description="A virtual Teaching Assistant API for Tools in Data Science course",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
question_processor = QuestionProcessor()
answer_generator = AnswerGenerator()


@app.get("/")
async def root():
    """
    Root endpoint with basic API information
    """
    return {
        "message": "TDS Virtual TA API",
        "endpoints": {
            "POST /api/": "Submit a question to get an answer",
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "TDS Virtual TA"}


@app.post("/api/", response_model=AnswerResponse)
async def answer_question(request: QuestionRequest):
    """
    Main API endpoint to answer student questions
    
    Args:
        request: QuestionRequest containing the question and optional image
    
    Returns:
        AnswerResponse: Contains the answer and relevant links
    """
    try:
        # Validate request
        if not request.question or len(request.question.strip()) == 0:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Process the question
        processed_question = question_processor.process_question(
            request.question, 
            request.image
        )
        
        # Generate answer
        answer_data = answer_generator.generate_answer(processed_question)
        
        # Format response
        # response = AnswerResponse(
        #     answer=answer_data['answer'],
        #     links=[
        #         LinkResponse(url=link['url'], text=link.get('text', link.get('title', 'Link')))
        #         for link in answer_data['links']
        #     ]
        # )
        response = AnswerResponse(
            answer=answer_data['answer'],
            links=[
                LinkResponse(
                    url=link.get('url', ''),
                    text=link.get('text', 'Link')
                )
                for link in answer_data.get('links', [])
                if isinstance(link, dict)
            ]
        )

        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """
    Get API statistics and available data
    """
    discourse_count = len(answer_generator.enhanced_discourse_posts)
    course_content_count = len(answer_generator.enhanced_course_content)
    
    return {
        "discourse_topics": discourse_count,
        "course_content_sections": course_content_count,
        "predefined_answer_categories": len(answer_generator.predefined_answers)
    }


if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"Starting TDS Virtual TA API on {host}:{port}")
    print(f"Debug mode: {debug}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )