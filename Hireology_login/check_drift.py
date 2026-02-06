import time
import requests
import datetime

def check_time_drift():
    print("Checking system time drift...")
    try:
        # Get time from a reliable source (Google)
        response = requests.head("https://www.google.com", timeout=10)
        server_date_str = response.headers.get('date')
        if not server_date_str:
            print("Could not get date from server headers.")
            return

        # Parse server time (GMT/UTC)
        try:
            # Use email.utils to parse RFC 2822 dates correctly
            import email.utils
            server_ts = email.utils.mktime_tz(email.utils.parsedate_tz(server_date_str))
        except:
            server_time = datetime.datetime.strptime(server_date_str, '%a, %d %b %Y %H:%M:%S %Z')
            server_ts = server_time.replace(tzinfo=datetime.timezone.utc).timestamp()

        # Get local time in UTC timestamp
        local_ts = time.time()
        
        drift = local_ts - server_ts
        
        print(f"Server Timestamp: {server_ts}")
        print(f"Local Timestamp:  {local_ts}")
        print(f"Drift: {drift:.2f} seconds")
        
        if abs(drift) > 30:
            print("⚠️ WARNING: Significant time drift detected! OTP might fail.")
        else:
            print("✅ Time drift is within acceptable range for TOTP.")
            
    except Exception as e:
        print(f"Error checking drift: {e}")

if __name__ == "__main__":
    check_time_drift()
