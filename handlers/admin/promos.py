# ============================================================
#  handlers/admin/promos.py  –  Admin Promokodlar boshqaruvi
# ============================================================

import logging
import asyncio
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states.admin_states import AdminBullDropState, AdminBallPromoState
from database import db
from keyboards.admin_kb import admin_panel_keyboard, admin_cancel_keyboard
import config

logger = logging.getLogger(__name__)
router = Router()

def _is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID

# ─────────────────────────────────────────────────────────────
#  BULLDROP PROMO QO'SHISH
# ─────────────────────────────────────────────────────────────
@router.message(F.text == "🎁 BullDrop Promo Yozish")
async def add_bulldrop_start(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    await state.set_state(AdminBullDropState.waiting_for_photo)
    await message.answer(
        "🎁 <b>BullDrop Promokod qo'shish</b>\n\n"
        "Iltimos, promokod bilan birga ketadigan rasmni yuboring:",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML"
    )

@router.message(AdminBullDropState.waiting_for_photo, F.text == "❌ Bekor qilish")
async def bulldrop_cancel_1(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())

@router.message(AdminBullDropState.waiting_for_photo, F.photo)
async def bulldrop_photo_received(message: Message, state: FSMContext) -> None:
    photo_id = message.photo[-1].file_id
    await state.update_data(rasm_id=photo_id)
    await state.set_state(AdminBullDropState.waiting_for_promos)

    await message.answer(
        "✅ Rasm qabul qilindi.\n\n"
        "Endi promokodlarni kiritishingiz mumkin.\n"
        "<i>Agar birdaniga bir nechta kiritmoqchi bo'lsangiz, vergul (,) bilan ajratib yozing yoki har birini yangi qatordan yozing.</i>",
        parse_mode="HTML"
    )

@router.message(AdminBullDropState.waiting_for_photo)
async def bulldrop_photo_invalid(message: Message) -> None:
    await message.answer("❌ Iltimos, rasm yuboring!")

@router.message(AdminBullDropState.waiting_for_promos, F.text == "❌ Bekor qilish")
async def bulldrop_cancel_2(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())

@router.message(AdminBullDropState.waiting_for_promos)
async def bulldrop_promos_received(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    rasm_id = data["rasm_id"]
    text = message.text

    # Vergul bilan yoki yangi qator bilan ajratib promokodlarni olamiz
    raw_promos = text.replace(",", "\n").split("\n")
    valid_promos = [p.strip() for p in raw_promos if p.strip()]

    if not valid_promos:
        await message.answer("❌ Hech qanday to'g'ri promokod topilmadi. Qaytadan urinib ko'ring.")
        return

    count = 0
    for p in valid_promos:
        db.add_bulldrop_promo(rasm_id, p)
        count += 1

    await state.clear()
    await message.answer(
        f"✅ <b>Muvaffaqiyatli!</b>\n\nJami {count} ta BullDrop promokod bazaga qo'shildi.",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )


# ─────────────────────────────────────────────────────────────
#  BALLI PROMO QO'SHISH VA KANALLARGA POST YUBORISH
# ─────────────────────────────────────────────────────────────
@router.message(F.text == "🎟 Balli Promo kiritish")
async def add_ball_promo_start(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    await state.set_state(AdminBallPromoState.waiting_for_promo_text)
    await message.answer(
        "🎟 <b>Balli Promokod qo'shish</b>\n\n"
        "Promokod nomini kiriting (Masalan: YANGIYIL2024):",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML"
    )

@router.message(AdminBallPromoState.waiting_for_promo_text, F.text == "❌ Bekor qilish")
async def ballpromo_cancel_1(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())

@router.message(AdminBallPromoState.waiting_for_promo_text)
async def ballpromo_text_received(message: Message, state: FSMContext) -> None:
    promo_text = message.text.strip()
    
    # Bazada bormi?
    if db.get_ball_promo(promo_text):
        await message.answer("❌ Bunday promokod bazada allaqachon mavjud! Boshqa nom tanlang:")
        return

    await state.update_data(promo_text=promo_text)
    await state.set_state(AdminBallPromoState.waiting_for_ball)
    await message.answer("✅ Promokod nomi qabul qilindi.\n\nEndi, ushbu promokod qancha <b>ball</b> berishini kiriting (faqat son):", parse_mode="HTML")


@router.message(AdminBallPromoState.waiting_for_ball, F.text == "❌ Bekor qilish")
async def ballpromo_cancel_2(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())

@router.message(AdminBallPromoState.waiting_for_ball)
async def ballpromo_ball_received(message: Message, state: FSMContext) -> None:
    try:
        ball = int(message.text.strip())
        if ball <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Iltimos, faqat musbat son kiriting.")
        return

    await state.update_data(ball=ball)
    await state.set_state(AdminBallPromoState.waiting_for_limit)
    await message.answer(f"✅ Ball ({ball}) qabul qilindi.\n\nEndi, bu promokoddan <b>necha kishi</b> foydalana olishi mumkin (limit):", parse_mode="HTML")


@router.message(AdminBallPromoState.waiting_for_limit, F.text == "❌ Bekor qilish")
async def ballpromo_cancel_3(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())

@router.message(AdminBallPromoState.waiting_for_limit)
async def ballpromo_limit_received(message: Message, bot: Bot, state: FSMContext) -> None:
    try:
        limit = int(message.text.strip())
        if limit <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Iltimos, faqat musbat son kiriting.")
        return

    data = await state.get_data()
    promo_text = data["promo_text"]
    ball = data["ball"]

    success = db.add_ball_promo(promo_text, ball, limit)
    await state.clear()

    if not success:
        await message.answer("❌ Nimadir xato ketdi (ehtimol, bu kod oldinroq qo'shib qo'yilgan).", reply_markup=admin_panel_keyboard())
        return

    await message.answer(f"✅ <b>Promokod qo'shildi!</b>\n\nEndi majburiy kanallarga habar yuborilmoqda...", reply_markup=admin_panel_keyboard(), parse_mode="HTML")

    # Kanallarga e'lon qilish
    bot_info = await bot.get_me()
    channels = db.get_channels()
    
    post_text = (
        f"🎉 <b>YANGI PROMOKOD!</b>\n\n"
        f"🎟 Promokod: <code>{promo_text}</code>\n"
        f"🎁 Promokod <b>{limit} ta</b> foydalanuvchi uchun!\n"
        f"💰 Beriladigan ball: <b>{ball} ball</b>\n\n"
        f"Shoshiling va botga o'tib promokodni ishlating 👇"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🤖 Botga O'tish", url=f"https://t.me/{bot_info.username}"))
    markup = builder.as_markup()

    if not channels:
        await message.answer("⚠️ Majburiy kanallar ro'yxati bo'sh bo'lgani uchun post hech qayerga jo'natilmadi.")
        return

    success_count = 0
    fail_count = 0

    for ch in channels:
        link = ch["kanal_haqolasi"]
        try:
            # chat_id ni username orqali topish (masalan: @username) yoki chat id dan (https link bo'lsa xato berishi mumkin, shuning uchun odatda @ bilan kiritilgan kanallarga ishlaydi)
            chat_id = link if link.startswith("@") else None
            if chat_id:
                await bot.send_message(
                    chat_id=chat_id,
                    text=post_text,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
                success_count += 1
            else:
                fail_count += 1 # Agar t.me/... formatda bo'lsa chat_id si to'g'ridan to'g'ri olib bo'lmaydi.
        except Exception as e:
            logger.error(f"Kanalga post yuborib bo'lmadi {link}: {e}")
            fail_count += 1
            
    await message.answer(f"📢 <b>Xabar yuborish yakunlandi:</b>\n✅ Muvaffaqiyatli: {success_count}\n❌ Xato: {fail_count}\n\n<i>Eslatma: Xatolik kanal formati (faqat @username orqali post jo'natish mumkin) yoki botning kanalda admin emasligi tufayli yuzaga kelishi mumkin.</i>", parse_mode="HTML")
