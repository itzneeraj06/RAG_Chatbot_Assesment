import pytest
from datetime import datetime, timedelta
from backend.agent.scheduling_agent import agent
from backend.rag.faq_rag import faq_system
from backend.api.calendly_integration import calendly_api
from backend.models.schemas import BookingRequest, PatientInfo, AppointmentType


class TestFAQSystem:
    """Test FAQ/RAG functionality"""
    
    def test_insurance_question(self):
        """Test insurance-related FAQ"""
        response = faq_system.answer_question("What insurance do you accept?")
        assert "insurance" in response.answer.lower() or "star health" in response.answer.lower()
        assert response.confidence > 0.5
        assert len(response.sources) > 0
    
    def test_location_question(self):
        """Test location-related FAQ"""
        response = faq_system.answer_question("Where is the clinic located?")
        assert "palasia" in response.answer.lower() or "indore" in response.answer.lower()
        assert response.confidence > 0.5
    
    def test_hours_question(self):
        """Test clinic hours FAQ"""
        response = faq_system.answer_question("What are your clinic hours?")
        assert "9" in response.answer or "hours" in response.answer.lower()
        assert response.confidence > 0.5
    
    def test_parking_question(self):
        """Test parking information"""
        response = faq_system.answer_question("Is parking available?")
        assert "parking" in response.answer.lower()
        assert response.confidence > 0.5
    
    def test_unknown_question(self):
        """Test handling of unknown questions"""
        response = faq_system.answer_question("Do you sell pizza?")
        assert response.confidence < 0.6
        assert "don't have" in response.answer.lower() or "call" in response.answer.lower()


class TestCalendlyIntegration:
    """Test Calendly API functionality"""
    
    def test_get_availability_valid_date(self):
        """Test getting availability for a valid future date"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        availability = calendly_api.get_availability(tomorrow, "consultation")
        
        assert availability.date == tomorrow
        assert isinstance(availability.available_slots, list)
        assert availability.total_slots >= 0
    
    def test_get_availability_past_date(self):
        """Test that past dates return no slots"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        availability = calendly_api.get_availability(yesterday, "consultation")
        
        assert availability.available_count == 0
    
    def test_get_availability_sunday(self):
        """Test that Sunday (closed day) returns no slots"""
        # Find next Sunday
        today = datetime.now()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)
        
        availability = calendly_api.get_availability(
            next_sunday.strftime("%Y-%m-%d"), 
            "consultation"
        )
        
        assert availability.available_count == 0
    
    def test_book_appointment_success(self):
        """Test successful appointment booking"""
        # Find next available weekday
        tomorrow = datetime.now() + timedelta(days=1)
        while tomorrow.weekday() == 6:  # Skip Sunday
            tomorrow += timedelta(days=1)
        
        date_str = tomorrow.strftime("%Y-%m-%d")
        
        booking_request = BookingRequest(
            appointment_type=AppointmentType.CONSULTATION,
            date=date_str,
            start_time="10:00",
            patient=PatientInfo(
                name="Test Patient",
                email="test@example.com",
                phone="+91-9876543210"
            ),
            reason="Test appointment"
        )
        
        response = calendly_api.book_appointment(booking_request)
        
        assert response.status == "confirmed"
        assert response.booking_id.startswith("APPT-")
        assert len(response.confirmation_code) == 6
        assert response.details["patient_name"] == "Test Patient"
    
    def test_book_appointment_past_date(self):
        """Test that booking in the past fails"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        booking_request = BookingRequest(
            appointment_type=AppointmentType.CONSULTATION,
            date=yesterday,
            start_time="10:00",
            patient=PatientInfo(
                name="Test Patient",
                email="test@example.com",
                phone="+91-9876543210"
            ),
            reason="Test appointment"
        )
        
        with pytest.raises(ValueError):
            calendly_api.book_appointment(booking_request)


class TestSchedulingAgent:
    """Test conversational agent"""
    
    def test_greeting(self):
        """Test that agent responds to greetings"""
        response = agent.chat("Hello", "test_session_greeting")
        assert response["response"]
        assert len(response["response"]) > 0
    
    def test_faq_integration(self):
        """Test that agent handles FAQ questions"""
        response = agent.chat(
            "What insurance do you accept?", 
            "test_session_faq"
        )
        assert response["response"]
        assert "search_faq" in response.get("tool_calls", []) or "insurance" in response["response"].lower()
    
    def test_scheduling_request(self):
        """Test that agent handles scheduling requests"""
        response = agent.chat(
            "I need to book an appointment", 
            "test_session_schedule"
        )
        assert response["response"]
        assert any(word in response["response"].lower() for word in ["appointment", "visit", "help", "when"])
    
    def test_context_switching(self):
        """Test FAQ during scheduling flow"""
        session_id = "test_session_switch"
        
        # Start scheduling
        response1 = agent.chat("I want to book an appointment", session_id)
        assert response1["response"]
        
        # Ask FAQ
        response2 = agent.chat("What are your hours?", session_id)
        assert response2["response"]
        
        # Continue scheduling
        response3 = agent.chat("I'd like tomorrow afternoon", session_id)
        assert response3["response"]
    
    def test_session_management(self):
        """Test session history management"""
        session_id = "test_session_mgmt"
        
        agent.chat("Hello", session_id)
        agent.chat("I need help", session_id)
        
        info = agent.get_session_info(session_id)
        assert info["message_count"] > 0
        assert info["session_id"] == session_id
        
        agent.reset_session(session_id)
        info_after = agent.get_session_info(session_id)
        assert info_after["message_count"] == 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_invalid_date_format(self):
        """Test handling of invalid date format"""
        with pytest.raises(ValueError):
            calendly_api.get_availability("2024-13-45", "consultation")
    
    def test_invalid_appointment_type(self):
        """Test handling of invalid appointment type"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # This should fail during enum validation
        try:
            booking_request = BookingRequest(
                appointment_type="invalid_type",
                date=tomorrow,
                start_time="10:00",
                patient=PatientInfo(
                    name="Test",
                    email="test@example.com",
                    phone="+919876543210"
                ),
                reason="Test"
            )
            assert False, "Should have raised validation error"
        except:
            pass  # Expected to fail
    
    def test_double_booking_prevention(self):
        """Test that double booking is prevented"""
        tomorrow = datetime.now() + timedelta(days=2)
        while tomorrow.weekday() == 6:
            tomorrow += timedelta(days=1)
        
        date_str = tomorrow.strftime("%Y-%m-%d")
        
        # Book first appointment
        booking1 = BookingRequest(
            appointment_type=AppointmentType.CONSULTATION,
            date=date_str,
            start_time="11:00",
            patient=PatientInfo(
                name="Patient 1",
                email="patient1@example.com",
                phone="+919876543210"
            ),
            reason="First appointment"
        )
        calendly_api.book_appointment(booking1)
        
        # Try to book overlapping appointment
        booking2 = BookingRequest(
            appointment_type=AppointmentType.CONSULTATION,
            date=date_str,
            start_time="11:00",
            patient=PatientInfo(
                name="Patient 2",
                email="patient2@example.com",
                phone="+919876543211"
            ),
            reason="Second appointment"
        )
        
        with pytest.raises(ValueError):
            calendly_api.book_appointment(booking2)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])