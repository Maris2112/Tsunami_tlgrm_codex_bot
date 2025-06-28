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
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")

# === CONFIG ===
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SYSTEM_PROMPT_PATH = os.environ.get("SYSTEM_PROMPT_PATH", "system_prompt.txt")

with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

app = Flask(__name__)

# === MEMORY ===
conversation_memory = {}

# === CALL OPENROUTER ===
# === CALL OPENROUTER ===
def ask_openrouter(question, history=[]):
    try:
        tz = pytz.timezone("Asia/Almaty")
        now = datetime.now(tz).strftime("%A, %d %B %Y, %H:%M")
        full_question = f"[{now}] {question}"

        # ✅ Ключ зашит напрямую
        OPENROUTER_API_KEY = "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"
        OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://tsunami-whatsapp.up.railway.app",  # ✅ для рейтинга
            "X-Title": "Tsunami Telegram Bot"  # ✅ для рейтинга на openrouter.ai
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

        import json
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)  # ✅ ключевой фикс
        )

        print("[DEBUG] OpenRouter response text:", response.text)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("[ERROR] OpenRouter call failed:", e)
        return "⚠️ Ошибка ИИ. Попробуй позже."

# === HEALTHCHECK ===
@app.route("/", methods=["GET"])
def root():
    return "TsunamiBot for Telegram + OpenRouter is running ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
