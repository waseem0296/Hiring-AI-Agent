
import os
import time
import pyotp
import json
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_hireology_token():
    """
    Logs into Hireology and returns the authentication token as a string.
    
    Returns:
        str: The JWT authentication token, or None if token could not be found
    """
    # Load env vars
    load_dotenv()

    EMAIL = os.getenv("HIREOLOGY_EMAIL") or os.getenv("EMAIL")
    PASSWORD = os.getenv("HIREOLOGY_PASSWORD") or os.getenv("PASSWORD")
    SECRET = os.getenv("TOTP_SECRET")

    if SECRET:
        SECRET = SECRET.replace(" ", "").upper()

    if not EMAIL or not PASSWORD or not SECRET:
        print("❌ Error: Missing credentials in .env")
        return None

    print(f"📧 Logging in as: {EMAIL}")
    totp = pyotp.TOTP(SECRET)

    # Setup Browser
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Keep visible for now

    # Enable Performance Logging to capture network headers
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    # Also add some arguments to make it less detectable and more permissive
    options.add_argument("--auto-open-devtools-for-tabs") 

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    # User defined deep-link
    TARGET_URL = "https://accounts.hireology.com/46e82dea-91f4-4d30-aabc-ac1ee030bec2/b2c_1a_hireology_jit_signup_signin/oauth2/v2.0/authorize?client_id=f067e6a3-815d-413d-878e-d223efaa0ca4&redirect_uri=https%3A%2F%2Fapi.hireology.com%2Fv2%2Foauth2%2Fcallback%2Fauthorize_web&response_type=code&scope=offline_access"

    token = None
    
    try:
        print("🌍 Opening Login Page...")
        driver.get(TARGET_URL)
        
        # ---------------------------------------------------------
        # Step 1: Email
        # ---------------------------------------------------------
        print("✍️  Entering Email...")
        email_field = wait.until(EC.visibility_of_element_located((By.ID, "signInName")))
        email_field.clear()
        email_field.send_keys(EMAIL)

        # ---------------------------------------------------------
        # Step 2: Password
        # ---------------------------------------------------------
        print("🔑 Entering Password...")
        try:
            # Try finding it immediately
            pass_field = driver.find_element(By.ID, "password")
            if not pass_field.is_displayed():
                # If hidden, maybe we need to Tab or it's behind a transition??
                # Or usually in B2C flows with specific layouts, it might just need a moment
                pass_field = wait.until(EC.visibility_of_element_located((By.ID, "password")))
                
            pass_field.clear()
            pass_field.send_keys(PASSWORD)
        except:
            # User reported success with clicking Next first in some flows
            print("   (Password field not found, clicking Next first...)")
            driver.find_element(By.ID, "next").click()
            pass_field = wait.until(EC.visibility_of_element_located((By.ID, "password")))
            pass_field.clear()
            pass_field.send_keys(PASSWORD)

        # Submit Password
        print("➡️  Submitting Credentials...")
        try:
            driver.find_element(By.ID, "next").click()
        except:
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()


        # ---------------------------------------------------------
        # Step 4: OTP Entry
        # ---------------------------------------------------------
        print("⏳ Waiting for OTP Input...")
        
        try:
            # After clicking Continue, we should see the OTP input
            otp_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 
                "input#otpCode, input[name='otp'], input[id='otp'], input#verificationCode, input[aria-label='Verification Code']"
            )))
        except:
            print("   ❌ OTP field not found. Current URL:", driver.current_url)
            raise


        
        print("   ✅ Found OTP Field!")
        
        # Wait for the beginning of a fresh 30-second window
        # to ensure the OTP is valid for as long as possible
        current_time = time.time()
        time_passed_in_window = current_time % 30
        
        if time_passed_in_window > 2:
            time_remaining = 30 - time_passed_in_window
            print(f"⏳ Current window is {time_passed_in_window:.1f}s old. Waiting {time_remaining + 1:.1f}s for a fresh OTP...")
            time.sleep(time_remaining + 1)
            print("✅ Fresh window started!")
        else:
            print(f"✅ Already at the start of a window ({time_passed_in_window:.1f}s passed).")

        otp_code = totp.now()
        print(f"🔐 Generated OTP: {otp_code}")
        otp_field.clear()
        otp_field.send_keys(otp_code)
        time.sleep(1) # Small delay to ensure input is registered
        
        # ---------------------------------------------------------
        # Step 5: Verify
        # ---------------------------------------------------------
        print("➡️  Clicking Verify...")
        try:
            verify_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], #verify, #next, #continue")
            verify_btn.click()
        except:
            pass # maybe auto-submit

        # ---------------------------------------------------------
        # Success Check
        # ---------------------------------------------------------
        print("⏳ Waiting for login completion...")
        
        # Wait for URL to change to something indicating success (callback or hireology.com dashboard)
        # We'll give it 20 seconds
        start_wait = time.time()
        success = False
        while time.time() - start_wait < 20:
            curr = driver.current_url
            # If we are back at the callback or on the main app
            if "authorize_web" in curr or ("hireology.com" in curr and "accounts" not in curr):
                print(f"🎉 Login Successful! Final URL: {curr}")
                success = True
                
                # ---------------------------------------------------------
                # Token Extraction
                # ---------------------------------------------------------
                # Try multiple methods to find the token
                
                # Step A: Give it a moment to settle
                print("🔍 Searching for Auth Token...")
                time.sleep(3)
                
                # Step B: If not found, try navigating to the page that triggers the token API
                # User specifically mentioned a locations API call.
                if not token:
                    print("   (Navigating to locations to trigger API calls...)")
                    driver.get("https://app.hireology.com/ui/locations")
                    time.sleep(5) # Wait for page and API calls
                
                # 1. Search localStorage and sessionStorage deep
                try:
                    # Check ALL values in localStorage and sessionStorage
                    script = """
                    let results = [];
                    for (let i = 0; i < localStorage.length; i++){
                        let key = localStorage.key(i);
                        let value = localStorage.getItem(key);
                        results.push({source: 'localStorage', key: key, value: value});
                    }
                    for (let i = 0; i < sessionStorage.length; i++){
                        let key = sessionStorage.key(i);
                        let value = sessionStorage.getItem(key);
                        results.push({source: 'sessionStorage', key: key, value: value});
                    }
                    return results;
                    """
                    items = driver.execute_script(script)
                    print(f"   (Checking {len(items)} storage items...)")
                    
                    for item in items:
                        val = item['value']
                        if not val: continue
                        
                        # Direct JWT check
                        if val.startswith("eyJ") and "." in val:
                            token = val
                            print(f"✅ Found Token in {item['source']} (key: {item['key']})")
                            break
                        
                        # Check if it's a JSON object containing a JWT
                        try:
                            data = json.loads(val)
                            if isinstance(data, (dict, list)):
                                # Recursively search for JWT in dict or list
                                def find_jwt(obj):
                                    if isinstance(obj, str) and obj.startswith("eyJ") and "." in obj:
                                        return obj
                                    if isinstance(obj, dict):
                                        for v in obj.values():
                                            res = find_jwt(v)
                                            if res: return res
                                    if isinstance(obj, list):
                                        for v in obj:
                                            res = find_jwt(v)
                                            if res: return res
                                    return None
                                
                                res = find_jwt(data)
                                if res:
                                    token = res
                                    print(f"✅ Found Token inside JSON object in {item['source']} (key: {item['key']})")
                                    break
                        except:
                            pass
                    
                except Exception as e:
                    print(f"⚠️ Error reading storage: {e}")

                # 2. Try Cookies if not found
                if not token:
                    print("   (Checking cookies...)")
                    try:
                        cookies = driver.get_cookies()
                        for cookie in cookies:
                            val = cookie['value']
                            # Cookies might URL encode the token
                            from urllib.parse import unquote
                            decoded_val = unquote(val)
                            
                            if decoded_val.startswith("eyJ") and "." in decoded_val:
                                token = decoded_val
                                print(f"✅ Found Token in Cookie: {cookie['name']}")
                                break
                            
                            # Some systems store them as JSON strings in cookies
                            if 'eyJ' in decoded_val:
                                import re
                                match = re.search(r'eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+', decoded_val)
                                if match:
                                    token = match.group(0)
                                    print(f"✅ Extracted Token from Cookie via regex: {cookie['name']}")
                                    break
                    except Exception as e:
                        print(f"⚠️ Error reading cookies: {e}")

                # 3. Scan Performance Logs for Authorization header (Active Interception)
                if not token:
                    print("   (Scanning Network Requests for Authorization header...)")
                    try:
                        # Give it another second for API calls to trigger
                        time.sleep(3)
                        logs = driver.get_log('performance')
                        for entry in logs:
                            log_data = json.loads(entry['message'])
                            message = log_data['message']
                            
                            # Look for Network.requestWillBeSent which contains headers
                            if message.get('method') == 'Network.requestWillBeSent':
                                params = message.get('params', {})
                                request = params.get('request', {})
                                url = request.get('url', '')
                                headers = request.get('headers', {})
                                
                                # Check specifically for the URL mentioned by the user or any hireology API
                                if "locations?organizationScope=ALL" in url or "api.hireology.com" in url:
                                    # Check for Authorization header (case-insensitive)
                                    auth_header = next((v for k, v in headers.items() if k.lower() == 'authorization'), None)
                                    
                                    if auth_header and "Bearer" in auth_header:
                                        potential_token = auth_header.replace("Bearer ", "").strip()
                                        if potential_token.startswith("eyJ") and "." in potential_token:
                                            token = potential_token
                                            print(f"✅ Extracted Token from Network Request: {url}")
                                            break
                    except Exception as e:
                        print(f"⚠️ Error reading performance logs: {e}")

                # 4. Last Resort: Deep scan for specific patterns in JS objects
                if not token:
                    print("   (Trying deep scan for specific patterns...)")
                    token = driver.execute_script("""
                        function find(obj, depth = 0) {
                            if (depth > 5 || !obj) return null;
                            try {
                                for (let key in obj) {
                                    let val = obj[key];
                                    if (typeof val === 'string' && val.startsWith('eyJ') && val.includes('.')) return val;
                                    if (typeof val === 'object') {
                                        let found = find(val, depth + 1);
                                        if (found) return found;
                                    }
                                }
                            } catch(e) {}
                            return null;
                        }
                        return find(window.Oidc || window.auth || window.config || window.__REDUX_STATE__);
                    """)
                    if token: print("✅ Found Token in window object via deep scan")

                if token:
                    print("\n" + "="*50)
                    print("🔑 AUTH TOKEN FOUND:")
                    print("="*50)
                    print(token)
                    print("="*50 + "\n")
                    
                    # Save to .jwt_cache (used by auth_manager.py)
                    try:
                        with open(".jwt_cache", "w") as f:
                            f.write(token)
                        print("💾 Token saved to .jwt_cache")
                    except Exception as e:
                        print(f"⚠️ Could not save to .jwt_cache: {e}")
                else:
                    print("❌ Could not find JWT token in localStorage, cookies, or network logs.")
                
                break
            time.sleep(1)
            
        if not success:
            print("⚠️  Warning: URL didn't change to expected success page, but script finished.")
            print(f"Current URL: {driver.current_url}")

        # Keep open briefly for user validation
        print("✅ Script Completed.")
        time.sleep(5) 

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        driver.save_screenshot("login_final_error.png")
    finally:
        
        #    driver.quit()
        pass
    
    return token


# Example usage:
if __name__ == "__main__":
    auth_token = get_hireology_token()
    if auth_token:
        print(f"\n✅ Token retrieved successfully!")
        print(f"Token: {auth_token}")
    else:
        print("\n Failed to retrieve token")