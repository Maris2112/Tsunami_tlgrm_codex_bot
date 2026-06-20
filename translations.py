"""i18n for the Tsunami bot. Languages: ru, kk (Kazakh), en.
detect_lang() picks the language from the user's message; for /start we fall
back to the Telegram app language (lang_from_code).
"""
import re

_KK = set("әғқңөұүһіӘҒҚҢӨҰҮҺІ")


def detect_lang(text):
    """Return 'ru' / 'kk' / 'en' from text, or None if there's no clear signal."""
    if not text:
        return None
    t = text.lower()
    if any(c in _KK for c in t):
        return "kk"
    if re.search(r"[а-яё]", t):
        return "ru"
    if re.search(r"[a-z]", t):
        return "en"
    return None


def lang_from_code(code):
    if not code:
        return None
    code = code.lower()
    for k in ("kk", "ru", "en"):
        if code.startswith(k):
            return k
    return None


GREET = {
    "ru": ["Доброе утро! ☀️ Солнце уже греет воду 🌊",
           "Привет! 🔥 Самый разгар летнего вайба 💦",
           "Добрый вечер! 🎧 Вечерний вайб включён 🍹",
           "Привет! 🌙 Сейчас мы закрыты, но утром снова ждём 💦"],
    "kk": ["Қайырлы таң! ☀️ Күн суды жылытып қойды 🌊",
           "Сәлем! 🔥 Жазғы көңіл-күй дәл қазір қызып тұр 💦",
           "Қайырлы кеш! 🎧 Кешкі вайб қосулы 🍹",
           "Сәлем! 🌙 Қазір жабықпыз, таңертең қайта күтеміз 💦"],
    "en": ["Good morning! ☀️ The sun is already warming the water 🌊",
           "Hey! 🔥 Peak summer vibe right now 💦",
           "Good evening! 🎧 Evening vibe is on 🍹",
           "Hi! 🌙 We're closed now, back in the morning 💦"],
}

