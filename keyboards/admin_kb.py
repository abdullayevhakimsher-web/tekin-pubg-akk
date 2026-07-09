# ============================================================
#  keyboards/admin_kb.py  –  Admin klaviaturalari
# ============================================================

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
import sqlite3


# ──────────────────────────────────────────────────────────────
#  Asosiy admin panel – ReplyKeyboard (pastki klaviatura)
# ──────────────────────────────────────────────────────────────
def admin_panel_keyboard() -> ReplyKeyboardMarkup:
    """
    Admin panelning asosiy ReplyKeyboard klaviaturasi.
    Foydalanuvchi klaviaturasini o'rniga chiqadi.
    """
    buttons = [
        [
            KeyboardButton(text="📢 Kanallarni boshqarish"),
            KeyboardButton(text="➕ Akkaunt qo'shish"),
        ],
        [
            KeyboardButton(text="🎁 BullDrop Promo Yozish"),
            KeyboardButton(text="🎟 Balli Promo kiritish"),
        ],
        [
            KeyboardButton(text="🎁 Referal bonusni o'zgartirish"),
            KeyboardButton(text="📊 Statistika"),
        ],
        [
            KeyboardButton(text="📣 Hammaga xabar yuborish"),
            KeyboardButton(text="🚪 Paneldan chiqish"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Admin panel...",
    )


def admin_panel_remove() -> ReplyKeyboardRemove:
    """Admin klaviaturasini yopish uchun."""
    return ReplyKeyboardRemove()


# ──────────────────────────────────────────────────────────────
#  Kanallar boshqaruvi – Inline (submenu)
# ──────────────────────────────────────────────────────────────
def channels_management_keyboard(channels: List[sqlite3.Row]) -> InlineKeyboardMarkup:
    """Kanallar ro'yxati + qo'shish va o'chirish tugmalari (inline)."""
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.row(
            InlineKeyboardButton(
                text=f"🗑 {ch['kanal_haqolasi']} ni o'chirish",
                callback_data=f"admin:del_channel:{ch['id']}"
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="➕ Yangi kanal qo'shish",
            callback_data="admin:add_channel"
        )
    )
    return builder.as_markup()


# ──────────────────────────────────────────────────────────────
#  Akkaunt turi tanlash – Inline (submenu)
# ──────────────────────────────────────────────────────────────
def account_type_keyboard() -> InlineKeyboardMarkup:
    """Akkaunt turini tanlash inline klaviaturasi."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🆓 Tekin PUBG akk",
            callback_data="acc_type:tekin_pubg"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💎 Pullik Google akk",
            callback_data="acc_type:pullik_google"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🛍 Balli akk",
            callback_data="acc_type:balli_akk"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Bekor qilish",
            callback_data="admin:cancel_account"
        )
    )
    return builder.as_markup()


# ──────────────────────────────────────────────────────────────
#  Kanal qo'shish klaviaturasi – "Bekor" tugmasi (Reply)
# ──────────────────────────────────────────────────────────────
def admin_cancel_keyboard() -> ReplyKeyboardMarkup:
    """FSM jarayonida bekor qilish uchun (admin uchun)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
    )
