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

def fill_form_with_extracted_data(pdf_path, extracted_data, word_positions, output_pdf_path):
    try:
        if not isinstance(extracted_data, dict):
            raise ValueError("extracted_data should be a dictionary")

        images = pdf2image.convert_from_path(pdf_path)  # Convert PDF to images
        font_path = "arialbd.ttf"  # Replace with the path to your TrueType font file
        font_size = 30
        font = ImageFont.truetype(font_path, font_size)

        mapping = {
            ".name*": "Name",
            ".date of birth*": "Date of Birth",
            ".pan*": "PAN Number",
            ".gender*": "Gender",
            "address*": "Address",
            "mobile no.": "Phone Number",
            "First Name": "First Name",
            "Last Name": "Last Name",
        }

        # Calculate a fixed width for each letter
        sample_letter = "G"  # Use "A" or any character as a reference
        fixed_letter_width = font.getbbox(sample_letter)[2] + 13  # Width of "A" + spacing

        for page_num, image in enumerate(images):
            img_cv = np.array(image)
            img_pil = image.copy()
            draw = ImageDraw.Draw(img_pil)

            for word, pos_list in word_positions.items():
                extracted_key = next(
                    (mapping[key] for key in mapping.keys() if key.lower() in word.lower()), None
                )
                if extracted_key and extracted_data.get(extracted_key) and extracted_data[extracted_key] != "NOT FOUND":
                    value_to_fill = extracted_data[extracted_key]

                    for (page, x, y, w, h) in pos_list:
                        if page == page_num + 1:
                            x_offset = x + 225  # Adjust the x_offset as needed
                            y_offset = y - 10  # Adjust the y_offset as needed
                            available_width = 100 # Maximum width for the address, adjust as needed

                            if extracted_key == "Address":
                                # Wrap the address text
                                address = value_to_fill[:74]
                                # Wrap the truncated address text
                                wrapped_text = textwrap.fill(address, width=40)
                                lines = wrapped_text.splitlines()
                                line_height = font.getbbox("A")[3] # Approximate line height

                                for line in lines:
                                    x_line_offset = x_offset  # Reset x_line_offset for each line
                                    for letter in line:
                                        draw.text((x_line_offset, y_offset), letter, fill="Blue", font=font)
                                        x_line_offset += fixed_letter_width    # Letter spacing for address
                                    y_offset += line_height + 22  # Adjust vertical spacing
                            else:
                                # For other fields, draw text normally
                                for letter in value_to_fill:
                                    draw.text((x_offset, y_offset), letter, fill="Blue", font=font)
                                    x_offset += fixed_letter_width    # Adjust the spacing between letters

            images[page_num] = img_pil  # Update image

        images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
        print(f"Form filled successfully. Output saved to {output_pdf_path}")
        return output_pdf_path

    except Exception as e:
        print(f"Error filling form: {e}")
        raise


def fill_pdf_form(pdf_path, extracted_data):
    # Ensure extracted_data is a dictionary
    # if isinstance(extracted_data, str):
    #     try:
    #         extracted_data = json.loads(extracted_data)
    #     except json.JSONDecodeError as e:
    #         print(f"Error decoding JSON: {e}")
    #         raise ValueError("extracted_data should be a dictionary or a JSON string that can be converted to a dictionary")

    # if not isinstance(extracted_data, dict):
    #     raise ValueError("extracted_data should be a dictionary")

    search_words = [".name*", ".date of birth*", ".gender*", "address*", ".pan*", "mobile no."]  # List of words to find
    word_positions = find_multiple_word_positions(pdf_path, search_words)
    print(f"Word Positions: {word_positions}")  # Debugging statement
    output_pdf_path = "uploads/filled_form.pdf"  # Output path for filled PDF
    result = fill_form_with_extracted_data(pdf_path, extracted_data, word_positions, output_pdf_path)
    print(f"Result: {result}")  # Debugging statement
    return result