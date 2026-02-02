# fetch_unchedualed_interviewees.py
"""
Fetches candidates with status "Candidate" who have an unscheduled phone interview.
Uses a two-step API approach:
1. Get list of interviews to find interview IDs
2. Fetch specific interview details to get interview_status
"""
import requests


def get_candidates_with_status(jwt_token, job_id, status="Candidate", page_size=100):
    """
    Fetch candidates for a specific job from Hireology with a given status.
    """
    url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    params = {
        "filter[status]": status,
        "sort_dir": "desc",
        "sort_step_id": "",
        "sort": "date",
        "page_size": page_size
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def get_candidate_interviews_list(jwt_token, job_id, candidate_id):
    """
    Fetch the list of interviews for a specific candidate to get interview IDs.
    Returns a list of interview objects with basic info (id, name, progress).
    """
    url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates/{candidate_id}/interviews"
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"  [WARN] HTTP Error fetching interview list for {candidate_id}: {http_err}")
        return None
    except Exception as err:
        print(f"  [WARN] Error fetching interview list for {candidate_id}: {err}")
        return None


def get_interview_details(jwt_token, job_id, candidate_id, interview_id):
    """
    Fetch detailed interview information including interview_status.
    This is the second step - uses the interview_id from get_candidate_interviews_list.
    
    API: GET /v2/jobs/{job_id}/candidates/{candidate_id}/interviews/{interview_id}
    """
    url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates/{candidate_id}/interviews/{interview_id}"
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "*/*"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"  [WARN] HTTP Error fetching interview details for interview {interview_id}: {http_err}")
        return None
    except Exception as err:
        print(f"  [WARN] Error fetching interview details for interview {interview_id}: {err}")
        return None


def extract_candidate_ids(response_json):
    """
    Extract candidate IDs from Hireology candidates response.
    """
    return [candidate["id"] for candidate in response_json.get("data", [])]
def extract_candidate_phone_number(response_json):
    """
    Extract candidate IDs from Hireology candidates response.
    """
    return [candidate["home_phone"] or candidate["phone_number"] or candidate["cell_phone"] for candidate in response_json.get("data", [])]
def find_phone_interview_id(interviews_data):
    """
    Find the 'Phone Interview' from the list of interviews and return its ID.
    Returns (interview_id, interview_name) or (None, None) if not found.
    
    The API response can be:
    - A dict where keys are interview IDs and values are interview objects
    - A list of interview objects
    - A single interview object
    """
    if interviews_data is None:
        return None, None
    

    # If it's a dict, keys might be interview IDs with interview objects as values
    if isinstance(interviews_data, dict):
        # Check if keys look like IDs (numeric strings)
        keys = list(interviews_data.keys())
        
        # If keys are numeric strings, they are interview IDs
        # The values are the interview objects
        for key in keys:
            if key.isdigit():
                interview = interviews_data[key]
                if isinstance(interview, dict):
                    name = interview.get("name", "")
                    if "Phone Interview" in name:
                        # Use the key as the ID, or get 'id' from the object
                        interview_id = interview.get("id", key)
                        return interview_id, name
        
        # Fallback: if it's a single interview object with 'id' and 'name' at root
        if "id" in interviews_data and "name" in interviews_data:
            name = interviews_data.get("name", "")
            if "Phone Interview" in name:
                return interviews_data["id"], name
        
        # Check for 'data' wrapper
        if "data" in interviews_data:  
            return find_phone_interview_id(interviews_data["data"])
    
    # If it's a list of interviews
    if isinstance(interviews_data, list):
        for interview in interviews_data:
            if isinstance(interview, dict):
                name = interview.get("name", "")
                if "Phone Interview" in name:
                    return interview.get("id"), name
    
    return None, None


def get_unscheduled_interviewees(jwt_token, job_id):
    """
    Fetch all candidates with status 'Candidate' who have an unscheduled phone interview.
    Uses two-step API approach:
    1. Get interview list to find Phone Interview ID
    2. Get interview details to check interview_status
    """
    print("[INFO] Fetching candidates with status 'Candidate'...")
    
    # Step 1: Get all candidates with "Candidate" status
    candidates_response = get_candidates_with_status(jwt_token, job_id, status="Candidate")
    candidate_ids = extract_candidate_ids(candidates_response)
    candidate_phone_numbers = extract_candidate_phone_number(candidates_response)
    
    print(f"[OK] Found {len(candidate_ids)} candidates with 'Candidate' status")
    
    if not candidate_ids:
        print("[WARN] No candidates found with 'Candidate' status")
        return []
    
    unscheduled_candidates = []
    
    # Step 2: Check interview status for each candidate
    print("\n[INFO] Checking interview status for each candidate...")
    
    for candidate_id in candidate_ids:
        # Step 2a: Get interview list to find Phone Interview ID
        interviews_data = get_candidate_interviews_list(
            jwt_token=jwt_token,
            job_id=job_id,
            candidate_id=candidate_id
        )
        
        if not interviews_data:
            continue
        
        # Find the Phone Interview ID
        interview_id, interview_name = find_phone_interview_id(interviews_data)
        
        if not interview_id:
            # No Phone Interview found for this candidate
            continue
        
        # Step 2b: Get detailed interview info with interview_status
        interview_details = get_interview_details(
            jwt_token=jwt_token,
            job_id=job_id,
            candidate_id=candidate_id,
            interview_id=interview_id
        )
        
        if not interview_details:
            continue
        
        # Check interview_status
        interview_status_obj = interview_details.get("interview_status", {})
        status = interview_status_obj.get("status", "")
        
        # Also check progress field as fallback
        if not status:
            status = interview_details.get("progress", "")
        
        status = str(status).lower() if status else "unknown"
        
        if status == "unscheduled":
            print(f"  [OK] Candidate {candidate_id}: Phone Interview is UNSCHEDULED")
            
            # Find candidate details from original response
            candidate_info = next(
                (c for c in candidates_response.get("data", []) if c["id"] == candidate_id),
                None
            )
            unscheduled_candidates.append({
                "candidate_id": candidate_id,
                # "interview_id": interview_id,
                # "interview_name": interview_name,
                # "interview_details": interview_details,
                # "candidate_info": candidate_info
                "phone":candidate_phone_numbers
            })
    
    return unscheduled_candidates


# Example usage
if __name__ == "__main__":
    # Your JWT token and job ID
    JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlFZdWgwSmFGcGpmanZJTWJMNGctYXhpdmttazgyaHQ5RlMwazd4Sk5JR2MiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY5Njk4NzE3LCJuYmYiOjE3Njk2OTUxMTcsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm1mYSI6dHJ1ZSwiYXpmcCI6dHJ1ZSwidGlkIjoiNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyIiwia21zaSI6IkZhbHNlIiwic2NwIjoidjIgYWkgdjMiLCJhenAiOiJmMDY3ZTZhMy04MTVkLTQxM2QtODc4ZS1kMjIzZWZhYTBjYTQiLCJ2ZXIiOiIxLjAiLCJpYXQiOjE3Njk2OTUxMTd9.TkiHAYOdEyNIa5HMBqBNM9KwhKvjr25_V8pK3vZ49hvA8DmfBPkAzg2tX-2kdshNfaQnbGui0k7jgWFaIb39VE3WjPE362QZtwI8Ktq4iAapoPF0RPFjfGTIuthqiWu4klav6_V7al-wW5Ayt2L-o9mziZyxex8sZcXdDL8-ridm3FV8F0163Yh6WO0cjK2E052zeCDmV6o3aEFgIs3RRd6si0SzSiZk-ks1sU_X9WVCgV2q5YRRh1CEG-hNKsU9tpDLlGpT0j28pZysGDqLBl9yKq3TK9d-ZKGSHay7IUCpvqV-fhu-1SGc257eRBgpZY918WSVcIF50gLxhwMnXQ"
    
    JOB_ID = "2606114"
    
    # Test with a single candidate first
    print("=== Testing single candidate ===")
    test_candidate_id = "47775915"
    
    # Step 1: Get interview list
    print(f"Getting interview list for candidate {test_candidate_id}...")
    interviews = get_candidate_interviews_list(JWT_TOKEN, JOB_ID, test_candidate_id)
    print(f"Interview list response type: {type(interviews)}")
    
    # Find Phone Interview ID
    interview_id, interview_name = find_phone_interview_id(interviews)
    print(f"Found Phone Interview: ID={interview_id}, Name={interview_name}")
    
    if interview_id:
        # Step 2: Get interview details
        print(f"\nGetting interview details for interview {interview_id}...")
        details = get_interview_details(JWT_TOKEN, JOB_ID, test_candidate_id, interview_id)
        
        if details:
            interview_status = details.get("interview_status", {})
            status = interview_status.get("status", "N/A")
            progress = details.get("progress", "N/A")
            print(f"Interview Status: {status}")
            print(f"Progress: {progress}")
        else:
            print("Failed to get interview details")
    else:
        print("No Phone Interview found")
    
    # Now run the full process
    print("\n\n=== Running full unscheduled interviewees search ===")
    unscheduled = get_unscheduled_interviewees(
        jwt_token=JWT_TOKEN,
        job_id=JOB_ID
    )
    
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(unscheduled)} candidates with unscheduled phone interviews")
    print(f"{'='*60}")
    
    for idx, candidate in enumerate(unscheduled, 1):
        candidate_info = candidate.get("candidate_info", {})
        candidate_id = candidate.get("candidate_id")
        interview_id = candidate.get("interview_id")
        
        # Get candidate name if available
        first_name = candidate_info.get("first_name", "N/A") if candidate_info else "N/A"
        last_name = candidate_info.get("last_name", "N/A") if candidate_info else "N/A"
        
        print(f"\n{idx}. Candidate ID: {candidate_id}")
        print(f"   Name: {first_name} {last_name}")
        print(f"   Interview ID: {interview_id}")
        print(f"   Interview Status: unscheduled")
    
    print("\n[DONE] Complete!")
 