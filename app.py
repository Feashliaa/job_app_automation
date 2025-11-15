# Flask Server - Serves as the backend for the application

from flask import Flask, send_from_directory, request, jsonify, session, abort
from flask_cors import CORS
from datetime import datetime
from pdfminer.high_level import extract_text
import os
import re
from backend.db.db_config import SessionLocal, engine, Base
from backend.db.models import (
    Job_Query,
    Scrape_Session,
    Job,
    ScrapeStatus,
    JobStatus,
    User,
)
from backend.services.scrape import run_scraper
from backend.services.utils import sanitize_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE_MB = 5

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax", # or "Strict", set this according to whether cross-site cookies are needed
    SESSION_COOKIE_SECURE=True,  # if HTTPS
    SESSION_PERMANENT=True, # make the session permanent, persists after browser close
    PERMANENT_SESSION_LIFETIME=3600,  # session lifetime in seconds, i.e. 1 hour
)
CORS(app, supports_credentials=True)

# Dynamically resolve the frontend folder path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Serve index.html
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

# Serve static assets (JS, CSS, etc.)
@app.route("/<path:path>")
def serve_static_files(path):
    if not path.endswith((".js", ".css", ".html", ".png", ".jpg", ".ico")):
        abort(404)
    return send_from_directory(FRONTEND_DIR, path)

