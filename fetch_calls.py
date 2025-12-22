# import requests
# import json
# from datetime import datetime
# import os

# class VoiceAIExtractor:
#     def __init__(self, api_key, location_id):
#         """
#         Initialize the Voice AI extractor
        
#         Args:
#             api_key: Your GoHighLevel API key or Private Integration token
#             location_id: Your location (sub-account) ID
#         """
#         self.api_key = api_key
#         self.location_id = location_id
#         self.base_url = "https://services.leadconnectorhq.com"
#         self.headers = {
#             "Authorization": f"Bearer {api_key}",
#             "Content-Type": "application/json",
#             "Version": "2021-07-28"
#         }
    
#     def get_call_logs(self, agent_id=None, start_date=None, end_date=None, page=1):
#         """
#         Retrieve call logs from Voice AI
        
#         Args:
#             agent_id: Optional - Filter by specific agent ID
#             start_date: Optional - Start date (YYYY-MM-DD)
#             end_date: Optional - End date (YYYY-MM-DD)
#             page: Page number for pagination (default: 1)
#         """
#         url = f"{self.base_url}/voice-ai/dashboard/call-logs"
        
#         params = {
#             "locationId": self.location_id
#         }
        
#         # Add optional filters
#         if agent_id:
#             params["agentId"] = agent_id
#         if start_date:
#             params["startDate"] = start_date
#         if end_date:
#             params["endDate"] = end_date
#         if page > 1:
#             params["page"] = page
        
#         try:
#             response = requests.get(url, headers=self.headers, params=params)
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             print(f"Error fetching call logs: {e}")
#             if hasattr(e.response, 'text'):
#                 print(f"Response: {e.response.text}")
#             return None
    
#     def get_single_call_log(self, call_id):
#         """
#         Get detailed information about a specific call
        
#         Args:
#             call_id: The ID of the call to retrieve
#         """
#         url = f"{self.base_url}/voice-ai/dashboard/call-logs/{call_id}"
        
#         params = {
#             "locationId": self.location_id
#         }
        
#         try:
#             response = requests.get(url, headers=self.headers, params=params)
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             print(f"Error fetching call log {call_id}: {e}")
#             return None
    
#     def save_to_json(self, data, filename):
#         """Save data to a JSON file"""
#         os.makedirs('call_data', exist_ok=True)
#         filepath = os.path.join('call_data', filename)
        
#         with open(filepath, 'w', encoding='utf-8') as f:
#             json.dump(data, f, indent=2, ensure_ascii=False)
        
#         print(f"Data saved to: {filepath}")
#         return filepath
    
#     def save_transcripts_to_text(self, call_logs):
#         """Extract and save transcripts to individual text files"""
#         os.makedirs('call_data/transcripts', exist_ok=True)
        
#         if not call_logs or 'data' not in call_logs:
#             print("No call logs found")
#             return
        
#         for call in call_logs['data']:
#             call_id = call.get('id', 'unknown')
            
#             # Get full call details to ensure we have transcript
#             full_call = self.get_single_call_log(call_id)
            
#             if full_call and 'transcript' in full_call:
#                 timestamp = call.get('createdAt', datetime.now().isoformat())
#                 filename = f"transcript_{call_id}_{timestamp.replace(':', '-')}.txt"
#                 filepath = os.path.join('call_data/transcripts', filename)
                
#                 with open(filepath, 'w', encoding='utf-8') as f:
#                     f.write(f"Call ID: {call_id}\n")
#                     f.write(f"Date: {timestamp}\n")
#                     f.write(f"Agent: {call.get('agentName', 'N/A')}\n")
#                     f.write(f"Contact: {call.get('contactName', 'N/A')}\n")
#                     f.write(f"Duration: {call.get('duration', 'N/A')} seconds\n")
#                     f.write("\n" + "="*50 + "\n")
#                     f.write("TRANSCRIPT:\n")
#                     f.write("="*50 + "\n\n")
#                     f.write(full_call['transcript'])
                
#                 print(f"Transcript saved: {filename}")
    
#     def extract_all_calls(self, agent_id=None):
#         """
#         Extract all calls and save them
        
#         Args:
#             agent_id: Optional - Filter by specific agent ID
#         """
#         print("Fetching call logs...")
#         call_logs = self.get_call_logs(agent_id=agent_id)
        
#         if not call_logs:
#             print("Failed to fetch call logs")
#             return
        
#         # Save complete call logs as JSON
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         self.save_to_json(call_logs, f"call_logs_{timestamp}.json")
        
#         # Extract and save transcripts
#         print("\nExtracting transcripts...")
#         self.save_transcripts_to_text(call_logs)
        
#         print("\n✅ Extraction complete!")
#         print(f"Total calls retrieved: {len(call_logs.get('data', []))}")


# # ============= USAGE EXAMPLE =============

# if __name__ == "__main__":
#     API_KEY = "pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324" 
#     LOCATION_ID = "M5jnxd1r8yq3o5gxSYOP" 
    
#     AGENT_ID = "693448f6231659c2a32a3bca" 
    
