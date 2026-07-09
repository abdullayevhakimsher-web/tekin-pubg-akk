# ============================================================
#  handlers/admin/stats.py  –  Statistika va broadcast
# ============================================================

import logging
import asyncio
from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminBroadcastState
from database import db
from keyboards.admin_kb import admin_panel_keyboard, admin_cancel_keyboard
import config

logger = logging.getLogger(__name__)
router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


# ──────────────────────────────────────────────────────
#  📊 Statistika (ReplyKeyboard orqali)
# ──────────────────────────────────────────────────────
@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return

    stats = db.get_stats()
    top_referrers = db.get_top_referrers(limit=10)

    # Top-10 reyting matni
    top_text = ""
    if top_referrers:
        top_text = "\n\n🏆 <b>Top-10 Referal Reytingi:</b>\n"
        medals = ["🥇", "🥈", "🥉"] + ["4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, user in enumerate(top_referrers):
            medal = medals[i] if i < len(medals) else f"{i + 1}."
            top_text += (
                f"{medal} <b>{user['ism']}</b> "
                f"– {user['taklif_qilgan_soni']} kishi "
                f"| {user['ball']} ball\n"
            )

    text = (
        f"📊 <b>Bot Statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"📢 Majburiy kanallar: <b>{stats['total_channels']}</b>\n\n"
        f"📦 Jami akkauntlar: <b>{stats['total_accounts']}</b>\n"
        f"✅ Sotilgan: <b>{stats['sold_accounts']}</b>\n"
        f"📌 Mavjud: <b>{stats['available_accounts']}</b>\n\n"
        f"🎁 Referal bonus: <b>{stats['referral_bonus']} ball</b>"
        + top_text
    )

    await message.answer(
        text=text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )


# ──────────────────────────────────────────────────────
#  📣 Barcha foydalanuvchilarga xabar yuborish (Broadcast)
# ──────────────────────────────────────────────────────
@router.message(F.text == "📣 Hammaga xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    await state.set_state(AdminBroadcastState.waiting_for_message)
    await message.answer(
        text=(
            "📣 <b>Barcha foydalanuvchilarga xabar</b>\n\n"
            "Yuboriladigan xabar matnini kiriting:\n"
            "<i>HTML teglari ishlaydi: &lt;b&gt;, &lt;i&gt;, &lt;code&gt;</i>\n\n"
            "Bekor qilish uchun pastdagi tugmani bosing."
        ),
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdminBroadcastState.waiting_for_message)
async def broadcast_send(message: Message, bot: Bot, state: FSMContext) -> None:
    """Xabarni barcha foydalanuvchilarga yuboradi."""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Xabar yuborish bekor qilindi.",
            reply_markup=admin_panel_keyboard()
        )
        return

    await state.clear()
    users = db.get_all_users()

    if not users:
        await message.answer(
            "❌ Foydalanuvchilar yo'q.",
            reply_markup=admin_panel_keyboard()
        )
        return

    progress_msg = await message.answer(
        f"📤 Yuborilmoqda... (0/{len(users)})",
        reply_markup=admin_panel_keyboard()
    )

    success_count = 0
    fail_count = 0
    broadcast_text = message.text

    for i, user in enumerate(users):
        try:
            await bot.send_message(
                chat_id=user["id"],
                text=broadcast_text,
                parse_mode="HTML"
            )
            success_count += 1
        except Exception:
            fail_count += 1

        # Har 20 foydalanuvchidan keyin progress yangilash
        if (i + 1) % 20 == 0:
            try:
                await progress_msg.edit_text(
                    f"📤 Yuborilmoqda... ({i + 1}/{len(users)})"
                )
            except Exception:
                pass

        # Anti-flood: har xabarda 50ms kutish
        await asyncio.sleep(0.05)

    await progress_msg.edit_text(
        text=(
            f"✅ <b>Xabar yuborish tugadi!</b>\n\n"
            f"📤 Muvaffaqiyatli: <b>{success_count}</b>\n"
            f"❌ Xatolik (bloklangan va h.k.): <b>{fail_count}</b>\n"
            f"👥 Jami: <b>{len(users)}</b>"
        ),
        parse_mode="HTML"
    )
