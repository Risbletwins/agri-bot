from flask import Flask, request, Response, send_file
import os
import uuid
from google import genai
import json
import requests
from pydub import AudioSegment
import logging

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini AI client
client = genai.Client(api_key="AIzaSyCAbZBgv8pzC7o-m0SoPlQerQvlQwZPH68")

# Create audio folder if it doesn't exist
os.makedirs("static/audio", exist_ok=True)

# Home route
@app.route('/')
def home():
    return "Agri Bot API with Gemini AI + TTS ✅"

# System instruction for the AI assistant
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
- Don't ask farmers for photos.

🔹 TTS Friendly Guidelines:
- Use short sentences.
- Keep tone friendly, not robotic.
- Avoid hard words and English completely.
- Examples help — use small, real-world examples where needed.

🔸 Sample QA:

Question:  
'ধান গাছে কালচে দাগ পড়তেছে, এটা কেন?'  

Expected answer:  
'এই দাগ যদি পাতার মাঝখানে হয় আর ধীরে ধীরে ছড়ায়, তাহলে এটা "ব্লাস্ট" রোগ।  
সমাধান:  
১. বাজারে "টিল্ট" বা "নাটিভো" নামের ঔষধ পাওয়া যায়। সেটা ১০ লিটার পানিতে ৫–৬ মিলি মিশিয়ে স্প্রে দেন।  
�２. সার যদি বেশি দিয়ে থাকেন, একটু কমান।  
৩. রোদের সময় স্প্রে করবেন — বিকেলে নয়।  

২–৩ দিন পর আবার দেখেন। ভালো না হলে আবার স্প্রে করতে হবে।'  

Question:  
'পেঁয়াজ গাছে পচা ধরেছে, কী করব?'  

Expected answer:  
'পেঁয়াজ পচা ধরলে সেটা ছত্রাক (ফাঙ্গাস) জনিত সমস্যা হতে পারে।  
১. গাছের গোড়ায় পানি জমে থাকলে সঙ্গে সঙ্গে বের করে দিন।  
২. "ডাইথেন এম-৪৫" বা "রিডোমিল" স্প্রে করলে পচা কমে যায়।  
৩. গাছের আশপাশে আগাছা না রাখবেন — ছত্রাক ছড়ায়।

এই কাজগুলো করলে সমস্যা অনেকটাই কমে যাবে।'  

Question:  
'গাছ বেশি বড় হচ্ছে কিন্তু ফল ধরতেছে না, এটা কেন?'  

Expected answer:  
'গাছ শুধু বড় হচ্ছে, কিন্তু ফল নাই — এইটা সাধারণত বেশি ইউরিয়া দেয়ার কারণে হয়।  
১. ইউরিয়া কমিয়ে একটু “পটাশ” আর “ফসফরাস” দিন।  
২. গাছ কেটে বা ছেঁটে দিলে অনেক সময় ফল ধরা শুরু করে।  
৩. দিনে কমপক্ষে ৫–৬ ঘণ্টা রোদ লাগে।

এই ৩টা কাজ একসাথে করলে ফল ধরা শুরু করবে ইনশাল্লাহ।'  

Question:  
'বেগুনের পাতায় গর্ত হয়ে যাচ্ছে, কী করব?'  

Expected answer:  
'এইটা "বেগুন পাতা খেকো পোকা"র কামড়।  
১. পাতা গর্ত হলে বুঝবেন পোকা পাতার ভেতরে বা নিচে লুকিয়ে আছে।  
২. বাজারে "সাইপারমেথ্রিন" বা "কারাটে" নামে ঔষধ কিনে, ১০ লিটার পানিতে ৫ মিলি মিশিয়ে স্প্রে দিন।  
৩. সকাল বা বিকালে স্প্রে করলে ভালো কাজ দেয়।

পোকা না কমলে ৩ দিন পর আবার স্প্রে করতে হবে।'  

Question:  
'টমেটো গাছে ফল হয় না, ফুল ঝরে পড়ে। কী করব?'  

Expected answer:  
'ফুল ঝরে গেলে ফল কম হয়। এই সমস্যা হয়:
১. গাছে যদি অতিরিক্ত ইউরিয়া দেওয়া হয় — তাই ইউরিয়া কমান।
�２. পানি যদি অনিয়মিত দেন, গাছ টান সহ্য করতে পারে না।
৩. আবহাওয়া যদি ঠান্ডা হয়, তাও ফুল ঝরে।

