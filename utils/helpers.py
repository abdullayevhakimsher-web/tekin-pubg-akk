# ============================================================
#  utils/helpers.py  –  Yordamchi funksiyalar
# ============================================================

import logging
from aiogram import Bot
from aiogram.types import ChatMember
from typing import List
import sqlite3

logger = logging.getLogger(__name__)


async def check_user_subscribed(bot: Bot, user_id: int, channels: List[sqlite3.Row]) -> bool:
    """
    Foydalanuvchini barcha majburiy kanallarga a'zo bo'lganini tekshiradi.
    Agar bitta kanaldan ham a'zo bo'lmasa, False qaytaradi.
    """
    if not channels:
        return True  # Kanal yo'q bo'lsa, tekshirishning hojati yo'q

    for channel in channels:
        link = channel["kanal_haqolasi"]
        try:
            # @username yoki -100xxx formatida bo'lishi kerak
            member: ChatMember = await bot.get_chat_member(chat_id=link, user_id=user_id)
            if member.status in ("left", "kicked", "banned"):
                return False
        except Exception as e:
            logger.warning(f"Kanal tekshirishda xato ({link}): {e}")
            # Agar kanal topilmasa yoki botga ruxsat yo'q bo'lsa, o'tkazib yuboramiz
            continue

    return True


def format_user_info(user: sqlite3.Row) -> str:
    """Foydalanuvchi ma'lumotlarini chiroyli formatda qaytaradi."""
    return (
        f"👤 <b>Hisobim</b>\n\n"
        f"🆔 ID: <code>{user['id']}</code>\n"
        f"📝 Ism: <b>{user['ism']}</b>\n"
        f"💰 Ball: <b>{user['ball']}</b> 🏆\n"
        f"👥 Taklif qilganlar: <b>{user['taklif_qilgan_soni']}</b> kishi\n"
    )


def format_account_info(account: sqlite3.Row) -> str:
    """Akkaunt ma'lumotlarini foydalanuvchiga ko'rsatish uchun formatlaydi."""
    return (
        f"✅ <b>Akkaunt ma'lumotlari</b>\n\n"
        f"📧 Email: <code>{account['email']}</code>\n"
        f"🔐 Parol: <code>{account['parol']}</code>\n\n"
        f"⚠️ Ushbu ma'lumotlarni saqlang va hech kimga bermang!"
    )


def get_referral_link(bot_username: str, user_id: int) -> str:
    """Foydalanuvchi uchun unikal referal havolasini yaratadi."""
    return f"https://t.me/{bot_username}?start=ref_{user_id}"