#     # Initialize extractor
#     extractor = VoiceAIExtractor(API_KEY, LOCATION_ID)
    
#     # Extract all calls
#     extractor.extract_all_calls(agent_id=AGENT_ID)
    
#     # ===== Alternative: Get specific date range =====
#     # call_logs = extractor.get_call_logs(
#     #     start_date="2025-01-01",
#     #     end_date="2025-12-20"
#     # )
    
#     # ===== Alternative: Get single call details =====
#     # call_details = extractor.get_single_call_log("specific_call_id")
#     # extractor.save_to_json(call_details, "single_call.json")



# ///////////////
import requests
import json
from datetime import datetime
import os
import re

class VoiceAIExtractor:
    def __init__(self, api_key, location_id):
        self.api_key = api_key
        self.location_id = location_id
        self.base_url = "https://services.leadconnectorhq.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
    
    def get_call_logs(self, agent_id=None):
        """Retrieve call logs from Voice AI"""
        url = f"{self.base_url}/voice-ai/dashboard/call-logs"
        
        params = {
            "locationId": self.location_id
        }
        
        if agent_id:
            params["agentId"] = agent_id
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching call logs: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def parse_transcript(self, transcript):
        """Parse transcript to extract bot questions and human answers"""
        lines = transcript.split('\n')
        
        qa_pairs = []
        current_question = []
        current_answer = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('bot:'):
                # If we have a previous Q&A pair, save it
                if current_question and current_answer:
                    qa_pairs.append({
                        'question': ' '.join(current_question),
                        'answer': ' '.join(current_answer)
                    })
                    current_answer = []
                
                # Start new question
                question_text = line[4:].strip()  # Remove 'bot:' prefix
                current_question.append(question_text)
                
            elif line.startswith('human:'):
                # Add to current answer
                answer_text = line[6:].strip()  # Remove 'human:' prefix
                if answer_text:  # Only add non-empty answers
                    current_answer.append(answer_text)
        
        # Add the last Q&A pair if exists
        if current_question and current_answer:
            qa_pairs.append({
                'question': ' '.join(current_question),
                'answer': ' '.join(current_answer)
            })
        
        return qa_pairs
    
    def extract_recent_call_qa(self, agent_id=None):
        """Extract Q&A from the most recent call"""
        print("Fetching call logs...")
        call_logs = self.get_call_logs(agent_id=agent_id)
        
        if not call_logs or 'callLogs' not in call_logs:
            print("No call logs found")
            return None
        
        # Get the most recent call (first in the list)
        recent_call = call_logs['callLogs'][0]
        
        print(f"\n Most Recent Call Details:")
        print(f"   Date: {recent_call['createdAt']}")
        print(f"   Duration: {recent_call['duration']} seconds")
        print(f"   Call ID: {recent_call['id']}")
        print(f"\n{'='*60}\n")
        
        # Parse the transcript
        transcript = recent_call.get('transcript', '')
        qa_pairs = self.parse_transcript(transcript)
        
        # Display Q&A
        print(" INTERVIEW QUESTIONS & ANSWERS:\n")
        for i, qa in enumerate(qa_pairs, 1):
            print(f"Q{i}: {qa['question']}")
            print(f"A{i}: {qa['answer']}")
            print()
        
        # Save to file
        self.save_qa_to_file(qa_pairs, recent_call)
        
        return qa_pairs
    
    def save_qa_to_file(self, qa_pairs, call_info):
        """Save Q&A to a text file"""
        os.makedirs('call_data', exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"call_data/recent_call_qa_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("MOST RECENT CALL - INTERVIEW Q&A\n")
            f.write("="*60 + "\n\n")
            f.write(f"Call Date: {call_info['createdAt']}\n")
            f.write(f"Duration: {call_info['duration']} seconds\n")
            f.write(f"Call ID: {call_info['id']}\n\n")
            f.write("="*60 + "\n\n")
            
            for i, qa in enumerate(qa_pairs, 1):
                f.write(f"Question {i}:\n{qa['question']}\n\n")
                f.write(f"Answer {i}:\n{qa['answer']}\n\n")
                f.write("-"*60 + "\n\n")
        
        print(f"✅ Q&A saved to: {filename}")
        
        # Also save as JSON for easy parsing
        json_filename = f"call_data/recent_call_qa_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'call_info': {
                    'date': call_info['createdAt'],
                    'duration': call_info['duration'],
                    'call_id': call_info['id']
                },
                'qa_pairs': qa_pairs
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Q&A saved to: {json_filename}")


# ============= USAGE =============

if __name__ == "__main__":
    API_KEY = "pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324" 
    LOCATION_ID = "M5jnxd1r8yq3o5gxSYOP" 
    AGENT_ID = "693448f6231659c2a32a3bca" 
    
    # Initialize extractor
    extractor = VoiceAIExtractor(API_KEY, LOCATION_ID)
    
    # Extract Q&A from most recent call
    qa_pairs = extractor.extract_recent_call_qa(agent_id=AGENT_ID)