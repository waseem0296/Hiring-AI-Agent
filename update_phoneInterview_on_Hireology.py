
import json
import requests
from typing import Dict, List, Any
from difflib import SequenceMatcher
from interview_id_fetcher import fetch_interview_id
# API Configuration
API_BASE_URL = "https://api.hireology.com/v2"
BEARER_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY2Njk0NTA1LCJuYmYiOjE3NjY2OTA5MDUsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY2NjkwOTA1fQ.YL7wunIIarQkSmcbwIb1OKBN5W9-ltonWTzGhAw4OCCj_njIuK9P6RUnA64L7QOBCrnWlPlgdihREWV76MsP-m18FmAEfFLXYDIPuk38CIh2d6NlfoHUlDgLCWhH6MxWs3mh2p6LdvCCtQmLjm8gf_VeINm7pc_2ShDBk1656FkEI0cj0pzAzz22KgnwRNlF-15Elap5HE_5HTTVzjMfkwigC-HoEyG4GhSi46gvzrtP6hiSwHbFwrYAwtsQVePhs2DBFeBC3O94lfDay-vZg_Wd4-pjyfZV52h1Rj-Plcqv_Nia0y17rbTiqYbboKUDBTfKS2TQDKjc-iPMdoN7wQ"
# Interview identifiers - UPDATE THESE FOR EACH CANDIDATE
JOB_ID = "2606114"
CANDIDATE_ID = "47212392"
# INTERVIEW_ID = "49720606"
BEARER_TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6IlJNblFlZmkwZFB5emRIdFR0Z2xrVmdFWGp0SHFzSEFkb0Jjbi1nMjJJb1UiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY3MzYxODA3LCJuYmYiOjE3NjczNTgyMDcsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsInRpZCI6IjQ2ZTgyZGVhLTkxZjQtNGQzMC1hYWJjLWFjMWVlMDMwYmVjMiIsImttc2kiOiJGYWxzZSIsInNjcCI6InYyIGFpIHYzIiwiYXpwIjoiZjA2N2U2YTMtODE1ZC00MTNkLTg3OGUtZDIyM2VmYWEwY2E0IiwidmVyIjoiMS4wIiwiaWF0IjoxNzY3MzU4MjA3fQ.KTuT1n334_vw4_uMZBEiBDdKcKEZyE0yMpdRVRrQzuKL84gF_7d6t0c-A-dKQp23r6l2FNLvh0PBDNgYX0hxACj-ruhR30b9cNiEyoNUiYQTP6VbKZHg-WsoT_7OjauKcqBTW5M0O7CLV3kBFxekldquMlFio495pvAnucq8vJMdVDoFbp_dCRMWAd-yy8lL0n1j2Blw1O3qOhVNpGXkP2P6DwofjuN3iVOfU7wtUn5rgrxbp0Vy2Wkt7dbmJtdCs9oEchyC8FNDR2J6EyCSu-kabuQV43zVNRU9nhoi2xmTRG8xgYsORYVTtbmgDFHgrG2A375krSM3xFqM0DEdDA"
INTERVIEW_TEMPLATE_ID=512090
# INTERVIEW_ID= fetch_interview_id(
#             jwt=BEARER_TOKEN,
#             job_id=JOB_ID,
#             candidate_id=CANDIDATE_ID,
#             interview_template_id=INTERVIEW_TEMPLATE_ID
#         )
INTERVIEW_ID = None
# Path to QA data - UPDATE THIS
# D:\AI related work\11 Hirology Agent\AI Agent\Hiring AI Agent\call_data\hireology_qa_20251226_003048.json
# LOCAL_JSON_PATH = r"D:\AI related work\\11 Hirology Agent\AI Agent\\Hiring AI Agent\\call_data\\hireology_qa_20251222_231959.json"
LOCAL_JSON_PATH = r"D:\AI related work\\11 Hirology Agent\AI Agent\\Hiring AI Agent\\Hiring AI Agent\\call_data\\hireology_qa_20260102_164522.json"


