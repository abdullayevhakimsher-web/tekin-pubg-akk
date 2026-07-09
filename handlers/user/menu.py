# ============================================================
#  handlers/user/menu.py  –  Asosiy menyu handlerlari
#  ("Hisobim", "Qoidalar", "Qo'llanma")
# ============================================================

import logging
from aiogram import Router, Bot, F
from aiogram.types import Message

from database import db
from keyboards.user_kb import main_menu_keyboard, subscription_keyboard
from utils.helpers import check_user_subscribed, format_user_info
import config

logger = logging.getLogger(__name__)
router = Router()


# ──────────────────────────────────────────────────────
#  Obuna tekshiruvi middleware vazifasini bajaruvchi yordamchi
# ──────────────────────────────────────────────────────
async def _require_subscription(message: Message, bot: Bot) -> bool:
    """
    Foydalanuvchini kanallarga a'zo bo'lganini tekshiradi.
    A'zo bo'lmagan bo'lsa, xabar yuborib False qaytaradi.
    """
    channels = db.get_channels()
    if not channels:
        return True

    is_sub = await check_user_subscribed(bot, message.from_user.id, channels)
    if not is_sub:
        await message.answer(
            "🔒 Botdan foydalanish uchun avvalo kanallarga a'zo bo'ling!",
            reply_markup=subscription_keyboard(channels)
        )
        return False
    return True


# ──────────────────────────────────────────────────────
#  👤 Hisobim
# ──────────────────────────────────────────────────────
@router.message(F.text == "👤 Hisobim")
async def my_profile(message: Message, bot: Bot) -> None:
    if not await _require_subscription(message, bot):
        return

    user_id = message.from_user.id
    user = db.get_user(user_id)

    if not user:
        await message.answer(
            "❗ Sizning ma'lumotlaringiz topilmadi. /start ni bosing.",
            reply_markup=main_menu_keyboard()
        )
        return

    await message.answer(
        text=format_user_info(user),
        parse_mode="HTML"
    )


# ──────────────────────────────────────────────────────
#  📜 Qoidalar
# ──────────────────────────────────────────────────────
@router.message(F.text == "📜 Qoidalar")
async def show_rules(message: Message, bot: Bot) -> None:
    if not await _require_subscription(message, bot):
        return

    await message.answer(
        text=config.RULES_TEXT,
        parse_mode="HTML"
    )


# ──────────────────────────────────────────────────────
#  📖 Qo'llanma
# ──────────────────────────────────────────────────────
@router.message(F.text == "📖 Qo'llanma")
async def show_guide(message: Message, bot: Bot) -> None:
    if not await _require_subscription(message, bot):
        return

    await message.answer(
        text=config.GUIDE_TEXT,
        parse_mode="HTML"
    )
