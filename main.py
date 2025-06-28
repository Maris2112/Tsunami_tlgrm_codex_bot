from flask import Flask, request, jsonify
import requests
import traceback
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
GREENAPI_INSTANCE_ID = os.environ.get("GREENAPI_INSTANCE_ID")
GREENAPI_TOKEN = os.environ.get("GREENAPI_TOKEN")
GREENAPI_API_URL = os.environ.get("GREENAPI_API_URL")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
BOT_CHAT_ID = os.environ.get("BOT_ID")
SYSTEM_PROMPT_PATH = os.environ.get("SYSTEM_PROMPT_PATH", "system_prompt.txt")

with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

app = Flask(__name__)

# === MEMORY ===
conversation_memory = {}

# === CALL OPENROUTER ===
def ask_openrouter(question, history=[]):
    try:
        tz = pytz.timezone("Asia/Almaty")
        now = datetime.now(tz).strftime("%A, %d %B %Y, %H:%M")
        full_question = f"[{now}] {question}"

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": full_question},
        ]
        payload = {
            "model": "meta-llama/llama-3-70b-instruct",
            "messages": messages
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("[ERROR] OpenRouter call failed:", e)
        return "⚠️ Ошибка ИИ. Попробуй позже."

# === SEND MESSAGE ===
def send_whatsapp_message(chat_id, text):
    try:
        url = f"{GREENAPI_API_URL}/waInstance{GREENAPI_INSTANCE_ID}/sendMessage/{GREENAPI_TOKEN}"
        payload = {"chatId": chat_id, "message": text}
        response = requests.post(url, json=payload)
        print("[SEND]", response.status_code, response.text)
    except Exception:
        print("[ERROR] WhatsApp message failed:")
        traceback.print_exc()

# === WEBHOOK ===
@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    try:
        data = request.get_json(force=True)
        print("[WEBHOOK]", data)

        sender_id = data.get("senderData", {}).get("chatId")
        if sender_id == BOT_CHAT_ID:
            print("[SKIP] Self-message detected.")
            return jsonify({"status": "self-message"}), 200

        message_data = data.get("messageData", {})
        message = None
        if "textMessageData" in message_data:
            message = message_data["textMessageData"].get("textMessage")
        elif "extendedTextMessageData" in message_data:
            message = message_data["extendedTextMessageData"].get("text")

        if not message:
            print("[SKIP] No valid message")
            return jsonify({"status": "no-message"}), 200

        history = conversation_memory.get(sender_id, [])[-6:]  # до 3 пар (вопрос+ответ)
        reply = ask_openrouter(message, history)

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        conversation_memory[sender_id] = history

        send_whatsapp_message(sender_id, reply)
        return jsonify({"status": "ok"}), 200

    except Exception:
        traceback.print_exc()
        return jsonify({"status": "fail"}), 500

# === HEALTHCHECK ===
@app.route("/", methods=["GET"])
def root():
    return "TsunamiBot with OpenRouter is running ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
