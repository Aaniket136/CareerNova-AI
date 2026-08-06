import os
import json
import time

from dotenv import load_dotenv
from django.shortcuts import render
from google import genai
from google.genai import errors


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)


def career_home(request):

    if request.method == "POST":

        education = request.POST.get("education")
        skills = request.POST.get("skills")
        target_role = request.POST.get("target_role")
        current_level = request.POST.get("current_level")
        timeline = request.POST.get("timeline")

        prompt = f"""
You are an expert AI Career Coach.

Create a practical and personalized career development plan.

User Details:

Education: {education}

Current Skills: {skills}

Target Career Role: {target_role}

Current Level: {current_level}

Goal Timeline: {timeline}


Return ONLY valid JSON.

Do not return markdown.

Do not use ```json.

Do not add any text before or after the JSON.

Use exactly this structure:

{{
    "career_readiness_score": 0,

    "career_summary": "",

    "strengths": [
        ""
    ],

    "skill_gaps": [
        ""
    ],

    "priority_skills": [
        ""
    ],

    "roadmap": [
    {{
        "phase": "",
        "duration": "",
        "goal": "",

        "topics": [
            {{
                "title": "",

                "learn": [
                    ""
                ],

                "practice": [
                    ""
                ],

                "outcome": ""
            }}
        ]
    }}
],

    "weekly_plan": [
        {{
            "day": "",
            "task": ""
        }}
    ],

    "recommended_projects": [
        {{
            "name": "",
            "description": "",
            "technologies": [
                ""
            ]
        }}
    ],

    "interview_preparation": [
        ""
    ],

    "portfolio_suggestions": [
        ""
    ],

    "expected_outcome": ""
}}

Rules:

- Career readiness score must be between 0 and 100.
- Give at least 4 strengths.
- Give at least 5 skill gaps.
- Give at least 5 priority skills.

Roadmap Rules:

- If timeline is 3 Months, create exactly 3 phases:
  Month 1, Month 2, Month 3.

- If timeline is 6 Months, create exactly 3 phases:
  Months 1-2, Months 3-4, Months 5-6.

- If timeline is 9 Months, create exactly 3 phases:
  Months 1-3, Months 4-6, Months 7-9.

- If timeline is 12 Months, create exactly 4 phases:
  Months 1-3, Months 4-6, Months 7-9, Months 10-12.

- Each phase must contain exactly 3 topics.

- Each topic must contain:
  a short title,
  exactly 3 learning points,
  exactly 2 practice tasks,
  and one short expected outcome.

- Keep all points concise and practical.

- Make the roadmap realistic for the user's current level,
  skills, target role and selected timeline.
"""

        data = None

        for _ in range(3):

            try:

                response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
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

                break

            except errors.ServerError:

                time.sleep(2)

            except json.JSONDecodeError:

                data = {
                    "career_readiness_score": 0,
                    "career_summary": "AI returned an invalid response.",
                    "strengths": [],
                    "skill_gaps": [],
                    "priority_skills": [],
                    "roadmap": [],
                    "weekly_plan": [],
                    "recommended_projects": [],
                    "interview_preparation": [],
                    "portfolio_suggestions": [],
                    "expected_outcome": "Please try again."
                }

                break

            except Exception as e:

                print("AI ERROR:", e)

                if "429" in str(e):

                    data = {
                        "career_readiness_score": 0,
                        "career_summary": "AI request limit reached. Please try again after a minute.",
                        "strengths": [],
                        "skill_gaps": [],
                        "priority_skills": [],
                        "roadmap": [],
                        "weekly_plan": [],
                        "recommended_projects": [],
                        "interview_preparation": [],
                        "portfolio_suggestions": [],
                        "expected_outcome": "Please wait for a minute and try again."
                    }

                    break

                time.sleep(2)


        if not data:

            data = {
                "career_readiness_score": 0,
                "career_summary": "AI service is currently unavailable.",
                "strengths": [],
                "skill_gaps": [],
                "priority_skills": [],
                "roadmap": [],
                "weekly_plan": [],
                "recommended_projects": [],
                "interview_preparation": [],
                "portfolio_suggestions": [],
                "expected_outcome": "Please try again after some time."
            }

        request.session["career_roadmap"] = data.get("roadmap", [])

        request.session.pop("resume_skills", None)
        return render(
            request,
            "career_coach/career_result.html",
            {
                "data": data
            }
        )


    resume_skills = request.session.get(
    "resume_skills",
    []
    )

    return render(
        request,
        "career_coach/career_home.html",
        {
            "resume_skills": ", ".join(resume_skills)
        }
    )
def roadmap_detail(request):

    roadmap = request.session.get(
        "career_roadmap",
        []
    )

    return render(
        request,
        "career_coach/roadmap_detail.html",
        {
            "roadmap": roadmap
        }
    )