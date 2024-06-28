from flask import Flask, render_template, jsonify, request
#from src.mofsynth import utils

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/results', methods=['GET'])
# def get_results():
#     utils.export_results()
#     return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=False)

