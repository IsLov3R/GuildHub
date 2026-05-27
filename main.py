import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from database import create_pool, create_tables, execute, fetchrow, fetch

TOKEN = "8592688032:AAFroY0M7X47fGUMsXH1jqraU8MP4ATxhlQ"
ADMIN_PASSWORD = "admin_pass_12"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ===== FSM =====
class CreateEvent(StatesGroup):
    game = State()
    date = State()
    players = State()
    description = State()

class AddFriend(StatesGroup):
    username = State()

class CreateClub(StatesGroup):
    name = State()
    description = State()

class AdminPassword(StatesGroup):
    password = State()

class AdminPassword(StatesGroup):
    password = State()

class BanUser(StatesGroup):
    username = State()

class EditRating(StatesGroup):
    user_id = State()
    amount = State()

# ===== /start =====
@dp.message(Command("start"))
async def start_handler(message: Message):
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
    if user["ban"]:
        await message.answer("ты забанен увы")
        return

    else:
        await message.answer("С возвращением 👋")

    builder = InlineKeyboardBuilder()
    builder.button(text="🧑 Профиль", callback_data="profile")
    builder.button(text="⛪ Смотреть клубы", callback_data="clubs")
    builder.button(text="👤 меню админа", callback_data="admin_panel")
    builder.button(text="⛪ Создать клуб", callback_data="create_club")
    builder.button(text="👥 Друзья", callback_data="friends")
    builder.button(text="📅 Смотреть события", callback_data="cobity")
    builder.button(text="🏆 Рейтинг", callback_data="rating")
    builder.button(text="🎮 Создать событие", callback_data="create_event")
    builder.adjust(2)

    await message.answer("Выбери категорию", reply_markup=builder.as_markup())

# ===== кнопки =====

