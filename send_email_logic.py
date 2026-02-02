
import requests
def send_incomplete_application_email(
    jwt_token,
    candidate_job_id,
    candidate_email,
    job_id,
    job_name,
    incomplete_questions
):
    """
    Send incomplete application email to candidate.
    Returns True if successful, False otherwise.
    """
    url = "https://api.hireology.com/v2/emails/send_single_email"

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "*/*"
        # DO NOT set Content-Type manually
    }

    questions_html = "".join(
        f"<li>{q}</li>" for q in incomplete_questions
    )

    email_body = f"""
    <p>Dear Applicant,</p>

    <p>Your application for <strong>{job_name}</strong> is incomplete.</p>

    <p>Please complete the following required information:</p>

    <ul>
        {questions_html}
    </ul>

    <p>Once completed, your application will proceed for further review.</p>

    <p>Thank you,<br>Hiring Team</p>
    """

    data = {
    "candidate_job_ids[]": str(candidate_job_id),
    "user[email_to]": candidate_email,
    "user[email_from]": "basil@dawsonhomecare.com",
    "user[email_subject]": "Incomplete Application – Action Required",
    "user[email_body]": email_body.strip(),
    "jobId": str(job_id),
    "filter_by_job": "false",
    "email_type": "custom"
    }


    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            timeout=30
        )

        print(f"Email POST status: {response.status_code}")
        print(f"Response: {response.text}")

        # Check if email was sent successfully
        if response.ok:
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ Email sending failed with exception: {e}")
        return False
if __name__ == "__main__":
    jwt_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlFZdWgwSmFGcGpmanZJTWJMNGctYXhpdmttazgyaHQ5RlMwazd4Sk5JR2MiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJiMWUwZTc4Yy05MGU3LTQxOTgtOTU5NC0zMDI3ZWZkN2Y3MTAiLCJpc3MiOiJodHRwczovL2FjY291bnRzLmhpcmVvbG9neS5jb20vNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyL3YyLjAvIiwiZXhwIjoxNzY5NzE1Nzg3LCJuYmYiOjE3Njk3MTIxODcsInN1YiI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm9pZCI6IjIzMGE5NjZhLTc4Y2ItNGMzOS1hZGEzLTdlODkyNWNjNmQ5MSIsIm1mYSI6dHJ1ZSwiYXpmcCI6dHJ1ZSwidGlkIjoiNDZlODJkZWEtOTFmNC00ZDMwLWFhYmMtYWMxZWUwMzBiZWMyIiwia21zaSI6IkZhbHNlIiwic2NwIjoidjIgYWkgdjMiLCJhenAiOiJmMDY3ZTZhMy04MTVkLTQxM2QtODc4ZS1kMjIzZWZhYTBjYTQiLCJ2ZXIiOiIxLjAiLCJpYXQiOjE3Njk3MTIxODd9.St9DS_GztlE_-NQf8aDuQJktnmzYk5prfhtN_yKrZ0JCIGoTSuHsm3oXMcybhuMlnxy8UDUEw2tARnGL81qamSFK7eHCCcylVG2igqtYi9RmUh8rQAIMFq67vCGLGjDCGHFIML-6bnxdQuO5ZFsvP69L-CBf-0-LtBNPyt0_QC81nqChF7VSs_wR2chJTXxmHUUlA7DCEQypPpymecd6t9EA2GJkwevP-nG78unUnlvMiNRQsEaB2jbHMyXXjgY54wOyFOmimSwQ3KU9MwgPHSetR235YDFsqL9TTig8o7ZCPCn1RCCD378A1nIoEtlotGz8uj1OtWjAYPP88gFNSw"
    candidate_job_id = "58844113"
    candidate_email = "waseemofficial5862@gmail.com"
    job_id = "2606114"
    job_name = "Job Simulation Please Dont Use this (TEST)"
    incomplete_questions = ["[2]testing questions","[1]another one"]
    send_incomplete_application_email(jwt_token, candidate_job_id, candidate_email, job_id, job_name, incomplete_questions)