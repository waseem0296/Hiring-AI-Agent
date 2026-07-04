# Hiring AI Agent

An end-to-end AI recruitment automation system for a home-care hiring pipeline. The system automatically screens Hireology applicants, conducts AI-powered phone interviews through GoHighLevel Voice AI, evaluates interview responses using Groq (LLaMA 3.3 70B), and writes interview scores back into Hireology—all without human intervention.

---

## Features

- Automatic applicant screening
- Application completeness validation
- AI-powered outbound phone interviews
- Automatic interview transcription
- LLM-based interview evaluation using Groq
- Automatic candidate scoring in Hireology
- Continuous applicant monitoring
- Automated rejection and follow-up emails
- Token management with automatic refresh
- End-to-end hiring workflow with minimal manual effort

---

## Workflow

```text
New Applicant
      │
      ▼
Screen Application
      │
      ▼
Qualify / Reject
      │
      ▼
AI Phone Interview
      │
      ▼
Transcript Processing
      │
      ▼
LLM Evaluation (Groq)
      │
      ▼
Score Candidate
      │
      ▼
Update Hireology
```

The complete hiring pipeline consists of the following steps:

1. **Screen Applicants**
   - Fetch new applicants from Hireology.
   - Validate application completeness.
   - Send reminder emails for incomplete applications.
   - Apply screening rules.

2. **Qualification**
   - Advance qualified applicants.
   - Reject unqualified applicants.
   - Send personalized rejection emails with reasons.

3. **AI Interview**
   - Automatically place an outbound AI phone call using GoHighLevel Voice AI.
   - Wait until the interview is completed.

4. **Interview Evaluation**
   - Retrieve the transcript.
   - Convert the transcript into structured Question & Answer pairs.
   - Evaluate every answer using Groq (LLaMA 3.3 70B).

5. **Hireology Update**
   - Match answers with Hireology interview questions.
   - Upload interview scores.
   - Trigger Hireology's interview scoring process.

A postponement guard prevents updating Hireology if the candidate requests a callback instead of completing the interview.

---

## Technologies Used

- Python
- Flask
- Selenium
- Groq API (LLaMA 3.3 70B)
- GoHighLevel Voice AI
- Hireology API
- JWT Authentication
- PyOTP (TOTP Authentication)
- IMAP Email Automation

---

## Integrations

### Hireology

- Applicant Tracking System
- Candidate Management
- Interview Management

### GoHighLevel Voice AI

- AI-powered outbound phone interviews
- Call management
- Transcript generation

### Groq

- LLaMA 3.3 70B
- Interview response evaluation
- Candidate scoring

Authentication tokens for both Hireology and GoHighLevel are obtained automatically through Selenium login flows (Hireology uses TOTP 2FA while GoHighLevel uses Gmail OTP verification). Tokens are cached locally and automatically refreshed whenever they expire.

---

## Project Structure

| File | Description |
|------|-------------|
| `main.py` | Main Flask application and complete hiring workflow (recommended entry point) |
| `fetch_applicants.py` | Applicant screening, validation, email handling, and status updates |
| `agent_call.py` | GoHighLevel Voice AI outbound calling |
| `formate_most_recent_callTranscript_to_Structured_json.py` | Transcript processing and Groq evaluation |
| `update_phoneInterview_on_Hireology.py` | Upload interview scores to Hireology |
| `interview_id_fetcher.py` | Fetch Hireology interview IDs |
| `applicant_id_fetcher.py` | Fetch applicant IDs |
| `Hireology_login/` | Hireology Selenium authentication |
| `GHL_login/` | GoHighLevel Selenium authentication |
| `*_need_checker.py` | Token validation |
| `*_needed.py` | Token refresh |
| `auto_monitor.py` | Continuous applicant monitoring |

> **Note:** `main.py` is the current production version. `app.py` and `flask_app.py` are older implementations retained for reference.

---

## Candidate Screening Rules

Applicants are qualified only if all of the following conditions are satisfied:

- Minimum 1 year of caregiving experience
- Valid driver's license
- Active vehicle insurance
- Able to pass a drug screening
- No criminal record
- At least two supervisor references with phone numbers

