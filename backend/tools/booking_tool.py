from typing import Dict, Any
from backend.api.calendly_integration import calendly_api
from backend.models.schemas import BookingRequest, PatientInfo, AppointmentType


def book_appointment(
    date: str,
    start_time: str,
    appointment_type: str,
    patient_name: str,
    patient_email: str,
    patient_phone: str,
    reason: str
) -> Dict[str, Any]:
    """
    Book an appointment
    
    Args:
        date: Date in YYYY-MM-DD format
        start_time: Start time in HH:MM format (24-hour)
        appointment_type: One of 'consultation', 'followup', 'physical', 'specialist'
        patient_name: Patient's full name
        patient_email: Patient's email address
        patient_phone: Patient's phone number
        reason: Reason for visit
    
    Returns:
        Dictionary with booking confirmation details
    """
    try:
        # Create booking request
        patient = PatientInfo(
            name=patient_name,
            email=patient_email,
            phone=patient_phone
        )
        
        booking_req = BookingRequest(
            appointment_type=AppointmentType(appointment_type),
            date=date,
            start_time=start_time,
            patient=patient,
            reason=reason
        )
        
        # Book through Calendly API
        booking_response = calendly_api.book_appointment(booking_req)
        
        # Format response for agent
        return {
            "success": True,
            "booking_id": booking_response.booking_id,
            "confirmation_code": booking_response.confirmation_code,
            "status": booking_response.status,
            "details": booking_response.details,
            "message": booking_response.message
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Booking failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "message": "I apologize, but there was an error booking your appointment. Please try again or call us at +91-731-555-0100."
        }