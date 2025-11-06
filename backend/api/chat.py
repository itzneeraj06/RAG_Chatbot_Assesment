from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.models.schemas import (
    ChatRequest, 
    ChatResponse, 
    FAQRequest, 
    FAQResponse
)
from backend.agent.scheduling_agent import agent
from backend.rag.faq_rag import faq_system


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main conversational endpoint for scheduling and FAQ
    
    This endpoint handles natural conversation for:
    - Appointment scheduling
    - Clinic FAQ
    - Seamless context switching between both
    """
    try:
        result = agent.chat(request.message, request.session_id)
        
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            timestamp=datetime.now(),
            context={
                "tool_calls": result.get("tool_calls", [])
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat: {str(e)}"
        )


@router.post("/ask-faq", response_model=FAQResponse)
async def ask_faq_endpoint(request: FAQRequest):
    """
    Direct FAQ endpoint for clinic information
    
    Uses RAG to answer questions about:
    - Clinic policies
    - Insurance and billing
    - Location and parking
    - Services offered
    - COVID-19 protocols
    """
    try:
        response = faq_system.answer_question(request.question, include_sources=True)
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing FAQ: {str(e)}"
        )


@router.post("/reset-session/{session_id}")
async def reset_session_endpoint(session_id: str):
    """Reset conversation history for a session"""
    try:
        agent.reset_session(session_id)
        return {
            "message": f"Session {session_id} has been reset",
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting session: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a session"""
    try:
        info = agent.get_session_info(session_id)
        return info
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting session info: {str(e)}"
        )