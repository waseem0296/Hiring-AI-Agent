# """
# Complete Hiring Workflow Application
# Orchestrates: Applicant Screening -> Phone Interview -> Hireology Update -> Score Calculation
# """

# import os
# import json
# from datetime import datetime
# from dotenv import load_dotenv

# # Import from your existing files
# from fetch_applicants import (
#     get_candidates,
#     extract_applicant_ids,
#     get_candidate_documents,
#     build_single_applicant_record,
#     get_incomplete_questions,
#     send_incomplete_application_email,
#     decide_candidate_status,
#     get_rejection_reason,
#     send_rejection_email,
#     update_candidate_status,
#     write_single_record_to_csv
# )

# from formate_most_recent_callTranscript_to_Structured_json import HireologyQAExtractor

# from update_phoneInterview_on_Hireology import (
#     fetch_interview_from_api,
#     update_interview_answers,
#     send_update_to_hireology,
#     trigger_score_calculation,
#     display_update_logs
# )

# # Import the interview ID fetcher from the dedicated module
# from interview_id_fetcher import fetch_interview_id

# load_dotenv()


# class HiringWorkflowOrchestrator:
#     """Orchestrates the complete hiring workflow"""
    
#     def __init__(self, config: dict):
#         """
#         Initialize with configuration
        
#         config should contain:
#         - hireology_jwt: Hireology JWT token
#         - hireology_job_id: Job ID in Hireology
#         - ghl_api_key: GoHighLevel API key
#         - ghl_location_id: GoHighLevel location ID
#         - ghl_agent_id: GoHighLevel agent ID
#         - groq_api_key: Groq API key (optional)
#         - interview_template_id: Interview template ID (optional, default: 512090)
#         """
#         self.config = config
#         self.results = {
#             'timestamp': datetime.now().isoformat(),
#             'steps_completed': [],
#             'errors': []
#         }
    
#     def step1_screen_applicants(self):
#         """Step 1: Screen all applicants for a job"""
#         print("\n" + "="*80)
#         print("STEP 1: SCREENING APPLICANTS")
#         print("="*80)
        
#         try:
#             jwt = self.config['hireology_jwt']
#             job_id = self.config['hireology_job_id']
            
#             # Fetch candidates
#             print(f"\n🔍 Fetching candidates for job {job_id}...")
#             candidates = get_candidates(jwt_token=jwt, job_id=job_id)
#             applicant_ids = extract_applicant_ids(candidates)
#             print(f"✅ Found {len(applicant_ids)} applicants")
            
#             screened_applicants = []
            
#             for idx, candidate_id in enumerate(applicant_ids, 1):
#                 print(f"\n{'─'*80}")
#                 print(f"Processing Applicant {idx}/{len(applicant_ids)} - ID: {candidate_id}")
#                 print(f"{'─'*80}")
                
#                 # Get documents
#                 documents = get_candidate_documents(
#                     jwt_token=jwt,
#                     job_id=job_id,
#                     candidate_id=candidate_id,
#                     transfer=False
#                 )
                
#                 if not documents:
#                     print(f"❌ Failed to fetch documents for {candidate_id}")
#                     continue
                
#                 # Build applicant record
#                 applicant_record = build_single_applicant_record(documents)
#                 candidate_job_id = documents[0].get("id")
                
#                 # Check for incomplete questions
#                 incomplete_questions = get_incomplete_questions(applicant_record)
                
#                 if incomplete_questions:
#                     print(f"⚠️  Incomplete application - {len(incomplete_questions)} missing answers")
                    
#                     # Send reminder email
#                     email_sent = send_incomplete_application_email(
#                         jwt_token=jwt,
#                         candidate_job_id=candidate_job_id,
#                         candidate_email=applicant_record["email"],
#                         job_id=job_id,
#                         job_name=applicant_record["job_name"],
#                         incomplete_questions=incomplete_questions
#                     )
                    
#                     status = "incomplete_email_sent" if email_sent else "incomplete_email_failed"
#                     screened_applicants.append({
#                         'candidate_id': candidate_id,
#                         'email': applicant_record["email"],
#                         'status': status
#                     })
#                     continue
                
#                 # Decide status
#                 final_status = decide_candidate_status(applicant_record)
#                 print(f"🎯 Decision: {final_status}")
                
#                 # Handle rejection
#                 if final_status == "Inactive":
#                     rejection_reason = get_rejection_reason(applicant_record)
#                     print(f"📧 Sending rejection email...")
                    
#                     email_sent = send_rejection_email(
#                         jwt_token=jwt,
#                         candidate_job_id=candidate_job_id,
#                         candidate_email=applicant_record["email"],
#                         job_name=applicant_record["job_name"],
#                         rejection_reason=rejection_reason
#                     )
                
#                 # Update status in Hireology
#                 print(f"🔄 Updating status to '{final_status}'...")
#                 update_candidate_status(
#                     jwt_token=jwt,
#                     job_id=job_id,
#                     candidate_id=candidate_id,
#                     status=final_status
#                 )
                
