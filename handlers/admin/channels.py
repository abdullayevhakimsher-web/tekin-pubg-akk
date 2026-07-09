# ============================================================
#  handlers/admin/channels.py  –  Kanallarni boshqarish
#  Admin ReplyKeyboard tugmasi "📢 Kanallarni boshqarish" orqali ishlaydi
# ============================================================

import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminAddChannelState
from database import db
from keyboards.admin_kb import (
    admin_panel_keyboard,
    channels_management_keyboard,
    admin_cancel_keyboard,
)
import config

logger = logging.getLogger(__name__)
router = Router()


def _is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshiradi."""
    return user_id == config.ADMIN_ID


# ──────────────────────────────────────────────────────
#  ReplyKeyboard tugmasi: "📢 Kanallarni boshqarish"
# ──────────────────────────────────────────────────────
@router.message(F.text == "📢 Kanallarni boshqarish")
async def channels_panel(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return

    channels = db.get_channels()
    count = len(channels)

    await message.answer(
        text=(
            f"📢 <b>Kanallarni boshqarish</b>\n\n"
            f"Joriy majburiy kanallar soni: <b>{count}</b>\n\n"
            f"{'📋 Kanallar ro\'yxati:' if channels else '❌ Kanallar yo\'q.'}"
            + (
                "\n" + "\n".join(
                    f"  {i + 1}. <code>{ch['kanal_haqolasi']}</code>"
                    for i, ch in enumerate(channels)
                )
                if channels else ""
            )
        ),
        reply_markup=channels_management_keyboard(channels),
        parse_mode="HTML"
    )


# ──────────────────────────────────────────────────────
#  Inline: Kanal qo'shish boshlash
# ──────────────────────────────────────────────────────
@router.callback_query(F.data == "admin:add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminAddChannelState.waiting_for_channel)
    await callback.message.answer(
        "📢 <b>Yangi kanal havolasini yuboring:</b>\n\n"
        "📌 Format: <code>@kanalusername</code>\n"
        "yoki <code>https://t.me/kanalusername</code>\n\n"
        "❌ Bekor qilish uchun tugmani bosing.",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ──────────────────────────────────────────────────────
#  FSM: Kanal havolasini qabul qilish
# ──────────────────────────────────────────────────────
@router.message(AdminAddChannelState.waiting_for_channel)
async def add_channel_receive(message: Message, state: FSMContext) -> None:
    """Kanal havolasini qabul qilib bazaga qo'shadi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi.",
            reply_markup=admin_panel_keyboard()
        )
        return

    channel_link = message.text.strip()

    # Minimal validatsiya
    if not (channel_link.startswith("@") or "t.me" in channel_link):
        await message.answer(
            "❌ Noto'g'ri format!\n"
            "@username yoki https://t.me/username ko'rinishida yuboring."
        )
        return

    success = db.add_channel(channel_link)
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>Kanal qo'shildi:</b> <code>{channel_link}</code>",
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"⚠️ Bu kanal allaqachon mavjud: <code>{channel_link}</code>",
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )


# ──────────────────────────────────────────────────────
#  Inline: Kanalni o'chirish
# ──────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("admin:del_channel:"))
async def delete_channel(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    channel_id = int(callback.data.split(":")[2])
    success = db.delete_channel(channel_id)

    if success:
        await callback.answer("✅ Kanal o'chirildi!", show_alert=True)
    else:
        await callback.answer("❌ Kanal topilmadi.", show_alert=True)

    # Ro'yxatni yangilash
    channels = db.get_channels()
    await callback.message.edit_text(
        text=(
            f"📢 <b>Kanallarni boshqarish</b>\n\n"
            f"Joriy kanallar: <b>{len(channels)}</b>"
            + (
                "\n" + "\n".join(
                    f"  {i + 1}. <code>{ch['kanal_haqolasi']}</code>"
                    for i, ch in enumerate(channels)
                )
                if channels else "\n\n❌ Kanallar yo'q."
            )
        ),
        reply_markup=channels_management_keyboard(channels),
        parse_mode="HTML"
    )


# ──────────────────────────────────────────────────────
#  Admin: Paneldan chiqish
# ──────────────────────────────────────────────────────
@router.message(F.text == "🚪 Paneldan chiqish")
async def exit_admin_panel(message: Message, state: FSMContext) -> None:
    """Admin klaviaturasini yopib, user menyusini ko'rsatadi."""
    if not _is_admin(message.from_user.id):
        return

    await state.clear()

    from keyboards.user_kb import main_menu_keyboard
    await message.answer(
        "👋 Admin paneldan chiqdingiz.\n"
        "Endi oddiy foydalanuvchi sifatida ishlaysiz.",
        reply_markup=main_menu_keyboard()
    )
