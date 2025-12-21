from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
import cv2
import re
import numpy as np
from PIL import Image
import pytesseract
from ingestion.config import POPPLER_PATH, TESSERACT_CMD
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def infer_ocr(file_path: Path, *, page_num: int | None = None) -> str:
    print("[infer_ocr]", file_path, "ext=", file_path.suffix.lower(), "page_num=", page_num)

    if page_num is not None:
        result = ocr_pdf_page(file_path, page_num)
    result = ocr_image(file_path)

    if determine_ocr_feasibility(result):
        return result


def ocr_pdf_page(file_path: Path, page_num: int) -> str:
    images = convert_from_path(
        str(file_path), first_page=page_num, last_page=page_num, poppler_path=POPPLER_PATH)
    if not images:
        return ""
    ocr_result = pytesseract.image_to_string(
        images[0], lang="eng", config="--psm 6")
    print(ocr_result)
    normalised_text = normalize_ocr_text(ocr_result)    
    return normalised_text


def ocr_image(file_path: Path) -> str:
    if not file_path.exists():
        return ""
    with Image.open(file_path) as img:
        processed = preprocess_for_ocr(img)
        ocr_result = pytesseract.image_to_string(processed, lang="eng", config="--oem 3 --psm 4")
        normalised_text = normalize_ocr_text(ocr_result)
    return normalised_text


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray_scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_scale_contrast = cv2.equalizeHist(gray_scale)
    no_noise_gray_scale_contrast = cv2.medianBlur(gray_scale_contrast, 3)

    preprocessed_image_thresh = cv2.adaptiveThreshold(
        no_noise_gray_scale_contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    
    processed_image = Image.fromarray(preprocessed_image_thresh)

    # cv2.imwrite("tests/processed.png", preprocessed_image_thresh)

    return processed_image


def normalize_ocr_text(text: str) -> str:
    text = text.upper()
    text = re.sub(r"[^\w\s.,:;!?()-]", "", text) # Removes malformed text
    text = re.sub(r"\s{2,}", " ", text) # whitespace normalisation
    # filter out noise
    lines = [
        line.strip()
        for line in text.splitlines()
        if len(line.strip()) > 8
        and sum(c.isalpha() for c in line) / max(len(line), 1) > 0.6 # threshold > 60%
    ]
    return "\n".join(lines)


def determine_ocr_feasibility(text: str) -> bool:

    print('OCR RESULT: ', text)

    if len(text) < 80: # threshold > 80%
        return False
    alpha_ratio = sum(c.isalpha() for c in text) / len(text)
    print(alpha_ratio)
    if alpha_ratio < 0.75:
        print('[WARN] OCR IS NOT FEASIBLE FALLING BACK TO VL (expensive) ...')
        return False
    return True
