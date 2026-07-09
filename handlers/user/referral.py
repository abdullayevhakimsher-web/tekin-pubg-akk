# ============================================================
#  handlers/user/referral.py  –  Referal tizimi
# ============================================================

import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states.user_states import EnterBallPromoState
from database import db
from utils.helpers import check_user_subscribed, get_referral_link
from keyboards.user_kb import subscription_keyboard, referral_inline_keyboard, cancel_keyboard, main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "🎁 Ball yig'ish")
async def referral_handler(message: Message, bot: Bot) -> None:
    """Foydalanuvchiga statistikani va inline menyuni ko'rsatadi."""
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

    text = (
        f"🎁 <b>Ball yig'ish bo'limi</b>\n\n"
        f"📊 <b>Hozirgi natijalaringiz:</b>\n"
        f"💰 Joriy ballingiz: <b>{user['ball']}</b>\n"
        f"👥 Taklif qilganlar: <b>{user['taklif_qilgan_soni']}</b> kishi\n\n"
        f"Quyidagi tugmalardan birini tanlang:"
    )

    await message.answer(text=text, reply_markup=referral_inline_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "ref:get_link")
async def get_referral_link_handler(callback: CallbackQuery, bot: Bot) -> None:
    bot_info = await bot.get_me()
    referral_link = get_referral_link(bot_info.username, callback.from_user.id)
    bonus = db.get_referral_bonus()

    text = (
        f"🔗 <b>Sizning shaxsiy havolangiz:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"Do'stlaringizni taklif qiling va har bir yangi foydalanuvchi uchun "
        f"<b>{bonus} ball</b> oling!\n\n"
        f"💡 <i>Havolani nusxalab do'stlaringizga yuboring!</i>"
    )
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "ref:enter_promo")
async def enter_promo_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(EnterBallPromoState.waiting_for_promo)
    await callback.message.answer(
        "🎫 <b>Promokodni kiriting:</b>\n(Bekor qilish uchun pastdagi tugmani bosing)",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(EnterBallPromoState.waiting_for_promo)
async def process_ball_promo(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())
        return

    promo_text = message.text.strip()
    promo = db.get_ball_promo(promo_text)

    if not promo:
        await message.answer("❌ Bunday promokod mavjud emas yoki xato kiritdingiz.", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    if promo["used_count"] >= promo["limit_count"]:
        await message.answer("❌ Promokod muddati tugagan (limit to'lgan).", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    if db.has_user_claimed_ball_promo(message.from_user.id, promo["id"]):
        await message.answer("❌ Siz bu promokodni allaqachon ishlatgansiz!", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    # Promokodni ishlatish
    db.record_ball_promo_claim(message.from_user.id, promo["id"])
    db.update_user_balls(message.from_user.id, promo["ball"])

    await message.answer(
        f"🎉 <b>Tabriklaymiz!</b>\nSiz promokod orqali <b>{promo['ball']} ball</b> oldingiz!",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
    await state.clear()
