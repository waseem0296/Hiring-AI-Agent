
import requests
import csv
import re
from dotenv import load_dotenv
import os

load_dotenv()  

API_URL = "https://api.hireology.com/v2/candidates"
API_KEY = os.getenv("HIREOLOGY_API_KEY")
OUTPUT_FILE = "form_data.csv"
SELECTED_FILE = "selected.csv"
REJECTED_FILE = "rejected.csv"
PER_PAGE = 100
MAX_PAGES = 50

def fetch_page(page):
    params = {
        "access_token": API_KEY,
        "page": page,
        "per_page": PER_PAGE,
        "application_form_data": "true"
    }
    r = requests.get(API_URL, params=params)

    print("STATUS:", r.status_code)
    if r.status_code != 200:
        print("API ERROR:", r.text)
        return []

    try:
        return r.json().get("data", [])
    except Exception as e:
        print("JSON ERROR:", r.text, e)
        return []

BASIC_FIELDS = [
    "id",
    "first_name",
    "last_name",
    "email",
    "phone",
    "street",
    "city",
    "state",
    "zip",
    "years_of_experience",
    "work_permit_in_us",
    "desired_compensation_hourly",
    "company_name",
    "job_title_held",
    "start_date",
    "end_date"
]

DESIRED_QUESTIONS = [
    'Please provide the contact name and phone number of 2-3 former supervisors. ',
    'Have you been arrested, convicted of a felony, or misdemeanor? ',
    'Are you able to pass a drug screen? ',
    "Do you have a valid driver's license, and car insurance?",
    'How many years of professional caregiving experience do you have?',
    'Do you currently hold any caregiving-related certifications (CNA, PCT, LPN, RN, MedTech, etc.)?',
    'Can you briefly describe your previous caregiving roles, including your main responsibilities and the care settings you worked in?',
    'What is your availability to start? Immediately or within a required timeframe?',
    'What was/ is your most recent pay rate?'
]

def extract_answers(candidate):
    """
    Extract custom question answers from the candidate data.
    Fixed to properly navigate the nested structure.
    """
    answers = {q: "N/A" for q in DESIRED_QUESTIONS}
    
    app_data_list = candidate.get("application_form_data", [])
    
    for entry in app_data_list:
        form = entry.get("application_form_data", {})
        custom = form.get("custom_answers") or {}
        sections = form.get("form_sections") or {}
        
        # Build a map of question names to their IDs
        question_name_to_id = {}
        for section_name, questions in sections.items():
            for q in questions:
                q_name = q.get("name", "")
                q_id = str(q.get("id", ""))
                if q_name:
                    question_name_to_id[q_name] = q_id
        
        # Match our desired questions with answers
        for desired_q in DESIRED_QUESTIONS:
            if desired_q in question_name_to_id:
                q_id = question_name_to_id[desired_q]
                if q_id in custom:
                    ans = custom[q_id].get("answer")
                    if ans:
                        answers[desired_q] = ans
            else:
                # Try partial match
                for q_name, q_id in question_name_to_id.items():
                    if desired_q.strip() in q_name or q_name in desired_q.strip():
                        if q_id in custom:
                            ans = custom[q_id].get("answer")
                            if ans:
                                answers[desired_q] = ans
                                break
    
    return answers


def extract_basic(c):
    """
    Extract basic candidate information.
    """
    profile = {}
    hr = {}
    work = {}
    
    app_data_list = c.get("application_form_data", [])
    if app_data_list:
        first_app = app_data_list[0]
        app_form = first_app.get("application_form_data", {})
        
        profile = app_form.get("candidate_profile") or {}
        hr = app_form.get("candidate_hr_attributes") or {}
        work_history = app_form.get("candidate_work_history") or []
        work = work_history[0] if work_history else {}

    return {
        "id": c.get("id"),
        "first_name": c.get("first_name", ""),
        "last_name": c.get("last_name", ""),
        "email": c.get("email", ""),
        "phone": c.get("home_phone", ""),
        "street": c.get("street_address", ""),
        "city": c.get("city", ""),
        "state": c.get("state", ""),
        "zip": c.get("zip_code", ""),
        "years_of_experience": profile.get("years_of_experience", ""),
        "work_permit_in_us": profile.get("work_permit_in_us", ""),
        "desired_compensation_hourly": hr.get("candidate.desired_compensation.hourly", ""),
        "company_name": work.get("company_name", ""),
        "job_title_held": work.get("job_title_held", ""),
        "start_date": work.get("start_date", ""),
        "end_date": work.get("end_date", ""),
    }


