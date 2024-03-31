from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import base64
from datetime import datetime
from google.cloud import storage
import logging
import subprocess
import os
import sys

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

bucket_name = 'shelley_photos'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/receive-image-url', methods=['POST'])
def receive_image_url():
    try:
        data = request.get_json()
        if not data or 'imageData' not in data:
            return jsonify({'error': 'Invalid image data'}), 400

        image_data = base64.b64decode(data['imageData'].split(",")[1])
        filename = f"raw_photos/image_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_data, content_type='image/png')

        public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"

        # Path to the Python executable running the Flask app & path to the script
        python_executable = sys.executable
        script_path = os.path.expanduser('~/Experiments/betaface3.py')

        # Call the script with the image URL
        subprocess.Popen([python_executable, script_path, public_url])

        logging.info(f"Image processed by betaface3.py: {filename}")

        return jsonify({'url': public_url}), 200

    except subprocess.CalledProcessError as e:
        logging.error(f"betaface3.py script error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to process image with betaface3.py'}), 500

    except Exception as e:
        logging.error(f"Failed to upload image: {e}", exc_info=True)
        return jsonify({'error': 'Failed to upload image'}), 500

@socketio.on('stream_data')
def handle_stream_data(data):
    emit('stream_response', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)