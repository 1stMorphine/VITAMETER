from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types import BufferedInputFile
from db import get_birth_date, get_reminder
from utils import calculate_life_stats, generate_life_chart
from datetime import datetime
from core import bot

scheduler = AsyncIOScheduler()

async def send_weekly_report(user_id: int):
    try:
        birth_date = await get_birth_date(user_id)
        if not birth_date:
            return

        stats = calculate_life_stats(birth_date)
        chart = generate_life_chart(birth_date)

        chart_file = BufferedInputFile(file=chart.getvalue(), filename="weekly_life_chart.png")

        await bot.send_photo(
            user_id,
            photo=chart_file,
            caption=f"Ваш еженедельный отчёт (по МСК):\n" + stats
        )
    except Exception as e:
        print(f"[Ошибка отправки отчёта] Пользователь {user_id}: {e}")

def add_reminder_job(user_id: int, weekday: int, hour: int, minute: int):
    scheduler.add_job(
        send_weekly_report,
        "cron",
        args=[user_id],
        day_of_week=weekday,
        hour=hour,
        minute=minute,
        timezone="Europe/Moscow",
        id=f"reminder_{user_id}",
        replace_existing=True
    )
