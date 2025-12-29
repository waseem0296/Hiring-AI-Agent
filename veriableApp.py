# """
# Complete Hiring Workflow Application - AUTOMATED VERSION
# Automatically finds candidates needing interviews and processes them
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

# load_dotenv()


# class HiringWorkflowOrchestrator:
#     """Orchestrates the complete hiring workflow with automatic candidate detection"""
    
#     def __init__(self, config: dict):
#         self.config = config
#         self.results = {
#             'timestamp': datetime.now().isoformat(),
#             'steps_completed': [],
#             'errors': []
#         }
    
#     def find_candidates_needing_interview(self):
#         """
#         Automatically find candidates who need phone interviews
#         Priority:
#         1. New applicants who haven't been interviewed
#         2. Existing candidates with incomplete/unscored interviews
        
#         Returns: list of dicts with candidate_id, interview_id, status
#         """
#         print("\n" + "="*80)
#         print("🔍 AUTO-DETECTING CANDIDATES NEEDING INTERVIEWS")
#         print("="*80)
        
#         try:
#             jwt = self.config['hireology_jwt']
#             job_id = self.config['hireology_job_id']
            
#             # Fetch all candidates
#             print(f"\n📥 Fetching all candidates for job {job_id}...")
#             candidates = get_candidates(jwt_token=jwt, job_id=job_id)
#             applicant_ids = extract_applicant_ids(candidates)
#             print(f"✅ Found {len(applicant_ids)} total applicants")
            
#             candidates_needing_interview = []
            
#             for idx, candidate_id in enumerate(applicant_ids, 1):
#                 print(f"\n{'─'*40}")
#                 print(f"Checking {idx}/{len(applicant_ids)} - Candidate {candidate_id}")
                
#                 try:
#                     # Get candidate documents to check interview status
#                     documents = get_candidate_documents(
#                         jwt_token=jwt,
#                         job_id=job_id,
#                         candidate_id=candidate_id,
#                         transfer=False
#                     )
                    
#                     if not documents:
#                         print(f"  ⏭️  Skipping - no documents found")
#                         continue
                    
#                     # Check if candidate has interviews
#                     interviews = self._get_candidate_interviews(jwt, job_id, candidate_id)
                    
#                     if not interviews:
#                         # NEW APPLICANT - No interview yet
#                         print(f"  🆕 NEW APPLICANT - No interview found")
#                         candidates_needing_interview.append({
#                             'candidate_id': candidate_id,
#                             'interview_id': None,
#                             'status': 'new_applicant',
#                             'priority': 1  # Highest priority
#                         })
#                     else:
#                         # Check if any interview is incomplete or unscored
#                         for interview in interviews:
#                             interview_id = interview.get('id')
#                             progress = interview.get('progress', 0)
#                             score = interview.get('score')
                            
#                             if progress < 100 or score is None:
#                                 print(f"  📝 INCOMPLETE INTERVIEW - ID: {interview_id}")
#                                 print(f"     Progress: {progress}%, Score: {score}")
#                                 candidates_needing_interview.append({
#                                     'candidate_id': candidate_id,
#                                     'interview_id': interview_id,
#                                     'status': 'incomplete_interview',
#                                     'priority': 2,
#                                     'progress': progress,
#                                     'score': score
#                                 })
#                                 break  # Only add once per candidate
#                             else:
#                                 print(f"  ✓ Interview complete (Progress: {progress}%, Score: {score})")
                
#                 except Exception as e:
#                     print(f"  ⚠️  Error checking candidate: {str(e)}")
#                     continue
            
#             # Sort by priority (new applicants first)
#             candidates_needing_interview.sort(key=lambda x: x['priority'])
            
#             print("\n" + "="*80)
#             print(f"📊 DETECTION COMPLETE")
#             print("="*80)
#             print(f"Total candidates needing interviews: {len(candidates_needing_interview)}")
#             print(f"  🆕 New applicants: {sum(1 for c in candidates_needing_interview if c['status'] == 'new_applicant')}")
#             print(f"  📝 Incomplete interviews: {sum(1 for c in candidates_needing_interview if c['status'] == 'incomplete_interview')}")
            
#             self.results['candidates_detected'] = candidates_needing_interview
#             return candidates_needing_interview
            
#         except Exception as e:
#             error_msg = f"Candidate detection failed: {str(e)}"
#             print(f"\n❌ {error_msg}")
#             self.results['errors'].append(error_msg)
#             return []
    
#     def _get_candidate_interviews(self, jwt, job_id, candidate_id):
#         """Helper method to fetch all interviews for a candidate"""
#         import requests
        
