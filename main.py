primary_answer = "none_for_now"
secondary_answer = "none_for_now"

from flask import Flask, request, Response, send_file, render_template, jsonify
import os
import uuid
import json
import time
import glob
import logging
from gtts import gTTS
from google import genai  
from dotenv import load_dotenv
from googletrans import Translator
from fuzzywuzzy import fuzz  # We'll use this for optional fuzzy matching
from flask_caching import Cache
import threading
import bleach

load_dotenv()

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini AI client (new SDK usage)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # ensure GEMINI_API_KEY set in env

# Caching setup
app.config['CACHE_TYPE'] = 'simple'  # Use simple in-memory cache
cache = Cache(app)

# Create audio folder if not exist
os.makedirs("static/audio", exist_ok=True)

# Translator for dynamic translations
translator = Translator()

# Predefined response translations (extended with soil moisture)
RESPONSE_TRANSLATIONS = {
    "লাইটটি চালু হয়েছে": "The light has been turned on",
    "লাইটটি বন্ধ হয়েছে": "The light has been turned off",
    "বীজ বপন ব্যবস্থা চালু হয়েছে": "The seed sowing system has been turned on",
    "বীজ বপন ব্যবস্থা বন্ধ হয়েছে": "The seed sowing system has been turned off",
    "কীটনাশক ব্যবস্থা চালু হয়েছে": "The fertilizer system has been turned on",
    "কীটনাশক ব্যবস্থা বন্ধ হয়েছে": "The fertilizer system has been turned off",
    "ওয়াটার পাম্প চালু হয়েছে": "The water pump has been turned on",
    "ওয়াটার পাম্প বন্ধ হয়েছে": "The water pump has been turned off",
    "পরিমাপ করা হচ্ছে... LCD প্যানেল দেখুন": "Measuring... Look at the LCD panel",  # Added for consistency
    "বন্ধ করা হচ্ছে...":'Stopping....'
}

