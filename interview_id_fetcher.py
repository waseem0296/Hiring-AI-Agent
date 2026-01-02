"""
Interview ID Fetcher for Hireology API

This module fetches an interview ID by:
1. Getting candidate_job_id from /jobs/{job_id}/candidates/{candidate_id}
2. Getting hiring_step_id from /jobs/{job_id}/interview_progress
3. Creating an interview using /v2/interviews endpoint
4. Returning the interview ID from the response
"""

import requests
from typing import Optional


API_BASE_URL = "https://api.hireology.com/v2"

# Default headers for all requests
DEFAULT_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://app.hireology.com",
    "referer": "https://app.hireology.com/",
    "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
}


def get_candidate_job_id(jwt: str, job_id: str, candidate_id: str) -> int:
    """
    Fetch candidate_job_id from /jobs/{job_id}/candidates/{candidate_id} endpoint.
    
    Args:
        jwt: Bearer token for authentication
        job_id: The job ID
        candidate_id: The candidate ID
        
    Returns:
        The candidate_job_id as an integer
    """
    url = f"{API_BASE_URL}/jobs/{job_id}/candidates/{candidate_id}"
    
    headers = {
        **DEFAULT_HEADERS,
        "authorization": f"Bearer {jwt}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch candidate info: {response.status_code} - {response.text}"
        )
    
    data = response.json()
    print(f"📋 Candidate Info Response: {data}")
    
    if not data:
        raise Exception("Empty response from candidates endpoint")
    
    # Extract candidate_job_id from the response
    candidate_job_id = None
    
    if isinstance(data, dict):
        # Try common field names
        candidate_job_id = data.get("candidate_job_id") or data.get("id")
        
        # Check if nested under 'candidate' key
        if not candidate_job_id and "candidate" in data:
            candidate_job_id = data["candidate"].get("candidate_job_id") or data["candidate"].get("id")
    
    if not candidate_job_id:
        raise Exception(f"Could not extract candidate_job_id from response: {data}")
    
    return int(candidate_job_id)


def get_hiring_step_id(jwt: str, job_id: str, candidate_id: str, candidate_job_id: int, interview_template_id: int) -> int:
    """
    Fetch hiring_step_id from /jobs/{job_id}/interview_progress endpoint.
    
    Args:
        jwt: Bearer token for authentication
        job_id: The job ID
        candidate_id: The candidate ID
        candidate_job_id: The candidate job ID (used as key in response)
        interview_template_id: The interview template ID to match
        
    Returns:
        The hiring_step_id as an integer
    """
    url = f"{API_BASE_URL}/jobs/{job_id}/interview_progress"
    params = {
        "candidate_ids[]": candidate_id
    }
    
    headers = {
        **DEFAULT_HEADERS,
        "authorization": f"Bearer {jwt}"
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch interview progress: {response.status_code} - {response.text}"
        )
    
    data = response.json()
    print(f"📋 Interview Progress Response: {data}")
    
    if not data:
        raise Exception("Empty response from interview_progress endpoint")
    
    # The response is keyed by candidate_job_id (as string)
    # Example: {'58007030': [{'id': None, 'name': 'Care Professional Interview', 
    #           'template_id': 477916, 'hiring_step_id': 9925429, ...}, ...]}
    
    hiring_step_id = None
    
    # Convert candidate_job_id to string for dict lookup
    candidate_job_id_str = str(candidate_job_id)
    
    if isinstance(data, dict) and candidate_job_id_str in data:
        interviews_list = data[candidate_job_id_str]
        
        if isinstance(interviews_list, list):
            # Find the interview that matches our template_id
            for interview in interviews_list:
                if interview.get("template_id") == interview_template_id:
                    hiring_step_id = interview.get("hiring_step_id")
                    print(f"🎯 Found matching interview template: {interview.get('name')} (template_id={interview_template_id})")
                    break
            
            # If no matching template found, use the first one with a hiring_step_id
            if not hiring_step_id and interviews_list:
                for interview in interviews_list:
                    if interview.get("hiring_step_id"):
                        hiring_step_id = interview.get("hiring_step_id")
                        print(f"⚠️ Using first available hiring_step_id from: {interview.get('name')}")
                        break
    
    if not hiring_step_id:
        raise Exception(f"Could not extract hiring_step_id from response: {data}")
    
    return int(hiring_step_id)


