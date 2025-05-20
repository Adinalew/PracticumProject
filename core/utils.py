import pytesseract
from PIL import Image
from django.core.files.storage import default_storage
from gtts import gTTS
from io import BytesIO

def extract_text_from_image(file):
    # Save the file temporarily
    temp_path = default_storage.save('temp_image.png', file)
    with default_storage.open(temp_path, 'rb') as f:
        image = Image.open(f)
        text = pytesseract.image_to_string(image)
    return text

def generate_tts_audio(text):
    tts = gTTS(text)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp
