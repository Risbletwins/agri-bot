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

SYSTEM_INSTRUCTION = """
আপনি একজন বন্ধুবান্ধব গ্রামীন কৃষি সহকারী। 
আপনার কাজ হলো কৃষকের প্রশ্ন বুঝে সহজ, ছোট, আর সহজে বোঝা যায় এমন উত্তর দেয়া। 
যেমন করে একজন বয়স্ক লোক বা অশিক্ষিত কৃষক বুঝতে পারে। 
অতিরিক্ত ইংরেজি বা কঠিন ভাষা ব্যবহার করবেন না। 
প্রয়োজনে উদাহরণ দিন যেন কৃষক সহজে বুঝতে পারে।
"""

@app.route('/ask', methods=['POST'])
def ask_bot():
    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({'error': 'Missing question'}), 400

    try:
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nপ্রশ্ন: {question}\n\nউত্তর দিন:"
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        answer = resp.text
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
