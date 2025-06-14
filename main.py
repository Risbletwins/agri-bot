from flask import Flask, request, jsonify, send_file
from gtts import gTTS
import io
import os
from google import generativeai as genai  # ✅ correct import

app = Flask(__name__)

# Initialize Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "YOUR_API_KEY_HERE"
genai.configure(api_key=GEMINI_API_KEY)

@app.route('/')
def home():
    return "Agri Bot API with Gemini AI ✅"

@app.route('/ask', methods=['POST'])
def ask_bot():
    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({'error': 'Missing question'}), 400

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")  # ✅ correct model
        response = model.generate_content(question)
        return jsonify({'answer': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts', methods=['POST'])
def bangla_tts():
    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({'error': 'Missing text'}), 400

    try:
        tts = gTTS(text=text, lang='bn')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return send_file(mp3_fp, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
