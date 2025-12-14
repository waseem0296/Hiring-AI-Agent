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
START_PAGE = 70  # Start from page 70

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
    "job_id",
    # "job_title",
    "status",
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

def extract_answers(app_form_data):
    """
    Extract custom question answers from a specific application form data entry.
    """
    answers = {q: "N/A" for q in DESIRED_QUESTIONS}
    
    form = app_form_data.get("application_form_data", {})
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


def extract_basic(c, app_form_data):
    """
    Extract basic candidate information including job_id, job_title, and status.
    """
    profile = {}
    hr = {}
    work = {}
    
    app_form = app_form_data.get("application_form_data", {})
    
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
        "job_id": app_form_data.get("job_id", ""),
        # "job_title": app_form_data.get("job_title", "N/A"),  # Will need to fetch separately
        "status": app_form_data.get("status", ""),
        "years_of_experience": profile.get("years_of_experience", ""),
        "work_permit_in_us": profile.get("work_permit_in_us", ""),
        "desired_compensation_hourly": hr.get("candidate.desired_compensation.hourly", ""),
        "company_name": work.get("company_name", ""),
        "job_title_held": work.get("job_title_held", ""),
        "start_date": work.get("start_date", ""),
        "end_date": work.get("end_date", ""),
    }


def evaluate_candidate(basic_info, answer_info):
    """
    Evaluate candidate based on enhanced criteria.
    Returns: (is_selected: bool, comment: str)
    """
    rejection_reasons = []
    positive_points = []
    
    # Medical/caregiving keywords
    caregiving_keywords = [
        'cna', 'rna', 'pct', 'lpn', 'rn', 'medtech', 'nurse', 'nursing',
        'caregiver', 'care giver', 'care', 'medical', 'health care',
        'healthcare', 'health assistant', 'certified nursing', 'home health',
        'patient care', 'hospice', 'assisted living', 'memory care'
    ]
    
    # Get answers
    arrested_q = 'Have you been arrested, convicted of a felony, or misdemeanor? '
    drug_screen_q = 'Are you able to pass a drug screen? '
    driver_license_q = "Do you have a valid driver's license, and car insurance?"
    caregiving_years_q = 'How many years of professional caregiving experience do you have?'
    certifications_q = 'Do you currently hold any caregiving-related certifications (CNA, PCT, LPN, RN, MedTech, etc.)?'
    description_q = 'Can you briefly describe your previous caregiving roles, including your main responsibilities and the care settings you worked in?'
    
    arrested_ans = answer_info.get(arrested_q, "N/A").lower()
    drug_screen_ans = answer_info.get(drug_screen_q, "N/A").lower()
    driver_license_ans = answer_info.get(driver_license_q, "N/A").lower()
    caregiving_years_ans = answer_info.get(caregiving_years_q, "N/A")
    certifications_ans = answer_info.get(certifications_q, "N/A")
    description_ans = answer_info.get(description_q, "N/A")
    
    # Check legal right to work
    work_permit = str(basic_info.get("work_permit_in_us", "")).lower()
    if work_permit in ['no', 'false', '0'] and work_permit != "":
        rejection_reasons.append("No legal right to work in US")
    
    # Check arrested/conviction
    if 'yes' in arrested_ans and arrested_ans != "n/a":
        rejection_reasons.append("Has arrest/conviction record")
    
    # Check drug screen
    if 'no' in drug_screen_ans and drug_screen_ans != "n/a":
        rejection_reasons.append("Cannot pass drug screen")
    
    # Check driver's license
    if 'no' in driver_license_ans and driver_license_ans != "n/a":
        rejection_reasons.append("No valid driver's license or car insurance")
    
    # Check caregiving experience
    has_caregiving_experience = False
    
    # Check years of experience from basic info
    years_exp = basic_info.get("years_of_experience", "")
    try:
        years_float = float(years_exp) if years_exp else 0
        if years_float > 0:
            has_caregiving_experience = True
            positive_points.append(f"{years_float} years of experience")
    except:
        pass
    
    # Check caregiving years answer
    if caregiving_years_ans != "N/A":
        numbers = re.findall(r'\d+', caregiving_years_ans)
        if numbers and int(numbers[0]) > 0:
            has_caregiving_experience = True
            positive_points.append(f"{caregiving_years_ans} caregiving experience")
        elif 'no' in caregiving_years_ans.lower() or '0' in caregiving_years_ans:
            rejection_reasons.append("No professional caregiving experience")
    
    # Check job title for caregiving background
    job_title = basic_info.get("job_title_held", "").lower()
    company = basic_info.get("company_name", "").lower()
    
    has_caregiving_title = any(keyword in job_title for keyword in caregiving_keywords)
    has_caregiving_company = any(keyword in company for keyword in caregiving_keywords)
    
    if has_caregiving_title:
        positive_points.append(f"Caregiving job title: {basic_info.get('job_title_held', '')}")
    if has_caregiving_company:
        positive_points.append(f"Caregiving company: {basic_info.get('company_name', '')}")
    
    # Check certifications
    has_certifications = False
    if certifications_ans != "N/A" and certifications_ans.lower() not in ['no', 'none', 'n/a']:
        cert_keywords = ['cna', 'pct', 'lpn', 'rn', 'medtech', 'certified', 'license']
        if any(keyword in certifications_ans.lower() for keyword in cert_keywords):
            has_certifications = True
            positive_points.append(f"Certifications: {certifications_ans}")
    
    # Check description
    has_good_description = False
    if description_ans != "N/A" and len(description_ans) > 20:
        has_good_description = True
        positive_points.append(f"Detailed caregiving description provided")
    
    # If no caregiving experience at all
    if not has_caregiving_experience and caregiving_years_ans.lower() in ['no', 'none', '0', 'n/a']:
        rejection_reasons.append("No caregiving experience")
    
    # If no caregiving background at all
    if not (has_caregiving_title or has_caregiving_company or has_certifications or has_good_description):
        rejection_reasons.append("No caregiving background or qualifications")
    
    # Decision logic
    if rejection_reasons:
        is_selected = False
        comment = "REJECTED - " + "; ".join(rejection_reasons)
    else:
        is_selected = True
        comment = "SELECTED - " + "; ".join(positive_points) if positive_points else "SELECTED - Meets basic qualifications"
    
    return is_selected, comment


