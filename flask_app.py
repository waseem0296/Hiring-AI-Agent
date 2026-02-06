"""
Complete Hiring Workflow Flask API - Single File Solution
Run once and it stays in monitoring mode forever, processing new applicants automatically.
All logs appear in real-time in the terminal where you run it.

Usage:
    python flask_hiring_workflow.py

Features:
- Auto-monitoring starts automatically on launch
- Real-time logs in terminal
- REST API endpoints available
- Continuous operation
- All original functionality preserved
"""

import os
import json
import time
import threading
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
from applicant_id_fetcher import get_applicants_info
from Hirology_jwt_need_checker import get_valid_jwt
from ghl_token_id_needed import get_valid_ghl_token

# Flask imports
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

# ============= Configuration =============
JOB_ID = "2606114"
CHECK_INTERVAL = 60  # seconds between checks for new applicants
GHL_API_KEY = "pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324"
GHL_LOCATION_ID = "M5jnxd1r8yq3o5gxSYOP"
GHL_AGENT_ID = "693448f6231659c2a32a3bca"
GHL_FROM_PHONE = "+18439407924"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ============= Global State =============
processed_candidates = set()  # Track processed candidate IDs
monitoring_active = True


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
        """Check real-time call status using callId"""
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


def wait_for_call_completion(call_checker, call_id, timeout=300, interval=5):
    """Wait until callStatus becomes completed"""
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
            candidates_to_call = []
            
            # Screen new applicants
            print(f"\n🔍 Fetching NEW applicants for job {job_id}...")
            candidates = get_candidates(jwt_token=jwt, job_id=job_id)
            applicant_ids = extract_applicant_ids(candidates)
            print(f"✅ Found {len(applicant_ids)} new applicants to screen")
            
            for idx, candidate_id in enumerate(applicant_ids, 1):
                print(f"\n{'─'*80}")
                print(f"Processing Applicant {idx}/{len(applicant_ids)} - ID: {candidate_id}")
                print(f"{'─'*80}")
                
                documents = get_candidate_documents(
                    jwt_token=jwt,
                    job_id=job_id,
                    candidate_id=candidate_id,
                    transfer=False
                )
                
                if not documents:
                    print(f"Failed to fetch documents for {candidate_id}")
                    continue
                
                applicant_record = build_single_applicant_record(documents)
                candidate_job_id = documents[0].get("id")
                candidate_phone = documents[0].get("home_phone") or documents[0].get("cell_phone")
                
                if str(candidate_id) == str(self.config.get('target_candidate_id')):
                    candidate_phone = self.config.get('candidate_phone') or candidate_phone
                
                incomplete_questions = get_incomplete_questions(applicant_record)
                
                if incomplete_questions:
                    print(f"⚠️  Incomplete application - {len(incomplete_questions)} missing answers")
                    
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
                
                final_status = decide_candidate_status(applicant_record)
                
                if final_status == "Inactive":
                    rejection_reason = get_rejection_reason(applicant_record)
                    print(f"Sending rejection email...")
                    
                    email_sent = send_rejection_email(
                        jwt_token=jwt,
                        candidate_job_id=candidate_job_id,
                        candidate_email=applicant_record["email"],
                        job_name=applicant_record["job_name"],
                        rejection_reason=rejection_reason
                    )
                
                print(f"🔄 Updating status to '{final_status}'...")
                update_candidate_status_response = update_candidate_status(
                    jwt_token=jwt,
                    job_id=job_id,
                    candidate_id=candidate_id,
                    status=final_status
                )

                applicant_data = {
                    'candidate_id': candidate_id,
                    'candidate_job_id': candidate_job_id,
                    'email': applicant_record["email"],
                    'status': final_status,
                    'record': applicant_record
                }

                if final_status == "Candidate":
                    applicant_data['phone'] = candidate_phone
                    candidates_to_call.append(applicant_data)
                    print(f"Candidate marked for phone interview: {candidate_phone}")

                screened_applicants.append(applicant_data)
            
            # Fetch existing Candidates
            print(f"\n{'─'*80}")
            print("🔍 Also fetching EXISTING candidates (already in Candidate status)...")
            print(f"{'─'*80}")
            
            try:
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
                
                for candidate_id in existing_candidate_ids:
                    if any(c.get('candidate_id') == candidate_id for c in candidates_to_call):
                        continue
                    
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
        """Step 1B: Make a call to a candidate and wait for completion"""
        print("\n" + "="*80)
        print(f"STEP 1B: CALLING CANDIDATE")
        print("="*80)
        
        phone = candidate.get('phone')
        if not phone:
            print(f"❌ No phone number for candidate {candidate.get('candidate_id')}")
            return None
        
        try:
            call_start_time = datetime.now()
            
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
            
            timeout = self.config.get('call_timeout_minutes', 15)
            interval = self.config.get('poll_interval_seconds', 10)
            
            call_id = call_result.get("_id") or call_result.get("id") or call_result.get("callId")
            print("The call id is:", call_id)
            
            if not call_id:
                print(f"❌ Could not extract Call ID from response: {call_result}")
                return None
            
            print(f"⏳ Waiting for call completion... (Call ID: {call_id})")
            
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
                    'status': completed_call.get('callStatus')
                })
                print("Call status after completion:", completed_call.get('callStatus'))
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
    
    def check_interview_postponement(self, json_path: str) -> bool:
        """Check if the interview should be skipped based on duration and postponing words"""
        POSTPONING_PHRASES = [
            "busy now", "busy right now", "can we talk later", "talk later",
            "can you postpone", "can you postponed", "postpone the interview",
            "reschedule", "call me back", "call back later", "not a good time",
            "bad time", "can't talk now", "cannot talk now", "can't talk right now",
            "in a meeting", "at work", "driving", "i'm driving", "call me later",
            "later please", "some other time", "another time", "not right now",
            "give me a minute", "hold on", "wait a moment", "i'm occupied",
            "occupied right now", "schedule for another day", "different time",
            "not available", "unavailable", "can we do this later",
            "can we reschedule", "talk tomorrow", "call tomorrow"
        ]
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            call_info = data.get('call_info', {})
            duration = call_info.get('duration', 0)
            
            qa_pairs = data.get('qa_pairs', [])
            top_7_qa = qa_pairs[:7] if len(qa_pairs) >= 7 else qa_pairs
            
            postponing_found = False
            for qa in top_7_qa:
                answer = qa.get('answer', '').lower()
                for phrase in POSTPONING_PHRASES:
                    if phrase.lower() in answer:
                        postponing_found = True
                        print(f"   ⚠️ Postponing phrase found: '{phrase}' in answer: '{qa.get('answer', '')[:50]}...'")
                        break
                if postponing_found:
                    break
            
            if duration < 100 and postponing_found:
                print(f"\n   🚫 Interview postponement detected:")
                print(f"      - Duration: {duration} seconds (< 100 seconds)")
                print(f"      - Postponing words found in top 7 questions")
                print(f"      - Skipping Hireology update for this candidate")
                return True
            elif postponing_found:
                print(f"\n   ⚠️ Postponing words found in answers but duration is {duration} seconds")
                return True
            
            return False
            
        except Exception as e:
            print(f"   ⚠️ Error checking interview postponement: {str(e)}")
            return False
    
    def step2_process_phone_interview(self, agent_id=None):
        """Step 2: Process most recent phone interview transcript"""
        print("\n" + "="*80)
        print("STEP 2: PROCESSING PHONE INTERVIEW")
        print("="*80)
        
        try:
            extractor = HireologyQAExtractor(
                api_key=self.config['ghl_api_key'],
                location_id=self.config['ghl_location_id'],
                groq_api_key=self.config.get('groq_api_key')
            )
            
            agent_id = agent_id or self.config.get('ghl_agent_id')
            print(f"\nExtracting interview from agent {agent_id}...")
            
            qa_pairs = extractor.extract_for_hireology(agent_id=agent_id)
            
            if not qa_pairs:
                raise Exception("No Q&A pairs extracted from interview")
            
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
        """Step 3: Fetch interview ID dynamically and update Hireology interview"""
        print("\n" + "="*80)
        print("STEP 3: UPDATING HIREOLOGY INTERVIEW")
        print("="*80)
        
        try:
            jwt = self.config['hireology_jwt']
            job_id = self.config['hireology_job_id']
            
            if not json_path:
                json_path = self.results.get('interview_json_path')
            
            if not json_path or not os.path.exists(json_path):
                raise Exception(f"JSON file not found: {json_path}")
            
            print(f"\n🔍 Fetching interview ID for candidate {candidate_id}...")
            
            try:
                interview_id = fetch_interview_id(jwt, job_id, candidate_id)
                print(f"✅ Found interview ID: {interview_id}")
                
                self.results['interview_id'] = interview_id
                self.results['candidate_id'] = candidate_id
                
            except Exception as fetch_error:
                error_msg = f"Failed to fetch interview ID: {str(fetch_error)}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            print(f"\n📥 Loading interview data from Hireology...")
            print(f"   Job ID: {job_id}")
            print(f"   Candidate ID: {candidate_id}")
            print(f"   Interview ID: {interview_id}")
            
            import update_phoneInterview_on_Hireology as upd
            upd.JOB_ID = job_id
            upd.CANDIDATE_ID = candidate_id
            upd.INTERVIEW_ID = interview_id
            upd.BEARER_TOKEN = jwt
            
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
            
            print(f"✓ Successfully updated interview!")
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
                    print(f"   ℹ️  Score should now be visible in Hireology")
                else:
                    print(f"   ⚠️  Score calculation returned: {score_response.status_code}")
                    print(f"   Response: {score_response.text}")
                    
            except Exception as score_error:
                print(f"   ⚠️  Score calculation error: {str(score_error)}")
                print(f"   Note: Interview was updated successfully, but score calculation failed")
            
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
    
    def run_complete_workflow(self, candidate_id=None):
        """Run the complete hiring workflow"""
        print("\n" + "="*80)
        print("🚀 STARTING COMPLETE HIRING WORKFLOW")
        print("="*80)
        print(f"Timestamp: {self.results['timestamp']}")
        
        candidates_to_call = self.step1_screen_applicants()
        
        if not candidates_to_call:
            print("\nNo candidates to call after screening.")
            if candidate_id:
                print(f"   Attempting to process existing transcript for candidate {candidate_id}...")
                json_path = self.step2_process_phone_interview()
                if json_path:
                    self.step3_update_hireology_interview(candidate_id, json_path)
            return self.results
        
        print(f"\nProcessing {len(candidates_to_call)} candidate(s) for phone interview...")
        
        for idx, candidate in enumerate(candidates_to_call, 1):
            current_candidate_id = candidate.get('candidate_id')
            
            # Skip if already processed
            if current_candidate_id in processed_candidates:
                print(f"\n⏭️  Skipping candidate {current_candidate_id} - already processed")
                continue
            
            print(f"\n{'='*80}")
            print(f"PROCESSING CANDIDATE {idx}/{len(candidates_to_call)}")
            print(f"  ID: {current_candidate_id}")
            print(f"  Phone: {candidate.get('phone')}")
            print(f"{'='*80}")
            
            completed_call = self.step1b_make_call_and_wait(candidate)

            if not completed_call:
                print(f"\nCall did not complete for candidate {current_candidate_id}")
                print("   Skipping to next candidate...")
                continue
            
            print("Call status:", completed_call.get('callStatus'))
            if completed_call.get('callStatus') != 'completed':
                print(f"\nCandidate {current_candidate_id} did not pick up the call")
                print("   Skipping to next candidate...")
                continue
            
            json_path = self.step2_process_phone_interview()
            
            if not json_path:
                print(f"\nFailed to process interview for candidate {current_candidate_id}")
                continue
             
            should_skip_step3 = self.check_interview_postponement(json_path)
            
            if should_skip_step3:
                print(f"\n⏭️ Skipping Step 3 for candidate {current_candidate_id} due to interview postponement")
                self.results['candidates_called'].append({
                    'candidate_id': current_candidate_id,
                    'status': 'postponed',
                    'reason': 'Interview postponed - duration < 100s and postponing words detected'
                })
                continue
            
            success = self.step3_update_hireology_interview(
                candidate_id=current_candidate_id,
                json_path=json_path
            )
            
            if success:
                print(f"\n✅ Successfully processed candidate {current_candidate_id}")
                processed_candidates.add(current_candidate_id)
            else:
                print(f"\n⚠️ Failed to update Hireology for candidate {current_candidate_id}")
        
        print("\n" + "="*80)
        print("WORKFLOW SUMMARY")
        print("="*80)
        print(f"Steps completed: {', '.join(self.results['steps_completed'])}")
        print(f"Candidates called: {len(self.results['candidates_called'])}")
        
        for call_info in self.results['candidates_called']:
            status_icon = "✅" if call_info.get('status') == 'completed' else "⚠️"
            print(f"  {status_icon} {call_info.get('candidate_id')}: {call_info.get('status')}")
        
        if 'interview_score' in self.results:
            print(f"\nLatest Interview Results:")
            print(f"   Final Score: {self.results.get('interview_score', 'N/A')}")
            print(f"   Confidence Score: {self.results.get('confidence_score', 'N/A')}")
            print(f"   Questions Matched: {self.results.get('matched_questions', 0)}")
        
        print(f"\nErrors: {len(self.results['errors'])}")
        if self.results['errors']:
            for error in self.results['errors']:
                print(f"   {error}")
        print("="*80)
        
        return self.results


