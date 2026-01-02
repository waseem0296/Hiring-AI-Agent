
"""
Applicant ID Fetcher
Fetches applicant IDs and phone numbers from Hireology
"""

from fetch_applicants import get_candidates


def get_applicants_info(jwt_token: str, job_id: str) -> list[dict]:
    """
    Fetch all applicants and return their ID and phone number.
    """
    response = get_candidates(jwt_token=jwt_token, job_id=job_id)

    applicants = []

    # REAL response key is "data"
    candidates = response.get("data", [])

    for candidate in candidates:
        applicants.append({
            "id": candidate.get("id"),
            "phone": (
                candidate.get("home_phone")
                or candidate.get("phone_number")
                or candidate.get("cell_phone")
            )
        })

    return applicants


def get_first_applicant(jwt_token: str, job_id: str) -> dict | None:
    applicants = get_applicants_info(jwt_token, job_id)
    return applicants[0] if applicants else None


def get_applicant_by_index(jwt_token: str, job_id: str, index: int = 0) -> dict | None:
    applicants = get_applicants_info(jwt_token, job_id)
    return applicants[index] if 0 <= index < len(applicants) else None


# ============= MAIN =============

if __name__ == "__main__":

    BEARER_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY3MDI2Mzg5LCJuYmYiOjE3NjcwMjI3ODksImlkcCI6Imdvb2dsZS5jb20iLCJzdWIiOiIyMzBhOTY2YS03OGNiLTRjMzktYWRhMy03ZTg5MjVjYzZkOTEiLCJvaWQiOiIyMzBhOTY2YS03OGNiLTRjMzktYWRhMy03ZTg5MjVjYzZkOTEiLCJtZmEiOnRydWUsImF6ZnAiOnRydWUsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY3MDIyNzg5fQ.rbGmdKB3rvzRwiFQakgs-1i-3Ya4iOn-CkJHOfh9zvjYPfrcw-Kmg33_7GNL3aYgK72phKBozLwr_E1mpxuYIi66kdrOvFJFdQAF32rWz74v2bLycqjYcTg57GFUxdu3y1xF_oIcdVlZtX16oXP4THoUNjJ4FsajubwcPtMH3Adk6fXJt8MojwNxvCzSR8vnIfzFQOV18qgDqjQ34LL3iqdLpF5Xp_8Wh6kaG84IhRHZL98cnqthaA8yUllYsUCLLjwIY513dG_oiKeWk9AVOpGtH2DjXpKubESJo86NESvGiZkyxU-hNgGJ2qXJ0CwKrOivTrGvjgoKNSyzO9oJlA"
    JOB_ID = "2606114"

    print("📋 Fetching applicants...\n")

    applicants = get_applicants_info(BEARER_TOKEN, JOB_ID)

    print(f"✅ Found {len(applicants)} applicants:\n")

    for i, applicant in enumerate(applicants):
        print(f"[{i}] ID: {applicant['id']} | Phone: {applicant['phone']}")

    print("\n📞 First applicant:")
    first = get_first_applicant(BEARER_TOKEN, JOB_ID)
    print(first if first else "No applicants found.")
