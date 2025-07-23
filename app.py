from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import boto3
import uuid
import os
import json
import threading

app = Flask(__name__)
CORS(app)

# Directories for audio + timing
AUDIO_DIR = 'audio'
MARKS_DIR = 'marks'

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(MARKS_DIR, exist_ok=True)

# AWS Polly client
polly = boto3.client('polly', region_name='us-east-1')

# Delete files after 10 minutes
def delete_files_later(audio_path, marks_path, delay=600):
    def delete():
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
            if os.path.exists(marks_path):
                os.remove(marks_path)
            print(f"[Deleted] {audio_path} and {marks_path}")
        except Exception as e:
            print("Error deleting files:", e)

    threading.Timer(delay, delete).start()

# POST /api/tts
@app.route('/api/tts', methods=['POST'])
def generate_tts():
    data = request.get_json()
    text = data.get('text', '')
    language = data.get('language', 'en')

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    # Choose Polly voice
    voice_map = {
        'en': 'Joanna',
        'hi': 'Aditi',
        'bn': 'Raveena',
        'es': 'Lupe',
        'fr': 'Celine'
    }
    voice = voice_map.get(language, 'Joanna')

    # Unique filenames
    uid = str(uuid.uuid4())
    audio_filename = f"{uid}.mp3"
    marks_filename = f"{uid}.json"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)
    marks_path = os.path.join(MARKS_DIR, marks_filename)

    # Generate audio
    audio_res = polly.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId=voice
    )
    with open(audio_path, 'wb') as f:
        f.write(audio_res['AudioStream'].read())

    # Generate speech marks
    marks_res = polly.synthesize_speech(
        Text=text,
        OutputFormat='json',
        VoiceId=voice,
        SpeechMarkTypes=['word']
    )
    marks_lines = marks_res['AudioStream'].read().decode('utf-8').splitlines()
    marks_json = [json.loads(line) for line in marks_lines]
    with open(marks_path, 'w') as f:
        json.dump(marks_json, f)

    # Schedule deletion
    delete_files_later(audio_path, marks_path)

    return jsonify({
        'audio': audio_filename,
        'marks': marks_filename
    })

# Serve audio file
@app.route('/api/audio/<filename>')
def get_audio(filename):
    return send_file(os.path.join(AUDIO_DIR, filename), mimetype='audio/mpeg')

# Serve marks file
@app.route('/api/marks/<filename>')
def get_marks(filename):
    path = os.path.join(MARKS_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(port=5000)
