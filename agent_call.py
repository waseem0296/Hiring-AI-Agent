"""
GoHighLevel Voice AI - Call Trial API
Initiates an outbound/inbound test call using the Voice AI agent
"""

import requests
import json
from typing import Literal



def make_trial_call(
    token_id: str,
    to_phone_number: str,
    from_phone_number: str = "+18439407924",
    agent_id: str = "693448f6231659c2a32a3bca",
    location_id: str = "M5jnxd1r8yq3o5gxSYOP",
    test_scenario: Literal["INBOUND", "OUTBOUND"] = "OUTBOUND"
) -> dict:
    """
    Make a trial call using GoHighLevel Voice AI
    
    Args:
        to_phone_number: Phone number to call (e.g., "+18001234567")
        from_phone_number: Caller ID phone number (e.g., "+18439407924")
        agent_id: Voice AI Agent ID
        location_id: GHL Location ID
        token_id: GHL authentication token (JWT)
        test_scenario: Either "INBOUND" or "OUTBOUND"
    
    Returns:
        dict: API response
    """
    url = "https://services.leadconnectorhq.com/voice-ai/call/trial"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "channel": "APP",
        "content-type": "application/json",
        "origin": "https://app.gohighlevel.com",
        "referer": "https://app.gohighlevel.com/",
        "source": "WEB_USER",
        "token-id": token_id,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "version": "2021-07-28"
    }
    
    payload = {
        "toPhoneNumber": to_phone_number,
        "fromPhoneNumber": from_phone_number,
        "agentId": agent_id,
        "locationId": location_id,
        "testScenario": test_scenario
    }
    
    print(f"\n📞 Initiating {test_scenario} trial call...")
    print(f"   From: {from_phone_number}")
    print(f"   To: {to_phone_number}")
    print(f"   Agent: {agent_id}")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Call initiated successfully!")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"❌ Call failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return {"error": response.text, "status_code": response.status_code}
            
    except Exception as e:
        print(f"❌ Error making call: {str(e)}")
        return {"error": str(e)}


# ============= MAIN EXECUTION =============

if __name__ == "__main__":
    # Configuration
    TOKEN_ID = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImEzOGVhNmEwNDA4YjBjYzVkYTE4OWRmYzg4ODgyZDBmMWI3ZmJmMGUiLCJ0eXAiOiJKV1QifQ.eyJ1c2VyX2lkIjoiaVJHOGdKSzI3MFBoUENSQlE3OUMiLCJjb21wYW55X2lkIjoiM2s4Wlh3VjNxVUZVU0JubjlSbDAiLCJyb2xlIjoiYWRtaW4iLCJ0eXBlIjoiYWNjb3VudCIsInZlcnNpb24iOjIsImxvY2F0aW9ucyI6WyJNNWpueGQxcjh5cTNvNWd4U1lPUCJdLCJwZXJtaXNzaW9ucyI6eyJ3b3JrZmxvd3NfZW5hYmxlZCI6dHJ1ZSwid29ya2Zsb3dzX3JlYWRfb25seSI6ZmFsc2V9LCJwcmltYXJ5VXNlciI6e30sImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9oaWdobGV2ZWwtYmFja2VuZCIsImF1ZCI6ImhpZ2hsZXZlbC1iYWNrZW5kIiwiYXV0aF90aW1lIjoxNzY2ODQ0OTM4LCJzdWIiOiJpUkc4Z0pLMjcwUGhQQ1JCUTc5QyIsImlhdCI6MTc2NzAxMjYzNSwiZXhwIjoxNzY3MDE2MjM1LCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7fSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.qNatUIgK2XNasWQToVIYAkJAhIWtmSP-6wEGU2ylzCu1u-LP5B4JbMiFvB_1nLI7awUHJxBXVQXIM3HmIWYNuzVVb3Ab0s4sqri0R3D01hsRsBn0YakzQYh7dewMTfB8LJT3jL43Lp8DF6IH1wPPiW79OAPqRt32YQWeq8IUMuKxcylmX-X7oMFg9gxy1F_VBkLe4elSfRYAHQesBLk9uZ53wKy-lP3hAVOFCQISIpnCd3_4fjYwH0q0iZGx4HFCRLdcTU9epN_zQ1WbH0-L0bbji4WkUN5B4bIm_oOuhIkuFr58kIpaESbhRJMayaGj109WaOWN-7doK4adjYTqLg"
    AGENT_ID = "693448f6231659c2a32a3bca"
    LOCATION_ID = "M5jnxd1r8yq3o5gxSYOP"
    FROM_PHONE = "+18439407924"
    
    # Phone number to call
    TO_PHONE = "+16135189745"  # Change this to your target number
    
    # Make the call
    result = make_trial_call(
        to_phone_number=TO_PHONE,
        from_phone_number=FROM_PHONE,
        agent_id=AGENT_ID,
        location_id=LOCATION_ID,
        token_id=TOKEN_ID,
        test_scenario="INBOUND"
    )
    
    print(f"\n Final Result: {json.dumps(result, indent=2)}")
