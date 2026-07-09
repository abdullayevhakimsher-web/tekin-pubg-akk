# ============================================================
#  handlers/admin/auth.py  –  Admin autentifikatsiya
# ============================================================

import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminAuthState
from keyboards.admin_kb import admin_panel_keyboard, admin_panel_remove
from keyboards.user_kb import main_menu_keyboard
import config

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("Admin11"))
async def admin_login_command(message: Message, state: FSMContext) -> None:
    """
    /Admin11 buyrug'i – admin paneliga kirish.
    Agar config.ADMIN_ID ga mos kelsa, parolsiz kiradi.
    Aks holda FSM orqali parol so'raydi.
    """
    # Agar allaqachon config dagi admin bo'lsa – parolsiz kirish
    if message.from_user.id == config.ADMIN_ID:
        await state.clear()
        # Avval foydalanuvchi klaviaturasini olib tashlaymiz
        await message.answer(
            "🔒 Kirish tasdiqlandi...",
            reply_markup=ReplyKeyboardRemove()
        )
        # Keyin admin Reply klaviaturasini ko'rsatamiz
        await message.answer(
            "👑 <b>Admin panelga xush kelibsiz!</b>\n\n"
            "Quyidagi menyudan foydalaning 👇",
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )
        return

    # Boshqa foydalanuvchilar uchun parol so'raymiz
    await state.set_state(AdminAuthState.waiting_for_password)
    await message.answer(
        "🔐 Admin panelga kirish uchun parolni kiriting:",
        reply_markup=ReplyKeyboardRemove()   # User klaviaturasini yopamiz
    )


@router.message(AdminAuthState.waiting_for_password)
async def admin_password_check(message: Message, state: FSMContext) -> None:
    """Kiritilgan parolni tekshiradi."""
    if message.text == config.ADMIN_PASSWORD:
        await state.clear()
        # Avval foydalanuvchi klaviaturasini olib tashlaymiz (ehtiyot uchun)
        await message.answer(
            "✅ <b>Parol to'g'ri! Admin panelga xush kelibsiz!</b> 👑\n\n"
            "Quyidagi menyudan foydalaning 👇",
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )
        logger.info(f"Admin panel ochildi: user_id={message.from_user.id}")
    else:
        await state.clear()
        await message.answer(
            "❌ <b>Noto'g'ri parol!</b> Kirish rad etildi.",
            reply_markup=main_menu_keyboard(),   # User klaviaturasini qayta ko'rsatamiz
            parse_mode="HTML"
        )
        logger.warning(f"Noto'g'ri parol kiritildi: user_id={message.from_user.id}")
