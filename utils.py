from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib

# Используем безопасный backend для серверов и Windows без GUI
matplotlib.use('Agg')

LIFE_EXPECTANCY_YEARS = 90

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        return None

def parse_two_dates(text):
    try:
        part1, part2 = text.split("-")
        return parse_date(part1.strip()), parse_date(part2.strip())
    except Exception:
        return None, None

def calculate_life_stats(birth_date):
    now = datetime.now()
    delta = relativedelta(now, birth_date)
    seconds = int((now - birth_date).total_seconds())
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    weeks = days // 7
    months = delta.years * 12 + delta.months
    years = delta.years

    return (
        f"Вы живёте:\n"
        f"{years} лет, {delta.months} месяцев, {delta.days} дней\n"
        f"Недели: {weeks}\n"
        f"Дни: {days}\n"
        f"Часы: {hours}\n"
        f"Минуты: {minutes}\n"
        f"Секунды: {seconds}"
    )

def format_timedelta(delta):
    total_seconds = int(abs(delta.total_seconds()))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)

    return (
        f"Недели: {weeks}\n"
        f"Дни: {days}\n"
        f"Часы: {hours}\n"
        f"Минуты: {minutes}\n"
        f"Секунды: {seconds}"
    )

def generate_life_chart(birth_date: datetime) -> BytesIO:
    now = datetime.now()
    death_date = birth_date + timedelta(days=LIFE_EXPECTANCY_YEARS * 365.25)

    lived_days = (now - birth_date).days
    remaining_days = max((death_date - now).days, 0)

    fig, ax = plt.subplots(figsize=(8, 2))
    ax.barh(0, lived_days, color='green', label='Прожито')
    ax.barh(0, remaining_days, left=lived_days, color='lightgray', label='Осталось')

    ax.set_xlim(0, LIFE_EXPECTANCY_YEARS * 365.25)
    ax.set_yticks([])
    ax.set_title('Жизненная шкала (из 90 лет)')
    ax.legend(loc='lower right')

    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    plt.close(fig)
    buffer.seek(0)  # Обязательно перед передачей дальше

    return buffer
