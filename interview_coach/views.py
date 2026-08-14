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


def is_meaningful_answer(answer):
    answer = answer.strip().lower()

    if not answer:
        return False

    invalid_answers = {
        "a",
        "aa",
        "abc",
        "xyz",
        "test",
        "testing",
        "a1",
        "a2",
        "a3",
        "a4",
        "a5",
        "a6",
        "a7",
        "a8",
        "none",
        "nothing",
        "no",
        "n/a",
        "na"
    }

    if answer in invalid_answers:
        return False

    # Very short answers
    if len(answer) < 10:
        return False

    # Answer containing almost no letters
    letters = sum(char.isalpha() for char in answer)

    if letters < 5:
        return False

    return True

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

        # NEW INTERVIEW STARTS HERE
        # Clear answers from previous interview
        request.session["interview_answers"] = []

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
    interview_data = request.session.get("interview_data", {})

    if not questions or current_question >= len(questions):
        return redirect("interview_home")

    answer = request.POST.get("answer", "").strip()

    if not answer:
        return render(request, "interview_coach/interview.html", {
            "question": questions[current_question],
            "question_number": current_question + 1,
            "total_questions": len(questions),
            "message": "Please write your answer before continuing."
        })

    meaningful = is_meaningful_answer(answer)

    answers.append({
        "question": questions[current_question]["question"],
        "type": questions[current_question]["type"],
        "answer": answer,
        "meaningful": meaningful
    })

    request.session["interview_answers"] = answers
    current_question += 1
    request.session["current_question"] = current_question
    request.session.modified = True

    if current_question < len(questions):
        return render(request, "interview_coach/interview.html", {
            "question": questions[current_question],
            "question_number": current_question + 1,
            "total_questions": len(questions)
        })

    evaluation_prompt = f"""
You are an expert placement interview evaluator.

Candidate Profile:
Target Role: {interview_data.get("target_role", "")}
Current Level: {interview_data.get("current_level", "")}
Skills: {interview_data.get("skills", "")}
Interview Type: {interview_data.get("interview_type", "")}
Difficulty: {interview_data.get("difficulty", "")}

Interview Answers:
{json.dumps(answers, indent=2)}

Return ONLY valid JSON. Do not return markdown. Do not use ```json. Do not add any text before or after the JSON.

Use exactly this structure:
{{
    "evaluations": [
        {{
            "question": "",
            "ideal_answer": "",
            "score": 0,
            "feedback": "",
            "strengths": [],
            "improvement": ""
        }}
    ],
    "overall_score": 0,
    "technical_score": 0,
    "communication_score": 0,
    "confidence_score": 0,
    "summary": "",
    "strengths": [],
    "improvements": []
}}

Rules:
- Evaluate every question.
- Return exactly one evaluation for every question.
- Score must be between 0 and 10.
- Give an ideal interview-quality answer.
- Ideal answer should normally be 2 to 4 sentences.
- Feedback should normally be 1 to 2 sentences.
- Keep strengths and improvements concise.
- Technical answers must be factually correct.
- Project and Resume answers should be realistic and relevant.
- HR answers should be professional and natural.
- Focus on correctness, relevance, clarity, structure and interview quality.
- If an answer is blank, meaningless, random text, placeholder text or does not attempt to answer the question, its score MUST be 0.
- Never give strengths for a meaningless answer.
- For meaningless answers, feedback must clearly say that no meaningful answer was provided.
- The ideal_answer should still contain the correct answer.
- Improvement should explain how the candidate should answer the question.
- Overall score must be between 0 and 100.
- Technical, communication and confidence scores must be between 0 and 100.
- Scores must be based only on the candidate's actual answers.
- Do not use random or fixed scores.
- Summary must contain only 2 or 3 concise sentences.
- Strengths must contain exactly 3 short points.
- Improvements must contain exactly 3 short points.
"""

    evaluation_data = None

    for _ in range(3):
        try:
            response = client.models.generate_content(model="gemini-2.5-flash", contents=evaluation_prompt)
            response_text = response.text.strip()

            if response_text.startswith("```"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            evaluation_data = json.loads(response_text)

            if len(evaluation_data.get("evaluations", [])) != len(answers):
                evaluation_data = None
                continue

            break

        except errors.ServerError:
            time.sleep(2)

        except json.JSONDecodeError:
            evaluation_data = None
            break

        except Exception as error:
            print("AI EVALUATION ERROR:", error)

            if "429" in str(error):
                break

            time.sleep(2)

    if evaluation_data:
        evaluations = evaluation_data["evaluations"]

        for answer_item, evaluation in zip(answers, evaluations):
            answer_item["ideal_answer"] = evaluation.get("ideal_answer", "")

            if answer_item.get("meaningful", False):
                answer_item["score"] = evaluation.get("score", 0)
                answer_item["feedback"] = evaluation.get("feedback", "")
                answer_item["strengths"] = evaluation.get("strengths", [])
                answer_item["improvement"] = evaluation.get("improvement", "")
            else:
                answer_item["score"] = 0
                answer_item["feedback"] = "No meaningful answer was provided."
                answer_item["strengths"] = []
                answer_item["improvement"] = "Provide a relevant and complete answer to the question."

        request.session["interview_answers"] = answers

        valid_scores = [item["score"] for item in answers if item.get("meaningful", False)]

        if valid_scores:
            overall_score = round((sum(valid_scores) / len(valid_scores)) * 10)
            technical_score = evaluation_data.get("technical_score", 0)
            communication_score = evaluation_data.get("communication_score", 0)
            confidence_score = evaluation_data.get("confidence_score", 0)
        else:
            overall_score = 0
            technical_score = 0
            communication_score = 0
            confidence_score = 0

        request.session["interview_result"] = {
            "overall_score": overall_score,
            "technical_score": technical_score,
            "communication_score": communication_score,
            "confidence_score": confidence_score,
            "summary": evaluation_data.get("summary", ""),
            "strengths": evaluation_data.get("strengths", []) if valid_scores else [],
            "improvements": evaluation_data.get("improvements", [])
        }

    else:
        request.session["interview_result"] = {
            "overall_score": 0,
            "technical_score": 0,
            "communication_score": 0,
            "confidence_score": 0,
            "summary": "Unable to generate the interview evaluation. Please try again.",
            "strengths": [],
            "improvements": []
        }

    request.session.modified = True

    return render(request, "interview_coach/interview_complete.html", {
        "answers": answers,
        "data": request.session.get("interview_result", {})
    })

def interview_complete(request):
    answers = request.session.get("interview_answers", [])
    data = request.session.get("interview_result", {})

    return render(
        request,
        "interview_coach/interview_complete.html",
        {
            "answers": answers,
            "data": data
        }
    )

def interview_answers(request):
    answers = request.session.get("interview_answers", [])

    return render(
        request,
        "interview_coach/interview_answers.html",
        {
            "answers": answers
        }
    )