SYSTEM_INSTRUCTION_BN =  """

আপনি একজন কৃষি সহকারী।  
আপনি সবসময় শুধু বাংলাতেই উত্তর দেবেন, যেকোনো ভাষায় প্রশ্ন এলেও।  
অন্য ভাষা বুঝতে পারবেন, কিন্তু আউটপুট সর্বদা বাংলায় হবে।  

সিস্টেম রুলস (ডিভাইস কন্ট্রোল):  
- যদি ইউজার বলে "TURN ON THE LIGHT" বা এরকম কিছু, উত্তর দিন: "লাইটটি চালু হয়েছে"।  
- যদি ইউজার বলে "TURN OFF THE LIGHT" বা এরকম কিছু, উত্তর দিন: "লাইটটি বন্ধ হয়েছে"।  

- যদি ইউজার বলে "TURN ON THE SEED SOW" বা এরকম কিছু, উত্তর দিন: "বীজ বপন ব্যবস্থা চালু হয়েছে"।  
- যদি ইউজার বলে "TURN OFF THE SEED SOW" বা এরকম কিছু, উত্তর দিন: "বীজ বপন ব্যবস্থা বন্ধ হয়েছে"।  

- যদি ইউজার বলে "TURN ON THE FERTILIZER SYSTEM" বা এরকম কিছু, উত্তর দিন: "কীটনাশক ব্যবস্থা চালু হয়েছে"।  
- যদি ইউজার বলে "TURN OFF THE FERTILIZER SYSTEM" বা এরকম কিছু, উত্তর দিন: "কীটনাশক ব্যবস্থা বন্ধ হয়েছে"।  

- যদি ইউজার বলে "TURN ON THE WATER PUMP" বা এরকম কিছু, উত্তর দিন: "ওয়াটার পাম্প চালু হয়েছে"।  
- যদি ইউজার বলে "TURN OFF THE WATER PUMP" বা এরকম কিছু, উত্তর দিন: "ওয়াটার পাম্প বন্ধ হয়েছে"।  
- যদি ইউজার বলে "START MEASURING THE SOIL MOISTURE" বা এরকম কিছু, উত্তর দিন: "পরিমাপ করা হচ্ছে... LCD প্যানেল দেখুন"।
- যদি ইউজার বলে "STOP MEASURING THE SOIL MOISTURE" বা এরকম কিছু, উত্তর দিন: "বন্ধ করা হচ্ছে..."।


সাধারণ নির্দেশিকা:  
- সবসময় বাংলায় উত্তর দিন।  
- উত্তর সংক্ষিপ্ত, সহজ আর বন্ধুত্বপূর্ণ হোক।  
- জটিল শব্দ এড়িয়ে চলুন।  
- ঘরে বসে বা স্থানীয় দোকান থেকে সমাধান করা যায় এমন পদ্ধতি বলুন।  
- কৃষি অফিসে যেতে বলবেন না, একেবারেই শেষ উপায় ছাড়া (যেমন মাটির টেস্ট)।  
- লিস্ট, বুলেট, চিহ্ন (* - _ ইত্যাদি) ব্যবহার করবেন না। স্বাভাবিকভাবে লিখবেন।  
- দরকার হলে লিঙ্ক দিতে পারেন (যেমন: https://dae.gov.bd/)।  

TTS ফ্রেন্ডলি রুলস:  
- ছোট বাক্য ব্যবহার করুন।  
- কথা যেন স্বাভাবিক ও সহজ হয়।  

উদাহরণ প্রশ্নোত্তর:  
Q: ধানের পাতায় কালো দাগ কেন?
A: এটা ব্লাস্ট রোগ। বাজার থেকে টিল্ট বা নাটিভো ঔষধ কিনে ১০ লিটার পানিতে ৫–৬ মিলি মিশিয়ে রোদে স্প্রে দিন।

Q: পেঁয়াজ পচে যাচ্ছে, কী করব?
A: পানি জমে গেলে পেঁয়াজ পচে। পানি বের করে দিন। তারপর ডাইথেন এম-৪৫ বা রিডোমিল ঔষধ ১০ লিটার পানিতে মিশিয়ে স্প্রে দিন।

Q: গাছ বড় হচ্ছে কিন্তু ফল আসছে না কেন?
A: বেশি ইউরিয়া দিলে শুধু গাছ বাড়ে, ফল আসে না। ইউরিয়া কমান। পটাশ আর ফসফরাস দিন। ডালপালা ছাঁটাই করুন, আর রোদে রাখুন।

Q: বেগুনের পাতায় গর্ত হচ্ছে কেন?
A: এটা পাতা খেকো পোকার কাজ। সাইপারমেথ্রিন বা কারাটে ঔষধ ১০ লিটার পানিতে ৫ মিলি মিশিয়ে সকালে বা বিকালে স্প্রে দিন। দরকার হলে ৩ দিন পর আবার দিন।

Q: টমেটোর ফুল ঝরে যাচ্ছে কেন?
A: বেশি ইউরিয়া দিলে বা পানি অনিয়ম হলে ফুল ঝরে। ইউরিয়া কমান, পানি নিয়মিত দিন। সপ্তাহে একবার বোরন স্প্রে করলে ভালো হবে।

Q: পাতাগুলো হলুদ হয়ে যাচ্ছে কেন?
A: সার কম থাকলে বা পানি বেশি/কম হলে এমন হয়। অল্প ইউরিয়া ও পটাশ দিন। যদি পাতার নিচে পোকা থাকে, তাহলে ভার্টিমেক স্প্রে করুন।

Q: আমি পেঁয়াজ কখন রোপণ করব?
A: অক্টোবর থেকে ডিসেম্বর মাসে পেঁয়াজ রোপণ করুন।

Q: আমি ধান কখন রোপণ করব?
A: জুন জুলাই মাসে আমন ধান রোপণ করুন। ডিসেম্বর জানুয়ারি মাসে বোরো ধান রোপণ করুন।

Q: আমি গম কখন বপন করব?
A: নভেম্বর মাসের মাঝামাঝি সময়ে গম বপন করুন।

Q: আমি ভুট্টা কখন রোপণ করব?
A: নভেম্বর ডিসেম্বর মাসে অথবা এপ্রিল মে মাসে ভুট্টা রোপণ করতে পারেন।

Q: আমি আলু কখন রোপণ করব?
A: নভেম্বর ডিসেম্বর মাসে আলু রোপণ করুন।

Q: আমি টমেটো কখন রোপণ করব?
A: নভেম্বর ডিসেম্বর মাসে টমেটো রোপণ করুন।

Q: আমি শসা কখন বপন করব?
A: জানুয়ারি ফেব্রুয়ারি মাসে শসা বপন করুন।

Q: আমি বেগুন কখন রোপণ করব?
A: বেগুন শীত অথবা গরম দুই সময়েই চাষ করা যায়।

Q: আমি শাক সবজি কখন বপন করব?
A: অক্টোবর নভেম্বর মাসে শাক সবজি বপন করুন।

""" 

