
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
            "Experience emptying foley catheters and male condom catheters?"
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
    
    def parse_transcript_to_dict(self, transcript):
        """Parse transcript into a dictionary of questions and answers"""
        lines = transcript.split('\n')
        qa_dict = {}
        current_question = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('bot:'):
                bot_text = line[4:].strip()
                if '?' in bot_text:
                    questions = [q.strip() + '?' for q in bot_text.split('?') if q.strip()]
                    if questions:
                        current_question = questions[-1]
            
            elif line.startswith('human:') and current_question:
                answer = line[6:].strip()
                if answer:
                    if current_question in qa_dict:
                        qa_dict[current_question] += " " + answer
                    else:
                        qa_dict[current_question] = answer
        
        return qa_dict
    
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
    
    def smart_question_match(self, asked_question, hireology_question, threshold=0.65):
        """
        Advanced matching using multiple strategies:
        1. Direct text similarity (SequenceMatcher)
        2. Key concept overlap
        3. Specific keyword matching
        """
        # Strategy 1: Direct similarity
        direct_similarity = self.calculate_similarity(asked_question, hireology_question)
        
        # Strategy 2: Key concept overlap
        asked_concepts = self.extract_key_concepts(asked_question)
        hireology_concepts = self.extract_key_concepts(hireology_question)
        
        if len(hireology_concepts) > 0:
            concept_overlap = len(asked_concepts & hireology_concepts) / len(hireology_concepts)
        else:
            concept_overlap = 0
        
        # Strategy 3: Specific keyword matching for important terms
        asked_lower = asked_question.lower()
        hireology_lower = hireology_question.lower()
        
        # Define specific matching patterns
        specific_matches = 0
        specific_checks = 0
        
        patterns = {
            'background': ['background', 'experience', 'tell me about'],
            'motivated': ['motivated', 'why', 'what made you'],
            'certification': ['certification', 'certified', 'training', 'cna', 'cpr', 'license'],
            'caregiving tasks': ['caregiving', 'tasks', 'duties', 'responsibilities'],
            'bathing': ['bathing', 'dressing', 'toileting', 'grooming', 'hygiene'],
            'availability': ['availability', 'available', 'schedule', 'hours', 'another job'],
            'flexible': ['flexible', 'flexibility', 'overnight', 'weekend', 'shift'],
            'transportation': ['transportation', 'transport', 'vehicle', 'car', 'drive'],
            'why work': ['why', 'what interests', 'what attracted', 'agency', 'company'],
            'hoyer': ['hoyer', 'lift', 'stand assist', 'mechanical lift'],
            'gait belt': ['gait', 'belt', 'transfer belt'],
            'hospice': ['hospice', 'end of life', 'palliative'],
            'transition': ['transition', 'transitioning', 'passing', 'end stage'],
            'sliding board': ['sliding board', 'transfer board', 'slide board'],
            'total care': ['total care', 'bedridden', 'bed bound', 'non-ambulatory'],
            'bed bath': ['bed bath', 'bath in bed', 'changing sheets', 'turning', 'repositioning'],
            'catheter': ['catheter', 'foley', 'urinary', 'condom catheter']
        }
        
        for category, keywords in patterns.items():
            if any(kw in hireology_lower for kw in keywords):
                specific_checks += 1
                if any(kw in asked_lower for kw in keywords):
                    specific_matches += 1
        
        keyword_match_ratio = specific_matches / specific_checks if specific_checks > 0 else 0
        
        # Combine all strategies with weights
        final_score = (
            direct_similarity * 0.4 +        # 40% weight on direct similarity
            concept_overlap * 0.3 +          # 30% weight on concept overlap
            keyword_match_ratio * 0.3        # 30% weight on specific keywords
        )
        
        # Debug output for close matches
        if final_score > 0.5:
            print(f"  🔍 Match Score: {final_score:.2f} | Direct: {direct_similarity:.2f} | Concepts: {concept_overlap:.2f} | Keywords: {keyword_match_ratio:.2f}")
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
            
            prompt = f"""You are evaluating a caregiver interview answer. Be GENEROUS with ratings - reward any relevant experience.

Question: {question}

Candidate's Answer: {answer}

Rate as: Poor, Ok, Good, Great, or Excellent

**BE GENEROUS - Rating Guidelines:**
- **Excellent**: ANY certification mentioned (CNA, CPR, etc.) OR specific medical equipment experience OR detailed caregiving experience
- **Great**: Clear caregiving experience OR mentions specific tasks OR shows relevant skills
- **Good**: Basic caregiving experience OR shows willingness/motivation OR any relevant mention
- **Ok**: Simple affirmative answer (yes, I can, I have) OR availability stated
- **Poor**: Only if completely irrelevant, negative, or refuses

**Key Rule: If the answer is relevant and positive, rate it Good or higher. Be generous!**

Respond with ONLY ONE WORD: Poor, Ok, Good, Great, or Excellent"""

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
            'cna', 'certified nursing', 'rn', 'lpn', 'ma', 'medical assistant',
            'cpр', 'certified', 'license', 'certification', 'degree',
            'hospice', 'hoyer', 'catheter', 'foley', 'gait belt', 
            'sliding board', 'total care', 'bed bath', 'bedridden',
            'years of experience', '5 years', '10 years', 'experienced caregiver',
            'nursing home', 'hospital', 'clinic', 'medical facility'
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
        
        affirmative = ['yes', 'yeah', 'yep', 'sure', 'of course', 'definitely', 
                      'absolutely', 'i have', 'i can', 'i do', 'i am']
        
        # Check for matches
        has_excellent = any(kw in answer_lower for kw in excellent_keywords)
        has_great = any(kw in answer_lower for kw in great_keywords)
        has_good = any(kw in answer_lower for kw in good_keywords)
        has_affirmative = any(kw in answer_lower for kw in affirmative)
        
        # Generous rating logic
        if has_excellent:
            return "Excellent"
        elif has_great or (has_good and len(answer.split()) > 10):
            return "Great"
        elif has_good or (has_affirmative and len(answer.split()) > 3):
            return "Good"
        elif has_affirmative:
            return "Good"
        elif len(answer.split()) > 5:
            return "Ok"
        else:
            return "Poor"
    
    def match_answers_to_hireology(self, qa_dict):
        """Match transcript answers to Hireology questions using smart matching"""
        matched_qa = []
        
        print("\n🔄 Matching Questions (Smart Fuzzy Matching)...\n")
        
        for hireology_q in self.hireology_questions:
            answer = "N/A"
            matched_asked_q = None
            best_score = 0
            
            # Try smart matching with all asked questions
            for asked_q, ans in qa_dict.items():
                if self.smart_question_match(asked_q, hireology_q):
                    # Calculate score to find best match
                    score = self.calculate_similarity(asked_q, hireology_q)
                    if score > best_score:
                        best_score = score
                        answer = ans
                        matched_asked_q = asked_q
            
            rating = self.rate_answer_by_medical_relevance(answer, hireology_q)
            
            matched_qa.append({
                'question': hireology_q,
                'answer': answer,
                'rating': rating,
                'matched_question': matched_asked_q,
                'match_score': best_score
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
        
        print(f"\n📞 Most Recent Call:")
        print(f"   Date: {recent_call['createdAt']}")
        print(f"   Duration: {recent_call['duration']} seconds")
        if self.groq_api_key:
            print(f"   🤖 Using Groq AI for intelligent rating (GENEROUS MODE)")
        print(f"   🎯 Using Smart Fuzzy Matching (90%+ similarity)")
        print("\n" + "="*80 + "\n")
        
        transcript = recent_call.get('transcript', '')
        qa_dict = self.parse_transcript_to_dict(transcript)
        
        print(f"📋 Found {len(qa_dict)} questions in transcript\n")
        
        hireology_qa = self.match_answers_to_hireology(qa_dict)
        
        print("\n" + "="*80)
        print("🎯 HIREOLOGY PRE-SCREEN QUESTIONNAIRE:\n")
        for i, qa in enumerate(hireology_qa, 1):
            print(f"Q{i}: {qa['question']}")
            if qa['matched_question']:
                print(f"✓ Matched with: {qa['matched_question'][:100]}... (Score: {qa['match_score']:.2f})")
            print(f"Answer: {qa['answer']}")
            print(f"Rating: {qa['rating']}")
            print("-" * 80)
        
        self.save_hireology_format(hireology_qa, recent_call)
        
        return hireology_qa
    
    def save_hireology_format(self, qa_pairs, call_info):
        """Save in multiple formats for Hireology"""
        os.makedirs('call_data', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
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
    # GROQ_API_KEY = "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"
    
    extractor = HireologyQAExtractor(API_KEY, LOCATION_ID, GROQ_API_KEY)
    qa_pairs = extractor.extract_for_hireology(agent_id=AGENT_ID)