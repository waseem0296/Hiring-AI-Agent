# import requests
# import csv
# import json


# def get_candidates(jwt_token, job_id, page_size=10):
#     """
#     Fetch candidates for a specific job from Hireology.
#     """
#     url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates"
#     headers = {
#         "Authorization": f"Bearer {jwt_token}",
#         "Content-Type": "application/json",
#         "Accept": "application/json"
#     }
#     params = {
#         "filter[status]": "Applicant",
#         "sort_dir": "desc",
#         "sort_step_id": "",
#         "sort": "date",
#         "page_size": page_size
#     }

#     response = requests.get(url, headers=headers, params=params)
#     response.raise_for_status()
#     return response.json()


# def get_candidate_documents(jwt_token, job_id, candidate_id, transfer=False):
#     """
#     Fetch all documents for a candidate from Hireology.

#     :param jwt_token: JWT access token (string)
#     :param job_id: Job ID (string or int)
#     :param candidate_id: Candidate ID (string or int)
#     :param transfer: Boolean flag for transfer parameter
#     :return: JSON response
#     """
#     url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates/{candidate_id}/documents/all_documents"

#     headers = {
#         "Authorization": f"Bearer {jwt_token}",
#         "Accept": "application/json"
#     }

#     params = {
#         "transfer": str(transfer).lower()  # API expects true/false as string
#     }

#     try:
#         response = requests.get(url, headers=headers, params=params, timeout=30)
#         response.raise_for_status()
#         return response.json()

#     except requests.exceptions.HTTPError as http_err:
#         print(f"HTTP Error: {http_err}")
#         print("Response:", response.text)
#     except Exception as err:
#         print(f"Error: {err}")

#     return None


# def extract_applicant_ids(response_json):
#     """
#     Extract applicant IDs from Hireology candidates response.
#     """
#     return [applicant["id"] for applicant in response_json.get("data", [])]


# def build_single_applicant_record(application_json):
#     """
#     Extract all application data for a single applicant including 
#     basic info and all custom question answers.
#     """
#     item = application_json[0]  # one applicant
    
#     candidate = item.get("candidate", {})
    
#     # Basic candidate information
#     record = {
#         "candidate_id": candidate.get("id", "N/A"),
#         "first_name": candidate.get("first_name", "N/A"),
#         "last_name": candidate.get("last_name", "N/A"),
#         "email": candidate.get("email", "N/A"),
#         "phone_number": candidate.get("phone_number", "N/A"),
#         "address": candidate.get("street_address", "N/A"),
#         "city": candidate.get("city", "N/A"),
#         "state": candidate.get("state", "N/A"),
#         "zip_code": candidate.get("zip_code", "N/A"),
#         "job_name": item.get("job_name", "N/A"),
#         "status": candidate.get("status", "N/A"),
#         "applied_at": candidate.get("applied_at", "N/A"),
#     }
    
#     # ✅ CORRECT PATH: application -> application_form_data -> custom_answers
#     custom_answers = (
#         item.get("application", {})
#             .get("application_form_data", {})
#             .get("custom_answers", {})
#     )
    
#     # Add all custom question answers to the record
#     for question, answer_obj in custom_answers.items():
#         answer = answer_obj.get("answer")
#         # Clean up the question text for column header
#         clean_question = question.strip()
#         record[clean_question] = answer if answer not in (None, "") else "N/A"
    
#     return record


# def write_single_record_to_csv(record, filename="application_answers.csv"):
#     """
#     Write a single applicant record to CSV file.
#     """
#     with open(filename, "w", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=record.keys())
#         writer.writeheader()
#         writer.writerow(record)
    
#     print(f"✅ CSV written successfully: {filename}")
#     print(f"📊 Total fields: {len(record)}")
# def get_incomplete_questions(applicant_record):
#     """
#     Returns a list of questions that are incomplete (N/A).
#     Ignores base candidate fields.
#     """

#     ignore_fields = {
#         "candidate_id", "first_name", "last_name",
#         "address", "city", "state",
#         "zip_code", "job_name", "status", "applied_at"
#     }

#     incomplete = []

#     for field, value in applicant_record.items():
#         if field in ignore_fields:
#             continue
#         if value == "N/A":
#             incomplete.append(field)

#     return incomplete
# def send_incomplete_application_email(jwt_token, candidate_id, candidate_email, job_name, incomplete_questions):
#     """
#     Sends an email to the applicant using Hireology email API.
#     """

#     url = "https://api.hireology.com/v2/emails/send_single_email"

