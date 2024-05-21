from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from googletrans import Translator
import os
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import pandas as pd
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_images_and_extract_text(pdf_path, output_image='PDF_image.png'):
    images = convert_from_path(pdf_path, dpi=300)
    text = ''
    for img in images:
        text += pytesseract.image_to_string(img)
    return text

def parse_ocr_text_to_df(ocr_text, languages=['es', 'te']):
    translator = Translator()
    lines = ocr_text.strip().split("\n")
    columns = ['Text'] + languages
    data = []
    for line in lines:
        if line.strip():
            row = {'Text': line.strip()}
            for lang in languages:
                row[lang] = translator.translate(line.strip(), dest=lang).text
            data.append(row)

    df = pd.DataFrame(data)
    return df

def extract_text_from_pdf_images(pdf_path, languages=['es', 'el']):
    text_from_images = {}
    for page_num, page_layout in enumerate(extract_pages(pdf_path)):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                crop_image(element, pdf_path, page_num)
                ocr_text = convert_to_images_and_extract_text('cropped_image.pdf')
                df = parse_ocr_text_to_df(ocr_text, languages=languages)
                text_from_images[f'Page_{page_num}'] = df
                os.remove('cropped_image.pdf')
    return text_from_images

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            extracted_data = extract_text_from_pdf_images(file_path)
            return render_template('result.html', extracted_data=extracted_data)
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
