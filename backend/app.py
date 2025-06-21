from flask import Flask, request, jsonify, send_file
import os
import json
from backend.form_filler import extract_text_from_id, fill_pdf_form
from werkzeug.utils import secure_filename
from flask_cors import CORS
import tempfile
import atexit
import shutil


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
CORS(app, resources={
    r"/fill-form": {
        "origins": ["https://your-frontend-url.com"],
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    }
})
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



# Create a temporary directory
TEMP_UPLOAD_FOLDER = tempfile.mkdtemp()

# Cleanup function
def cleanup():
    shutil.rmtree(TEMP_UPLOAD_FOLDER, ignore_errors=True)

atexit.register(cleanup)

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
        temp_file = tempfile.NamedTemporaryFile(dir=TEMP_UPLOAD_FOLDER, delete=False)
        file.save(temp_file.name)
        temp_file.close()

        try:
            new_data = extract_text_from_id(temp_file.name)
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
    print("Request received - Files:", request.files)  # Debug log
    print("Request headers:", request.headers)  # Debug log
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == '':
            print("Empty filename")  # Debug log
            return jsonify({"error": "No selected file"}), 400

        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # Read extracted data
        extracted_data_path = os.path.join(tempfile.gettempdir(), "extracted_data.json")
        if not os.path.exists(extracted_data_path):
            return jsonify({"error": "No extracted data found"}), 400

        with open(extracted_data_path, "r") as f:
            extracted_data = json.load(f)

        # Process PDF
        output_path = fill_pdf_form(tmp_path, extracted_data)

        # Delete the extracted data file after sending the response
        # if os.path.exists(extracted_data_path):
        #     os.remove(extracted_data_path)
        
        # Return the filled PDF
        return send_file(output_path, as_attachment=False, mimetype="application/pdf")
    

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")  # This will appear in Render logs
        return jsonify({"error": str(e)}), 500
            

if __name__ == "__main__":
    app.run()