SYSTEM_INSTRUCTION_EN = """

You are an agriculture assistant for Bangladeshi farmers.  
You must ALWAYS reply only in ENGLISH, no matter what language the user uses.  
You can understand Bangla or other languages, but your output must stay in English only.  

System Rules for Device Control:
- If the user says "TURN ON THE LIGHT" or similar, reply: "The light has been turned on".  
- If the user says "TURN OFF THE LIGHT" or similar, reply: "The light has been turned off".  

- If the user says "TURN ON THE SEED SOW" or similar, reply: "The seed sowing system has been turned on".  
- If the user says "TURN OFF THE SEED SOW" or similar, reply: "The seed sowing system has been turned off".  

- If the user says "TURN ON THE FERTILIZER SYSTEM" or similar, reply: "The fertilizer system has been turned on".  
- If the user says "TURN OFF THE FERTILIZER SYSTEM" or similar, reply: "The fertilizer system has been turned off".  

- If the user says "TURN ON THE WATER PUMP" or similar, reply: "The water pump has been turned on".  
- If the user says "TURN OFF THE WATER PUMP" or similar, reply: "The water pump has been turned off".  

- If the user says "START MEASURING THE SOIL MOISTURE" or similar, reply: "Measuring... Look at the LCD panel". 
- IF the user says "STOP MEASURING THE SOIL MOISTURE" or similar, reply: "Stopping....".
  

General Guidelines:
- Always answer in English.  
- Keep tone short, friendly, and practical.  
- Avoid technical jargon.  
- Suggest home-based or shop-based solutions whenever possible.  
- Do not redirect to agriculture offices unless it is the very last option (like soil testing).  
- Do not use lists, bullet points, or symbols (* - _ etc). Write naturally.  
- Include useful support links if available (example: https://dae.gov.bd/).  

TTS-Friendly Rules:
- Use short, clear sentences.  
- Keep it natural and easy to read aloud.  

Example Q&A:
Q: Why are there black spots on rice leaves?
A: It's blast disease. Buy Tilt or Nativo, mix 5-6 ml in 10 liters of water, and spray in the sun.

Q: My onions are rotting, what should I do?
A: Onions rot if water stays. Remove water. Then spray Dithane M-45 or Ridomil mixed in 10 liters of water.

Q: The plant is growing big but no fruits, why?
A: Too much urea makes only leaves. Reduce urea, add potash and phosphorus. Prune branches and keep in sunlight.

Q: Holes are appearing in eggplant leaves, what to do?
A: This is leaf-eating insects. Spray Cypermethrin or Karate (5 ml in 10 liters water) in morning or evening. Repeat after 3 days if needed.

Q: Tomato flowers are falling, what to do?
A: Too much urea or irregular watering causes flower drop. Reduce urea, water regularly. Spray boron once a week.

Q: Leaves are turning yellow, why?
A: Lack of fertilizer or too much/less water. Add little urea & potash. If insects are under leaves, spray Vertimec.

Q: When should I plant onion?
A: Plant onion in October to December.

Q: When should I plant rice?
A: Plant aman rice in June and July. Plant boro rice in December and January.

Q: When should I sow wheat?
A: Sow wheat in mid November.

Q: When should I plant maize?
A: Plant maize in November or December. You can also plant in April or May.

Q: When should I plant potatoes?
A: Plant potatoes in November or December.

Q: When should I plant tomato?
A: Plant tomato in November or December.

Q: When should I plant cucumber?
A: Sow cucumber in January or February.

Q: When should I plant brinjal?
A: You can plant brinjal in winter or in summer.

Q: When should I plant leafy vegetables?
A: Plant leafy vegetables in October or November.

"""

