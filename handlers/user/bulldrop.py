# ============================================================
#  handlers/user/bulldrop.py  –  BullDrop Promokod olish
# ============================================================

import logging
from datetime import datetime, timedelta
from aiogram import Router, Bot, F
from aiogram.types import Message
from database import db
from utils.helpers import check_user_subscribed
from keyboards.user_kb import subscription_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "🎁 BullDrop Promokod Olish")
async def get_bulldrop_handler(message: Message, bot: Bot) -> None:
    """Foydalanuvchiga kunlik 1 ta BullDrop promokod beradi."""
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
    last_claim = db.get_last_bulldrop_claim_time(user_id)

    # 24 soat limit tekshiruvi
    if last_claim:
        last_time = datetime.strptime(last_claim, "%Y-%m-%d %H:%M:%S")
        if datetime.now() < last_time + timedelta(hours=24):
            remaining = (last_time + timedelta(hours=24)) - datetime.now()
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            await message.answer(
                f"⏳ <b>Limit!</b>\n\nSiz kunlik BullDrop promokodingizni olib bo'ldingiz.\n"
                f"Keyingisini olish uchun yana <b>{hours} soat, {minutes} daqiqa</b> kuting.",
                parse_mode="HTML"
            )
            return

    # Foydalanuvchi hali olmagan birinchi promoni bazadan qidiramiz
    promo = db.get_available_bulldrop_for_user(user_id)
    if not promo:
        await message.answer(
            "😔 <b>Kechirasiz, barcha BullDrop promokodlari tugagan!</b>\n"
            "Admin yangi promokodlarni kiritishini kuting.",
            parse_mode="HTML"
        )
        return

    # Promokod berildi
    db.record_bulldrop_claim(user_id, promo["id"])

    await message.answer_photo(
        photo=promo["rasm_id"],
        caption=(
            f"🎁 <b>Tabriklaymiz, sizning bugungi BullDrop promokodingiz!</b>\n\n"
            f"🎫 Promokod: <code>{promo['promo_text']}</code>"
        ),
        parse_mode="HTML"
    )
