from gtts import gTTS
from io import BytesIO
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
from pdf2image import convert_from_bytes
import openai
from django.conf import settings
from docx import Document
from pptx import Presentation
import fitz  # PyMuPDF

# Set this path if pytesseract can't find tesseract automatically
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_file):
    image = Image.open(image_file)
    image = image.convert('L')  # Convert to grayscale
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Enhance contrast
    image = image.filter(ImageFilter.SHARPEN)  # Optional: sharpen
    return image

def extract_text_from_image(image_file):
    image = preprocess_image(image_file)
    text = pytesseract.image_to_string(image)
    return text.strip()

def extract_text_from_pdf(file):
    file.seek(0)
    print(f"extract_text_from_pdf called with file: {file.name}")
    images = convert_from_bytes(file.read())
    full_text = ""
    for image in images:
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        buf.seek(0)
        page_text = extract_text_from_image(buf)
        print(f"Extracted text from one PDF page: {page_text[:100]}")  # preview
        full_text += page_text + "\n"
    return full_text.strip()

def extract_text_from_docx(file):
    file.seek(0)
    print(f"extract_text_from_docx called with file: {file.name}")
    doc = Document(file)
    full_text = [paragraph.text for paragraph in doc.paragraphs]
    return "\n".join(full_text).strip()

def extract_text_from_pptx(file):
    file.seek(0)
    print(f"extract_text_from_pptx called with file: {file.name}")
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
    combined_text = "\n\n".join(note.text for note in notes if note.text.strip())
    return combined_text

def generate_study_review(text):
    openai.api_key = settings.OPENAI_API_KEY
    prompt = (
        "You are an AI assistant tasked with creating a detailed study review. "
        "Based on the following input text, generate a review that highlights key points, "
        "definitions, and main concepts:\n\n"
        f"{text}\n\n"
        "Please provide a structured and concise review."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except openai.error.OpenAIError as e:
        print(f"Error generating study review: {e}")
        return "An error occurred while generating the study review."



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