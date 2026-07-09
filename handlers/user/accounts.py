# ============================================================
#  handlers/user/accounts.py  –  Akkaunt olish handlerlari
#  ("Tekin PUBG", "Google akk", "Balli akklar")
# ============================================================

import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto

from database import db
from keyboards.user_kb import (
    subscription_keyboard,
    google_accounts_keyboard,
    balli_accounts_slider_keyboard,
    confirm_buy_keyboard,
    main_menu_keyboard,
)
from utils.helpers import check_user_subscribed, format_account_info

logger = logging.getLogger(__name__)
router = Router()


# ──────────────────────────────────────────────────────
#  Yordamchi – obuna tekshirish
# ──────────────────────────────────────────────────────
async def _check_sub(message: Message, bot: Bot) -> bool:
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
#  🆓 Tekin PUBG akk
# ──────────────────────────────────────────────────────
@router.message(F.text == "🆓 Tekin pubg akk olish")
async def free_pubg_account(message: Message, bot: Bot) -> None:
    """
    Bazadan bitta mavjud tekin_pubg akkauntini olib, foydalanuvchiga beradi
    va akkauntni "sotilgan" deb belgilaydi.
    """
    if not await _check_sub(message, bot):
        return

    accounts = db.get_accounts_by_type("tekin_pubg", only_available=True)

    if not accounts:
        await message.answer(
            "😔 <b>Afsuski, hozirda tekin PUBG akkaunti mavjud emas.</b>\n\n"
            "🔔 Admin tez orada yangi akkаuntlar qo'shadi. Kuting!",
            parse_mode="HTML"
        )
        return

    # Birinchi mavjud akkauntni olamiz
    account = accounts[0]
    account_id = account["id"]
    user_id = message.from_user.id

    # Akkauntni sotilgan deb belgilash
    success = db.mark_account_sold(account_id, user_id)
    if not success:
        await message.answer("⚠️ Xatolik yuz berdi. Qayta urinib ko'ring.")
        return

    # Rasm va ma'lumotlarni yuborish
    caption = format_account_info(account)
    try:
        await message.answer_photo(
            photo=account["rasm_id"],
            caption=caption,
            parse_mode="HTML"
        )
    except Exception:
        # Rasm yuborishda xato bo'lsa, faqat matnni yuboramiz
        await message.answer(text=caption, parse_mode="HTML")


# ──────────────────────────────────────────────────────
#  💎 Ballga Google akk
# ──────────────────────────────────────────────────────
@router.message(F.text == "💎 Ballga haqiqiy Google akk olish")
async def google_accounts_list(message: Message, bot: Bot) -> None:
    """Mavjud pullik_google akkauntlar ro'yxatini ko'rsatadi."""
    if not await _check_sub(message, bot):
        return

    user = db.get_user(message.from_user.id)
    accounts = db.get_accounts_by_type("pullik_google", only_available=True)

    if not accounts:
        await message.answer(
            "😔 <b>Hozirda Google akkаunt mavjud emas.</b>\n\n"
            "Admin tez orada qo'shadi, kuting!",
            parse_mode="HTML"
        )
        return

    text = (
        f"💎 <b>Ballga Google Akkauntlar</b>\n\n"
        f"💰 Sizning balingiz: <b>{user['ball']}</b>\n\n"
        f"Xarid qilmoqchi bo'lgan akkаuntni tanlang:"
    )

    await message.answer(
        text=text,
        reply_markup=google_accounts_keyboard(accounts),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("buy_google:"))
async def buy_google_confirm(callback: CallbackQuery, bot: Bot) -> None:
    """Google akkauntni sotib olishdan oldin tasdiq so'raydi."""
    account_id = int(callback.data.split(":")[1])
    account = db.get_account_by_id(account_id)
    user = db.get_user(callback.from_user.id)

    if not account or account["is_sold"]:
        await callback.answer("❌ Bu akkaunt allaqachon sotilgan!", show_alert=True)
        return

    if user["ball"] < account["narx_ball"]:
        await callback.answer(
            f"❌ Yetarli balingiz yo'q!\n"
            f"Kerak: {account['narx_ball']} ball | Sizda: {user['ball']} ball",
            show_alert=True
        )
        return

    try:
        await callback.message.answer_photo(
            photo=account["rasm_id"],
            caption=(
                f"💎 <b>Akkaunt #{account_id}</b>\n\n"
                f"💰 Narxi: <b>{account['narx_ball']} ball</b>\n"
                f"💳 Sizning balingiz: <b>{user['ball']}</b>\n\n"
                f"Sotib olishni tasdiqlaysizmi?"
            ),
            reply_markup=confirm_buy_keyboard(account_id, "google"),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text=(
                f"💎 <b>Akkaunt #{account_id}</b>\n\n"
                f"💰 Narxi: <b>{account['narx_ball']} ball</b>\n"
                f"Sotib olishni tasdiqlaysizmi?"
            ),
            reply_markup=confirm_buy_keyboard(account_id, "google"),
            parse_mode="HTML"
        )
    await callback.answer()


# ──────────────────────────────────────────────────────
#  🛍 Balli akklar ko'rish (SLIDER / CAROUSEL)
# ──────────────────────────────────────────────────────
@router.message(F.text == "🛍 Balli akkları ko'rish")
async def balli_accounts_list(message: Message, bot: Bot) -> None:
    """Mavjud balli_akk akkаuntlarni bittadan carousel ko'rinishida ko'rsatadi."""
    if not await _check_sub(message, bot):
        return

    accounts = db.get_accounts_by_type("balli_akk", only_available=True)

    if not accounts:
        await message.answer(
            "😔 <b>Hozirda balli akkаunt mavjud emas.</b>",
            parse_mode="HTML"
        )
        return

    await send_slider_account(message, accounts, 0)

async def send_slider_account(message_or_callback, accounts: list, index: int):
    account = accounts[index]
    total_count = len(accounts)
    
    caption = (
        f"🛍 <b>Balli Akkaunt #{account['id']}</b> ({index + 1}/{total_count})\n"
        f"💰 Narxi: <b>{account['narx_ball']} ball</b>"
    )
    markup = balli_accounts_slider_keyboard(account['id'], index, total_count)

    if isinstance(message_or_callback, Message):
        try:
            await message_or_callback.answer_photo(
                photo=account["rasm_id"],
                caption=caption,
                reply_markup=markup,
                parse_mode="HTML"
            )
        except Exception:
            await message_or_callback.answer(
                text=caption,
                reply_markup=markup,
                parse_mode="HTML"
            )
    else:
        # Callback query bo'lsa edit qilamiz
        try:
            await message_or_callback.message.edit_media(
                media=InputMediaPhoto(media=account["rasm_id"], caption=caption, parse_mode="HTML"),
                reply_markup=markup
            )
        except Exception:
            # Rasm o'xshamasa yoki media o'zgartirish muammoli bo'lsa
            pass

@router.callback_query(F.data.startswith("slider:balli:"))
async def balli_slider_navigate(callback: CallbackQuery, bot: Bot) -> None:
    """Keyingisi tugmasi bosilganda ishlaydi."""
    index = int(callback.data.split(":")[2])
    accounts = db.get_accounts_by_type("balli_akk", only_available=True)
    
    if not accounts:
        await callback.answer("Hozirda hech qanday balli akkaunt qolmagan", show_alert=True)
        await callback.message.delete()
        return
        
    if index >= len(accounts):
        index = 0
        
    await send_slider_account(callback, accounts, index)
    await callback.answer()


@router.callback_query(F.data.startswith("buy_balli:"))
async def buy_balli_confirm(callback: CallbackQuery, bot: Bot) -> None:
    """Balli akkauntni sotib olishdan oldin tasdiq so'raydi."""
    account_id = int(callback.data.split(":")[1])
    account = db.get_account_by_id(account_id)
    user = db.get_user(callback.from_user.id)

    if not account or account["is_sold"]:
        await callback.answer("❌ Bu akkaunt allaqachon sotilgan!", show_alert=True)
        return

    if user["ball"] < account["narx_ball"]:
        await callback.answer(
            f"❌ Yetarli balingiz yo'q!\n"
            f"Kerak: {account['narx_ball']} ball | Sizda: {user['ball']} ball",
            show_alert=True
        )
        return

    try:
        await callback.message.answer_photo(
            photo=account["rasm_id"],
            caption=(
                f"🛍 <b>Akkaunt #{account_id}</b>\n\n"
                f"💰 Narxi: <b>{account['narx_ball']} ball</b>\n"
                f"💳 Sizning balingiz: <b>{user['ball']}</b>\n\n"
                f"Sotib olishni tasdiqlaysizmi?"
            ),
            reply_markup=confirm_buy_keyboard(account_id, "balli"),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text=(
                f"🛍 <b>Akkaunt #{account_id}</b>\n\n"
                f"💰 Narxi: <b>{account['narx_ball']} ball</b>\n"
                f"Sotib olishni tasdiqlaysizmi?"
            ),
            reply_markup=confirm_buy_keyboard(account_id, "balli"),
            parse_mode="HTML"
        )
    await callback.answer()


# ──────────────────────────────────────────────────────
#  ✅ Sotib olishni tasdiqlash (google va balli uchun umumiy)
# ──────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("confirm_buy:"))
async def confirm_purchase(callback: CallbackQuery, bot: Bot) -> None:
    """
    Akkauntni rasmiy sotib oladi:
    1. Baldan yechadi
    2. Akkauntni "sotilgan" deb belgilaydi
    3. Akkaunt ma'lumotlarini yuboradi
    """
    parts = callback.data.split(":")
    # confirm_buy:{prefix}:{account_id}
    prefix = parts[1]
    account_id = int(parts[2])

    user_id = callback.from_user.id
    user = db.get_user(user_id)
    account = db.get_account_by_id(account_id)

    if not account or account["is_sold"]:
        await callback.answer("❌ Bu akkaunt allaqachon sotilgan!", show_alert=True)
        return

    if user["ball"] < account["narx_ball"]:
        await callback.answer(
            f"❌ Yetarli balingiz yo'q! Kerak: {account['narx_ball']} ball",
            show_alert=True
        )
        return

    # Baldan yechish
    db.update_user_balls(user_id, -account["narx_ball"])
    # Akkauntni sotilgan deb belgilash
    success = db.mark_account_sold(account_id, user_id)

    if not success:
        # Agar boshqa biri olgan bo'lsa
        db.update_user_balls(user_id, account["narx_ball"])  # Balini qaytarish
        await callback.answer("❌ Akkaunt boshqa foydalanuvchi tomonidan sotib olindi!", show_alert=True)
        return

    # Xabar matnini yangilash
    await callback.message.edit_caption(
        caption="✅ <b>Sotib olindi!</b> Akkaunt ma'lumotlari quyida:",
        parse_mode="HTML"
    )

    # Akkaunt ma'lumotlarini yuborish
    await callback.message.answer(
        text=format_account_info(account),
        parse_mode="HTML"
    )
    await callback.answer("🎉 Muvaffaqiyatli sotib oldingiz!")


@router.callback_query(F.data == "cancel_buy")
async def cancel_purchase(callback: CallbackQuery) -> None:
    """Sotib olishni bekor qiladi."""
    await callback.message.delete()
    await callback.answer("❌ Bekor qilindi.")