# API route
@app.route("/add_job_request", methods=["POST"])
def add_job_request():
    db = SessionLocal() # create a new session
    try: 
        job_data = request.get_json() # get the job data from the request
        user_email = session.get("user") # get the logged-in user's email
        if not user_email:
            return jsonify({"error": "User not logged in"}), 401

        # get and parse user's resume
        parsed_resume = get_user_parsed_resume(db, user_email)
        scrape_params = extract_scrape_params(job_data)
        scraped_jobs = run_scraper(**scrape_params)

        query = create_job_query(db, job_data)
        db.flush()  # ensure query_id exists before use

        session_entry = create_scrape_session(
            db, query.query_id, job_data.get("jobTitle"), user_email
        )
        db.flush()

        insert_scraped_jobs(
            db, scraped_jobs, session_entry.scrape_session_id, user_email, parsed_resume
        )

        finalize_scrape_session(
            db, session_entry, ScrapeStatus.Complete, len(scraped_jobs)
        )

        db.commit()  # commit

        jobs_saved = get_new_jobs(db, user_email) # get newly saved jobs
        return jsonify({"status": "success", "jobs": jobs_saved}), 200

    except Exception as e:
        db.rollback()
        print("Error in add_job_request:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()

def get_user_parsed_resume(db, email):
    # Retrieve and parse the user's resume file.
    user = db.query(User).filter_by(email=email).first()

    if not user or not user.resume_path: 
        return None
    
    try:
        return resume_parse(user.resume_path, user.resume_name)
    except Exception as e:
        print(f"Error parsing resume for {email}: {e}")
        return None

def create_job_query(db, data):
    # Create and store a Job_Query entry.
    query = Job_Query(
        date_posted=data.get("datePosted"),
        experience_level=data.get("experienceLevel"),
        job_title=data.get("jobTitle"),
        location=data.get("location"),
    )
    db.add(query)
    return query

def create_scrape_session(db, query_id, keywords, email):
    # Start a new scrape session entry.
    session_entry = Scrape_Session(
        query_id=query_id,
        keywords=keywords,
        timestamp=datetime.now(),
        status=ScrapeStatus.Running,
        log="Scrape started.",
        user_email=email,
    )
    db.add(session_entry) 
    return session_entry

def extract_scrape_params(data):
    # Extract scraper parameters from request data.
    return {
        "date_posted": data.get("datePosted"),
        "experience_level": data.get("experienceLevel"),
        "job_title": data.get("jobTitle"),
        "location": data.get("location"),
    }

def insert_scraped_jobs(db, scraped_jobs, session_id, user_email, parsed_resume):
    # Insert all scraped jobs into the database with calculated job scores.
    
    has_resume = parsed_resume is not None
    
    for job in scraped_jobs:
        # Skip duplicates
        existing = (
            db.query(Job)
            .filter_by(URL=job["URL"], user_email=user_email)
            .first()
        )
        if existing:
            continue

        # Compute resume-based score
        if has_resume:
            job_score = calculate_job_score(parsed_resume, job)
        else:
            job_score = None

        new_job = Job(
            JobTitle=job["JobTitle"],
            Company=job["Company"],
            Location=job["Location"],
            Salary=job["Salary"],
            URL=job["URL"],
            Status=JobStatus.New,
            DateFound=datetime.now().date(),
            scrape_session_id=session_id,
            user_email=user_email,
            job_score=job_score,
        )
        db.add(new_job)

def finalize_scrape_session(db, session_entry, status, total):
    # Finalize the scrape session with status and job count.
    session_entry.status = status
    session_entry.log = f"Scrape completed. Found {total} job listings."

# Get New Jobs for API response
def get_new_jobs(db, user_email):
    # Return recently scraped jobs formatted for API response.
    jobs = ( 
        db.query(Job)
        .filter(Job.Status == JobStatus.New, Job.user_email == user_email)
        .order_by(Job.DateFound.desc())
        .all()
    )
    return [
        {
            "JobTitle": job.JobTitle,
            "Company": job.Company,
            "Location": job.Location,
            "Salary": job.Salary,
            "URL": job.URL,
            "Status": job.Status,
            "DateFound": str(job.DateFound),
            "JobScore": job.job_score if job.job_score is not None else "N/A",
        }
        for job in jobs
    ]

# Require Login
def require_login():
    if "user" not in session:
        return jsonify({"error": "Login required"}), 401
    return None

# Remove Selected Jobs API route
@app.route("/remove_jobs", methods=["POST"])
def remove_jobs():
    if (resp := require_login()):
        return resp
    try: # mark jobs as ignored
        jobs_to_remove = request.get_json().get("jobURLs", [])
        db = SessionLocal()
        for job_url in jobs_to_remove:
            job = (
                db.query(Job)
                .filter(Job.URL == job_url, Job.user_email == session["user"])
                .first()
            )
            if job:
                job.Status = JobStatus.Ignored
                print(f"Marked job as Ignored: {job.JobTitle} at {job.Company}")
        db.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.rollback()
        print("Error in remove_jobs:", e)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        db.close()

# Apply To Jobs API route - Place holder for just changing status
@app.route("/apply_jobs", methods=["POST"])
def apply_jobs():
    if (resp := require_login()):
        return resp
    try: # mark jobs as applied
        jobs_to_apply = request.get_json().get("jobURLs", [])
        db = SessionLocal()
        for job_url in jobs_to_apply:
            job = (
                db.query(Job)
                .filter(Job.URL == job_url, Job.user_email == session["user"])
                .first()
            )
            if job:
                job.Status = JobStatus.Applied
                print(f"Marked job as Applied: {job.JobTitle} at {job.Company}")
        db.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.rollback()
        print("Error in apply_jobs:", e)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        db.close()

# Refresh Jobs API route
@app.route("/refresh_jobs", methods=["GET"])
def refresh_jobs():
    if (resp := require_login()):
        return resp
    try:
        user_email = session.get("user")
        db = SessionLocal()
        jobs_in_db = db.query(Job).filter(Job.user_email == user_email).all()
        jobs_list = []
        for job in jobs_in_db:
            jobs_list.append(
                {
                    "JobTitle": job.JobTitle,
                    "Company": job.Company,
                    "Location": job.Location,
                    "Salary": job.Salary,
                    "URL": job.URL,
                    "Status": job.Status,
                    "DateFound": str(job.DateFound),
                    "JobScore": job.job_score if job.job_score is not None else "N/A",
                }
            )
        return jsonify({"status": "success", "jobs": jobs_list}), 200
    except Exception as e:
        print("Error in refresh_jobs:", e)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        db.close()

# Resume upload handling
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS # check extension

@app.before_request
def limit_upload_size():
    if request.content_length and request.content_length > MAX_FILE_SIZE_MB * 1024 * 1024:
        abort(413, description="File too large")

# Resume handler API route
@app.route("/resume_handler", methods=["POST"])
def resume_handler():
    if (resp := require_login()):
        return resp

    file = request.files.get("resumeFile")
    if not file or not file.filename:
        return jsonify({"error": "No file uploaded"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    safe_filename = sanitize_filename(file.filename)
    file_path = os.path.join(upload_dir, safe_filename)
    
    file.save(file_path)

    user_email = session.get("user")
    db = SessionLocal()

    try:
        user = db.query(User).filter_by(email=user_email).first()
        if user:
            user.resume_name = safe_filename
            user.resume_path = os.path.join("uploads", safe_filename)
            db.commit()

        parsed_resume = resume_parse(file_path, safe_filename)
        return jsonify(parsed_resume)

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.rollback()
        print("Resume handler error:", e)
        return jsonify({"error": "Internal server error"}), 500

    finally:
        db.close()

# Resume parsing function
def resume_parse(file_path, filename):
    """Extract and structure key resume sections."""
    text = extract_text(file_path)

    # Split sections by flexible headings (case-insensitive)
    sections = re.split(
        r"(?i)(?:Professional Summary:?|Summary:?|Technical Skills:?|Skills:?|Experience:?|"
        r"Academic & Independent Projects:?|Projects:?|Education:?)",
        text,
    )

    # Pad for safety
    while len(sections) < 6:
        sections.append("")

    data = {
        "summary": sections[1].strip(),
        "skills": sections[2].strip(),
        "experience": sections[3].strip(),
        "projects": sections[4].strip(),
        "education": sections[5].strip(),
    }

    # Parse "Technical Skills" section into dict
    skills = {}
    for line in data["skills"].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            skills[key.strip()] = [s.strip() for s in value.split(",") if s.strip()]

    return {
        "status": "ok",
        "filename": filename,
        "summary": data["summary"],
        "skills": skills,
        "experience": data["experience"],
        "projects": data["projects"],
        "education": data["education"],
    }

# Job score calculation function, using TF-IDF and keyword overlap
def calculate_job_score(parsed_resume, job):
    """Compute job fit score using TF-IDF + keyword overlap."""
    
    if not parsed_resume:
        return 0.0

    skills_dict = parsed_resume.get("skills") or {}
    job_title = job.get("JobTitle", "")
    job_text_raw = f"{job.get('Skills', '')} {job.get('Description', '')}"

    # Combine resume text sections for stronger context, lowercased
    resume_text = (
        " ".join(
            f"{category} {' '.join(skills)}"
            for category, skills in skills_dict.items()
        )
        + " "
        + parsed_resume.get("summary", "")
        + " "
        + parsed_resume.get("experience", "")
        + " "
        + parsed_resume.get("projects", "")
    ).lower()

    job_text = f"{job_title} {job_text_raw}".lower() # combined job text

    def clean(s): # remove non-letters
        return re.sub(r"[^a-z\s]", " ", s)

    resume_text, job_text = clean(resume_text), clean(job_text) # clean texts

    if not resume_text.strip() or not job_text.strip(): # empty check
        return 0.0

    # TF-IDF cosine similarity
    vectorizer = TfidfVectorizer(stop_words="english") # init vectorizer
    tfidf = vectorizer.fit_transform([resume_text, job_text]) # fit + transform
    cosine_score = float(cosine_similarity(tfidf)[0, 1]) # get cosine sim

    # Keyword overlap
    resume_words = set(resume_text.split()) # unique words in resume
    job_words = set(job_text.split()) # unique words in job
    overlap_ratio = len(resume_words & job_words) / (len(job_words) or 1) # overlap ratio

    # Blend + scale
    blended = (cosine_score * 0.7) + (overlap_ratio * 0.3) # weighted blend
    return round(min(blended * 200, 100), 2) # scale to 0-100

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return jsonify({"error": "User doesn't Exist"}), 404
        if not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid Password"}), 401

        session["user"] = user.email
        return jsonify({"status": "success", "user": user.email}), 200

    except Exception as e:
        print("Login Error: ", e)
        return jsonify({"error": "Login Failed"}), 500
    finally:
        db.close()
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True) # get the data from the request
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first() # check if user exists
        if existing:
            return jsonify({"error": "User already exists"}), 400

        # otherwise, new user, hash the password
        hashed_slinging_slasher = generate_password_hash(password)

        new_user = User(email=email, password_hash=hashed_slinging_slasher) 
        db.add(new_user)
        db.commit()

        session["user"] = new_user.email # log in the new user

        return jsonify({"status": "success", "user": email}), 200
    except Exception as e:
        db.rollback()
        print("Registration Error: ", e)
        return jsonify({"error": "Registration Error"}), 500
    finally:
        db.close()

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"status": "logged_out"}), 200

@app.route("/session_status")
def session_status():
    user = session.get("user")
    if user:
        return jsonify({"logged_in": True, "user": user})
    return jsonify({"logged_in": False})

# backend/server.py
if __name__ == "__main__":
    assert app.secret_key != "dev-secret", "SECRET_KEY must be set in environment"
    app.run(host="0.0.0.0", port=5000)