@dp.callback_query(F.data == "admin_panel")
async def admin_password(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer(
        "🔐 Введите пароль админа:"
    )

    await state.set_state(AdminPassword.password)

    await callback.answer()

@dp.message(AdminPassword.password)
async def check_admin_password(message: Message, state: FSMContext):

    if message.text != ADMIN_PASSWORD:
        await message.answer("❌ Неверный пароль")
        return

    builder = InlineKeyboardBuilder()

    builder.button(text="🚫 баны", callback_data="bans")
    builder.button(text="📂 изменить рейтинг", callback_data="edit_reting")

    builder.adjust(2)

    await message.answer(
        "👤 меню админа",
        reply_markup=builder.as_markup()
    )

    await state.clear()

@dp.callback_query(F.data == "bans")
async def ban_player(callback: CallbackQuery):

    builder = InlineKeyboardBuilder()

    builder.button(text="🚫 забанить игрока", callback_data="ban_")
    builder.button(text="🚫 разбанить игрока", callback_data="ban_end")

    builder.adjust(2)

    await callback.message.answer(
        "баны и разбаны",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "edit_reting")
async def edit_rating_menu(callback: CallbackQuery):

    users = await fetch("""
    SELECT *
    FROM users
    ORDER BY rating DESC
    """)

    builder = InlineKeyboardBuilder()

    for user in users:
        builder.button(
            text=f"🏆 @{user['username']} ({user['rating']})",
            callback_data=f"ratinguser_{user['telegram_id']}"
        )

    builder.adjust(1)

    await callback.message.answer(
        "Выбери игрока:",
        reply_markup=builder.as_markup()
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("ratinguser_"))
async def choose_rating_user(callback: CallbackQuery, state: FSMContext):

    user_id = int(callback.data.split("_")[1])

    await state.update_data(user_id=user_id)

    await callback.message.answer(
        "Введи новый рейтинг:"
    )

    await state.set_state(EditRating.amount)

    await callback.answer()

@dp.message(EditRating.amount)
async def set_new_rating(message: Message, state: FSMContext):

    if not message.text.isdigit():
        await message.answer("Введите число ❌")
        return

    data = await state.get_data()

    new_rating = int(message.text)

    await execute("""
    UPDATE users
    SET rating = $1
    WHERE telegram_id = $2
    """,
    new_rating,
    data["user_id"]
    )

    user = await fetchrow("""
    SELECT *
    FROM users
    WHERE telegram_id = $1
    """,
    data["user_id"]
    )

    await message.answer(
        f"✅ Рейтинг @{user['username']} изменён на {new_rating}"
    )

    await state.clear()

@dp.callback_query(F.data == "ban_")
async def ban_menu(callback: CallbackQuery):

    users = await fetch("""
    SELECT *
    FROM users
    ORDER BY username
    """)

    builder = InlineKeyboardBuilder()

    for user in users:

        builder.button(
            text=f"🚫 @{user['username']}",
            callback_data=f"banuser_{user['telegram_id']}"
        )

    builder.adjust(1)

    await callback.message.answer(
        "Выбери игрока для бана:",
        reply_markup=builder.as_markup()
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("banuser_"))
async def ban_user(callback: CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    await execute("""
    UPDATE users
    SET ban = true
    WHERE telegram_id = $1
    """,
    user_id
    )

    user = await fetchrow("""
    SELECT *
    FROM users
    WHERE telegram_id = $1
    """,
    user_id
    )

    await callback.message.answer(
        f"🚫 @{user['username']} забанен"
    )

    await callback.answer("Игрок забанен")

@dp.callback_query(F.data == "ban_end")
async def unban_menu(callback: CallbackQuery):

    users = await fetch("""
    SELECT *
    FROM users
    WHERE ban = true
    ORDER BY username
    """)

    if not users:
        await callback.message.answer(
            "Забаненных игроков нет ✅"
        )
        return

    builder = InlineKeyboardBuilder()

    for user in users:

        builder.button(
            text=f"✅ @{user['username']}",
            callback_data=f"unban_{user['telegram_id']}"
        )

    builder.adjust(1)

    await callback.message.answer(
        "Выбери игрока для разбана:",
        reply_markup=builder.as_markup()
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("unban_"))
async def unban_user(callback: CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    await execute("""
    UPDATE users
    SET ban = false
    WHERE telegram_id = $1
    """,
    user_id
    )

    user = await fetchrow("""
    SELECT *
    FROM users
    WHERE telegram_id = $1
    """,
    user_id
    )

    await callback.message.answer(
        f"✅ @{user['username']} разбанен"
    )

    await callback.answer("Игрок разбанен")

@dp.callback_query(F.data == "friends")
async def friends_menu(callback: CallbackQuery):

    builder = InlineKeyboardBuilder()

    builder.button(text="➕ Добавить друга", callback_data="add_friend")
    builder.button(text="📋 Мои друзья", callback_data="my_friends")
    builder.button(text="📨 Заявки", callback_data="friend_requests")

    builder.adjust(1)

    await callback.message.answer(
        "👥 Меню друзей",
        reply_markup=builder.as_markup()
    )

    @dp.callback_query(F.data == "add_friend")
    async def add_friend_start(callback: CallbackQuery, state: FSMContext):
        await callback.message.answer(
            "Введите username друга без @"
        )

        await state.set_state(AddFriend.username)
        await callback.answer()

    await callback.answer()

@dp.callback_query(F.data == "friend_requests")
async def friend_requests(callback: CallbackQuery):

    requests = await fetch("""
    SELECT users.username, users.telegram_id
    FROM friends
    JOIN users ON users.telegram_id = friends.user_id
    WHERE friends.friend_id = $1
    AND friends.status = 'pending'
    """,
    callback.from_user.id
    )

    if not requests:
        await callback.message.answer("Заявок нет ❌")
        return

    builder = InlineKeyboardBuilder()

    for user in requests:
        builder.button(
            text=f"✅ @{user['username']}",
            callback_data=f"accept_{user['telegram_id']}"
        )

    builder.adjust(1)

    await callback.message.answer(
        "📨 Заявки в друзья:",
        reply_markup=builder.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data == "my_friends")
async def my_friends(callback: CallbackQuery):

    friends = await fetch("""
    SELECT users.username, users.telegram_id
    FROM friends
    JOIN users
    ON users.telegram_id = friends.friend_id 
    WHERE friends.user_id = $1
    AND friends.status = 'accepted'
    """,
    callback.from_user.id
    )

    if not friends:
        await callback.message.answer("👥 У тебя пока нет друзей")
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()

    text = "👥 Мои друзья:\n\n"

    for friend in friends:
        text += f"• @{friend['username']}\n"

        builder.button(
            text=f"❌ @{friend['username']}",
            callback_data=f"delete_friend_{friend['telegram_id']}"
        )

    builder.adjust(1)

    await callback.message.answer(
        text,
        reply_markup=builder.as_markup()
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("delete_friend_"))
async def delete_friend(callback: CallbackQuery):

    friend_id = int(callback.data.split("_")[2])

    # удаляем дружбу
    await execute("""
    DELETE FROM friends
    WHERE (
        user_id = $1 AND friend_id = $2
    )
    OR (
        user_id = $2 AND friend_id = $1
    )
    """,
    callback.from_user.id,
    friend_id
    )

    await callback.answer("Друг удалён ❌")

    await bot.send_message(
        friend_id,
        f"❌ @{callback.from_user.username} удалил тебя из друзей"
    )

    await callback.message.answer("Друг успешно удалён ✅")

@dp.callback_query(F.data.startswith("accept_"))
async def accept_friend(callback: CallbackQuery):

    user_id = int(callback.data.split("_")[1])

    # обновляем заявку
    await execute("""
    UPDATE friends
    SET status = 'accepted'
    WHERE user_id = $1
    AND friend_id = $2
    """,
    user_id,
    callback.from_user.id
    )

    # создаём обратную дружбу
    await execute("""
    INSERT INTO friends (user_id, friend_id, status)
    VALUES ($1, $2, 'accepted')
    ON CONFLICT DO NOTHING
    """,
    callback.from_user.id,
    user_id
    )

    await callback.answer("Друг добавлен ✅")

    await bot.send_message(
        user_id,
        f"👥 @{callback.from_user.username} принял заявку"
    )

@dp.message(AddFriend.username)
async def process_add_friend(message: Message, state: FSMContext):

    username = message.text.replace("@", "")

    friend = await fetchrow(
        "SELECT * FROM users WHERE username = $1",
        username
    )

    if not friend:
        await message.answer("Пользователь не найден ❌")
        return

    if friend["telegram_id"] == message.from_user.id:
        await message.answer("Нельзя добавить себя ❌")
        return

    # проверяем есть ли уже заявка
    existing = await fetchrow("""
    SELECT * FROM friends
    WHERE user_id = $1 AND friend_id = $2
    """,
    message.from_user.id,
    friend["telegram_id"]
    )

    if existing:
        await message.answer("Заявка уже отправлена ❌")
        return

    # добавляем заявку
    await execute("""
    INSERT INTO friends (user_id, friend_id, status)
    VALUES ($1, $2, 'pending')
    """,
    message.from_user.id,
    friend["telegram_id"]
    )

    await message.answer(f"Заявка @{username} отправлена ✅")

    await bot.send_message(
        friend["telegram_id"],
        f"📨 @{message.from_user.username} отправил тебе заявку в друзья"
    )

    await state.clear()

@dp.callback_query(F.data == "press")
async def press_handler(callback: CallbackQuery):
    await callback.message.answer("Ты нажал кнопку!")
    await callback.answer()

@dp.callback_query(F.data == "back_start")
async def back_to_start(callback: CallbackQuery):
    await start_handler(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "cobity")
async def show_cobity(callback: CallbackQuery):
    events = await fetch("SELECT * FROM events ORDER BY id DESC")

    builder = InlineKeyboardBuilder()

    for event in events:
        builder.button(text=f"🎮 {event['game']}", callback_data=f"event_{event['id']}")

    builder.adjust(1)

    await callback.message.answer("⚔️ Ивенты:", reply_markup=builder.as_markup())
    await callback.answer()


# ===== КЛУБЫ =====
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

@dp.callback_query(F.data == "profile")
async def press_handler(callback: CallbackQuery):

    user = await fetchrow("""
    SELECT *
    FROM users
    WHERE telegram_id = $1
    """,
    callback.from_user.id
    )

    friends_count = await fetchrow("""
    SELECT COUNT(*) AS count
    FROM friends
    WHERE (
        user_id = $1
        OR friend_id = $1
    )
    AND status = 'accepted'
    """,
    callback.from_user.id
    )

    clubs_count = await fetchrow("""
    SELECT COUNT(*) AS count
    FROM club_members
    WHERE user_id = $1
    """,
    callback.from_user.id
    )

    await callback.message.answer(
        f"👤 Профиль\n\n"
        f"🆔 ID: {user['telegram_id']}\n"
        f"👤 Username: @{user['username']}\n"
        f"🏆 Рейтинг: {user['rating']}\n"
        f"👥 Друзей: {friends_count['count']}\n"
    )

    await callback.answer()

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

    await execute("""
    INSERT INTO club_members (user_id, club_id)
    VALUES ($1, $2)
    """,
    message.from_user.id,
    club["id"]
    )

    await message.answer(f"Клуб создан ✅\nНазвание: {data['name']}")
    await state.clear()


@dp.callback_query(F.data == "clubs")
async def show_clubs(callback: CallbackQuery):
    clubs = await fetch("SELECT * FROM clubs")

    if not clubs:
        await callback.message.answer("Клубов пока нет ❌")
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()

    for club in clubs:
        builder.button(text=club["name"], callback_data=f"club_{club['id']}")
    builder.button(text="❌ назад", callback_data=f"back_start")
    builder.adjust(1)

    await callback.message.answer("⛪ Список клубов:", reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("club_"))
async def open_club(callback: CallbackQuery):
    club_id = int(callback.data.split("_")[1])

    club = await fetchrow("SELECT * FROM clubs WHERE id = $1", club_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Вступить", callback_data=f"join_{club_id}")
    builder.button(text="❌ назад", callback_data=f"clubs")
    builder.button(text="🗑️ удалить клуб", callback_data=f"dele_{club_id}")

    builder.adjust(1)

    await callback.message.answer(
        f"⛪ {club['name']}\n📝 {club['description']}",
        reply_markup=builder.as_markup()
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("join_"))
async def join_club(callback: CallbackQuery):
    club_id = int(callback.data.split("_")[1])

    await execute("""
    INSERT INTO club_members (user_id, club_id)
    VALUES ($1, $2)
    ON CONFLICT DO NOTHING
    """,
    callback.from_user.id,
    club_id
    )

    await callback.answer("Ты вступил в клуб ✅")

    await start_handler(message=callback.message)

@dp.callback_query(F.data.startswith("dele_"))
async def delete_club(callback: CallbackQuery):

    club_id = int(callback.data.split("_")[1])

    await execute("""
    DELETE FROM clubs
    WHERE id = $1
    """,
    club_id
                  )

    await callback.answer("клуб удален ❌")

    await start_handler(message=callback.message)

# ===== СОЗДАНИЕ СОБЫТИЯ =====
@dp.callback_query(F.data == "create_event")
async def create_event_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🎮Введи название игры:")
    await state.set_state(CreateEvent.game)
    await callback.answer()

@dp.message(CreateEvent.game)
async def event_game(message: Message, state: FSMContext):
    await state.update_data(game=message.text)
    await message.answer("📅 Введи дату (25.12.2026 18:30)")
    await state.set_state(CreateEvent.date)


@dp.message(CreateEvent.date)
async def event_date(message: Message, state: FSMContext):
    try:
        event_date = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("❌ Неверный формат даты")
        return

    await state.update_data(date=event_date)
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

    await fetchrow("""
    INSERT INTO events (creator_id, game, event_date, max_players, description)
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id
    """,
    message.from_user.id,
    data["game"],
    data["date"].strftime("%d.%m.%Y %H:%M"),
    data["players"],
    message.text
    )

    await message.answer(
        f"🎮 {data['game']}\n"
        f"📅 {data['date'].strftime('%d.%m.%Y %H:%M')}\n"
        f"👥 {data['players']}\n"
        f"📝 {message.text}"
    )

    await state.clear()


# ===== СПИСОК ИВЕНТОВ =====
@dp.callback_query(F.data == "events_list")
async def show_events(callback: CallbackQuery):
    events = await fetch("SELECT * FROM events ORDER BY id DESC")

    builder = InlineKeyboardBuilder()

    for event in events:
        builder.button(text=f"🎮 {event['game']}", callback_data=f"event_{event['id']}")

    builder.adjust(1)

    await callback.message.answer("⚔️ Ивенты:", reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("event_"))
async def open_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])

    event = await fetchrow("SELECT * FROM events WHERE id = $1", event_id)

    participants = await fetch("""
    SELECT users.username, event_participants.status, users.rating
    FROM event_participants
    JOIN users ON users.telegram_id = event_participants.user_id
    WHERE event_participants.event_id = $1
    """, event_id)

    going, maybe, no = [], [], []

    for u in participants:
        text = f"@{u['username'] or 'unknown' } { u['rating']}"

        if u["status"] == "going":
            going.append(text)

        elif u["status"] == "maybe":
            maybe.append(text)

        else:
            no.append(text)

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Иду", callback_data=f"go_{event_id}")
    builder.button(text="❌ Не иду", callback_data=f"no_{event_id}")
    builder.button(text="❓ Под вопросом", callback_data=f"maybe_{event_id}")
    builder.button(text="🗑️удалить событие", callback_data=f"del_{event_id}")

    builder.adjust(1)

    await callback.message.answer(
        f"🎮 {event['game']}\n"
        f"📅 {event['event_date']}\n"
        f"👥 {event['max_players']}\n"
        f"📝 {event['description']}\n\n"
        f"✅ Идут:\n{chr(10).join(going) or 'Никого'}\n\n"
        f"❓ Под вопросом:\n{chr(10).join(maybe) or 'Никого'}\n\n"
        f"❌ Не идут:\n{chr(10).join(no) or 'Никого'}",
        reply_markup=builder.as_markup()
    )

    await callback.answer()

@dp.callback_query(F.data.startswith("del_"))
async def delete_cobity(callback: CallbackQuery):

    event_id = int(callback.data.split("_")[1])

    await execute("""
    DELETE FROM events
    WHERE id = $1
    """,
    event_id
                  )

    await callback.answer("событие удалено ❌")

    await start_handler(message=callback.message)


# ===== RSVP =====
@dp.callback_query(F.data.startswith("go_"))
async def go(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])

    await execute("""
    INSERT INTO event_participants (event_id, user_id, status)
    VALUES ($1, $2, 'going')
    ON CONFLICT (event_id, user_id)
    DO UPDATE SET status = 'going'
    """, event_id, callback.from_user.id)

    await execute("""
    UPDATE users
    SET rating = rating + 10
    WHERE telegram_id = $1
    """, callback.from_user.id)

    await callback.answer("Ты идёшь ✅")

    await start_handler(message=callback.message)


@dp.callback_query(F.data.startswith("no_"))
async def no(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])

    await execute("""
    INSERT INTO event_participants (event_id, user_id, status)
    VALUES ($1, $2, 'no')
    ON CONFLICT (event_id, user_id)
    DO UPDATE SET status = 'no'
    """, event_id, callback.from_user.id)

    await callback.answer("Ты не идёшь ❌")

    await start_handler(message=callback.message)

@dp.callback_query(F.data.startswith("maybe_"))
async def maybe(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])

    await execute("""
    INSERT INTO event_participants (event_id, user_id, status)
    VALUES ($1, $2, 'maybe')
    ON CONFLICT (event_id, user_id)
    DO UPDATE SET status = 'maybe'
    """, event_id, callback.from_user.id)

    await callback.answer("Под вопросом ❓")

    await start_handler(message=callback.message)

# ===== РЕЙТИНГ =====
@dp.callback_query(F.data == "rating")
async def show_rating(callback: CallbackQuery):

    users = await fetch("""
    SELECT *
    FROM users
    ORDER BY rating DESC
    LIMIT 10
    """)

    text = "🏆 Топ игроков:\n\n"

    for i, user in enumerate(users, start=1):
        text += f"{i}. @{user['username']} — {user['rating']} очков\n"

    await callback.message.answer(text)
    await callback.answer()


# ===== RUN =====
async def main():
    await create_pool()
    await create_tables()
    print("БД подключена и таблицы созданы ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())