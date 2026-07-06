import PyPDF2
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage



def home(request):
    return render(request, 'home.html')

def upload_resume(request):
    if request.method == 'POST':
        file = request.FILES.get('resume')

        if file:
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)

            text = ""

            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)#binary to readable conversion

                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text

            return render(request, 'upload_resume.html', {
                'text': text
            })

    return render(request, 'upload_resume.html')