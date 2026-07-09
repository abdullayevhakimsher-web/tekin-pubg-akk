# ============================================================
#  handlers/user/support.py  –  Adminga murojat (FSM)
# ============================================================

import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from states.user_states import SupportState
from database import db
from keyboards.user_kb import main_menu_keyboard, subscription_keyboard, cancel_keyboard
from utils.helpers import check_user_subscribed
import config

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "👨‍💻 Adminga murojat")
async def support_start(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Adminga murojat boshlanadi.
    Foydalanuvchidan xabar matnini kutadi.
    """
    # Obuna tekshirish
    channels = db.get_channels()
    if channels:
        is_sub = await check_user_subscribed(bot, message.from_user.id, channels)
        if not is_sub:
            await message.answer(
                "🔒 Botdan foydalanish uchun avvalo kanallarga a'zo bo'ling!",
                reply_markup=subscription_keyboard(channels)
            )
            return

    await state.set_state(SupportState.waiting_for_message)
    await message.answer(
        text=(
            "👨‍💻 <b>Adminga murojat</b>\n\n"
            "Xabaringizni yozing. Admin imkon qadar tez javob beradi.\n\n"
            "❌ Bekor qilish uchun <b>\"❌ Bekor qilish\"</b> tugmasini bosing."
        ),
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(SupportState.waiting_for_message, F.text == "❌ Bekor qilish")
async def support_cancel(message: Message, state: FSMContext) -> None:
    """Murojatni bekor qiladi."""
    await state.clear()
    await message.answer(
        "❌ Murojat bekor qilindi.",
        reply_markup=main_menu_keyboard()
    )


@router.message(SupportState.waiting_for_message)
async def support_send_message(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Foydalanuvchi xabarini qabul qilib, adminga forward qiladi.
    """
    await state.clear()

    user_id = message.from_user.id
    user = db.get_user(user_id)
    user_name = user["ism"] if user else message.from_user.full_name

    # Admin uchun xabar formatini tayyorlaymiz
    admin_text = (
        f"📩 <b>Yangi murojat keldi!</b>\n\n"
        f"👤 Foydalanuvchi: <b>{user_name}</b>\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"💬 Xabar:\n\n"
        f"<i>{message.text or '[Matn yoq]'}</i>"
    )

    try:
        # Xabarni adminga yuborish
        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text=admin_text,
            parse_mode="HTML"
        )

        # Agar xabar matn bo'lmasa (foto, fayl va h.k.), original xabarni ham forward qilamiz
        if not message.text:
            await message.forward(chat_id=config.ADMIN_ID)

        await message.answer(
            text=(
                "✅ <b>Xabaringiz adminga yuborildi!</b>\n\n"
                "Admin tez orada javob beradi. Sabr qiling 🙏"
            ),
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Admin ga xabar yuborishda xato: {e}")
        await message.answer(
            "❌ Xabar yuborishda xatolik yuz berdi. Keyinroq urinib ko'ring.",
            reply_markup=main_menu_keyboard()
        )
