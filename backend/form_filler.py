import cv2
import pytesseract
import json
import os
import re
import tempfile
import numpy as np
import pdf2image
from PIL import Image, ImageDraw, ImageFont
import textwrap
import google.generativeai as genai
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO

# Configure Tesseract path (needed for Render)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def extract_text_from_id(image_path):
    """Extract structured data from ID image using Gemini API"""
    try:
        # Configure Gemini (move API key to environment variables in production)
        genai.configure(api_key=os.getenv("GEMINI_API_KEY", "AIzaSyBSlkTW52fBvrHs-oByEb0AgSBo44qjm0A"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        with Image.open(image_path) as img:
            response = model.generate_content(
                [
                    '''You are an expert in text extraction and formatting.
                    Extract these fields from the ID document:
                    - Name (split into First/Last)
                    - Date of Birth (DD-MM-YYYY)
                    - Phone Number (10 digits)
                    - Aadhaar Number (12 digits)
                    - Gender (MALE/FEMALE/OTHER)
                    - PAN Number (10 chars)
                    - VID Number (16 digits)
                    - Address (with PIN code)
                    Return "NOT FOUND" for missing fields.''',
                    img,
                ],
                stream=True,
            )
            response.resolve()
            extracted_text = re.sub(r'\*+', '', response.text)

        # Field extraction patterns
        fields = {
            "Name": r"Name:\s*([A-Za-z\s/]+)\n",
            "Date of Birth": r"Date of Birth:\s*(\d{2}-\d{2}-\d{4})",
            "Phone Number": r"Phone Number:\s*(\d{10})",
            "Aadhaar Number": r"Aadhaar Number:\s*(\d{4}\s?\d{4}\s?\d{4})",
            "Gender": r"Gender:\s*(MALE|FEMALE|OTHER)",
            "PAN Number": r"PAN Number:\s*(.+)\n",
            "VID Number": r"VID Number:\s*(\d{16})",
            "Address": r"Address:\s*([\w\s,.-]+?)(?:\s*(\d{6}))?\s*(?=\n|$)"
        }
        
        extracted_data = {}
        for key, pattern in fields.items():
            match = re.search(pattern, extracted_text)
            if key == "Address" and match:
                address = match.group(1).strip().upper()
                pincode = match.group(2) or ""
                extracted_data[key] = f"{address} {pincode}".strip()
            else:
                extracted_data[key] = match.group(1).strip().upper() if match else "NOT FOUND"

        # Split name
        if "Name" in extracted_data:
            name_parts = extracted_data["Name"].split()
            extracted_data["First Name"] = " ".join(name_parts[:-1]) if len(name_parts) > 1 else name_parts[0]
            extracted_data["Last Name"] = name_parts[-1] if len(name_parts) > 1 else ""

        return extracted_data

    except Exception as e:
        print(f"Error in extract_text_from_id: {str(e)}")
        raise

def process_pdf_fields(pdf_path, search_words):
    """Find positions of form fields in PDF"""
    try:
        images = pdf2image.convert_from_path(pdf_path)
        word_positions = {word.lower(): [] for word in search_words}

        for page_num, image in enumerate(images):
            img_cv = np.array(image)
            img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            data = pytesseract.image_to_data(img_gray, output_type=pytesseract.Output.DICT)
            
            # Clean and merge text
            cleaned_text = [re.sub(r'[^a-zA-Z\s]', '', word).strip() for word in data["text"]]
            merged_data = merge_multiline_fields({
                **data,
                "text": cleaned_text
            })

            for i, word in enumerate(merged_data["text"]):
                word_lower = word.lower()
                if word_lower in word_positions:
                    x, y = merged_data["left"][i], merged_data["top"][i]
                    w, h = merged_data["width"][i], merged_data["height"][i]
                    word_positions[word_lower].append((page_num + 1, x, y, w, h))

        return word_positions

    except Exception as e:
        print(f"Error in process_pdf_fields: {str(e)}")
        raise

def fill_pdf_form(pdf_path, extracted_data):
    """Main function to fill PDF form"""
    try:
        # Create temp output directory
        os.makedirs("uploads", exist_ok=True)
        output_path = os.path.join("uploads", "filled_form.pdf")
        
        # Field mapping
        search_words = [".name*", ".date of birth*", ".gender*", "address*", ".pan*", "mobile no."]
        word_positions = process_pdf_fields(pdf_path, search_words)
        
        # Convert PDF to images and fill fields
        images = pdf2image.convert_from_path(pdf_path)
        font = ImageFont.truetype("arialbd.ttf", 30)  # Ensure this font exists on Render
        
        for page_num, image in enumerate(images):
            draw = ImageDraw.Draw(image)
            for field_word, positions in word_positions.items():
                field_name = {
                    ".name*": "First Name",
                    ".date of birth*": "Date of Birth",
                    ".pan*": "PAN Number",
                    ".gender*": "Gender",
                    "address*": "Address",
                    "mobile no.": "Phone Number"
                }.get(field_word, field_word)
                
                if field_name in extracted_data and extracted_data[field_name] != "NOT FOUND":
                    for (page, x, y, w, h) in positions:
                        if page == page_num + 1:
                            x_offset = x + 225
                            y_offset = y - 10
                            value = extracted_data[field_name]
                            
                            if field_name == "Address":
                                wrapped = textwrap.fill(value[:74], width=40)
                                for line in wrapped.splitlines():
                                    draw.text((x_offset, y_offset), line, fill="blue", font=font)
                                    y_offset += 35
                            else:
                                draw.text((x_offset, y_offset), value, fill="blue", font=font)

        # Save filled PDF
        images[0].save(output_path, save_all=True, append_images=images[1:])
        return output_path

    except Exception as e:
        print(f"Error in fill_pdf_form: {str(e)}")
        raise

# Helper function (unchanged)
def merge_multiline_fields(data, threshold_x=70, threshold_y=18):
    merged_fields = {k: [] for k in ["text", "left", "top", "width", "height"]}
    temp_field = ""
    last_x, last_y = 0, 0
    temp_left, temp_top, temp_width, temp_height = 0, 0, 0, 0

    for i, word in enumerate(data["text"]):
        if word:
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            if temp_field:
                if abs(y - last_y) < threshold_y and abs(x - (last_x + temp_width)) < threshold_x:
                    temp_field += " " + word
                    temp_width = x + w - temp_left
                    temp_height = max(temp_height, h)
                else:
                    merged_fields["text"].append(temp_field)
                    merged_fields["left"].append(temp_left)
                    merged_fields["top"].append(temp_top)
                    merged_fields["width"].append(temp_width)
                    merged_fields["height"].append(temp_height)
                    temp_field = word
                    temp_left, temp_top, temp_width, temp_height = x, y, w, h
            else:
                temp_field = word
                temp_left, temp_top, temp_width, temp_height = x, y, w, h
            last_x, last_y = x, y

    if temp_field:
        merged_fields["text"].append(temp_field)
        merged_fields["left"].append(temp_left)
        merged_fields["top"].append(temp_top)
        merged_fields["width"].append(temp_width)
        merged_fields["height"].append(temp_height)

    return merged_fields