# ============================================================
#  bot.py  –  Asosiy kirish nuqtasi (main entry point)
#  Barcha routerlarni ro'yxatdan o'tkazadi va botni ishga tushiradi
# ============================================================

import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.responses import Response

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI (Uvicorn) ishga tushishi bilan botni orqa fonda ishga tushiramiz
    logger.info("🚀 Bot ishga tushirilmoqda...")
    bot_task = asyncio.create_task(start_bot())
    try:
        yield
    finally:
        # Server o'chganda bot taskini to'xtatamiz
        logger.info("🛑 Server to'xtatilyapti, bot vazifasi bekor qilinmoqda...")
        bot_task.cancel()
        with suppress(asyncio.CancelledError):
            await bot_task


app = FastAPI(lifespan=lifespan)


def create_app() -> FastAPI:
    """FastAPI app obyektini qaytaradi."""
    return app


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    icon_svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
      <rect width="64" height="64" rx="12" fill="#2563eb"/>
      <path d="M20 18h24v8H28v6h14v8H28v6h16v8H20z" fill="white"/>
    </svg>'''
    return Response(content=icon_svg, media_type="image/svg+xml", status_code=200)


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


# ──────────────────────────────────────────────────────────
#  Kirish nuqtasi (Kompuyterda sinab ko'rish uchun)
# ──────────────────────────────────────────────────────────
def main() -> None:
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    try:
        uvicorn.run(app, host=host, port=port, reload=False)
    except KeyboardInterrupt:
        logger.info("⚡ Bot foydalanuvchi tomonidan to'xtatildi (Ctrl+C).")


if __name__ == "__main__":
    main()