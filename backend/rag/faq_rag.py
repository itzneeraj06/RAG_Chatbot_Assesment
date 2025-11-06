from openai import OpenAI
import os
from typing import List, Dict, Any, Optional
from backend.rag.vector_store import vector_store
from backend.models.schemas import FAQRequest, FAQResponse
from dotenv import load_dotenv
load_dotenv()

class FAQSystem:
    """RAG-based FAQ system for clinic information"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
        self.vector_store = vector_store
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for FAQ answering"""
        return """You are a helpful medical clinic assistant for HealthCare Plus Clinic. 

Your role is to answer patient questions about the clinic using ONLY the information provided in the context. 

Key guidelines:
- Be warm, friendly, and professional
- Answer accurately based on the provided context
- If information is not in the context, politely say you don't have that information and suggest calling the clinic
- Keep answers concise but complete
- Use natural, conversational language
- If asked about booking appointments, mention they can schedule through the chat or call the clinic
- Never make up information or provide medical advice

Clinic Details:
- Name: HealthCare Plus Clinic
- Doctor: Dr. Rajendra Kumar Gupta, M.D.
- Location: 302 Old Palasia, Indore, MP 452001
- Phone: +91-731-555-0100
- Email: info@healthcareplus.com"""
    
    def _retrieve_context(self, question: str, n_results: int = 3) -> tuple[str, List[str], List[str]]:
        """Retrieve relevant context from vector store"""
        results = self.vector_store.search(question, n_results=n_results)
        
        if not results:
            return "", [], []
        
        # Combine retrieved texts
        context_parts = []
        sources = []
        chunks = []
        
        for result in results:
            context_parts.append(result["text"])
            sources.append(result["id"])
            chunks.append(result["text"])
        
        context = "\n\n".join(context_parts)
        return context, sources, chunks
    
    def _calculate_confidence(self, answer: str, context: str) -> float:
        """Calculate confidence score based on answer quality"""
        # Simple heuristic: if answer is substantial and context was provided
        if not context:
            return 0.3
        
        if len(answer) < 20:
            return 0.5
        
        if "I don't have" in answer or "not sure" in answer or "don't know" in answer:
            return 0.4
        
        # If answer seems complete
        if len(answer) > 50:
            return 0.9
        
        return 0.7
    
    def answer_question(self, question: str, include_sources: bool = False) -> FAQResponse:
        """Answer a question using RAG"""
        
        # Retrieve relevant context
        context, sources, chunks = self._retrieve_context(question)
        
        if not context:
            return FAQResponse(
                answer="I don't have specific information about that in my knowledge base. Please call us at +91-731-555-0100 or email info@healthcareplus.com for assistance.",
                sources=[],
                confidence=0.3,
                retrieved_chunks=[] if include_sources else None
            )
        
        # Create prompt
        user_prompt = f"""Context information from our clinic database:

{context}

Patient question: {question}

Please provide a helpful, accurate answer based on the context above."""
        
        # Get response from LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._create_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            confidence = self._calculate_confidence(answer, context)
            
            return FAQResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                retrieved_chunks=chunks if include_sources else None
            )
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return FAQResponse(
                answer="I apologize, but I'm having trouble accessing information right now. Please call us at +91-731-555-0100 for assistance.",
                sources=[],
                confidence=0.1,
                retrieved_chunks=[] if include_sources else None
            )
    
    def handle_multi_turn_question(
        self, 
        question: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> FAQResponse:
        """Handle questions with conversation context"""
        
        if not conversation_history:
            return self.answer_question(question)
        
        # Enhance question with conversation context
        context_summary = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in conversation_history[-3:]  # Last 3 messages
        ])
        
        enhanced_question = f"Previous conversation:\n{context_summary}\n\nCurrent question: {question}"
        
        # Retrieve context
        context, sources, chunks = self._retrieve_context(enhanced_question)
        
        if not context:
            return FAQResponse(
                answer="I don't have specific information about that. Please call +91-731-555-0100 for assistance.",
                sources=[],
                confidence=0.3,
                retrieved_chunks=[]
            )
        
        # Create messages with conversation history
        messages = [{"role": "system", "content": self._create_system_prompt()}]
        
        # Add conversation history
        for msg in conversation_history[-3:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current question with context
        messages.append({
            "role": "user",
            "content": f"Context: {context}\n\nQuestion: {question}"
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            confidence = self._calculate_confidence(answer, context)
            
            return FAQResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                retrieved_chunks=chunks
            )
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return FAQResponse(
                answer="I'm having trouble right now. Please call +91-731-555-0100.",
                sources=[],
                confidence=0.1,
                retrieved_chunks=[]
            )


# Singleton instance
faq_system = FAQSystem()