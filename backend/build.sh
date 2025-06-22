#!/bin/bash
set -e  # Exit immediately if any command fails

# System dependencies
echo "Installing system dependencies..."
apt-get update -qq && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \  # Add language packs as needed
    poppler-utils \
    libgl1 \
    libsm6 \
    libxext6 > /dev/null

# Verify Tesseract installation
echo "Verifying Tesseract installation..."
if ! command -v tesseract &> /dev/null; then
    echo "ERROR: Tesseract not found in PATH" >&2
    exit 1
fi
echo "Tesseract version: $(tesseract --version)"

# Python environment
echo "Setting up Python environment..."
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Verify Python packages
echo "Verifying Python packages..."
python -c "
import pytesseract
from pdf2image import convert_from_path
print('Dependencies verified:')
print(f'pytesseract: {pytesseract.get_tesseract_version()}')
print('pdf2image: OK')
"