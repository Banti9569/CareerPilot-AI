from flask import Flask, render_template, request, redirect, session
from google import genai
from dotenv import load_dotenv
import sqlite3
import os
import json
import markdown
from PyPDF2 import PdfReader

app = Flask(__name__)
load_dotenv()

app.secret_key = "careerpilot_secret_key_2026"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

model_name = "gemini-3.6-flash"

import time

def generate_ai(prompt):
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text

        except Exception as e:
            print(f"Gemini attempt {attempt + 1} failed:", e)

            if attempt < 2:
                time.sleep(5)
            else:
                raise e

SKILLS = [
    "Python",
    "Java",
    "C",
    "C++",
    "SQL",
    "MySQL",
    "Flask",
    "FastAPI",
    "HTML",
    "CSS",
    "JavaScript",
    "React",
    "Git",
    "GitHub",
    "Linux",
    "Docker",
    "Machine Learning",
    "Deep Learning",
    "Artificial Intelligence",
    "TensorFlow",
    "PyTorch",
    "Data Science",
    "Pandas",
    "NumPy",
    "OpenCV"
]

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("database/database.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM user WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        connection.close()

        if user:
           session["user_name"] = user[1]
           session["user_email"] = user[2]

           return redirect("/dashboard")

        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("database/database.db")
        cursor = connection.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            connection.close()
            return "Email already exists. Please login."

        cursor.execute(
            "INSERT INTO user (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )

        connection.commit()
        connection.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "user_name" not in session:
        return redirect("/login")
    
    return render_template(
        "dashboard.html",
        name=session["user_name"]

    )

@app.route("/resume", methods=["GET", "POST"])
def resume():

    if "user_name" not in session:
        return redirect("/login")

    extracted_text = ""
    found_skills = []

    ats_score = 0
    strengths = []
    weaknesses = []
    missing_skills = []
    suggestions = []
    job_roles = []
    error_message = ""

    if request.method == "POST":

        file = request.files.get("resume")

        if file and file.filename != "":

            filepath = os.path.join("uploads", "resumes", file.filename)
            file.save(filepath)

            with open(filepath, "rb") as pdf_file:

                reader = PdfReader(pdf_file)

                for page in reader.pages:

                    text = page.extract_text()

                    if text:
                        extracted_text += text + "\n"

            prompt = f"""
You are an expert ATS Resume Reviewer.

Return ONLY valid JSON.

{{
    "ats_score": 0,
    "strengths": [],
    "weaknesses": [],
    "missing_skills": [],
    "suggestions": [],
    "job_roles": []
}}

Resume:

{extracted_text}
"""

            try:

                ai_text = generate_ai(prompt)

                print(ai_text)
                ai_text = ai_text.replace("```json", "").replace("```", "").strip()

                ai_data = json.loads(ai_text)

                ats_score = ai_data.get("ats_score", 0)
                strengths = ai_data.get("strengths", [])
                weaknesses = ai_data.get("weaknesses", [])
                missing_skills = ai_data.get("missing_skills", [])
                suggestions = ai_data.get("suggestions", [])
                job_roles = ai_data.get("job_roles", [])

            except Exception as e:

               print("Gemini Error:", e)

               error_message = "⚠️ AI service is temporarily unavailable. Please try again after a few minutes."

        resume_lower = extracted_text.lower()

        for skill in SKILLS:

            if skill.lower() in resume_lower:
                found_skills.append(skill)

        if not missing_skills:

            for skill in SKILLS:

                if skill not in found_skills:
                    missing_skills.append(skill)

    return render_template(
        "resume.html",
        extracted_text=extracted_text,
        skills=found_skills,
        ats_score=ats_score,
        strengths=strengths,
        weaknesses=weaknesses,
        missing_skills=missing_skills,
        suggestions=suggestions,
        job_roles=job_roles,
        error_message=error_message
)

@app.route("/career", methods=["GET", "POST"])
def career():

    if "user_name" not in session:
        return redirect("/login")

    career_data = {}
    error_message = ""

    if request.method == "POST":

        name = request.form["name"]
        degree = request.form["degree"]
        skills = request.form["skills"]
        interests = request.form["interests"]
        goal = request.form["goal"]

        prompt = f"""
You are an expert AI Career Advisor.

Return ONLY valid JSON.

{{
  "career_path":"",
  "job_roles":[
    "",
    ""
  ],
  "skills_to_learn":[
    "",
    ""
  ],
  "expected_salary":"",
  "roadmap":[
    "",
    "",
    "",
    "",
    "",
    ""
  ],
  "final_advice":""
}}

Student Details

Name: {name}

Degree: {degree}

Skills: {skills}

Interests: {interests}

Career Goal: {goal}
"""

        try:

            print("CALLING GEMINI...")

            ai_text = generate_ai(prompt)

            print("GEMINI CALL FINISHED")

            print("\n========== GEMINI RESPONSE ==========")
            print(ai_text)
            print("=====================================\n")

            ai_text = ai_text.replace("```json", "").replace("```", "").strip()

            career_data = json.loads(ai_text)
            print(career_data)

        except Exception as e:

          print("ERROR:", e)

          error_message = "⚠️ AI service is temporarily unavailable. Please try again after a few minutes."

          career_data = {
               "career_path": "",
               "job_roles": [],
               "skills_to_learn": [],
               "expected_salary": "",
               "roadmap": [],
               "final_advice": ""
            }

    return render_template(
    "career.html",
    career_data=career_data,
    error_message=error_message
)


@app.route("/interview", methods=["GET", "POST"])
def interview():

    if "user_name" not in session:
        return redirect("/login")

    interview_data = {}
    error_message = ""

    if request.method == "POST":

        job_role = request.form["job_role"]
        experience = request.form["experience"]
        interview_type = request.form["interview_type"]

        prompt = f"""
You are an expert Technical and HR Interview Coach.

Return ONLY valid JSON.

{{

  "questions": [
    "",
    "",
    "",
    "",
    ""
  ],
  "answers": [
    "",
    "",
    "",
    "",
    ""
  ],
  "tips": [
    "",
    "",
    "",
    "",
    ""
  ]
}}

Job Role: {job_role}
Experience: {experience}
Interview Type: {interview_type}
"""

        try:

            ai_text = generate_ai(prompt)

            ai_text = ai_text.replace("```json", "").replace("```", "").strip()

            interview_data = json.loads(ai_text)


        except Exception as e:

               print("ERROR:", e)

               error_message = f"⚠️ AI Error: {str(e)}"

               interview_data = {
                     "questions": [],
                     "answers": [],
                     "tips": []
    }
    return render_template(
        "interview.html",
         interview_data=interview_data,
         error_message=error_message
    )


@app.route("/roadmap", methods=["GET", "POST"])
def roadmap():

    if "user_name" not in session:
        return redirect("/login")

    roadmap_data = {}

    if request.method == "POST":

        career = request.form["career"]
        level = request.form["level"]
        hours = request.form["hours"]

        prompt = f"""
You are an expert Software Engineering Mentor.

Return ONLY valid JSON.

{{
  "target_career": "",
  "skills": ["", "", "", "", ""],
  "roadmap": ["", "", "", "", "", ""],
  "youtube": ["", "", ""],
  "websites": ["", "", ""],
  "practice": ["", "", ""],
  "projects": ["", "", ""],
  "final_advice": ""
}}

Target Career: {career}
Current Level: {level}
Study Hours Per Day: {hours}
"""

        try:
           ai_text = generate_ai(prompt)
           ai_text = ai_text.replace("```json", "").replace("```", "").strip()
           roadmap_data = json.loads(ai_text)

        except Exception as e:

              print("Gemini Error:", e)

              roadmap_data = {}
       

    return render_template(
        "roadmap.html",
        roadmap_data=roadmap_data
    )



@app.route("/logout")
def logout():

    session.clear()
    return redirect("/login")


    

if __name__ == "__main__":
    app.run(debug=True)