#                 screened_applicants.append({
#                     'candidate_id': candidate_id,
#                     'email': applicant_record["email"],
#                     'status': final_status,
#                     'record': applicant_record
#                 })
            
#             self.results['screened_applicants'] = screened_applicants
#             self.results['steps_completed'].append('step1_screening')
            
#             print("\n" + "="*80)
#             print(f"✅ STEP 1 COMPLETE: Screened {len(screened_applicants)} applicants")
#             print("="*80)
            
#             return screened_applicants
            
#         except Exception as e:
#             error_msg = f"Step 1 failed: {str(e)}"
#             print(f"\n❌ {error_msg}")
#             self.results['errors'].append(error_msg)
#             return None
    
#     def step2_process_phone_interview(self, agent_id=None):
#         """Step 2: Process most recent phone interview transcript"""
#         print("\n" + "="*80)
#         print("STEP 2: PROCESSING PHONE INTERVIEW")
#         print("="*80)
        
#         try:
#             # Initialize extractor
#             extractor = HireologyQAExtractor(
#                 api_key=self.config['ghl_api_key'],
#                 location_id=self.config['ghl_location_id'],
#                 groq_api_key=self.config.get('groq_api_key')
#             )
            
#             # Extract Q&A from most recent call
#             agent_id = agent_id or self.config.get('ghl_agent_id')
#             print(f"\n📞 Extracting interview from agent {agent_id}...")
            
#             qa_pairs = extractor.extract_for_hireology(agent_id=agent_id)
            
#             if not qa_pairs:
#                 raise Exception("No Q&A pairs extracted from interview")
            
#             # Find the saved JSON file (most recent)
#             call_data_dir = 'call_data'
#             json_files = [f for f in os.listdir(call_data_dir) if f.startswith('hireology_qa_') and f.endswith('.json')]
            
#             if not json_files:
#                 raise Exception("No JSON file created")
            
#             latest_json = max([os.path.join(call_data_dir, f) for f in json_files], key=os.path.getctime)
            
#             self.results['interview_json_path'] = latest_json
#             self.results['qa_pairs_count'] = len(qa_pairs)
#             self.results['steps_completed'].append('step2_interview_processing')
            
#             print("\n" + "="*80)
#             print(f"✅ STEP 2 COMPLETE: Processed {len(qa_pairs)} Q&A pairs")
#             print(f"   JSON saved: {latest_json}")
#             print("="*80)
            
#             return latest_json
            
#         except Exception as e:
#             error_msg = f"Step 2 failed: {str(e)}"
#             print(f"\n❌ {error_msg}")
#             self.results['errors'].append(error_msg)
#             return None
    
#     def step3_update_hireology_interview(self, candidate_id, json_path=None):
#         """
#         Step 3: Fetch interview ID dynamically and update Hireology interview with phone interview results
        
#         Uses the fetch_interview_id function from interview_id_fetcher.py which:
#         1. Gets candidate_job_id from /jobs/{job_id}/candidates/{candidate_id}
#         2. Gets hiring_step_id from /jobs/{job_id}/interview_progress
#         3. Creates an interview using /v2/interviews endpoint
#         4. Returns the interview ID
        
#         Args:
#             candidate_id: Candidate ID to fetch interview for
#             json_path: Path to JSON file with interview answers (optional, uses from step 2 if not provided)
#         """
#         print("\n" + "="*80)
#         print("STEP 3: UPDATING HIREOLOGY INTERVIEW")
#         print("="*80)
        
#         try:
#             jwt = self.config['hireology_jwt']
#             job_id = self.config['hireology_job_id']
#             interview_template_id = self.config.get('interview_template_id', 512090)
            
#             # Use provided path or from previous step
#             if not json_path:
#                 json_path = self.results.get('interview_json_path')
            
#             if not json_path or not os.path.exists(json_path):
#                 raise Exception(f"JSON file not found: {json_path}")
            
#             # ========== FETCH INTERVIEW ID DYNAMICALLY ==========
#             print(f"\n🔍 Fetching/Creating interview for candidate {candidate_id}...")
#             print(f"   Using interview_id_fetcher.fetch_interview_id()")
            
#             try:
#                 # Use the fetch_interview_id function from interview_id_fetcher.py
#                 interview_id = fetch_interview_id(
#                     jwt=jwt,
#                     job_id=job_id,
#                     candidate_id=candidate_id,
#                     interview_template_id=interview_template_id
#                 )
#                 print(f"✅ Got interview ID: {interview_id}")
                
#                 # Store in results
#                 self.results['interview_id'] = interview_id
#                 self.results['candidate_id'] = candidate_id
                
#             except Exception as fetch_error:
#                 error_msg = f"Failed to fetch/create interview ID: {str(fetch_error)}"
#                 print(f"❌ {error_msg}")
#                 raise Exception(error_msg)
#             # ========== END FETCH INTERVIEW ID ==========
            
