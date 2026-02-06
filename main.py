"""
Flask API for Hiring Workflow
Essential endpoints for: Screening, Calling, Interview Processing, and Hireology Updates
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

# Import from existing files
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

load_dotenv()

# ============= FLASK APP SETUP =============
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============= CONFIGURATION =============
JOB_ID = os.getenv('HIREOLOGY_JOB_ID', '2606114')
GHL_API_KEY = os.getenv('GHL_API_KEY', 'pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324')
GHL_LOCATION_ID = os.getenv('GHL_LOCATION_ID', 'M5jnxd1r8yq3o5gxSYOP')
GHL_AGENT_ID = os.getenv('GHL_AGENT_ID', '693448f6231659c2a32a3bca')
GHL_FROM_PHONE = os.getenv('GHL_FROM_PHONE', '+18439407924')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Track state
processed_applicants = set()
auto_monitor_running = False


# ============= HELPER CLASSES =============

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
            logger.error(f"Error checking call status: {e}")
            return None

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison"""
        if not phone:
            return ""
        return ''.join(filter(str.isdigit, str(phone)))


def wait_for_call_completion(call_checker, call_id, timeout=300, interval=5):
    """Wait until callStatus becomes completed"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        data = call_checker.get_call_status(call_id)
        if not data:
            time.sleep(interval)
            continue

        call_status = data.get("callStatus")
        logger.info(f"Current callStatus: {call_status}")

        if call_status == "completed":
            return data
        if call_status in ["failed", "busy", "no-answer", "cancelled"]:
            return data
        time.sleep(interval)

    raise TimeoutError("Call did not finish within timeout")


# ============= CORE WORKFLOW FUNCTIONS =============

def get_config():
    """Get configuration with fresh tokens"""
    jwt = get_valid_jwt()
    ghl_token_id = get_valid_ghl_token()
    
    return {
        'hireology_jwt': jwt,
        'hireology_job_id': JOB_ID,
        'ghl_api_key': GHL_API_KEY,
        'ghl_location_id': GHL_LOCATION_ID,
        'ghl_agent_id': GHL_AGENT_ID,
        'ghl_token_id': ghl_token_id,
        'ghl_from_phone': GHL_FROM_PHONE,
        'groq_api_key': GROQ_API_KEY,
        'call_timeout_minutes': 15,
        'poll_interval_seconds': 10
    }


def screen_applicants(jwt, job_id, target_candidate_id=None, candidate_phone=None):
    """Screen applicants and return candidates to call"""
    screened_applicants = []
    candidates_to_call = []

    # Fetch new applicants
    candidates = get_candidates(jwt_token=jwt, job_id=job_id)
    applicant_ids = extract_applicant_ids(candidates)
    logger.info(f"Found {len(applicant_ids)} new applicants to screen")

    for candidate_id in applicant_ids:
        documents = get_candidate_documents(
            jwt_token=jwt,
            job_id=job_id,
            candidate_id=candidate_id,
            transfer=False
        )
        
        if not documents:
            continue

        applicant_record = build_single_applicant_record(documents)
        candidate_job_id = documents[0].get("id")
        phone = documents[0].get("home_phone") or documents[0].get("cell_phone")
        
        # Use provided phone if target candidate
        if str(candidate_id) == str(target_candidate_id) and candidate_phone:
            phone = candidate_phone

        # Check for incomplete questions
        incomplete_questions = get_incomplete_questions(applicant_record)
        if incomplete_questions:
            send_incomplete_application_email(
                jwt_token=jwt,
                candidate_job_id=candidate_job_id,
                candidate_email=applicant_record["email"],
                job_id=job_id,
                job_name=applicant_record["job_name"],
                incomplete_questions=incomplete_questions
            )
            screened_applicants.append({
                'candidate_id': candidate_id,
                'status': 'incomplete'
            })
            continue

        # Decide status
        final_status = decide_candidate_status(applicant_record)
        
        if final_status == "Inactive":
            rejection_reason = get_rejection_reason(applicant_record)
            send_rejection_email(
                jwt_token=jwt,
                candidate_job_id=candidate_job_id,
                candidate_email=applicant_record["email"],
                job_name=applicant_record["job_name"],
                rejection_reason=rejection_reason
            )

        # Update status in Hireology
        update_candidate_status(
            jwt_token=jwt,
            job_id=job_id,
            candidate_id=candidate_id,
            status=final_status
        )

        applicant_data = {
            'candidate_id': candidate_id,
            'candidate_job_id': candidate_job_id,
            'email': applicant_record.get("email"),
            'status': final_status
        }

        if final_status == "Candidate":
            applicant_data['phone'] = phone
            candidates_to_call.append(applicant_data)

        screened_applicants.append(applicant_data)

    return {
        'screened_applicants': screened_applicants,
        'candidates_to_call': candidates_to_call
    }


def make_call_and_wait(config, phone):
    """Make a call and wait for completion"""
    call_checker = CallStatusChecker(
        api_key=config['ghl_api_key'],
        location_id=config['ghl_location_id'],
        agent_id=config['ghl_agent_id']
    )

    # Make the call
    call_result = make_trial_call(
        to_phone_number=phone,
        from_phone_number=config['ghl_from_phone'],
        agent_id=config['ghl_agent_id'],
        location_id=config['ghl_location_id'],
        token_id=config['ghl_token_id'],
        test_scenario="OUTBOUND"
    )

    if 'error' in call_result:
        return {'error': call_result.get('error')}

    # Extract call ID
    call_id = call_result.get("_id") or call_result.get("id") or call_result.get("callId")
    if not call_id:
        return {'error': 'Could not extract call ID'}

    # Wait for completion
    timeout = config.get('call_timeout_minutes', 15) * 60
    interval = config.get('poll_interval_seconds', 10)
    
    try:
        completed_call = wait_for_call_completion(call_checker, call_id, timeout, interval)
        return {
            'call_id': call_id,
            'status': completed_call.get('callStatus'),
            'duration': completed_call.get('duration'),
            'data': completed_call
        }
    except TimeoutError:
        return {'error': 'Call timeout', 'call_id': call_id}


def process_phone_interview(config):
    """Process most recent phone interview transcript"""
    extractor = HireologyQAExtractor(
        api_key=config['ghl_api_key'],
        location_id=config['ghl_location_id'],
        groq_api_key=config.get('groq_api_key')
    )

    agent_id = config.get('ghl_agent_id')
    qa_pairs = extractor.extract_for_hireology(agent_id=agent_id)

    if not qa_pairs:
        return {'error': 'No Q&A pairs extracted'}

    # Find the saved JSON file
    call_data_dir = 'call_data'
    json_files = [f for f in os.listdir(call_data_dir) if f.startswith('hireology_qa_') and f.endswith('.json')]
    
    if not json_files:
        return {'error': 'No JSON file created'}

    latest_json = max([os.path.join(call_data_dir, f) for f in json_files], key=os.path.getctime)

    return {
        'json_path': latest_json,
        'qa_pairs_count': len(qa_pairs)
    }


def check_interview_postponement(json_path):
    """Check if interview should be skipped due to postponement"""
    POSTPONING_PHRASES = [
        "busy now", "busy right now", "can we talk later", "talk later",
        "can you postpone", "postpone the interview", "reschedule",
        "call me back", "call back later", "not a good time", "bad time",
        "can't talk now", "cannot talk now", "in a meeting", "at work",
        "driving", "i'm driving", "call me later", "later please",
        "some other time", "another time", "not right now", "not available"
    ]

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        call_info = data.get('call_info', {})
        duration = call_info.get('duration', 0)
        qa_pairs = data.get('qa_pairs', [])[:7]

        postponing_found = False
        for qa in qa_pairs:
            answer = qa.get('answer', '').lower()
            for phrase in POSTPONING_PHRASES:
                if phrase.lower() in answer:
                    postponing_found = True
                    break
            if postponing_found:
                break

        return duration < 100 and postponing_found

    except Exception as e:
        logger.error(f"Error checking postponement: {e}")
        return False


def update_hireology_interview(config, candidate_id, json_path):
    """Update Hireology interview with phone interview results"""
    jwt = config['hireology_jwt']
    job_id = config['hireology_job_id']

    # Fetch interview ID
    interview_id = fetch_interview_id(jwt, job_id, candidate_id)
    
    # Set globals for the update module
    import update_phoneInterview_on_Hireology as upd
    upd.JOB_ID = job_id
    upd.CANDIDATE_ID = candidate_id
    upd.INTERVIEW_ID = interview_id
    upd.BEARER_TOKEN = jwt

    # Fetch and update interview
    interview_data = fetch_interview_from_api()
    updated_interview, update_logs, all_logs = update_interview_answers(json_path, interview_data)
    
    if all_logs:
        display_update_logs(all_logs, len(update_logs))

    # Send to Hireology
    response = send_update_to_hireology(updated_interview)
    
    if response.status_code not in [200, 204]:
        return {'error': f'API returned {response.status_code}'}

    # Trigger score calculation
    score_response = trigger_score_calculation()
    score_data = score_response.json() if score_response.status_code == 200 else {}

    return {
        'success': True,
        'interview_id': interview_id,
        'matched_questions': len(update_logs),
        'score': score_data.get('score'),
        'confidence_score': score_data.get('confidence_score')
    }


def run_complete_workflow(candidate_id=None, candidate_phone=None):
    """Run the complete hiring workflow"""
    config = get_config()
    results = {
        'timestamp': datetime.now().isoformat(),
        'steps_completed': [],
        'errors': []
    }

    # Step 1: Screen applicants
    screening_result = screen_applicants(
        jwt=config['hireology_jwt'],
        job_id=config['hireology_job_id'],
        target_candidate_id=candidate_id,
        candidate_phone=candidate_phone
    )
    results['screening'] = screening_result
    results['steps_completed'].append('screening')

    candidates_to_call = screening_result.get('candidates_to_call', [])
    if not candidates_to_call:
        results['message'] = 'No candidates to call'
        return results

    # Process each candidate
    for candidate in candidates_to_call:
        current_id = candidate.get('candidate_id')
        phone = candidate.get('phone')

        # Step 1B: Make call
        call_result = make_call_and_wait(config, phone)
        if 'error' in call_result:
            results['errors'].append(f"Call failed for {current_id}: {call_result['error']}")
            continue

        if call_result.get('status') != 'completed':
            results['errors'].append(f"Call not answered for {current_id}")
            continue

        results['steps_completed'].append(f'call_{current_id}')

        # Step 2: Process interview
        interview_result = process_phone_interview(config)
        if 'error' in interview_result:
            results['errors'].append(f"Processing failed for {current_id}")
            continue

        json_path = interview_result.get('json_path')
        results['steps_completed'].append(f'process_{current_id}')

        # Check for postponement
        if check_interview_postponement(json_path):
            results['errors'].append(f"Interview postponed for {current_id}")
            continue

        # Step 3: Update Hireology
        update_result = update_hireology_interview(config, current_id, json_path)
        if 'error' in update_result:
            results['errors'].append(f"Hireology update failed for {current_id}")
            continue

        results['steps_completed'].append(f'update_{current_id}')
        results['interview_result'] = update_result

    return results


# ============= API ENDPOINTS =============

@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'job_id': JOB_ID,
        'auto_monitor': auto_monitor_running,
        'processed_count': len(processed_applicants),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/applicants', methods=['GET'])
def get_applicants():
    """Get all applicants for the job"""
    try:
        jwt = get_valid_jwt()
        applicants = get_applicants_info(jwt, JOB_ID)
        return jsonify({
            'success': True,
            'applicants': applicants,
            'count': len(applicants) if applicants else 0
        })
    except Exception as e:
        logger.error(f"Error fetching applicants: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/screen', methods=['POST'])
def screen_candidates():
    """Screen applicants and identify candidates for calling"""
    try:
        config = get_config()
        data = request.get_json() or {}
        
        result = screen_applicants(
            jwt=config['hireology_jwt'],
            job_id=config['hireology_job_id'],
            target_candidate_id=data.get('candidate_id'),
            candidate_phone=data.get('candidate_phone')
        )
        
        return jsonify({
            'success': True,
            'screened': len(result.get('screened_applicants', [])),
            'to_call': len(result.get('candidates_to_call', [])),
            'data': result
        })
    except Exception as e:
        logger.error(f"Error screening: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/call', methods=['POST'])
def make_call():
    """Make a call to a specific phone number"""
    try:
        data = request.get_json() or {}
        phone = data.get('phone')
        
        if not phone:
            return jsonify({'success': False, 'error': 'phone required'}), 400

        config = get_config()
        result = make_call_and_wait(config, phone)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 500

        return jsonify({
            'success': True,
            'call_id': result.get('call_id'),
            'status': result.get('status'),
            'duration': result.get('duration')
        })
    except Exception as e:
        logger.error(f"Error making call: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/process-interview', methods=['POST'])
def process_interview():
    """Process the most recent phone interview transcript"""
    try:
        config = get_config()
        result = process_phone_interview(config)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 500

        return jsonify({
            'success': True,
            'json_path': result.get('json_path'),
            'qa_pairs_count': result.get('qa_pairs_count')
        })
    except Exception as e:
        logger.error(f"Error processing interview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/update-hireology', methods=['POST'])
def update_hireology():
    """Update Hireology interview with processed answers"""
    try:
        data = request.get_json() or {}
        candidate_id = data.get('candidate_id')
        json_path = data.get('json_path')
        
        if not candidate_id:
            return jsonify({'success': False, 'error': 'candidate_id required'}), 400

        config = get_config()
        
        # If no json_path provided, get the latest
        if not json_path:
            call_data_dir = 'call_data'
            json_files = [f for f in os.listdir(call_data_dir) if f.startswith('hireology_qa_') and f.endswith('.json')]
            if json_files:
                json_path = max([os.path.join(call_data_dir, f) for f in json_files], key=os.path.getctime)
            else:
                return jsonify({'success': False, 'error': 'No interview data found'}), 400

        result = update_hireology_interview(config, candidate_id, json_path)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 500

        return jsonify({
            'success': True,
            'interview_id': result.get('interview_id'),
            'matched_questions': result.get('matched_questions'),
            'score': result.get('score'),
            'confidence_score': result.get('confidence_score')
        })
    except Exception as e:
        logger.error(f"Error updating Hireology: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/workflow', methods=['POST'])
def run_workflow():
    """Run the complete workflow for a specific candidate"""
    try:
        data = request.get_json() or {}
        candidate_id = data.get('candidate_id')
        candidate_phone = data.get('candidate_phone')

        results = run_complete_workflow(
            candidate_id=candidate_id,
            candidate_phone=candidate_phone
        )

        if candidate_id:
            processed_applicants.add(candidate_id)

        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        logger.error(f"Error running workflow: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/monitor/status', methods=['GET'])
def monitor_status():
    """Get auto-monitor status"""
    return jsonify({
        'running': auto_monitor_running,
        'processed_count': len(processed_applicants),
        'processed_applicants': list(processed_applicants),
        'job_id': JOB_ID
    })


@app.route('/monitor/start', methods=['POST'])
def start_monitor():
    """Start the auto-monitor"""
    global auto_monitor_running
    
    if auto_monitor_running:
        return jsonify({'success': False, 'message': 'Monitor already running'})

    interval = request.get_json().get('interval', 60) if request.get_json() else 60
    
    def monitor_worker():
        global auto_monitor_running
        auto_monitor_running = True
        
        while auto_monitor_running:
            try:
                jwt = get_valid_jwt()
                applicants = get_applicants_info(jwt, JOB_ID)
                
                if applicants:
                    for applicant in applicants:
                        if applicant['id'] not in processed_applicants:
                            processed_applicants.add(applicant['id'])
                            run_complete_workflow(
                                candidate_id=applicant['id'],
                                candidate_phone=applicant['phone']
                            )
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(interval)

    thread = threading.Thread(target=monitor_worker, daemon=True)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Monitor started'})


@app.route('/monitor/stop', methods=['POST'])
def stop_monitor():
    """Stop the auto-monitor"""
    global auto_monitor_running
    auto_monitor_running = False
    return jsonify({'success': True, 'message': 'Monitor stopped'})


# ============= MAIN =============
if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("🚀 STARTING HIRING WORKFLOW FLASK API")
    logger.info("=" * 80)
    logger.info(f"Job ID: {JOB_ID}")
    logger.info("Endpoints:")
    logger.info("  GET  /              - Health check")
    logger.info("  GET  /applicants    - List applicants")
    logger.info("  POST /screen        - Screen applicants")
    logger.info("  POST /call          - Make a call")
    logger.info("  POST /process-interview - Process transcript")
    logger.info("  POST /update-hireology  - Update interview")
    logger.info("  POST /workflow      - Run complete workflow")
    logger.info("  GET  /monitor/status - Monitor status")
    logger.info("  POST /monitor/start  - Start auto-monitor")
    logger.info("  POST /monitor/stop   - Stop auto-monitor")
    logger.info("=" * 80)

    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        threaded=True
    )