def map_rating_to_answer(rating: str) -> Dict[str, Any]:
    """Map rating string to Hireology answer format"""
    rating_map = {
        "Excellent": ("Excellent", 5),
        "Great": ("Good", 4),
        "Good": ("Good", 4),
        "Ok": ("Ok", 3),
        "Poor": ("Poor", 0),
        "Skipped": ("Skipped", -1)
    }
    
    normalized_rating = rating.capitalize()
    if normalized_rating == "Great":
        normalized_rating = "Good"
    
    name, score = rating_map.get(normalized_rating, ("Ok", 3))
    return {"name": name, "score": score, "selected": True}


def fuzzy_match_question(qa_question: str, interview_questions: List[Dict]) -> Dict:
    """Find the best matching question from interview using fuzzy matching"""
    best_match = None
    best_score = 0
    
    for question in interview_questions:
        prompt = question.get('prompt', '').lower()
        qa_q = qa_question.lower()
        similarity = SequenceMatcher(None, prompt, qa_q).ratio()
        
        if similarity > best_score:
            best_score = similarity
            best_match = question
    
    return best_match if best_score > 0.5 else None


def update_interview_answers(local_json_path: str, interview_data: Dict) -> tuple:
    """Update interview data with answers from local JSON file"""
    with open(local_json_path, 'r') as f:
        qa_data = json.load(f)
    
    qa_pairs = qa_data.get('qa_pairs', [])
    questions = interview_data.get('questions', [])
    
    update_logs = []
    all_questions_logs = []
    matched_question_ids = set()
    
    # Questions to consolidate into Q11 (Clinical Experience)
    clinical_sub_questions = [
        "Experience using a Hoyer Lift",
        "Experience using a Gait Belt",
        "Experience with Hospice Clients",
        "Experience with a client on Hospice Care",
        "Experience using a Sliding board",
        "Experience with Total Care Clients",
        "Experience giving bed baths",
        "Experience emptying foley catheters"
    ]
    
    # Lists to hold consolidated data
    q11_text_parts = []
    
    print("\n📝 Matching questions with QA data...")
    
    # Update each question with matching answer
    for qa_pair in qa_pairs:
        question_text = qa_pair.get('question', '')
        answer_text = qa_pair.get('answer', 'N/A')
        rating = qa_pair.get('rating', 'Ok')
        
        # Check if this is one of the clinical questions for Q11
        is_clinical = any(sub in question_text for sub in clinical_sub_questions)
        
        if is_clinical:
            # Add to consolidated list
            q11_text_parts.append(f"Q: {question_text}\nA: {answer_text}")
            continue # Skip individual matching for these
        
        # Standard matching for other questions
        matched_question = fuzzy_match_question(question_text, questions)
        
        if matched_question:
             # Special handling for "How did you hear about us?" (Q9)
            if "Reason for Applying" in matched_question.get('prompt', '') or "hear about us" in matched_question.get('prompt', '').lower():
                pass # existing logic continues...
        
        # Fallback for CPR Question (Fuzzy match often fails here due to phrasing diff)
        if not matched_question:
            if "certifications" in question_text.lower() and "cpr" in question_text.lower():
                 for q in questions:
                    if "cpr certified" in q.get('prompt', '').lower():
                        matched_question = q
                        print(f"   ℹ️  Manual Match: CPR Question matched (Fuzzy failed)")
                        break

        if matched_question:
            prompt = matched_question.get('prompt', '')
            # Special handling
            if "Reason for Applying" in prompt or "hear about us" in prompt.lower():
                if answer_text in ['N/A', '', None] or (
                        isinstance(answer_text, str) and not answer_text.strip()
                    ):
                        answer_text = "LinkedIn"
                        print("     Defaulting source to 'LinkedIn'")
                rating = "Good"

            # Generic empty check (after defaulting)
            is_no_answer = answer_text in ['N/A', '', None] or (
                isinstance(answer_text, str) and not answer_text.strip()
            )

            if is_no_answer:
                matched_question['text_answer'] = ''
                rating = 'Skipped'
            else:
                matched_question['text_answer'] = answer_text

            
            # Update rating selection
            rating_info = map_rating_to_answer(rating)
            for answer in matched_question['answers']:
                answer['selected'] = (answer['name'] == rating_info['name'])
            
            # Log
            log_entry = {
                'question': matched_question.get('prompt'),
                'answer': answer_text if not is_no_answer else 'N/A (No answer provided)',
                'rating': rating,
                'question_id': matched_question.get('id'),
                'matched': True,
                'order': matched_question.get('order', 0)
            }
            update_logs.append(log_entry)
            matched_question_ids.add(matched_question.get('id'))
            
            print(f"✓ Q{matched_question.get('order', '?') + 1}: {rating}")
            
    # Handle the Consolidated Q11 Update
    if q11_text_parts:
        # Find Q11 (Clinical Experience) in interview_data
        # It usually starts with "Experience using a Hoyer Lift"
        q11_target = None
        for q in questions:
            if "Hoyer Lift" in q.get('prompt', '') and "Gait Belt" in q.get('prompt', ''):
                q11_target = q
                break
        
        if q11_target:
            combined_text = "\n\n".join(q11_text_parts)
            q11_target['text_answer'] = combined_text
            
            # Force rating to "Excellent"
            rating = "Excellent"
            rating_info = map_rating_to_answer(rating)
            for answer in q11_target['answers']:
                answer['selected'] = (answer['name'] == rating_info['name'])
                
            log_entry = {
                'question': "Clinical Experience (Consolidated Q11)",
                'answer': combined_text,
                'rating': rating,
                'question_id': q11_target.get('id'),
                'matched': True,
                'order': q11_target.get('order', 0)
            }
            update_logs.append(log_entry)
            matched_question_ids.add(q11_target.get('id'))
            print(f"✓ Q{q11_target.get('order', '?') + 1} (Consolidated): {rating} (Hardcoded)")
    
    # Handle unmatched questions
    for question in questions:
        if question.get('id') not in matched_question_ids:
            # Special Handling for Source Question (Q9) if unmatched
            if "hear about us" in question.get('prompt', '').lower():
                print("   ℹ️  Defaulting source to 'Linkedin' (Standard Default)")
                
                # Apply defaults
                existing_answer = "Linkedin"
                selected_answer = "Good"
                
                # Update the question object so it sends correctly
                question['text_answer'] = existing_answer
                
                # Set selection in answers array
                rating_info = map_rating_to_answer(selected_answer)
                for answer in question.get('answers', []):
                    answer['selected'] = (answer['name'] == rating_info['name'])
                
                log_entry = {
                    'question': question.get('prompt'),
                    'answer': existing_answer,
                    'rating': selected_answer,
                    'question_id': question.get('id'),
                    'matched': True, # Mark as matched since we handled it
                    'order': question.get('order', 0)
                }
                # Add to update logs so it counts as "Matched & Updated"
                update_logs.append(log_entry)
                matched_question_ids.add(question.get('id'))
                continue

            # Special Handling for Job Search / Deal Breakers (Q10) if unmatched
            q_prompt = question.get('prompt', '').lower()

            if "job search" in q_prompt and ("important" in q_prompt or "deal-breakers" in q_prompt):
                print("    Handling Job Search / Deal-Breakers (Q10)")

                existing_answer = question.get('text_answer')

                # Apply default ONLY if empty or None
                if existing_answer is None or (
                    isinstance(existing_answer, str) and not existing_answer.strip()
                ):
                    existing_answer = "I look for growth and a healthy work environment."
                    print("   ℹ️  Defaulting Job Search answer")

                question['text_answer'] = existing_answer

                # Rating logic (always Good, or adjust if needed)
                selected_answer = "Good"

                rating_info = map_rating_to_answer(selected_answer)
                for answer in question.get('answers', []):
                    answer['selected'] = (answer['name'] == rating_info['name'])

                log_entry = {
                    'question': question.get('prompt'),
                    'answer': existing_answer,
                    'rating': selected_answer,
                    'question_id': question.get('id'),
                    'matched': True,
                    'order': question.get('order', 0)
                }

                update_logs.append(log_entry)
                matched_question_ids.add(question.get('id'))
                continue

            existing_answer = question.get('text_answer')
            has_no_answer = existing_answer is None or existing_answer == ''
            
            if has_no_answer:
                existing_answer = 'N/A (No answer provided)'
                # Set to Skipped
                for answer in question.get('answers', []):
                    answer['selected'] = (answer['name'] == 'Skipped')
            
            selected_answer = next((ans['name'] for ans in question.get('answers', []) if ans.get('selected')), 'Skipped')
            
            log_entry = {
                'question': question.get('prompt'),
                'answer': existing_answer,
                'rating': selected_answer,
                'question_id': question.get('id'),
                'matched': False,
                'order': question.get('order', 0)
            }
            all_questions_logs.append(log_entry)
    
    # Combine and sort
    all_logs = update_logs + all_questions_logs
    all_logs.sort(key=lambda x: x['order'])
    
    print(f"✓ Matched {len(update_logs)} out of {len(questions)} questions\n")
    
    return interview_data, update_logs, all_logs


