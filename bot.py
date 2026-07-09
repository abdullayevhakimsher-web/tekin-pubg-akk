# ============================================================
#  bot.py  –  Asosiy kirish nuqtasi (main entry point)
#  Barcha routerlarni ro'yxatdan o'tkazadi va botni ishga tushiradi
# ============================================================

import asyncio
import logging
from fastapi import FastAPI  # <--- YANGI: Render uchun FastAPI

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# ── Konfiguratsiya
import config

# ── Ma'lumotlar bazasi
from database.db import create_tables

# ── User handlerlari
from handlers.user import start, menu, referral, accounts, support

# ── Admin handlerlari
from handlers.admin import auth, channels, accounts as admin_accounts, referral as admin_referral, stats

# ──────────────────────────────────────────────────────────
#  Logging sozlamasi
# ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────
#  FastAPI va Bot obyrktlarini Global miqyosda yaratish
# ──────────────────────────────────────────────────────────
app = FastAPI()  # <--- Render aynan shu "app"ni qidiradi

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())

# ─────────────────────────────────────────────────────
#  Routerlarni ulash (Global miqyosga chiqarildi)
#  MUHIM: tartib muhim – spetsifik filterlar avval kelishi kerak
# ─────────────────────────────────────────────────────

# === Admin routerlari ===
dp.include_router(auth.router)              # /Admin11 kirish
dp.include_router(channels.router)          # Kanallar boshqarish
dp.include_router(admin_accounts.router)    # Akkaunt qo'shish
dp.include_router(admin_referral.router)    # Referal bonus
dp.include_router(stats.router)             # Statistika + broadcast

# === User routerlari ===
dp.include_router(start.router)             # /start
dp.include_router(menu.router)              # Asosiy menyu
dp.include_router(referral.router)          # Ball yig'ish
dp.include_router(accounts.router)          # Akkaunt olish
dp.include_router(support.router)           # Adminga murojat


# ──────────────────────────────────────────────────────────
#  Render uchun maxsus soxta sahifa va Lifespan (Fonda ishlash)
# ──────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "success", "message": "Bot is running perfectly!"}

@app.get("/api/stats")
async def get_statistics():
    """Bot statistikalarini ko'rish uchun maxsus API endpoint"""
    try:
        from database.db import get_stats
        stats = get_stats()
        return {"status": "success", "data": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/users")
async def get_users():
    """Barcha bot foydalanuvchilarini ko'rish uchun API endpoint"""
    try:
        from database.db import get_all_users
        users = [dict(u) for u in get_all_users()]
        return {"status": "success", "total_users": len(users), "data": users}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def start_bot() -> None:
    """Botni orqa fonda (background task) polling rejimida ishga tushirish"""
    # --- Ma'lumotlar bazasini yaratish ---
    logger.info("📦 Ma'lumotlar bazasi yaratilmoqda...")
    create_tables()

    bot_info = await bot.get_me()
    logger.info(f"🤖 Bot ishga tushdi: @{bot_info.username} (ID: {bot_info.id})")
    logger.info(f"👑 Admin ID: {config.ADMIN_ID}")
    logger.info("🚀 Long polling fonda boshlandi...")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()
        logger.info("🛑 Bot to'xtatildi.")

@app.router.lifespan_context
async def lifespan(app: FastAPI):
    # FastAPI (Uvicorn) ishga tushishi bilan botni orqa fonda ishga tushiramiz
    bot_task = asyncio.create_task(start_bot())
    yield
    # Server o'chganda bot taskini to'xtatamiz
    logger.info("🛑 Server to'xtatilyapti, bot vazifasi bekor qilinmoqda...")
    bot_task.cancel()

app.router.lifespan_context = lifespan


# ──────────────────────────────────────────────────────────
#  Kirish nuqtasi (Kompuyterda sinab ko'rish uchun)
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    try:
        # reload=True aiogramning routerlari ikki marta ulanib qolishiga olib kelishi mumkin
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        logger.info("⚡ Bot foydalanuvchi tomonidan to'xtatildi (Ctrl+C).")