def get_system_instruction(lang):
    return SYSTEM_INSTRUCTION_BN if lang == 'bn' else SYSTEM_INSTRUCTION_EN

def split_text(text, max_length=200):
    sentences = text.split('।' if '.' not in text else '.')
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence + ("। " if '.' not in text else ". ")
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ("। " if '.' not in text else ". ")
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def generate_audio_sync(text_chunks, lang):
    audio_urls = []
    for chunk in text_chunks:
        try:
            # Save file in OS-safe way
            chunk_mp3 = os.path.join("static", "audio", f"{uuid.uuid4()}.mp3")
            tts = gTTS(text=chunk, lang=lang, slow=False)
            tts.save(chunk_mp3)
            # Build public URL using host_url (works better behind proxies)
            base = request.host_url.rstrip('/') 
            public_path = f"{base}/{chunk_mp3.replace(os.sep, '/')}"
            audio_urls.append(public_path)
            logger.info("TTS saved: %s -> %s", chunk_mp3, public_path)
        except Exception as e:
            logger.error("TTS error saving chunk: %s", e, exc_info=True)
    return audio_urls

def get_english_translation(bn_text):
    if bn_text in RESPONSE_TRANSLATIONS:
        return RESPONSE_TRANSLATIONS[bn_text]
    try:
        return translator.translate(bn_text, src='bn', dest='en').text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return bn_text + " (Translation unavailable)"

def get_bangla_translation(en_text):
    # Reverse lookup for exact matches; otherwise translate
    for bn, en in RESPONSE_TRANSLATIONS.items():
        if en == en_text:
            return bn
    try:
        return translator.translate(en_text, src='en', dest='bn').text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return en_text + " (অনুবাদ অনুপলব্ধ)"

@app.route('/')
def serve_webpage():
    return render_template('homepage.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/moveauto')
def moveauto():
    return render_template('movement_auto.html')

@app.route('/movemanual')
def movemanual():
    return render_template('movemen_manual.html')

@cache.cached(timeout=300, query_string=True)
@app.route('/ask', methods=['GET'])
def ask_bot():
    global primary_answer
    global secondary_answer
    primary_answer = "none_for_now"
    question = bleach.clean(request.args.get('q', ''))
    lang = request.args.get('lang', 'bn')
    if not question:
        return jsonify({'error': 'Missing question'}), 400

    try:
        full_prompt = f"{get_system_instruction(lang)}\n\nপ্রশ্ন: {question}\n\nউত্তর দিন:" if lang == 'bn' else f"{get_system_instruction(lang)}\n\nQuestion: {question}\n\nAnswer:"

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        primary_answer = response.text.strip()

        # Get secondary translation
        secondary_answer = get_english_translation(primary_answer) if lang == 'bn' else get_bangla_translation(primary_answer)

        # Generate audio synchronously (reliable)
        primary_chunks = split_text(primary_answer)
        secondary_chunks = split_text(secondary_answer)

        audio_urls_primary = generate_audio_sync(primary_chunks, lang)
        audio_urls_secondary = generate_audio_sync(secondary_chunks, 'en' if lang == 'bn' else 'bn')

        logger.info("Audio URLs primary: %s", audio_urls_primary)
        logger.info("Audio URLs secondary: %s", audio_urls_secondary)

        cleanup_audio_files()

        return jsonify({
            'answer_bn': primary_answer if lang == 'bn' else secondary_answer,
            'answer_en': secondary_answer if lang == 'bn' else primary_answer,
            'audio_urls_bn': audio_urls_primary if lang == 'bn' else audio_urls_secondary,
            'audio_urls_en': audio_urls_secondary if lang == 'bn' else audio_urls_primary
        })

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def cleanup_audio_files():
    max_age = 3600
    for file in glob.glob("static/audio/*.mp3"):
        if os.path.getmtime(file) < time.time() - max_age:
            try:
                os.remove(file)
            except Exception as e:
                logger.error("Error removing old audio file %s: %s", file, e)

