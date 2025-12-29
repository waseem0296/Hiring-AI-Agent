
import requests
import csv
import json
import re


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

def build_single_applicant_record(application_json):
    """
    Extract all application data for a single applicant including 
    basic info, custom questions, and work history (job titles).
    """
    item = application_json[0]  # one applicant
    candidate = item.get("candidate", {})

    # ---------------- BASIC INFO ----------------
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

    # ---------------- CUSTOM QUESTIONS ----------------
    custom_answers = (
        item.get("application", {})
            .get("application_form_data", {})
            .get("custom_answers", {})
    )

    for question, answer_obj in custom_answers.items():
        answer = answer_obj.get("answer")
        record[question.strip()] = answer if answer not in (None, "") else "N/A"

    # # ---------------- WORK HISTORY (IMPORTANT PART) ----------------
    # work_history = (
    #     item.get("application", {})
    #         .get("candidate_work_history", [])
    # )
    # print("Work History:.................",work_history)

    # if work_history:
    #     titles = []
    #     companies = [] 
    #     locations = []

    #     for job in work_history:
    #         if job.get("job_title_held"):
    #             titles.append(job.get("job_title_held"))

    #         if job.get("company_name"):
    #             companies.append(job.get("company_name"))

    #         if job.get("city"):
    #             locations.append(job.get("city"))

    #     record["previous_job_titles"] = ", ".join(titles) if titles else "N/A"
    #     record["previous_companies"] = ", ".join(companies) if companies else "N/A"
    #     record["previous_job_locations"] = ", ".join(locations) if locations else "N/A"
    # else:
    #     record["previous_job_titles"] = "N/A"
    #     record["previous_companies"] = "N/A"
    #     record["previous_job_locations"] = "N/A"

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


def validate_supervisor_references(answer_text):
    """
    Validates that at least 2 supervisor names and 2 phone numbers are provided.
    Returns (is_valid, message)
    """

    if not answer_text or answer_text == "N/A":
        return False, (
            "Please provide at least 2 former supervisors with their names and phone numbers."
        )

    # Count phone numbers (simple but effective)
    phone_numbers = re.findall(r"\+?\d[\d\-\s]{8,}\d", answer_text)

    # Count names (words starting with capital letters)
    names = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b", answer_text)

    if len(phone_numbers) < 2 or len(names) < 2:
        return False, (
            "Please provide at least 2 former supervisors with their names and phone numbers. "
            "Supervisors cannot be co-workers, family members, or friends."
        )

    return True, None


def get_incomplete_questions(applicant_record):
    """
    Returns a list of incomplete questions including business-rule validation.
    """

    ignore_fields = {
        "candidate_id", "first_name", "last_name", "email", "phone_number",
        "address", "city", "state", "zip_code", "job_name", "status", "applied_at"
    }

    incomplete = []

    SUPERVISOR_QUESTION = (
        "Please provide the contact name and phone number of 2-3 former supervisors. "
        "*Cannot be co-workers, family, or friends*"
    )

    for field, value in applicant_record.items():
        if field in ignore_fields:
            continue

        # Standard missing check
        if value in ("N/A", None, ""):
            incomplete.append(field)
            continue

        # Special supervisor validation
        if SUPERVISOR_QUESTION in field:
            is_valid, message = validate_supervisor_references(value)
            if not is_valid:
                incomplete.append(message)

    return incomplete


def send_incomplete_application_email(
    jwt_token,
    candidate_job_id,
    candidate_email,
    job_id,
    job_name,
    incomplete_questions
):
    """
    Send incomplete application email to candidate.
    Returns True if successful, False otherwise.
    """
    url = "https://api.hireology.com/v2/emails/send_single_email"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "*/*"
        # DO NOT set Content-Type manually
    }

    questions_html = "".join(
        f"<li>{q}</li>" for q in incomplete_questions
    )

    email_body = f"""
    <p>Dear Applicant,</p>

    <p>Your application for <strong>{job_name}</strong> is incomplete.</p>

    <p>Please complete the following required information:</p>

    <ul>
        {questions_html}
    </ul>

    <p>Once completed, your application will proceed for further review.</p>

    <p>Thank you,<br>Hiring Team</p>
    """

    data = {
        "candidate_job_ids[]": str(candidate_job_id),
        "user[email_to]": candidate_email,
        "user[email_subject]": "Incomplete Application – Action Required",
        "user[email_body]": email_body,
        "job_id": str(job_id),
        "email_type": "custom"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            timeout=30
        )

        print(f"Email POST status: {response.status_code}")
        print(f"Response: {response.text}")

        # Check if email was sent successfully
        if response.status_code == 200:
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ Email sending failed with exception: {e}")
        return False

