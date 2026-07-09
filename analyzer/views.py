import os
import json
import time
from dotenv import load_dotenv
import PyPDF2
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from google import genai
from google.api_core import exceptions

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def home(request):
    return render(request, 'home.html')


def upload_resume(request):
    data = None
    text = ""

    if request.method == 'POST':
        file = request.FILES.get('resume')

        if file:
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)
            # 1. PDF → TEXT
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
            # 2. PROMPT
            prompt = f"""
            You are an ATS Resume Analyzer.

            Return ONLY valid JSON:

            {{
            "ats_score": 0,
            "strengths": ["short point"],
            "weaknesses": ["short point"],
            "improvements": ["short point"]
            }}

            Rules:
            - Keep each point max 1 line
            - ATS score out of 100 only

            Resume:
            {text}
            """
            # 3. AI CALL (RETRY SAFE)
  
            response_text = ""

            for i in range(3):
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )

                    if response and response.text:
                        response_text = response.text.strip()

                        # remove markdown if any
                        if "```" in response_text:
                            response_text = response_text.replace("```json", "").replace("```", "").strip()

                        data = json.loads(response_text)
                        break

                except exceptions.ResourceExhausted:
                    time.sleep(2)

                except json.JSONDecodeError:
                    data = {
                        "ats_score": 0,
                        "strengths": ["Invalid AI response"],
                        "weaknesses": [],
                        "improvements": ["Try again"]
                    }
                    break
            # 4. FINAL FALLBACK
            if not data:
                data = {
                    "ats_score": 0,
                    "strengths": ["AI failed to respond"],
                    "weaknesses": ["Try again"],
                    "improvements": ["Retry upload"]
                }

            return render(request, 'response.html', {
                'text': text,
                'data': data
            })

    return render(request, 'upload_resume.html')