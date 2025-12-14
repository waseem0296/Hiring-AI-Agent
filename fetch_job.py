import requests
import csv

# ===================== CONFIG =====================

URL = "https://api.hireology.com/ats/v3/org/ac036f48-f44d-41b8-a1c7-fcd60b9d60bd/search/jobs"

HEADERS = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY1NzQ2MDYwLCJuYmYiOjE3NjU3NDI0NjAsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY1NzQyNDYwfQ.uNCbV2IVtbjB-1ojUFIAyG59fWJt6WV8yUIfOH9jdUDzFZLrFpbHCcR7DNkH5w7BGNn80mjrMFfbZqQvVKvAdKAjcnhXj1lpyVHUhcRlFt2x7MPemnM-iDQJ_iLB8wdX815e_LnuhAAf3bd15sp7e2dTjSHpwIsp6rggbRAhjTNfRzdGuXp77z8Ne7MThksGQBogWjSbajBhIaNkoKjo9FVq_EgHoB7PuUZyBaVZF89u4kJQ7TkQzv6yvRtybLygm13EHbGaDqS1lNncA009yAySadohvGdQdLUa4oTGzF_fSz7CFbYrBODLrH6G4K2rDIHOaL0soJpcnLcXpZ31Kw",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# ===================== FUNCTIONS =====================

def fetch_jobs():
    """Fetch all jobs from Hireology"""
    response = requests.post(URL, headers=HEADERS, json={})
    response.raise_for_status()
    return response.json()


def write_jobs_to_csv(jobs, filename="jobs.csv"):
    """Write job details to CSV"""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Legacy ID",
            "Job ID",
            "Job Title",
            "Applicant Count",
            "Candidate Count"
        ])

        for job in jobs:
            writer.writerow([
                job.get("legacyId"),
                job.get("id"),
                job.get("title"),
                job.get("applicantCount", 0),
                job.get("candidateCount", 0)
            ])


def get_jobs_with_applicants_only(data):
    """
    Return legacyId and title of jobs where applicantCount > 0
    """
    jobs = data.get("jobs", [])
    result = []

    for job in jobs:
        if job.get("applicantCount", 0) > 0:
            result.append({
                "legacyId": job.get("legacyId"),
                "title": job.get("title")
            })

    return result


def main():
    data = fetch_jobs()
    jobs = data.get("jobs", [])
    print(f"Total jobs found: {len(jobs)}")

    write_jobs_to_csv(jobs)
    print("✅ jobs.csv generated successfully")

    jobs_with_applicants = get_jobs_with_applicants_only(data)
    print("Jobs with applicants:")
    for job in jobs_with_applicants:
        print(job["legacyId"], "-", job["title"])


# ===================== ENTRY POINT =====================

if __name__ == "__main__":
    main()

  