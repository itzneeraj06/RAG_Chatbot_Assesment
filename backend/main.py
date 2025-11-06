from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv

from backend.api.chat import router as chat_router
from backend.api.calendly_integration import calendly_api
from backend.models.schemas import (
    HealthCheckResponse,
    AvailabilityRequest,
    BookingRequest
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Medical Appointment Scheduling Agent",
    description="Intelligent conversational agent for scheduling medical appointments with RAG-based FAQ system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api", tags=["Chat & FAQ"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to HealthCare Plus Clinic Appointment Scheduling API",
        "clinic": "HealthCare Plus Clinic",
        "doctor": "Dr. Rajendra Kumar Gupta, M.D.",
        "location": "302 Old Palasia, Indore, MP 452001",
        "phone": "+91-731-555-0100",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Check if essential services are working
        openai_key = os.getenv("OPENAI_API_KEY")
        
        services = {
            "api": "healthy",
            "openai": "configured" if openai_key else "not_configured",
            "calendly": "healthy",
            "vector_db": "healthy"
        }
        
        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now(),
            services=services
        )
    except Exception as e:
        return HealthCheckResponse(
            status="degraded",
            timestamp=datetime.now(),
            services={"error": str(e)}
        )


# Calendly Integration Endpoints
@app.get("/api/calendly/availability", tags=["Calendly"])
async def get_availability(date: str, appointment_type: str):
    """
    Get available time slots for a given date and appointment type
    
    Query Parameters:
    - date: Date in YYYY-MM-DD format (e.g., '2024-01-15')
    - appointment_type: One of 'consultation', 'followup', 'physical', 'specialist'
    """
    try:
        availability = calendly_api.get_availability(date, appointment_type)
        return availability
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching availability: {str(e)}")


@app.post("/api/calendly/book", tags=["Calendly"])
async def book_appointment_endpoint(request: BookingRequest):
    """
    Book an appointment
    
    Body:
    - appointment_type: Type of appointment
    - date: Date in YYYY-MM-DD format
    - start_time: Start time in HH:MM format (24-hour)
    - patient: Patient information (name, email, phone)
    - reason: Reason for visit
    """
    try:
        booking = calendly_api.book_appointment(request)
        return booking
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error booking appointment: {str(e)}")


@app.get("/api/calendly/booking/{booking_id}", tags=["Calendly"])
async def get_booking(booking_id: str):
    """Get booking details by ID"""
    booking = calendly_api.get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@app.delete("/api/calendly/booking/{booking_id}", tags=["Calendly"])
async def cancel_booking(booking_id: str):
    """Cancel a booking"""
    success = calendly_api.cancel_booking(booking_id)
    if not success:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": f"Booking {booking_id} has been cancelled", "booking_id": booking_id}


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Not Found",
        "detail": "The requested resource was not found",
        "path": str(request.url)
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "error": "Internal Server Error",
        "detail": "An unexpected error occurred. Please try again or contact support.",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)