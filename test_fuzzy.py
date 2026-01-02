
from difflib import SequenceMatcher

q_json = "Do you have any certifications or specialized training related to caregiving? (CNA, MA, CPR, etc.)"
q_hireology = "Are you currently CPR certified? Do you have any other certifications such as CNA, RN, etc?"

ratio = SequenceMatcher(None, q_json.lower(), q_hireology.lower()).ratio()
print(f"Match Score: {ratio}")
