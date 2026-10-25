import logging
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, render_template, request, send_file
from werkzeug.middleware.proxy_fix import ProxyFix

from songselect_to_pptx import lyric_converter

logging.basicConfig(level=logging.INFO)


def get_version():
    version_file = Path(__file__).with_name('sslc_app_version')
    if version_file.exists():
        return version_file.read_text().strip()
    return os.getenv('SSLC_APP_VERSION', 'flask-dev-build')


APP_VERSION = get_version()
MAX_LYRIC_FILE_SIZE = 256 * 1024
app = Flask(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    MAX_FORM_MEMORY_SIZE=128 * 1024,
    MAX_FORM_PARTS=20,
)
if os.getenv('TRUSTED_HOSTS'):
    app.config['TRUSTED_HOSTS'] = os.environ['TRUSTED_HOSTS'].split(',')

# Only enable behind a trusted proxy that replaces incoming forwarded headers.
proxy_count = int(os.getenv('TRUSTED_PROXY_COUNT', '0'))
if proxy_count < 0:
    raise ValueError('TRUSTED_PROXY_COUNT must be non-negative')
if proxy_count:
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=proxy_count, x_proto=proxy_count,
        x_host=0, x_port=0, x_prefix=0,
    )


def render_index(error=None, status=200):
    return render_template('index.html', sslc_version=APP_VERSION, error=error), status


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_index()
    if request.headers.get('Sec-Fetch-Site') == 'cross-site':
        return render_index('Cross-site uploads are not allowed.', 403)

    files = request.files.getlist('files[]')
    if not files or all(not file.filename for file in files):
        return render_index('Select at least one lyric file.', 400)
    if len(files) > 10:
        return render_index('Maximum 10 files allowed.', 400)
    if any(not allowed_file(file.filename) for file in files):
        return render_index('Only .txt lyric files are allowed.', 400)

    # Each request owns its uploads and presentations; no shared paths or teardown.
    archive = tempfile.SpooledTemporaryFile(max_size=1024 * 1024, mode='w+b')
    try:
        with tempfile.TemporaryDirectory(prefix='ohc-lyrics-') as work_dir:
            with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
                used_names = set()
                for file in files:
                    content = file.stream.read(MAX_LYRIC_FILE_SIZE + 1)
                    if len(content) > MAX_LYRIC_FILE_SIZE:
                        return render_index('Each lyric file must be 256 KiB or smaller.', 413)
                    song_dir = Path(tempfile.mkdtemp(prefix='song-', dir=work_dir))
                    input_path = song_dir / 'lyrics.txt'
                    input_path.write_bytes(content)
                    output_path = Path(lyric_converter(input_path, song_dir))
                    archive_name = output_path.name
                    suffix = 2
                    while archive_name.casefold() in used_names:
                        archive_name = f'{output_path.stem}-{suffix}.pptx'
                        suffix += 1
                    used_names.add(archive_name.casefold())
                    bundle.write(output_path, arcname=archive_name)
        archive.seek(0)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        response = send_file(
            archive, mimetype='application/zip', as_attachment=True,
            download_name=f'ohc-lyric-pptx-{timestamp}.zip',
            conditional=False, etag=False, max_age=0,
        )
        # Keep the archive open until WSGI finishes sending it, then release it.
        response.direct_passthrough = False
        response.call_on_close(archive.close)
    except (ValueError, UnicodeError):
        return render_index('Invalid lyric file. Use a UTF-8 SongSelect text export.', 400)
    except Exception:
        app.logger.exception('Lyric conversion failed')
        return render_index('Conversion failed. Please try again with a SongSelect text export.', 500)
    finally:
        # On success the response owns the archive; close it on all failure paths.
        if 'response' not in locals():
            archive.close()
    return response


def allowed_file(filename):
    return bool(filename) and '.' in filename and filename.rsplit('.', 1)[1].lower() == 'txt'


@app.errorhandler(413)
def too_large(error):
    return render_index('Upload too large. Maximum total size is 10 MiB.', 413)


@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self'; object-src 'none'; base-uri 'none'; "
        "frame-ancestors 'none'; form-action 'self'"
    )
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