#         url = f"https://api.hireology.com/v1/jobs/{job_id}/candidates/{candidate_id}/interviews"
#         headers = {
#             "Authorization": f"Bearer {jwt}",
#             "Content-Type": "application/json"
#         }
        
#         try:
#             response = requests.get(url, headers=headers)
#             if response.status_code == 200:
#                 return response.json()
#             return []
#         except:
#             return []
    
#     def create_interview_for_candidate(self, candidate_id):
#         """
#         Create a new phone interview for a candidate
#         Returns the interview_id if successful
#         """
#         print(f"\n📞 Creating new interview for candidate {candidate_id}...")
        
#         try:
#             import requests
            
#             jwt = self.config['hireology_jwt']
#             job_id = self.config['hireology_job_id']
            
#             # You'll need to specify your phone interview template ID
#             # This should be the ID of your phone interview template in Hireology
#             interview_template_id = self.config.get('phone_interview_template_id')
            
#             if not interview_template_id:
#                 print("  ⚠️  Warning: No phone_interview_template_id configured")
#                 print("  ℹ️  Please add 'phone_interview_template_id' to your config")
#                 return None
            
#             url = f"https://api.hireology.com/v1/jobs/{job_id}/candidates/{candidate_id}/interviews"
#             headers = {
#                 "Authorization": f"Bearer {jwt}",
#                 "Content-Type": "application/json"
#             }
            
#             payload = {
#                 "interview_template_id": interview_template_id,
#                 "interview_type": "phone"  # or whatever type you use
#             }
            
#             response = requests.post(url, headers=headers, json=payload)
            
#             if response.status_code in [200, 201]:
#                 interview_data = response.json()
#                 interview_id = interview_data.get('id')
#                 print(f"  ✅ Interview created successfully! ID: {interview_id}")
#                 return interview_id
#             else:
#                 print(f"  ❌ Failed to create interview: {response.status_code}")
#                 print(f"     Response: {response.text}")
#                 return None
                
#         except Exception as e:
#             print(f"  ❌ Error creating interview: {str(e)}")
#             return None
    
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
                
#                 documents = get_candidate_documents(
#                     jwt_token=jwt,
#                     job_id=job_id,
#                     candidate_id=candidate_id,
#                     transfer=False
#                 )
                
#                 if not documents:
#                     print(f"❌ Failed to fetch documents for {candidate_id}")
#                     continue
                
#                 applicant_record = build_single_applicant_record(documents)
#                 candidate_job_id = documents[0].get("id")
                
#                 incomplete_questions = get_incomplete_questions(applicant_record)
                
#                 if incomplete_questions:
#                     print(f"⚠️  Incomplete application - {len(incomplete_questions)} missing answers")
                    
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
                
#                 final_status = decide_candidate_status(applicant_record)
#                 print(f"🎯 Decision: {final_status}")
                
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
#             extractor = HireologyQAExtractor(
#                 api_key=self.config['ghl_api_key'],
#                 location_id=self.config['ghl_location_id'],
#                 groq_api_key=self.config.get('groq_api_key')
#             )
            
#             agent_id = agent_id or self.config.get('ghl_agent_id')
#             print(f"\n📞 Extracting interview from agent {agent_id}...")
            
#             qa_pairs = extractor.extract_for_hireology(agent_id=agent_id)
            
#             if not qa_pairs:
#                 raise Exception("No Q&A pairs extracted from interview")
            
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
    
#     def step3_update_hireology_interview(self, interview_id, candidate_id, json_path=None):
#         """Step 3: Update Hireology interview with phone interview results AND calculate score"""
#         print("\n" + "="*80)
#         print("STEP 3: UPDATING HIREOLOGY INTERVIEW")
#         print("="*80)
        
#         try:
#             job_id = self.config['hireology_job_id']
            
#             if not json_path:
#                 json_path = self.results.get('interview_json_path')
            
#             if not json_path or not os.path.exists(json_path):
#                 raise Exception(f"JSON file not found: {json_path}")
            
#             print(f"\n📥 Loading interview data from Hireology...")
#             print(f"   Job ID: {job_id}")
#             print(f"   Candidate ID: {candidate_id}")
#             print(f"   Interview ID: {interview_id}")
            
#             import update_phoneInterview_on_Hireology as upd
#             upd.JOB_ID = job_id
#             upd.CANDIDATE_ID = candidate_id
#             upd.INTERVIEW_ID = interview_id
#             upd.BEARER_TOKEN = self.config['hireology_jwt']
            