#     headers = {
#         "Authorization": f"Bearer {jwt_token}",
#         "Content-Type": "application/json",
#         "Accept": "application/json"
#     }

#     questions_list = "\n".join(
#         f"- {q}" for q in incomplete_questions
#     )

#     body_text = f"""
# Dear Applicant,

# Your application for the position of "{job_name}" is currently incomplete.

# Please complete the following required questions and submit your application again:

# {questions_list}

# Once completed, your application will continue to the next stage of review.

# Thank you,
# Hiring Team
# """

#     payload = {
#         "recipient_type": "candidate",
#         "candidate_id": candidate_id,
#         "subject": "Incomplete Application – Action Required",
#         "body": body_text.strip(),
#         "send_email": True
#     }

#     response = requests.post(url, headers=headers, json=payload)
#     response.raise_for_status()

#     return response.json()


# # Example usage:
# if __name__ == "__main__":
#     # Your JWT token and job ID
#     jwt = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY1ODM3MjY2LCJuYmYiOjE3NjU4MzM2NjYsImlkcCI6Imdvb2dsZS5jb20iLCJzdWIiOiIyMzBhOTY2YS03OGNiLTRjMzktYWRhMy03ZTg5MjVjYzZkOTEiLCJvaWQiOiIyMzBhOTY2YS03OGNiLTRjMzktYWRhMy03ZTg5MjVjYzZkOTEiLCJtZmEiOnRydWUsImF6ZnAiOnRydWUsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY1ODMzNjY2fQ.LUhF8-a1-YYxsaQErYaPZK9dV2paJ6jX6xim35fo3651n75o_cHjX8lMc70ciILC5JieHQyEOScoIwylOnA9voacz5j1vJIDjh5AvcSkdH5qLsMJ6za19MXWBrPiYwXBNf9lXJZG_a130x7pfzvQL2y7f0ok9ohxFddUqs4VUwzGf7nBWf9wvuFA_cKxFBLIQkhzu2zFuEL5FKoHFNH5DS-lcRC-HkMst9iPI5dY8hyTchTxDn1MJIXnq9YKkvnQkqqH_WALCjytkTi63cNFTF7EvUWibZi2XLncA0gN33GYkLx3hTo7W3eR_epyzIPPE8kBfPQoYhIdUqKiyZVWPw"
#     job_id = "2160721"
    
#     # Step 1: Get all candidates
#     print("🔍 Fetching candidates...")
#     candidates = get_candidates(jwt_token=jwt, job_id=job_id)
#     applicant_ids = extract_applicant_ids(candidates)
#     print(f"✅ Found {len(applicant_ids)} applicants: {applicant_ids}")

#     # Step 2: Get the first applicant's documents
#     CANDIDATE_ID = applicant_ids[0]
#     print(f"\n📄 Fetching documents for candidate {CANDIDATE_ID}...")
    
#     documents = get_candidate_documents(
#         jwt_token=jwt,
#         job_id=job_id,
#         candidate_id=CANDIDATE_ID,
#         transfer=False
#     )

#     if documents is None:
#         print("❌ Failed to fetch documents")
#         exit(1)
    

#     print("✅ Documents fetched successfully")
#     print(documents)

#     # Step 3: documents is already a JSON object (list/dict), not a filename
#     # So we use it directly instead of opening it as a file
#     application_data = documents  # 🔥 THIS IS THE KEY FIX
    
#     # Step 4: Build the record
#     print("\n📊 Building applicant record...")
#     applicant_record = build_single_applicant_record(application_data)
    
#     # Step 5: Write to CSV
#     write_single_record_to_csv(applicant_record, "basil_khan_application.csv")
    
#     # Step 6: Print all fields to verify
#     print("\n📋 All fields extracted:")
#     for key, value in applicant_record.items():
#         print(f"  {key}: {value}")
        
#         #  https://api.hireology.com/v2/emails/send_single_email
#     # Step 7: Check for incomplete questions
#     incomplete_questions = get_incomplete_questions(applicant_record)

#     if incomplete_questions:
#         print("⚠ Incomplete application detected")
#         print("Missing questions:")
#         for q in incomplete_questions:
#             print(" -", q)

#         print("\n📧 Sending reminder email to applicant...")

#         email_response = send_incomplete_application_email(
#             jwt_token=jwt,
#             candidate_id=applicant_record["candidate_id"],
#             candidate_email=applicant_record["email"],
#             job_name=applicant_record["job_name"],
#             incomplete_questions=incomplete_questions
#         )