import re
def evaluate_caregiver_experience(applicant_record):
    """
    Evaluates caregiver/nursing experience using:
    1) Free-text caregiving description
    2) Previous job titles
    Returns 'Candidate' or 'Inactive'
    """

    # -------- TEXT SOURCES --------
    description = applicant_record.get(
        "Can you briefly describe your previous caregiving roles, including your main responsibilities and the care settings you worked in?",
        ""
    )

    job_titles = applicant_record.get("job_title_held", "")

    combined_text = f"{description} {job_titles}".lower()

    if not combined_text.strip():
        return "Inactive"

    # -------- EXPANDED KEYWORDS --------
    caregiver_keywords = [
        # Caregiving
        "caregiver", "caregiving", "carer", "home care", "personal care",
        "companion care", "elder care", "elderly care", "senior care",
        "geriatric", "hospice", "palliative", "respite",

        # Nursing
        "nurse", "nursing", "registered nurse", "rn",
        "licensed practical nurse", "lpn",
        "licensed vocational nurse", "lvn",
        "nursing assistant", "nurse aide",

        # Certifications / Clinical
        "cna", "pct", "medtech", "medical technician",
        "patient care technician", "medical assistant",
        "healthcare aide", "clinical aide",

        # Facilities
        "assisted living", "long-term care", "nursing home",
        "skilled nursing", "snf", "rehab", "rehabilitation",
        "hospital", "clinic", "memory care", "dementia care",

        # Responsibilities
        "patient care", "direct care", "activities of daily living", "adl",
        "bathing", "feeding", "toileting", "grooming",
        "mobility assistance", "vitals", "medication"
    ]

    # -------- MATCH CHECK --------
    for keyword in caregiver_keywords:
        if keyword in combined_text:
            return "Candidate"

    return "Inactive"

def get_rejection_reason(applicant_record):
    """
    Generates a reason why the applicant was rejected based on business rules.
    """
    reasons = []

    # Experience check
    experience_text = applicant_record.get(
        "How many years of professional caregiving experience do you have?", ""
    )
    match = re.search(r"\d+", str(experience_text))
    years = int(match.group()) if match else 0
    if years < 1:
        reasons.append("Less than 1 year of professional caregiving experience")

    # Driver's license check
    drivers_license = applicant_record.get(
        "Do you have a valid driver's license, and car insurance?", ""
    )
    if drivers_license.strip().lower() != "yes":
        reasons.append("Does not have a valid driver's license and car insurance")

    # Drug screen check
    drug_screen = applicant_record.get("Are you able to pass a drug screen?", "")
    if drug_screen.strip().lower() != "yes":
        reasons.append("Unable to pass a drug screen")

    # Criminal record check
    criminal_record = applicant_record.get(
        "Have you been arrested, convicted of a felony, or misdemeanor?", ""
    )
    if criminal_record.strip().lower() != "no":
        reasons.append("Has a criminal record")

    # NEW: Caregiver experience description check
    selection_status = evaluate_caregiver_experience(applicant_record)
    if selection_status == "Inactive":
        reasons.append("No relevant caregiver experience or certification found")

    if not reasons:
        return "Did not meet our standard application requirements."

    return "; ".join(reasons)


def send_rejection_email(jwt_token, candidate_job_id, candidate_email, job_name, rejection_reason):
    """
    Send rejection email to candidate.
    Returns True if successful, False otherwise.
    """
    url = "https://api.hireology.com/v2/emails/send_single_email"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "*/*"
    }

    email_body = f"""
    <p>Dear Applicant,</p>

    <p>Thank you for applying for <strong>{job_name}</strong>.</p>

    <p>We regret to inform you that your application has not been successful.</p>

    <p><strong>Reason for rejection:</strong></p>
    <p>{rejection_reason}</p>

    <p>We encourage you to apply for future opportunities that match your skills.</p>

    <p>Thank you,<br>Hiring Team</p>
    """

    data = {
        "candidate_job_ids[]": str(candidate_job_id),
        "user[email_to]": candidate_email,
        "user[email_subject]": "Application Status – Rejection",
        "user[email_body]": email_body,
        "job_id": str(candidate_job_id),
        "email_type": "custom"
    }

    try:
        response = requests.post(url, headers=headers, data=data, timeout=30)

        print(f"📧 Rejection Email POST status: {response.status_code}")
        print(f"📧 Response: {response.text}")

        return response.status_code == 200

    except Exception as e:
        print(f"❌ Rejection email sending failed with exception: {e}")
        return False


