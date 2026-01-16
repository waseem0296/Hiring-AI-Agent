
# formate_most_recent_callTranscript_to_Structured_json.py
import requests
import json
from datetime import datetime
import os
import re
from difflib import SequenceMatcher
from dotenv import load_dotenv
load_dotenv()

class HireologyQAExtractor:
    def __init__(self, api_key, location_id, groq_api_key=None):
        self.api_key = api_key
        self.location_id = location_id
        self.groq_api_key = groq_api_key
        self.base_url = "https://services.leadconnectorhq.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
        
        self.hireology_questions = [
            "Can you tell me a little about your background and experience in care professionals?",
            "What motivated you to become a care professional?",
            "Do you have any certifications or specialized training related to caregiving? (CNA, MA, CPR, etc.)",
            "Can you name a few caregiving tasks you have experience in?",
            "Do you have experience with tasks such as bathing, dressing, and toileting clients?",
            "Do you have another job? What's your availability?",
            "How flexible is your schedule, and are you available for overnight or weekend shifts if needed?",
            "Do you have reliable transportation to get to clients' homes? Is this your own vehicle?",
            "Why do you want to work for our home care agency specifically?",
            "Experience using a Hoyer Lift or Stand Assist? (Manual or Electric)",
            "Experience using a Gait Belt?",
            "Experience with Hospice Clients",
            "Experience with a client on Hospice Care who is Transitioning",
            "Experience using a Sliding board?",
            "Experience with Total Care Clients and/or bedridden clients?",
            "Experience giving bed baths, changing the client in bed, turning, repositioning, and changing sheets of a bedridden client?",
            "Experience emptying foley catheters and male condom catheters?",
            "How did you hear about us?",
            "As you go through your job search, what things do you consider to be most important? What are some deal-breakers?"
        ]
    
    def get_call_logs(self, agent_id=None):
        """Retrieve call logs from Voice AI"""
        url = f"{self.base_url}/voice-ai/dashboard/call-logs"
        params = {"locationId": self.location_id}
        if agent_id:
            params["agentId"] = agent_id
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching call logs: {e}")
            return None
    
    # def parse_transcript_to_dict(self, transcript):
    #     """
    #     Parse transcript into a dictionary of questions and answers.
    #     Robustly handles:
    #     - Merged questions (e.g. "Do you have X? [no pause] Can you do Y?")
    #     - Interrupted questions (no '?' before human answers)
    #     - Multi-turn answers
    #     - Lines missing 'bot:' or 'human:' prefixes (assumed continuation)
    #     """
    #     lines = transcript.split('\n')
    #     qa_dict = {}
    #     last_question = None
    #     last_speaker = None  # 'bot' or 'human'
        
    #     # Buffer for current bot output that hasn't been finalized into a question yet
    #     current_bot_buffer = ""
        
    #     # Phrases that clearly indicate a NEW question starting
    #     # Used to force-split if multiple questions are glued together
    #     question_starters = [
    #         "can you", "do you", "what", "how", "why", "are you", "is there", 
    #         "tell me", "have you"
    #     ]
        
    #     # Ignore short filler phrases if they end up as standalone "questions"
    #     ignore_phrases = [
    #         "thank you", "got it", "great", "ok", "alright", "hello", "hi", 
    #         "ready to begin", "let's get started", "call is recorded"
    #     ]
        
    #     for line in lines:
    #         line = line.strip()
    #         if not line: continue
            
    #         # Determine speaker and text
    #         if line.startswith('bot:'):
    #             speaker = 'bot'
    #             text = line[4:].strip()
    #         elif line.startswith('human:'):
    #             speaker = 'human'
    #             text = line[6:].strip()
    #         else:
    #             # No prefix - assume continuation of last speaker
    #             # If no last speaker (start of file), skip or assume bot?
    #             if last_speaker:
    #                 speaker = last_speaker
    #                 text = line
    #             else:
    #                 continue
            
    #         last_speaker = speaker
            
    #         if speaker == 'bot':
    #             text_lower = text.lower()
                
    #             # Check for FORCE SPLIT: 
    #             # If we already have significant text in buffer, and this new line 
    #             # starts with a capitalized Question Starter, assume previous question ended.
    #             is_new_start = any(text_lower.startswith(s) for s in question_starters)
                
    #             # If buffer has "Do you have certifications" and new line is "Can you name...", split!
    #             if current_bot_buffer and is_new_start and len(current_bot_buffer) > 10:
    #                  q_text = current_bot_buffer.strip()
    #                  # Only register as question if it's not just "Thank you"
    #                  if not any(q_text.lower() == p for p in ignore_phrases):
    #                      if q_text not in qa_dict:
    #                          qa_dict[q_text] = ""
    #                      last_question = q_text
    #                  current_bot_buffer = ""
                
    #             current_bot_buffer += " " + text
                
    #             # Now check for standard '?' splits
    #             if '?' in current_bot_buffer:
    #                 parts = current_bot_buffer.split('?')
                    
    #                 # Process all complete segments
    #                 for i in range(len(parts) - 1):
    #                     q_candidate = parts[i].strip() + '?'
                        
    #                     # Filter out pure filler "questions" like "Ready to begin?" if strictly filler
    #                     q_clean = q_candidate.lower().strip()
    #                     is_filler = any(phrase in q_clean for phrase in ignore_phrases) and len(q_clean) < 20
                        
    #                     if len(q_candidate) > 5 and not is_filler:
    #                          if q_candidate not in qa_dict:
    #                              qa_dict[q_candidate] = ""
    #                          last_question = q_candidate
                    
    #                 # The remainder stays in buffer (start of next sentence)
    #                 current_bot_buffer = parts[-1]
            
    #         elif speaker == 'human':
    #             ans = text
    #             if not ans: continue
                
    #             # CRITICAL FIX: If human answers and we have a "pending" bot buffer 
    #             # that hasn't been finalized (e.g. "Do you have certifications" with no '?'),
    #             # treat that buffer as the question IMMEDIATELY.
    #             if current_bot_buffer.strip() and len(current_bot_buffer) > 10:
    #                 q_candidate = current_bot_buffer.strip()
    #                 # Check if it looks like a question (contains question words) or is long enough
    #                 has_q_word = any(w in q_candidate.lower() for w in question_starters)
                    
    #                 if has_q_word or len(q_candidate) > 20: 
    #                     if q_candidate not in qa_dict:
    #                         qa_dict[q_candidate] = ""
    #                     last_question = q_candidate
    #                     current_bot_buffer = "" # Consumed
                
    #             # Attach answer to the most recent identified question
    #             if last_question:
    #                 # Ignore "inaudible speech" if we already have an answer
    #                 # But don't ignore it if it's the ONLY answer
    #                 is_inaudible = ans.lower() == "(inaudible speech)"
    #                 if is_inaudible and qa_dict[last_question]:
    #                     continue
                        
    #                 if qa_dict[last_question]:
    #                     qa_dict[last_question] += " " + ans
    #                 else:
    #                     qa_dict[last_question] = ans
        
    #     # Final cleanup: Remove purely empty questions or distinct non-questions
    #     final_dict = {}
    #     for q, a in qa_dict.items():
    #         # Check if q is just filler text
    #         q_lower = q.lower()
    #         is_filler = any(q_lower == p or q_lower == p+"." for p in ignore_phrases)
    #         if not is_filler and len(q) > 5:
    #             # Clean up the key string
    #             final_dict[q] = a.strip()
                
    #     return final_dict
    

    def parse_transcript_to_dict(self, transcript):
        """
        Parse transcript into a dictionary of questions and answers.
        Robustly handles:
        - Merged questions (e.g. "Do you have X? [no pause] Can you do Y?")
        - Interrupted questions (no '?' before human answers)
        - Multi-turn answers
        - Lines missing 'bot:' or 'human:' prefixes (assumed continuation)
        - Human requests to repeat questions (filters out and waits for actual answer)
        """
        lines = transcript.split('\n')
        qa_dict = {}
        last_question = None
        last_speaker = None  # 'bot' or 'human'
        
        # Buffer for current bot output that hasn't been finalized into a question yet
        current_bot_buffer = ""
        
        # Phrases that clearly indicate a NEW question starting
        # Used to force-split if multiple questions are glued together
        question_starters = [
            "can you", "do you", "what", "how", "why", "are you", "is there",
            "tell me", "have you"
        ]
        
        # Ignore short filler phrases if they end up as standalone "questions"
        ignore_phrases = [
            "thank you", "got it", "great", "ok", "alright", "hello", "hi",
            "ready to begin", "let's get started", "call is recorded"
        ]
        
        # NEW: Phrases indicating human is asking to repeat the question
        repeat_request_phrases = [
            "can you repeat", "please repeat", "repeat the question", 
            "say that again", "could you repeat", "what was the question",
            "come again", "pardon", "sorry", "what did you say"
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Determine speaker and text
            if line.startswith('bot:'):
                speaker = 'bot'
                text = line[4:].strip()
            elif line.startswith('human:'):
                speaker = 'human'
                text = line[6:].strip()
            else:
                # No prefix - assume continuation of last speaker
                # If no last speaker (start of file), skip or assume bot?
                if last_speaker:
                    speaker = last_speaker
                    text = line
                else:
                    continue
            
            last_speaker = speaker
            
            if speaker == 'bot':
                text_lower = text.lower()
                
                # Check for FORCE SPLIT:
                # If we already have significant text in buffer, and this new line
                # starts with a capitalized Question Starter, assume previous question ended.
                is_new_start = any(text_lower.startswith(s) for s in question_starters)
                
                # If buffer has "Do you have certifications" and new line is "Can you name...", split!
                if current_bot_buffer and is_new_start and len(current_bot_buffer) > 10:
                    q_text = current_bot_buffer.strip()
                    # Only register as question if it's not just "Thank you"
                    if not any(q_text.lower() == p for p in ignore_phrases):
                        if q_text not in qa_dict:
                            qa_dict[q_text] = ""
                        last_question = q_text
                    current_bot_buffer = ""
                
                current_bot_buffer += " " + text
                
                # Now check for standard '?' splits
                if '?' in current_bot_buffer:
                    parts = current_bot_buffer.split('?')
                    # Process all complete segments
                    for i in range(len(parts) - 1):
                        q_candidate = parts[i].strip() + '?'
                        # Filter out pure filler "questions" like "Ready to begin?" if strictly filler
                        q_clean = q_candidate.lower().strip()
                        is_filler = any(phrase in q_clean for phrase in ignore_phrases) and len(q_clean) < 20
                        
                        if len(q_candidate) > 5 and not is_filler:
                            if q_candidate not in qa_dict:
                                qa_dict[q_candidate] = ""
                            # ALWAYS update last_question, even if question already exists
                            # This ensures answers are captured when bot repeats a question
                            last_question = q_candidate
                    
                    # The remainder stays in buffer (start of next sentence)
                    current_bot_buffer = parts[-1]
            
            elif speaker == 'human':
                ans = text
                if not ans:
                    continue
                
                # NEW: Check if human is asking to repeat the question
                ans_lower = ans.lower()
                is_repeat_request = any(phrase in ans_lower for phrase in repeat_request_phrases)
                
                # If it's a repeat request, skip adding it to the answer
                if is_repeat_request:
                    continue
                
                # CRITICAL FIX: If human answers and we have a "pending" bot buffer
                # that hasn't been finalized (e.g. "Do you have certifications" with no '?'),
                # treat that buffer as the question IMMEDIATELY.
                if current_bot_buffer.strip() and len(current_bot_buffer) > 10:
                    q_candidate = current_bot_buffer.strip()
                    # Check if it looks like a question (contains question words) or is long enough
                    has_q_word = any(w in q_candidate.lower() for w in question_starters)
                    if has_q_word or len(q_candidate) > 20:
                        if q_candidate not in qa_dict:
                            qa_dict[q_candidate] = ""
                        last_question = q_candidate
                        current_bot_buffer = ""  # Consumed
                
                # Attach answer to the most recent identified question
                if last_question:
                    # Ignore "inaudible speech" if we already have an answer
                    # But don't ignore it if it's the ONLY answer
                    is_inaudible = ans.lower() == "(inaudible speech)"
                    if is_inaudible and qa_dict[last_question]:
                        continue
                    
                    if qa_dict[last_question]:
                        qa_dict[last_question] += " " + ans
                    else:
                        qa_dict[last_question] = ans
        
        # Final cleanup: Remove purely empty questions or distinct non-questions
        # AND merge similar questions (when bot repeats with slightly different wording)
        # AND merge follow-up fragments (when bot splits one question into multiple parts)
        final_dict = {}
        
        # First pass: collect all valid questions
        valid_questions = []
        for q, a in qa_dict.items():
            q_lower = q.lower()
            is_filler = any(q_lower == p or q_lower == p+"." for p in ignore_phrases)
            if not is_filler and len(q) > 5:
                valid_questions.append((q, a.strip()))
        
        # Define patterns for follow-up question fragments
        # These are short questions that are typically part of a larger question
        follow_up_patterns = [
            "deal-breaker",  # Will match "deal-breakers" too
            "dealbreaker",
            "is this your own vehicle",
            "what's your availability",
            "what is your availability"
        ]
        
        # Second pass: merge follow-up fragments with previous questions
        # Also merge similar questions (when bot repeats after "can you repeat?")
        
        # Phase 1: Identify all follow-up fragment merges to perform
        fragment_merges = {}  # Maps fragment index to main question index
        
        for i, (q1, a1) in enumerate(valid_questions):
            q1_lower = q1.lower()
            
            # Check if this is a follow-up fragment that should be merged
            is_follow_up = any(pattern in q1_lower for pattern in follow_up_patterns)
            
            if is_follow_up and len(q1) < 50:  # Only short follow-up questions
                # Look for a related main question
                for j, (q2, a2) in enumerate(valid_questions):
                    if j == i:
                        continue
                    
                    q2_lower = q2.lower()
                    
                    # Check if they are related
                    related = False
                    if ("deal-breaker" in q1_lower or "dealbreaker" in q1_lower) and \
                       ("job search" in q2_lower or "most important" in q2_lower):
                        related = True
                    elif "vehicle" in q1_lower and "transportation" in q2_lower:
                        related = True
                    elif "availability" in q1_lower and ("another job" in q2_lower or "current" in q2_lower):
                        related = True
                    
                    if related:
                        fragment_merges[i] = j
                        break
        
        # Phase 2: Apply fragment merges
        used_indices = set(fragment_merges.keys())  # Fragments are consumed
        
        for frag_idx, main_idx in fragment_merges.items():
            frag_q, frag_a = valid_questions[frag_idx]
            main_q, main_a = valid_questions[main_idx]
            
            # Combine questions and answers - prefer the fragment's answer if main has none
            combined_question = main_q + " " + frag_q
            if frag_a and not main_a:
                combined_answer = frag_a
            elif main_a and not frag_a:
                combined_answer = main_a
            elif frag_a and main_a:
                combined_answer = (main_a + " " + frag_a).strip()
            else:
                combined_answer = ""
            
            # Update the main question's entry
            valid_questions[main_idx] = (combined_question, combined_answer)
        
        # Phase 3: Build final dict with similarity-based merges
        final_dict = {}
        
        for i, (q1, a1) in enumerate(valid_questions):
            if i in used_indices:
                continue
            
            best_question = q1
            best_answer = a1
            
            # Check for similar questions (existing logic)
            for j, (q2, a2) in enumerate(valid_questions):
                if i == j or j in used_indices:
                    continue
                
                # Calculate similarity between questions
                similarity = SequenceMatcher(None, q1.lower(), q2.lower()).ratio()
                
                # If very similar (>85%), merge them
                if similarity > 0.85:
                    used_indices.add(j)
                    # Prefer the question/answer pair that has an actual answer
                    if a2 and not best_answer:
                        best_answer = a2
                        best_question = q2  # Use the repeated question text
                    elif a2 and best_answer:
                        # Both have answers, concatenate if different
                        if a2 not in best_answer:
                            best_answer = best_answer + " " + a2
            
            final_dict[best_question] = best_answer
            used_indices.add(i)
        
        return final_dict 
    def calculate_similarity(self, str1, str2):
        """Calculate similarity ratio between two strings (0-1)"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def extract_key_concepts(self, question):
        """Extract important keywords from a question"""
        # Remove common words
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'you', 'your', 
                     'have', 'has', 'do', 'does', 'can', 'could', 'would', 'should',
                     'to', 'for', 'of', 'in', 'on', 'at', 'with', 'and', 'or', 'but'}
        
        words = re.findall(r'\b\w+\b', question.lower())
        key_words = [w for w in words if w not in stop_words and len(w) > 2]
        return set(key_words)
    
    def smart_question_match(self, asked_question, hireology_question, threshold=0.45):
        """
        Advanced matching using multiple strategies:
        1. Direct text similarity (SequenceMatcher)
        2. Key concept overlap
        3. Specific keyword matching
        """
        # Normalize questions - remove common prefixes/filler words
        normalize_patterns = [
            r'^(thank you!?|thanks!?|got it,?|great!?|alright,?)\s*',
            r'^(thank you for.*?\.|got it, thank you!?)\s*',
        ]
        asked_clean = asked_question.lower().strip()
        for pattern in normalize_patterns:
            asked_clean = re.sub(pattern, '', asked_clean, flags=re.IGNORECASE).strip()
        
        hireology_clean = hireology_question.lower().strip()
        
        # Strategy 1: Direct similarity
        direct_similarity = self.calculate_similarity(asked_clean, hireology_clean)
        
        # Strategy 1b: Check if one contains the other (substring match)
        substring_bonus = 0
        if hireology_clean in asked_clean or asked_clean in hireology_clean:
            substring_bonus = 0.3
        
        # Strategy 2: Key concept overlap
        asked_concepts = self.extract_key_concepts(asked_clean)
        hireology_concepts = self.extract_key_concepts(hireology_clean)
        
        if len(hireology_concepts) > 0:
            concept_overlap = len(asked_concepts & hireology_concepts) / len(hireology_concepts)
        else:
            concept_overlap = 0
        
        # Strategy 3: Specific keyword matching for important terms
        asked_lower = asked_clean
        hireology_lower = hireology_clean
        
        # Define specific matching patterns
        specific_matches = 0
        specific_checks = 0
        
        patterns = {
            'background': ['background', 'experience', 'tell me about', 'care professional'],
            'motivated': ['motivated', 'why', 'what made you', 'become a care'],
            'certification': ['certification', 'certified', 'training', 'cna', 'cpr', 'license', 'specialized'],
            'caregiving tasks': ['caregiving', 'tasks', 'duties', 'responsibilities', 'name a few'],
            'bathing': ['bathing', 'dressing', 'toileting', 'grooming', 'hygiene'],
            'availability': ['availability', 'available', 'schedule', 'hours', 'another job'],
            'flexible': ['flexible', 'flexibility', 'overnight', 'weekend', 'shift'],
            'transportation': ['transportation', 'transport', 'vehicle', 'car', 'drive', 'reliable'],
            'why work': ['why', 'what interests', 'what attracted', 'agency', 'company', 'specifically'],
            'hoyer': ['hoyer', 'lift', 'stand assist', 'mechanical lift'],
            'gait belt': ['gait', 'belt', 'transfer belt'],
            'hospice': ['hospice', 'end of life', 'palliative'],
            'transition': ['transition', 'transitioning', 'passing', 'end stage'],
            'sliding board': ['sliding board', 'transfer board', 'slide board'],
            'total care': ['total care', 'bedridden', 'bed bound', 'non-ambulatory'],
            'bed bath': ['bed bath', 'bath in bed', 'changing sheets', 'turning', 'repositioning'],
            'catheter': ['catheter', 'foley', 'urinary', 'condom catheter', 'emptying']
        }
        
        for category, keywords in patterns.items():
            if any(kw in hireology_lower for kw in keywords):
                specific_checks += 1
                if any(kw in asked_lower for kw in keywords):
                    specific_matches += 1
        
        keyword_match_ratio = specific_matches / specific_checks if specific_checks > 0 else 0
        
        # Combine all strategies with weights
        final_score = (
            direct_similarity * 0.35 +        # 35% weight on direct similarity
            concept_overlap * 0.25 +          # 25% weight on concept overlap
            keyword_match_ratio * 0.30 +      # 30% weight on specific keywords
            substring_bonus * 0.10            # 10% bonus for substring match
        )
        
        # Debug output for close matches
        if final_score > 0.35:
            print(f"  [MATCH] Score: {final_score:.2f} | Direct: {direct_similarity:.2f} | Concepts: {concept_overlap:.2f} | Keywords: {keyword_match_ratio:.2f}")
            print(f"     Asked: {asked_question[:80]}...")
            print(f"     Target: {hireology_question[:80]}...")
        
        return final_score >= threshold
    
    def rate_with_groq(self, question, answer):
        """Use Groq AI with more generous rating criteria"""
        if not self.groq_api_key:
            return None
        
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""You are evaluating a caregiver interview answer. Be VERY GENEROUS with ratings.

Question: {question}

Candidate's Answer: {answer}

Rate as: Poor, Ok, Good, or Excellent

**RATING GUIDELINES (BE VERY GENEROUS):**
- **Excellent**: 
  - ANY affirmative answer to experience questions ("Yes", "Yes I have", "Of course", "I do")
  - ANY certification mentioned (CNA, CPR, MA, etc.)
  - ANY experience mentioned (years, previous jobs, specific tasks)
  - Confirms having relevant skills or equipment experience
  
- **Good**: 
  - Partial experience or willingness to learn
  - Brief but relevant answers
  - Mentions availability or schedule flexibility
  
- **Ok**: 
  - "No" to a specific experience question (honest answer is still Ok)
  - Very minimal response that's still on-topic
  
- **Poor**: ONLY if completely irrelevant, rude, or refuses entirely

**IMPORTANT RULES:**
1. "Yes", "Yes I have", "Yes of course" to experience questions = Excellent
2. Mentioning ANY certification or experience = Excellent  
3. When in doubt, rate UP not down
4. Short answers are fine if they're affirmative

Respond with ONLY ONE WORD: Poor, Ok, Good, or Excellent"""

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a generous HR interviewer who values any relevant experience. Default to higher ratings when in doubt."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 10
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            rating = result['choices'][0]['message']['content'].strip()
            
            valid_ratings = ["Poor", "Ok", "Good", "Great", "Excellent"]
            if rating in valid_ratings:
                return rating
            else:
                return None
                
        except Exception as e:
            print(f"Groq API error: {e}")
            return None
    
    def rate_answer_by_medical_relevance(self, answer, question):
        """More generous rating based on relevance - rewards correct answers"""
        if not answer or answer.strip().upper() == "N/A":
            return "Ok"
        
        answer_lower = answer.lower()
        
        # Try Groq AI first
        if self.groq_api_key:
            groq_rating = self.rate_with_groq(question, answer)
            if groq_rating:
                return groq_rating
        
        # More generous keyword-based rating
        excellent_keywords = [
            'cna', 'certified nursing','nursing', 'rn', 'lpn', 'ma', 'medical assistant',
            'cpr', 'certified', 'license', 'certification', 'degree',
            'hospice', 'hoyer', 'catheter', 'foley', 'gait belt', 
            'sliding board', 'total care', 'bed bath', 'bedridden',
            'years of experience', '5 years', '10 years', 'experienced caregiver',
            'nursing home', 'hospital', 'clinic', 'medical facility',
            'two years', 'three years', 'care unit', 'profession'
        ]
        
        great_keywords = [
            'experience with', 'worked with', 'helped with', 'trained in',
            'bathing', 'dressing', 'toileting', 'feeding', 'medication',
            'mobility', 'transferring', 'turning', 'repositioning',
            'dementia', 'alzheimer', 'stroke', 'diabetes', 'wound care',
            'previous job', 'last position', 'current role'
        ]
        
        good_keywords = [
            'care', 'caregiver', 'caring for', 'help', 'assist', 'support',
            'patient', 'client', 'elderly', 'senior', 'disabled',
            'comfortable with', 'willing to', 'able to', 'can do',
            'experience', 'background', 'worked', 'provided'
        ]
        
        # Strong affirmative answers = Excellent for experience questions
        strong_affirmative = ['yes i have', 'yes of course', 'yes. i have', 'yes. of course',
                             'of course', 'definitely', 'absolutely', 'certainly']
        
        # Basic affirmative = Good
        affirmative = ['yes', 'yeah', 'yep', 'sure', 'i have', 'i can', 'i do', 'i am']
        
        # Check for matches
        has_excellent = any(kw in answer_lower for kw in excellent_keywords)
        has_great = any(kw in answer_lower for kw in great_keywords)
        has_good = any(kw in answer_lower for kw in good_keywords)
        has_strong_affirmative = any(kw in answer_lower for kw in strong_affirmative)
        has_affirmative = any(kw in answer_lower for kw in affirmative)
        
        # Check if question is about experience (most are)
        is_experience_question = 'experience' in question.lower() or 'do you have' in question.lower()
        
        # Very generous rating logic
        if has_excellent or (has_strong_affirmative and is_experience_question):
            return "Excellent"
        elif has_great or has_strong_affirmative:
            return "Excellent"
        elif has_good or (has_affirmative and len(answer.split()) >= 2):
            return "Good"
        elif has_affirmative:
            return "Good"
        elif len(answer.split()) > 3:
            return "Ok"
        else:
            return "Ok"
    
    def match_answers_to_hireology(self, qa_dict):
        """Match transcript answers to Hireology questions using robust multi-pass matching"""
        matched_qa = []
        used_transcript_questions = set()  # Track which transcript questions are already matched
        
        print("\n[MATCHING] Matching Questions (Multi-Pass Algorithm)...\n")
        
        # Define exact keyword mappings for each hireology question
        # This ensures unique identification of questions
        question_keywords = {
            0: ['background', 'experience', 'care professional', 'tell me'],  # Q1
            1: ['motivated', 'become a care'],  # Q2
            2: ['certification', 'specialized training', 'cna', 'cpr', 'ma'],  # Q3
            3: ['name a few', 'caregiving tasks'],  # Q4
            4: ['bathing', 'dressing', 'toileting'],  # Q5
            5: ['another job', 'availability', 'what\'s your availability'],  # Q6
            6: ['flexible', 'schedule', 'overnight', 'weekend shifts'],  # Q7
            7: ['transportation', 'vehicle', 'clients\' homes'],  # Q8
            8: ['why', 'work for', 'agency specifically'],  # Q9
            9: ['hoyer', 'lift', 'stand assist'],  # Q10
            10: ['gait belt'],  # Q11
            11: ['hospice client'],  # Q12
            12: ['hospice care', 'transitioning'],  # Q13
            13: ['sliding board'],  # Q14
            14: ['total care', 'bedridden client'],  # Q15
            15: ['bed bath', 'repositioning', 'changing sheets'],  # Q16
            16: ['foley', 'catheter', 'condom catheter'],  # Q17
        }
        
        # Pass 1: Find best match for each hireology question
        preliminary_matches = []
        
        for idx, hireology_q in enumerate(self.hireology_questions):
            best_match = None
            best_score = 0
            best_answer = "N/A"
            
            hireology_lower = hireology_q.lower()
            keywords = question_keywords.get(idx, [])
            
            for asked_q, ans in qa_dict.items():
                asked_lower = asked_q.lower()
                
                # Calculate multiple matching scores
                # 1. Direct similarity
                similarity = self.calculate_similarity(asked_lower, hireology_lower)
                
                # 2. Keyword match score - how many keywords from the mapping are in the question
                keyword_matches = sum(1 for kw in keywords if kw in asked_lower)
                keyword_score = keyword_matches / len(keywords) if keywords else 0
                
                # 3. Key concept overlap
                asked_concepts = self.extract_key_concepts(asked_q)
                hireology_concepts = self.extract_key_concepts(hireology_q)
                concept_overlap = len(asked_concepts & hireology_concepts) / len(hireology_concepts) if hireology_concepts else 0
                
                # Combined score with keyword matching given highest weight
                combined_score = (keyword_score * 0.5) + (similarity * 0.3) + (concept_overlap * 0.2)
                
                # Bonus for exact phrase matches
                for kw in keywords:
                    if kw in asked_lower and len(kw) > 5:
                        combined_score += 0.15  # Bonus for longer keyword matches
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = asked_q
                    best_answer = ans
            
            preliminary_matches.append({
                'hireology_q': hireology_q,
                'matched_q': best_match,
                'answer': best_answer,
                'score': best_score,
                'index': idx
            })
        
        # Pass 2: Resolve conflicts (same transcript question matched to multiple hireology questions)
        # and re-match for low-score matches (< 0.50)
        
        # Group by matched transcript question
        match_groups = {}
        for m in preliminary_matches:
            key = m['matched_q'] if m['matched_q'] else 'None'
            if key not in match_groups:
                match_groups[key] = []
            match_groups[key].append(m)
        
        # Resolve conflicts - keep highest score match for each transcript question
        final_matches = {}
        questions_needing_rematch = []
        
        for matched_q, matches in match_groups.items():
            if matched_q == 'None':
                for m in matches:
                    questions_needing_rematch.append(m['index'])
                continue
            
            if len(matches) == 1:
                final_matches[matches[0]['index']] = matches[0]
                used_transcript_questions.add(matched_q)
            else:
                # Multiple hireology questions matched to same transcript question
                # Keep the one with highest score
                matches.sort(key=lambda x: x['score'], reverse=True)
                final_matches[matches[0]['index']] = matches[0]
                used_transcript_questions.add(matched_q)
                
                # Other matches need to be re-matched
                for m in matches[1:]:
                    questions_needing_rematch.append(m['index'])
        
        # Pass 3: Re-match questions with low scores or conflicts
        for idx in questions_needing_rematch:
            hireology_q = self.hireology_questions[idx]
            keywords = question_keywords.get(idx, [])
            hireology_lower = hireology_q.lower()
            
            best_match = None
            best_score = 0
            best_answer = "N/A"
            
            for asked_q, ans in qa_dict.items():
                if asked_q in used_transcript_questions:
                    continue  # Skip already used questions
                
                asked_lower = asked_q.lower()
                
                # Re-calculate with focus on keywords
                keyword_matches = sum(1 for kw in keywords if kw in asked_lower)
                keyword_score = keyword_matches / len(keywords) if keywords else 0
                similarity = self.calculate_similarity(asked_lower, hireology_lower)
                
                combined_score = (keyword_score * 0.6) + (similarity * 0.4)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = asked_q
                    best_answer = ans
            
            if best_match:
                used_transcript_questions.add(best_match)
            
            final_matches[idx] = {
                'hireology_q': hireology_q,
                'matched_q': best_match,
                'answer': best_answer,
                'score': best_score,
                'index': idx
            }
        
        # Pass 4: COMPREHENSIVE SEARCH for questions that still don't have a match
        # Each question searches independently through ALL transcript Q&A pairs
        # NO FALLBACK to other question's answers - each question must find its OWN answer
        
        for idx in range(len(self.hireology_questions)):
            current_match = final_matches.get(idx, {})
            
            # If no match found or score is very low, do comprehensive search
            if not current_match.get('matched_q') or current_match.get('score', 0) < 0.25:
                hireology_q = self.hireology_questions[idx]
                keywords = question_keywords.get(idx, [])
                hireology_lower = hireology_q.lower()
                
                best_match = None
                best_score = 0
                best_answer = "N/A"
                
                print(f"  [COMPREHENSIVE SEARCH] Q{idx+1}: Searching all transcript pairs...")
                
                # Search through ALL transcript Q&A, even used ones but with penalty
                for asked_q, ans in qa_dict.items():
                    asked_lower = asked_q.lower()
                    
                    # Calculate comprehensive matching score
                    # 1. Direct text similarity
                    similarity = self.calculate_similarity(asked_lower, hireology_lower)
                    
                    # 2. Keyword matching with exact phrase detection
                    keyword_matches = 0
                    for kw in keywords:
                        if kw in asked_lower:
                            keyword_matches += 1
                            # Extra bonus for longer/more specific keywords
                            if len(kw) > 6:
                                keyword_matches += 0.5
                    keyword_score = keyword_matches / len(keywords) if keywords else 0
                    
                    # 3. Concept overlap
                    asked_concepts = self.extract_key_concepts(asked_q)
                    hireology_concepts = self.extract_key_concepts(hireology_q)
                    concept_overlap = len(asked_concepts & hireology_concepts) / len(hireology_concepts) if hireology_concepts else 0
                    
                    # Combined score - prioritize keyword matches heavily
                    combined_score = (keyword_score * 0.55) + (similarity * 0.25) + (concept_overlap * 0.20)
                    
                    # Apply penalty if this transcript question is already used
                    if asked_q in used_transcript_questions:
                        combined_score *= 0.3  # Heavy penalty but not zero
                    
                    if combined_score > best_score and combined_score > 0.20:
                        best_score = combined_score
                        best_match = asked_q
                        best_answer = ans
                
                # Only update if we found a valid match with its OWN answer
                if best_match and best_answer and best_answer != "N/A":
                    # DO NOT use this match if it would steal another question's answer
                    if best_match not in used_transcript_questions or best_score > 0.5:
                        final_matches[idx] = {
                            'hireology_q': hireology_q,
                            'matched_q': best_match,
                            'answer': best_answer,
                            'score': best_score,
                            'index': idx
                        }
                        print(f"    -> Found match: Score {best_score:.2f}")
                    else:
                        print(f"    -> No unique match found (would duplicate another question's answer)")
                else:
                    print(f"    -> No match found in comprehensive search")
        
        # Build final result
        for idx, hireology_q in enumerate(self.hireology_questions):
            match = final_matches.get(idx, {
                'hireology_q': hireology_q,
                'matched_q': None,
                'answer': 'N/A',
                'score': 0,
                'index': idx
            })
            
            answer = match['answer']
            rating = self.rate_answer_by_medical_relevance(answer, hireology_q)
            
            # Log match info
            if match['matched_q']:
                print(f"Q{idx+1}: Score {match['score']:.2f} | {hireology_q[:50]}...")
                print(f"   -> {match['matched_q'][:60]}...")
            else:
                print(f"Q{idx+1}: NO MATCH | {hireology_q[:50]}...")
            
            matched_qa.append({
                'question': hireology_q,
                'answer': answer,
                'rating': rating,
                'matched_question': match['matched_q'],
                'match_score': match['score']
            })
        
        return matched_qa
    
    def extract_for_hireology(self, agent_id=None):
        """Extract and format data for Hireology"""
        print("Fetching call logs...")
        call_logs = self.get_call_logs(agent_id=agent_id)
        
        if not call_logs or 'callLogs' not in call_logs:
            print("No call logs found")
            return None
        
        recent_call = call_logs['callLogs'][0]
        
        print(f"\n[CALL] Most Recent Call:")
        print(f"   Date: {recent_call['createdAt']}")
        print(f"   Duration: {recent_call['duration']} seconds")
        if self.groq_api_key:
            print(f"   [AI] Using Groq AI for intelligent rating (GENEROUS MODE)")
        print(f"   [MATCH] Using Smart Fuzzy Matching (45%+ threshold)")
        print("\n" + "="*80 + "\n")
        
        transcript = recent_call.get('transcript', '')
        qa_dict = self.parse_transcript_to_dict(transcript)
        print("######################## the transcript is: ", transcript)

        print("######################## the Q&A dict is: ", qa_dict)
        
        print(f"[INFO] Found {len(qa_dict)} questions in transcript")
        print("[DEBUG] Parsed questions from transcript:")
        for i, q in enumerate(qa_dict.keys(), 1):
            print(f"  T{i}: {q[:80]}...")
        print()
        
        hireology_qa = self.match_answers_to_hireology(qa_dict)
        
        print("\n" + "="*80)
        print("[RESULTS] HIREOLOGY PRE-SCREEN QUESTIONNAIRE:\n")
        for i, qa in enumerate(hireology_qa, 1):
            print(f"Q{i}: {qa['question']}")
            if qa['matched_question']:
                print(f"âœ“ Matched with: {qa['matched_question'][:100]}... (Score: {qa['match_score']:.2f})")
            print(f"Answer: {qa['answer']}")
            print(f"Rating: {qa['rating']}")
            print("-" * 80)
        
        self.save_hireology_format(hireology_qa, recent_call)
        
        return hireology_qa
    
    def save_hireology_format(self, qa_pairs, call_info):
        """Save in multiple formats for Hireology"""
        os.makedirs('call_data', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean up old files FIRST - before saving the new one
        import glob
        old_files = glob.glob("call_data/hireology_qa_*.json")
        
        for old_file in old_files:
            try:
                os.remove(old_file)
                print(f" Removed old file: {old_file}")
            except Exception as e:
                print(f" Warning: Could not remove {old_file}: {e}")
        
        # Now save the new JSON file
        json_file = f"call_data/hireology_qa_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'call_info': {
                    'date': call_info['createdAt'],
                    'duration': call_info['duration'],
                    'call_id': call_info['id']
                },
                'qa_pairs': qa_pairs
            }, f, indent=2, ensure_ascii=False)
        print(f"\n JSON saved: {json_file}")
        
      
# ============= USAGE =============

if __name__ == "__main__":
    API_KEY = "pit-6ce5eac0-b1b2-4e1e-8313-018cbf31e324" 
    LOCATION_ID = "M5jnxd1r8yq3o5gxSYOP" 
    AGENT_ID = "693448f6231659c2a32a3bca"
    GROQ_API_KEY=os.getenv("GROQ_API_KEY")
    
    
    extractor = HireologyQAExtractor(API_KEY, LOCATION_ID, GROQ_API_KEY)
    qa_pairs = extractor.extract_for_hireology(agent_id=AGENT_ID)
    print("The QA Extractor is:",extractor)
    print("The QA pairs from Hirelogy is:",extractor)

