from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "PASTE_YOUR_API_KEY_HERE"
genai.configure(api_key=GEMINI_API_KEY)

# Use the latest correct model setup
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 1024
}

model = genai.GenerativeModel(
    model_name="models/gemini-pro",
    generation_config=generation_config
)

@app.route('/')
def home():
    return "Agri Bot API with Gemini AI ✅"

@app.route('/ask', methods=['POST'])
def ask_bot():
    data = request.get_json()
    question = data.get('question')

    try:
        response = model.generate_content([question])
        return jsonify({'answer': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
