import os
import json
import time
import PyPDF2

from dotenv import load_dotenv
from django.shortcuts import redirect, render
from django.core.files.storage import FileSystemStorage

from google import genai
from google.genai import errors

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)

def interview_home(request):
    resume_skills = []

    if request.session.get("from_resume"):
        resume_skills = request.session.get("resume_skills", [])
        request.session.pop("from_resume", None)

    if request.method == "POST":
        target_role = request.POST.get("target_role", "").strip()
        current_level = request.POST.get("current_level", "").strip()
        skills = request.POST.get("skills", "").strip()
        interview_type = request.POST.get("interview_type", "Mixed").strip()
        difficulty = request.POST.get("difficulty", "Mixed").strip()
        focus_areas = request.POST.getlist("focus")

        if not target_role or not current_level or not skills:
            return render(request, "interview_coach/interview_home.html", {
                "message": "Please fill in all the required fields.",
                "target_role": target_role,
                "current_level": current_level,
                "resume_skills": skills
            })

        resume = request.FILES.get("resume")

        if resume:
            if not resume.name.lower().endswith(".pdf"):
                return render(request, "interview_coach/interview_home.html", {
                    "message": "Only PDF files are supported.",
                    "target_role": target_role,
                    "current_level": current_level,
                    "resume_skills": skills
                })

            if resume.size > 5 * 1024 * 1024:
                return render(request, "interview_coach/interview_home.html", {
                    "message": "File size must be less than 5 MB.",
                    "target_role": target_role,
                    "current_level": current_level,
                    "resume_skills": skills
                })

        resume_text = ""

        if resume:
            fs = FileSystemStorage()
            filename = fs.save(resume.name, resume)
            file_path = fs.path(filename)

            try:
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)

                    for page in reader.pages:
                        page_text = page.extract_text()

                        if page_text:
                            resume_text += page_text

            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

        prompt = f"""
You are an expert AI Interview Coach.

Generate a personalized placement interview based on the user's profile.

User Details:

Target Role: {target_role}
Current Level: {current_level}
Skills: {skills}
Interview Type: {interview_type}
Difficulty: {difficulty}
Focus Areas: {", ".join(focus_areas)}

Resume:

{resume_text if resume_text else "No resume uploaded."}

Return ONLY valid JSON.

Do not return markdown.
Do not use ```json.
Do not add any text before or after the JSON.

Use exactly this structure:

{{
    "questions": [
        {{
            "question_number": 1,
            "type": "",
            "question": ""
        }}
    ]
}}

Rules:

- Generate exactly 8 questions.
- Questions must match the target role.
- Questions must match the user's current level.
- Use the selected focus areas.
- Keep questions realistic for a placement interview.
- Do not ask duplicate questions.
- If a resume is provided, use its skills and projects to create personalized questions.
- If no resume is provided, use the target role and skills.
- Question type must be one of:
  Technical, Project, Resume, HR.
- Keep every question concise.
"""

        data = None

        for _ in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )

                response_text = response.text.strip()

                if response_text.startswith("```"):
                    response_text = (
                        response_text
                        .replace("```json", "")
                        .replace("```", "")
                        .strip()
                    )

                data = json.loads(response_text)

                if len(data.get("questions", [])) != 8:
                    data = None
                    continue

                break

            except errors.ServerError:
                time.sleep(2)

            except json.JSONDecodeError:
                data = None
                break

            except Exception as error:
                print("AI ERROR:", error)

                if "429" in str(error):
                    break

                time.sleep(2)

        if not data:
            return render(request, "interview_coach/interview_home.html", {
                "message": "Unable to generate interview questions. Please try again.",
                "target_role": target_role,
                "current_level": current_level,
                "resume_skills": skills
            })

        request.session["interview_data"] = {
            "target_role": target_role,
            "current_level": current_level,
            "skills": skills,
            "interview_type": interview_type,
            "difficulty": difficulty,
            "focus_areas": focus_areas
        }

        request.session["interview_questions"] = data["questions"]
        request.session["current_question"] = 0

        return render(
            request,
            "interview_coach/interview.html",
            {
                "question": data["questions"][0],
                "question_number": 1,
                "total_questions": 8
            }
        )

    return render(
        request,
        "interview_coach/interview_home.html",
        {
            "resume_skills": ", ".join(resume_skills)
        }
    )

def submit_answer(request):
    if request.method != "POST":
        return redirect("interview_home")

    questions = request.session.get("interview_questions", [])
    answers = request.session.get("interview_answers", [])
    current_question = request.session.get("current_question", 0)

    answer = request.POST.get("answer", "").strip()

    if not answer:
        return render(
            request,
            "interview_coach/interview.html",
            {
                "question": questions[current_question],
                "question_number": current_question + 1,
                "total_questions": len(questions),
                "message": "Please write your answer before continuing."
            }
        )

    answers.append({
        "question": questions[current_question]["question"],
        "type": questions[current_question]["type"],
        "answer": answer
    })

    request.session["interview_answers"] = answers

    current_question += 1
    request.session["current_question"] = current_question

    if current_question < len(questions):
        return render(
            request,
            "interview_coach/interview.html",
            {
                "question": questions[current_question],
                "question_number": current_question + 1,
                "total_questions": len(questions)
            }
        )

    return render(
        request,
        "interview_coach/interview_complete.html",
        {
            "answers": answers
        }
    )