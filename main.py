from flask import Flask, request, jsonify
import requests
import traceback
import os
import urllib.parse
import random
import threading
import time as _time
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

import db
import translations as i18n

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SYSTEM_PROMPT_PATH = os.environ.get("SYSTEM_PROMPT_PATH", "system_prompt.txt")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# --- Venue config (keep in sync with system_prompt.txt) ---
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "77777195000")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
INSTAGRAM_URL = "https://www.instagram.com/tsunami_almaty"
GMAPS_URL = "https://www.google.com/maps/search/?api=1&query=43.1624331,76.8991943"
GIS_URL = "https://go.2gis.com/Jbq8h"
POOL_LAT, POOL_LON = 43.1624331, 76.8991943
BOT_USERNAME = os.getenv("BOT_USERNAME", "tsunamiAIBot")


def _ids(name):
    return set(int(x) for x in os.getenv(name, "").replace(";", ",").split(",") if x.strip().isdigit())


ENTRANCE_IDS = _ids("ENTRANCE_IDS")     # who redeems 🎟 entry tickets
CASHIER_IDS = _ids("CASHIER_IDS")       # who redeems 🥃🍺🥤🍕
ADMIN_REPORT_CHAT = os.getenv("ADMIN_REPORT_CHAT")   # daily report at 23:00 Almaty

with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

db.init_db()

app = Flask(__name__)
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
ALMATY = pytz.timezone("Asia/Almaty")

conversation_memory = {}
processed_messages = set()
user_lang = {}            # chat_id -> 'ru'/'kk'/'en'

CANCEL_WORDS = ("отмена", "/cancel", "стоп", "cancel", "болдырмау", "тоқта")
MENU_WORDS = ("/start", "/menu", "/help", "меню", "menu", "мәзір")


# ===================== Language =====================
def update_lang(chat_id, frm=None, text=None):
    # current preference: memory -> DB -> default
    if chat_id not in user_lang:
        stored = db.get_user_lang(chat_id)
        user_lang[chat_id] = stored or "ru"
        had_pref = stored is not None
    else:
        had_pref = True
    new = None
    if text:
        low = text.strip().lower()
        # don't infer language from commands / menu words ("/start" looks English)
        if not low.startswith("/") and low not in MENU_WORDS:
            new = i18n.detect_lang(text)              # strong signal — may override
    if new is None and not had_pref and frm:
        new = i18n.lang_from_code(frm.get("language_code"))   # init only, never overrides
    if new and new != user_lang.get(chat_id):
        user_lang[chat_id] = new
        db.set_user_lang(chat_id, new)
    return user_lang[chat_id]


def L(chat_id):
    if chat_id not in user_lang:
        user_lang[chat_id] = db.get_user_lang(chat_id) or "ru"
    return user_lang[chat_id]


# ===================== OpenRouter =====================
def ask_openrouter(question, history=[]):
    try:
        now = datetime.now(ALMATY).strftime("%A, %d %B %Y, %H:%M")
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://tsunami-telegram-bot-production.up.railway.app",
            "X-Title": "Tsunami Telegram Bot",
        }
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": f"[{now}] {question}"},
        ]
        payload = {"model": OPENROUTER_MODEL, "messages": messages}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("[ERROR] OpenRouter call failed:", e)
        traceback.print_exc()
        return "⚠️ Ошибка ИИ. Попробуй позже."


# ===================== Telegram helpers =====================
def tg(method, payload):
    try:
        if not TELEGRAM_BOT_TOKEN:
            print("[ERROR] TELEGRAM_BOT_TOKEN пустой")
            return None
        return requests.post(f"{TG_API}/{method}", json=payload, timeout=20).json()
    except Exception:
        print(f"[ERROR] Telegram {method} failed:")
        traceback.print_exc()
        return None


def send_message(chat_id, text, reply_markup=None, html=False):
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if html:
        payload["parse_mode"] = "HTML"
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg("sendMessage", payload)


def send_photo(chat_id, photo, caption=None, reply_markup=None):
    payload = {"chat_id": chat_id, "photo": photo}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg("sendPhoto", payload)


def gen_code():
    return "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))


def staff_role(user_id):
    if user_id in CASHIER_IDS:
        return "cashier"
    if user_id in ENTRANCE_IDS:
        return "entrance"
    return None


# ===================== Menu / vibe =====================
def main_menu_kb(lang):
    T = i18n.t
    return {"inline_keyboard": [
        [{"text": T(lang, "b_prices"), "callback_data": "prices"},
         {"text": T(lang, "b_hours"), "callback_data": "hours"}],
        [{"text": T(lang, "b_bar"), "url": INSTAGRAM_URL},
         {"text": T(lang, "b_loc"), "callback_data": "location"}],
        [{"text": T(lang, "b_book"), "callback_data": "booking"},
         {"text": T(lang, "b_events"), "callback_data": "events"}],
        [{"text": T(lang, "b_admin"), "url": f"https://wa.me/{ADMIN_PHONE}"},
         {"text": T(lang, "b_inst"), "url": INSTAGRAM_URL}],
    ]}


