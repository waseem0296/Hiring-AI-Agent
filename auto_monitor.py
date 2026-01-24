"""
Auto Monitor - Automatically detects and processes new applicants
Simple single-file solution for automatic applicant monitoring
"""

import os
import json
import time
from datetime import datetime


def start_auto_monitor(
    orchestrator_class,
    get_applicants_func,
    get_hireology_token_func,
    get_ghl_token_func,
    job_id="2606114",
    check_interval=60
):
    """
    Start automatic monitoring for new applicants
    
    Args:
        orchestrator_class: HiringWorkflowOrchestrator class
        get_applicants_func: Function to get applicants (takes jwt, job_id)
        get_hireology_token_func: Function to get Hireology token
        get_ghl_token_func: Function to get GHL token
        job_id: Job ID to monitor
        check_interval: Seconds between checks
    """
    
    # Load/save processed applicants
    state_file = "processed_applicants.json"
    
    def load_processed():
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    return set(json.load(f).get('processed_ids', []))
            except:
                return set()
        return set()
    
    def save_processed(processed_set):
        with open(state_file, 'w') as f:
            json.dump({
                'processed_ids': list(processed_set),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
    
    processed_applicants = load_processed()
    
    print(f"\n{'='*80}")
    print(f"🚀 AUTO MONITOR STARTED")
    print(f"{'='*80}")
    print(f"Job ID: {job_id}")
    print(f"Check Interval: {check_interval}s")
    print(f"Already Processed: {len(processed_applicants)} applicants")
    print(f"{'='*80}\n")
    print(f"⏳ Monitoring... (Press Ctrl+C to stop)\n")
    
    # GHL Config
    ghl_config = {
        'ghl_api_key': os.getenv("GHL_API_KEY", "pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324"),
        'ghl_location_id': os.getenv("GHL_LOCATION_ID", "M5jnxd1r8yq3o5gxSYOP"),
        'ghl_agent_id': os.getenv("GHL_AGENT_ID", "693448f6231659c2a32a3bca"),
        'ghl_from_phone': os.getenv("GHL_FROM_PHONE", "+18439407924"),
        'groq_api_key': os.getenv("GROQ_API_KEY"),
        'call_timeout_minutes': 15,
        'poll_interval_seconds': 10
    }
    
    try:
        while True:
            try:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking for new applicants...")
                
                # Get tokens and applicants
                jwt = get_hireology_token_func()
                ghl_token = get_ghl_token_func()
                all_applicants = get_applicants_func(jwt, job_id)
                
                # Find new applicants
                new_applicants = [
                    app for app in (all_applicants or [])
                    if app['id'] not in processed_applicants
                ]
                
                if new_applicants:
                    print(f"✨ Found {len(new_applicants)} new applicant(s)!\n")
                    
                    for applicant in new_applicants:
                        candidate_id = applicant['id']
                        candidate_phone = applicant['phone']
                        
                        print(f"{'='*80}")
                        print(f"🆕 NEW APPLICANT: {candidate_id}")
                        print(f"   Phone: {candidate_phone}")
                        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"{'='*80}\n")
                        
                        try:
                            # Build config
                            config = {
                                'hireology_jwt': jwt,
                                'hireology_job_id': job_id,
                                'ghl_token_id': ghl_token,
                                'candidate_phone': candidate_phone,
                                'target_candidate_id': candidate_id,
                                **ghl_config
                            }
                            
                            # Run workflow
                            orchestrator = orchestrator_class(config)
                            results = orchestrator.run_complete_workflow(candidate_id=candidate_id)
                            
                            # Save results
                            result_file = f"workflow_results_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            with open(result_file, 'w') as f:
                                json.dump(results, f, indent=2)
                            
                            print(f"\n✅ Completed! Results: {result_file}\n")
                            
                        except Exception as e:
                            print(f"\n❌ Error processing {candidate_id}: {e}\n")
                        
                        # Mark as processed
                        processed_applicants.add(candidate_id)
                        save_processed(processed_applicants)
                        
                        # Delay between applicants
                        if len(new_applicants) > 1:
                            print(f"⏸️  Waiting 30s before next applicant...\n")
                            time.sleep(30)
                else:
                    print(f"   No new applicants.")
                
                print(f"   Next check in {check_interval}s...\n")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"❌ Error: {e}")
                print(f"   Retrying in {check_interval}s...\n")
                time.sleep(check_interval)
    
    except KeyboardInterrupt:
        print(f"\n\n{'='*80}")
        print(f"🛑 MONITOR STOPPED")
        print(f"   Total Processed: {len(processed_applicants)}")
        print(f"{'='*80}\n")