def decide_candidate_status(applicant_record):
    """
    Decide whether candidate should be Advanced (Candidate) or Inactive.
    """

    # Extract answers safely
    experience_text = applicant_record.get(
        "How many years of professional caregiving experience do you have?", ""
    )

    drivers_license = applicant_record.get(
        "Do you have a valid driver's license, and car insurance?", ""
    )

    drug_screen = applicant_record.get(
        "Are you able to pass a drug screen?", ""
    )

    criminal_record = applicant_record.get(
        "Have you been arrested, convicted of a felony, or misdemeanor?", ""
    )

    # 1️⃣ Extract number of years from text like "4 years"
    years = 0
    match = re.search(r"\d+", str(experience_text))
    if match:
        years = int(match.group())

    # 2️⃣ Apply rules
    if (
        years >= 1
        and drivers_license.strip().lower() == "yes"
        and drug_screen.strip().lower() == "yes"
        and criminal_record.strip().lower() == "no"
    ):
        return "Candidate"   # Advance
    else:
        return "Inactive"


def update_candidate_status(jwt_token, job_id, candidate_id, status):
    """
    Update candidate status in Hireology.
    """

    url = f"https://api.hireology.com/v2/jobs/{job_id}/candidates/{candidate_id}"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "*/*"
    }

    payload = {
        "status": status
    }

    response = requests.put(url, headers=headers, json=payload, timeout=30)

    print(f"🔄 Updating status to '{status}'")
    print(f"Status Code: {response.status_code}")
    print(f"📄 Response: {response.text}")

    response.raise_for_status()
    return response.json()


# Example usage:
if __name__ == "__main__":
    # Your JWT token and job ID
    jwt = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY2MjQxOTI0LCJuYmYiOjE3NjYyMzgzMjQsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY2MjM4MzI0fQ.NfGjBU0QgS9B1m_hsU3wOCXE2iYuLem9JoWooKNNUIXnBXxaztkHasPmUlAIQcQ8gA6st1HoIKoqKflYONM6lpY1wez2aKFdHkZKL0Y5H448_39l_TrUZ7Fyh3OGp02PxgOnx2aoC6V7NR7RQVAoA7DYQnJBNE11BcIk5fGC6uGKxQIYENLoQhkosQ1bX5AGnmx8prw4Ajjx1Jeq9vZJVscnDqi9Sixqq87DyiwLCdR8cIDzfnSiRm-SgwRGOKBPXduY0cY_l-1HszyuDkgqvhfoPA04Ucws1ks8KLBe_fQpwSiGcqxxm-wtEBQOa5WECzPTqcCFNyxge42gI32Ccg"
            
    job_id = "2606114"
    
    # Step 1: Get all candidates
    print("🔍 Fetching candidates...")
    candidates = get_candidates(jwt_token=jwt, job_id=job_id)
    print("candidates:", candidates)
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
    candidate_job_id = documents[0].get("id")
    
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

        email_sent = send_incomplete_application_email(
            jwt_token=jwt,
            candidate_job_id=candidate_job_id,
            candidate_email=applicant_record["email"],
            job_id=job_id,
            job_name=applicant_record["job_name"],
            incomplete_questions=incomplete_questions
        )

        if email_sent:
            print("✅ Email sent successfully")
        else:
            print("❌ Email sending failed")
        
        # Don't process further if application is incomplete
        print("\n⏹️  Stopping processing - application is incomplete")
        exit(0)

    else:
        print("✅ Application is complete. Proceeding with evaluation...")
    
    # Step 8: Decide candidate status (only if application is complete)
    final_status = decide_candidate_status(applicant_record)
    print(f"\n🎯 Final Decision: {final_status}")

    # Step 9: Send rejection email if Inactive
    if final_status == "Inactive":
        rejection_reason = get_rejection_reason(applicant_record)
        print(f"\n📧 Sending rejection email... Reason: {rejection_reason}")

        email_sent = send_rejection_email(
            jwt_token=jwt,
            candidate_job_id=candidate_job_id,
            candidate_email=applicant_record["email"],
            job_name=applicant_record["job_name"],
            rejection_reason=rejection_reason
        )

        if email_sent:
            print("✅ Rejection email sent successfully")
        else:
            print("❌ Failed to send rejection email")

    # Step 10: Update status in Hireology
    print(f"\n🔄 Updating candidate status to '{final_status}'...")
    update_response = update_candidate_status(
        jwt_token=jwt,
        job_id=job_id,
        candidate_id=applicant_record["candidate_id"],
        status=final_status
    )

    print("✅ Candidate status updated successfully")
    
    print("\n🎉 Processing complete!")