from flask import Flask, request, jsonify
import requests
import traceback
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# ✅ Загрузка переменных окружения из файла .env
load_dotenv()

# ✅ Получение ключей из окружения
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SYSTEM_PROMPT_PATH = os.environ.get("SYSTEM_PROMPT_PATH", "system_prompt.txt")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")

# ✅ Прямо в коде зашит ключ (для стабильности на проде)
OPENROUTER_API_KEY = "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"

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
            "HTTP-Referer": "https://tsunami-whatsapp.up.railway.app",  # ✅ рейтинг
            "X-Title": "Tsunami Telegram Bot"  # ✅ отображение на openrouter.ai
        }

        # 🔍 Печать заголовков перед запросом
        print("[DEBUG] Headers sent to OpenRouter:", headers)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": full_question},
        ]

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": messages
        }

        import json
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)  # ⚠️ важно: data=, не json=
        )

        # 🔍 Печать текста ответа
        print("[DEBUG] OpenRouter response text:", response.text)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("[ERROR] OpenRouter call failed:", e)
        traceback.print_exc()
        return "⚠️ Ошибка ИИ. Попробуй позже."


# === SEND TELEGRAM ===
def send_telegram_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=payload)
        print("[SEND TG]", response.status_code, response.text)
    except Exception:
        print("[ERROR] Telegram message failed:")
        traceback.print_exc()

# === TELEGRAM WEBHOOK ===
@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json(force=True)
        print("[TG WEBHOOK]", data)

        message = data.get("message", {})
        text = message.get("text")
        sender_id = message.get("chat", {}).get("id")

        if not text or not sender_id:
            print("[SKIP] Empty Telegram message.")
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

# === HEALTHCHECK ===
@app.route("/", methods=["GET"])
def root():
    return "TsunamiBot для Telegram + OpenRouter запущен ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


