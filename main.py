from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Agri Bot API is running ✅"

@app.route('/ask', methods=['POST'])
def ask_bot():
    data = request.get_json()
    question = data.get('question')

    # TODO: Use OpenAI or your logic here
    # Dummy response
    answer = f"You asked: {question}. Here's your answer (pretend AI)."

    return jsonify({'answer': answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
