
"""
Complete Hiring Workflow Application
Orchestrates: Applicant Screening -> Phone Call -> Wait for Completion -> 
             Phone Interview Processing -> Hireology Update -> Score Calculation
"""

import os
import json
import time
from datetime import datetime, timedelta
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


class CallStatusChecker:
    """Helper class to check call status from GoHighLevel"""
    

    def __init__(self, api_key: str, location_id: str, agent_id: str):
        self.api_key = api_key
        self.location_id = location_id
        self.agent_id = agent_id
        self.base_url = "https://services.leadconnectorhq.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }

    def get_call_status(self, call_id: str):
        """
        Check real-time call status using callId
        """
        url = f"{self.base_url}/voice-ai/call/{call_id}"
        params = {
            "locationId": self.location_id,
            "agentId": self.agent_id
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error checking call status: {e}")
            return None

    
    # def get_recent_call_for_phone(self, phone_number: str, since_time: datetime = None):
    #     """
    #     Check if there's a completed call to a specific phone number
        
    #     Args:
    #         phone_number: The phone number to check for
    #         since_time: Optional - only look for calls after this time
        
    #     Returns:
    #         Call data if a completed call is found, None otherwise
    #     """
    #     url = f"{self.base_url}/voice-ai/dashboard/call-logs"
        
    #     params = {
    #         "locationId": self.location_id,
    #         "agentId": self.agent_id
    #     }
        
    #     try:
    #         response = requests.get(url, headers=self.headers, params=params)
    #         response.raise_for_status()
    #         call_logs = response.json()
            
    #         if not call_logs or 'data' not in call_logs:
    #             return None
            
    #         # Normalize the phone number for comparison
    #         normalized_target = self._normalize_phone(phone_number)
            
    #         for call in call_logs.get('data', []):
    #             # Check if this call matches the phone number
    #             call_to_phone = self._normalize_phone(call.get('toNumber', '') or call.get('phoneNumber', ''))
                
    #             if call_to_phone == normalized_target:
    #                 # Check if call was after the since_time (if provided)
    #                 if since_time:
    #                     call_time_str = call.get('createdAt', '')
    #                     if call_time_str:
    #                         try:
    #                             # Parse ISO format datetime
    #                             call_time = datetime.fromisoformat(call_time_str.replace('Z', '+00:00'))
    #                             since_time_utc = since_time.replace(tzinfo=call_time.tzinfo) if since_time.tzinfo is None else since_time
    #                             if call_time < since_time_utc:
    #                                 continue
    #                         except:
    #                             pass
                    
    #                 # Check if call has reached a terminal status (completed, failed, cancelled, etc.)
    #                 status = call.get('status')
    #                 if call.get('transcript') or status in ['completed', 'failed', 'busy', 'no-answer', 'cancelled', 'voicemail']:
    #                     return call
            
    #         return None
            
    #     except requests.exceptions.RequestException as e:
    #         print(f"Error checking call status: {e}")
    #         return None
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison (remove non-digits)"""
        if not phone:
            return ""
        return ''.join(filter(str.isdigit, str(phone)))
    
    # def wait_for_call_completion(
    #     self, 
    #     phone_number: str, 
    #     timeout_minutes: int = 7, 
    #     poll_interval_seconds: int = 10,
    #     call_start_time: datetime = None
    # ) -> dict:
    #     """
    #     Wait for a call to be completed
        
    #     Args:
    #         phone_number: Phone number to monitor
    #         timeout_minutes: Maximum time to wait
    #         poll_interval_seconds: How often to check for call completion
    #         call_start_time: When the call was initiated (to filter old calls)
        
    #     Returns:
    #         Call data when completed, or None if timeout
    #     """
    #     start_time = datetime.now()
    #     timeout = timedelta(minutes=timeout_minutes)
        
    #     print(f"\n⏳ Waiting for call to complete...")
    #     print(f"   Phone: {phone_number}")
    #     print(f"   Timeout: {timeout_minutes} minutes")
    #     print(f"   Polling every {poll_interval_seconds} seconds")
        
    #     while datetime.now() - start_time < timeout:
    #         # Check for completed call
    #         completed_call = self.get_recent_call_for_phone(
    #             phone_number, 
    #             since_time=call_start_time
    #         )
            
    #         if completed_call:
    #             status = completed_call.get('status', 'unknown')
    #             print(f"\n✅ Call finished! Status: {status}")
    #             print(f"   Call ID: {completed_call.get('id', 'N/A')}")
    #             print(f"   Duration: {completed_call.get('duration', 'N/A')} seconds")
    #             return completed_call
            
    #         # Wait before next poll
    #         elapsed = datetime.now() - start_time
    #         remaining = timeout - elapsed
    #         print(f"   ⏳ Waiting... (elapsed: {int(elapsed.total_seconds())}s, remaining: {int(remaining.total_seconds())}s)")
    #         time.sleep(poll_interval_seconds)
        
    #     print(f"\n⚠️ Timeout: Call did not complete within {timeout_minutes} minutes")
    #     return None

def wait_for_call_completion(call_checker, call_id, timeout=300, interval=5):
    """
    Wait until callStatus becomes completed
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        data = call_checker.get_call_status(call_id)

        if not data:
            time.sleep(interval)
            continue

        call_status = data.get("callStatus")

        print(f"Current callStatus: {call_status}")

        if call_status == "completed":
            return data

        if call_status in ["failed", "busy", "no-answer", "cancelled"]:
            return data

        time.sleep(interval)

    raise TimeoutError("Call did not finish within timeout")


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
        - ghl_token_id: GoHighLevel token ID for making calls
        - ghl_from_phone: Phone number to call from
        - groq_api_key: Groq API key (optional)
        - call_timeout_minutes: Max time to wait for call (default: 15)
        - poll_interval_seconds: How often to check call status (default: 10)
        """
        self.config = config
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'steps_completed': [],
            'errors': [],
            'candidates_called': []
        }
        
        # Initialize call status checker
        self.call_checker = CallStatusChecker(
            api_key=config['ghl_api_key'],
            location_id=config['ghl_location_id'],
            agent_id=config['ghl_agent_id']
        )
    
    def step1_screen_applicants(self):
        """Step 1: Screen all applicants for a job and fetch existing candidates"""
        print("\n" + "="*80)
        print("STEP 1: SCREENING APPLICANTS")
        print("="*80)
        
        try:
            jwt = self.config['hireology_jwt']
            job_id = self.config['hireology_job_id']
            
            screened_applicants = []
            candidates_to_call = []  # Applicants with status "Candidate"
            
            # ========== PART A: Screen new applicants (status = "Applicant") ==========
            print(f"\n🔍 Fetching NEW applicants for job {job_id}...")
            candidates = get_candidates(jwt_token=jwt, job_id=job_id)
            print("The candidates are:", candidates)
            applicant_ids = extract_applicant_ids(candidates)
            print(f"✅ Found {len(applicant_ids)} new applicants to screen")
            
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
                
                # Use phone from config if this is the target candidate
                if str(candidate_id) == str(self.config.get('target_candidate_id')):
                    candidate_phone = self.config.get('candidate_phone') or candidate_phone
                
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
                # ///////////////////$$$$$$$$ Uncomment here must//////////
                final_status = decide_candidate_status(applicant_record)
                # print(f"🎯 Decision: {final_status}")
                # ////////////////////////%%%%%%%%%%55 must comment here ////////
                # final_status = "Candidate"
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
                # ///////////////  uncomment here ///////////////
                print(f"🔄 Updating status to '{final_status}'...")
                update_candidate_status_response=update_candidate_status(
                    jwt_token=jwt,
                    job_id=job_id,
                    candidate_id=candidate_id,
                    status=final_status
                )
                
                print("The update candidate status response is:", update_candidate_status_response)

                applicant_data = {
                    'candidate_id': candidate_id,
                    'candidate_job_id': candidate_job_id,
                    'email': applicant_record["email"],
                    'status': final_status,
                    'record': applicant_record
                }
                # candidate_phone = update_candidate_status_response[0].get("home_phone") or documents[0].get("cell_phone") 


                # ADD PHONE ONLY IF STATUS IS "Candidate"
                if final_status == "Candidate":
                    applicant_data['phone'] = candidate_phone
                    candidates_to_call.append(applicant_data)
                    print(f"Candidate marked for phone interview: {candidate_phone}")

                screened_applicants.append(applicant_data)
            
            # ========== PART B: Fetch existing Candidates who need calls ==========
            print(f"\n{'─'*80}")
            print("🔍 Also fetching EXISTING candidates (already in Candidate status)...")
            print(f"{'─'*80}")
            
            try:
                # Fetch candidates with "Candidate" status
                url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates"
                headers = {
                    "Authorization": f"Bearer {jwt}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                params = {
                    "filter[status]": "Candidate",
                    "sort_dir": "desc",
                    "sort": "date",
                    "page_size": 10
                }
                
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                existing_candidates = response.json()
                
                existing_candidate_ids = extract_applicant_ids(existing_candidates)
                print(f"✅ Found {len(existing_candidate_ids)} existing candidates")
                
                # Add existing candidates to the call list
                for candidate_id in existing_candidate_ids:
                    # Skip if already in our list
                    if any(c.get('candidate_id') == candidate_id for c in candidates_to_call):
                        continue
                    
                    # Get documents for phone number
                    documents = get_candidate_documents(
                        jwt_token=jwt,
                        job_id=job_id,
                        candidate_id=candidate_id,
                        transfer=False
                    )
                    
                    if documents:
                        candidate_phone = documents[0].get("home_phone") or documents[0].get("cell_phone")
                        candidate_job_id = documents[0].get("id")
                        
                        if candidate_phone:
                            candidate_data = {
                                'candidate_id': candidate_id,
                                'candidate_job_id': candidate_job_id,
                                'phone': candidate_phone,
                                'status': 'Candidate',
                                'email': documents[0].get("email", "")
                            }
                            candidates_to_call.append(candidate_data)
                            print(f"📞 Existing candidate added for calling: {candidate_id} - {candidate_phone}")
                
            except Exception as e:
                print(f"⚠️ Could not fetch existing candidates: {str(e)}")
            
            self.results['screened_applicants'] = screened_applicants
            self.results['candidates_to_call'] = candidates_to_call
            self.results['steps_completed'].append('step1_screening')
            
            print("\n" + "="*80)
            print(f"✅ STEP 1 COMPLETE: Screened {len(screened_applicants)} new applicants")
            print(f"   Total candidates to call: {len(candidates_to_call)}")
            print("="*80)
            
            return candidates_to_call
            
        except Exception as e:
            error_msg = f"Step 1 failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.results['errors'].append(error_msg)
            return None
    
    def step1b_make_call_and_wait(self, candidate: dict) -> dict:
        """
        Step 1B: Make a call to a candidate and wait for completion
        
        Args:
            candidate: Candidate data with phone number
        
        Returns:
            Completed call data or None
        """
        print("\n" + "="*80)
        print(f"STEP 1B: CALLING CANDIDATE")
        print("="*80)
        
        phone = candidate.get('phone')
        if not phone:
            print(f"❌ No phone number for candidate {candidate.get('candidate_id')}")
            return None
        
        try:
            # Record the time before making the call
            call_start_time = datetime.now()
            
            # Make the call
            print(f"\n📞 Initiating call to {phone}...")
            call_result = make_trial_call(
                to_phone_number=phone,
                from_phone_number=self.config.get('ghl_from_phone', '+18439407924'),
                agent_id=self.config['ghl_agent_id'],
                location_id=self.config['ghl_location_id'],
                token_id=self.config['ghl_token_id'],
                test_scenario="OUTBOUND"
            )
            
            if 'error' in call_result:
                print(f"❌ Failed to initiate call: {call_result.get('error')}")
                return None
            
            print(f"✅ Call initiated successfully!")
            
            # Wait for call to complete
            timeout = self.config.get('call_timeout_minutes', 15)
            interval = self.config.get('poll_interval_seconds', 10)
            
            # Extract call ID (support both conversationId and id)
            call_id = call_result.get("_id") or call_result.get("id") or call_result.get("callId")
            print("The call id is:", call_id)
            if not call_id:
                print(f"❌ Could not extract Call ID from response: {call_result}")
                return None
            
            print(f"⏳ Waiting for call completion... (Call ID: {call_id})")
            
            # Use the global wait_for_call_completion function
            # Convert timeout from minutes to seconds
            completed_call = wait_for_call_completion(
                call_checker=self.call_checker,
                call_id=call_id,
                timeout=timeout * 60,
                interval=interval
            )
            
            if completed_call:
                self.results['candidates_called'].append({
                    'candidate_id': candidate.get('candidate_id'),
                    'phone': phone,
                    'call_id': completed_call.get('id'),
                    'duration': completed_call.get('duration'),
                    'status': 'completed'
                })
                return completed_call
            else:
                self.results['candidates_called'].append({
                    'candidate_id': candidate.get('candidate_id'),
                    'phone': phone,
                    'status': 'timeout'
                })
                return None
            
        except Exception as e:
            error_msg = f"Call step failed for {phone}: {str(e)}"
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
            print(f"\n Extracting interview from agent {agent_id}...")
            
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
        """Run only the screening step (Step 1) - no calls"""
        print("\n" + "="*80)
        print("🚀 RUNNING SCREENING ONLY WORKFLOW")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        
        screened = self.step1_screen_applicants()
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 SCREENING COMPLETE")
        print("="*80)
        print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        print(f"Candidates to call: {len(self.results.get('candidates_to_call', []))}")
        print(f"\nErrors: {len(self.results['errors'])}")
        if self.results['errors']:
            for error in self.results['errors']:
                print(f"  ❌ {error}")
        print("="*80)
        
        return self.results
    
    def run_screening_with_calls(self):
        """
        Run screening (Step 1), then for each candidate:
        - Make a call (Step 1B)
        - Wait for call completion
        - Process transcript (Step 2)
        - Update Hireology (Step 3)
        """
        print("\n" + "="*80)
        print("🚀 RUNNING COMPLETE WORKFLOW WITH CALLS")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        
        # Step 1: Screen applicants
        candidates_to_call = self.step1_screen_applicants()
        
        if not candidates_to_call:
            print("\n⚠️ No candidates to call. Workflow complete.")
            return self.results
        
        print(f"\n📋 Processing {len(candidates_to_call)} candidate(s) for phone interview...")
        
        for idx, candidate in enumerate(candidates_to_call, 1):
            print(f"\n{'='*80}")
            print(f"PROCESSING CANDIDATE {idx}/{len(candidates_to_call)}")
            print(f"  ID: {candidate.get('candidate_id')}")
            print(f"  Phone: {candidate.get('phone')}")
            print(f"{'='*80}")
            
            # Step 1B: Make call and wait for completion
            completed_call = self.step1b_make_call_and_wait(candidate)
            
            if not completed_call:
                print(f"\n⚠️ Call did not complete for candidate {candidate.get('candidate_id')}")
                print("   Skipping to next candidate...")
                continue
            
            # Step 2: Process phone interview transcript
            json_path = self.step2_process_phone_interview()
            
            if not json_path:
                print(f"\n⚠️ Failed to process interview for candidate {candidate.get('candidate_id')}")
                continue
            
            # Step 3: Update Hireology
            success = self.step3_update_hireology_interview(
                candidate_id=candidate.get('candidate_id'),
                json_path=json_path
            )
            
            if success:
                print(f"\n✅ Successfully processed candidate {candidate.get('candidate_id')}")
            else:
                print(f"\n⚠️ Failed to update Hireology for candidate {candidate.get('candidate_id')}")
        
        # Final summary
        print("\n" + "="*80)
        print("🎉 COMPLETE WORKFLOW SUMMARY")
        print("="*80)
        print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        print(f"Candidates called: {len(self.results['candidates_called'])}")
        
        for call_info in self.results['candidates_called']:
            status_icon = "✅" if call_info.get('status') == 'completed' else "⚠️"
            print(f"  {status_icon} {call_info.get('candidate_id')}: {call_info.get('status')}")
        
        if 'interview_score' in self.results:
            print(f"\n📊 Latest Interview Results:")
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
    
    def run_complete_workflow(self, candidate_id=None):
        """
        Run the complete hiring workflow with call integration:
        Step 1: Screen applicants -> Find "Candidate" status
        Step 1B: Make call -> Wait for completion
        Step 2: Process call transcript from GHL
        Step 3: Update Hireology interview
        
        Args:
            candidate_id: Optional - if provided, uses this specific candidate
                         if not provided, processes all candidates with "Candidate" status
        """
        print("\n" + "="*80)
        print("🚀 STARTING COMPLETE HIRING WORKFLOW")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        
        # Step 1: Screen applicants
        candidates_to_call = self.step1_screen_applicants()
        
        if not candidates_to_call:
            print("\n No candidates to call after screening.")
            # If a specific candidate_id was provided, try to continue with existing transcript
            if candidate_id:
                print(f"   Attempting to process existing transcript for candidate {candidate_id}...")
                json_path = self.step2_process_phone_interview()
                if json_path:
                    self.step3_update_hireology_interview(candidate_id, json_path)
            return self.results
        
        print(f"\n Processing {len(candidates_to_call)} candidate(s) for phone interview...")
        
        # Process each candidate
        for idx, candidate in enumerate(candidates_to_call, 1):
            current_candidate_id = candidate.get('candidate_id')
            
            print(f"\n{'='*80}")
            print(f"PROCESSING CANDIDATE {idx}/{len(candidates_to_call)}")
            print(f"  ID: {current_candidate_id}")
            print(f"  Phone: {candidate.get('phone')}")
            print(f"{'='*80}")
            
