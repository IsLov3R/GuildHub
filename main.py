import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8592688032:AAFroY0M7X47fGUMsXH1jqraU8MP4ATxhlQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🧑 Профиль", callback_data="press")
    builder.button(text="👥 Друзья ", callback_data="press")
    builder.button(text="📅 События", callback_data="press")
    builder.button(text="⚔️ Битвы", callback_data="press")
    builder.button(text="🏆 Рейтинг", callback_data="press")
    builder.button(text="🧺 Маркет", callback_data="press")
    builder.button(text="⚙️ Настройки", callback_data="press")
    builder.adjust(2)

    await message.answer(
        "Выбери категорию",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "press")
async def press_handler(callback: CallbackQuery):
    await callback.message.answer("Ты нажал кнопку!")
    await callback.answer()


@dp.message(F.photo)
async def photo_handler(message: Message):
    await message.reply("Привет! Я асинхронный бот 🤖")


@dp.message(Command("pic"))
async def send_image(message: Message):
    photo = FSInputFile("синема.jpg")
    await message.answer_photo(photo, caption="Вот твоя картинка!")


@dp.message()
async def echo_handler(message: Message):
    print(message.text, message.from_user.username)
    if message.text == "привет":
        await message.answer("Привет! Я асинхронный бот 🤖")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())