@app.route('/static/audio/<filename>')
def get_audio(filename):
    return send_file(f'static/audio/{filename}', mimetype='audio/mpeg')

@app.route("/esp32-receive", methods=["GET"])
def esp32_receive():
    # Define command triggers with all variants (Bangla + English, including old ones for safety)
    # Key: command, Value: list of phrases (case-sensitive, but we'll lower() in checks)
    print(request.content_type)
    command_triggers = {
        "light_on": ["লাইটটি চালু হয়েছে", "The light has been turned on", "Light has been turned ON"],
        "light_off": ["লাইটটি বন্ধ হয়েছে", "The light has been turned off", "Light has been turned OFF"],
        "seed_sow_on": ["বীজ বপন ব্যবস্থা চালু হয়েছে", "The seed sowing system has been turned on", "Seed sowing system has been turned ON"],
        "seed_sow_off": ["বীজ বপন ব্যবস্থা বন্ধ হয়েছে", "The seed sowing system has been turned off", "Seed sowing system has been turned OFF"],
        "fertilizer_on": ["কীটনাশক ব্যবস্থা চালু হয়েছে", "The fertilizer system has been turned on", "Fertilizer system has been turned ON"],
        "fertilizer_off": ["কীটনাশক ব্যবস্থা বন্ধ হয়েছে", "The fertilizer system has been turned off", "Fertilizer system has been turned OFF"],
        "water_pump_on": ["ওয়াটার পাম্প চালু হয়েছে", "The water pump has been turned on", "Water pump has been turned ON"],
        "water_pump_off": ["ওয়াটার পাম্প বন্ধ হয়েছে", "The water pump has been turned off", "Water pump has been turned OFF"],
        "start_measuring_soil_moisture": ["পরিমাপ করা হচ্ছে... LCD প্যানেল দেখুন", "Measuring... Look at the LCD panel", "MEASURING.... LOOK AT THE LCD PANEL"],
        "stop_measuring_soil_moisture": ["বন্ধ করা হচ্ছে...","Stopping....","STOPPING...."]
    }

    # Check both primary and secondary answers for any matching phrase (case-insensitive)
    answers = [primary_answer.lower(), secondary_answer.lower()]
    for cmd, phrases in command_triggers.items():
        for phrase in [p.lower() for p in phrases]:
            for ans in answers:
                if phrase in ans:
                    # Optional: Add fuzzy check if you want more robustness (e.g., if AI paraphrases)
                    # if fuzz.partial_ratio(phrase, ans) > 90:
                    return cmd

    return "none_for_now"
@app.route("/esp32-receive-movement", methods=["POST"])
def esp32_receive_movement():
    data = request.get_json()
    content_type = request.content_type
    print(content_type)
    print(data)
    
    height = data.get('height')
    width = data.get('width')
    num_rows = data.get('num_rows')
    orientation = data.get('orientation')
    distance = data.get('distance')

    print(f"Received data: Height = {height} ft, Width = {width} ft, Rows = {num_rows}, Orientation = {orientation}, Distance = {distance} ft")

    total_area = height * width
    print(f"Calculated total land area: {total_area} sq ft")

    movement_plan = {
        "rows": num_rows,
        "distance_between_rows": distance,
        "orientation": orientation,
        "field_dimensions": {"height": height, "width": width}
    }

    return jsonify({
        "message": "Data received successfully!",
        "received_data": data,
        "calculated_area": total_area,
        "movement_plan": movement_plan
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)