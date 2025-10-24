# Flask Server - Serves as the backend for the application

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from backend.db.db_config import SessionLocal, engine, Base
from backend.db.models import Job_Query, Scrape_Session, Job, ScrapeStatus, JobStatus
from backend.services.scrape import run_scraper

app = Flask(__name__)
CORS(app)

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
    return send_from_directory(FRONTEND_DIR, path)

# API route
@app.route("/add_job_request", methods=["POST"])
def add_job_request():
    try:
        job_data = request.get_json()
        db = SessionLocal()

        # Save query info
        new_query = Job_Query(
            date_posted=job_data.get("datePosted"),
            experience_level=job_data.get("experienceLevel"),
            job_title=job_data.get("jobTitle"),
            location=job_data.get("location"),
        )

        db.add(new_query)
        db.commit()
        db.refresh(new_query)

        # Start scrape session
        try:
            new_session = Scrape_Session(
                keywords=job_data.get("jobTitle"),
                timestamp=datetime.now(),
                status=ScrapeStatus.Running,
                log="Scrape started.",
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)

        except Exception as session_error:
            db.rollback()
            print("Error creating scrape session:", session_error)
            return (
                jsonify(
                    {"status": "error", "message": "Failed to create scrape session."}
                ),
                500,
            )

        try:
            # Run scraper
            scraped_jobs = run_scraper(
                date_posted=job_data.get("datePosted"),
                experience_level=job_data.get("experienceLevel"),
                job_title=job_data.get("jobTitle"),
                location=job_data.get("location"),
            )
            
            # Insert scraped jobs
            for job in scraped_jobs:
                new_job = Job(
                    JobTitle=job["JobTitle"],
                    Company=job["Company"],
                    Location=job["Location"],
                    URL=job["URL"],
                    Status="New",
                    DateFound=datetime.now().date(),
                )
                # check if the url in this matches any url in the table already
                temp_job = db.query(Job).filter(Job.URL == new_job.URL).first()
                
                if temp_job:
                    print("Job Already in database")
                else: # job isnt in database, we are good to go
                    db.add(new_job)
                    # save new_job to an array for testing purposes
                    jobs_saved = []
                    jobs_saved.append(new_job)
                    print(f"Saved job: {new_job.JobTitle} at {new_job.Company}")

            # status can be either, Running, Complete, or Failed
            new_session.status = ScrapeStatus.Complete
            new_session.log = (
                f"Scrape completed. Found {len(scraped_jobs)} job listings."
            )

        except Exception as scrape_error:
            new_session.status = ScrapeStatus.Failed
            new_session.log = str(scrape_error)

        db.commit()
        db.close()
        
        # open database session
        # create a dictionary to grab all the jobs from the jobs table
        # return them as a list of dictionaries
        db = SessionLocal()
        jobs_in_db = db.query(Job).all()
        jobs_saved = []
        for job in jobs_in_db:
            if job.Status == JobStatus.Ignored:
                print("Job Ignored...")
            else:
                jobs_saved.append({
                    "JobTitle": job.JobTitle,
                    "Company": job.Company,
                    "Location": job.Location,
                    "URL": job.URL,
                    "Status": job.Status,
                    "DateFound": job.DateFound.isoformat(),
                })
        db.close()
        
        print(f"Total jobs in database: {len(jobs_saved)}")  # Debugging line
        print("Jobs:", jobs_saved)  # Debugging line
        
        # return success response
        return jsonify({"status": "success", "jobs": jobs_saved}), 200
    
    except Exception as e:
        print("Error in add_job_request:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# Remove Selected Jobs API route
@app.route("/remove_jobs", methods=["POST"])
def remove_jobs():
    try:
        jobs_to_remove = request.get_json().get("jobURLs", [])
        db = SessionLocal()
        for job_url in jobs_to_remove:
            job = db.query(Job).filter(Job.URL == job_url).first()
            if job:
                job.Status = JobStatus.Ignored
                print(f"Marked job as Ignored: {job.JobTitle} at {job.Company}")
        db.commit()
        db.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Error in remove_jobs:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
     
# Refresh Jobs API route
@app.route("/refresh_jobs", methods=["GET"])
def refresh_jobs():
    try:
        db = SessionLocal()
        jobs_in_db = db.query(Job).all()
        jobs_list = []
        for job in jobs_in_db:
            jobs_list.append({
                "JobTitle": job.JobTitle,
                "Company": job.Company,
                "Location": job.Location,
                "URL": job.URL,
                "Status": job.Status,
                "DateFound": job.DateFound.isoformat(),
            })
        db.close()
        return jsonify({"status": "success", "jobs": jobs_list}), 200
    except Exception as e:
        print("Error in refresh_jobs:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    
# Get Jobs API route
@app.route("/get_jobs", methods=["GET"])
def get_jobs():
    return jsonify({"status": "success"}), 200 # this isnt likely to be used
    
if __name__ == "__main__":
    # Only for testing: drop existing tables - If actually using a persistent DB, remove this line
    Base.metadata.drop_all(bind=engine)

    # Create tables based on models
    Base.metadata.create_all(bind=engine)

    app.run(debug=True, host="0.0.0.0", port=5000)