#         print("✅ Email sent successfully")
#         print(email_response)

#     else:
#         print("✅ Application is complete. No email sent.")



import requests
import csv
import json


def get_candidates(jwt_token, job_id, page_size=10):
    """
    Fetch candidates for a specific job from Hireology.
    """
    url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    params = {
        "filter[status]": "Applicant",
        "sort_dir": "desc",
        "sort_step_id": "",
        "sort": "date",
        "page_size": page_size
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def get_candidate_documents(jwt_token, job_id, candidate_id, transfer=False):
    """
    Fetch all documents for a candidate from Hireology.

    :param jwt_token: JWT access token (string)
    :param job_id: Job ID (string or int)
    :param candidate_id: Candidate ID (string or int)
    :param transfer: Boolean flag for transfer parameter
    :return: JSON response
    """
    url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates/{candidate_id}/documents/all_documents"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/json"
    }

    params = {
        "transfer": str(transfer).lower()  # API expects true/false as string
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error: {http_err}")
        print("Response:", response.text)
    except Exception as err:
        print(f"Error: {err}")

    return None


def extract_applicant_ids(response_json):
    """
    Extract applicant IDs from Hireology candidates response.
    """
    return [applicant["id"] for applicant in response_json.get("data", [])]


def build_single_applicant_record(application_json):
    """
    Extract all application data for a single applicant including 
    basic info and all custom question answers.
    """
    item = application_json[0]  # one applicant
    
    candidate = item.get("candidate", {})
    
    # Basic candidate information
    record = {
        "candidate_id": candidate.get("id", "N/A"),
        "first_name": candidate.get("first_name", "N/A"),
        "last_name": candidate.get("last_name", "N/A"),
        "email": candidate.get("email", "N/A"),
        "phone_number": candidate.get("phone_number", "N/A"),
        "address": candidate.get("street_address", "N/A"),
        "city": candidate.get("city", "N/A"),
        "state": candidate.get("state", "N/A"),
        "zip_code": candidate.get("zip_code", "N/A"),
        "job_name": item.get("job_name", "N/A"),
        "status": candidate.get("status", "N/A"),
        "applied_at": candidate.get("applied_at", "N/A"),
    }
    
    # ✅ CORRECT PATH: application -> application_form_data -> custom_answers
    custom_answers = (
        item.get("application", {})
            .get("application_form_data", {})
            .get("custom_answers", {})
    )
    
    # Add all custom question answers to the record
    for question, answer_obj in custom_answers.items():
        answer = answer_obj.get("answer")
        # Clean up the question text for column header
        clean_question = question.strip()
        record[clean_question] = answer if answer not in (None, "") else "N/A"
    
    return record


def write_single_record_to_csv(record, filename="application_answers.csv"):
    """
    Write a single applicant record to CSV file.
    """
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=record.keys())
        writer.writeheader()
        writer.writerow(record)
    
    print(f"✅ CSV written successfully: {filename}")
    print(f"📊 Total fields: {len(record)}")


def get_incomplete_questions(applicant_record):
    """
    Returns a list of questions that are incomplete (N/A).
    Ignores base candidate fields.
    """
    ignore_fields = {
        "candidate_id", "first_name", "last_name", "email", "phone_number",
        "address", "city", "state", "zip_code", "job_name", "status", "applied_at"
    }

    incomplete = []

    for field, value in applicant_record.items():
        if field in ignore_fields:
            continue
        if value == "N/A" or value is None or value == "":
            incomplete.append(field)

    return incomplete