# //////////////////  must uncomment this line to make call///////////
            # Step 1B: Make call and wait for completion
            completed_call = self.step1b_make_call_and_wait(candidate)
            # completed_call = True

            if not completed_call:
                print(f"\n Call did not complete for candidate {current_candidate_id}")
                print("   Skipping to next candidate...")
                continue
            
            # Step 2: Process phone interview transcript
            json_path = self.step2_process_phone_interview()
            
            if not json_path:
                print(f"\n Failed to process interview for candidate {current_candidate_id}")
                continue
            
            # Step 3: Update Hireology
            success = self.step3_update_hireology_interview(
                candidate_id=current_candidate_id,
                json_path=json_path
            )
            
            if success:
                print(f"\n Successfully processed candidate {current_candidate_id}")
            else:
                print(f"\n Failed to update Hireology for candidate {current_candidate_id}")
        
        # Final summary
        print("\n" + "="*80)
        print(" COMPLETE WORKFLOW SUMMARY")
        print("="*80)
        print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        print(f"Candidates called: {len(self.results['candidates_called'])}")
        
        for call_info in self.results['candidates_called']:
            status_icon = "" if call_info.get('status') == 'completed' else "⚠️"
            print(f"  {status_icon} {call_info.get('candidate_id')}: {call_info.get('status')}")
        
        # Display score if available
        if 'interview_score' in self.results:
            print(f"\n Latest Interview Results:")
            print(f"   Interview ID: {self.results.get('interview_id', 'N/A')}")
            print(f"   Final Score: {self.results.get('interview_score', 'N/A')}")
            print(f"   Confidence Score: {self.results.get('confidence_score', 'N/A')}")
            print(f"   Questions Matched: {self.results.get('matched_questions', 0)}")
        
        print(f"\nErrors: {len(self.results['errors'])}")
        if self.results['errors']:
            for error in self.results['errors']:
                print(f"   {error}")
        print("="*80)
        
        return self.results

