import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# FSM
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from database import create_pool, create_tables, execute, fetchrow, fetch

TOKEN = "8592688032:AAFroY0M7X47fGUMsXH1jqraU8MP4ATxhlQ"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ===== FSM =====
class CreateEvent(StatesGroup):
    game = State()
    date = State()
    players = State()
    description = State()


class CreateClub(StatesGroup):
    name = State()
    description = State()


# ===== /start =====
@dp.message(Command("start"))
async def start_handler(message: Message):
    args = message.text.split()

    # регистрация
    user = await fetchrow(
        "SELECT * FROM users WHERE telegram_id = $1",
        message.from_user.id
    )

    if not user:
        await execute(
            "INSERT INTO users (telegram_id, username) VALUES ($1, $2)",
            message.from_user.id,
            message.from_user.username
        )
        await message.answer("Ты зарегистрирован ✅")
    else:
        await message.answer("С возвращением 👋")

    # меню
    builder = InlineKeyboardBuilder()
    builder.button(text="🧑 Профиль", callback_data="press")
    builder.button(text="⛪ Смотреть клубы", callback_data="clubs")
    builder.button(text="⛪ Создать клуб", callback_data="create_club")
    builder.button(text="👥 Друзья", callback_data="press")
    builder.button(text="📅 События", callback_data="press")
    builder.button(text="⚔️ Битвы", callback_data="press")
    builder.button(text="🏆 Рейтинг", callback_data="press")
    builder.button(text="🧺 Маркет", callback_data="press")
    builder.button(text="⚙️ Настройки", callback_data="press")
    builder.button(text="🎮 Создать ивент", callback_data="create_event")
    builder.adjust(2)

    await message.answer("Выбери категорию", reply_markup=builder.as_markup())


# ===== кнопки =====
@dp.callback_query(F.data == "press")
async def press_handler(callback: CallbackQuery):
    await callback.message.answer("Ты нажал кнопку!")
    await callback.answer()


# ===== КЛУБЫ =====

# создание клуба
@dp.callback_query(F.data == "create_club")
async def create_club_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("⛪ Введи название клуба:")
    await state.set_state(CreateClub.name)
    await callback.answer()


@dp.message(CreateClub.name)
async def club_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 Введи описание клуба:")
    await state.set_state(CreateClub.description)


@dp.message(CreateClub.description)
async def club_description(message: Message, state: FSMContext):
    data = await state.get_data()

    club = await fetchrow("""
    INSERT INTO clubs (name, description, owner_id)
    VALUES ($1, $2, $3)
    RETURNING id
    """,
    data["name"],
    message.text,
    message.from_user.id
    )

    # владелец автоматически вступает
    await execute("""
    INSERT INTO club_members (user_id, club_id)
    VALUES ($1, $2)
    """, message.from_user.id, club["id"])

    await message.answer(f"Клуб создан ✅\nНазвание: {data['name']}")
    await state.clear()


# список клубов
@dp.callback_query(F.data == "clubs")
async def show_clubs(callback: CallbackQuery):
    clubs = await fetch("SELECT * FROM clubs")

    if not clubs:
        await callback.message.answer("Клубов пока нет ❌")
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()

    for club in clubs:
        builder.button(
            text=club["name"],
            callback_data=f"club_{club['id']}"
        )

    builder.adjust(1)

    await callback.message.answer("⛪ Список клубов:", reply_markup=builder.as_markup())
    await callback.answer()


# открыть клуб
@dp.callback_query(F.data.startswith("club_"))
async def open_club(callback: CallbackQuery):
    club_id = int(callback.data.split("_")[1])

    club = await fetchrow("SELECT * FROM clubs WHERE id = $1", club_id)

    if not club:
        await callback.answer("Клуб не найден ❌")
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Вступить", callback_data=f"join_{club_id}")
    builder.button(text=" ➖ Не вступать", callback_data=f"join_{club_id}")

    builder.adjust(2)

    await callback.message.answer(
        f"⛪ {club['name']}\n📝 {club['description']}",
        reply_markup=builder.as_markup()
    )

    await callback.answer()


