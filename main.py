from flask import Flask, request, Response, send_file
import os
from google import genai
import json
import tempfile
import gtts

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCAbZBgv8pzC7o-m0SoPlQerQvlQwZPH68"
client = genai.Client(api_key=GEMINI_API_KEY)

@app.route('/')
def home():
    return "Agri Bot API with Gemini AI ✅"

SYSTEM_INSTRUCTION = """ 
You are a Bangladeshi কৃষি সহকারী (agriculture assistant) designed to help farmers who may be অশিক্ষিত (illiterate) or not tech-savvy. You reply only in সহজ ও সুন্দর বাংলা (simple and clear Bangla). All your replies must sound natural, friendly, and easy to speak aloud.

🔹 Your goal:
Give clear, practical advice that a farmer can follow **without needing to go to any কৃষি অফিস**.

🔸 Strict rules:
- Never say “কৃষি অফিসে যান” unless it's the **last and only option** (e.g. soil testing lab).
- You are the *main problem solver*, like a smart, trusted village কৃষি উপদেষ্টা (agriculture advisor).
- Use real product names or methods if helpful (e.g. ইউরিয়া, ভার্টিমেক, ট্রাইসাইক্লাজোল).
- Always make sure the solution is possible at home or with products from a local দোকান (shop).
- If there's more than one possible cause, explain them shortly and help the farmer decide what to do first.
- Don't ask farmars for photos.

🔹 TTS Friendly Guidelines:
- Use short sentences.
- Keep tone friendly, not robotic.
- Avoid hard words and English completely.
- Examples help — use small, real-world examples where needed.

Remember: your job is to help — not redirect and also optimize the text for voice output.
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

@app.route('/tts', methods=['POST'])
def tts():
    data = request.get_json()
    text = data.get('text')

    if not text:
        return Response(
            json.dumps({'error': 'Missing Bangla text'}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

    try:
        tts = gtts.gTTS(text, lang='bn')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tts.save(temp_file.name)
        temp_file.close()

        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name="bangla_voice.wav",
            mimetype='audio/wav'
        )
    except Exception as e:
        return Response(
            json.dumps({'error': str(e)}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
