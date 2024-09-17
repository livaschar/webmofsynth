from src.mofsynth import utils
from werkzeug.utils import secure_filename
# import subprocess
import time
import os
import pandas as pd
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_file
import secrets
import string
import shutil
from pathlib import Path

app = Flask(__name__)

''' random FOLDER GENERATOR '''
def generate_random_string(length):
    characters = string.ascii_letters  # Includes both uppercase and lowercase letters
    return ''.join(secrets.choice(characters) for _ in range(length))

# Function to create session-specific folders if they don't exist
def create_session_folders(random_str):
    session_folder = os.path.join(BASE_FOLDER, random_str)
    UPLOAD_FOLDER = os.path.expanduser('~/TEST/repos/%s/uploads' %random_str)
    INPUT_FOLDER = os.path.expanduser('~/TEST/repos/%s/input_data' %random_str)
    EXECUTION_FOLDER = session_folder

    # Create folders if they don't exist
    for folder in [session_folder, UPLOAD_FOLDER, INPUT_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # Copy files from the source folder to the input folder
    for item in os.listdir(SOURCE_FOLDER):
        s = os.path.join(SOURCE_FOLDER, item)
        d = os.path.join(INPUT_FOLDER, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    return UPLOAD_FOLDER, EXECUTION_FOLDER

BASE_FOLDER = os.path.expanduser('~/TEST/repos')
SOURCE_FOLDER = os.getcwd() + '/src/mofsynth/input_data'
original_folder = os.getcwd()
# Necessary for using sessions
app.secret_key = '3224dd25ca82b528ad1c59c082185f2880dc59c9c38cf98528acbedc22e086b0'
# app.secret_key = generate_random_string(20)


def delete_directory(dir_path):
    path = Path(dir_path)
    if path.exists():
        if path.is_dir():
            try:
                shutil.rmtree(path)
                print(f"Directory '{path}' and all its contents have been removed.")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"'{path}' is not a directory.")
    else:
        print(f"'{path}' does not exist.")

''' --------------------------- '''


@app.route('/reload', methods=['POST'])
def page_reload():
    print('Page reloaded')
    
    if 'EXECUTION_FOLDER' in session:
        delete_directory(session['EXECUTION_FOLDER'])
    session.clear()

    return jsonify({'status': 'success'})


# File requirements
ALLOWED_EXTENSIONS = {'cif'}
MAX_FILESIZE = 5 * 1024 * 1024  # 5 MB
app.config['MAX_CONTENT_LENGTH'] = MAX_FILESIZE
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    files = request.files.getlist('file')

    # Initialize file count and filenames in session if not already present
    if 'file_count' not in session:
        session['file_count'] = 0
    if 'filenames' not in session:
        session['filenames'] = []

    # Check if file count exceeds the limit (10)
    if len(files) > 10:
        return jsonify({'error': 'Upload limit exceeded. You can upload up to 10 files.'}), 400
    
    if 'first_visit' not in session:
        print('First visit')
        session['first_visit'] = True
        random_str = generate_random_string(10)
        UPLOAD_FOLDER, EXECUTION_FOLDER = create_session_folders(random_str)
        session['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        session['EXECUTION_FOLDER'] = EXECUTION_FOLDER
        print("Created", UPLOAD_FOLDER, "for upload and", EXECUTION_FOLDER, "for execution")

    filenames = []
    for file in files:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            if file.content_length > app.config['MAX_CONTENT_LENGTH']:
                return jsonify({'error': 'File size exceeds limit of 5MB'}), 400

            filename = secure_filename(file.filename)
            filenames.append(filename)
            file.save(os.path.join(session['UPLOAD_FOLDER'], filename))
            session['file_count'] += 1
            session['filenames'].append(filename)
        else:
            return jsonify({'error': 'Invalid file type. Allowed file types: .cif'}), 400

    print("Session in upload:", session)

    return jsonify({'message': 'Files uploaded successfully', 'filenames': filenames}), 200


@app.route('/submit-job', methods=['POST'])
def submit_job():
    
    # Session resets for some reason somewhere after upload_file() and before submit_job()
    print("Session in submit:", session)

    option = request.form.get('option')
    if not option:
        return jsonify({'error': 'No option selected'})

    try:    
        # Execute the command and capture output
        result, user = utils.main_run('uploads', option, session['EXECUTION_FOLDER'])

        # utils.main_run was succesful
        if result == 1:
            print('Result = 1' )
            
            # check which of the runs have finished and which not 
            counter = 0
            finished = False
            while not finished and counter < 10 :
                converged, finished = utils.check_opt(session['EXECUTION_FOLDER'], session.get('file_count', 0), user)
                time.sleep(5)
                counter += 1
            
            # if all runs have finished
            if finished and converged != []:
                
                if session.get('file_count', 0) == 1:
                    print('Entered true mode')
                    result = utils.export_results(session['EXECUTION_FOLDER'], user, compare = True)
                else:
                    result = utils.export_results(session['EXECUTION_FOLDER'], user, compare = False)
                
                # Check for errors or success based on command output
                if result == 1:
                    # return jsonify({'message': 'Runs were succesful. Results are ready.'})
                    return jsonify({'message': 'Runs were succesful. Results are ready.'})
                else:
                    return jsonify({'error': 'Runs were succesful. Error processing the results.'})
            
            elif finished and converged == []:
                return jsonify({'message': 'No run was converged succesfully'})
            
            # if some runs have not finished
            else:
                return jsonify({'message': 'Error handling all/part of your CIFs'})    
        
        # No CIF was found
        elif result == 2:
            return jsonify({'message': 'No CIF to work with'})
        
        # An error occured in utils.main_run
        else:
            return jsonify({'message': 'Error submitting job'})
    
    except Exception as e:
        return jsonify({'error': 'Exception occurred', 'details': str(e)})


@app.route('/show-csv')
def show_csv():

    file_path = os.path.join(session['EXECUTION_FOLDER'], 'Synth_folder', 'synth_results.csv')

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
    csv_file_path = os.path.join(session['EXECUTION_FOLDER'], 'Synth_folder/synth_results.csv')
    
    try:
        # Ensure the file exists
        if os.path.exists(csv_file_path):
            return send_file(csv_file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html'), 404
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
    # app.run(debug=False)
