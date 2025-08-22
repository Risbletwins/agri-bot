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
from fuzzywuzzy import fuzz
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

# Predefined response translations (extended if needed)
RESPONSE_TRANSLATIONS = {
    "লাইটটি চালু হয়েছে": "The light has been turned on",
    "লাইটটি বন্ধ হয়েছে": "The light has been turned off",
    "বীজ বপন ব্যবস্থা চালু হয়েছে": "The seed sowing system has been turned on",
    "বীজ বপন ব্যবস্থা বন্ধ হয়েছে": "The seed sowing system has been turned off",
    "কীটনাশক ব্যবস্থা চালু হয়েছে": "The fertilizer system has been turned on",
    "কীটনাশক ব্যবস্থা বন্ধ হয়েছে": "The fertilizer system has been turned off",
    "ওয়াটার পাম্প চালু হয়েছে": "The water pump has been turned on",
    "ওয়াটার পাম্প বন্ধ হয়েছে": "The water pump has been turned off",

}

# Command mappings for ESP32 with fuzzy thresholds
COMMAND_MAPPINGS = {
    "turn on the light": "লাইটটি চালু হয়েছে",
    "turn off the light": "লাইটটি বন্ধ হয়েছে",
    "turn on the seed sow": "বীজ বপন ব্যবস্থা চালু হয়েছে",
    "turn off the seed sow": "বীজ বপন ব্যবস্থা বন্ধ হয়েছে",
    "turn on the fertilizer system": "কীটনাশক ব্যবস্থা চালু হয়েছে",
    "turn off the fertilizer system": "কীটনাশক ব্যবস্থা বন্ধ হয়েছে",
    "turn on water pump": "ওয়াটার পাম্প চালু হয়েছে",
    "turn off water pump": "ওয়াটার পাম্প বন্ধ হয়েছে",

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
প্রশ্ন: ধান গাছে কালচে দাগ পড়তেছে, এটা কেন?  
উত্তর: এই দাগ যদি পাতার মাঝখানে হয় আর ধীরে ছড়ায়, তাহলে এটা ব্লাস্ট রোগ। বাজারে টিল্ট বা নাটিভো নামের ঔষধ পাওয়া যায়। সেটা ১০ লিটার পানিতে ৫–৬ মিলি মিশিয়ে স্প্রে দিন। রোদের সময় স্প্রে করলে ভালো কাজ হয়।

প্রশ্ন: পেঁয়াজ গাছে পচা ধরেছে, কী করব?  
উত্তর: পেঁয়াজ পচা সাধারণত ছত্রাকের কারণে হয়। প্রথমে গোড়ায় জমে থাকা পানি বের করে দিন। বাজারে ডাইথেন এম-৪৫ বা রিডোমিল নামের ঔষধ পাওয়া যায়, এগুলো স্প্রে করলে পচা কমে যায়। মাঠে আগাছা থাকলে পরিষ্কার করুন।  

প্রশ্ন: গাছ বড় হচ্ছে কিন্তু ফল ধরছে না কেন?  
উত্তর: সাধারণত বেশি ইউরিয়া দিলে গাছ শুধু বড় হয়, কিন্তু ফল হয় না। ইউরিয়া কমিয়ে কিছুটা পটাশ আর ফসফরাস দিন। ডালপালা কেটে ছাঁটাই করলে অনেক সময় ফল আসে। প্রতিদিন অন্তত ৫–৬ ঘণ্টা রোদ লাগবে।  

প্রশ্ন: বেগুনের পাতায় গর্ত হয়ে যাচ্ছে, কী করব?  
উত্তর: এটা বেগুন পাতা খেকো পোকা। এরা সাধারণত পাতার নিচে লুকায়। বাজারে সাইপারমেথ্রিন বা কারাটে নামে ঔষধ কিনে, ১০ লিটার পানিতে ৫ মিলি মিশিয়ে সকালে বা বিকালে স্প্রে দিন। প্রয়োজনে ৩ দিন পর আবার দিন।  

প্রশ্ন: টমেটোর ফুল ঝরে যাচ্ছে, কী করব?  
উত্তর: ফুল ঝরে গেলে ফল কম হয়। বেশি ইউরিয়া দিলে বা পানি অনিয়ম করলে এই সমস্যা হয়। ইউরিয়া কমান আর পানি নিয়মিত দিন। আবহাওয়া ঠান্ডা হলেও ফুল ঝরে যায়। সপ্তাহে একবার বোরন মিশিয়ে স্প্রে করলে অনেকটা কমে যায়।  

প্রশ্ন: পাতাগুলো হলুদ হয়ে যাচ্ছে কেন?  
উত্তর: পাতার হলুদ হওয়ার কয়েকটা কারণ আছে। সার কম পেলে এমন হয়, তাই ইউরিয়া আর পটাশ সামান্য দিন। পাতার নিচে ছোট পোকা বা জালের মতো কিছু দেখলে বুঝবেন মাকড় লেগেছে। দোকান থেকে ভার্টিমেক কিনে স্প্রে দিন। বেশি পানি জমে থাকলেও বা একেবারেই না থাকলেও হলুদ হয়। মাটি ভেজা রাখবেন, কিন্তু জমাট পানি নয়।  

""" 

SYSTEM_INSTRUCTION_EN = """

You are an agriculture assistant for Bangladeshi farmers.  
You must ALWAYS reply only in ENGLISH, no matter what language the user uses.  
You can understand Bangla or other languages, but your output must stay in English only.  

System Rules for Device Control:
- If the user says "TURN ON THE LIGHT" or similar, reply: "Light has been turned ON".  
- If the user says "TURN OFF THE LIGHT" or similar, reply: "Light has been turned OFF".  

- If the user says "TURN ON THE SEED SOW" or similar, reply: "Seed sowing system has been turned ON".  
- If the user says "TURN OFF THE SEED SOW" or similar, reply: "Seed sowing system has been turned OFF".  

- If the user says "TURN ON THE FERTILIZER SYSTEM" or similar, reply: "Fertilizer system has been turned ON".  
- If the user says "TURN OFF THE FERTILIZER SYSTEM" or similar, reply: "Fertilizer system has been turned OFF".  

- If the user says "TURN ON THE WATER PUMP" or similar, reply: "Water pump has been turned ON".  
- If the user says "TURN OFF THE WATER PUMP" or similar, reply: "Water pump has been turned OFF".  
  

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
Q: Why are my rice plants getting black spots on leaves?  
A: If the spots are in the middle of the leaves and spreading slowly, it may be blast disease. You can buy Tilt or Nativo fungicide from the market. Mix 5–6 ml in 10 liters of water and spray during the daytime, not evening. Reduce excess fertilizer if used.  

Q: My onion plants are rotting, what should I do?  
A: Onion rot usually happens because of fungus. First, remove excess water from the base. You can spray Dithane M-45 or Ridomil, both are available in local shops. Also, keep the area clean from weeds, as fungus spreads faster if the field is dirty.  

Q: My plants are growing big but no fruits are coming, why?  
A: This happens mostly if too much urea fertilizer is used. Reduce urea, and add some potash and phosphorus. Pruning branches can also help the plant focus on fruits. Make sure the plants get at least 5–6 hours of sunlight daily.  

Q: Brinjal leaves are full of holes, what should I do?  
A: That is the brinjal leaf-eating pest. The insects usually hide under the leaves. You can buy Cypermethrin or Karate insecticide, mix 5 ml in 10 liters of water, and spray in the morning or evening. Repeat after 3 days if needed.  

Q: My tomato flowers are falling before fruits come, what can I do?  
A: Flower drop can happen if too much urea is used, or if water supply is irregular. Reduce urea and water regularly. If the weather is too cold, flowers may also drop. Spraying liquid boron once a week helps prevent flower drop.  

Q: My leaves are turning yellow, what’s the reason?  
A: Yellow leaves can be due to lack of urea or potash. Add a little fertilizer around the root. If you see small insects or webbing under the leaf, it’s mites. In that case, use Vertimec insecticide. If water is too much or too little, leaves also turn yellow. Keep the soil moist but not flooded. 

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
    """
    Synchronous TTS generation. Returns list of public URLs for saved mp3 files.
    """
    audio_urls = []
    for chunk in text_chunks:
        try:
            # Save file in OS-safe way
            chunk_mp3 = os.path.join("static", "audio", f"{uuid.uuid4()}.mp3")
            tts = gTTS(text=chunk, lang=lang, slow=False)
            tts.save(chunk_mp3)
            # Build public URL using host_url (works better behind proxies)
            base = request.host_url.rstrip('/')  # e.g. https://your-app.onrender.com
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

@cache.cached(timeout=300, query_string=True)
@limiter.limit("10 per minute")
@app.route('/ask', methods=['GET'])
def ask_bot():
    question = bleach.clean(request.args.get('q', ''))
    lang = request.args.get('lang', 'bn')
    if not question:
        return jsonify({'error': 'Missing question'}), 400

    try:
        full_prompt = f"{get_system_instruction(lang)}\n\nপ্রশ্ন: {question}\n\nউত্তর দিন:" if lang == 'bn' else f"{get_system_instruction(lang)}\n\nQuestion: {question}\n\nAnswer:"

        # FIXED: use client.models.generate_content (google-genai SDK)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        global primary_answer
        primary_answer = response.text.strip()

        # Get secondary translation
        global secondary_answer
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

@app.route("/esp32-receive/", methods=["GET"])
def esp32_receive():
    

    # Map to ESP32 commands
    if "লাইটটি চালু হয়েছে" in primary_answer or "The light has been turned on" in primary_answer:
        return "light_on"
    if "লাইটটি বন্ধ হয়েছে" in primary_answer or "The light has been turned off" in primary_answer:
        return "light_off"
    if "বীজ বপন ব্যবস্থা চালু হয়েছে" in primary_answer or "The seed sowing system has been turned on" in primary_answer:
        return "seed_sow_on"
    if "বীজ বপন ব্যবস্থা বন্ধ হয়েছে" in primary_answer or "The seed sowing system has been turned off" in primary_answer:
        return "seed_sow_off"
    if "কীটনাশক ব্যবস্থা চালু হয়েছে" in primary_answer or "The fertilizer system has been turned on" in primary_answer:
        return "fertilizer_on"
    if "কীটনাশক ব্যবস্থা বন্ধ হয়েছে" in primary_answer or "The fertilizer system has been turned off" in primary_answer:
        return "fertilizer_off"
    if "ওয়াটার পাম্প চালু হয়েছে" in primary_answer or "The water pump has been turned on" in primary_answer:
        return "water_pump_on"
    if "ওয়াটার পাম্প বন্ধ হয়েছে" in primary_answer or "The water pump has been turned off" in primary_answer:
        return "water_pump_off"
    return 0


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)