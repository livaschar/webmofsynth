from src.mofsynth import utils
from werkzeug.utils import secure_filename
import subprocess
import time
import os
import pandas as pd
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_file
app = Flask(__name__)

original_folder = os.getcwd()

# Define a folder to store uploaded files
# UPLOAD_FOLDER = '../random_user_dion/uploads'
UPLOAD_FOLDER = os.path.expanduser('~/TEST/repos/random_user_dion/uploads')
ALLOWED_EXTENSIONS = {'cif'}
MAX_FILESIZE = 5 * 1024 * 1024  # 5 MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILESIZE

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Configuration
EXECUTION_FOLDER = os.path.expanduser('~/TEST/repos/random_user_dion')
app.config['EXECUTION_FOLDER'] = EXECUTION_FOLDER


app.secret_key = 'any_key'  # Necessary for using sessions


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])

def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    files = request.files.getlist('file')

    # Initialize file count in session if not already present
    if 'file_count' not in session:
        session['file_count'] = 0

    # Check if file count exceeds the limit (10)
    if session['file_count'] + len(files) > 10:
        return jsonify({'error': 'Upload limit exceeded. You can upload up to 10 files.'}), 400

    filenames = []

    for file in files:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            if file.content_length > app.config['MAX_CONTENT_LENGTH']:
                return jsonify({'error': 'File size exceeds limit of 5MB'}), 400

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)

            # Increment file count in session
            session['file_count'] += 1
        else:
            return jsonify({'error': 'Invalid file type. Allowed file types: .cif'}), 400

    return jsonify({'message': 'Files uploaded successfully', 'filenames': filenames}), 200


@app.route('/submit-job', methods=['POST'])
def submit_job():
    
    option = request.form.get('option')
    if not option:
        return jsonify({'error': 'No option selected'})

    original_folder = os.getcwd()
    print("Must be webmofsynth: ", original_folder)

    try:
        # Change directory to the execution folder
        os.chdir(EXECUTION_FOLDER)
        print("Must be random_user_dion id: ", os.getcwd())

        # Execute the command and capture output
        result = utils.main_run('uploads', option, EXECUTION_FOLDER)
        # time.sleep(10)

        # Check for errors or success based on command output
        if result == 1:
            return jsonify({'message': 'Job submitted successfully'})
        else:
            return jsonify({'error': 'Error submitting job'})
    
    except Exception as e:
        return jsonify({'error': 'Exception occurred', 'details': str(e)})
    
    finally:
        # Change back to the original working directory
        os.chdir(original_folder)
    

@app.route('/fetch-results', methods=['GET'])
def fetch_results():
    result = utils.export_results(EXECUTION_FOLDER)
    # Check for errors or success based on command output
    if result == 1:
        return jsonify({'message': 'Results fetched succesfully'})
    else:
        return jsonify({'error': 'Results were not fetched'})

@app.route('/read-csv')
def read_csv():
    print("Current directory:", os.getcwd())
    file_path = os.path.join(os.getcwd(), '../random_user_dion/Synth_folder', 'synth_results.csv')

    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            table_html = df.to_html(classes='table table-striped table-bordered table-hover', index=False)
            session['table_html'] = table_html
            return jsonify({'table': table_html})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/print-results')
def print_results():
    table_html = session.get('table_html')
    if table_html:
        return render_template('results.html', table=table_html)
    else:
        return render_template('error.html', error='No data to display')

@app.route('/download-csv')
def download_csv():
    csv_file_path = os.path.join(EXECUTION_FOLDER, 'Synth_folder/synth_results.csv')
    print('Ok: ', csv_file_path)
    
    # Ensure the file exists
    if not os.path.exists(csv_file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(csv_file_path, as_attachment=True)


# @app.route('/read-file', methods=['GET'])
# def read_file():
#     # Define the file path
#     file_path = os.path.join(os.getcwd(), '../random_user_dion/Synth_folder', 'synth_results.txt')
    
#     # Check if the file exists
#     if os.path.exists(file_path):
#         with open(file_path, 'r') as file:
#             file_contents = file.read()
#         return jsonify({'file_contents': file_contents})
#     else:
#         return jsonify({'error': 'File not found'}), 404




    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
    # app.run(debug=False)

