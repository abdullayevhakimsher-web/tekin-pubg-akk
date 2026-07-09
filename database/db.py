# ============================================================
#  database/db.py  –  SQLite3 bilan ishlash uchun barcha
#  ma'lumotlar bazasi operatsiyalari
# ============================================================

import sqlite3
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = "bot_database.db"


# ─────────────────────────────────────────────────────────────
#  Ulanish yordamchisi
# ─────────────────────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    """SQLite ulanishini qaytaradi, Row factory sozlangan."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # natijalarni dict kabi ishlatish uchun
    conn.execute("PRAGMA journal_mode=WAL") # Concurrent o'qish uchun
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─────────────────────────────────────────────────────────────
#  Jadvallarni yaratish
# ─────────────────────────────────────────────────────────────
def create_tables() -> None:
    """
    Barcha kerakli jadvallarni (mavjud bo'lmasa) yaratadi.
    Bot ishga tushganda bir marta chaqiriladi.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # --- Foydalanuvchilar jadvali ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id                    INTEGER PRIMARY KEY,   -- Telegram user_id
                ism                   TEXT    NOT NULL,
                ball                  INTEGER NOT NULL DEFAULT 0,
                taklif_qilgan_soni    INTEGER NOT NULL DEFAULT 0,
                referral_by           INTEGER,               -- Kim taklif qilganini saqlaydi
                registered_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- Majburiy kanallar jadvali ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                kanal_haqolasi  TEXT    NOT NULL UNIQUE    -- @username yoki invite link
            )
        """)

        # --- Akkauntlar jadvali ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                rasm_id     TEXT    NOT NULL,               -- Telegram file_id
                email       TEXT    NOT NULL,
                parol       TEXT    NOT NULL,
                tur         TEXT    NOT NULL CHECK(
                    tur IN ('tekin_pubg', 'pullik_google', 'balli_akk')
                ),
                narx_ball   INTEGER NOT NULL DEFAULT 0,    -- 0 = tekin
                is_sold     INTEGER NOT NULL DEFAULT 0,     -- 0=mavjud, 1=sotilgan
                sold_to     INTEGER,                        -- sotilgan foydalanuvchi ID si
                added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # --- Referal bonus sozlamasi jadvali (bir qatorli) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key     TEXT PRIMARY KEY,
                value   TEXT NOT NULL
            )
        """)

        # Default referal bonus qiymatini yozing (agar yo'q bo'lsa)
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('referral_bonus', '10')
        """)

        conn.commit()
    logger.info("✅ Ma'lumotlar bazasi jadvallari muvaffaqiyatli yaratildi.")


# ─────────────────────────────────────────────────────────────
#  USERS CRUD
# ─────────────────────────────────────────────────────────────
def add_user(user_id: int, ism: str, referral_by: Optional[int] = None) -> bool:
    """
    Yangi foydalanuvchini bazaga qo'shadi.
    Agar foydalanuvchi allaqachon mavjud bo'lsa, False qaytaradi.
    """
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (id, ism, referral_by)
                VALUES (?, ?, ?)
                """,
                (user_id, ism, referral_by)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Foydalanuvchi allaqachon mavjud


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    """ID bo'yicha foydalanuvchini qaytaradi."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def user_exists(user_id: int) -> bool:
    """Foydalanuvchi bazada mavjudligini tekshiradi."""
    return get_user(user_id) is not None


def update_user_balls(user_id: int, amount: int) -> None:
    """Foydalanuvchi balini oshiradi yoki kamaytiradi (+/-)."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET ball = ball + ? WHERE id = ?",
            (amount, user_id)
        )
        conn.commit()


def increment_referral_count(user_id: int) -> None:
    """Referal taklif qilganlar sonini 1 ga oshiradi."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET taklif_qilgan_soni = taklif_qilgan_soni + 1 WHERE id = ?",
            (user_id,)
        )
        conn.commit()


def get_all_users() -> List[sqlite3.Row]:
    """Barcha foydalanuvchilarni qaytaradi."""
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users").fetchall()


