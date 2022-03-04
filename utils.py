import json
import random
import logging
import spacy
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

def convert_dataturks_to_spacy(dataturks_JSON_FilePath):
    try:
        training_data = []
        lines=[]
        with open(dataturks_JSON_FilePath, 'r') as f:
            lines = f.readlines()

        for line in lines:
            data = json.loads(line)
            text = data['content']
            entities = []
            for annotation in data['annotation']:
                #only a single point in text annotation.
                point = annotation['points'][0]
                labels = annotation['label']
                # handle both list of labels or a single label.
                if not isinstance(labels, list):
                    labels = [labels]

                for label in labels:
                    #dataturks indices are both inclusive [start, end] but spacy is not [start, end)
                    entities.append((point['start'], point['end'] + 1 ,label))
            training_data.append((text, {"entities": entities}))
        return training_data
    except Exception as e:
        logging.exception("Unable to process " + dataturks_JSON_FilePath + "\n" + "error = " + str(e))
        return None

def trim_entity_spans(data: list) -> list:
    """Removes leading and trailing white spaces from entity spans.

    Args:
        data (list): The data to be cleaned in spaCy JSON format.

    Returns:
        list: The cleaned data.
    """
    invalid_span_tokens = re.compile(r'\s')

    cleaned_data = []
    for text, annotations in data:
        entities = annotations['entities']
        valid_entities = []
        for start, end, label in entities:
            valid_start = start
            valid_end = end
            while valid_start < len(text) and invalid_span_tokens.match(
                    text[valid_start]):
                valid_start += 1
            while valid_end > 1 and invalid_span_tokens.match(
                    text[valid_end - 1]):
                valid_end -= 1

            valid_entities.append([valid_start, valid_end, label])
        cleaned_data.append([text, {'entities': valid_entities}])

    return cleaned_data

def trim_special_characters(data: list) -> list:

    special_character = re.compile(r'\W')

    cleaned_data = []
    for text, annotations in data:
        entities = annotations['entities']
        valid_entities = []
        for start, end, label in entities:
            valid_start = start
            valid_end = end
            while valid_start < len(text) and special_character.match(
                    text[valid_start]):
                valid_start += 1
            while valid_end > 1 and special_character.match(
                    text[valid_end - 1]) and text[valid_end-1]!='#':
                valid_end -= 1

            valid_entities.append([valid_start, valid_end, label])
        cleaned_data.append([text, {'entities': valid_entities}])

    return cleaned_data

def read_data(path):
    training_data = []
    json_lst = glob.glob(path)
    for direc in json_lst:
        f = open(direc)
        data = json.load(f)
        for text, entity in data['annotations']:
            if (len(text) != 0) and (len(entity['entities'])!=0):
                training_data.append((text, entity))
        f.close()
    return training_data

def correct_label(label):
    label_correction_dic = {'Email Address': 'EMAIL ADDRESS',
                            'College Name': 'COLLEGE NAME',
                            'Degree': 'DEGREE',
                            'Location': 'LOCATION',
                            'Skills': 'SKILLS',
                            'Companies worked at': 'COMPANIES WORKED AT',
                            'Name': 'NAME',
                            'DESIGNATION ': 'DESIGNATION',
                            'Designation': 'DESIGNATION',
                            'Years of Experience': 'YEARS OF EXPERIENCE',
                            'Graduation Year': 'GRADUATION YEAR'
                            }
    if label in label_correction_dic:
        return label_correction_dic[label]
    return label

def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    # codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text
