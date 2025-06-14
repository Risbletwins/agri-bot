from flask import Flask, request, jsonify
import os
from google import genai  # new SDK

app = Flask(__name__)

# Read API key from environment or placeholder
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCAbZBgv8pzC7o-m0SoPlQerQvlQwZPH68"
client = genai.Client(api_key=GEMINI_API_KEY)

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
        resp = client.models.generate_content(
            model="gemini-2.0-flash",  # approved model name
            contents=question
        )
        answer = resp.text
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
