from gtts import gTTS
from io import BytesIO
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import httpx
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
from django.conf import settings
from docx import Document
from pptx import Presentation
import fitz  # PyMuPDF

# Load environment variables
load_dotenv()

# Tesseract setup
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_file):
    image = Image.open(image_file)
    image = image.convert('L')
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    image = image.filter(ImageFilter.SHARPEN)
    return image

def extract_text_from_image(image_file):
    image = preprocess_image(image_file)
    return pytesseract.image_to_string(image).strip()

def extract_text_from_pdf(file):
    file.seek(0)
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            page_text = page.get_text()
            text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def extract_text_from_docx(file):
    file.seek(0)
    doc = Document(file)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs).strip()

def extract_text_from_pptx(file):
    file.seek(0)
    presentation = Presentation(file)
    full_text = []
    for slide in presentation.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    full_text.append(paragraph.text)
    return "\n".join(full_text).strip()

def extract_text_from_file(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
        return extract_text_from_image(file)
    elif ext == '.pdf':
        return extract_text_from_pdf(file)
    elif ext == '.docx':
        return extract_text_from_docx(file)
    elif ext == '.pptx':
        return extract_text_from_pptx(file)
    else:
        return ""

def extract_text_from_uploaded_file(uploaded_file):
    file_field = uploaded_file.file
    ext = os.path.splitext(file_field.name)[1].lower()
    print(f"extract_text_from_uploaded_file called for {file_field.name} with extension {ext}")

    try:
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            return extract_text_from_image(file_field)
        elif ext == '.txt':
            print("Trying to read .txt file...")
            file_field.open()
            file_field.seek(0)
            content_bytes = file_field.read()
            print(f"Raw content bytes: {content_bytes[:50]}")
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                print("UTF-8 decode failed, trying latin-1...")
                content = content_bytes.decode('latin-1')
            print(f"Extracted text from txt file (preview): {content[:100]}")
            return content.strip()
        elif ext == '.pdf':
            return extract_text_from_pdf(file_field)
        elif ext == '.docx':
            return extract_text_from_docx(file_field)
        elif ext == '.pptx':
            return extract_text_from_pptx(file_field)
        else:
            print(f"No extractor for file type: {ext}")
            return ""
    except Exception as e:
        print(f"Error extracting text from {file_field.name}: {e}")
        return ""

def generate_tts_audio(text):
    tts = gTTS(text)
    audio_stream = BytesIO()
    tts.write_to_fp(audio_stream)
    audio_stream.seek(0)
    return audio_stream.read()

def get_text_from_session(session):
    notes = session.extracted_notes.all()
    return "\n\n".join(note.text for note in notes if note.text.strip())

def generate_study_review(text, options=None):
    api_key = os.getenv("OPENAI_API_KEY")
    cert_path = "C:/certificate/2023 techloq bundle certificate.crt"

    if os.path.exists(cert_path):
        print("✅ Using Techloq certificate for SSL.")
        http_client = httpx.Client(verify=cert_path)
    else:
        print("ℹ️ No custom cert found. Using default SSL.")
        http_client = httpx.Client()

    client = OpenAI(api_key=api_key, http_client=http_client)

    # Include user preferences in prompt
    if options:
        notes = (
            f"Language level: {options.get('language_level')}, "
            f"Teaching style: {options.get('explanation_style')}, "
            f"Depth: {options.get('review_depth')}, "
            f"User notes: {options.get('additional_notes') or 'None'}."
        )
    else:
        notes = "No additional preferences provided."

    prompt = (
        f"You are an AI assistant. Based on the following notes, create a study review.\n"
        f"{notes}\n\n"
        f"Study text:\n{text}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        print(f"❌ OpenAI API error: {e}")
        return "An error occurred while generating the study review."

def generate_followup_response(question, previous_review, options=None):
    api_key = os.getenv("OPENAI_API_KEY")
    cert_path = "C:/certificate/2023 techloq bundle certificate.crt"

    if os.path.exists(cert_path):
        http_client = httpx.Client(verify=cert_path)
    else:
        http_client = httpx.Client()

    client = OpenAI(api_key=api_key, http_client=http_client)

    style = options.get('explanation_style', 'normal') if options else 'normal'

    prompt = (
        f"You are a helpful tutor. Based on the study material below, respond to the user's follow-up question.\n"
        f"Make sure to answer in the appropriate tone. Explanation style: {style}.\n\n"
        f"Study Material:\n{previous_review}\n\n"
        f"Follow-up Question:\n{question}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a kind, helpful tutor."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        print(f"Error generating follow-up: {e}")
        return "Sorry, something went wrong while generating your answer."