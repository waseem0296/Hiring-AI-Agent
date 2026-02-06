import os
import sys
import time
import pyotp
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
log_file = open("login_log.txt", "w", encoding="utf-8")
def log(msg):
    print(msg)
    log_file.write(str(msg) + "\n")
    log_file.flush()

# Load env vars
load_dotenv()

EMAIL = os.getenv("HIREOLOGY_EMAIL") or os.getenv("EMAIL")
PASSWORD = os.getenv("HIREOLOGY_PASSWORD") or os.getenv("PASSWORD")
SECRET = os.getenv("TOTP_SECRET")

if SECRET:
    SECRET = SECRET.replace(" ", "").upper()

log(f"Logging in as: {EMAIL}")
totp = pyotp.TOTP(SECRET)

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)

TARGET_URL = "https://accounts.hireology.com/46e82dea-91f4-4d30-aabc-ac1ee030bec2/b2c_1a_hireology_jit_signup_signin/oauth2/v2.0/authorize?client_id=f067e6a3-815d-413d-878e-d223efaa0ca4&login_state=WC9LMzFZWlhHZ3lpMXZsS1ZTR1h5U0ZLK0VtRHRjS2NXZzFUU0NlaFlFN0l3SXdNejhxU2dWV25wN0l6MGVTYURhNko2akdLUVBPSk54RzF5SVMxZ1E9PS0tYnZLalR2UUpUTyt3U0RBRk9DOXNHQT09--3937bf2fb969f36f1881a116452c17cd159b4475&prompt=login&redirect_uri=https%3A%2F%2Fapi.hireology.com%2Fv2%2Foauth2%2Fcallback%2Fauthorize_web&response_mode=query&response_type=code&scope=https%3A%2F%2Fapi.hireology.com%2Fv2+https%3A%2F%2Fapi.hireology.com%2Fv3+https%3A%2F%2Fapi.hireology.com%2Fai+email+offline_access&state=WC9LMzFZWlhHZ3lpMXZsS1ZTR1h5U0ZLK0VtRHRjS2NXZzFUU0NlaFlFN0l3SXdNejhxU2dWV25wN0l6MGVTYURhNko2akdLUVBPSk54RzF5SVMxZ1E9PS0tYnZLalR2UUpUTyt3U0RBRk9DOXNHQT09--3937bf2fb969f36f1881a116452c17cd159b4475"

try:
    log("Opening Login Page...")
    driver.get(TARGET_URL)
    
    # 1. Email
    log("Entering Email...")
    wait.until(EC.visibility_of_element_located((By.ID, "signInName"))).send_keys(EMAIL)

    # 2. Password
    log("Entering Password...")
    try:
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
    except:
        driver.find_element(By.ID, "next").click()
        wait.until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(PASSWORD)

    # 3. Submit Password
    log("Submitting Password...")
    try:
        driver.find_element(By.ID, "next").click()
    except:
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # 4. WAIT LONGER
    log("Waiting 15s for next screen...")
    time.sleep(15)
    
    log("--- DUMPING PAGE STATE ---")
    log(f"Current URL: {driver.current_url}")
    log(f"Title: {driver.title}")
    
    # Try to find any visible inputs
    inputs = driver.find_elements(By.TAG_NAME, "input")
    visible_inputs = [i for i in inputs if i.is_displayed()]
    log(f"Visible Inputs: {len(visible_inputs)}")
    for i in visible_inputs:
        log(f"  Input: name='{i.get_attribute('name')}', id='{i.get_attribute('id')}'")
        
    # Dump Body Text (truncated)
    body_text = driver.find_element(By.TAG_NAME, "body").text
    log(f"Body Text Snippet: {body_text[:200].replace('\n', ' ')}")
    
    # 5. Fallback Search for OTP
    log("Searching for OTP field...")
    try:
        otp_field = driver.find_element(By.CSS_SELECTOR, "input[id='otp'], input[name='otp'], input[id='verificationCode']")
        if otp_field.is_displayed():
            log(f"FOUND OTP FIELD! ID: {otp_field.get_attribute('id')}")
            
            otp_code = totp.now()
            log(f"Generating OTP: {otp_code}")
            otp_field.send_keys(otp_code)
            
            log("Clicking Verify...")
            try:
                driver.find_element(By.CSS_SELECTOR, "button[type='submit'], #verify, #continue").click()
            except:
                pass
            
            time.sleep(5)
    except:
        log("OTP Field not found in simple search.")

    log("--- END DUMP ---")

except Exception as e:
    log(f"ERROR: {e}")
finally:
    driver.quit()
    log_file.close()
