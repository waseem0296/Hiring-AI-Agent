import os
import pyotp
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_login_flow():
    load_dotenv()
    email = os.getenv('HIREOLOGY_EMAIL') or os.getenv('EMAIL')
    password = os.getenv('HIREOLOGY_PASSWORD') or os.getenv('PASSWORD')
    secret = os.getenv('TOTP_SECRET')
    
    if not secret:
        print("Error: TOTP_SECRET not found")
        return

    totp = pyotp.TOTP(secret.replace(' ','').upper())
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print("Starting navigation...")
        driver.get('https://app.hireology.com/')
        
        print("Entering Credentials...")
        wait.until(EC.visibility_of_element_located((By.ID, 'signInName'))).send_keys(email)
        driver.find_element(By.ID, 'password').send_keys(password)
        driver.find_element(By.ID, 'next').click()
        
        print("Waiting for MFA Selection...")
        time.sleep(3)
        wait.until(EC.element_to_be_clickable((By.ID, 'continue'))).click()
        
        print("Waiting for OTP Field...")
        time.sleep(3)
        otp_field = wait.until(EC.visibility_of_element_located((By.ID, 'otpCode')))
        
        otp_code = totp.now()
        print(f"Entering OTP: {otp_code}")
        otp_field.send_keys(otp_code)
        
        print("Clicking Verify...")
        driver.find_element(By.ID, 'continue').click()
        
        print("Waiting for result...")
        time.sleep(10)
        
        driver.save_screenshot('otp_result.png')
        print(f"Final URL: {driver.current_url}")
        
        # Check if error message is present
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "error").text
            print(f"Page Error: {error_msg}")
        except:
            pass
            
    except Exception as e:
        print(f"Error during flow: {e}")
        driver.save_screenshot('flow_error.png')
    finally:
        driver.quit()

if __name__ == "__main__":
    run_login_flow()