def menu_hint_kb(lang):
    return {"inline_keyboard": [[{"text": i18n.t(lang, "b_menu"), "callback_data": "menu"}]]}


def greeting(lang):
    h = datetime.now(ALMATY).hour
    idx = 0 if 5 <= h < 12 else 1 if 12 <= h < 17 else 2 if 17 <= h < 23 else 3
    return i18n.greet(lang, idx)


def send_main_menu(chat_id):
    lang = L(chat_id)
    send_message(chat_id, f"{greeting(lang)}\n\n{i18n.t(lang, 'welcome')}", main_menu_kb(lang), html=True)


# ===================== Daily report (23:00 Almaty) =====================
def build_report(day):
    day_start_utc = datetime.now(ALMATY).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.UTC)
    d = db.report_data(day, day_start_utc)
    lines = [f"📊 <b>Отчёт Tsunami за {day.strftime('%d.%m.%Y')}</b>", "",
             f"🎡 Прокрутов колеса: <b>{d['spins']}</b>",
             f"🎁 Призов выиграно: <b>{sum(c for _, c in d['won'])}</b>"]
    for plabel, cnt in d["won"]:
        lines.append(f"   • {plabel}: {cnt}")
    lines.append(f"✅ Призов погашено: <b>{d['redeemed']}</b>")
    lines.append(f"🛏 Новых контактов/броней: <b>{d['contacts']}</b>")
    return "\n".join(lines)


def is_report_viewer(chat_id):
    return (ADMIN_REPORT_CHAT and str(chat_id) == str(ADMIN_REPORT_CHAT)) or staff_role(chat_id) is not None


def send_daily_report(day):
    send_message(ADMIN_REPORT_CHAT, build_report(day), html=True)


def report_loop():
    while True:
        try:
            now = datetime.now(ALMATY)
            day = now.date()
            if ADMIN_REPORT_CHAT and now.hour >= 23 and not db.report_sent(day):
                send_daily_report(day)
                db.mark_report(day)
        except Exception:
            traceback.print_exc()
        _time.sleep(300)


def handle_callback(cq):
    chat_id = cq.get("message", {}).get("chat", {}).get("id")
    update_lang(chat_id, cq.get("from"))
    lang = L(chat_id)
    data = cq.get("data")
    tg("answerCallbackQuery", {"callback_query_id": cq.get("id")})

    if data == "booking":
        send_message(chat_id, i18n.t(lang, "book_call"), menu_hint_kb(lang), html=True); return
    if data == "menu":
        send_main_menu(chat_id); return
    if data == "location":
        tg("sendLocation", {"chat_id": chat_id, "latitude": POOL_LAT, "longitude": POOL_LON})
        send_message(chat_id, i18n.t(lang, "loc", g=GMAPS_URL, d=GIS_URL), html=True); return
    if data in ("prices", "hours", "events"):
        send_message(chat_id, i18n.t(lang, data), html=True)


# ===================== Webhook =====================
@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json(force=True)
        print("[TG WEBHOOK]", data)

        update_id = data.get("update_id")
        if update_id in processed_messages:
            return jsonify({"status": "duplicate"}), 200
        processed_messages.add(update_id)

        if "callback_query" in data:
            handle_callback(data["callback_query"])
            return jsonify({"status": "ok"}), 200

        message = data.get("message", {})
        text = message.get("text")
        sender_id = message.get("chat", {}).get("id")
        if not text or not sender_id:
            return jsonify({"status": "no-message"}), 200

        update_lang(sender_id, message.get("from"), text)
        low = text.strip().lower()

        if low == "/myid":
            send_message(sender_id, f"🆔 Ваш Telegram ID: <code>{sender_id}</code>", html=True)
            return jsonify({"status": "ok"}), 200

        if low.startswith("/report") or low in ("отчет", "отчёт", "report"):
            if is_report_viewer(sender_id):
                send_message(sender_id, build_report(datetime.now(ALMATY).date()), html=True)
            else:
                send_message(sender_id, "🔒 Отчёт доступен только администратору и персоналу.")
            return jsonify({"status": "ok"}), 200

        if low in MENU_WORDS:
            send_main_menu(sender_id)
            return jsonify({"status": "ok"}), 200

        history = conversation_memory.get(sender_id, [])[-6:]
        reply = ask_openrouter(text, history)
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": reply})
        conversation_memory[sender_id] = history
        send_message(sender_id, reply, menu_hint_kb(L(sender_id)))
        return jsonify({"status": "ok"}), 200

    except Exception:
        traceback.print_exc()
        return jsonify({"status": "fail"}), 500


@app.route("/", methods=["GET"])
def root():
    return "TsunamiBot Telegram запущен ✅"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=report_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=port)
