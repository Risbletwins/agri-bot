from flask import Flask, request, Response, send_file, render_template, jsonify
import os
import uuid
import json
import time
import glob
import logging
from gtts import gTTS
from google import genai

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini AI client
client = genai.Client(api_key="AIzaSyCAbZBgv8pzC7o-m0SoPlQerQvlQwZPH68")

# Create audio folder if not exist
os.makedirs("static/audio", exist_ok=True)

# Store latest ESP32 command
target_command = {"action": "stop"}

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
- Never use any numbering or asterisk sign in the response
- Never use any symbols and 

🔹 TTS Friendly Guidelines:
- Use short sentences and also short answers.
- Keep tone friendly, not robotic.
- Avoid hard words and English completely.
- Examples help — use small, real-world examples where needed.

🔸 Sample QA:

Question:  
'ধান গাছে কালচে দাগ পড়তেছে, এটা কেন?'  

Expected answer:  
'এই দাগ যদি পাতার মাঝখানে হয় আর ধীরে ধীরে ছড়ায়, তাহলে এটা "ব্লাস্ট" রোগ। বাজারে "টিল্ট" বা "নাটিভো" নামের ঔষধ পাওয়া যায়। সেটা ১০ লিটার পানিতে ৫–৬ মিলি মিশিয়ে স্প্রে দেন।  সার যদি বেশি দিয়ে থাকেন, একটু কমান।  রোদের সময় স্প্রে করবেন — বিকেলে নয়।  ২–৩ দিন পর আবার দেখেন। ভালো না হলে আবার স্প্রে করতে হবে।'  

Question:  
'পেঁয়াজ গাছে পচা ধরেছে, কী করব?'  

Expected answer:  
'পেঁয়াজ পচা ধরলে সেটা ছত্রাক (ফাঙ্গাস) জনিত সমস্যা হতে পারে। গাছের গোড়ায় পানি জমে থাকলে সঙ্গে সঙ্গে বের করে দিন। "ডাইথেন এম-৪৫" বা "রিডোমিল" স্প্রে করলে পচা কমে যায়। গাছের আশপাশে আগাছা না রাখবেন — ছত্রাক ছড়ায়। এই কাজগুলো করলে সমস্যা অনেকটাই কমে যাবে।'  

Question:  
'গাছ বেশি বড় হচ্ছে কিন্তু ফল ধরতেছে না, এটা কেন?'  

Expected answer:  
'গাছ শুধু বড় হচ্ছে, কিন্তু ফল নাই এইটা সাধারণত বেশি ইউরিয়া দেয়ার কারণে হয়। ইউরিয়া কমিয়ে একটু “পটাশ” আর “ফসফরাস” দিন। গাছ কেটে বা ছেঁটে দিলে অনেক সময় ফল ধরা শুরু করে।  দিনে কমপক্ষে ৫–৬ ঘণ্টা রোদ লাগে। এই ৩টা কাজ একসাথে করলে ফল ধরা শুরু করবে ইনশাল্লাহ।'  

Question:  
'বেগুনের পাতায় গর্ত হয়ে যাচ্ছে, কী করব?'  

Expected answer:  
'এইটা "বেগুন পাতা খেকো পোকা"র কামড়। পাতা গর্ত হলে বুঝবেন পোকা পাতার ভেতরে বা নিচে লুকিয়ে আছে। বাজারে "সাইপারমেথ্রিন" বা "কারাটে" নামে ঔষধ কিনে, ১০ লিটার পানিতে ৫ মিলি মিশিয়ে স্প্রে দিন। সকাল বা বিকালে স্প্রে করলে ভালো কাজ দেয়। পোকা না কমলে ৩ দিন পর আবার স্প্রে করতে হবে।'  

Question:  
'টমেটো গাছে ফল হয় না, ফুল ঝরে পড়ে। কী করব?'  

Expected answer:  
ফুল ঝরে গেলে ফল কম হয়। এই সমস্যা হয়, গাছে যদি অতিরিক্ত ইউরিয়া দেওয়া হয়, তাই ইউরিয়া কমান। পানি যদি অনিয়মিত দেন, গাছ টান সহ্য করতে পারে না। আবহাওয়া যদি ঠান্ডা হয়, তাও ফুল ঝরে। সপ্তাহে একবার “বোরন” নামে তরল সার মিশিয়ে স্প্রে দিন। আর পানি নিয়ম করে দিন। কিছুদিন পর ফল আসতে শুরু করবে।'  

Question:
'আমার গাছের পাতা হলুদ হয়ে যাচ্ছে কেন?'

