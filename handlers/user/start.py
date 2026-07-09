# ============================================================
#  handlers/user/start.py  –  /start buyrug'i va obuna tekshirish
# ============================================================

import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database import db
from keyboards.user_kb import main_menu_keyboard, subscription_keyboard
from utils.helpers import check_user_subscribed, get_referral_link
import config

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    /start buyrug'ini qayta ishlaydi.
    Referal parametrini tekshiradi, foydalanuvchini ro'yxatdan o'tkazadi,
    va majburiy obunani tekshiradi.
    """
    await state.clear()  # Avvalgi FSM holatini tozalash

    user_id = message.from_user.id
    full_name = message.from_user.full_name

    # --- Referal parametrini tahlil qilish ---
    referral_by = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1][4:])
            if referrer_id != user_id:  # O'zini taklif qilolmaydi
                referral_by = referrer_id
        except ValueError:
            pass

    # --- Foydalanuvchini bazaga qo'shish ---
    is_new = db.add_user(user_id=user_id, ism=full_name, referral_by=referral_by)

    if is_new and referral_by:
        # Taklif qilgan odamga bonus berish
        bonus = db.get_referral_bonus()
        referrer = db.get_user(referral_by)
        if referrer:
            db.update_user_balls(referral_by, bonus)
            db.increment_referral_count(referral_by)
            try:
                await bot.send_message(
                    chat_id=referral_by,
                    text=(
                        f"🎉 Tabriklaymiz! Siz taklif qilgan odam botga qo'shildi!\n"
                        f"💰 Hisobingizga <b>+{bonus} ball</b> qo'shildi!"
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass

    # --- Majburiy obunani tekshirish ---
    channels = db.get_channels()

    if channels:
        is_subscribed = await check_user_subscribed(bot, user_id, channels)
        if not is_subscribed:
            await message.answer(
                text=(
                    "👋 <b>Xush kelibsiz!</b>\n\n"
                    "🔒 Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:\n"
                    "A'zo bo'lgandan so'ng <b>\"✅ A'zo bo'ldim, tekshir!\"</b> tugmasini bosing."
                ),
                reply_markup=subscription_keyboard(channels),
                parse_mode="HTML"
            )
            return

    # --- Asosiy menyuni ko'rsatish ---
    await _show_main_menu(message, is_new)


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot) -> None:
    """
    Foydalanuvchi "A'zo bo'ldim" tugmasini bosganda obunani tekshiradi.
    """
    user_id = callback.from_user.id
    channels = db.get_channels()

    is_subscribed = await check_user_subscribed(bot, user_id, channels)

    if not is_subscribed:
        await callback.answer(
            "❌ Siz hali ham barcha kanallarga a'zo emassiz! Iltimos, barchasiga a'zo bo'ling.",
            show_alert=True
        )
        return

    # Obunadan o'tdi – eski xabarni o'chirib, asosiy menyuni chiqaramiz
    await callback.message.delete()

    user = db.get_user(user_id)
    ism = user["ism"] if user else callback.from_user.full_name

    await callback.message.answer(
        text=(
            f"✅ <b>Obuna tasdiqlandi!</b>\n\n"
            f"Salom, <b>{ism}</b>! 👋\n"
            f"Botga xush kelibsiz! Quyidagi menyudan foydalaning:"
        ),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


async def _show_main_menu(message: Message, is_new: bool) -> None:
    """Asosiy menyuni ko'rsatadigan yordamchi funksiya."""
    ism = message.from_user.full_name
    if is_new:
        text = (
            f"🎉 <b>Xush kelibsiz, {ism}!</b>\n\n"
            f"Bot orqali quyidagi imkoniyatlardan foydalanishingiz mumkin:\n"
            f"• Ball yig'ish va do'stlarni taklif qilish\n"
            f"• Tekin PUBG akkaunti olish\n"
            f"• Ballga Google akkauntlar xarid qilish\n\n"
            f"Pastdagi menyudan boshlang 👇"
        )
    else:
        text = (
            f"👋 <b>Qaytib kelganingizdan xursandmiz, {ism}!</b>\n\n"
            f"Menyudan foydalaning 👇"
        )

    await message.answer(
        text=text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
