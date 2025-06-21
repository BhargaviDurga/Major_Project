from flask import Flask, request, jsonify, send_file
import os
import json
from form_filler import extract_text_from_id, fill_pdf_form
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for simplicity
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload-id", methods=["POST"])
def upload_id():
    if "files" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    files = request.files.getlist("files")
    extracted_data = {}

    # Clear existing extracted data at the start of a new session or request
    extracted_data_path = os.path.join(UPLOAD_FOLDER, "extracted_data.json")
    if os.path.exists(extracted_data_path):
        os.remove(extracted_data_path)

    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        try:
            new_data = extract_text_from_id(file_path)
            for key, value in new_data.items():
                if key in extracted_data and extracted_data[key] == "NOT FOUND":
                    extracted_data[key] = value
                elif key not in extracted_data:
                    extracted_data[key] = value
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Save combined extracted data to a temporary file
    with open(extracted_data_path, "w") as f:
        json.dump(extracted_data, f)

    return jsonify({"extracted_data": extracted_data})

@app.route("/update-data", methods=["POST"])
def update_data():
    updated_data = request.json
    # Save updated data to a temporary file
    extracted_data_path = os.path.join(UPLOAD_FOLDER, "extracted_data.json")
    try:
        with open(extracted_data_path, "w") as f:
            json.dump(updated_data, f)
        return jsonify({"message": "Details updated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/fill-form", methods=["POST"])
def fill_form():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename)
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(pdf_path)

    try:
        # Read extracted data from the temporary file
        extracted_data_path = os.path.join(UPLOAD_FOLDER, "extracted_data.json")
        with open(extracted_data_path, "r") as f:
            extracted_data = json.load(f)
        
        filled_pdf_path = fill_pdf_form(pdf_path, extracted_data)
        response = send_file(filled_pdf_path, as_attachment=False, mimetype="application/pdf")
        
        # Delete the extracted data file after sending the response
        # if os.path.exists(extracted_data_path):
        #     os.remove(extracted_data_path)
        
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)