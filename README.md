# Medical Appointment Scheduling Agent
An intelligent conversational agent that helps patients schedule medical appointments and answers frequently asked questions using RAG (Retrieval-Augmented Generation).

## Clinic Information
- **Clinic Name**: HealthCare Plus Clinic
- **Doctor**: Dr. Rajendra Kumar Gupta, M.D.
- **Location**: 302 Old Palasia, Indore, MP 452001
- **Phone**: +91-731-555-0100
- **Email**: info@healthcareplus.com

## Features
### Core Feature 1: Calendly Integration
- Mock Calendly API for appointment scheduling
- Multiple appointment types with correct durations:
  - General Consultation: 30 minutes
  - Follow-up: 15 minutes
  - Physical Exam: 45 minutes
  - Specialist Consultation: 60 minutes
- Smart availability detection
- Conflict prevention (no double-booking)
  -Time slot recommendations based on preferences

### Core Feature 2: FAQ System (RAG)
- ChromaDB vector database for FAQ storage
- OpenAI embeddings for semantic search
- Accurate answers grounded in clinic information
- Context continuity across multiple questions
- No hallucination (answers only from knowledge base)

### Intelligent Agent
- Natural, empathetic conversation flow
- Seamless context switching (FAQ ↔ Scheduling)
- Tool calling for availability checks and bookings
- Edge case handling (no slots, invalid dates, API failures)
- Smart slot recommendations based on preferences

## Architecture

```
User Request → FastAPI → Scheduling Agent
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
            RAG System              Calendly API
          (ChromaDB + GPT)         (Mock Backend)
                    ↓                   ↓
              FAQ Answer         Available Slots
                    ↓                   ↓
                    └─────────┬─────────┘
                              ↓
                      Natural Response
```

## Project Structur

```
appointment-scheduling-agent/
├── README.md
├── .env
├── requirements.txt
├── backend/
│   ├── main.py
│   ├── agent/
│   │   ├── scheduling_agent.py
│   │   └── prompts.py
│   ├── rag/
│   │   ├── faq_rag.py
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   ├── api/
│   │   ├── chat.py
│   │   └── calendly_integration.py
│   ├── tools/
│   │   ├── availability_tool.py
│   │   └── booking_tool.py
│   └── models/
│       └── schemas.py
|── data/
    ├── clinic_info.json
    ├── doctor_schedule.json
    └── bookings.json

```

## Setup Instructions

### Prerequisites
- Python 3.10+
- OpenAI API Key
- pip package manager

### Installation

1. **Clone the repository**

git clone https://github.com/itzneeraj06/mufadar-doorways-showcase.git
cd appointment-scheduling-agent

2. **Create virtual environment**

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install dependencies**

pip install -r requirements.txt


4. **Set up environment variables**
.env
add your OPENAI_API_KEY in env file

5. **Initialize the vector database**
python backend/rag/vector_store.py

6. **Run the application**

uvicorn backend.main:app --reload --port 8000

The API will be available at `http://localhost:8000`

## API Documentation

### Interactive Docs
- Swagger UI: `http://localhost:8000/docs`

### Main Endpoints

#### 1. **POST /api/chat**
Main conversational endpoint for scheduling and FAQ


## System Design

### Agent Conversation Flow
1. **Understanding Phase**: Greet and understand patient needs
2. **Classification**: Determine if FAQ or scheduling request
3. **Tool Execution**: Call appropriate tools (RAG search or availability check)
4. **Slot Recommendation**: Suggest 3-5 slots based on preferences
5. **Information Collection**: Gather patient details
6. **Confirmation**: Confirm and book appointment

### RAG Pipeline for FAQs
1. **Ingestion**: Load clinic_info.json into ChromaDB
2. **Embedding**: Use OpenAI text-embedding-3-small
3. **Retrieval**: Semantic search with top-k=3
4. **Generation**: GPT-4 generates grounded answers
5. **Validation**: Ensure no hallucination

### Scheduling Logic
- **Available Slots Determination**: Check doctor schedule vs existing bookings
- **Appointment Type Handling**: Match duration with slot availability
- **Conflict Prevention**: Validate no overlapping appointments
- **Buffer Time**: 5-minute buffer between appointments
- **Business Hours**: Mon-Sat, 9:00 AM - 6:00 PM (lunch 1-2 PM)

### Tool Calling Strategy
The agent uses OpenAI function calling with these tools:
- `check_availability`: Get available slots for date/type
- `book_appointment`: Create confirmed booking
- `search_faq`: Semantic search in knowledge base
- `get_booking_details`: Retrieve existing appointment info

## Edge Cases Covered

### No Available Slots
- Clearly explain situation
- Offer alternative dates
- Suggest calling office for urgent needs

### User Changes Mind
- Handle gracefully mid-booking
- Allow conversation restart
- Maintain context appropriately

### Ambiguous Time References
- "Tomorrow morning" → Clarify specific time
- "Next week" → Confirm which day
- "Around 3" → Confirm AM/PM

### Invalid Input
- Non-existent dates
- Past dates
- Outside business hours
- Proper error messages

### API Failures
- Graceful degradation
- Informative error messages
- Fallback suggestions