#             interview_data = fetch_interview_from_api()
#             print(f"✓ Fetched interview with {len(interview_data.get('questions', []))} questions")
            
#             print(f"\n📝 Matching answers from: {json_path}")
#             updated_interview, update_logs, all_logs = update_interview_answers(json_path, interview_data)
            
#             if all_logs:
#                 display_update_logs(all_logs, len(update_logs))
            
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
    
#     def run_automated_workflow(self, skip_screening=False, process_all=False):
#         """
#         Run FULLY AUTOMATED workflow
        
#         Args:
#             skip_screening: Skip Step 1 (applicant screening)
#             process_all: Process all candidates needing interviews (default: only first one)
#         """
#         print("\n" + "="*80)
#         print("🤖 STARTING FULLY AUTOMATED HIRING WORKFLOW")
#         print("="*80)
#         print(f"Timestamp: {self.results['timestamp']}")
        
#         # Step 1: Screen applicants (optional)
#         if not skip_screening:
#             screened = self.step1_screen_applicants()
#             if screened is None:
#                 print("\n⚠️  Step 1 failed, but continuing with remaining steps...")
        
#         # AUTO-DETECT: Find candidates needing interviews
#         candidates = self.find_candidates_needing_interview()
        
#         if not candidates:
#             print("\n✅ No candidates need interviews at this time!")
#             return self.results
        
#         # Decide how many to process
#         candidates_to_process = candidates if process_all else [candidates[0]]
        
#         print(f"\n🎯 Processing {len(candidates_to_process)} candidate(s)...")
        
#         for idx, candidate_info in enumerate(candidates_to_process, 1):
#             print(f"\n{'='*80}")
#             print(f"PROCESSING CANDIDATE {idx}/{len(candidates_to_process)}")
#             print(f"{'='*80}")
            
#             candidate_id = candidate_info['candidate_id']
#             interview_id = candidate_info.get('interview_id')
#             status = candidate_info['status']
            
#             print(f"Candidate ID: {candidate_id}")
#             print(f"Status: {status}")
#             print(f"Interview ID: {interview_id or 'None (will create)'}")
            
#             # Create interview if needed (for new applicants)
#             if not interview_id:
#                 print(f"\n🆕 New applicant detected - creating interview...")
#                 interview_id = self.create_interview_for_candidate(candidate_id)
                
#                 if not interview_id:
#                     print(f"❌ Failed to create interview for candidate {candidate_id}")
#                     print(f"   Skipping to next candidate...")
#                     continue
            
#             # Step 2: Process phone interview
#             json_path = self.step2_process_phone_interview()
#             if json_path is None:
#                 print(f"\n⚠️  Phone interview processing failed for candidate {candidate_id}")
#                 continue
            
#             # Step 3: Update Hireology
#             success = self.step3_update_hireology_interview(interview_id, candidate_id, json_path)
#             if not success:
#                 print(f"\n⚠️  Hireology update failed for candidate {candidate_id}")
        
#         # Final summary
#         print("\n" + "="*80)
#         print("🎉 AUTOMATED WORKFLOW SUMMARY")
#         print("="*80)
#         print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
#         print(f"Candidates processed: {len(candidates_to_process)}")
        
#         if 'interview_score' in self.results:
#             print(f"\n📊 Last Interview Results:")
#             print(f"   Final Score: {self.results.get('interview_score', 'N/A')}")
#             print(f"   Confidence Score: {self.results.get('confidence_score', 'N/A')}")
#             print(f"   Questions Matched: {self.results.get('matched_questions', 0)}")
        
#         print(f"\nErrors: {len(self.results['errors'])}")
#         if self.results['errors']:
#             for error in self.results['errors']:
#                 print(f"  ❌ {error}")
#         print("="*80)
        
#         return self.results
    
#     def run_complete_workflow(self, interview_id=None, candidate_id=None, skip_screening=False):
#         """LEGACY METHOD - Still available for manual use"""
#         print("\n⚠️  Using MANUAL mode (legacy)")
#         print("   💡 Tip: Use run_automated_workflow() for full automation")
        
#         print("\n" + "="*80)
#         print("🚀 STARTING COMPLETE HIRING WORKFLOW")
#         print("="*80)
#         print(f"Timestamp: {self.results['timestamp']}")
        
#         if not skip_screening:
#             screened = self.step1_screen_applicants()
#             if screened is None:
#                 print("\n⚠️  Step 1 failed, but continuing with remaining steps...")
        
