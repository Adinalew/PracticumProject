import PyPDF2
import pytesseract
from PIL import Image
from django.core.files.storage import default_storage
import io
import pyttsx3
from docx import Document
from gtts import gTTS
from io import BytesIO
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import os

# Set this path if pytesseract can't find tesseract automatically
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_file):
    # Open image
    image = Image.open(image_file)
    # Convert to grayscale
    image = image.convert('L')
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    # Optional: sharpen
    image = image.filter(ImageFilter.SHARPEN)
    return image

def extract_text_from_image(image_file):
    image = preprocess_image(image_file)
    text = pytesseract.image_to_string(image)
    return text.strip()

def extract_text_from_file(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
        return extract_text_from_image(file)
    elif ext == '.pdf':
        return extract_text_from_pdf(file)
    else:
        return ""

from pdf2image import convert_from_bytes

def extract_text_from_pdf(file):
    images = convert_from_bytes(file.read())
    full_text = ""
    for image in images:
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        buf.seek(0)
        full_text += extract_text_from_image(buf) + "\n"
    return full_text.strip()

def generate_tts_audio(text):
    tts = gTTS(text)
    audio_stream = BytesIO()
    tts.write_to_fp(audio_stream)
    audio_stream.seek(0)
    return audio_stream.read()