T = {
    "ru": {
        "welcome": "Я <b>Tsunami AI</b> 🌊 — твой гид по летнему бассейну Tsunami в Алматы 🏖️\nВыбирай кнопку ниже или просто напиши вопрос 👇",
        "wa_menu": "📋 *Меню Tsunami* 🌊\n\n1 — 💰 Цены\n2 — 🕐 Часы работы\n3 — 📍 Как добраться\n4 — 🍸 Бар и меню\n5 — 🛏 Бронь топчана\n6 — 🎡 Колесо фортуны\n7 — 📞 Администратор\n\nНапиши *цифру* или просто задай вопрос 👇",
        "b_prices": "💰 Цены", "b_hours": "🕐 Часы работы", "b_bar": "🍸 Бар и меню",
        "b_loc": "📍 Как добраться", "b_book": "🛏 Бронь топчана", "b_events": "🎉 Афиша",
        "b_wheel": "🎡 Колесо фортуны", "b_admin": "📞 Администратор", "b_inst": "📲 Instagram",
        "b_menu": "📋 Меню",
        "prices": "💰 <b>Вход:</b>\n• Будни (Пн–Пт): 18+ — <b>7000₸</b>\n• Выходные (Сб–Вс): 21+ — <b>10000₸</b>\n\nСауна включена в стоимость 🧖",
        "hours": "🕐 Работаем <b>09:00–23:00</b>\n📅 Сезон: 1 июня – 31 августа ☀️",
        "events": "🎉 Каждые <b>Сб и Вс</b> — DJ-сеты и пенные вечеринки 🫧\n🧨 Каждый понедельник — «No Michelin Party» для HoReCa\nАфиша: @tsunami_almaty",
        "loc": "📍 Nurtazina 3a, Almaty\n🗺 <a href=\"{g}\">Google Maps</a> · <a href=\"{d}\">2GIS</a>",
        "bk1": "🛏 <b>Бронь топчана</b>\nШаг 1/5 — на какую <b>дату</b>? Выбери кнопку или напиши (например, 25.06).",
        "bk_today": "Сегодня", "bk_tomorrow": "Завтра", "bk_cancel": "✖️ Отмена",
        "bk2": "Шаг 2/5 — какая <b>зона</b>? 🛏",
        "z_std": "Standard (до 8 чел)", "z_vip1": "VIP 1 (до 35)", "z_vip2": "VIP 2 (до 18)",
        "bk3": "Шаг 3/5 — сколько <b>человек</b>? 👥",
        "bk4": "Шаг 4/5 — на чьё <b>имя</b> бронь? 📝",
        "bk5": "Шаг 5/5 — <b>телефон</b> для связи? 📞",
        "sum_date": "Дата", "sum_zone": "Зона", "sum_people": "Человек", "sum_name": "Имя", "sum_phone": "Телефон",
        "bk_done": "✅ <b>Заявка собрана!</b>\n\n{summary}\n\nНажми кнопку ниже — отправим её администратору, он подтвердит бронь 👇",
        "bk_send": "📲 Отправить админу в WhatsApp", "bk_cancelled": "Отменил бронь 👍",
        "wa_hi": "Здравствуйте! Хочу забронировать топчан 🛏",
        "w_already": "🎡 Сегодня ты уже крутил колесо!\nВозвращайся завтра за новым призом 😉",
        "w_win": "🎡 Крутим барабан... 🥁\n\n🎉 Тебе выпало:\n<b>{prize}</b>\n\nПокажи это сообщение на стойке, чтобы забрать приз 😉",
        "w_lose": "🎡 Крутим барабан... 🥁\n\n{prize}",
        "w_win_qr": "🎡 Крутим барабан... 🥁\n\n🎉 Поздравляем! Ты выиграл:\n<b>{prize}</b>\n\n📲 Покажи этот QR {who} — отсканируют и выдадут.\n⏳ Действует только сегодня.\nКод: <code>{code}</code>",
        "redeem_cashier": "кассиру", "redeem_entrance": "на входе",
    },
    "kk": {
        "welcome": "Мен <b>Tsunami AI</b> 🌊 — Алматыдағы Tsunami жазғы бассейнінің гидімін 🏖️\nТөмендегі батырманы таңда немесе жай ғана сұрағыңды жаз 👇",
        "wa_menu": "📋 *Tsunami мәзірі* 🌊\n\n1 — 💰 Бағалар\n2 — 🕐 Жұмыс уақыты\n3 — 📍 Қалай жетуге болады\n4 — 🍸 Бар және мәзір\n5 — 🛏 Топчан брондау\n6 — 🎡 Сәттілік дөңгелегі\n7 — 📞 Әкімші\n\n*Цифр* жаз немесе сұрағыңды қой 👇",
        "b_prices": "💰 Бағалар", "b_hours": "🕐 Жұмыс уақыты", "b_bar": "🍸 Бар және мәзір",
        "b_loc": "📍 Қалай жетуге болады", "b_book": "🛏 Топчан брондау", "b_events": "🎉 Афиша",
        "b_wheel": "🎡 Сәттілік дөңгелегі", "b_admin": "📞 Әкімші", "b_inst": "📲 Instagram",
        "b_menu": "📋 Мәзір",
        "prices": "💰 <b>Кіру:</b>\n• Жұмыс күндері (Дс–Жм): 18+ — <b>7000₸</b>\n• Демалыс (Сб–Жс): 21+ — <b>10000₸</b>\n\nСауна бағаға кіреді 🧖",
        "hours": "🕐 Жұмыс уақыты <b>09:00–23:00</b>\n📅 Маусым: 1 маусым – 31 тамыз ☀️",
        "events": "🎉 Әр <b>сенбі мен жексенбі</b> — DJ-сеттер және көбік кештері 🫧\n🧨 Әр дүйсенбі — HoReCa үшін «No Michelin Party»\nАфиша: @tsunami_almaty",
        "loc": "📍 Нұртазина 3а, Алматы\n🗺 <a href=\"{g}\">Google Maps</a> · <a href=\"{d}\">2GIS</a>",
        "bk1": "🛏 <b>Топчан брондау</b>\n1/5 қадам — қай <b>күнге</b>? Батырманы таңда немесе жаз (мысалы, 25.06).",
        "bk_today": "Бүгін", "bk_tomorrow": "Ертең", "bk_cancel": "✖️ Болдырмау",
        "bk2": "2/5 қадам — қай <b>аймақ</b>? 🛏",
        "z_std": "Standard (8 адамға дейін)", "z_vip1": "VIP 1 (35-ке дейін)", "z_vip2": "VIP 2 (18-ге дейін)",
        "bk3": "3/5 қадам — <b>неше адам</b>? 👥",
        "bk4": "4/5 қадам — бронь <b>кімнің атына</b>? 📝",
        "bk5": "5/5 қадам — байланыс <b>телефоны</b>? 📞",
        "sum_date": "Күні", "sum_zone": "Аймақ", "sum_people": "Адам", "sum_name": "Аты", "sum_phone": "Телефон",
        "bk_done": "✅ <b>Өтінім дайын!</b>\n\n{summary}\n\nТөмендегі батырманы бас — әкімшіге жібереміз, ол брондауды растайды 👇",
        "bk_send": "📲 Әкімшіге WhatsApp-та жіберу", "bk_cancelled": "Брондау тоқтатылды 👍",
        "wa_hi": "Сәлеметсіз бе! Топчан брондағым келеді 🛏",
        "w_already": "🎡 Бүгін дөңгелекті айналдырып қойдың!\nЕртең жаңа сыйлыққа қайт 😉",
        "w_win": "🎡 Дөңгелек айналуда... 🥁\n\n🎉 Саған түскені:\n<b>{prize}</b>\n\nСыйлықты алу үшін осы хабарламаны стойкада көрсет 😉",
        "w_lose": "🎡 Дөңгелек айналуда... 🥁\n\n{prize}",
        "w_win_qr": "🎡 Дөңгелек айналуда... 🥁\n\n🎉 Құттықтаймыз! Сен ұтып алдың:\n<b>{prize}</b>\n\n📲 Бұл QR-ды {who} көрсет — сканерлеп береді.\n⏳ Тек бүгін жарамды.\nКод: <code>{code}</code>",
        "redeem_cashier": "кассирге", "redeem_entrance": "кіреберісте",
    },
    "en": {
        "welcome": "I'm <b>Tsunami AI</b> 🌊 — your guide to the Tsunami summer pool in Almaty 🏖️\nPick a button below or just type your question 👇",
        "wa_menu": "📋 *Tsunami menu* 🌊\n\n1 — 💰 Prices\n2 — 🕐 Hours\n3 — 📍 How to get there\n4 — 🍸 Bar & menu\n5 — 🛏 Book a lounger\n6 — 🎡 Wheel of fortune\n7 — 📞 Administrator\n\nType a *number* or just ask 👇",
        "b_prices": "💰 Prices", "b_hours": "🕐 Hours", "b_bar": "🍸 Bar & menu",
        "b_loc": "📍 How to get there", "b_book": "🛏 Book a lounger", "b_events": "🎉 Events",
        "b_wheel": "🎡 Wheel of fortune", "b_admin": "📞 Administrator", "b_inst": "📲 Instagram",
        "b_menu": "📋 Menu",
        "prices": "💰 <b>Entry:</b>\n• Weekdays (Mon–Fri): 18+ — <b>7000₸</b>\n• Weekends (Sat–Sun): 21+ — <b>10000₸</b>\n\nSauna included 🧖",
        "hours": "🕐 Open <b>09:00–23:00</b>\n📅 Season: June 1 – August 31 ☀️",
        "events": "🎉 Every <b>Sat & Sun</b> — DJ sets and foam parties 🫧\n🧨 Every Monday — “No Michelin Party” for HoReCa\nEvents: @tsunami_almaty",
        "loc": "📍 Nurtazina 3a, Almaty\n🗺 <a href=\"{g}\">Google Maps</a> · <a href=\"{d}\">2GIS</a>",
        "bk1": "🛏 <b>Book a lounger</b>\nStep 1/5 — which <b>date</b>? Tap a button or type it (e.g. 25.06).",
        "bk_today": "Today", "bk_tomorrow": "Tomorrow", "bk_cancel": "✖️ Cancel",
        "bk2": "Step 2/5 — which <b>zone</b>? 🛏",
        "z_std": "Standard (up to 8)", "z_vip1": "VIP 1 (up to 35)", "z_vip2": "VIP 2 (up to 18)",
        "bk3": "Step 3/5 — how many <b>people</b>? 👥",
        "bk4": "Step 4/5 — <b>name</b> for the booking? 📝",
        "bk5": "Step 5/5 — contact <b>phone</b>? 📞",
        "sum_date": "Date", "sum_zone": "Zone", "sum_people": "People", "sum_name": "Name", "sum_phone": "Phone",
        "bk_done": "✅ <b>Request ready!</b>\n\n{summary}\n\nTap below — we'll send it to the administrator to confirm 👇",
        "bk_send": "📲 Send to admin on WhatsApp", "bk_cancelled": "Booking cancelled 👍",
        "wa_hi": "Hello! I'd like to book a lounger 🛏",
        "w_already": "🎡 You already spun today!\nCome back tomorrow for a new prize 😉",
        "w_win": "🎡 Spinning the wheel... 🥁\n\n🎉 You got:\n<b>{prize}</b>\n\nShow this message at the counter to claim it 😉",
        "w_lose": "🎡 Spinning the wheel... 🥁\n\n{prize}",
        "w_win_qr": "🎡 Spinning the wheel... 🥁\n\n🎉 Congrats! You won:\n<b>{prize}</b>\n\n📲 Show this QR to {who} — they'll scan and give it to you.\n⏳ Valid today only.\nCode: <code>{code}</code>",
        "redeem_cashier": "the cashier", "redeem_entrance": "at the entrance",
    },
}

