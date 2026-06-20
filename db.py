"""Lightweight Postgres layer for Tsunami bot.
Stores guest contacts (from bookings) and daily wheel spins.
Degrades gracefully: if DATABASE_URL is missing or DB is unreachable,
functions no-op / allow, so the bot keeps working without the DB.
"""
import os
import traceback
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")


def _conn():
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)


def _run(sql, params=(), fetch=False, many=False):
    if not DATABASE_URL:
        return [] if many else None
    conn = None
    try:
        conn = _conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchall() if many else (cur.fetchone() if fetch else None)
        conn.commit()
        return row
    except Exception as e:
        print("[DB] query failed:", e)
        traceback.print_exc()
        return [] if many else None
    finally:
        if conn is not None:
            conn.close()


def init_db():
    if not DATABASE_URL:
        print("[DB] DATABASE_URL not set — DB disabled, bot runs without persistence")
        return
    _run("""CREATE TABLE IF NOT EXISTS contacts (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT,
        name TEXT,
        phone TEXT,
        source TEXT,
        extra TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    )""")
    _run("""CREATE TABLE IF NOT EXISTS spins (
        chat_id BIGINT,
        spin_date DATE,
        prize TEXT,
        created_at TIMESTAMPTZ DEFAULT now(),
        PRIMARY KEY (chat_id, spin_date)
    )""")
    _run("""CREATE TABLE IF NOT EXISTS user_prefs (
        chat_id BIGINT PRIMARY KEY,
        lang TEXT,
        updated_at TIMESTAMPTZ DEFAULT now()
    )""")
    _run("""CREATE TABLE IF NOT EXISTS prizes (
        code TEXT PRIMARY KEY,
        chat_id BIGINT,
        prize_key TEXT,
        prize_label TEXT,
        role TEXT,
        status TEXT DEFAULT 'issued',
        valid_date DATE,
        created_at TIMESTAMPTZ DEFAULT now(),
        redeemed_at TIMESTAMPTZ,
        redeemed_by BIGINT
    )""")
    _run("""CREATE TABLE IF NOT EXISTS daily_reports (
        report_date DATE PRIMARY KEY,
        sent_at TIMESTAMPTZ DEFAULT now()
    )""")
    print("[DB] init OK")


# ----- Prizes -----
def create_prize(code, chat_id, prize_key, prize_label, role, valid_date):
    _run("INSERT INTO prizes (code, chat_id, prize_key, prize_label, role, valid_date) "
         "VALUES (%s,%s,%s,%s,%s,%s)", (code, chat_id, prize_key, prize_label, role, valid_date))


def get_prize(code):
    row = _run("SELECT prize_key, prize_label, role, status, valid_date FROM prizes WHERE code=%s",
               (code,), fetch=True)
    if not row:
        return None
    return {"prize_key": row[0], "prize_label": row[1], "role": row[2], "status": row[3], "valid_date": row[4]}


def redeem_prize(code, staff_id, today):
    """Atomically redeem if issued and valid today. Returns prize_label or None."""
    row = _run("UPDATE prizes SET status='redeemed', redeemed_at=now(), redeemed_by=%s "
               "WHERE code=%s AND status='issued' AND valid_date=%s RETURNING prize_label",
               (staff_id, code, today), fetch=True)
    return row[0] if row else None


# ----- Daily report -----
def report_data(day, day_start_utc):
    spins = (_run("SELECT count(*) FROM spins WHERE spin_date=%s", (day,), fetch=True) or [0])[0]
    won = _run("SELECT prize_label, count(*) FROM prizes WHERE valid_date=%s GROUP BY prize_label ORDER BY 2 DESC",
               (day,), many=True) or []
    redeemed = (_run("SELECT count(*) FROM prizes WHERE valid_date=%s AND status='redeemed'", (day,), fetch=True) or [0])[0]
    contacts = (_run("SELECT count(*) FROM contacts WHERE created_at >= %s", (day_start_utc,), fetch=True) or [0])[0]
    return {"spins": spins, "won": won, "redeemed": redeemed, "contacts": contacts}


def report_sent(day):
    return _run("SELECT 1 FROM daily_reports WHERE report_date=%s", (day,), fetch=True) is not None


def mark_report(day):
    _run("INSERT INTO daily_reports (report_date) VALUES (%s) ON CONFLICT DO NOTHING", (day,))


def get_user_lang(chat_id):
    if not DATABASE_URL:
        return None
    row = _run("SELECT lang FROM user_prefs WHERE chat_id=%s", (chat_id,), fetch=True)
    return row[0] if row else None


def set_user_lang(chat_id, lang):
    _run("INSERT INTO user_prefs (chat_id, lang) VALUES (%s, %s) "
         "ON CONFLICT (chat_id) DO UPDATE SET lang=EXCLUDED.lang, updated_at=now()",
         (chat_id, lang))


def save_contact(chat_id, name, phone, source="booking", extra=None):
    """Store a guest contact (name + phone). Called when a booking is completed."""
    _run(
        "INSERT INTO contacts (chat_id, name, phone, source, extra) VALUES (%s,%s,%s,%s,%s)",
        (chat_id, name, phone, source, extra),
    )


def can_spin_today(chat_id):
    """True if this chat has NOT spun the wheel yet today. No DB -> allow."""
    if not DATABASE_URL:
        return True
    row = _run(
        "SELECT 1 FROM spins WHERE chat_id=%s AND spin_date=CURRENT_DATE",
        (chat_id,), fetch=True,
    )
    return row is None


def record_spin(chat_id, prize):
    """Mark today's spin for this chat (idempotent per day)."""
    _run(
        "INSERT INTO spins (chat_id, spin_date, prize) VALUES (%s, CURRENT_DATE, %s) "
        "ON CONFLICT (chat_id, spin_date) DO NOTHING",
        (chat_id, prize),
    )