def get_top_referrers(limit: int = 10) -> List[sqlite3.Row]:
    """Eng ko'p odam taklif qilgan foydalanuvchilarni qaytaradi."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, ism, ball, taklif_qilgan_soni
            FROM users
            ORDER BY taklif_qilgan_soni DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()


# ─────────────────────────────────────────────────────────────
#  CHANNELS CRUD
# ─────────────────────────────────────────────────────────────
def add_channel(kanal_haqolasi: str) -> bool:
    """Majburiy kanal qo'shadi. Agar allaqachon mavjud bo'lsa, False qaytaradi."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO channels (kanal_haqolasi) VALUES (?)",
                (kanal_haqolasi,)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_channels() -> List[sqlite3.Row]:
    """Barcha majburiy kanallarni qaytaradi."""
    with get_connection() as conn:
        return conn.execute("SELECT * FROM channels").fetchall()


def delete_channel(channel_id: int) -> bool:
    """ID bo'yicha kanalni o'chiradi."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM channels WHERE id = ?", (channel_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


# ─────────────────────────────────────────────────────────────
#  ACCOUNTS CRUD
# ─────────────────────────────────────────────────────────────
def add_account(
    rasm_id: str,
    email: str,
    parol: str,
    tur: str,
    narx_ball: int = 0
) -> int:
    """
    Yangi akkaunt qo'shadi.
    Yangi akkauntning ID sini qaytaradi.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO accounts (rasm_id, email, parol, tur, narx_ball)
            VALUES (?, ?, ?, ?, ?)
            """,
            (rasm_id, email, parol, tur, narx_ball)
        )
        conn.commit()
        return cursor.lastrowid


def get_accounts_by_type(tur: str, only_available: bool = True) -> List[sqlite3.Row]:
    """
    Tur bo'yicha akkauntlarni qaytaradi.
    only_available=True bo'lsa, faqat sotilmaganlarni ko'rsatadi.
    """
    query = "SELECT * FROM accounts WHERE tur = ?"
    params = [tur]
    if only_available:
        query += " AND is_sold = 0"
    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def get_account_by_id(account_id: int) -> Optional[sqlite3.Row]:
    """ID bo'yicha akkauntni qaytaradi."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()


def mark_account_sold(account_id: int, user_id: int) -> bool:
    """Akkauntni sotilgan deb belgilaydi."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE accounts
            SET is_sold = 1, sold_to = ?
            WHERE id = ? AND is_sold = 0
            """,
            (user_id, account_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_account(account_id: int) -> bool:
    """ID bo'yicha akkauntni o'chiradi."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM accounts WHERE id = ?", (account_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_user_purchased_accounts(user_id: int) -> List[sqlite3.Row]:
    """Foydalanuvchi sotib olgan akkauntlar sonini qaytaradi."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM accounts WHERE sold_to = ?", (user_id,)
        ).fetchall()


# ─────────────────────────────────────────────────────────────
#  SETTINGS (Referal bonus)
# ─────────────────────────────────────────────────────────────
def get_referral_bonus() -> int:
    """Joriy referal bonus miqdorini qaytaradi."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'referral_bonus'"
        ).fetchone()
        return int(row["value"]) if row else 10


def set_referral_bonus(amount: int) -> None:
    """Referal bonus miqdorini yangilaydi."""
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('referral_bonus', ?)",
            (str(amount),)
        )
        conn.commit()


# ─────────────────────────────────────────────────────────────
#  STATISTIKA
# ─────────────────────────────────────────────────────────────
def get_stats() -> Dict[str, Any]:
    """Admin uchun umumiy statistikani qaytaradi."""
    with get_connection() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_accounts = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        sold_accounts = conn.execute(
            "SELECT COUNT(*) FROM accounts WHERE is_sold = 1"
        ).fetchone()[0]
        total_channels = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
        referral_bonus = get_referral_bonus()

        return {
            "total_users": total_users,
            "total_accounts": total_accounts,
            "sold_accounts": sold_accounts,
            "available_accounts": total_accounts - sold_accounts,
            "total_channels": total_channels,
            "referral_bonus": referral_bonus,
        }