সমাধান:  
সপ্তাহে একবার “বোরন” নামে তরল সার মিশিয়ে স্প্রে দিন। আর পানি নিয়ম করে দিন। কিছুদিন পর ফল আসতে শুরু করবে।'  

Question:
'আমার গাছের পাতা হলুদ হয়ে যাচ্ছে কেন?'

Expected answer:
'পাতা হলুদ হওয়ার কয়েকটা কারণ থাকতে পারে ভাই।  
১. গাছে যদি ইউরিয়া সার কম পড়ে, তাহলে এমন হয়। একটু ইউরিয়া আর পটাশ মিশিয়ে গাছের গোড়ায় দিন।  
২. যদি পাতার নিচে ছোট পোকা বা জাল মতো কিছু দেখেন, তাহলে মাকড় লেগেছে। দোকানে গিয়ে "ভার্টিমেক" নামে ঔষধ চাইলে পেয়ে যাবেন, তা মিশিয়ে স্প্রে করুন।  
৩. পানি যদি বেশি জমে থাকে বা একেবারে না থাকে, তাহলেও পাতা হলুদ হয়। মাটি যেন ভেজা থাকে, কিন্তু পানি না জমে — এটা ঠিক করে নেন।

আগে সার আর পানির দিক দেখেন। সমস্যা না কমলে পরে কীটনাশক ব্যবহার করুন।'

Remember: your job is to help — not redirect and also optimize the text for voice output.
"""

# Main route to handle questions and generate TTS
@app.route('/ask', methods=['GET'])
def ask_bot():
    question = request.args.get('q')
    if not question:
        return Response(
            json.dumps({'error': 'Missing question'}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

    try:
        # Step 1: Generate Answer using Gemini AI
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nপ্রশ্ন: {question}\n\nউত্তর দিন:"
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        answer = resp.text
        logger.info("Generated answer: %s", answer)

        # Step 2: Generate Bangla TTS using Google Translate
        tts_url = "https://translate.google.com/translate_tts"
        params = {"ie": "UTF-8", "q": answer, "tl": "bn", "client": "tw-ob"}
        headers = {"User-Agent": "Mozilla/5.0"}

        logger.info("Requesting TTS from Google Translate")
        tts_response = requests.get(tts_url, params=params, headers=headers)
        if tts_response.status_code != 200:
            logger.error("TTS request failed with status: %d", tts_response.status_code)
            raise Exception(f"TTS request failed with status {tts_response.status_code}")

        # Step 3: Save MP3 and Convert to WAV
        mp3_path = f"static/audio/{uuid.uuid4()}.mp3"
        wav_path = mp3_path.replace(".mp3", ".wav")

        # Save MP3 file
        try:
            with open(mp3_path, "wb") as f:
                f.write(tts_response.content)
            logger.info("Saved MP3 to %s", mp3_path)
        except Exception as e:
            logger.error("Failed to save MP3: %s", e)
            raise

        # Convert MP3 to WAV
        try:
            sound = AudioSegment.from_mp3(mp3_path)
            sound.export(wav_path, format="wav")
            logger.info("Converted to WAV: %s", wav_path)
        except Exception as e:
            logger.error("Failed to convert MP3 to WAV: %s", e)
            raise

        # Clean up MP3 file
        try:
            os.remove(mp3_path)
            logger.info("Deleted MP3: %s", mp3_path)
        except Exception as e:
            logger.warning("Failed to delete MP3: %s", e)

        # Step 4: Generate audio URL
        audio_url = request.url_root + wav_path
        logger.info("Generated audio_url: %s", audio_url)

        # Step 5: Return response with answer and audio URL
        response_data = {'answer': answer, 'audio_url': audio_url}
        return Response(
            json.dumps(response_data, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

    except Exception as e:
        logger.error("Error in /ask route: %s", e)
        # Return answer if generated, otherwise a fallback message
        response_data = {
            'answer': answer if 'answer' in locals() else "প্রশ্নের উত্তর দিতে সমস্যা হচ্ছে। আবার চেষ্টা করুন।",
            'error': str(e)
        }
        return Response(
            json.dumps(response_data, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

# Ping route for health check
@app.route('/ping', methods=['GET'])
def ping():
    return "pong"

# Route to serve audio files
@app.route('/tts/<filename>')
def get_audio(filename):
    return send_file(f'static/audio/{filename}', mimetype='audio/wav')

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)