def fetch_interview_from_api() -> Dict:
    """Fetch current interview data from Hireology API"""
    url = f"{API_BASE_URL}/jobs/{JOB_ID}/candidates/{CANDIDATE_ID}/interviews/{INTERVIEW_ID}"
    
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {BEARER_TOKEN}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch interview: {response.status_code} - {response.text}")


def display_update_logs(all_logs: List[Dict], matched_count: int):
    """Display detailed logs of ALL questions"""
    print("\n" + "=" * 100)
    print("ALL INTERVIEW QUESTIONS - ANSWERS BEING SENT TO HIREOLOGY")
    print("=" * 100)
    
    for i, log in enumerate(all_logs, 1):
        status = "✓ UPDATED" if log['matched'] else "○ NOT MATCHED (keeping existing)"
        
        print(f"\n{'─' * 100}")
        print(f"Question #{i} (ID: {log['question_id']}) - {status}")
        print(f"{'─' * 100}")
        print(f"\n📋 QUESTION:")
        print(f"   {log['question']}")
        print(f"\n💬 ANSWER:")
        
        answer_text = log['answer']
        if answer_text is None or answer_text == '':
            answer_text = "N/A (No answer provided)"
        
        # Word wrap
        if len(answer_text) > 90:
            words = answer_text.split()
            lines = []
            current_line = "   "
            for word in words:
                if len(current_line) + len(word) + 1 <= 93:
                    current_line += word + " "
                else:
                    lines.append(current_line.rstrip())
                    current_line = "   " + word + " "
            lines.append(current_line.rstrip())
            print("\n".join(lines))
        else:
            print(f"   {answer_text}")
        
        rating_text = log['rating'] if log['rating'] else "N/A"
        print(f"\n⭐ RATING:")
        print(f"   {rating_text}")
    
    print(f"\n{'=' * 100}")
    print(f"SUMMARY:")
    print(f"  Total Questions: {len(all_logs)}")
    print(f"  Matched & Updated: {matched_count}")
    print(f"  Not Matched: {len(all_logs) - matched_count}")
    print(f"{'=' * 100}\n")


