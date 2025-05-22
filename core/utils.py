import PyPDF2
import pytesseract
from PIL import Image
from django.core.files.storage import default_storage
from gtts import gTTS
from io import BytesIO
import io
import pyttsx3
from docx import Document

def extract_text_from_image(file):
    # Save the file temporarily
    temp_path = default_storage.save('temp_image.png', file)
    with default_storage.open(temp_path, 'rb') as f:
        image = Image.open(f)
        text = pytesseract.image_to_string(image)
    return text

def extract_text_from_file(file):
    name = file.name.lower()
    if name.endswith(('.png', '.jpg', '.jpeg')):
        return extract_text_from_image(file)
    elif name.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
        return text
    elif name.endswith('.docx'):
        doc = Document(file)
        return '\n'.join([para.text for para in doc.paragraphs])
    elif name.endswith('.txt'):
        return file.read().decode('utf-8')
    else:
        return ''

def generate_tts_audio(text):
    engine = pyttsx3.init()
    audio_stream = io.BytesIO()
    engine.save_to_file(text, audio_stream)
    engine.runAndWait()
    audio_stream.seek(0)
    return audio_stream.read()