def main():
    all_rows = []
    selected_rows = []
    rejected_rows = []
    
    page = START_PAGE
    total_candidates = 0
    total_applicants = 0
    
    print(f"\n{'='*70}")
    print(f"Starting to fetch candidates from page {START_PAGE}...")
    print(f"{'='*70}\n")

    while True:
        print(f"\n{'='*70}")
        print(f"FETCHING PAGE {page}")
        print(f"{'='*70}")
        
        candidates = fetch_page(page)
        
        if not candidates:
            print(f"\nNo more candidates found. Stopping at page {page}.")
            break
        
        print(f"✓ Number of candidates fetched: {len(candidates)}\n")
        total_candidates += len(candidates)
        
        for c in candidates:
            # Get all application form data entries
            app_data_list = c.get("application_form_data", [])
            
            if not app_data_list:
                continue
            
            # Process each job application separately
            for app_data in app_data_list:
                status = app_data.get("status", "").lower()
                
                # Filter only 'Applicant' status
                if status != "applicant":
                    continue
                
                total_applicants += 1
                
                print(f"\n{'='*70}")
                print(f"CANDIDATE {total_applicants}: {c.get('first_name', '')} {c.get('last_name', '')}")
                print(f"Job ID: {app_data.get('job_id', 'N/A')}, Status: {app_data.get('status', 'N/A')}")
                print(f"{'='*70}")
                
                # Extract data for this specific job application
                basic_info = extract_basic(c, app_data)
                answer_info = extract_answers(app_data)
                
                # Evaluate candidate
                is_selected, comment = evaluate_candidate(basic_info, answer_info)
                
                # Combine for CSV (add comment at the end)
                combined = list(basic_info.values()) + list(answer_info.values()) + [comment]
                all_rows.append(combined)
                
                if is_selected:
                    selected_rows.append(combined)
                    print(f"✓ SELECTED")
                else:
                    rejected_rows.append(combined)
                    print(f"✗ REJECTED")
                
                print(f"Comment: {comment}")
        
        # Move to next page
        page += 1
        
        # Safety check to prevent infinite loops
        if page > 200:  # Adjust this limit as needed
            print("\nReached maximum page limit (200). Stopping.")
            break

    # Write all CSVs
    headers = BASIC_FIELDS + DESIRED_QUESTIONS + ["Comment"]
    
    print(f"\n{'='*70}")
    print("Writing CSV files...")
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(all_rows)
    print(f"✔ All applicants: {OUTPUT_FILE} ({len(all_rows)} total)")
    
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
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total candidates processed: {total_candidates}")
    print(f"Total applicants (status='Applicant'): {total_applicants}")
    print(f"Selected: {len(selected_rows)}")
    print(f"Rejected: {len(rejected_rows)}")
    print(f"Pages processed: {START_PAGE} to {page-1}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()