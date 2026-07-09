# ============================================================
#  states/admin_states.py  –  Admin FSM holatlari
# ============================================================

from aiogram.fsm.state import State, StatesGroup


class AdminAuthState(StatesGroup):
    """Admin autentifikatsiya holatlari."""
    waiting_for_password = State()   # Parolni kutish


class AdminAddChannelState(StatesGroup):
    """Kanal qo'shish holatlari."""
    waiting_for_channel = State()    # Kanal havolasini kutish


class AdminAddAccountState(StatesGroup):
    """Akkaunt qo'shish holatlari (ko'p bosqichli FSM)."""
    choosing_type   = State()    # Akkaunt turini tanlash
    waiting_photo   = State()    # Rasmni kutish
    waiting_email   = State()    # Emailni kutish
    waiting_password = State()   # Parolni kutish
    waiting_price   = State()    # Narxni (ball) kutish (faqat pullik/balli akk uchun)


class AdminReferralState(StatesGroup):
    """Referal bonus miqdorini o'zgartirish holati."""
    waiting_for_amount = State()  # Yangi miqdorni kutish


class AdminBroadcastState(StatesGroup):
    """Barcha foydalanuvchilarga xabar yuborish holati."""
    waiting_for_message = State()  # Xabar matnini kutish


class AdminBullDropState(StatesGroup):
    """BullDrop promokodlarni kiritish holatlari."""
    waiting_for_photo = State()  # Rasm kiritish
    waiting_for_promos = State() # Promokod(lar) matnini kiritish


class AdminBallPromoState(StatesGroup):
    """Balli Promokod kiritish holatlari."""
    waiting_for_promo_text = State()
    waiting_for_ball = State()
    waiting_for_limit = State()
