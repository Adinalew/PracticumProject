import pytesseract
from PIL import Image
from django.core.files.storage import default_storage

def extract_text_from_image(file):
    # Save the file temporarily
    temp_path = default_storage.save('temp_image.png', file)
    with default_storage.open(temp_path, 'rb') as f:
        image = Image.open(f)
        text = pytesseract.image_to_string(image)
    return text