def create_interview(jwt: str, candidate_job_id: int, interview_template_id: int, hiring_step_id: int) -> str:
    """
    Create an interview and return the interview ID.
    
    Args:
        jwt: Bearer token for authentication
        candidate_job_id: The candidate job ID
        interview_template_id: The interview template ID
        hiring_step_id: The hiring step ID
        
    Returns:
        The interview ID as a string
    """
    url = f"{API_BASE_URL}/interviews"
    
    headers = {
        **DEFAULT_HEADERS,
        "authorization": f"Bearer {jwt}"
    }
    
    payload = {
        "candidate_job_id": candidate_job_id,
        "interview_template_id": interview_template_id,
        "hiring_step_id": hiring_step_id
    }
    
    print(f"📤 Creating interview with payload: {payload}")
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code not in [200, 201]:
        raise Exception(
            f"Failed to create interview: {response.status_code} - {response.text}"
        )
    
    data = response.json()
    print(f"📝 Create Interview Response: {data}")
    
    # Extract interview_id from response
    interview_id = None
    
    if isinstance(data, dict):
        # Check common field names for interview ID
        interview_id = data.get("id") or data.get("interview_id")
        
        # If the response is a dictionary with the interview_id as a key
        if not interview_id and len(data) == 1:
            interview_id = next(iter(data.keys()))
        
        # Check if nested under 'interview' or 'data' key
        if not interview_id:
            if "interview" in data:
                interview_id = data["interview"].get("id") or data["interview"].get("interview_id")
            elif "data" in data:
                interview_id = data["data"].get("id") or data["data"].get("interview_id")
    
    if not interview_id:
        raise Exception(f"Could not extract interview_id from response: {data}")
    
    return str(interview_id)


def fetch_interview_id(jwt: str, job_id: str, candidate_id: str, interview_template_id: int = 512090) -> str:
    """
    Main function to fetch interview ID for a candidate.
    
    This function:
    1. Gets candidate_job_id from /jobs/{job_id}/candidates/{candidate_id}
    2. Gets hiring_step_id from /jobs/{job_id}/interview_progress
    3. Creates an interview using the interviews endpoint
    4. Returns the interview ID
    
    Args:
        jwt: Bearer token for authentication
        job_id: The job ID
        candidate_id: The candidate ID
        interview_template_id: The interview template ID (default: 512090)
        
    Returns:
        The interview ID as a string
    """
    print(f"🔍 Fetching data for job_id={job_id}, candidate_id={candidate_id}")
    
    # Step 1: Get candidate_job_id from candidates endpoint
    print(f"\n📥 Step 1: Getting candidate_job_id...")
    candidate_job_id = get_candidate_job_id(jwt, job_id, candidate_id)
    print(f"✅ Got candidate_job_id={candidate_job_id}")
    
    # Step 2: Get hiring_step_id from interview_progress endpoint
    print(f"\n📥 Step 2: Getting hiring_step_id for template_id={interview_template_id}...")
    hiring_step_id = get_hiring_step_id(jwt, job_id, candidate_id, candidate_job_id, interview_template_id)
    print(f"✅ Got hiring_step_id={hiring_step_id}")
    
    # Step 3: Create interview and get interview_id
    print(f"\n📞 Step 3: Creating interview with template_id={interview_template_id}")
    interview_id = create_interview(
        jwt=jwt,
        candidate_job_id=candidate_job_id,
        interview_template_id=interview_template_id,
        hiring_step_id=hiring_step_id
    )
    
    print(f"\n✅ Interview created with ID: {interview_id}")
    
    return interview_id


# For testing
if __name__ == "__main__":
    # Test configuration
    BEARER_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY3Mzc2MTA1LCJuYmYiOjE3NjczNzI1MDUsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY3MzcyNTA1fQ.AVJK8iHjlpmWbnzlq6JiULGvV_bzkW5OV12VV5CGhUr9WIQ0Irp_bmZyQUWsNtDyDkGBbogCF9fiZd2IhChL5ovDVnj6flNIg_HLDj0nN8y8cFNE4ess5Zo9IsBLT_kOvWFLk7aTgxpyXjqlrZHb3rthnXp2-gelvG90LhRfeUkjjhmtsFoukyfTPc50oJqL5QujQw9Vd8vYwVv2_ZVA8KpBO0FyhW2BHuylnyJCw8N9ajCXCcGGnD5QKZUtHNzP_6I4vu4KHVGYvl8pKcdZ9vGCiUkA-btTdKttazirLr_tOLJfJHhqqSiprv02bnrlEkBnfPU6U9FwGHeVKKyymA"
    JOB_ID = "2606114"
    CANDIDATE_ID = "47113924"
    INTERVIEW_TEMPLATE_ID = 512090
    
    print("=" * 70)
    print("Hireology Interview ID Fetcher")
    print("=" * 70)
    
    try:
        interview_id = fetch_interview_id(
            jwt=BEARER_TOKEN,
            job_id=JOB_ID,
            candidate_id=CANDIDATE_ID,
            interview_template_id=INTERVIEW_TEMPLATE_ID
        )
        print(f"\n🎉 Successfully fetched Interview ID: {interview_id}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
