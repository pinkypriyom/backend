from flask import Flask, request, send_file
from flask_cors import CORS
from gtts import gTTS

app = Flask(__name__)
CORS(app)

@app.route('/api/tts', methods=['POST'])
def tts():
    text = request.json.get('text', '')
    if not text:
        return {'error': 'No text provided'}, 400

    tts = gTTS(text)
    filename = 'output.mp3'
    tts.save(filename)
    return send_file(filename, mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(port=5000)
