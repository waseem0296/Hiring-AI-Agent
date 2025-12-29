"""
Applicant ID Fetcher
Fetches applicant IDs and phone numbers from Hireology
"""

from fetch_applicants import get_candidates


def get_applicants_info(jwt_token: str, job_id: str) -> list[dict]:
    """
    Fetch all applicants and return their ID and phone number.
    
    Args:
        jwt_token: Hireology JWT token
        job_id: Job ID to fetch candidates for
    
    Returns:
        List of dicts with 'id' and 'phone' keys
    """
    # Get candidates from Hireology
    response = get_candidates(jwt_token=jwt_token, job_id=job_id)
    
    applicants = []
    
    # Extract candidates list from response
    candidates = response.get("candidates", [])
    
    for candidate in candidates:
        applicant_info = {
            "id": candidate.get("id"),
            "phone": candidate.get("home_phone") or candidate.get("phone_number") or candidate.get("cell_phone")
        }
        applicants.append(applicant_info)
    
    return applicants


def get_first_applicant(jwt_token: str, job_id: str) -> dict:
    """
    Get the first applicant's ID and phone number.
    
    Returns:
        Dict with 'id' and 'phone' keys, or None if no applicants
    """
    applicants = get_candidates(jwt_token=jwt_token, job_id=job_id)
    
    if applicants:
        return applicants[0]
    return None


def get_applicant_by_index(jwt_token: str, job_id: str, index: int = 0) -> dict:
    """
    Get a specific applicant by index.
    
    Args:
        jwt_token: Hireology JWT token
        job_id: Job ID
        index: Index of applicant to fetch (default: 0)
    
    Returns:
        Dict with 'id' and 'phone' keys, or None if index out of range
    """
    applicants = get_candidates(jwt_token=jwt_token, job_id=job_id)
    
    if 0 <= index < len(applicants):
        return applicants[index]
    return None


# ============= MAIN EXECUTION =============

if __name__ == "__main__":
    # Configuration
    BEARER_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY2ODY4MjMwLCJuYmYiOjE3NjY4NjQ2MzAsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY2ODY0NjMwfQ.aEC9xnlJKCXAN4G-MnydIvzgJJZU3IzMmrIdqocaPuBZTKEIaSa1jXRlcdeA6z-b-U8dxHEy0GlCSg6wfe5NGnC3dP8orclEbL6zORNT5R9CI8AxtjcMZa9m9MWNVWQEsNO2HlEEpyzkVeIN1rDhknHkOIp2tDv1IJHKD48Uju8vROBuV_nqytTESgxQq1s1588Ga9jvVGU_b0dOEBfxF_LkUQsthqHCQSe0eh-qarpuWWyir8SKRhRGeMGqjvBIp5AHcutSjhq2tUTc3Pd1qfpYYw9kvLBE3RitVURdfAvwJZtfTdU45M-nX67z5OaAgs5-rogW-K0h7-mVYefwaA"
    JOB_ID = "2606114"
    
    # Fetch all applicants
    print("📋 Fetching applicants...")
    applicants = get_candidates(jwt_token=BEARER_TOKEN, job_id=JOB_ID)
    print("The applicants", applicants)
    
    print(f"\n✅ Found {len(applicants)} applicants:\n")
    
    for i, applicant in enumerate(applicants):
        print(f"  [{i}] ID: {applicant['id']} | Phone: {applicant['phone']}")
    
    # Get first applicant
    print("\n📞 First applicant:")
    first = get_first_applicant(BEARER_TOKEN, JOB_ID)
    if first:
        print(f"   ID: {first['id']}")
        print(f"   Phone: {first['phone']}")
    else:
        print("   No applicants found.")
