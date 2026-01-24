"""
Quick test of auto monitor
"""

from app_updated import run_auto_monitor

if __name__ == "__main__":
    print("Testing auto monitor...")
    print("This will check once and then you can stop it with Ctrl+C")
    print()
    
    # Run with a longer interval for testing
    run_auto_monitor(job_id="2606114", check_interval=120)