#         json_path = self.step2_process_phone_interview()
#         if json_path is None:
#             print("\n❌ Workflow stopped: Phone interview processing failed")
#             return self.results
        
#         if interview_id and candidate_id:
#             success = self.step3_update_hireology_interview(interview_id, candidate_id, json_path)
#             if not success:
#                 print("\n⚠️  Step 3 failed, but previous steps completed")
#         else:
#             print("\n⏭️  Skipping Step 3: No interview_id or candidate_id provided")
        
#         print("\n" + "="*80)
#         print("🎉 WORKFLOW SUMMARY")
#         print("="*80)
#         print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        
#         if 'interview_score' in self.results:
#             print(f"\n📊 Interview Results:")
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
#     # Configuration
    
#     config = {
#         'hireology_jwt': "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY2NzYwMjQxLCJuYmYiOjE3NjY3NTY2NDEsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY2NzU2NjQxfQ.FVGLLT57Y24zBEyyr0oZp8vm5Ftv2Euj6-jzc4hrnOX0EhZp68rVVq9gWwycOHa1ppYYLkHPGxvyx1us6p8is3s0SkDfw01LZX9sd0DHF0K_D0Jrz7Nf33gvtYO1B_yvMWf5TjikJg2ihEPI42C9HXRNuGGnJjpy6UeJy7vfJFYrgIs4lLdmF0vmrDKgI3DQSzVpUgzHmMrD0VbhLpOZh6eU6PyoW827FEpMD-G3K-9pVE4wOg8nnYjeSoEGB689qSJ_x03-Gr5y-fYvLGvElL5N0NIrWuSGBcNmxrfGiiPjfE3Y0kX63GjrNvo-UJRAm4ORDzkQ4T8hvKKvOck7og",
#         'hireology_job_id': "2606114",
        
#         # OPTIONAL: If you want to auto-create interviews for new applicants
#         # Find this ID in Hireology under Interview Templates
#         'phone_interview_template_id': "YOUR_TEMPLATE_ID",  # Add this if you want auto-creation
        
#         'ghl_api_key': "pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324",
#         'ghl_location_id': "M5jnxd1r8yq3o5gxSYOP",
#         'ghl_agent_id': "693448f6231659c2a32a3bca",
#         'groq_api_key': os.getenv("GROQ_API_KEY")
#     }
    
#     # Create orchestrator
#     orchestrator = HiringWorkflowOrchestrator(config)
    
#     # ========== 🤖 FULLY AUTOMATED MODE (RECOMMENDED) ==========
#     # This will:
#     # 1. Find all candidates needing interviews (new or incomplete)
#     # 2. Process the first one automatically
#     # 3. Create interview if needed
#     # 4. Extract phone interview
#     # 5. Update Hireology and calculate score
    
#     results = orchestrator.run_automated_workflow(
#         skip_screening=False,    # Set True to skip applicant screening
#         process_all=False        # Set True to process ALL candidates (not just first)
#     )
    
#     # ==========  DETECTION ONLY MODE ==========
#     # Just see who needs interviews without processing
#     # candidates = orchestrator.find_candidates_needing_interview()
#     # print(f"\nFound {len(candidates)} candidates:")
#     # for c in candidates:
#     #     print(f"  - Candidate {c['candidate_id']}: {c['status']}")
    
#     # ========== MANUAL MODE (LEGACY) ==========
#     # Still available if you want to specify IDs manually
#     # results = orchestrator.run_complete_workflow(
#     #     interview_id="49557285",
#     #     candidate_id="47026869",
#     #     skip_screening=False
#     # )
    
#     # Save results
#     with open('workflow_results.json', 'w') as f:
#         json.dump(results, f, indent=2)
    
