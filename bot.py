
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import BufferedInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
from dateutil.relativedelta import relativedelta
from config import BOT_TOKEN
from db import init_db, set_birth_date, get_birth_date, delete_birth_date, set_reminder, get_reminder
from scheduler import scheduler, add_reminder_job
from utils import parse_date, calculate_life_stats, format_timedelta, parse_two_dates, generate_life_chart

# --- FSM States ---
class Form(StatesGroup):
    waiting_for_birth_date = State()
    waiting_for_target_date = State()
    waiting_for_past_date = State()
    waiting_for_between_dates = State()
    waiting_for_reminder = State()

# --- Keyboards ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Установить дату"), KeyboardButton(text="📊 Статистика жизни")],
        [KeyboardButton(text="🗓 Рассчитать ДО"), KeyboardButton(text="⏳ Рассчитать ПОСЛЕ")],
        [KeyboardButton(text="🔀 Рассчитать МЕЖДУ"), KeyboardButton(text="⏰ Настройка уведомлений")],
        [KeyboardButton(text="❌ Удалить дату"), KeyboardButton(text="ℹ️ Помощь")],
        [KeyboardButton(text="🧑‍💻 GitHub"), KeyboardButton(text="👋 Добро пожаловать!")]
    ],
    resize_keyboard=True
)

# --- Bot Init ---
from core import bot, dp

# --- FSM Interrupt Handler ---
@dp.message(F.text.in_([
    "📅 Установить дату", "📊 Статистика жизни",
    "🗓 Рассчитать ДО", "⏳ Рассчитать ПОСЛЕ",
    "🔀 Рассчитать МЕЖДУ", "⏰ Настройка уведомлений",
    "❌ Удалить дату", "ℹ️ Помощь", "🧑‍💻 GitHub", "👋 Добро пожаловать!"
]))
async def menu_interrupt(message: Message, state: FSMContext):
    await state.clear()
    if message.text == "📅 Установить дату":
        await set_date(message, state)
    elif message.text == "📊 Статистика жизни":
        await life_stats(message)
    elif message.text == "🗓 Рассчитать ДО":
        await calc_to(message, state)
    elif message.text == "⏳ Рассчитать ПОСЛЕ":
        await calc_after(message, state)
    elif message.text == "🔀 Рассчитать МЕЖДУ":
        await calc_between(message, state)
    elif message.text == "⏰ Настройка уведомлений":
        await setup_reminder(message, state)
    elif message.text == "❌ Удалить дату":
        await delete_date(message)
    elif message.text == "ℹ️ Помощь":
        await help_info(message)
    elif message.text == "🧑‍💻 GitHub":
        await github_link(message)
    elif message.text == "👋 Добро пожаловать!":
        await cmd_start(message)

# --- Handlers ---
@dp.message(CommandStart())
@dp.message(F.text == "👋 Добро пожаловать!")
async def cmd_start(message: Message):
    await message.answer("👋 Добро пожаловать в Vitameter — Статистика жизни! Выберите действие:", reply_markup=main_menu)

@dp.message(F.text == "📅 Установить дату")
async def set_date(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Введите дату рождения в формате ДД.ММ.ГГГГ")
    await state.set_state(Form.waiting_for_birth_date)

@dp.message(Form.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    date = parse_date(message.text)
    if not date:
        return await message.answer("Некорректный формат даты. Попробуйте снова.")
    await set_birth_date(message.from_user.id, date)
    await message.answer("Дата рождения установлена!")
    await state.clear()

@dp.message(F.text == "📊 Статистика жизни")
async def life_stats(message: Message):
    user_id = message.from_user.id
    bdate = await get_birth_date(user_id)
    if not bdate:
        return await message.answer("Сначала установите дату рождения через 📅 Установить дату.")
    try:
        stats = calculate_life_stats(bdate)
        chart_buffer = generate_life_chart(bdate)
        chart_file = BufferedInputFile(file=chart_buffer.getvalue(), filename="life_chart.png")
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=chart_file,
            caption=f"<b>Ваша жизненная статистика :</b>\n{stats}",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer("Произошла ошибка при расчёте статистики. Попробуйте снова.")
        print(f"[Ошибка] Статистика: {e}")

@dp.message(F.text == "🗓 Рассчитать ДО")
async def calc_to(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Введите целевую дату в формате ДД.ММ.ГГГГ")
    await state.set_state(Form.waiting_for_target_date)

@dp.message(Form.waiting_for_target_date)
async def process_to_date(message: Message, state: FSMContext):
    date = parse_date(message.text)
    if not date:
        return await message.answer("Некорректный формат даты. Попробуйте снова.")
    delta = date - datetime.now()
    await message.answer("До этой даты осталось:\n" + format_timedelta(delta))
    await state.clear()

@dp.message(F.text == "⏳ Рассчитать ПОСЛЕ")
async def calc_after(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Введите прошедшую дату в формате ДД.ММ.ГГГГ")
    await state.set_state(Form.waiting_for_past_date)

@dp.message(Form.waiting_for_past_date)
async def process_after_date(message: Message, state: FSMContext):
    date = parse_date(message.text)
    if not date or date > datetime.now():
        return await message.answer("Некорректная дата. Убедитесь, что дата в прошлом.")
    delta = datetime.now() - date
    await message.answer("С этой даты прошло:\n" + format_timedelta(delta))
    await state.clear()

@dp.message(F.text == "🔀 Рассчитать МЕЖДУ")
async def calc_between(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Введите две даты через дефис (ДД.ММ.ГГГГ-ДД.ММ.ГГГГ)")
    await state.set_state(Form.waiting_for_between_dates)

@dp.message(Form.waiting_for_between_dates)
async def process_between(message: Message, state: FSMContext):
    d1, d2 = parse_two_dates(message.text)
    if not d1 or not d2:
        return await message.answer("Некорректный ввод. Формат: ДД.ММ.ГГГГ-ДД.ММ.ГГГГ")
    delta = abs(d2 - d1)
    await message.answer("Между этими датами:\n" + format_timedelta(delta))
    await state.clear()

@dp.message(F.text == "⏰ Настройка уведомлений")
async def setup_reminder(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Введите день недели и время в формате: понедельник 09:00 (по МСК)")
    await state.set_state(Form.waiting_for_reminder)

@dp.message(Form.waiting_for_reminder)
async def process_reminder(message: Message, state: FSMContext):
    try:
        day_str, time_str = message.text.lower().split()
        day_map = {
            'понедельник': 0, 'вторник': 1, 'среда': 2,
            'четверг': 3, 'пятница': 4, 'суббота': 5, 'воскресенье': 6
        }
        hour, minute = map(int, time_str.split(":"))
        weekday = day_map[day_str]
        await set_reminder(message.from_user.id, weekday, hour, minute)
        add_reminder_job(message.from_user.id, weekday, hour, minute)
        await message.answer("Напоминание установлено (по МСК). Еженедельно в выбранное время вы будете получать отчёт.")
    except Exception:
        await message.answer("Неверный формат. Попробуйте: вторник 18:30")
    await state.clear()

@dp.message(F.text == "❌ Удалить дату")
async def delete_date(message: Message):
    await delete_birth_date(message.from_user.id)
    await message.answer("Дата рождения удалена.")

@dp.message(F.text == "ℹ️ Помощь")
async def help_info(message: Message):
    await message.answer("Vitameter — бот, который отображает статистику жизни. \nВыберите кнопку и следуйте инструкциям.\nЧтобы отобразить список возможностей, отправь /help в чат")

@dp.message(F.text == "🧑‍💻 GitHub")
async def github_link(message: Message):
    await message.answer("Проект на GitHub: [VitameTer GitHub](https://github.com/YOUR_GITHUB_URL)", parse_mode="Markdown")

# --- Main Run ---
async def main():
    await init_db()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