# Wheel prizes — aligned by index. key/role drive redemption; w = weight.
PRIZES = [
    {"key": "none",    "w": 35, "real": False, "role": None,      "ru": "🎁 В этот раз не повезло — лови вайб и приходи завтра!", "kk": "🎁 Бұл жолы сәтсіз — вайбты ұста, ертең кел!", "en": "🎁 No luck this time — catch the vibe and come back tomorrow!"},
    {"key": "shot",    "w": 25, "real": True,  "role": "cashier", "ru": "🥃 Шот (на выбор бармена)", "kk": "🥃 Шот (бармен таңдауымен)", "en": "🥃 Shot (bartender's choice)"},
    {"key": "beer",    "w": 18, "real": True,  "role": "cashier", "ru": "🍺 Кружка пива (на выбор бармена)", "kk": "🍺 Сыра кружкасы (бармен таңдауымен)", "en": "🍺 Mug of beer (bartender's choice)"},
    {"key": "welcome", "w": 10, "real": True,  "role": "cashier", "ru": "🥤 Велком-дринк", "kk": "🥤 Велком-дринк", "en": "🥤 Welcome drink"},
    {"key": "pizza",   "w": 6,  "real": True,  "role": "cashier", "ru": "🍕 Пицца", "kk": "🍕 Пицца", "en": "🍕 Pizza"},
    {"key": "entry",   "w": 6,  "real": True,  "role": "entrance","ru": "🎟 Входной билет", "kk": "🎟 Кіру билеті", "en": "🎟 Entry ticket"},
]


def t(lang, key, **kw):
    d = T.get(lang) or T["ru"]
    s = d.get(key) or T["ru"].get(key, key)
    return s.format(**kw) if kw else s


def greet(lang, idx):
    return (GREET.get(lang) or GREET["ru"])[idx]