Applicants who fail any requirement are automatically rejected and receive an email explaining the reasons.

---

# Installation

## Clone Repository

```bash
git clone https://github.com/waseem0296/Hiring-AI-Agent.git

cd Hiring-AI-Agent
```

## Create Virtual Environment

Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt

pip install \
PyJWT \
selenium \
webdriver-manager \
pyotp \
imap-tools
```

---

## Requirements

- Python 3.9+
- Google Chrome
- ChromeDriver
- Groq API Key
- Hireology Account
- GoHighLevel Account

---

# Environment Variables

## Root `.env`

```env
HIREOLOGY_JOB_ID=2606114
GHL_API_KEY=your_ghl_api_key
GHL_LOCATION_ID=your_location_id
GHL_AGENT_ID=your_agent_id
GHL_FROM_PHONE=+1XXXXXXXXXX
GROQ_API_KEY=your_groq_api_key
FLASK_PORT=5000
```

---

## Hireology Login

`Hireology_login/.env`

```env
HIREOLOGY_EMAIL=your_email
HIREOLOGY_PASSWORD=your_password
TOTP_SECRET=your_totp_secret
```

---

## GoHighLevel Login

`GHL_login/.env`

```env
GHL_EMAIL=your_email
GHL_PASSWORD=your_password

GMAIL_EMAIL=your_gmail
GMAIL_APP_PASSWORD=your_gmail_app_password
```

> Gmail App Passwords are required because GoHighLevel OTP emails are retrieved automatically through Gmail.

---

# Running the Project

Start the Flask application.

```bash
python main.py
```

The server starts on

```
http://0.0.0.0:5000
```

---

## Execute Complete Hiring Workflow

```bash
curl -X POST http://localhost:5000/workflow \
-H "Content-Type: application/json" \
-d '{
"candidate_id":"48032355",
"candidate_phone":"+1XXXXXXXXXX"
}'
```

---

## Start Continuous Monitoring

```bash
curl -X POST http://localhost:5000/monitor/start \
-H "Content-Type: application/json" \
-d '{"interval":60}'
```

---

# API Endpoints

| Method | Endpoint | Purpose |
|---------|----------|---------|
| GET | `/` | Health check |
| GET | `/applicants` | Retrieve applicants |
| POST | `/screen` | Screen applicants |
| POST | `/call` | Initiate AI interview |
| POST | `/process-interview` | Evaluate latest interview |
| POST | `/update-hireology` | Upload scores |
| POST | `/workflow` | Execute complete workflow |
| GET / POST | `/monitor/status` | Monitor status |
| POST | `/monitor/start` | Start monitoring |
| POST | `/monitor/stop` | Stop monitoring |

---


The project currently contains:

- Hard-coded JWT tokens
- Cached authentication tokens
- API keys
- Private credentials
- TOTP secrets
- PEM key files

Before making the repository public:

- Rotate all API keys.
- Remove every hard-coded secret.
- Replace secrets with environment variables.
- Delete cached authentication files.
- Remove sensitive Git history.
- Set `debug=False` before deployment.

Recommended `.gitignore`

```gitignore
.env
**/.env

.jwt_cache
**/.jwt_cache

GHL_login/token_output.txt

*.pem

call_data/
logs/

__pycache__/

processed_applicants.json
workflow_results*.json
```

---

# Limitations

- Screening rules are currently tailored for caregiver recruitment.
- Interview questions are specific to the home-care industry.
- Selenium login automation depends on the current Hireology and GoHighLevel interfaces.
- UI changes in either platform may require updates to the automation scripts.
- `run_monitor.py` references a missing `app_updated` module. Use `/monitor/start` instead.

---

# Future Improvements

- Docker support
- CI/CD pipeline
- Database integration
- Multi-job support
- Dashboard for recruiters
- WebSocket live monitoring
- Analytics and reporting
- Multi-language interviews

---

# License

No license has been added yet. Consider adding an MIT or Apache 2.0 license before distributing the project publicly.
