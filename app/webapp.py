
import os
import zipfile
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

# Import functions from your original script
from songselect_to_pptx import lyric_converter

# Set up logging
logging.basicConfig(level=logging.INFO)

def get_version():
    """Get app version"""
    # Look for app_version file
    version_file = Path('sslc_app_version')
    if version_file.exists():
        return version_file.read_text().strip()
    
    # Alternatively use an env variable
    if 'SSLC_APP_VERSION' in os.environ:
        return os.environ['SSLC_APP_VERSION']
    
    # Default value
    return 'flask-dev-build'

APP_VERSION = get_version()
logging.debug(f'APP_VERSION var = {APP_VERSION}')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Below is used if a proxy is in front of flask
# If only using WSGI set to 1
# If using a reverse proxy with WSGI set to 2
proxy_num = 2
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=proxy_num, x_proto=proxy_num, x_host=proxy_num, x_prefix=proxy_num
)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
logging.debug('Temp file directory... ' + app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def index():
    base_url = '/'
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'files[]' not in request.files:
            flash('No file part', 'danger')
            return redirect(base_url)
            
        files = request.files.getlist('files[]')
        logging.debug(f'Upload file list... {files}')
        
        # Check if files were selected
        if not files or files[0].filename == '':
            flash('No files selected', 'danger')
            return redirect(base_url)
        
        # Check that we don't exceed 10 files
        if len(files) > 10:
            flash('Maximum 10 files allowed', 'danger')
            return redirect(base_url)
        
        pptx_file_list = []
        # Create temp dir to store pptx files in
        tmp_pptx_dir_name = 'ohc_pptx_files'
        os.makedirs(tmp_pptx_dir_name, exist_ok=True)
        for file in files:
            # Loop through uploaded files
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                logging.debug(f'filename var = {filename}')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logging.debug(f'filepath var = {filepath}')
                file.save(filepath)
                try:
                    # Convert lyric file to PPTX
                    pptx_file_location = lyric_converter(filepath, tmp_pptx_dir_name)
                    logging.debug(f'pptx_file_location var = {pptx_file_location}')

                    pptx_file_list.append({
                        'pptx_file_location': f'{pptx_file_location}'
                    })
                except Exception as e:
                    logging.error(f"Error processing {filename}: {str(e)}")
                    flash(f"Error processing {filename}: {str(e)}", 'danger')
        if pptx_file_list:
            logging.debug(f'pptx_file_list var = {pptx_file_list}')
            iso_timestamp = datetime.now().replace(microsecond=0).isoformat()
            try:
                zip_filename = f'ohc-lyric-pptx-{iso_timestamp}.zip'
                logging.debug(f'zip_filename var = {zip_filename}')
                zip_filepath = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

                with zipfile.ZipFile(zip_filepath, 'w') as zip_folder:
                    for pptx_file in pptx_file_list:
                        zip_folder.write(pptx_file['pptx_file_location'])
                return send_file(
                    zip_filepath,
                    as_attachment=True,
                    download_name=zip_filename
                )
            except Exception as e:
                logging.error(f'Error creating zip file: {str(e)}')
                flash(f'Error creating zip file: {str(e)}', 'danger')
                return redirect(base_url)
            finally:
                # Cleanup temp pptx dir
                shutil.rmtree(tmp_pptx_dir_name)
        
    return render_template('index.html', sslc_version=APP_VERSION)

def allowed_file(filename):
    """Check if the uploaded file is a text file"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'txt'

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 10MB.', 'danger')
    return redirect(url_for('index'))

@app.teardown_appcontext
def cleanup(exception=None):
    """Clean up temporary files when the app context ends"""
    try:
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        # Create a new temporary directory for the next request
        app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except Exception as e:
        logging.error(f"Error cleaning up temporary files: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
