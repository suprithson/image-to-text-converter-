from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from googletrans import Translator
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to convert PDF to text using OCR
def pdf_to_text(pdf_path):
    images = convert_from_path(pdf_path)
    text = ''
    for img in images:
        text += pytesseract.image_to_string(img)
    return text

## Route for the main page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # Check if the file is selected
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        # Check if the file extension is allowed
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            return redirect(url_for('select_language', filename=filename))  # Redirect to select_language route
    return render_template('index.html')

# Route for selecting the language
@app.route('/select_language/<filename>', methods=['GET', 'POST'])
def select_language(filename):
    if request.method == 'POST':
        language = request.form['language']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        text = pdf_to_text(file_path)
        translator = Translator()
        translated_text = translator.translate(text, dest=language).text
        return render_template('result.html', original_text=text, translated_text=translated_text, language=language)
    return render_template('select_language.html')

if __name__ == '__main__':
    app.run(debug=True)