def send_update_to_hireology(interview_data: Dict) -> requests.Response:
    """Send PUT request to update interview answers"""
    url = f"{API_BASE_URL}/jobs/{JOB_ID}/candidates/{CANDIDATE_ID}/interviews/{INTERVIEW_ID}"
    
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Build the answers dictionary
    answers_dict = {}
    
    for question in interview_data['questions']:
        question_id = str(question['id'])
        text_answer = question.get('text_answer', '')
        
        # Get the selected answer's score
        answer_score = 0
        for answer in question.get('answers', []):
            if answer.get('selected', False):
                answer_score = answer.get('score', 0)
                break
        
        answers_dict[question_id] = {
            "notes": text_answer,
            "answer_score": answer_score
        }
    
    # Calculate total score for display
    total_score = sum(ans['answer_score'] for ans in answers_dict.values())
    
    # Build payload
    payload = {
        "updates": {
            "interview": {
                "progress": "completed"
            },
            "answers": answers_dict
        }
    }
    
    print(f"   📤 Sending {len(answers_dict)} answers to API...")
    print(f"   📊 Calculated Total Score: {total_score}")
    print(f"   🎯 Setting progress to: completed")
    
    response = requests.put(url, headers=headers, json=payload)
    return response


def trigger_score_calculation() -> requests.Response:
    """
    Call the /score endpoint to trigger score calculation
    This is what happens when you manually click 'Finish Interview'
    """
    url = f"{API_BASE_URL}/jobs/{JOB_ID}/candidates/{CANDIDATE_ID}/interviews/{INTERVIEW_ID}/score"
    
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {BEARER_TOKEN}",
        "content-length": "0"
    }
    
    print(f"\n   🧮 Triggering score calculation...")
    response = requests.post(url, headers=headers)
    return response