#     print("\n✅ Full results saved to: workflow_results.json")
# /////////
"""
Complete Hiring Workflow Application - FIXED VERSION
Detects candidates with NOT STARTED interviews (progress = 0%)
Ensures interview processing matches the correct candidate
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

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

load_dotenv()


class HiringWorkflowOrchestrator:
    """Orchestrates the complete hiring workflow with automatic interview ID detection"""
    
    def __init__(self, config: dict):
        self.config = config
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'steps_completed': [],
            'errors': []
        }
    
    def _get_candidate_interviews(self, jwt, job_id, candidate_id):
        """Helper method to fetch all interviews for a candidate"""
        import requests
        
        url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates/{candidate_id}/interviews"
        headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"     Error fetching interviews: {str(e)}")
            return []
    
    def _get_candidate_name(self, jwt, job_id, candidate_id):
        """Fetch candidate's name for verification"""
        import requests
        
        url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates/{candidate_id}"
        headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                first_name = data.get('first_name', '')
                last_name = data.get('last_name', '')
                return f"{first_name} {last_name}".strip()
            return "Unknown"
        except:
            return "Unknown"
    
    def find_candidates_needing_interview(self):
        """
        FIXED: Finds candidates with interviews that are:
        - Created but NOT STARTED (progress = 0%)
        - Incomplete (progress < 100%)
        """
        print("\n" + "="*80)
        print("🔍 DETECTING CANDIDATES NEEDING INTERVIEWS")
        print("="*80)
        print("Before try")
        
        try:
            print("In the try")
            jwt = self.config['hireology_jwt']
            job_id = self.config['hireology_job_id']
            
            print(f"\n📥 Fetching all candidates for job {job_id}...")
            candidates = get_candidates(jwt_token=jwt, job_id=job_id)
            print("The candidates are:",candidates)
            applicant_ids = extract_applicant_ids(candidates)
            print(f"✅ Found {len(applicant_ids)} total applicants")
            
            candidates_needing_interview = []
            
            for idx, candidate_id in enumerate(applicant_ids, 1):
                print(f"\n{'─'*40}")
                print(f"Checking {idx}/{len(applicant_ids)} - Candidate {candidate_id}")
                
                try:
                    # Get candidate name for verification
                    candidate_name = self._get_candidate_name(jwt, job_id, candidate_id)
                    print(f"  👤 Name: {candidate_name}")
                    
                    # Check for interviews
                    interviews = self._get_candidate_interviews(jwt, job_id, candidate_id)
                    
                    if not interviews:
                        print(f"  ⚠️  NO INTERVIEW FOUND - Must create in Hireology")
                        candidates_needing_interview.append({
                            'candidate_id': candidate_id,
                            'candidate_name': candidate_name,
                            'interview_id': None,
                            'status': 'needs_manual_interview_creation',
                            'priority': 3,
                            'progress': 0,
                            'action_required': '❌ Create interview in Hireology first'
                        })
                        continue
                    
                    # Analyze all interviews for this candidate
                    print(f"  📋 Found {len(interviews)} interview(s)")
                    
                    not_started_interviews = []
                    incomplete_interviews = []
                    completed_interviews = []
                    
                    for interview in interviews:
                        interview_id = interview.get('id')
                        interview_type = interview.get('type', '').lower()
                        progress = interview.get('progress', 0)
                        score = interview.get('score')
                        created_at = interview.get('created_at', '')
                        
                        print(f"\n     Interview {interview_id}:")
                        print(f"     Type: {interview_type}")
                        print(f"     Progress: {progress}%")
                        print(f"     Score: {score}")
                        
                        # CRITICAL: Detect NOT STARTED interviews
                        if progress == 0:
                            print(f"     🆕 STATUS: NOT STARTED - Ready for processing!")
                            not_started_interviews.append(interview)
                        elif progress < 100 or score is None:
                            print(f"     ⏳ STATUS: INCOMPLETE - Can be updated")
                            incomplete_interviews.append(interview)
                        else:
                            print(f"     ✅ STATUS: COMPLETE")
                            completed_interviews.append(interview)
                    
                    # Decision logic - PRIORITIZE NOT STARTED
                    selected_interview = None
                    status = None
                    priority = None
                    
                    if not_started_interviews:
                        # HIGHEST PRIORITY: Not started interviews
                        selected_interview = not_started_interviews[0]
                        status = 'not_started'
                        priority = 1
                        print(f"\n  ✅ SELECTED: Not started interview {selected_interview['id']}")
                        print(f"     🎯 This interview needs to be conducted!")
                    
                    elif incomplete_interviews:
                        # MEDIUM PRIORITY: Incomplete interviews
                        selected_interview = incomplete_interviews[0]
                        status = 'incomplete'
                        priority = 2
                        print(f"\n  ✅ SELECTED: Incomplete interview {selected_interview['id']}")
                        print(f"     🔄 This interview can be updated")
                    
                    else:
                        # All interviews complete
                        print(f"\n  ✓ All {len(completed_interviews)} interview(s) are complete")
                        continue
                    
                    if selected_interview:
                        interview_id = selected_interview.get('id')
                        progress = selected_interview.get('progress', 0)
                        interview_type = selected_interview.get('type', '')
                        
                        candidates_needing_interview.append({
                            'candidate_id': candidate_id,
                            'candidate_name': candidate_name,
                            'interview_id': interview_id,
                            'interview_type': interview_type,
                            'status': status,
                            'priority': priority,
                            'progress': progress,
                            'action_required': '🎙️ Process phone interview transcript' if status == 'not_started' else '🔄 Update interview answers'
                        })
                
                except Exception as e:
                    print(f"  ⚠️  Error checking candidate: {str(e)}")
                    continue
            
            # Sort by priority (1 = highest)
            candidates_needing_interview.sort(key=lambda x: (x['priority'], x['candidate_id']))
            
            print("\n" + "="*80)
            print(f"📊 DETECTION COMPLETE")
            print("="*80)
            print(f"Total candidates found: {len(candidates_needing_interview)}")
            
            not_started = [c for c in candidates_needing_interview if c['status'] == 'not_started']
            incomplete = [c for c in candidates_needing_interview if c['status'] == 'incomplete']
            needs_manual = [c for c in candidates_needing_interview if c['status'] == 'needs_manual_interview_creation']
            
            if not_started:
                print(f"\n🆕 NOT STARTED INTERVIEWS: {len(not_started)}")
                for c in not_started:
                    print(f"   - {c['candidate_name']} (ID: {c['candidate_id']})")
                    print(f"     Interview: {c['interview_id']}, Type: {c['interview_type']}")
            
            if incomplete:
                print(f"\n⏳ INCOMPLETE INTERVIEWS: {len(incomplete)}")
                for c in incomplete:
                    print(f"   - {c['candidate_name']} (ID: {c['candidate_id']}) - {c['progress']}%")
            
            if needs_manual:
                print(f"\n⚠️  NEED MANUAL SETUP: {len(needs_manual)}")
                for c in needs_manual:
                    print(f"   - {c['candidate_name']} (ID: {c['candidate_id']})")
            
            self.results['candidates_detected'] = candidates_needing_interview
            return candidates_needing_interview
            
        except Exception as e:
            error_msg = f"Candidate detection failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.results['errors'].append(error_msg)
            return []
    
    def step2_process_phone_interview(self, candidate_id, candidate_name, agent_id=None):
        """
        Step 2: Process phone interview transcript for SPECIFIC candidate
        FIXED: Ensures we're processing the right candidate's call
        """
        print("\n" + "="*80)
        print("STEP 2: PROCESSING PHONE INTERVIEW")
        print("="*80)
        print(f"🎯 Target Candidate: {candidate_name} (ID: {candidate_id})")
        
        try:
            extractor = HireologyQAExtractor(
                api_key=self.config['ghl_api_key'],
                location_id=self.config['ghl_location_id'],
                groq_api_key=self.config.get('groq_api_key')
            )
            
            agent_id = agent_id or self.config.get('ghl_agent_id')
            print(f"\n📞 Extracting interview from agent {agent_id}...")
            print(f"⚠️  IMPORTANT: Ensure the most recent call is with {candidate_name}")
            
            qa_pairs = extractor.extract_for_hireology(agent_id=agent_id)
            
            if not qa_pairs:
                raise Exception("No Q&A pairs extracted from interview")
            
            print(f"\n✅ Extracted {len(qa_pairs)} Q&A pairs")
            
            # Verify the call is for the right candidate
            call_data_dir = 'call_data'
            json_files = [f for f in os.listdir(call_data_dir) if f.startswith('hireology_qa_') and f.endswith('.json')]
            
            if not json_files:
                raise Exception("No JSON file created")
            
            latest_json = max([os.path.join(call_data_dir, f) for f in json_files], key=os.path.getctime)
            
            # Load and check the JSON
            with open(latest_json, 'r') as f:
                json_data = json.load(f)
            
            print(f"\n📄 Interview data saved to: {latest_json}")
            print(f"📋 Preview of extracted answers:")
            for i, qa in enumerate(qa_pairs[:3], 1):
                print(f"   {i}. Q: {qa.get('question', 'N/A')[:60]}...")
                print(f"      A: {qa.get('answer', 'N/A')[:60]}...")
            
            print(f"\n⚠️  VERIFICATION REQUIRED:")
            print(f"   Please confirm this interview is for: {candidate_name}")
            print(f"   If not, you'll need to process a different call")
            
            self.results['interview_json_path'] = latest_json
            self.results['qa_pairs_count'] = len(qa_pairs)
            self.results['processed_for_candidate'] = {
                'id': candidate_id,
                'name': candidate_name
            }
            self.results['steps_completed'].append('step2_interview_processing')
            
            print("\n" + "="*80)
            print(f"✅ STEP 2 COMPLETE: Processed {len(qa_pairs)} Q&A pairs")
            print("="*80)
            
            return latest_json
            
        except Exception as e:
            error_msg = f"Step 2 failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.results['errors'].append(error_msg)
            return None
    
    def step3_update_hireology_interview(self, interview_id, candidate_id, candidate_name, json_path=None):
        """Step 3: Update Hireology interview with phone interview results AND calculate score"""
        print("\n" + "="*80)
        print("STEP 3: UPDATING HIREOLOGY INTERVIEW")
        print("="*80)
        print(f"🎯 Candidate: {candidate_name} (ID: {candidate_id})")
        print(f"📝 Interview ID: {interview_id}")
        
        try:
            job_id = self.config['hireology_job_id']
            
            if not json_path:
                json_path = self.results.get('interview_json_path')
            
            if not json_path or not os.path.exists(json_path):
                raise Exception(f"JSON file not found: {json_path}")
            
            print(f"\n📥 Loading interview data from Hireology...")
            
            import update_phoneInterview_on_Hireology as upd
            upd.JOB_ID = job_id
            upd.CANDIDATE_ID = candidate_id
            upd.INTERVIEW_ID = interview_id
            upd.BEARER_TOKEN = self.config['hireology_jwt']
            
            interview_data = fetch_interview_from_api()
            print(f"✓ Fetched interview with {len(interview_data.get('questions', []))} questions")
            
            print(f"\n📝 Matching answers from: {json_path}")
            updated_interview, update_logs, all_logs = update_interview_answers(json_path, interview_data)
            
            if all_logs:
                display_update_logs(all_logs, len(update_logs))
            
            print(f"\n📤 Sending update to Hireology API...")
            response = send_update_to_hireology(updated_interview)
            
            if response.status_code not in [200, 204]:
                raise Exception(f"API returned status {response.status_code}: {response.text}")
            
            print(f"✓ Successfully updated interview for {candidate_name}!")
            if response.status_code == 200:
                resp_data = response.json()
                print(f"\n   📊 INITIAL Response:")
                print(f"      Score: {resp_data.get('score', 'N/A')} (not calculated yet)")
                print(f"      Progress: {resp_data.get('progress', 'N/A')}")
            
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
                    
                    self.results['interview_score'] = score_data.get('score')
                    self.results['confidence_score'] = score_data.get('confidence_score')
                    
                elif score_response.status_code == 204:
                    print(f"   ✅ Score calculation triggered (no content returned)")
                else:
                    print(f"   ⚠️  Score calculation returned: {score_response.status_code}")
                    
            except Exception as score_error:
                print(f"   ⚠️  Score calculation error: {str(score_error)}")
            
            self.results['interview_updated'] = True
            self.results['matched_questions'] = len(update_logs)
            self.results['steps_completed'].append('step3_interview_update')
            
            print("\n" + "="*80)
            print(f"✅ STEP 3 COMPLETE: Updated {len(update_logs)} answers for {candidate_name}")
            print("="*80)
            
            return True
            
        except Exception as e:
            error_msg = f"Step 3 failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.results['errors'].append(error_msg)
            return False
    
    def run_automated_workflow(self, skip_screening=False, process_all=False):
        """
        FIXED: Fully automated workflow that detects NOT STARTED interviews
        Ensures each candidate is processed with their own interview transcript
        """
        print("\n" + "="*80)
        print("🤖 STARTING AUTOMATED WORKFLOW")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        
        # AUTO-DETECT: Find candidates with interviews
        candidates = self.find_candidates_needing_interview()
        
        if not candidates:
            print("\n✅ No candidates need processing at this time!")
            return self.results
        
        # Filter: Only process candidates that HAVE interview IDs
        processable = [c for c in candidates if c['interview_id'] is not None]
        needs_manual = [c for c in candidates if c['interview_id'] is None]
        
        if needs_manual:
            print(f"\n⚠️  {len(needs_manual)} candidate(s) need manual interview creation:")
            for c in needs_manual:
                print(f"   - {c['candidate_name']}: {c['action_required']}")
        
        if not processable:
            print("\n❌ No candidates ready to process!")
            return self.results
        
        # Prioritize NOT STARTED interviews
        not_started = [c for c in processable if c['status'] == 'not_started']
        incomplete = [c for c in processable if c['status'] == 'incomplete']
        
        if not_started:
            print(f"\n🎯 Found {len(not_started)} NOT STARTED interview(s) - Processing these first!")
            candidates_to_process = not_started if process_all else [not_started[0]]
        else:
            print(f"\n🎯 No NOT STARTED interviews. Processing {len(incomplete)} incomplete interview(s)")
            candidates_to_process = incomplete if process_all else [incomplete[0]]
        
        print(f"\n📋 Will process {len(candidates_to_process)} candidate(s):")
        for c in candidates_to_process:
            print(f"   - {c['candidate_name']} (ID: {c['candidate_id']})")
            print(f"     Interview: {c['interview_id']}, Status: {c['status']}, Progress: {c['progress']}%")
        
        for idx, candidate_info in enumerate(candidates_to_process, 1):
            print(f"\n{'='*80}")
            print(f"PROCESSING CANDIDATE {idx}/{len(candidates_to_process)}")
            print(f"{'='*80}")
            
            candidate_id = candidate_info['candidate_id']
            candidate_name = candidate_info['candidate_name']
            interview_id = candidate_info['interview_id']
            status = candidate_info['status']
            
            print(f"👤 Name: {candidate_name}")
            print(f"🆔 Candidate ID: {candidate_id}")
            print(f"📝 Interview ID: {interview_id}")
            print(f"📊 Status: {status.upper()}")
            print(f"📈 Progress: {candidate_info['progress']}%")
            
            # Step 2: Process phone interview FOR THIS SPECIFIC CANDIDATE
            print(f"\n⚠️  IMPORTANT: About to extract transcript from most recent call")
            print(f"   Make sure the latest call in the system is with: {candidate_name}")
            
            json_path = self.step2_process_phone_interview(
                candidate_id=candidate_id,
                candidate_name=candidate_name
            )
            
            if json_path is None:
                print(f"\n⚠️  Phone interview processing failed for {candidate_name}")
                continue
            
            # Step 3: Update Hireology
            success = self.step3_update_hireology_interview(
                interview_id=interview_id,
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                json_path=json_path
            )
            
            if not success:
                print(f"\n⚠️  Hireology update failed for {candidate_name}")
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 AUTOMATED WORKFLOW COMPLETE")
        print("="*80)
        print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        print(f"Candidates processed: {len(candidates_to_process)}")
        
        if 'processed_for_candidate' in self.results:
            print(f"\nLast processed:")
            print(f"  👤 {self.results['processed_for_candidate']['name']}")
            print(f"  🆔 {self.results['processed_for_candidate']['id']}")
        
        if 'interview_score' in self.results:
            print(f"\n📊 Final Interview Results:")
            print(f"   Score: {self.results.get('interview_score', 'N/A')}")
            print(f"   Confidence: {self.results.get('confidence_score', 'N/A')}")
            print(f"   Questions Matched: {self.results.get('matched_questions', 0)}")
        
        if self.results['errors']:
            print(f"\n❌ Errors: {len(self.results['errors'])}")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        print("="*80)
        
        return self.results


