import requests
import csv

url = "https://api.hireology.com/ats/v3/org/ac036f48-f44d-41b8-a1c7-fcd60b9d60bd/search/jobs"

headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY1NzQ2MDYwLCJuYmYiOjE3NjU3NDI0NjAsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY1NzQyNDYwfQ.uNCbV2IVtbjB-1ojUFIAyG59fWJt6WV8yUIfOH9jdUDzFZLrFpbHCcR7DNkH5w7BGNn80mjrMFfbZqQvVKvAdKAjcnhXj1lpyVHUhcRlFt2x7MPemnM-iDQJ_iLB8wdX815e_LnuhAAf3bd15sp7e2dTjSHpwIsp6rggbRAhjTNfRzdGuXp77z8Ne7MThksGQBogWjSbajBhIaNkoKjo9FVq_EgHoB7PuUZyBaVZF89u4kJQ7TkQzv6yvRtybLygm13EHbGaDqS1lNncA009yAySadohvGdQdLUa4oTGzF_fSz7CFbYrBODLrH6G4K2rDIHOaL0soJpcnLcXpZ31Kw",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

payload = {}

response = requests.post(url, headers=headers, json=payload)
response.raise_for_status()

data = response.json()
print("Data ", data)
jobs = data.get("jobs", [])

print(f"Total jobs found: {len(jobs)}")

with open("jobs.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Legacy ID", "Job ID", "Job Title", "New Applicant Count", "Candidate Count"])

    for job in jobs:
        writer.writerow([
            job.get("legacyId"),
            job.get("id"),
            job.get("title"),
            job.get("applicantCount", 0),
            job.get("candidateCount", 0)
        ])

print("✅ jobs.csv generated successfully")

  