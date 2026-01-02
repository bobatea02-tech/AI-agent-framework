
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Ensure output directory exists
FIXTURES_DIR = "tests/fixtures"
os.makedirs(FIXTURES_DIR, exist_ok=True)

def generate_aadhaar_mock():
    """Generate a synthetic Aadhaar-like card image."""
    width, height = 600, 400
    img = Image.new('RGB', (width, height), color=(250, 250, 250))
    d = ImageDraw.Draw(img)
    
    # Header bar
    d.rectangle([0, 0, width, 50], fill=(255, 100, 100)) # Saffron-ish
    d.rectangle([0, 50, width, 60], fill=(255, 255, 255))
    d.rectangle([0, 60, width, 110], fill=(20, 150, 20)) # Green-ish
    
    # Text
    try:
        # Try to use a standard font if available, else default
        font_large = ImageFont.truetype("arial.ttf", 30)
        font_med = ImageFont.truetype("arial.ttf", 20)
        font_small = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font_large = ImageFont.load_default()
        font_med = ImageFont.load_default()
        font_small = ImageFont.load_default()

    d.text((20, 120), "Government of India", fill=(0,0,0), font=font_med)
    d.text((20, 160), "Name: John Doe", fill=(0,0,0), font=font_med)
    d.text((20, 190), "DOB: 01/01/1990", fill=(0,0,0), font=font_med)
    d.text((20, 220), "Gender: Male", fill=(0,0,0), font=font_med)
    
    # Number
    d.text((150, 320), "1234 5678 9012", fill=(0,0,0), font=font_large)
    
    # Photo placeholder
    d.rectangle([400, 120, 550, 270], outline=(0,0,0), width=2)
    d.text((430, 180), "PHOTO", fill=(100,100,100), font=font_med)

    # Save
    path = os.path.join(FIXTURES_DIR, "sample_aadhaar.jpg")
    img.save(path)
    print(f"Generated {path}")
    return path

def generate_pan_mock():
    """Generate a synthetic PAN-like card image."""
    width, height = 600, 350
    img = Image.new('RGB', (width, height), color=(220, 230, 255)) # Light blueish
    d = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 30)
        font_med = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font_large = ImageFont.load_default()
        font_med = ImageFont.load_default()

    d.text((200, 20), "INCOME TAX DEPARTMENT", fill=(0,0,0), font=font_med)
    d.text((200, 50), "GOVT. OF INDIA", fill=(0,0,0), font=font_med)
    
    d.text((30, 150), "ABCDE1234F", fill=(0,0,0), font=font_large)
    d.text((30, 200), "Name", fill=(100,100,100), font=font_med)
    d.text((30, 230), "JANE DOE", fill=(0,0,0), font=font_med)
    
    # Photo placeholder
    d.rectangle([450, 100, 550, 250], outline=(0,0,0), width=2)
    
    path = os.path.join(FIXTURES_DIR, "sample_pan.jpg")
    img.save(path)
    print(f"Generated {path}")
    return path

if __name__ == "__main__":
    generate_aadhaar_mock()
    generate_pan_mock()