# вступить в клуб
@dp.callback_query(F.data.startswith("join_"))
async def join_club(callback: CallbackQuery):
    club_id = int(callback.data.split("_")[1])

    await execute("""
    INSERT INTO club_members (user_id, club_id)
    VALUES ($1, $2)
    ON CONFLICT DO NOTHING
    """, callback.from_user.id, club_id)

    await callback.answer("Ты вступил в клуб ✅")

    builder = InlineKeyboardBuilder()
    builder.button(text="🧑 Профиль", callback_data="press")
    builder.button(text="⛪ Смотреть клубы", callback_data="clubs")
    builder.button(text="⛪ Создать клуб", callback_data="create_club")
    builder.button(text="👥 Друзья", callback_data="press")
    builder.button(text="📅 События", callback_data="press")
    builder.button(text="⚔️ Битвы", callback_data="press")
    builder.button(text="🏆 Рейтинг", callback_data="press")
    builder.button(text="🧺 Маркет", callback_data="press")
    builder.button(text="⚙️ Настройки", callback_data="press")
    builder.button(text="🎮 Создать ивент", callback_data="create_event")
    builder.adjust(2)

    await callback.message.answer("Выбери категорию", reply_markup=builder.as_markup())

# ===== СОБЫТИЯ =====
@dp.callback_query(F.data == "create_event")
async def create_event_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🎮 Введи игру:")
    await state.set_state(CreateEvent.game)
    await callback.answer()


@dp.message(CreateEvent.game)
async def event_game(message: Message, state: FSMContext):
    await state.update_data(game=message.text)
    await message.answer("📅 Введи дату:")
    await state.set_state(CreateEvent.date)


@dp.message(CreateEvent.date)
async def event_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await message.answer("👥 Сколько игроков?")
    await state.set_state(CreateEvent.players)


@dp.message(CreateEvent.players)
async def event_players(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число ❌")
        return

    await state.update_data(players=int(message.text))
    await message.answer("📝 Описание:")
    await state.set_state(CreateEvent.description)


@dp.message(CreateEvent.description)
async def event_description(message: Message, state: FSMContext):
    data = await state.get_data()

    event = await fetchrow("""
    INSERT INTO events (creator_id, game, event_date, max_players, description)
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id
    """,
    message.from_user.id,
    data["game"],
    data["date"],
    data["players"],
    message.text
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Иду", callback_data=f"go_{event['id']}")
    builder.button(text="❌ Не иду", callback_data=f"no_{event['id']}")
    builder.button(text="❓ Под вопросом", callback_data=f"maybe_{event['id']}")
    builder.adjust(1)

    await message.answer(
        f"🎮 {data['game']}\n📅 {data['date']}\n👥 {data['players']}\n📝 {message.text}",
        reply_markup=builder.as_markup()
    )

    await state.clear()


# RSVP
@dp.callback_query(F.data.startswith("go_"))
async def rsvp_go(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])

    await execute("""
    INSERT INTO event_participants (event_id, user_id, status)
    VALUES ($1, $2, 'going')
    ON CONFLICT (event_id, user_id)
    DO UPDATE SET status = 'going'
    """, event_id, callback.from_user.id)

    await callback.answer("Ты идёшь ✅")


@dp.callback_query(F.data.startswith("no_"))
async def rsvp_no(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])

    await execute("""
    INSERT INTO event_participants (event_id, user_id, status)
    VALUES ($1, $2, 'no')
    ON CONFLICT (event_id, user_id)
    DO UPDATE SET status = 'no'
    """, event_id, callback.from_user.id)

    await callback.answer("Ты не идёшь ❌")


@dp.callback_query(F.data.startswith("maybe_"))
async def rsvp_maybe(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])

    await execute("""
    INSERT INTO event_participants (event_id, user_id, status)
    VALUES ($1, $2, 'maybe')
    ON CONFLICT (event_id, user_id)
    DO UPDATE SET status = 'maybe'
    """, event_id, callback.from_user.id)

    await callback.answer("Под вопросом ❓")


# ===== прочее =====
@dp.message(F.photo)
async def photo_handler(message: Message):
    await message.reply("Привет! Я асинхронный бот 🤖")


@dp.message(Command("pic"))
async def send_image(message: Message):
    photo = FSInputFile("синема.jpg")
    await message.answer_photo(photo, caption="Вот твоя картинка!")


@dp.message()
async def echo_handler(message: Message):
    if message.text and message.text.lower() == "привет":
        await message.answer("Привет! Я асинхронный бот 🤖")


# ===== запуск =====
async def main():
    await create_pool()
    await create_tables()
    print("БД подключена и таблицы созданы ✅")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())