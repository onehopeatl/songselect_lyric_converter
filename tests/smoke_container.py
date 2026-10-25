"""Exercise the real Gunicorn download inside a hardened container."""
import io
import os
from importlib.metadata import version
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
import zipfile

assert os.getuid() != 0, 'Container must run as a non-root user'
assert not os.access('/app/webapp.py', os.W_OK), 'App source must not be writable'
print('Container pip:', version('pip'))
server = subprocess.Popen(['gunicorn', '--config', 'gunicorn_config.py', 'webapp:app'])
try:
    for attempt in range(100):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8080/', timeout=1) as response:
                assert response.status == 200
                assert response.headers['X-Content-Type-Options'] == 'nosniff'
            break
        except (urllib.error.URLError, TimeoutError):
            if server.poll() is not None:
                raise RuntimeError('Gunicorn stopped during startup')
            time.sleep(0.1)
    else:
        raise RuntimeError('Gunicorn did not start')
    boundary = 'ohc-security-smoke-test'
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="files[]"; filename="test.txt"\r\n'
        'Content-Type: text/plain\r\n\r\n'
        'Original Test Song\n\nVerse 1\nAn original lyric\n\nTest Author\nCopyright 2026\n'
        f'\r\n--{boundary}--\r\n'
    ).encode()
    upload = urllib.request.Request(
        'http://127.0.0.1:8080/', data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    )
    with urllib.request.urlopen(upload, timeout=15) as response:
        assert response.headers['Content-Type'] == 'application/zip'
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.namelist() == ['Original_Test_Song.pptx']
        with zipfile.ZipFile(io.BytesIO(archive.read(archive.namelist()[0]))) as pptx:
            assert b'An original lyric' in pptx.read('ppt/slides/slide2.xml')
    assert not list(Path('/tmp').glob('ohc-lyrics-*')), 'Request files leaked'
    print('PASS: non-root Gunicorn serves a complete PPTX ZIP with read-only app files and cleans uploads')
finally:
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()
