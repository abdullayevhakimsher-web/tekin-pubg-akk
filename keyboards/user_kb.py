# ============================================================
#  keyboards/user_kb.py  –  Foydalanuvchi klaviaturalari
# ============================================================

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
import sqlite3


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    8 ta tugmali asosiy menyu klaviaturasi.
    Foydalanuvchi obunadan o'tgach ko'rsatiladi.
    """
    buttons = [
        [
            KeyboardButton(text="🎁 BullDrop Promokod Olish"),
        ],
        [
            KeyboardButton(text="🎁 Ball yig'ish"),
            KeyboardButton(text="🆓 Tekin pubg akk olish"),
        ],
        [
            KeyboardButton(text="💎 Ballga haqiqiy Google akk olish"),
            KeyboardButton(text="🛍 Balli akkları ko'rish"),
        ],
        [
            KeyboardButton(text="👤 Hisobim"),
            KeyboardButton(text="👨‍💻 Adminga murojat"),
        ],
        [
            KeyboardButton(text="📜 Qoidalar"),
            KeyboardButton(text="📖 Qo'llanma"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Menyu bandini tanlang...",
    )


def subscription_keyboard(channels: List[sqlite3.Row]) -> InlineKeyboardMarkup:
    """
    Majburiy obuna uchun inline klaviatura.
    Har bir kanal uchun alohida tugma + tekshirish tugmasi.
    """
    builder = InlineKeyboardBuilder()
    for ch in channels:
        link = ch["kanal_haqolasi"]
        # Agar @username bo'lsa, t.me havolasiga aylantiramiz
        if link.startswith("@"):
            url = f"https://t.me/{link[1:]}"
        else:
            url = link
        builder.row(
            InlineKeyboardButton(
                text=f"📢 {link}",
                url=url
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="✅ A'zo bo'ldim, tekshir!",
            callback_data="check_subscription"
        )
    )
    return builder.as_markup()


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmali klaviatura (FSM uchun)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
    )


def google_accounts_keyboard(accounts: List[sqlite3.Row]) -> InlineKeyboardMarkup:
    """Sotib olish uchun Google akkauntlar ro'yxati."""
    builder = InlineKeyboardBuilder()
    for acc in accounts:
        builder.row(
            InlineKeyboardButton(
                text=f"💎 #{acc['id']} – {acc['narx_ball']} ball",
                callback_data=f"buy_google:{acc['id']}"
            )
        )
    return builder.as_markup()


def balli_accounts_keyboard(accounts: List[sqlite3.Row]) -> InlineKeyboardMarkup:
    """Balli akkları sotib olish tugmalari."""
    builder = InlineKeyboardBuilder()
    for acc in accounts:
        builder.row(
            InlineKeyboardButton(
                text=f"🛍 #{acc['id']} – {acc['narx_ball']} ball",
                callback_data=f"buy_balli:{acc['id']}"
            )
        )
    return builder.as_markup()


def confirm_buy_keyboard(account_id: int, prefix: str) -> InlineKeyboardMarkup:
    """Akkauntni sotib olishni tasdiqlash klaviaturasi."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Ha, sotib olaman",
            callback_data=f"confirm_buy:{prefix}:{account_id}"
        ),
        InlineKeyboardButton(
            text="❌ Bekor",
            callback_data="cancel_buy"
        )
    )
    return builder.as_markup()

def referral_inline_keyboard() -> InlineKeyboardMarkup:
    """Ball yig'ish bosilganda chiqadigan inline tugmalar."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔗 Link olish", callback_data="ref:get_link"),
        InlineKeyboardButton(text="🎫 Promokod yozish", callback_data="ref:enter_promo")
    )
    return builder.as_markup()

def balli_accounts_slider_keyboard(account_id: int, current_index: int, total_count: int) -> InlineKeyboardMarkup:
    """Balli akkauntlarni carousel/slider uslubida ko'rsatish."""
    builder = InlineKeyboardBuilder()
    
    # 1-qator: Sotib olish
    builder.row(
        InlineKeyboardButton(
            text="✅ Sotib olish",
            callback_data=f"buy_balli:{account_id}"
        )
    )
    # 2-qator: Navigatsiya
    nav_buttons = []
    
    next_index = (current_index + 1) % total_count
    
    nav_buttons.append(
        InlineKeyboardButton(
            text="➡️ Keyingisi",
            callback_data=f"slider:balli:{next_index}"
        )
    )
    
    builder.row(*nav_buttons)
    
    return builder.as_markup()
