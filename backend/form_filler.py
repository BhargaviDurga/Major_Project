import cv2
import pytesseract
from PyPDF2 import PdfReader, PdfWriter
import json
import os
import PIL.Image
import google.generativeai as genai
import re
import pdf2image
import numpy as np
from PIL import ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from PIL import ImageDraw, ImageFont
import textwrap
import tempfile
import shutil
import logging

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'


def extract_text_from_id(image_path):
    os.environ["GOOGLE_API_KEY"] = "AIzaSyBSlkTW52fBvrHs-oByEb0AgSBo44qjm0A"
    genai.configure(api_key="AIzaSyBSlkTW52fBvrHs-oByEb0AgSBo44qjm0A")
    img = PIL.Image.open(image_path)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        [
            '''You are an expert in text extraction and formatting.
        Given the following image, return structured data with these fields:
        
        - Name
        - Date of Birth (format: DD-MM-YYYY)
        - Phone Number (10-digit format)
        - Aadhaar Number (12-digit format)
        - Gender (MALE/FEMALE/OTHER)
        - PAN Number (10-character alphanumeric)
        - VID Number (16-digit format)
        - Address


        If any field is missing, try to infer it or return "NOT FOUND".
        ''',
            img,
        ],
        stream=True,
    )
    response.resolve()
    extracted_data_str = response.text
    extracted_text = re.sub(r'\*+', '', extracted_data_str)
    
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
            address_part = match.group(1).strip().upper()
            pincode_part = match.group(2)  # pincode part
            extracted_data[key] = f"{address_part} {pincode_part}".strip() if pincode_part else address_part
        else:
            extracted_data[key] = match.group(1).strip().upper() if match else "NOT FOUND"
    
    # Separate the name into first name and last name
    if "Name" in extracted_data and extracted_data["Name"] != "NOT FOUND":
        name_parts = extracted_data["Name"].split()
        if len(name_parts) > 1:
            extracted_data["First Name"] = " ".join(name_parts[:-1])
            extracted_data["Last Name"] = name_parts[-1]
        else:
            extracted_data["First Name"] = name_parts[0]
            extracted_data["Last Name"] = ""
    
    return extracted_data

def find_multiple_word_positions(pdf_path, search_words):
    try:
        # Verify Tesseract is installed
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError("Tesseract is not installed or not in system PATH")
    images = pdf2image.convert_from_path(pdf_path)
    word_positions = {word.lower(): [] for word in search_words}  # Initialize dictionary

    for page_num, image in enumerate(images):
        img_cv = np.array(image)
        img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # Perform OCR with bounding box detection
        data = pytesseract.image_to_data(img_gray, output_type=pytesseract.Output.DICT)

        # Clean text data
        cleaned_text = [re.sub(r'[0-9:]', '', word) for word in data["text"]]
        data["text"] = cleaned_text

        # Call the function to merge multi-line fields
        merged_data = merge_multiline_fields(data)

        # print(f"Page {page_num + 1} OCR Data:\n", merged_data["text"])

        for i, word in enumerate(merged_data["text"]):
            word_lower = word.lower().strip()
            if word_lower in word_positions:  # Check if word is in the search list
                x, y, w, h = merged_data["left"][i], merged_data["top"][i], merged_data["width"][i], merged_data["height"][i]
                # Store page number & coordinates
                word_positions[word_lower].append((page_num + 1, x, y, w, h))

    return word_positions

