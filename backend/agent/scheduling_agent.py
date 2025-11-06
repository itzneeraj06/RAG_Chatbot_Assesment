import json
import os
from typing import Dict, Any, List
from openai import OpenAI
from backend.agent.prompts import SYSTEM_PROMPT, TOOL_DESCRIPTIONS
from backend.tools.availability_tool import check_availability
from backend.tools.booking_tool import book_appointment
from backend.rag.faq_rag import faq_system


class SchedulingAgent:
    """Intelligent conversational agent for medical appointment scheduling"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
        
        # Session storage for conversation context
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
    
    def _get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]
    
    def _add_to_session(self, session_id: str, role: str, content: str):
        """Add message to session history"""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({
            "role": role,
            "content": content
        })
        
        # Keep only last 20 messages to manage context length
        if len(self.sessions[session_id]) > 20:
            self.sessions[session_id] = self.sessions[session_id][-20:]
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        
        if tool_name == "search_faq":
            question = arguments.get("question", "")
            faq_response = faq_system.answer_question(question)
            return {
                "answer": faq_response.answer,
                "confidence": faq_response.confidence,
                "sources": faq_response.sources
            }
        
        elif tool_name == "check_availability":
            date = arguments.get("date")
            appointment_type = arguments.get("appointment_type")
            return check_availability(date, appointment_type)
        
        elif tool_name == "book_appointment":
            return book_appointment(
                date=arguments.get("date"),
                start_time=arguments.get("start_time"),
                appointment_type=arguments.get("appointment_type"),
                patient_name=arguments.get("patient_name"),
                patient_email=arguments.get("patient_email"),
                patient_phone=arguments.get("patient_phone"),
                reason=arguments.get("reason")
            )
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def chat(self, message: str, session_id: str) -> Dict[str, Any]:
        """
        Process a chat message and return response
        
        Args:
            message: User's message
            session_id: Session identifier for conversation context
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Get conversation history
            history = self._get_session_history(session_id)
            # Build messages for API call
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            
            # Add conversation history
            messages.extend(history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            # Make API call with tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_DESCRIPTIONS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000
            )
            print("--------->",response)
            assistant_message = response.choices[0].message
            # Handle tool calls
            if assistant_message.tool_calls:
                # Add assistant message with tool calls to history
                self._add_to_session(session_id, "assistant", assistant_message.content or "")
                
                # Execute tools and collect results
                tool_results = []
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    print(f"🔧 Executing tool: {tool_name} with args: {tool_args}")
                    
                    tool_result = self._execute_tool(tool_name, tool_args)
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(tool_result)
                    })
                
                # Make second API call with tool results
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })
                
                for tool_result in tool_results:
                    messages.append(tool_result)
                
                # Get final response
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                final_message = final_response.choices[0].message.content
                
                # Add to session
                self._add_to_session(session_id, "user", message)
                self._add_to_session(session_id, "assistant", final_message)
                
                return {
                    "response": final_message,
                    "session_id": session_id,
                    "tool_calls": [tc.function.name for tc in assistant_message.tool_calls]
                }
            
            else:
                # No tool calls, just return response
                response_text = assistant_message.content
                
                # Add to session
                self._add_to_session(session_id, "user", message)
                self._add_to_session(session_id, "assistant", response_text)
                
                return {
                    "response": response_text,
                    "session_id": session_id,
                    "tool_calls": []
                }
        
        except Exception as e:
            print(f"❌ Error in chat: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Please try again or call us at +91-731-555-0100 for immediate assistance.",
                "session_id": session_id,
                "error": str(e)
            }
    
    def reset_session(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a session"""
        history = self._get_session_history(session_id)
        return {
            "session_id": session_id,
            "message_count": len(history),
            "last_messages": history[-5:] if history else []
        }


# Singleton instance
agent = SchedulingAgent()