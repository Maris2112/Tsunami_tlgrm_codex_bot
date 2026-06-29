# Tsunami Telegram Bot 🌊

AI-ассистент летнего бассейна **Tsunami** (Алматы, Nurtazina 3a) для **Telegram**.
Отвечает гостям на 3 языках (RU/KZ/EN), показывает кнопочное меню и шлёт владельцу ежедневный отчёт.
Бронь топчанов — по телефону администратора.

Прод: `https://tsunami-telegram-bot-production.up.railway.app` · бот **@tsunamiAIBot**

---

## Возможности
- **🤖 ИИ-ответы** на свободные вопросы через OpenRouter (`system_prompt.txt` = «мозг»/контент).
- **🌐 Мультиязык** — определяет язык каждого сообщения (RU/KZ/EN), язык запоминается в БД (`user_prefs`).
- **📋 Меню на кнопках** (`/start`): Цены · Часы · Как добраться (гео-пин) · Бар · Бронь · Афиша · Админ · Instagram. Готовые карточки — мгновенно, без трат на ИИ.
- **🛏 Бронь топчана** — только по телефону: бот показывает номер администратора для звонка (мастер брони и отправка заявки из бота убраны).
- **📊 Ежедневный отчёт** в 23:00 (Asia/Almaty) на чат админа: прокруты, призы, гашения, новые контакты (фоновый поток).
- **🆔 `/myid`** — сотрудник узнаёт свой Telegram ID (для настройки ролей).

## Архитектура
```
Telegram → POST /webhook (Flask) → роутер:
  /start, "меню"            → меню (inline-кнопки)
  callback кнопок           → готовые карточки / гео / бронь (звонок админу)
  свободный текст           → OpenRouter (gemini-2.5-flash-lite) + кнопка «Меню»
Фоновый поток → ежедневный отчёт в 23:00 Almaty
```

## Файлы
- `main.py` — вебхук, меню, бронь (звонок админу), отчёт.
- `db.py` — Postgres (psycopg2): `contacts`, `spins`, `prizes`, `user_prefs`, `daily_reports`. Деградирует мягко, если БД недоступна.
- `translations.py` — строки UI и призы на RU/KZ/EN + определение языка.
- `system_prompt.txt` — персона и контент бассейна (цены, правила, контакты). **Главная точка редактирования контента.**

## Переменные окружения
| Переменная | Назначение |
|---|---|
| `TELEGRAM_BOT_TOKEN` | токен @BotFather (секрет) |
| `OPENROUTER_API_KEY` | ключ OpenRouter (секрет) |
| `OPENROUTER_MODEL` | модель, по умолчанию `google/gemini-2.5-flash-lite` |
| `DATABASE_URL` | Postgres (на Railway — ссылка `${{Postgres.DATABASE_URL}}`) |
| `ENTRANCE_IDS` | Telegram ID сотрудников «вход» (через запятую) |
| `CASHIER_IDS` | Telegram ID «кассир» |
| `ADMIN_REPORT_CHAT` | чат для ежедневного отчёта |
| `ADMIN_PHONE` | WhatsApp админа для брони (по умолч. 77777195000) |
| `BOT_USERNAME` | username бота для QR-ссылки (по умолч. tsunamiAIBot) |
| `SYSTEM_PROMPT_PATH` | путь к промпту (по умолч. system_prompt.txt) |

## Запуск локально
```bash
pip install -r requirements.txt
# создать .env с переменными выше, затем:
python main.py            # слушает PORT (8080), эндпоинт /webhook
```
Webhook регистрируется один раз: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<домен>/webhook`

## Деплой
Railway (план Hobby). `Procfile`: `web: python main.py`. Деплой кода: `railway up`. Postgres — отдельный сервис в проекте; `DATABASE_URL` пробрасывается ссылкой.

> ⚠️ Секреты никогда не коммитятся (`.env` в `.gitignore`).