from auto_monitor import start_auto_monitor
from applicant_id_fetcher import get_applicants_info
from Hirology_jwt_need_checker import get_valid_jwt
from ghl_token_id_needed import get_valid_ghl_token
def run_auto_monitor(job_id="2606114", check_interval=60):
    """
    Start automatic monitoring for new applicants
    
    Usage:
        run_auto_monitor()  # Use defaults
        run_auto_monitor(job_id="YOUR_JOB_ID", check_interval=120)
    """

    
    start_auto_monitor(
        orchestrator_class=HiringWorkflowOrchestrator,
        get_applicants_func=get_applicants_info,
        get_hireology_token_func=get_valid_jwt,
        get_ghl_token_func=get_valid_ghl_token,
        job_id=job_id,
        check_interval=check_interval
    )


# ============= MAIN EXECUTION =============
from applicant_id_fetcher import get_applicants_info
# from Hirology_jwt_need_checker import get_valid_jwt
# from ghl_token_id_needed import get_valid_ghl_token
if __name__ == "__main__":
    print("New execution started")
    jwt = get_valid_jwt()
    print("The extracted tken is :",jwt)
    job_id = "2606114"
    
    ghl_token_id = get_valid_ghl_token()
    print("The extracted ghl token is :", ghl_token_id)
    print("\n" + "="*80)
    print("Fetching applicants...")
    print("="*80)
    applicants = get_applicants_info(jwt, job_id)
    
    

    if not applicants:
        print("No applicants found for this job. Proceeding to Auto-Monitor...")
    else:
        print(f"Found {len(applicants)} applicants for job ID {job_id}")
        print("the applicants are:")
        for i, applicant in enumerate(applicants):
            print(f"[{i}] ID: {applicant['id']} | Phone: {applicant['phone']}")


    for i, applicant in enumerate(applicants):
        print(f"[{i}] ID: {applicant['id']} | Phone: {applicant['phone']}")
        candidate_id = applicants[i]["id"]
        candidate_phone = applicants[i]["phone"]

        print(f" Using Candidate ID: {candidate_id}")
        print(f" Candidate Phone: {candidate_phone}")
        
    
    
    # GHL Token ID (for making calls - this needs to be a valid session token)
    
    # Configuration
        config = {
            'hireology_jwt': jwt,
            'hireology_job_id': job_id,
            'ghl_api_key': "pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324",
            'ghl_location_id': "M5jnxd1r8yq3o5gxSYOP",
            'ghl_agent_id': "693448f6231659c2a32a3bca",
            'ghl_token_id': ghl_token_id,
            'ghl_from_phone': "+18439407924",
            'ghl_to_phone': candidate_phone,
            'groq_api_key': os.getenv("GROQ_API_KEY"),
            # Call waiting settings
            'call_timeout_minutes': 15,  # Max time to wait for call completion
            'poll_interval_seconds': 10,  # How often to check for call completion
            'candidate_phone': candidate_phone,
            'target_candidate_id': candidate_id
        }
    
    # Create orchestrator
        orchestrator = HiringWorkflowOrchestrator(config)
    
    # ========== USAGE EXAMPLES ==========
    
    # EXAMPLE 1: Run complete workflow (RECOMMENDED)
    # This will: Screen -> Call candidates -> Wait for call -> Process transcript -> Update Hireology
        results = orchestrator.run_complete_workflow(candidate_id=candidate_id)
    
    # EXAMPLE 2: Run only screening (Step 1) - no calls
    # results = orchestrator.run_screening_only()
    
    # EXAMPLE 3: Run only interview workflow (Steps 2 & 3) - for when call already happened
    # results = orchestrator.run_interview_workflow(candidate_id=candidate_id)
    
    # EXAMPLE 4: Run screening with calls (alternative method)
    # results = orchestrator.run_screening_with_calls()
    
        # Save results to file
        with open('workflow_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n✅ Full results saved to: workflow_results.json")
 # Start the automatic monitor
    # This will:
    # 1. Check for new applicants every 60 seconds
    # 2. Automatically call them
    # 3. Process the interview
    print("Starting Auto-Monitor...")
    run_auto_monitor()