def main():
    print("=" * 70)
    print("Hireology Interview Answer Update Script")
    print("=" * 70)
    
    # Step 1: Fetch interview
    print(f"\n1. Fetching interview data from Hireology API...")
    print(f"   Job ID: {JOB_ID}")
    print(f"   Candidate ID: {CANDIDATE_ID}")
    print(f"   Interview ID: {INTERVIEW_ID}")
    
    try:
        interview_data = fetch_interview_from_api()
        print(f"   ✓ Fetched interview with {len(interview_data.get('questions', []))} questions")
        print("The feched questions from Hireology is:",interview_data)
    except Exception as e:
        print(f"   ✗ Error fetching interview: {str(e)}")
        print(f"\n   Possible issues:")
        print(f"   - Bearer token may have expired")
        print(f"   - Check Job ID, Candidate ID, or Interview ID")
        return
    
    # Step 2: Load and match QA data
    print(f"\n2. Loading QA data from local file...")
    print(f"   Path: {LOCAL_JSON_PATH}")
    
    try:
        updated_interview, update_logs, all_logs = update_interview_answers(LOCAL_JSON_PATH, interview_data)
        print(f"   ✓ QA data processed")
    except FileNotFoundError:
        print(f"   ✗ Error: Could not find {LOCAL_JSON_PATH}")
        return
    except Exception as e:
        print(f"   ✗ Error processing QA data: {str(e)}")
        return
    
    # Step 3: Display logs
    if all_logs:
        display_update_logs(all_logs, len(update_logs))
    
    # Step 4: Send update to API
    print(f"\n3. Sending update to Hireology API...")
    
    try:
        response = send_update_to_hireology(updated_interview)
        
        if response.status_code == 200:
            print(f"   ✓ Successfully updated interview!")
            resp_data = response.json()
            print(f"\n   📊 INITIAL RESPONSE:")
            print(f"      Score: {resp_data.get('score', 'N/A')} (not calculated yet)")
            print(f"      Progress: {resp_data.get('progress', 'N/A')}")
            
        elif response.status_code == 204:
            print(f"   ✓ Successfully updated interview (no content returned)")
        else:
            print(f"   ✗ Failed to update interview")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except Exception as e:
        print(f"   ✗ Error making API request: {str(e)}")
        return
    
    # Step 5: Trigger score calculation (NEW!)
    print(f"\n4. Calculating final score...")
    
    try:
        score_response = trigger_score_calculation()
        
        if score_response.status_code == 200:
            score_data = score_response.json()
            print(f"   ✓ Score calculated successfully!")
            print(f"\n   📊 FINAL INTERVIEW STATUS:")
            print(f"      Score: {score_data.get('score', 'N/A')}")
            print(f"      Confidence Score: {score_data.get('confidence_score', 'N/A')}")
            print(f"      Progress: {score_data.get('progress', 'N/A')}")
            
            # Show the full response for debugging
            print(f"\n   📋 Complete Response:")
            print(f"      {json.dumps(score_data, indent=2)}")
            
        elif score_response.status_code == 204:
            print(f"   ✓ Score calculation triggered (no content returned)")
            print(f"   ℹ️  Score should now be visible in Hireology")
        else:
            print(f"   ⚠️  Score calculation returned: {score_response.status_code}")
            print(f"   Response: {score_response.text}")
            
    except Exception as e:
        print(f"   ✗ Error triggering score calculation: {str(e)}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()