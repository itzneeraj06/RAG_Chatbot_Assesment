from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum


class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOWUP = "followup"
    PHYSICAL = "physical"
    SPECIALIST = "specialist"


class PatientInfo(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?[\d\s\-()]+$')
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove spaces, dashes, parentheses
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 10:
            raise ValueError('Phone number must have at least 10 digits')
        return v


class TimeSlot(BaseModel):
    start_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    end_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    available: bool
    appointment_id: Optional[str] = None


class AvailabilityRequest(BaseModel):
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    appointment_type: AppointmentType


class AvailabilityResponse(BaseModel):
    date: str
    day_of_week: str
    available_slots: List[TimeSlot]
    total_slots: int
    available_count: int


class BookingRequest(BaseModel):
    appointment_type: AppointmentType
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    start_time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    patient: PatientInfo
    reason: str = Field(..., min_length=5, max_length=500)


class BookingResponse(BaseModel):
    booking_id: str
    status: str
    confirmation_code: str
    details: Dict[str, Any]
    message: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(..., min_length=1, max_length=100)


class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None


class FAQRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class FAQResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: float
    retrieved_chunks: Optional[List[str]] = None


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime