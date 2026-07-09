# ============================================================
#  handlers/admin/accounts.py  –  Akkaunt qo'shish (ko'p bosqichli FSM)
#  Admin ReplyKeyboard tugmasi "➕ Akkaunt qo'shish" orqali ishlaydi
# ============================================================

import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminAddAccountState
from database import db
from keyboards.admin_kb import (
    admin_panel_keyboard,
    account_type_keyboard,
    admin_cancel_keyboard,
)
import config

logger = logging.getLogger(__name__)
router = Router()

# Tur nomlarini o'zbek tiliga tarjima
TYPE_LABELS = {
    "tekin_pubg":    "🆓 Tekin PUBG",
    "pullik_google": "💎 Pullik Google",
    "balli_akk":     "🛍 Balli Akk",
}


def _is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


# ──────────────────────────────────────────────────────
#  ReplyKeyboard tugmasi: "➕ Akkaunt qo'shish"
# ──────────────────────────────────────────────────────
@router.message(F.text == "➕ Akkaunt qo'shish")
async def add_account_start_text(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    await state.set_state(AdminAddAccountState.choosing_type)
    await message.answer(
        text="➕ <b>Akkaunt qo'shish</b>\n\nAkkaunt turini tanlang:",
        reply_markup=account_type_keyboard(),
        parse_mode="HTML"
    )


# ──────────────────────────────────────────────────────
#  Inline: Tur saqlash, rasm so'rash
# ──────────────────────────────────────────────────────
@router.callback_query(
    AdminAddAccountState.choosing_type,
    F.data.startswith("acc_type:")
)
async def account_type_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    acc_type = callback.data.split(":")[1]
    await state.update_data(acc_type=acc_type)
    await state.set_state(AdminAddAccountState.waiting_photo)

    label = TYPE_LABELS.get(acc_type, acc_type)
    await callback.message.edit_text(
        text=(
            f"✅ Tur tanlandi: <b>{label}</b>\n\n"
            f"📷 Endi akkаunt rasmini yuboring:\n"
            f"<i>(Screenshot yoki istalgan rasm)</i>"
        ),
        parse_mode="HTML"
    )
    # FSM davomida bekor qilish tugmasi
    await callback.message.answer(
        "❌ Bekor qilish uchun pastdagi tugmani bosing.",
        reply_markup=admin_cancel_keyboard()
    )
    await callback.answer()


# ──────────────────────────────────────────────────────
#  Inline: Akkaunt qo'shishni bekor qilish
# ──────────────────────────────────────────────────────
@router.callback_query(F.data == "admin:cancel_account")
async def cancel_add_account(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        text="❌ Bekor qilindi.",
        parse_mode="HTML"
    )
    await callback.message.answer(
        "👑 <b>Admin Panel</b>",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# ──────────────────────────────────────────────────────
#  FSM: Rasmni qabul qilish → email so'rash
# ──────────────────────────────────────────────────────
@router.message(AdminAddAccountState.waiting_photo, F.text == "❌ Bekor qilish")
async def cancel_from_photo(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())


@router.message(AdminAddAccountState.waiting_photo, F.photo)
async def account_photo_received(message: Message, state: FSMContext) -> None:
    photo_id = message.photo[-1].file_id
    await state.update_data(rasm_id=photo_id)
    await state.set_state(AdminAddAccountState.waiting_email)

    await message.answer(
        "✅ Rasm qabul qilindi!\n\n"
        "📧 Endi akkaunt emailini yuboring:",
        reply_markup=admin_cancel_keyboard()
    )


@router.message(AdminAddAccountState.waiting_photo)
async def account_photo_invalid(message: Message) -> None:
    await message.answer("❌ Iltimos, rasm yuboring (screenshot yoki foto).")


# ──────────────────────────────────────────────────────
#  FSM: Email qabul qilish → parol so'rash
# ──────────────────────────────────────────────────────
@router.message(AdminAddAccountState.waiting_email, F.text == "❌ Bekor qilish")
async def cancel_from_email(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())


@router.message(AdminAddAccountState.waiting_email)
async def account_email_received(message: Message, state: FSMContext) -> None:
    email = message.text.strip()
    if "@" not in email:
        await message.answer("❌ To'g'ri email kiriting (masalan: user@gmail.com)")
        return

    await state.update_data(email=email)
    await state.set_state(AdminAddAccountState.waiting_password)

    await message.answer(
        f"✅ Email saqlandi: <code>{email}</code>\n\n"
        f"🔐 Endi akkaunt parolini yuboring:",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML"
    )


# ──────────────────────────────────────────────────────
#  FSM: Parol qabul qilish
# ──────────────────────────────────────────────────────
@router.message(AdminAddAccountState.waiting_password, F.text == "❌ Bekor qilish")
async def cancel_from_password(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())


@router.message(AdminAddAccountState.waiting_password)
async def account_password_received(message: Message, state: FSMContext) -> None:
    parol = message.text.strip()
    await state.update_data(parol=parol)

    data = await state.get_data()
    acc_type = data.get("acc_type")

    if acc_type == "tekin_pubg":
        # Tekin uchun narx = 0
        await _save_account(message, state, narx_ball=0)
    else:
        await state.set_state(AdminAddAccountState.waiting_price)
        await message.answer(
            f"✅ Parol saqlandi!\n\n"
            f"💰 Endi akkаunt narxini (ball miqdorida) yuboring:\n"
            f"<i>Faqat raqam kiriting, masalan: 50</i>",
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML"
        )


# ──────────────────────────────────────────────────────
#  FSM: Narx qabul qilish va bazaga yozish
# ──────────────────────────────────────────────────────
@router.message(AdminAddAccountState.waiting_price, F.text == "❌ Bekor qilish")
async def cancel_from_price(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_keyboard())


@router.message(AdminAddAccountState.waiting_price)
async def account_price_received(message: Message, state: FSMContext) -> None:
    try:
        narx_ball = int(message.text.strip())
        if narx_ball <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Iltimos, musbat son kiriting (masalan: 50, 100, 200)")
        return

    await _save_account(message, state, narx_ball=narx_ball)


# ──────────────────────────────────────────────────────
#  Yordamchi: Bazaga saqlash
# ──────────────────────────────────────────────────────
async def _save_account(message: Message, state: FSMContext, narx_ball: int) -> None:
    """Yig'ilgan ma'lumotlarni bazaga saqlaydi."""
    data = await state.get_data()
    await state.clear()

    acc_type  = data["acc_type"]
    rasm_id   = data["rasm_id"]
    email     = data["email"]
    parol     = data["parol"]

    new_id = db.add_account(
        rasm_id=rasm_id,
        email=email,
        parol=parol,
        tur=acc_type,
        narx_ball=narx_ball
    )

    label = TYPE_LABELS.get(acc_type, acc_type)

    await message.answer(
        text=(
            f"✅ <b>Akkaunt muvaffaqiyatli qo'shildi!</b>\n\n"
            f"🆔 ID: <code>{new_id}</code>\n"
            f"📂 Tur: <b>{label}</b>\n"
            f"📧 Email: <code>{email}</code>\n"
            f"🔐 Parol: <code>{parol}</code>\n"
            f"💰 Narx: <b>{narx_ball} ball</b>"
        ),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    logger.info(f"Yangi akkaunt qo'shildi: ID={new_id}, tur={acc_type}")