#             print(f"\n📥 Loading interview data from Hireology...")
#             print(f"   Job ID: {job_id}")
#             print(f"   Candidate ID: {candidate_id}")
#             print(f"   Interview ID: {interview_id}")
            
#             # Temporarily set global variables for the imported functions
#             import update_phoneInterview_on_Hireology as upd
#             upd.JOB_ID = job_id
#             upd.CANDIDATE_ID = candidate_id
#             upd.INTERVIEW_ID = interview_id
#             upd.BEARER_TOKEN = jwt
            
#             # Fetch interview
#             interview_data = fetch_interview_from_api()
#             print(f"✓ Fetched interview with {len(interview_data.get('questions', []))} questions")
            
#             # Update with answers
#             print(f"\n📝 Matching answers from: {json_path}")
#             updated_interview, update_logs, all_logs = update_interview_answers(json_path, interview_data)
            
#             # Display logs
#             if all_logs:
#                 display_update_logs(all_logs, len(update_logs))
            
#             # Send to Hireology
#             print(f"\n📤 Sending update to Hireology API...")
#             response = send_update_to_hireology(updated_interview)
            
#             if response.status_code not in [200, 204]:
#                 raise Exception(f"API returned status {response.status_code}: {response.text}")
            
#             print(f"✓ Successfully updated interview!")
#             if response.status_code == 200:
#                 resp_data = response.json()
#                 print(f"\n   📊 INITIAL Response:")
#                 print(f"      Score: {resp_data.get('score', 'N/A')} (not calculated yet)")
#                 print(f"      Progress: {resp_data.get('progress', 'N/A')}")
            
#             # ========== TRIGGER SCORE CALCULATION ==========
#             print(f"\n🧮 Calculating interview score...")
            
#             try:
#                 score_response = trigger_score_calculation()
                
#                 if score_response.status_code == 200:
#                     score_data = score_response.json()
#                     print(f"   ✅ Score calculated successfully!")
#                     print(f"\n   📊 FINAL INTERVIEW STATUS:")
#                     print(f"      Score: {score_data.get('score', 'N/A')}")
#                     print(f"      Confidence Score: {score_data.get('confidence_score', 'N/A')}")
#                     print(f"      Progress: {score_data.get('progress', 'N/A')}")
                    
#                     # Store score in results
#                     self.results['interview_score'] = score_data.get('score')
#                     self.results['confidence_score'] = score_data.get('confidence_score')
                    
#                 elif score_response.status_code == 204:
#                     print(f"   ✅ Score calculation triggered (no content returned)")
#                     print(f"   ℹ️  Score should now be visible in Hireology")
#                 else:
#                     print(f"   ⚠️  Score calculation returned: {score_response.status_code}")
#                     print(f"   Response: {score_response.text}")
                    
#             except Exception as score_error:
#                 print(f"   ⚠️  Score calculation error: {str(score_error)}")
#                 print(f"   Note: Interview was updated successfully, but score calculation failed")
#             # ========== END SCORE CALCULATION ==========
            
#             self.results['interview_updated'] = True
#             self.results['matched_questions'] = len(update_logs)
#             self.results['steps_completed'].append('step3_interview_update')
            
#             print("\n" + "="*80)
#             print(f"✅ STEP 3 COMPLETE: Updated {len(update_logs)} interview answers")
#             print("="*80)
            
#             return True
            
#         except Exception as e:
#             error_msg = f"Step 3 failed: {str(e)}"
#             print(f"\n❌ {error_msg}")
#             self.results['errors'].append(error_msg)
#             return False
    
#     def run_screening_only(self):
#         """Run only the screening step (Step 1)"""
#         print("\n" + "="*80)
#         print("🚀 RUNNING SCREENING WORKFLOW")
#         print("="*80)
#         print(f"Timestamp: {self.results['timestamp']}")
        
#         screened = self.step1_screen_applicants()
        
#         # Final summary
#         print("\n" + "="*80)
#         print("🎉 SCREENING COMPLETE")
#         print("="*80)
#         print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
#         print(f"\nErrors: {len(self.results['errors'])}")
#         if self.results['errors']:
#             for error in self.results['errors']:
#                 print(f"  ❌ {error}")
#         print("="*80)
        
#         return self.results
    
#     def run_interview_workflow(self, candidate_id):
#         """
#         Run the interview processing and update workflow (Steps 2 & 3)
#         Interview ID is fetched dynamically in Step 3 using interview_id_fetcher.py
        
#         Args:
#             candidate_id: Candidate ID to process interview for
#         """
#         print("\n" + "="*80)
#         print("🚀 RUNNING INTERVIEW WORKFLOW")
#         print("="*80)
#         print(f"Timestamp: {self.results['timestamp']}")
#         print(f"Candidate ID: {candidate_id}")
        
#         # Step 2: Process phone interview
#         json_path = self.step2_process_phone_interview()
#         if json_path is None:
#             print("\n❌ Workflow stopped: Phone interview processing failed")
#             return self.results
        