def monitoring_loop():
    """Continuous monitoring loop that runs forever"""
    global monitoring_active
    
    print("\n" + "="*80)
    print("🔄 AUTO-MONITORING STARTED")
    print("="*80)
    print(f"Job ID: {JOB_ID}")
    print(f"Check Interval: {CHECK_INTERVAL} seconds")
    print("Monitoring will continue until you stop the program (Ctrl+C)")
    print("="*80 + "\n")
    
    last_check_time = None
    
    while monitoring_active:
        try:
            current_time = datetime.now()
            
            # Display monitoring heartbeat
            if last_check_time:
                elapsed = (current_time - last_check_time).total_seconds()
                print(f"\n⏱️  [{current_time.strftime('%Y-%m-%d %H:%M:%S')}] Checking for new applicants... (Last check: {int(elapsed)}s ago)")
            else:
                print(f"\n⏱️  [{current_time.strftime('%Y-%m-%d %H:%M:%S')}] Initial check for new applicants...")
            
            last_check_time = current_time
            
            # Get fresh tokens
            jwt = get_valid_jwt()
            ghl_token_id = get_valid_ghl_token()
            
            # Fetch current applicants
            applicants = get_applicants_info(jwt, JOB_ID)
            
            if not applicants:
                print("   No applicants found in this check cycle.")
            else:
                print(f"   Found {len(applicants)} total applicants")
                
                # Find new applicants (not yet processed)
                new_applicants = [a for a in applicants if a['id'] not in processed_candidates]
                
                if new_applicants:
                    print(f"   🆕 {len(new_applicants)} NEW applicant(s) detected!")
                    
                    for applicant in new_applicants:
                        print(f"\n   Processing NEW applicant: ID={applicant['id']}, Phone={applicant['phone']}")
                        
                        # Create config for this applicant
                        config = {
                            'hireology_jwt': jwt,
                            'hireology_job_id': JOB_ID,
                            'ghl_api_key': GHL_API_KEY,
                            'ghl_location_id': GHL_LOCATION_ID,
                            'ghl_agent_id': GHL_AGENT_ID,
                            'ghl_token_id': ghl_token_id,
                            'ghl_from_phone': GHL_FROM_PHONE,
                            'groq_api_key': GROQ_API_KEY,
                            'call_timeout_minutes': 15,
                            'poll_interval_seconds': 10,
                            'candidate_phone': applicant['phone'],
                            'target_candidate_id': applicant['id']
                        }
                        
                        # Run workflow for this applicant
                        orchestrator = HiringWorkflowOrchestrator(config)
                        orchestrator.run_complete_workflow(candidate_id=applicant['id'])
                        
                        # Save results
                        with open(f'workflow_results_{applicant["id"]}.json', 'w') as f:
                            json.dump(orchestrator.results, f, indent=2)
                else:
                    print("   No new applicants to process.")
            
            # Wait before next check
            print(f"\n💤 Waiting {CHECK_INTERVAL} seconds before next check...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Monitoring interrupted by user (Ctrl+C)")
            monitoring_active = False
            break
        except Exception as e:
            print(f"\n❌ Error in monitoring loop: {str(e)}")
            print(f"   Will retry in {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)


# ============= Flask API (Optional - for manual control) =============

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'monitoring_active': monitoring_active,
        'timestamp': datetime.now().isoformat(),
        'processed_count': len(processed_candidates)
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current status"""
    return jsonify({
        'monitoring_active': monitoring_active,
        'processed_candidates': list(processed_candidates),
        'job_id': JOB_ID,
        'check_interval': CHECK_INTERVAL
    })

@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring (use with caution)"""
    global monitoring_active
    monitoring_active = False
    return jsonify({'message': 'Monitoring stopped'})


# ============= Main Entry Point =============

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 HIRING WORKFLOW - CONTINUOUS MONITORING MODE")
    print("="*80)
    print("\nThis program will:")
    print("  1. Start auto-monitoring for new applicants")
    print("  2. Run continuously in the background")
    print("  3. Process new applicants automatically")
    print("  4. Show all logs in real-time in this terminal")
    print("\nOptional Flask API available at: http://localhost:5000")
    print("  - GET  /health - Check system health")
    print("  - GET  /api/status - Get monitoring status")
    print("  - POST /api/stop - Stop monitoring")
    print("\nPress Ctrl+C to stop monitoring")
    print("="*80 + "\n")
    
    # Start Flask API in background thread (optional)
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False),
        daemon=True
    )
    flask_thread.start()
    print("✅ Flask API started on http://localhost:5000")
    
    # Start monitoring in main thread (so Ctrl+C works)
    time.sleep(2)  # Give Flask time to start
    monitoring_loop()
    
    print("\n" + "="*80)
    print("👋 MONITORING STOPPED")
    print("="*80)
    print(f"Total candidates processed: {len(processed_candidates)}")
    print("="*80 + "\n")