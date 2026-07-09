# ============================================================
#  states/user_states.py  –  Foydalanuvchi FSM holatlari
# ============================================================

from aiogram.fsm.state import State, StatesGroup


class SupportState(StatesGroup):
    """Admin bilan bog'lanish uchun FSM holatlari."""
    waiting_for_message = State()   # Xabar matnini kutish


class BuyAccountState(StatesGroup):
    """Akkaunt sotib olish tasdiqlash holati."""
    waiting_for_confirm = State()   # Tasdiqlash javobini kutish
