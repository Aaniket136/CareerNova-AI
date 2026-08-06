import os
import json
import time

from dotenv import load_dotenv
import PyPDF2

from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

from google import genai
from google.genai import errors


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)


def home(request):
    return render(request, "home.html")


def upload_resume(request):

    data = None
    text = ""

    if request.method == "POST":

        file = request.FILES.get("resume")

        if file:

            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)

            #  PDF TO TEXT 

            with open(file_path, "rb") as f:

                reader = PyPDF2.PdfReader(f)

                for page in reader.pages:

                    page_text = page.extract_text()

                    if page_text:
                        text += page_text


            # EMPTY TEXT CHECK

            if not text.strip():

                if os.path.exists(file_path):
                    os.remove(file_path)

                return render(
                    request,
                    "upload_resume.html",
                    {
                        "message": "Unable to extract text from the uploaded PDF."
                    }
                )


            # AI PROMPT 

            prompt = f"""
You are an ATS Resume Analyzer.

Analyze the resume and return ONLY valid JSON.

Do not return markdown.
Do not use ```json.
Do not add any text before or after the JSON.

Use exactly this format:

{{
    "ats_score": 0,

    "strengths": [
        "point"
    ],

    "weaknesses": [
        "point"
    ],

    "improvements": [
        "point"
    ],

    "skills": [
        "Python",
        "Django"
    ]
}}

Rules:

- ATS score must be between 0 and 100.
- Give concise and practical strengths.
- Give concise and practical weaknesses.
- Give actionable resume improvements.
- Extract technical and professional skills explicitly mentioned in the resume.
- Do not add skills that are not present in the resume.
- Return skills as clean individual names.
- Keep every point short.

Resume:

{text}
"""


            #  AI REQUEST

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

                    break


                except errors.ServerError:

                    time.sleep(2)


                except json.JSONDecodeError:

                    data = {
                        "ats_score": 0,
                        "strengths": [
                            "AI returned an invalid response."
                        ],
                        "weaknesses": [],
                        "improvements": [
                            "Please try again."
                        ],
                        "skills": []
                    }

                    break


                except Exception as error:

                    print("AI ERROR:", error)

                    time.sleep(2)


            # FALLBACK 

            if not data:

                data = {
                    "ats_score": 0,
                    "strengths": [
                        "AI service is currently unavailable."
                    ],
                    "weaknesses": [],
                    "improvements": [
                        "Please try again after some time."
                    ],
                    "skills": []
                }


            # SAVE RESUME SKILLS 

            request.session["resume_skills"] = data.get(
                "skills",
                []
            )


            #  DELETE UPLOADED FILE 

            if os.path.exists(file_path):
                os.remove(file_path)


            # SHOW RESPONSE 

            return render(
                request,
                "response.html",
                {
                    "data": data
                }
            )


    return render(
        request,
        "upload_resume.html"
    )