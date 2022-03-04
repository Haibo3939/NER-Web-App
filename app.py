from flask import Flask,url_for,render_template,request,flash,redirect
import spacy
from spacy import displacy
import json
import pandas as pd
import numpy as np
from pathlib import Path

import random
import logging
import sys
import re
import tqdm
import glob
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import glob, os
from utils import convert_pdf_to_txt
from werkzeug.utils import secure_filename

HTML_WRAPPER = """<div style="overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem">{}</div>"""

from flaskext.markdown import Markdown

#initialize upload path
UPLOAD_FOLDER = "/Users/haibo/NER WEB APP/uploads"

ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["ALLOWED_EXTENSIONS"] = ALLOWED_EXTENSIONS
Markdown(app)

#load model
model = spacy.load(r"./models/bert_fine_tuned")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route("/upload-pdf", methods=["GET", "POST"])
def upload_pdf():
    if request.method == "POST":

        if request.files:
            pdf = request.files["pdf"]

            if pdf.filename == "":
                print("PDF must have a filename!")
                return redirect(request.url)

            if not allowed_file(pdf.filename):
                print("File type not allowed!")
                return redirect(request.url)

            filename = secure_filename(pdf.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf.save(save_path)

            print(convert_pdf_to_txt(save_path))
            raw_text = convert_pdf_to_txt(save_path)
            docx = model(raw_text)
            html = displacy.render(docx, style="ent")
            html = html.replace("\n\n", "\n")
            result = HTML_WRAPPER.format(html)


    return render_template('result.html', rawtext=raw_text, result=result)


if __name__ == '__main__':
	app.run(debug=True)