def is_caregiving_qualified(basic_info, answer_info):
    """
    Filter candidates based on caregiving qualifications.
    
    Criteria:
    1. Job title must indicate caregiving/medical background
    2. Must have caregiving experience (years > 0 OR answered the experience question)
    3. Must have certifications OR good caregiving description
    """
    
    # Medical/caregiving keywords to look for
    caregiving_keywords = [
        'cna', 'rna', 'pct', 'lpn', 'rn', 'medtech', 'nurse', 'nursing',
        'caregiver', 'care giver', 'care', 'medical', 'health care',
        'healthcare', 'health assistant', 'certified nursing', 'home health',
        'patient care', 'hospice', 'assisted living', 'memory care'
    ]
    
    # Check job title
    job_title = basic_info.get("job_title_held", "").lower()
    company = basic_info.get("company_name", "").lower()
    
    has_caregiving_title = any(keyword in job_title for keyword in caregiving_keywords)
    has_caregiving_company = any(keyword in company for keyword in caregiving_keywords)
    
    print(f"  Job Title: '{job_title}' -> Caregiving: {has_caregiving_title}")
    print(f"  Company: '{company}' -> Caregiving: {has_caregiving_company}")
    
    # Check years of experience
    years_exp = basic_info.get("years_of_experience", "")
    try:
        years_float = float(years_exp) if years_exp else 0
        has_experience = years_float > 0
        print(f"  Years of Experience: {years_float} -> Has experience: {has_experience}")
    except:
        has_experience = False
        print(f"  Years of Experience: Invalid value '{years_exp}'")
    
    # Check the three critical questions
    caregiving_years_q = 'How many years of professional caregiving experience do you have?'
    certifications_q = 'Do you currently hold any caregiving-related certifications (CNA, PCT, LPN, RN, MedTech, etc.)?'
    description_q = 'Can you briefly describe your previous caregiving roles, including your main responsibilities and the care settings you worked in?'
    
    caregiving_years_ans = answer_info.get(caregiving_years_q, "N/A")
    certifications_ans = answer_info.get(certifications_q, "N/A")
    description_ans = answer_info.get(description_q, "N/A")
    
    # Check if they answered the caregiving experience question with a number
    has_caregiving_years = False
    if caregiving_years_ans != "N/A":
        # Look for numbers in the answer
        numbers = re.findall(r'\d+', caregiving_years_ans)
        if numbers and int(numbers[0]) > 0:
            has_caregiving_years = True
            print(f"  ✓ Caregiving years answer: {caregiving_years_ans}")
    
    # Check certifications
    has_certifications = False
    if certifications_ans != "N/A" and certifications_ans.lower() not in ['no', 'none', 'n/a']:
        # Check if they mentioned any certification keywords
        cert_keywords = ['cna', 'pct', 'lpn', 'rn', 'medtech', 'certified', 'license']
        if any(keyword in certifications_ans.lower() for keyword in cert_keywords):
            has_certifications = True
            print(f"  ✓ Has certifications: {certifications_ans}")
    
    # Check description quality
    has_good_description = False
    if description_ans != "N/A" and len(description_ans) > 20:  # At least 20 characters
        has_good_description = True
        print(f"  ✓ Has description: {description_ans[:50]}...")
    
    # DECISION LOGIC
    # Must have caregiving title/company AND (experience OR certifications OR good description)
    title_check = has_caregiving_title or has_caregiving_company
    experience_check = has_experience or has_caregiving_years
    qualification_check = has_certifications or has_good_description
    
    qualified = title_check and (experience_check or qualification_check)
    
    print(f"\n  DECISION:")
    print(f"    - Caregiving title/company: {title_check}")
    print(f"    - Has experience: {experience_check}")
    print(f"    - Has qualifications: {qualification_check}")
    print(f"    → QUALIFIED: {qualified}\n")
    
    return qualified


def main():
    all_rows = []
    selected_rows = []
    rejected_rows = []
    
    page = 75
    count = 0

    print("Fetching data for page 75...")
    candidates = fetch_page(page)
    print(f"\n✓ Number of candidates fetched: {len(candidates)}\n")

    for c in candidates:
        count += 1
        print(f"\n{'='*70}")
        print(f"CANDIDATE {count}: {c.get('first_name', '')} {c.get('last_name', '')}")
        print(f"{'='*70}")
        # Extract data
        basic_info = extract_basic(c)
        answer_info = extract_answers(c)
        
        # Combine for CSV
        combined = list(basic_info.values()) + list(answer_info.values())
        all_rows.append(combined)
        
        # Filter candidate
        if is_caregiving_qualified(basic_info, answer_info):
            selected_rows.append(combined)
            print(f"  SELECTED")
        else:
            rejected_rows.append(combined)
            print(f"  REJECTED")

    # Write all CSVs
    headers = BASIC_FIELDS + DESIRED_QUESTIONS
    
    print(f"\n{'='*70}")
    print("Writing CSV files...")
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(all_rows)
    print(f"✔ All candidates: {OUTPUT_FILE} ({len(all_rows)} total)")
    
    with open(SELECTED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(selected_rows)
    print(f"✔ Selected: {SELECTED_FILE} ({len(selected_rows)} qualified)")
    
    with open(REJECTED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rejected_rows)
    print(f"✔ Rejected: {REJECTED_FILE} ({len(rejected_rows)} not qualified)")
    
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()