# ============================================================
#  handlers/admin/referral.py  –  Referal bonus boshqarish
# ============================================================

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminReferralState
from database import db
from keyboards.admin_kb import admin_panel_keyboard, admin_cancel_keyboard
import config

logger = logging.getLogger(__name__)
router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


# ──────────────────────────────────────────────────────
#  ReplyKeyboard tugmasi: "🎁 Referal bonusni o'zgartirish"
# ──────────────────────────────────────────────────────
@router.message(F.text == "🎁 Referal bonusni o'zgartirish")
async def referral_panel(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    current_bonus = db.get_referral_bonus()
    await state.set_state(AdminReferralState.waiting_for_amount)

    await message.answer(
        text=(
            f"🎁 <b>Referal Bonus Sozlamalari</b>\n\n"
            f"Joriy bonus miqdori: <b>{current_bonus} ball</b>\n\n"
            f"Yangi miqdorni kiriting (faqat musbat son):\n"
            f"<i>Masalan: 5, 10, 20, 50</i>\n\n"
            f"Bekor qilish uchun pastdagi tugmani bosing."
        ),
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML"
    )


# ──────────────────────────────────────────────────────
#  FSM: Referal miqdorni qabul qilish
# ──────────────────────────────────────────────────────
@router.message(AdminReferralState.waiting_for_amount)
async def referral_set_amount(message: Message, state: FSMContext) -> None:
    """Yangi referal bonus miqdorini qabul qilib saqlaydi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())
        return

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Iltimos, musbat butun son kiriting (masalan: 10)")
        return

    db.set_referral_bonus(amount)
    await state.clear()

    await message.answer(
        text=(
            f"✅ <b>Referal bonus yangilandi!</b>\n\n"
            f"Yangi miqdor: <b>{amount} ball</b>\n\n"
            f"Endi har bir yangi taklif uchun {amount} ball beriladi."
        ),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    logger.info(f"Referal bonus o'zgartirildi: {amount} ball")
