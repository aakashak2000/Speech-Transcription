import os
from diar import *
from werkzeug.utils import secure_filename
from flask import Flask, send_from_directory, Response, flash, request, redirect, url_for, render_template

UPLOAD_FOLDER = './audioFiles/'
ALLOWED_EXTENSIONS = {'WAV', 'wav', 'mp3'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'MYSECRETKEY'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods = ['GET', 'POST'])
def upload_file():
    allScripts = []
    warn = '*This might take a few minutes'
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            audioFile = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            scripts = getScript(audioFile)
            allScripts = scripts
            if os.path.exists(audioFile):
                os.remove(audioFile)

    return render_template('index.html', allScripts = allScripts, warn=warn)

@app.route('/audioFiles/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main___':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
