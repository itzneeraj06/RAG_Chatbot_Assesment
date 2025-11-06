from datetime import datetime
from typing import Dict, Any
from backend.api.calendly_integration import calendly_api


def check_availability(date: str, appointment_type: str) -> Dict[str, Any]:
    """
    Check available appointment slots for a given date and appointment type
    
    Args:
        date: Date in YYYY-MM-DD format
        appointment_type: One of 'consultation', 'followup', 'physical', 'specialist'
    
    Returns:
        Dictionary with available slots and metadata
    """
    try:
        # Get availability from Calendly API
        availability = calendly_api.get_availability(date, appointment_type)
        
        # Filter only available slots
        available_slots = [
            slot for slot in availability.available_slots 
            if slot.available
        ]
        
        # Format for agent consumption
        result = {
            "date": availability.date,
            "day_of_week": availability.day_of_week,
            "total_slots": availability.total_slots,
            "available_count": len(available_slots),
            "available_slots": [
                {
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "display_time": _format_time_12hr(slot.start_time)
                }
                for slot in available_slots
            ]
        }
        
        # Add helpful message
        if len(available_slots) == 0:
            result["message"] = f"No available slots on {availability.day_of_week}, {date}"
        else:
            result["message"] = f"Found {len(available_slots)} available slots on {availability.day_of_week}, {date}"
        
        return result
        
    except ValueError as e:
        return {
            "error": str(e),
            "date": date,
            "available_slots": [],
            "available_count": 0
        }
    except Exception as e:
        return {
            "error": f"Failed to check availability: {str(e)}",
            "date": date,
            "available_slots": [],
            "available_count": 0
        }


def _format_time_12hr(time_24hr: str) -> str:
    """Convert 24-hour time to 12-hour format with AM/PM"""
    try:
        time_obj = datetime.strptime(time_24hr, "%H:%M")
        return time_obj.strftime("%I:%M %p").lstrip('0')
    except:
        return time_24hr