Expected answer:
পাতা হলুদ হওয়ার কয়েকটা কারণ থাকতে পারে ভাই। গাছে যদি ইউরিয়া সার কম পড়ে, তাহলে এমন হয়। একটু ইউরিয়া আর পটাশ মিশিয়ে গাছের গোড়ায় দিন। যদি পাতার নিচে ছোট পোকা বা জাল মতো কিছু দেখেন, তাহলে মাকড় লেগেছে। দোকানে গিয়ে "ভার্টিমেক" নামে ঔষধ চাইলে পেয়ে যাবেন, তা মিশিয়ে স্প্রে করুন।  পানি যদি বেশি জমে থাকে বা একেবারে না থাকে, তাহলেও পাতা হলুদ হয়। মাটি যেন ভেজা থাকে, কিন্তু পানি না জমে — এটা ঠিক করে নেন। আগে সার আর পানির দিক দেখেন। সমস্যা না কমলে পরে কীটনাশক ব্যবহার করুন।'


Remember: your job is to help — not redirect and also optimize the text for voice output.


"""   # Omitted for brevity, unchanged

def split_text(text, max_length=200):
    sentences = text.split('।')
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
    return render_template('homepage.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/ask', methods=['GET'])
def ask_bot():
    question = request.args.get('q')
    if not question:
        return Response(json.dumps({'error': 'Missing question'}, ensure_ascii=False), content_type='application/json; charset=utf-8')

    try:
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nপ্রশ্ন: {question}\n\nউত্তর দিন:"
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=full_prompt)
        answer = resp.text
        mp3_path = f"static/audio/{uuid.uuid4()}.mp3"
        audio_urls = []
        answer_chunks = split_text(answer) if len(answer) > 200 else [answer]

        if len(answer_chunks) == 1:
            tts = gTTS(text=answer, lang='bn', slow=False)
            tts.save(mp3_path)
            audio_urls.append(request.url_root + mp3_path)
        else:
            for chunk in answer_chunks:
                chunk_mp3 = f"static/audio/{uuid.uuid4()}.mp3"
                tts = gTTS(text=chunk, lang='bn', slow=False)
                tts.save(chunk_mp3)
                audio_urls.append(request.url_root + chunk_mp3)

        cleanup_audio_files()

        return Response(json.dumps({
            'answer': answer,
            'audio_urls': audio_urls
        }, ensure_ascii=False), content_type='application/json; charset=utf-8')

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return Response(json.dumps({'error': str(e)}, ensure_ascii=False), content_type='application/json; charset=utf-8')

def cleanup_audio_files():
    max_age = 3600
    for file in glob.glob("static/audio/*.mp3"):
        if os.path.getmtime(file) < time.time() - max_age:
            os.remove(file)

@app.route('/static/audio/<filename>')
def get_audio(filename):
    return send_file(f'static/audio/{filename}', mimetype='audio/mpeg')

@app.route("/seed_sowing_system", methods=["GET","POST"])
def get_seed_sowing_system_page():
    return render_template("seed_sowing_system.html")

@app.route("/water_pump_system", methods=["GET","POST"])
def get_water_pump_system_page():
    return render_template("water_pump_system.html")

@app.route("/humidity_measuring_system", methods=["GET","POST"])
def get_humidity_measuring_system_page():
    return render_template("humidity_measuring_system.html")

@app.route("/soil_moisture_measuring_system", methods=["GET","POST"])
def get_soil_moisture_measuring_system_page():
    return render_template("soil_moisture_measuring_system.html")

@app.route("/controller", methods=["GET","POST"])
def get_controller_page():
    return render_template("controller.html")

# Update command state from button presses
@app.route('/controller/moveup', methods=["GET",'POST'])
def handle_button_up():
    return "ControllerMoveUp"

@app.route('/controller/movedown', methods=["GET",'POST'])
def handle_button_down():
    return "ControllerMoveDown"

@app.route('/controller/moveright', methods=['GET','POST'])
def handle_button_right():
    return "ControllerMoveRight"

@app.route('/controller/moveleft', methods=['GET','POST'])
def handle_button_left():
    return "ControllerMoveLeft"


@app.route('/seed_sowing_system/button', methods=['GET','POST'])
def seed_sowing_button():
    data = request.get_json()
    return "SeedSowingSystem"+data

@app.route('/soil_moisture_measuring_system/button', methods=["GET",'POST'])
def soil_moisture_button():
    data = request.get_json()
    return "SoilMoistureMeasuringSystem"+data

@app.route('/water_pump_system/button', methods=["GET",'POST'])
def water_pump_system_button():
    data = request.get_json()
    return "WaterPumpSystem"+data

@app.route('/humidity_measuring_system/button', methods=["GET",'POST'])
def humidity_measuring_system_button():
    data = request.get_json()
    return "HumidityMeasuringSystem"+data

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
