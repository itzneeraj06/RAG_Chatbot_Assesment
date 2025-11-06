import json
import os
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings


class VectorStore:
    """ChromaDB vector store for FAQ system"""
    
    def __init__(self, persist_directory: str = "./data/vectordb"):
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Get or create collection
        self.collection_name = "clinic_faq"
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"✓ Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "HealthCare Plus Clinic FAQ"}
            )
            print(f"✓ Created new collection: {self.collection_name}")
    
    def _flatten_clinic_info(self, clinic_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten nested clinic info into searchable chunks"""
        chunks = []
        
        # Clinic Details
        if "clinic_details" in clinic_data:
            details = clinic_data["clinic_details"]
            text = f"Clinic: {details['name']}. Doctor: {details['doctor']}, {details['specialization']}. "
            text += f"Experience: {details['experience']}. "
            text += f"Address: {details['address']}. Phone: {details['phone']}. Email: {details['email']}"
            chunks.append({
                "id": "clinic_basic_info",
                "text": text,
                "category": "clinic_details",
                "metadata": details
            })
        
        # Location and Directions
        if "location_and_directions" in clinic_data:
            loc = clinic_data["location_and_directions"]
            text = f"Clinic location: {loc['address']}. Landmark: {loc['landmark']}. "
            text += f"Directions: {loc['directions']} "
            text += f"Parking: {loc['parking']} "
            text += f"Public transport: {loc['public_transport']} "
            text += f"Accessibility: {loc['accessibility']}"
            chunks.append({
                "id": "location_directions",
                "text": text,
                "category": "location",
                "metadata": loc
            })
        
        # Hours of Operation
        if "hours_of_operation" in clinic_data:
            hours = clinic_data["hours_of_operation"]
            text = f"Clinic hours: Monday to Friday: {hours['monday_to_friday']}. "
            text += f"Saturday: {hours['saturday']}. Sunday: {hours['sunday']}. "
            text += f"Holidays: {hours['holidays']}. {hours['emergency_note']}"
            chunks.append({
                "id": "hours_of_operation",
                "text": text,
                "category": "hours",
                "metadata": hours
            })
        
        # Insurance and Billing
        if "insurance_and_billing" in clinic_data:
            ins = clinic_data["insurance_and_billing"]
            text = "Accepted insurance: " + ", ".join(ins['accepted_insurance']) + ". "
            text += "Payment methods: " + ", ".join(ins['payment_methods']) + ". "
            text += f"Billing policy: {ins['billing_policy']}"
            chunks.append({
                "id": "insurance_billing",
                "text": text,
                "category": "insurance",
                "metadata": ins
            })
            
            # Consultation fees
            fees = ins['consultation_fees']
            fee_text = "Consultation fees: "
            fee_text += f"General consultation: {fees['general_consultation']}, "
            fee_text += f"Follow-up visit: {fees['followup_visit']}, "
            fee_text += f"Specialist consultation: {fees['specialist_consultation']}, "
            fee_text += f"Physical exam: {fees['physical_exam']}"
            chunks.append({
                "id": "consultation_fees",
                "text": fee_text,
                "category": "fees",
                "metadata": fees
            })
        
        # Visit Preparation
        if "visit_preparation" in clinic_data:
            prep = clinic_data["visit_preparation"]
            
            text = "First visit requirements: " + ", ".join(prep['first_visit_requirements'])
            chunks.append({
                "id": "first_visit_requirements",
                "text": text,
                "category": "preparation",
                "metadata": {"items": prep['first_visit_requirements']}
            })
            
            text = "What to bring: " + ", ".join(prep['what_to_bring'])
            chunks.append({
                "id": "what_to_bring",
                "text": text,
                "category": "preparation",
                "metadata": {"items": prep['what_to_bring']}
            })
            
            text = "Before appointment: " + ", ".join(prep['before_appointment'])
            chunks.append({
                "id": "before_appointment",
                "text": text,
                "category": "preparation",
                "metadata": {"items": prep['before_appointment']}
            })
        
        # Policies
        if "policies" in clinic_data:
            policies = clinic_data["policies"]
            
            # Cancellation
            if "cancellation_policy" in policies:
                cancel = policies["cancellation_policy"]
                text = f"Cancellation policy: {cancel['notice_required']} notice required. "
                text += f"Fee: {cancel['cancellation_fee']} "
                text += f"How to cancel: {cancel['how_to_cancel']} "
                text += f"Rescheduling: {cancel['rescheduling']}"
                chunks.append({
                    "id": "cancellation_policy",
                    "text": text,
                    "category": "policy",
                    "metadata": cancel
                })
            
            # Late arrival
            if "late_arrival_policy" in policies:
                late = policies["late_arrival_policy"]
                text = f"Late arrival policy: {late['grace_period']} grace period. "
                text += f"{late['after_grace_period']} "
                text += f"Recommendation: {late['recommendation']}"
                chunks.append({
                    "id": "late_arrival_policy",
                    "text": text,
                    "category": "policy",
                    "metadata": late
                })
            
            # Prescription refill
            if "prescription_refill" in policies:
                rx = policies["prescription_refill"]
                text = f"Prescription refill: {rx['process']}. "
                text += f"Pickup: {rx['pickup']}. "
                text += f"Controlled substances: {rx['controlled_substances']}"
                chunks.append({
                    "id": "prescription_refill",
                    "text": text,
                    "category": "policy",
                    "metadata": rx
                })
            
            # Medical records
            if "medical_records" in policies:
                records = policies["medical_records"]
                text = f"Medical records: {records['request_process']}. "
                text += f"Processing time: {records['processing_time']}. "
                text += f"Fees: {records['fees']}. "
                text += f"Digital access: {records['digital_access']}"
                chunks.append({
                    "id": "medical_records",
                    "text": text,
                    "category": "policy",
                    "metadata": records
                })
        
        # COVID-19 Protocols
        if "covid19_protocols" in clinic_data:
            covid = clinic_data["covid19_protocols"]
            text = "COVID-19 safety measures: " + ", ".join(covid['safety_measures']) + ". "
            text += f"Vaccination status: {covid['vaccination_status']}. "
            text += f"Symptoms policy: {covid['symptoms_policy']}. "
            text += f"Telemedicine: {covid['telemedicine']}"
            chunks.append({
                "id": "covid19_protocols",
                "text": text,
                "category": "covid",
                "metadata": covid
            })
        
        # Services Offered
        if "services_offered" in clinic_data:
            services = clinic_data["services_offered"]
            
            text = "General services: " + ", ".join(services['general_services'])
            chunks.append({
                "id": "general_services",
                "text": text,
                "category": "services",
                "metadata": {"services": services['general_services']}
            })
            
            text = "Diagnostic services: " + ", ".join(services['diagnostic_services'])
            chunks.append({
                "id": "diagnostic_services",
                "text": text,
                "category": "services",
                "metadata": {"services": services['diagnostic_services']}
            })
        
        # Appointment Types
        if "appointment_types" in clinic_data:
            for appt_key, appt_data in clinic_data["appointment_types"].items():
                text = f"{appt_data['description']}. Duration: {appt_data['duration']}. Fee: {appt_data['fee']}"
                chunks.append({
                    "id": f"appointment_type_{appt_key}",
                    "text": text,
                    "category": "appointment_types",
                    "metadata": appt_data
                })
        
        # FAQs
        if "frequently_asked_questions" in clinic_data:
            for idx, faq in enumerate(clinic_data["frequently_asked_questions"]):
                text = f"Question: {faq['question']} Answer: {faq['answer']}"
                chunks.append({
                    "id": f"faq_{idx}",
                    "text": text,
                    "category": "faq",
                    "metadata": faq
                })
        
        # Contact Information
        if "contact_information" in clinic_data:
            contact = clinic_data["contact_information"]
            text = f"Contact: Appointments: {contact['appointments']}. "
            text += f"General inquiries: {contact['general_inquiries']}. "
            text += f"Emergency: {contact['emergency']}. "
            text += f"WhatsApp: {contact['whatsapp']}"
            chunks.append({
                "id": "contact_information",
                "text": text,
                "category": "contact",
                "metadata": contact
            })
        
        return chunks
    
    def initialize_from_json(self, json_file_path: str):
        """Load clinic info from JSON and store in vector DB"""
        
        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            clinic_data = json.load(f)
        
        # Flatten into chunks
        chunks = self._flatten_clinic_info(clinic_data)
        
        # Clear existing data
        try:
            self.collection.delete(where={})
        except:
            pass
        
        # Add to collection
        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [{"category": chunk["category"]} for chunk in chunks]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✓ Initialized vector store with {len(chunks)} chunks")
        return len(chunks)
    
    def search(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant information"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "category": results['metadatas'][0][i]['category'],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    def get_collection_count(self) -> int:
        """Get number of documents in collection"""
        return self.collection.count()


# Initialize on import (singleton pattern)
vector_store = VectorStore()


# CLI tool to initialize the database
if __name__ == "__main__":
    print("Initializing vector store...")
    clinic_info_path = "data/clinic_info.json"
    
    if not os.path.exists(clinic_info_path):
        print(f"Error: {clinic_info_path} not found")
        exit(1)
    
    count = vector_store.initialize_from_json(clinic_info_path)
    print(f"\n✓ Successfully initialized vector store")
    print(f"✓ Total chunks: {count}")
    print(f"✓ Collection count: {vector_store.get_collection_count()}")
    
    # Test search
    print("\n--- Test Search ---")
    test_query = "What insurance do you accept?"
    results = vector_store.search(test_query, n_results=2)
    print(f"\nQuery: {test_query}")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Category: {result['category']}")
        print(f"   Text: {result['text'][:100]}...")