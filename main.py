from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Load your Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCAbZBgv8pzC7o-m0SoPlQerQvlQwZPH68"
genai.configure(api_key=GEMINI_API_KEY)

# Load the Gemini Pro model
model = genai.GenerativeModel('gemini-pro')

@app.route('/')
def home():
    return "Agri Bot API with Gemini AI ✅"

@app.route('/ask', methods=['POST'])
def ask_bot():
    data = request.get_json()
    question = data.get('question')

    try:
        response = model.generate_content(question)
        return jsonify({'answer': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