#         # Step 3: Fetch interview ID dynamically and update Hireology
#         success = self.step3_update_hireology_interview(candidate_id, json_path)
#         if not success:
#             print("\n⚠️  Step 3 failed")
        
#         # Final summary
#         print("\n" + "="*80)
#         print("🎉 INTERVIEW WORKFLOW SUMMARY")
#         print("="*80)
#         print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        
#         # Display score if available
#         if 'interview_score' in self.results:
#             print(f"\n📊 Interview Results:")
#             print(f"   Interview ID: {self.results.get('interview_id', 'N/A')}")
#             print(f"   Final Score: {self.results.get('interview_score', 'N/A')}")
#             print(f"   Confidence Score: {self.results.get('confidence_score', 'N/A')}")
#             print(f"   Questions Matched: {self.results.get('matched_questions', 0)}")
        
#         print(f"\nErrors: {len(self.results['errors'])}")
#         if self.results['errors']:
#             for error in self.results['errors']:
#                 print(f"  ❌ {error}")
#         print("="*80)
        
#         return self.results
    
#     def run_complete_workflow(self, candidate_id):
#         """
#         Run the complete hiring workflow (all 3 steps)
#         Interview ID is fetched dynamically in Step 3 using interview_id_fetcher.py
        
#         Args:
#             candidate_id: Candidate ID to process interview for (used in Step 3)
#         """
#         print("\n" + "="*80)
#         print("🚀 STARTING COMPLETE HIRING WORKFLOW")
#         print("="*80)
#         print(f"Timestamp: {self.results['timestamp']}")
        
#         # Step 1: Screen applicants
#         screened = self.step1_screen_applicants()
#         if screened is None:
#             print("\n⚠️  Step 1 failed, but continuing with remaining steps...")
        
#         # Step 2: Process phone interview
#         json_path = self.step2_process_phone_interview()
#         if json_path is None:
#             print("\n❌ Workflow stopped: Phone interview processing failed")
#             return self.results
        
#         # Step 3: Fetch interview ID dynamically and update Hireology
#         success = self.step3_update_hireology_interview(candidate_id, json_path)
#         if not success:
#             print("\n⚠️  Step 3 failed, but previous steps completed")
        
#         # Final summary
#         print("\n" + "="*80)
#         print("🎉 COMPLETE WORKFLOW SUMMARY")
#         print("="*80)
#         print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        
#         # Display score if available
#         if 'interview_score' in self.results:
#             print(f"\n📊 Interview Results:")
#             print(f"   Interview ID: {self.results.get('interview_id', 'N/A')}")
#             print(f"   Final Score: {self.results.get('interview_score', 'N/A')}")
#             print(f"   Confidence Score: {self.results.get('confidence_score', 'N/A')}")
#             print(f"   Questions Matched: {self.results.get('matched_questions', 0)}")
        
#         print(f"\nErrors: {len(self.results['errors'])}")
#         if self.results['errors']:
#             for error in self.results['errors']:
#                 print(f"  ❌ {error}")
#         print("="*80)
        
#         return self.results


# # ============= MAIN EXECUTION =============

# if __name__ == "__main__":
#     # Your credentials (replace with actual values or use environment variables)
#     jwt = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY2ODY0NjkzLCJuYmYiOjE3NjY4NjEwOTMsImlkcCI6Imdvb2dsZS5jb20iLCJzdWIiOiIyMzBhOTY2YS03OGNiLTRjMzktYWRhMy03ZTg5MjVjYzZkOTEiLCJvaWQiOiIyMzBhOTY2YS03OGNiLTRjMzktYWRhMy03ZTg5MjVjYzZkOTEiLCJtZmEiOnRydWUsImF6ZnAiOnRydWUsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY2ODYxMDkzfQ.HmLjXrQgMMaqU5jiubdPn5OyI79pLlTDKXCCHKMnH8xIqofle_4vFLbCqHE9jNSH6oQpSry97T8NzXTKV6lapUZvk9sJB6I-yvve6nkKrUDoht1h4_3IbaqQzWUnm2Mvy_T3VQS3iZCRiouBVF8QqzBPFsSHvLqgTiM9T3P8Uc9J1_edP8wSs1nZie0S-UCeaVpBz_ufuUzkUT5FNNMQTA9nCnK-gCfKrPjVglNkycqSukdVLBoyngfO4WXNCl-ZVvOnW3cQ8rd1CpDL5uYUEsSDl6hRCTXViHBMolOODM5CWMdMghOtfdL-Tv9d9MYS919Jq8pf9DJgvmbYiHKbHg"
#     job_id = "2606114"
#     candidate_id = "47113924"
    
#     # Configuration
#     config = {
#         'hireology_jwt': jwt,
#         'hireology_job_id': job_id,
#         'ghl_api_key': "pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324",
#         'ghl_location_id': "M5jnxd1r8yq3o5gxSYOP",
#         'ghl_agent_id': "693448f6231659c2a32a3bca",
#         'groq_api_key': os.getenv("GROQ_API_KEY"),
#         'interview_template_id': 512090  # Phone Interview template
#     }
    
