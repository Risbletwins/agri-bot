from flask import Flask, request, Response, send_file, render_template
import os
import uuid
import json
import time
import glob
import logging
from gtts import gTTS
from google import genai  # Adjust import based on actual library

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini AI client
client = genai.Client(api_key="AIzaSyCAbZBgv8pzC7o-m0SoPlQerQvlQwZPH68")

# Create audio folder if not exist
os.makedirs("static/audio", exist_ok=True)

# System instruction for Gemini AI (unchanged)
SYSTEM_INSTRUCTION =  """ 
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

🔸 Sample QA:

Question:  
'ধান গাছে কালচে দাগ পড়তেছে, এটা কেন?'  

Expected answer:  
'এই দাগ যদি পাতার মাঝখানে হয় আর ধীরে ধীরে ছড়ায়, তাহলে এটা "ব্লাস্ট" রোগ।  
সমাধান:  
১. বাজারে "টিল্ট" বা "নাটিভো" নামের ঔষধ পাওয়া যায়। সেটা ১০ লিটার পানিতে ৫–৬ মিলি মিশিয়ে স্প্রে দেন।  
২. সার যদি বেশি দিয়ে থাকেন, একটু কমান।  
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
২. পানি যদি অনিয়মিত দেন, গাছ টান সহ্য করতে পারে না।
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


def split_text(text, max_length=200):
    """Split text into chunks for gTTS compatibility."""
    sentences = text.split('।')  # Split on Bangla full stop
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence + "। "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + "। "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

@app.route('/')
def serve_webpage():
    return render_template('index.html')

@app.route('/ask', methods=['GET'])
def ask_bot():
    question = request.args.get('q')
    if not question:
        return Response(
            json.dumps({'error': 'Missing question'}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

    try:
        # Step 1: Generate Answer
        logger.info(f"Processing question: {question}")
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nপ্রশ্ন: {question}\n\nউত্তর দিন:"
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        answer = resp.text
        logger.info(f"Generated answer: {answer[:100]}... (length: {len(answer)})")

        # Step 2: Generate Bangla TTS using gTTS
        mp3_path = f"static/audio/{uuid.uuid4()}.mp3"
        audio_urls = []

        # Split answer if too long
        answer_chunks = split_text(answer) if len(answer) > 200 else [answer]
        logger.info(f"Answer split into {len(answer_chunks)} chunks")

        if len(answer_chunks) == 1:
            tts = gTTS(text=answer, lang='bn', slow=False)
            tts.save(mp3_path)
            audio_urls.append(request.url_root + mp3_path)
        else:
            # Generate multiple MP3s for chunks
            for i, chunk in enumerate(answer_chunks):
                chunk_mp3 = f"static/audio/{uuid.uuid4()}.mp3"
                tts = gTTS(text=chunk, lang='bn', slow=False)
                tts.save(chunk_mp3)
                audio_urls.append(request.url_root + chunk_mp3)

        # Cleanup old audio files
        cleanup_audio_files()

        # Return response with audio URLs
        response_data = {
            'answer': answer,
            'audio_urls': audio_urls  # Support multiple URLs for chunks
        }
        logger.info(f"Returning response with {len(audio_urls)} audio URLs")
        return Response(
            json.dumps(response_data, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return Response(
            json.dumps({'error': str(e)}, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )

def cleanup_audio_files():
    max_age = 3600  # 1 hour in seconds
    for file in glob.glob("static/audio/*.mp3"):
        if os.path.getmtime(file) < time.time() - max_age:
            os.remove(file)

@app.route('/ping', methods=['GET'])
def ping():
    return "pong"

@app.route('/static/audio/<filename>')
def get_audio(filename):
    return send_file(f'static/audio/{filename}', mimetype='audio/mpeg')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)