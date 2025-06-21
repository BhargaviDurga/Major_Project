#!/bin/bash
# Install system dependencies
apt-get update
apt-get install -y tesseract-ocr poppler-utils

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt