# ============================================================
#  handlers/user/referral.py  –  Referal tizimi
# ============================================================

import logging
from aiogram import Router, Bot, F
from aiogram.types import Message

from database import db
from utils.helpers import check_user_subscribed, get_referral_link
from keyboards.user_kb import subscription_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🎁 Ball yig'ish")
async def referral_handler(message: Message, bot: Bot) -> None:
    """
    Foydalanuvchiga uning shaxsiy referal havolasini ko'rsatadi.
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

    user_id = message.from_user.id
    user = db.get_user(user_id)

    if not user:
        await message.answer("❗ Avval /start buyrug'ini bosing!")
        return

    bot_info = await bot.get_me()
    referral_link = get_referral_link(bot_info.username, user_id)
    bonus = db.get_referral_bonus()

    text = (
        f"🎁 <b>Referal tizimi</b>\n\n"
        f"Do'stlaringizni taklif qiling va har bir yangi foydalanuvchi uchun "
        f"<b>{bonus} ball</b> oling!\n\n"
        f"🔗 <b>Sizning shaxsiy havolangiz:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 <b>Hozirgi natijalaringiz:</b>\n"
        f"💰 Joriy ballingiz: <b>{user['ball']}</b>\n"
        f"👥 Taklif qilganlar: <b>{user['taklif_qilgan_soni']}</b> kishi\n\n"
        f"💡 <i>Havolani nusxalab do'stlaringizga yuboring!</i>"
    )

    await message.answer(text=text, parse_mode="HTML")
