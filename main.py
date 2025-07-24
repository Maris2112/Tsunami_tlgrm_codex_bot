from flask import Flask, request, jsonify
import requests
import traceback
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SYSTEM_PROMPT_PATH = os.environ.get("SYSTEM_PROMPT_PATH", "system_prompt.txt")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

app = Flask(__name__)

conversation_memory = {}
processed_messages = set()

def ask_openrouter(question, history=[]):
    try:
        tz = pytz.timezone("Asia/Almaty")
        now = datetime.now(tz).strftime("%A, %d %B %Y, %H:%M")
        full_question = f"[{now}] {question}"

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://tsunami-whatsapp.up.railway.app",
            "X-Title": "Tsunami Telegram Bot"
        }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": full_question},
        ]

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": messages
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("[ERROR] OpenRouter call failed:", e)
        traceback.print_exc()
        return "⚠️ Ошибка ИИ. Попробуй позже."

def send_telegram_message(chat_id, text):
    try:
        if not TELEGRAM_BOT_TOKEN:
            print("[ERROR] TELEGRAM_BOT_TOKEN пустой")
            return

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        print("[SEND TG PAYLOAD]", payload)
        response = requests.post(url, json=payload)
        print("[SEND TG]", response.status_code, response.text)
    except Exception:
        print("[ERROR] Telegram message failed:")
        traceback.print_exc()

@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json(force=True)
        print("[TG WEBHOOK]", data)

        update_id = data.get("update_id")
        if update_id in processed_messages:
            print(f"[DUPLICATE] Уже обработано: {update_id}")
            return jsonify({"status": "duplicate"}), 200
        processed_messages.add(update_id)

        message = data.get("message", {})
        text = message.get("text")
        sender_id = message.get("chat", {}).get("id")

        if not text or not sender_id:
            print("[SKIP] Пустое сообщение или ID")
            return jsonify({"status": "no-message"}), 200

        history = conversation_memory.get(sender_id, [])[-6:]
        reply = ask_openrouter(text, history)

        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": reply})
        conversation_memory[sender_id] = history

        send_telegram_message(sender_id, reply)
        return jsonify({"status": "ok"}), 200

    except Exception:
        traceback.print_exc()
        return jsonify({"status": "fail"}), 500

@app.route("/", methods=["GET"])
def root():
    return "TsunamiBot Telegram запущен ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
