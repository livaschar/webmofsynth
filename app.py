from src.mofsynth import utils
from werkzeug.utils import secure_filename
import pickle
import json
import time
import os
import pandas as pd
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_file
import secrets
import string
import shutil
from pathlib import Path
from flask_caching import Cache
from flask_compress import Compress
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
# from flask_assets import Environment, Bundle # add later on a need basis

SESSION_DURATION = 30 # in minutes

app = Flask(__name__)
cache = Cache(config={'CACHE_TYPE': 'redis'})
cache.init_app(app)
Compress(app)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=SESSION_DURATION)
# assets = Environment(app)
# js = Bundle

session_store = {}


def cleanup_expired_sessions():
    current_time = datetime.now()
    expired_sessions = [s for s, expiry in session_store.items() if expiry < current_time]
    for s in expired_sessions:
        directory = "/home/" + os.getlogin() + "/SITE/folders/" + s
        delete_directory(directory)
        del session_store[s]
    if expired_sessions != []:
        print(f"Expired sessions cleaned up: {expired_sessions}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_expired_sessions, trigger="interval", seconds=60)
scheduler.start()

''' random FOLDER GENERATOR '''
def generate_random_string(length):
    characters = string.ascii_letters  # Includes both uppercase and lowercase letters
    return ''.join(secrets.choice(characters) for _ in range(length))

# Function to create session-specific folders if they don't exist
def create_session_folders(random_str):
    session_folder = os.path.join(BASE_FOLDER, random_str)
    UPLOAD_FOLDER = os.path.expanduser('~/SITE/folders/%s/uploads' %random_str)
    INPUT_FOLDER = os.path.expanduser('~/SITE/folders/%s/input_data' %random_str)
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

BASE_FOLDER = os.path.expanduser('~/SITE/folders')
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

def refresh_session():
    if not session:
        session.permanent = True
        session.modified = True

def session_clear():
    if 'EXECUTION_FOLDER' in session:
        delete_directory(session['EXECUTION_FOLDER'])
    session.clear()


@app.route('/reload', methods=['POST'])
def page_reload():
    print('User reloaded or left')
    
    session_clear()

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
        return jsonify({'error': 'No selected file'}), 400

    files = request.files.getlist('file')

    # Initialize file count and filenames in session if not already present
    if 'file_count' not in session:
        session['file_count'] = 0
    if 'filenames' not in session:
        session['filenames'] = []

    # Check if file count exceeds the limit (10)
    if len(files) > 10:
        return jsonify({'error': 'Upload limit exceeded.\nYou can upload up to 10 files.'}), 400
    
    if 'first_visit' not in session:
        # print('First visit')
        refresh_session()
        session['first_visit'] = True
        random_str = generate_random_string(10)
        UPLOAD_FOLDER, EXECUTION_FOLDER = create_session_folders(random_str)
        session['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        session['EXECUTION_FOLDER'] = EXECUTION_FOLDER
        userID = EXECUTION_FOLDER.rsplit('/', 1)[-1]
        session_store[userID] = datetime.now() + app.config['PERMANENT_SESSION_LIFETIME']
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
            try:
                file.save(os.path.join(session['UPLOAD_FOLDER'], filename))
            except:
                return jsonify({'error': '404'}), 400
            
            if filename not in session['filenames']:
                session['file_count'] += 1
                session['filenames'].append(filename)
        else:
            return jsonify({'error': 'Invalid file type.\nAllowed file types: .cif'}), 400

    print("Session in upload:", session)

    return jsonify({'message': 'Files uploaded successfully', 'filenames': filenames}), 200


@app.route('/submit-job', methods=['POST'])
def submit_job():
    
    # Session resets for some reason somewhere after upload_file() and before submit_job()
    print("Session in submit:", session)

    option = request.form.get('option')
    if not option:
        return jsonify({'error': 'No option selected.\nNan is a safe option.\nAdvise the paper for further information.'}), 400

    try:    
        # Execute the command and capture output
        main_run_result, error, user, discarded = utils.main_run('uploads', option, session['EXECUTION_FOLDER'])
        
        if main_run_result == 0:
            return jsonify({'error': error}), 400
        
        # utils.main_run was succesful
        elif main_run_result == 1:
            print('utils.main_run was succesfull' )
            
            # check which of the runs have finished and which not 
            counter = 0
            len_remaining_files = session.get('file_count', 0) - len(discarded.keys())
            while counter < 5 :
                print('\nCounter: ', counter)
                check_opt_result, converged, not_converged = utils.check_opt(session['EXECUTION_FOLDER'], len_remaining_files, user)
                if check_opt_result == 0 or check_opt_result == -1:
                    print('  Check opt is:', check_opt_result, '\n')
                    time.sleep(3)
                    counter += 1
                elif check_opt_result == 1:
                    break
            
            if check_opt_result == 0:
                utils.handle_non_convergence(user, not_converged, discarded, session['EXECUTION_FOLDER'])
            elif check_opt_result == -1:
                return jsonify({'error': 'None of the provided CIFs could be optimized'}), 400
            
            export_result, message = utils.export_results(session['EXECUTION_FOLDER'], user)
            if export_result == 1:                  
                return jsonify({'message': message })
            elif export_result == 0:
                return jsonify({'error': 'Evaluation was succesful. Error processing the results.'}), 400
        
        # An error occured in utils.main_run
        else:
            return jsonify({'error': 'Error submitting job'}), 400
    
    except Exception as e:
        return jsonify({'error': f'Exception occurred. {str(e)}', 'details': str(e)}), 400


@app.route('/show-csv')
def show_csv():

    file_path = os.path.join(session['EXECUTION_FOLDER'], 'Synth_folder', 'synth_results.csv')

    try:
        if os.path.exists(file_path):
            
            df = pd.read_csv(file_path)
            converged_table = df.to_html(classes='table table-striped table-bordered table-hover', index=False)
            session['converged_table'] = converged_table
            
            discarded_path = os.path.join(session['EXECUTION_FOLDER'], 'discarded.json')
            with open(discarded_path, 'r') as json_file:
                discarded_data = json.load(json_file)
            
            if discarded_data:
                discarded_df = pd.DataFrame(list(discarded_data.items()), columns=['File', 'Error Message'])
                print(f'discarded_df {discarded_df}')
                discarded_table_html = discarded_df.to_html(classes='table table-striped table-bordered table-hover', index=False)
            else:
                discarded_table_html = "<p>No discarded files.</p>"
            session['discarded_table'] = discarded_table_html
            
            return jsonify({'success': True})
        
        else:
            return jsonify({'error': 'File not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/print-results')
def print_results():
    # Retrieve tables from session
    converged_table = session.get('converged_table')
    discarded_table = session.get('discarded_table')
    if discarded_table == "<p>No discarded files.</p>":
        return render_template('results.html', converged_table=converged_table)
    else:
        return render_template('results.html', converged_table=converged_table, discarded_table=discarded_table)


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
    try: 
        app.run(host='0.0.0.0', port=5000, debug=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
