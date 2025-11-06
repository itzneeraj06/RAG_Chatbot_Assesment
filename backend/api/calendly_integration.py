import json
import os
from datetime import datetime, timedelta, date as dt_date
from typing import List, Dict, Any, Optional
import random
import string
from pathlib import Path

from backend.models.schemas import (
    AppointmentType, 
    AvailabilityRequest, 
    AvailabilityResponse,
    BookingRequest, 
    BookingResponse,
    TimeSlot
)


class CalendlyIntegration:
    """Mock Calendly API for appointment scheduling"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.schedule_file = self.data_dir / "doctor_schedule.json"
        self.bookings_file = self.data_dir / "bookings.json"
        self._load_schedule()
        self._load_bookings()
    
    def _load_schedule(self):
        """Load doctor schedule from JSON"""
        with open(self.schedule_file, 'r') as f:
            self.schedule = json.load(f)
    
    def _load_bookings(self):
        """Load existing bookings from JSON"""
        if self.bookings_file.exists():
            with open(self.bookings_file, 'r') as f:
                self.bookings = json.load(f)
        else:
            self.bookings = {"appointments": []}
            self._save_bookings()
    
    def _save_bookings(self):
        """Save bookings to JSON file"""
        with open(self.bookings_file, 'w') as f:
            json.dump(self.bookings, f, indent=2)
    
    def _get_day_name(self, date_str: str) -> str:
        """Get day name from date string"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%A").lower()
    
    def _is_working_day(self, date_str: str) -> bool:
        """Check if the given date is a working day"""
        day_name = self._get_day_name(date_str)
        
        # Check if it's a holiday
        if date_str in self.schedule.get("holidays", []):
            return False
        
        # Check if it's a blocked date
        blocked = self.schedule.get("blocked_dates", [])
        for block in blocked:
            if block["date"] == date_str:
                return False
        
        # Check if there are working hours
        working_hours = self.schedule["working_hours"].get(day_name, {})
        return len(working_hours.get("sessions", [])) > 0
    
    def _get_working_sessions(self, date_str: str) -> List[Dict[str, str]]:
        """Get working sessions for a given date"""
        if not self._is_working_day(date_str):
            return []
        
        day_name = self._get_day_name(date_str)
        return self.schedule["working_hours"][day_name]["sessions"]
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert time string (HH:MM) to minutes since midnight"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    
    def _minutes_to_time(self, minutes: int) -> str:
        """Convert minutes since midnight to time string (HH:MM)"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def _get_appointment_duration(self, appointment_type: str) -> int:
        """Get duration in minutes for appointment type"""
        return self.schedule["appointment_types"][appointment_type]["duration_minutes"]
    
    def _get_booked_slots(self, date_str: str) -> List[Dict[str, str]]:
        """Get all booked slots for a given date"""
        booked = []
        for appt in self.bookings["appointments"]:
            if appt["date"] == date_str and appt["status"] == "confirmed":
                booked.append({
                    "start_time": appt["start_time"],
                    "end_time": appt["end_time"],
                    "appointment_id": appt["booking_id"]
                })
        return booked
    
    def _is_slot_available(self, date_str: str, start_time: str, end_time: str) -> bool:
        """Check if a time slot is available"""
        start_mins = self._time_to_minutes(start_time)
        end_mins = self._time_to_minutes(end_time)
        
        booked_slots = self._get_booked_slots(date_str)
        
        for slot in booked_slots:
            slot_start = self._time_to_minutes(slot["start_time"])
            slot_end = self._time_to_minutes(slot["end_time"])
            
            # Check for overlap
            if not (end_mins <= slot_start or start_mins >= slot_end):
                return False
        
        return True
    
    def get_availability(self, date_str: str, appointment_type: str) -> AvailabilityResponse:
        """Get available time slots for a given date and appointment type"""
        
        # Validate date
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = dt_date.today()
            
            if date_obj < today:
                return AvailabilityResponse(
                    date=date_str,
                    day_of_week=self._get_day_name(date_str).capitalize(),
                    available_slots=[],
                    total_slots=0,
                    available_count=0
                )
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}")
        
        # Check if working day
        if not self._is_working_day(date_str):
            return AvailabilityResponse(
                date=date_str,
                day_of_week=self._get_day_name(date_str).capitalize(),
                available_slots=[],
                total_slots=0,
                available_count=0
            )
        
        # Get duration and buffer
        duration = self._get_appointment_duration(appointment_type)
        buffer = self.schedule["buffer_minutes"]
        slot_duration = duration + buffer
        
        # Generate slots
        sessions = self._get_working_sessions(date_str)
        all_slots = []
        
        for session in sessions:
            session_start = self._time_to_minutes(session["start"])
            session_end = self._time_to_minutes(session["end"])
            
            current = session_start
            while current + duration <= session_end:
                start_time = self._minutes_to_time(current)
                end_time = self._minutes_to_time(current + duration)
                
                is_available = self._is_slot_available(date_str, start_time, end_time)
                
                slot = TimeSlot(
                    start_time=start_time,
                    end_time=end_time,
                    available=is_available,
                    appointment_id=None
                )
                all_slots.append(slot)
                
                current += slot_duration
        
        available_count = sum(1 for slot in all_slots if slot.available)
        
        return AvailabilityResponse(
            date=date_str,
            day_of_week=self._get_day_name(date_str).capitalize(),
            available_slots=all_slots,
            total_slots=len(all_slots),
            available_count=available_count
        )
    
    def _generate_booking_id(self) -> str:
        """Generate unique booking ID"""
        date_part = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.digits, k=4))
        return f"APPT-{date_part}-{random_part}"
    
    def _generate_confirmation_code(self) -> str:
        """Generate confirmation code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def book_appointment(self, booking_request: BookingRequest) -> BookingResponse:
        """Book an appointment"""
        
        date_str = booking_request.date
        start_time = booking_request.start_time
        appointment_type = booking_request.appointment_type.value
        
        # Validate date is not in the past
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        if date_obj < dt_date.today():
            raise ValueError("Cannot book appointments in the past")
        
        # Check if it's a working day
        if not self._is_working_day(date_str):
            raise ValueError(f"Clinic is closed on {date_str}")
        
        # Calculate end time
        duration = self._get_appointment_duration(appointment_type)
        start_mins = self._time_to_minutes(start_time)
        end_time = self._minutes_to_time(start_mins + duration)
        
        # Check if slot is available
        if not self._is_slot_available(date_str, start_time, end_time):
            raise ValueError(f"Time slot {start_time} is not available")
        
        # Check if within working hours
        sessions = self._get_working_sessions(date_str)
        in_session = False
        for session in sessions:
            session_start = self._time_to_minutes(session["start"])
            session_end = self._time_to_minutes(session["end"])
            end_mins = self._time_to_minutes(end_time)
            
            if session_start <= start_mins and end_mins <= session_end:
                in_session = True
                break
        
        if not in_session:
            raise ValueError(f"Time slot {start_time} is outside working hours")
        
        # Generate booking details
        booking_id = self._generate_booking_id()
        confirmation_code = self._generate_confirmation_code()
        
        # Create appointment record
        appointment = {
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "status": "confirmed",
            "appointment_type": appointment_type,
            "date": date_str,
            "start_time": start_time,
            "end_time": end_time,
            "patient": {
                "name": booking_request.patient.name,
                "email": booking_request.patient.email,
                "phone": booking_request.patient.phone
            },
            "reason": booking_request.reason,
            "created_at": datetime.now().isoformat(),
            "clinic": "HealthCare Plus Clinic",
            "doctor": "Dr. Rajendra Kumar Gupta"
        }
        
        # Save booking
        self.bookings["appointments"].append(appointment)
        self._save_bookings()
        
        # Prepare response
        type_info = self.schedule["appointment_types"][appointment_type]
        
        return BookingResponse(
            booking_id=booking_id,
            status="confirmed",
            confirmation_code=confirmation_code,
            details={
                "date": date_str,
                "day": self._get_day_name(date_str).capitalize(),
                "time": start_time,
                "duration": f"{type_info['duration_minutes']} minutes",
                "appointment_type": type_info["name"],
                "patient_name": booking_request.patient.name,
                "patient_email": booking_request.patient.email,
                "patient_phone": booking_request.patient.phone,
                "reason": booking_request.reason,
                "doctor": "Dr. Rajendra Kumar Gupta",
                "clinic": "HealthCare Plus Clinic",
                "address": "302 Old Palasia, Indore, MP 452001",
                "clinic_phone": "+91-731-555-0100"
            },
            message=f"Your appointment has been confirmed for {date_str} at {start_time}. Confirmation code: {confirmation_code}"
        )
    
    def get_booking_by_id(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """Get booking details by ID"""
        for appt in self.bookings["appointments"]:
            if appt["booking_id"] == booking_id:
                return appt
        return None
    
    def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a booking"""
        for appt in self.bookings["appointments"]:
            if appt["booking_id"] == booking_id:
                appt["status"] = "cancelled"
                appt["cancelled_at"] = datetime.now().isoformat()
                self._save_bookings()
                return True
        return False


# Singleton instance
calendly_api = CalendlyIntegration()