# Function to merge multi-line fields
def merge_multiline_fields(data, threshold_x=70, threshold_y=18):
    merged_fields = {
        "text": [],
        "left": [],
        "top": [],
        "width": [],
        "height": []
    }
    temp_field = ""
    last_x, last_y = 0, 0
    temp_left, temp_top, temp_width, temp_height = 0, 0, 0, 0

    for i, word in enumerate(data["text"]):
        if word:
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]

            if temp_field:  # If there's already a word in progress
                if abs(y - last_y) < threshold_y and abs(x - (last_x + temp_width)) < threshold_x:
                    temp_field += " " + word  # Merge words horizontally
                    temp_width = x + w - temp_left  # Update width to include new word
                    temp_height = max(temp_height, h)  # Update height to the maximum height
                else:
                    merged_fields["text"].append(temp_field)
                    merged_fields["left"].append(temp_left)
                    merged_fields["top"].append(temp_top)
                    merged_fields["width"].append(temp_width)
                    merged_fields["height"].append(temp_height)
                    temp_field = word  # Start new phrase
                    temp_left, temp_top, temp_width, temp_height = x, y, w, h
            else:
                temp_field = word  # Initialize first word
                temp_left, temp_top, temp_width, temp_height = x, y, w, h

            last_x, last_y = x, y  # Update position reference

    if temp_field:
        merged_fields["text"].append(temp_field)
        merged_fields["left"].append(temp_left)
        merged_fields["top"].append(temp_top)
        merged_fields["width"].append(temp_width)
        merged_fields["height"].append(temp_height)

    return merged_fields

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fill_form_with_extracted_data(pdf_path, extracted_data, word_positions, output_pdf_path):
    """Fill PDF form fields with extracted data at specified positions"""
    try:
        # Validate input data
        if not isinstance(extracted_data, dict):
            raise ValueError("extracted_data must be a dictionary")
        if not isinstance(word_positions, dict):
            raise ValueError("word_positions must be a dictionary")

        # Convert PDF to images
        images = pdf2image.convert_from_path(pdf_path)
        if not images:
            raise ValueError("Failed to convert PDF to images")

        # Font configuration
        try:
            font = ImageFont.truetype("arialbd.ttf", 30)
        except IOError:
            font = ImageFont.load_default()
            logger.warning("Using default font as arialbd.ttf not found")

        # Field mapping configuration
        FIELD_MAPPING = {
            ".name*": "Name",
            ".date of birth*": "Date of Birth",
            ".pan*": "PAN Number",
            ".gender*": "Gender",
            "address*": "Address",
            "mobile no.": "Phone Number",
            "First Name": "First Name",
            "Last Name": "Last Name"
        }

        for page_num, image in enumerate(images):
            draw = ImageDraw.Draw(image)
            
            for word, positions in word_positions.items():
                field_name = next(
                    (FIELD_MAPPING[key] for key in FIELD_MAPPING 
                     if key.lower() in word.lower()), None)
                
                if field_name and extracted_data.get(field_name, "NOT FOUND") != "NOT FOUND":
                    value = extracted_data[field_name]
                    
                    for (page, x, y, w, h) in positions:
                        if page == page_num + 1:  # 1-based page numbers
                            x_offset = x + 225
                            y_offset = y - 10
                            
                            if field_name == "Address":
                                # Handle address with text wrapping
                                wrapped_text = textwrap.fill(value[:74], width=40)
                                for line in wrapped_text.splitlines():
                                    draw.text((x_offset, y_offset), line, fill="blue", font=font)
                                    y_offset += 35  # Line height
                            else:
                                # Handle regular fields
                                draw.text((x_offset, y_offset), value, fill="blue", font=font)

        # Save filled PDF
        images[0].save(
            output_pdf_path,
            save_all=True,
            append_images=images[1:],
            quality=100
        )
        
        logger.info(f"Successfully filled form saved to {output_pdf_path}")
        return output_pdf_path

    except Exception as e:
        logger.error(f"Error in fill_form_with_extracted_data: {str(e)}")
        raise

def fill_pdf_form(pdf_path, extracted_data, output_path):
    """Main function to process and fill PDF form"""
    temp_dir = None
    try:
        # Create temp directory for processing
        temp_dir = tempfile.mkdtemp()
        temp_output = os.path.join(temp_dir, "filled_form.pdf")
        
        # Find field positions in the PDF
        search_words = [
            ".name*", ".date of birth*", ".gender*", 
            "address*", ".pan*", "mobile no."
        ]
        word_positions = find_multiple_word_positions(pdf_path, search_words)
        
        # Fill the form with data
        result_path = fill_form_with_extracted_data(
            pdf_path,
            extracted_data,
            word_positions,
            temp_output
        )
        
        # Move to final output location
        shutil.move(result_path, output_path)
        return output_path

    except Exception as e:
        logger.error(f"Error in fill_pdf_form: {str(e)}")
        raise
    finally:
        # Clean up temp directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