#     # Create orchestrator
#     orchestrator = HiringWorkflowOrchestrator(config)
    
#     # ========== USAGE EXAMPLES ==========
    
#     # EXAMPLE 1: Run complete workflow (all 3 steps)
#     # Interview ID is fetched dynamically using interview_id_fetcher.fetch_interview_id()
#     results = orchestrator.run_complete_workflow(candidate_id=candidate_id)
    
#     # EXAMPLE 2: Run only screening (Step 1)
#     # results = orchestrator.run_screening_only()
    
#     # EXAMPLE 3: Run only interview workflow (Steps 2 & 3)
#     # Interview ID is fetched dynamically
#     # results = orchestrator.run_interview_workflow(candidate_id=candidate_id)
    
#     # EXAMPLE 4: Run individual steps manually
#     # orchestrator.step1_screen_applicants()
#     # json_path = orchestrator.step2_process_phone_interview()
#     # orchestrator.step3_update_hireology_interview(candidate_id=candidate_id, json_path=json_path)
    
#     # Save results to file
#     with open('workflow_results.json', 'w') as f:
#         json.dump(results, f, indent=2)
    
#     print("\n✅ Full results saved to: workflow_results.json")


# //////////////

"""
Complete Hiring Workflow Application
Orchestrates: Applicant Screening -> Phone Interview -> Hireology Update -> Score Calculation
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
# Import from your existing files
from fetch_applicants import (
    get_candidates,
    extract_applicant_ids,
    get_candidate_documents,
    build_single_applicant_record,
    get_incomplete_questions,
    send_incomplete_application_email,
    decide_candidate_status,
    get_rejection_reason,
    send_rejection_email,
    update_candidate_status,
    write_single_record_to_csv
)

from formate_most_recent_callTranscript_to_Structured_json import HireologyQAExtractor

from update_phoneInterview_on_Hireology import (
    fetch_interview_from_api,
    update_interview_answers,
    send_update_to_hireology,
    trigger_score_calculation,
    display_update_logs
)
from interview_id_fetcher import fetch_interview_id
from agent_call import make_trial_call
load_dotenv()

class HiringWorkflowOrchestrator:
    """Orchestrates the complete hiring workflow"""
    
    def __init__(self, config: dict):
        """
        Initialize with configuration
        
        config should contain:
        - hireology_jwt: Hireology JWT token
        - hireology_job_id: Job ID in Hireology
        - ghl_api_key: GoHighLevel API key
        - ghl_location_id: GoHighLevel location ID
        - ghl_agent_id: GoHighLevel agent ID
        - groq_api_key: Groq API key (optional)
        """
        self.config = config
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'steps_completed': [],
            'errors': []
        }
    
    def step1_screen_applicants(self):
        """Step 1: Screen all applicants for a job"""
        print("\n" + "="*80)
        print("STEP 1: SCREENING APPLICANTS")
        print("="*80)
        
        try:
            jwt = self.config['hireology_jwt']
            job_id = self.config['hireology_job_id']
            
            # Fetch candidates
            print(f"\n🔍 Fetching candidates for job {job_id}...")
            candidates = get_candidates(jwt_token=jwt, job_id=job_id)
            print("The candidates are :", candidates)
            applicant_ids = extract_applicant_ids(candidates)
            print(f"✅ Found {len(applicant_ids)} applicants")
            
            screened_applicants = []
            
            for idx, candidate_id in enumerate(applicant_ids, 1):
                print(f"\n{'─'*80}")
                print(f"Processing Applicant {idx}/{len(applicant_ids)} - ID: {candidate_id}")
                print(f"{'─'*80}")
                
                # Get documents
                documents = get_candidate_documents(
                    jwt_token=jwt,
                    job_id=job_id,
                    candidate_id=candidate_id,
                    transfer=False
                )
                
                if not documents:
                    print(f"❌ Failed to fetch documents for {candidate_id}")
                    continue
                
                # Build applicant record
                applicant_record = build_single_applicant_record(documents)
                candidate_job_id = documents[0].get("id")
                candidate_phone = documents[0].get("home_phone") or documents[0].get("cell_phone") 
                
                # Check for incomplete questions
                incomplete_questions = get_incomplete_questions(applicant_record)
                
                if incomplete_questions:
                    print(f"⚠️  Incomplete application - {len(incomplete_questions)} missing answers")
                    
                    # Send reminder email
                    email_sent = send_incomplete_application_email(
                        jwt_token=jwt,
                        candidate_job_id=candidate_job_id,
                        candidate_email=applicant_record["email"],
                        job_id=job_id,
                        job_name=applicant_record["job_name"],
                        incomplete_questions=incomplete_questions
                    )
                    
                    status = "incomplete_email_sent" if email_sent else "incomplete_email_failed"
                    screened_applicants.append({
                        'candidate_id': candidate_id,
                        'email': applicant_record["email"],
                        'status': status
                    })
                    continue
                
                # Decide status
                final_status = decide_candidate_status(applicant_record)
                print(f"🎯 Decision: {final_status}")
                
                # Handle rejection
                if final_status == "Inactive":
                    rejection_reason = get_rejection_reason(applicant_record)
                    print(f"📧 Sending rejection email...")
                    
                    email_sent = send_rejection_email(
                        jwt_token=jwt,
                        candidate_job_id=candidate_job_id,
                        candidate_email=applicant_record["email"],
                        job_name=applicant_record["job_name"],
                        rejection_reason=rejection_reason
                    )
                
                # Update status in Hireology
                print(f"🔄 Updating status to '{final_status}'...")
                update_candidate_status(
                    jwt_token=jwt,
                    job_id=job_id,
                    candidate_id=candidate_id,
                    status=final_status
                )
                
                applicant_data = {
                    'candidate_id': candidate_id,
                    'email': applicant_record["email"],
                    'status': final_status,
                    'record': applicant_record
                }

                # 🔹 ADD PHONE ONLY IF NOT INACTIVE
                if final_status == "Candidate":
                    applicant_data['phone'] = candidate_phone

                screened_applicants.append(applicant_data)

            
            self.results['screened_applicants'] = screened_applicants
            self.results['steps_completed'].append('step1_screening')
            
            print("\n" + "="*80)
            print(f"✅ STEP 1 COMPLETE: Screened {len(screened_applicants)} applicants")
            print("="*80)
            
            return screened_applicants
            
        except Exception as e:
            error_msg = f"Step 1 failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.results['errors'].append(error_msg)
            return None
    
    def step2_process_phone_interview(self, agent_id=None):
        """Step 2: Process most recent phone interview transcript"""
        print("\n" + "="*80)
        print("STEP 2: PROCESSING PHONE INTERVIEW")
        print("="*80)
        
        try:
            # Initialize extractor
            extractor = HireologyQAExtractor(
                api_key=self.config['ghl_api_key'],
                location_id=self.config['ghl_location_id'],
                groq_api_key=self.config.get('groq_api_key')
            )
            
            # Extract Q&A from most recent call
            agent_id = agent_id or self.config.get('ghl_agent_id')
            print(f"\n📞 Extracting interview from agent {agent_id}...")
            
            qa_pairs = extractor.extract_for_hireology(agent_id=agent_id)
            
            if not qa_pairs:
                raise Exception("No Q&A pairs extracted from interview")
            
            # Find the saved JSON file (most recent)
            call_data_dir = 'call_data'
            json_files = [f for f in os.listdir(call_data_dir) if f.startswith('hireology_qa_') and f.endswith('.json')]
            
            if not json_files:
                raise Exception("No JSON file created")
            
            latest_json = max([os.path.join(call_data_dir, f) for f in json_files], key=os.path.getctime)
            
            self.results['interview_json_path'] = latest_json
            self.results['qa_pairs_count'] = len(qa_pairs)
            self.results['steps_completed'].append('step2_interview_processing')
            
            print("\n" + "="*80)
            print(f"✅ STEP 2 COMPLETE: Processed {len(qa_pairs)} Q&A pairs")
            print(f"   JSON saved: {latest_json}")
            print("="*80)
            
            return latest_json
            
        except Exception as e:
            error_msg = f"Step 2 failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.results['errors'].append(error_msg)
            return None
    
    def step3_update_hireology_interview(self, candidate_id, json_path=None):
        """
        Step 3: Fetch interview ID dynamically and update Hireology interview with phone interview results
        
        Args:
            candidate_id: Candidate ID to fetch interview for
            json_path: Path to JSON file with interview answers (optional, uses from step 2 if not provided)
        """
        print("\n" + "="*80)
        print("STEP 3: UPDATING HIREOLOGY INTERVIEW")
        print("="*80)
        
        try:
            jwt = self.config['hireology_jwt']
            job_id = self.config['hireology_job_id']
            
            # Use provided path or from previous step
            if not json_path:
                json_path = self.results.get('interview_json_path')
            
            if not json_path or not os.path.exists(json_path):
                raise Exception(f"JSON file not found: {json_path}")
            
            # ========== FETCH INTERVIEW ID DYNAMICALLY ==========
            print(f"\n🔍 Fetching interview ID for candidate {candidate_id}...")
            
            try:
                interview_id = fetch_interview_id(jwt, job_id, candidate_id)
                print(f"✅ Found interview ID: {interview_id}")
                
                # Store in results
                self.results['interview_id'] = interview_id
                self.results['candidate_id'] = candidate_id
                
            except Exception as fetch_error:
                error_msg = f"Failed to fetch interview ID: {str(fetch_error)}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            # ========== END FETCH INTERVIEW ID ==========
            
            print(f"\n📥 Loading interview data from Hireology...")
            print(f"   Job ID: {job_id}")
            print(f"   Candidate ID: {candidate_id}")
            print(f"   Interview ID: {interview_id}")
            
            # Temporarily set global variables for the imported functions
            import update_phoneInterview_on_Hireology as upd
            upd.JOB_ID = job_id
            upd.CANDIDATE_ID = candidate_id
            upd.INTERVIEW_ID = interview_id
            upd.BEARER_TOKEN = jwt
            
            # Fetch interview
            interview_data = fetch_interview_from_api()
            print(f"✓ Fetched interview with {len(interview_data.get('questions', []))} questions")
            
            # Update with answers
            print(f"\n📝 Matching answers from: {json_path}")
            updated_interview, update_logs, all_logs = update_interview_answers(json_path, interview_data)
            
            # Display logs
            if all_logs:
                display_update_logs(all_logs, len(update_logs))
            
            # Send to Hireology
            print(f"\n📤 Sending update to Hireology API...")
            response = send_update_to_hireology(updated_interview)
            
            if response.status_code not in [200, 204]:
                raise Exception(f"API returned status {response.status_code}: {response.text}")
            
            print(f"✓ Successfully updated interview!")
            if response.status_code == 200:
                resp_data = response.json()
                print(f"\n   📊 INITIAL Response:")
                print(f"      Score: {resp_data.get('score', 'N/A')} (not calculated yet)")
                print(f"      Progress: {resp_data.get('progress', 'N/A')}")
            
            # ========== TRIGGER SCORE CALCULATION ==========
            print(f"\n🧮 Calculating interview score...")
            
            try:
                score_response = trigger_score_calculation()
                
                if score_response.status_code == 200:
                    score_data = score_response.json()
                    print(f"   ✅ Score calculated successfully!")
                    print(f"\n   📊 FINAL INTERVIEW STATUS:")
                    print(f"      Score: {score_data.get('score', 'N/A')}")
                    print(f"      Confidence Score: {score_data.get('confidence_score', 'N/A')}")
                    print(f"      Progress: {score_data.get('progress', 'N/A')}")
                    
                    # Store score in results
                    self.results['interview_score'] = score_data.get('score')
                    self.results['confidence_score'] = score_data.get('confidence_score')
                    
                elif score_response.status_code == 204:
                    print(f"   ✅ Score calculation triggered (no content returned)")
                    print(f"   ℹ️  Score should now be visible in Hireology")
                else:
                    print(f"   ⚠️  Score calculation returned: {score_response.status_code}")
                    print(f"   Response: {score_response.text}")
                    
            except Exception as score_error:
                print(f"   ⚠️  Score calculation error: {str(score_error)}")
                print(f"   Note: Interview was updated successfully, but score calculation failed")
            # ========== END SCORE CALCULATION ==========
            
            self.results['interview_updated'] = True
            self.results['matched_questions'] = len(update_logs)
            self.results['steps_completed'].append('step3_interview_update')
            
            print("\n" + "="*80)
            print(f"✅ STEP 3 COMPLETE: Updated {len(update_logs)} interview answers")
            print("="*80)
            
            return True
            
        except Exception as e:
            error_msg = f"Step 3 failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.results['errors'].append(error_msg)
            return False
    
    def run_screening_only(self):
        """Run only the screening step (Step 1)"""
        print("\n" + "="*80)
        print("🚀 RUNNING SCREENING WORKFLOW")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        
        screened = self.step1_screen_applicants()

        # for applicant in screened:
        #     if applicant['status'] == 'Candidate':
        #         make_trial_call(token_id=self.config['ghl_api_key'], to_phone_number=applicant['phone'])
        #         print(applicant['candidate_id'], applicant['phone'])

        
        # Final summary
        print("\n" + "="*80)
        print("🎉 SCREENING COMPLETE")
        print("="*80)
        print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        print(f"\nErrors: {len(self.results['errors'])}")
        if self.results['errors']:
            for error in self.results['errors']:
                print(f"  ❌ {error}")
        print("="*80)
        
        return self.results
    
    def run_interview_workflow(self, candidate_id):
        """
        Run the interview processing and update workflow (Steps 2 & 3)
        Interview ID is fetched dynamically in Step 3
        
        Args:
            candidate_id: Candidate ID to process interview for
        """
        print("\n" + "="*80)
        print("🚀 RUNNING INTERVIEW WORKFLOW")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Candidate ID: {candidate_id}")
        
        # Step 2: Process phone interview
        json_path = self.step2_process_phone_interview()
        if json_path is None:
            print("\n❌ Workflow stopped: Phone interview processing failed")
            return self.results
        
        # Step 3: Fetch interview ID dynamically and update Hireology
        success = self.step3_update_hireology_interview(candidate_id, json_path)
        if not success:
            print("\n⚠️  Step 3 failed")
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 INTERVIEW WORKFLOW SUMMARY")
        print("="*80)
        print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        
        # Display score if available
        if 'interview_score' in self.results:
            print(f"\n📊 Interview Results:")
            print(f"   Interview ID: {self.results.get('interview_id', 'N/A')}")
            print(f"   Final Score: {self.results.get('interview_score', 'N/A')}")
            print(f"   Confidence Score: {self.results.get('confidence_score', 'N/A')}")
            print(f"   Questions Matched: {self.results.get('matched_questions', 0)}")
        
        print(f"\nErrors: {len(self.results['errors'])}")
        if self.results['errors']:
            for error in self.results['errors']:
                print(f"  ❌ {error}")
        print("="*80)
        
        return self.results
    
    def run_complete_workflow(self, candidate_id):
        """
        Run the complete hiring workflow (all 3 steps)
        Interview ID is fetched dynamically in Step 3
        
        Args:
            candidate_id: Candidate ID to process interview for (used in Step 3)
        """
        print("\n" + "="*80)
        print("🚀 STARTING COMPLETE HIRING WORKFLOW")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        
        # Step 1: Screen applicants
        screened = self.step1_screen_applicants()
        if screened is None:
            print("\n⚠️  Step 1 failed, but continuing with remaining steps...")
        
        # Step 2: Process phone interview
        json_path = self.step2_process_phone_interview()
        if json_path is None:
            print("\n❌ Workflow stopped: Phone interview processing failed")
            return self.results
        
        # Step 3: Fetch interview ID dynamically and update Hireology
        success = self.step3_update_hireology_interview(candidate_id, json_path)
        if not success:
            print("\n⚠️  Step 3 failed, but previous steps completed")
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 COMPLETE WORKFLOW SUMMARY")
        print("="*80)
        print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        
        # Display score if available
        if 'interview_score' in self.results:
            print(f"\n📊 Interview Results:")
            print(f"   Interview ID: {self.results.get('interview_id', 'N/A')}")
            print(f"   Final Score: {self.results.get('interview_score', 'N/A')}")
            print(f"   Confidence Score: {self.results.get('confidence_score', 'N/A')}")
            print(f"   Questions Matched: {self.results.get('matched_questions', 0)}")
        
        print(f"\nErrors: {len(self.results['errors'])}")
        if self.results['errors']:
            for error in self.results['errors']:
                print(f"  ❌ {error}")
        print("="*80)
        
        return self.results


# ============= MAIN EXECUTION =============

if __name__ == "__main__":
    print("New execution started")
    jwt = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY3MDI2Mzg5LCJuYmYiOjE3NjcwMjI3ODksImlkcCI6Imdvb2dsZS5jb20iLCJzdWIiOiIyMzBhOTY2YS03OGNiLTRjMzktYWRhMy03ZTg5MjVjYzZkOTEiLCJvaWQiOiIyMzBhOTY2YS03OGNiLTRjMzktYWRhMy03ZTg5MjVjYzZkOTEiLCJtZmEiOnRydWUsImF6ZnAiOnRydWUsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY3MDIyNzg5fQ.rbGmdKB3rvzRwiFQakgs-1i-3Ya4iOn-CkJHOfh9zvjYPfrcw-Kmg33_7GNL3aYgK72phKBozLwr_E1mpxuYIi66kdrOvFJFdQAF32rWz74v2bLycqjYcTg57GFUxdu3y1xF_oIcdVlZtX16oXP4THoUNjJ4FsajubwcPtMH3Adk6fXJt8MojwNxvCzSR8vnIfzFQOV18qgDqjQ34LL3iqdLpF5Xp_8Wh6kaG84IhRHZL98cnqthaA8yUllYsUCLLjwIY513dG_oiKeWk9AVOpGtH2DjXpKubESJo86NESvGiZkyxU-hNgGJ2qXJ0CwKrOivTrGvjgoKNSyzO9oJlA"
    job_id = "2606114"
    candidate_id = "47160826"
    
    # Configuration
    config = {
        'hireology_jwt': jwt,
        'hireology_job_id': job_id,
        'ghl_api_key': "pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324",
        'ghl_location_id': "M5jnxd1r8yq3o5gxSYOP",
        'ghl_agent_id': "693448f6231659c2a32a3bca",
        'groq_api_key': os.getenv("GROQ_API_KEY")
    }
    
    # Create orchestrator
    orchestrator = HiringWorkflowOrchestrator(config)
    
    # ========== USAGE EXAMPLES ==========
    
    # EXAMPLE 1: Run complete workflow (all 3 steps)
    # Interview ID is fetched dynamically in Step 3
    results = orchestrator.run_complete_workflow(candidate_id=candidate_id)
    
    # EXAMPLE 2: Run only screening (Step 1)
    # results = orchestrator.run_screening_only()
    
    # EXAMPLE 3: Run only interview workflow (Steps 2 & 3)
    # Interview ID is fetched dynamically
    # results = orchestrator.run_interview_workflow(candidate_id=candidate_id)
    
    # EXAMPLE 4: Run individual steps manually
    # orchestrator.step1_screen_applicants()
    # json_path = orchestrator.step2_process_phone_interview()
    # orchestrator.step3_update_hireology_interview(candidate_id=candidate_id, json_path=json_path)
    
    # Save results to file
    with open('workflow_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Full results saved to: workflow_results.json")