from flask import Flask, request, Response
import os
from google import genai
import json

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCAbZBgv8pzC7o-m0SoPlQerQvlQwZPH68"
client = genai.Client(api_key=GEMINI_API_KEY)

@app.route('/')
def home():
    return "Agri Bot API with Gemini AI ✅"

SYSTEM_INSTRUCTION = """ 
[... keep the full system instruction exactly as you had it ...]
"""

@app.route('/ask', methods=['POST'])
def ask_bot():
    data = request.get_json()
    question = data.get('question')
    if not question:
        return Response(
            json.dumps({'error': 'Missing question'}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

    try:
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nপ্রশ্ন: {question}\n\nউত্তর দিন:"
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        answer = resp.text

        # ✅ Proper UTF-8 JSON response
        response_data = {'answer': answer}
        return Response(
            json.dumps(response_data, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
    except Exception as e:
        return Response(
            json.dumps({'error': str(e)}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
