# Auto Monitor - Simple Guide

## What It Does
Automatically calls new applicants when they appear in Hireology.

## Files
- **`auto_monitor.py`** - The monitoring code (only 1 file!)
- **`processed_applicants.json`** - Tracks who was already called (auto-created)

## How to Use

### Method 1: From Python
```python
from app_updated import run_auto_monitor

# Start monitoring (default: job 2606114, check every 60 seconds)
run_auto_monitor()

# Or customize
run_auto_monitor(job_id="YOUR_JOB_ID", check_interval=120)
```

### Method 2: Run test file
```bash
python test_monitor.py
```

## What Happens
1. Checks for new applicants every 60 seconds
2. When new applicant found → automatically runs complete workflow
3. Marks as processed → won't call again
4. Repeats forever (until you press Ctrl+C)

## Stop It
Press `Ctrl+C`

## That's It!
Simple and clean - just 1 file + 1 function in app_updated.py
