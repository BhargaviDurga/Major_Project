import cv2
import pytesseract
import os
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def preprocess_image(image_path, target_size=(1600, 1600)):
    """
    Preprocess the input image for better OCR accuracy.

    :param image_path: Path to the input image.
    :param target_size: Tuple specifying the target size (width, height) for resizing.
    :return: Preprocessed image.
    """
    # Read the image
    img = cv2.imread(image_path)

    # Resize the image to a higher resolution
    resized_img = cv2.resize(img, target_size, interpolation=cv2.INTER_CUBIC)

    # Convert to grayscale
    gray = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)

    # Denoise the image
    denoised = cv2.fastNlMeansDenoising(gray, h=30)

    # Apply contrast adjustment
    contrast = cv2.convertScaleAbs(denoised, alpha=2.0, beta=0)

    # Apply adaptive thresholding
    thresholded = cv2.adaptiveThreshold(
        contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Apply dilation to make numbers more distinct
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    dilated = cv2.dilate(thresholded, kernel, iterations=1)

    # Debugging: Save and display the preprocessed image
    cv2.imwrite("debug_preprocessed.jpg", dilated)
    cv2.imshow("Preprocessed Image", dilated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return dilated


def detect_text_regions(image):
    """
    Detect text regions in the image using contours.

    :param image: The preprocessed image.
    :return: List of bounding boxes for detected text regions.
    """
    contours, _ = cv2.findContours(
        image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bounding_boxes = [cv2.boundingRect(contour) for contour in contours]
    return bounding_boxes


def extract_text_from_regions(image, bounding_boxes, languages="eng+hin+tel"):
    """
    Extract text from detected text regions.

    :param image: The preprocessed image.
    :param bounding_boxes: List of bounding boxes for detected text regions.
    :param languages: Languages to be used for OCR.
    :return: List of extracted text strings.
    """
    extracted_texts = []
    for (x, y, w, h) in bounding_boxes:
        roi = image[y:y+h, x:x+w]
        text = pytesseract.image_to_string(roi, lang=languages)
        extracted_texts.append(text)
    return extracted_texts


def post_process_text(text):
    """
    Post-process the extracted text to clean and correct it.
    """
    # Remove unwanted characters but preserve spaces, line breaks, '/', and ':'
    filtered_text = re.sub(r'[^A-Za-z0-9\s\n/:]', '', text)
    return filtered_text


if __name__ == "__main__":
    # Input image path
    image_path = "img/Bhargavi_aadhar.jpg"  # Replace with your image path

    try:
        # Preprocess the image
        logging.info("Preprocessing the image...")
        preprocessed_img = preprocess_image(image_path)

        # Detect text regions
        logging.info("Detecting text regions...")
        bounding_boxes = detect_text_regions(preprocessed_img)

        # Extract text from detected regions
        logging.info("Extracting text from detected regions...")
        extracted_texts = extract_text_from_regions(
            preprocessed_img, bounding_boxes, languages="eng+tel")

        # Post-process and display the extracted text
        for i, text in enumerate(extracted_texts):
            cleaned_text = post_process_text(text)
            logging.info(
                f"\nExtracted Text from Region {i+1}:\n{cleaned_text}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