def send_incomplete_application_email(jwt_token, candidate_id, candidate_email, job_name, incomplete_questions):
    """
    Sends an email to the applicant using Hireology email API.
    """
    url = "https://api.hireology.com/v2/emails/send_single_email"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    questions_list = "\n".join(f"- {q}" for q in incomplete_questions)

    body_text = f"""Dear Applicant,

Your application for the position of "{job_name}" is currently incomplete.

Please complete the following required questions and submit your application again:

{questions_list}

Once completed, your application will continue to the next stage of review.

Thank you,
Hiring Team"""

    # 🔥 FIXED: Corrected payload structure based on Hireology API docs
    payload = {
        "recipient_type": "candidate",
        "candidate_id": str(candidate_id),  # Ensure it's a string
        "subject": "Incomplete Application – Action Required",
        "body": body_text,
        "from_email": None,  # Uses default organization email
        "from_name": None    # Uses default organization name
    }

    try:
        print(f"\n📧 Sending email to: {candidate_email}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Print response details for debugging
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Body: {response.text}")
        
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP Error: {http_err}")
        print(f"📄 Response Text: {response.text}")
        
        # Try alternative payload format if first attempt fails
        print("\n🔄 Trying alternative email format...")
        
        # Alternative: Use simpler format
        alt_payload = {
            "recipient_type": "candidate",
            "candidate_id": int(candidate_id),  # Try as integer
            "subject": "Incomplete Application – Action Required",
            "body": body_text
        }
        
        try:
            alt_response = requests.post(url, headers=headers, json=alt_payload, timeout=30)
            alt_response.raise_for_status()
            return alt_response.json()
        except Exception as alt_err:
            print(f"❌ Alternative format also failed: {alt_err}")
            return None
            
    except Exception as err:
        print(f"❌ Error: {err}")
        return None


# Example usage:
if __name__ == "__main__":
    # Your JWT token and job ID
    jwt = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY1ODM3MjY2LCJuYmYiOjE3NjU4MzM2NjYsImlkcCI6Imdvb2dsZS5jb20iLCJzdWIiOiIyMzBhOTY2YS03OGNiLTRjMzktYWRhMy03ZTg5MjVjYzZkOTEiLCJvaWQiOiIyMzBhOTY2YS03OGNiLTRjMzktYWRhMy03ZTg5MjVjYzZkOTEiLCJtZmEiOnRydWUsImF6ZnAiOnRydWUsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY1ODMzNjY2fQ.LUhF8-a1-YYxsaQErYaPZK9dV2paJ6jX6xim35fo3651n75o_cHjX8lMc70ciILC5JieHQyEOScoIwylOnA9voacz5j1vJIDjh5AvcSkdH5qLsMJ6za19MXWBrPiYwXBNf9lXJZG_a130x7pfzvQL2y7f0ok9ohxFddUqs4VUwzGf7nBWf9wvuFA_cKxFBLIQkhzu2zFuEL5FKoHFNH5DS-lcRC-HkMst9iPI5dY8hyTchTxDn1MJIXnq9YKkvnQkqqH_WALCjytkTi63cNFTF7EvUWibZi2XLncA0gN33GYkLx3hTo7W3eR_epyzIPPE8kBfPQoYhIdUqKiyZVWPw"
    job_id = "2160721"
    
    # Step 1: Get all candidates
    print("🔍 Fetching candidates...")
    candidates = get_candidates(jwt_token=jwt, job_id=job_id)
    applicant_ids = extract_applicant_ids(candidates)
    print(f"✅ Found {len(applicant_ids)} applicants: {applicant_ids}")

    # Step 2: Get the first applicant's documents
    CANDIDATE_ID = applicant_ids[0]
    print(f"\n📄 Fetching documents for candidate {CANDIDATE_ID}...")
    
    documents = get_candidate_documents(
        jwt_token=jwt,
        job_id=job_id,
        candidate_id=CANDIDATE_ID,
        transfer=False
    )

    if documents is None:
        print("❌ Failed to fetch documents")
        exit(1)

    print("✅ Documents fetched successfully")
    print(documents)

    # Step 3: Use documents directly (already parsed JSON)
    application_data = documents
    
    # Step 4: Build the record
    print("\n📊 Building applicant record...")
    applicant_record = build_single_applicant_record(application_data)
    
    # Step 5: Write to CSV
    write_single_record_to_csv(applicant_record, "basil_khan_application.csv")
    
    # Step 6: Print all fields to verify
    print("\n📋 All fields extracted:")
    for key, value in applicant_record.items():
        print(f"  {key}: {value}")
    
    # Step 7: Check for incomplete questions
    print("\n🔍 Checking for incomplete questions...")
    incomplete_questions = get_incomplete_questions(applicant_record)

    if incomplete_questions:
        print(f"⚠️  Incomplete application detected - {len(incomplete_questions)} missing answers")
        print("\n📝 Missing questions:")
        for q in incomplete_questions:
            print(f"   - {q}")

        print("\n📧 Sending reminder email to applicant...")

        email_response = send_incomplete_application_email(
            jwt_token=jwt,
            candidate_id=applicant_record["candidate_id"],
            candidate_email=applicant_record["email"],
            job_name=applicant_record["job_name"],
            incomplete_questions=incomplete_questions
        )

        if email_response:
            print("✅ Email sent successfully")
            print(f"📬 Response: {json.dumps(email_response, indent=2)}")
        else:
            print("❌ Failed to send email")

    else:
        print("✅ Application is complete. No email needed.")