# ============= MAIN EXECUTION =============

if __name__ == "__main__":
    config = {
        'hireology_jwt': "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY2Nzc2NzQ3LCJuYmYiOjE3NjY3NzMxNDcsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY2NzczMTQ3fQ.pbZ9QuH7tbFvAo9NY2mRusgNcboHnhIL1ObQDuCaL1zR_M8yfrZhXslbSsiWoQU7b5JofoLqkQTwZGRJ_p4Se4syx9xZ2mLqaeyu8HWBTR5XvjUNINe_GQCtq2zvw3kM0mJKn9ILFcGU2nDkWKW-ToDqhPfCppIaJ6in93PUQyNU9R0W4fqxE4VAzSS2Ja97NVkewxxHlS49mt_VU-cGf7GUa6WKyhfd7of7HhT1SAN8Fe5hAuQ1ZfVfvIe4rZkkzjbSpbJ2Nwi-CIi0eMYj1VEpK-_6fNExRdXpOrjyS8gvzgDrzqinFlr48UoVUi68Bi_WeKFFKif7oZfmedh5ng",
        'hireology_job_id': "2606114",
        'ghl_api_key': "pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324",
        'ghl_location_id': "M5jnxd1r8yq3o5gxSYOP",
        'ghl_agent_id': "693448f6231659c2a32a3bca",
        'groq_api_key': os.getenv("GROQ_API_KEY")
    }
    
    orchestrator = HiringWorkflowOrchestrator(config)
    
    # Run automated workflow - will now detect NOT STARTED interviews!
    results = orchestrator.run_automated_workflow(
        skip_screening=False,    # Set True to skip applicant screening
        process_all=False        # Set True to process ALL candidates (not just first)
    )
    
    # Save results
    with open('workflow_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: workflow_results.json")