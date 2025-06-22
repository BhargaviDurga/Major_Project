from flask import Flask, request, jsonify, send_file
import os
import json
from werkzeug.utils import secure_filename
from flask_cors import CORS
import tempfile
import atexit
import shutil
import logging
from backend.form_filler import extract_text_from_id, fill_pdf_form
import io

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB file limit
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://smartforms-frontend.onrender.com",
            "http://localhost:3000"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "Service is healthy"}), 200

# Create upload directory
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload-id", methods=["POST"])
def upload_id():
    """Endpoint for uploading ID documents and extracting data"""
    try:
        if "files" not in request.files:
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist("files")
        extracted_data = {}

        for file in files:
            if file.filename == '':
                continue

            # Create temp file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                file.save(tmp_file.name)
                tmp_path = tmp_file.name

            try:
                # Extract data from ID
                new_data = extract_text_from_id(tmp_path)
                
                # Merge with existing data
                for key, value in new_data.items():
                    if key in extracted_data and extracted_data[key] == "NOT FOUND":
                        extracted_data[key] = value
                    elif key not in extracted_data:
                        extracted_data[key] = value
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}")
                return jsonify({"error": f"Failed to process {file.filename}"}), 500
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        return jsonify({
            "message": "ID processed successfully",
            "extracted_data": extracted_data
        })

    except Exception as e:
        logger.error(f"Error in upload-id: {str(e)}")
        return jsonify({"error": "Server error processing IDs"}), 500

@app.route("/update-data", methods=["POST"])
def update_data():
    """Endpoint for updating extracted data"""
    try:
        updated_data = request.get_json()
        if not updated_data:
            return jsonify({"error": "No data provided"}), 400

        # In production, you might want to validate the data structure here
        return jsonify({
            "message": "Details updated successfully!",
            "extracted_data": updated_data
        })

    except Exception as e:
        logger.error(f"Error in update-data: {str(e)}")
        return jsonify({"error": "Server error updating data"}), 500

@app.route("/fill-form", methods=["POST"])
def fill_form():
    """Endpoint for filling PDF forms"""
    try:
        # Check for Tesseract availability first
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
        except Exception as ocr_error:
            logger.error(f"OCR dependency error: {str(ocr_error)}")
            return jsonify({
                "error": "Server missing required OCR capabilities. Please contact support.",
                "details": str(ocr_error)
            }), 503

        # Validate file upload
        if "file" not in request.files:
            logger.error("No file part in request")
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == '':
            logger.error("Empty filename in request")
            return jsonify({"error": "No selected file"}), 400

        # Validate and parse extracted data
        extracted_data = request.form.get("extracted_data")
        if not extracted_data:
            logger.error("No extracted data provided")
            return jsonify({"error": "No extracted data provided"}), 400

        try:
            extracted_data = json.loads(extracted_data)
            if not isinstance(extracted_data, dict):
                raise ValueError("Extracted data must be a dictionary")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid extracted data format: {str(e)}")
            return jsonify({"error": "Invalid extracted data format"}), 400

        # Process PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_pdf:
            file.save(tmp_pdf.name)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, "filled_form.pdf")
                
                try:
                    filled_path = fill_pdf_form(
                        tmp_pdf.name,
                        extracted_data,
                        output_path
                    )
                    
                    if not os.path.exists(filled_path):
                        logger.error("PDF generation failed")
                        raise ValueError("Failed to generate filled PDF")
                    
                    # Read filled PDF into memory
                    with open(filled_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    logger.info("PDF generated successfully")
                    return send_file(
                        io.BytesIO(pdf_data),
                        mimetype="application/pdf",
                        as_attachment=False,
                        download_name="filled_form.pdf"
                    )
                except Exception as e:
                    logger.error(f"PDF processing failed: {str(e)}")
                    return jsonify({
                        "error": "Failed to process PDF",
                        "details": str(e)
                    }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))