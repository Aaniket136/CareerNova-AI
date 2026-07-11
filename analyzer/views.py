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

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def home(request):
    return render(request, 'home.html')


def upload_resume(request):
    data = None
    text = ""

    if request.method == "POST":
        file = request.FILES.get("resume")

        if file:

            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)

            # ---------------- PDF TO TEXT ---------------- #

            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)

                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text

            # Empty PDF check
            if not text.strip():
                os.remove(file_path)
                return render(request, "upload_resume.html", {
                    "message": "Unable to extract text from the uploaded PDF."
                })

            # ---------------- PROMPT ---------------- #

            prompt = f"""
            You are an ATS Resume Analyzer.

            Return ONLY valid JSON.

            Format:

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
                ]
            }}

            Rules:
            - Do NOT return markdown.
            - Do NOT use ```json
            - Return only JSON.
            - ATS score must be between 0 and 100.
            - Keep every point short (maximum one line).

            Resume:

            {text}
            """

            # ---------------- GEMINI CALL ---------------- #

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
                        "strengths": ["AI returned an invalid response."],
                        "weaknesses": [],
                        "improvements": ["Please try again."]
                    }
                    break

                except Exception:
                    time.sleep(2)

            # ---------------- FALLBACK ---------------- #

            if not data:
                data = {
                    "ats_score": 0,
                    "strengths": ["AI service is currently unavailable."],
                    "weaknesses": [],
                    "improvements": ["Please try again after some time."]
                }

            # ---------------- DELETE FILE ---------------- #

            if os.path.exists(file_path):
                os.remove(file_path)

            return render(request, "response.html", {
                "data": data
            })

    return render(request, "upload_resume.html")