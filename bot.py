import os
import re
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from werkzeug.security import generate_password_hash

from app import app
from config import BOT_TOKEN
from models import db, User


bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class UserState(StatesGroup):
    email = State()
    password = State()


def sanitize_input(text: str) -> str:
    """Sanitize user input by removing leading/trailing whitespace."""
    return text.strip()


def is_valid_email(email: str) -> str:
    """Check if the given email is in a valid format."""
    return re.match(r'[^@]+@[^@]+\.[^@]+', email)


async def save_user_to_db(telegram_id, username, first_name, last_name, email, password, image) -> None:
    """Save the user to the database."""
    password_hash = generate_password_hash(password)

    if not username:
        username = telegram_id
    if not first_name:
        first_name = ''
    if not last_name:
        last_name = ''

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password_hash,
        image=image,
    )
    with app.app_context():
        db.session.add(user)
        db.session.commit()


async def download_profile_photo(telegram_id: int) -> str:
    """Download the profile photo of the user."""
    profile_pictures = await dp.bot.get_user_profile_photos(telegram_id)
    photo_file = await dp.bot.get_file(profile_pictures.photos[0][-1].file_id)

    photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{photo_file.file_path}"
    filename = f"user_{telegram_id}_{photo_url.split('/')[-1]}"
    dir_path = "static/images/"
    os.makedirs(dir_path, exist_ok=True)
    photo_path = os.path.join(dir_path, filename)
    image = photo_path[7:]

    async with aiohttp.ClientSession() as session:
        async with session.get(photo_url) as resp:
            with open(photo_path, 'wb') as photo:
                photo.write(await resp.read())
    return image


async def register_user(telegram_id, username, first_name, last_name, email, password) -> None:
    """Register the user by saving their details and profile photo."""
    image = await download_profile_photo(telegram_id)
    await save_user_to_db(telegram_id, username, first_name, last_name, email, password, image)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message) -> None:
    """Send a welcome message to the user."""
    await message.answer("Вітаю! Для реєстрації на сайті натисніть команду /register")


@dp.message_handler(commands=['register'])
async def start_register(message: types.Message) -> None:
    """Start the registration process."""
    await message.answer("Введіть свій email:")
    await UserState.email.set()


@dp.message_handler(state=UserState.email)
async def get_email(message: types.Message, state: FSMContext) -> None:
    """Get the email from the user."""
    email = sanitize_input(message.text)
    if is_valid_email(email):
        await state.update_data(email=email)
        await message.answer("Введіть пароль:")
        await UserState.password.set()
    else:
        await message.answer("Введений email некоректний. Будь ласка, введіть правильний email:")


@dp.message_handler(state=UserState.password)
async def get_password(message: types.Message, state: FSMContext) -> None:
    """Get the password from the user and complete the registration."""
    data = await state.get_data()

    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    password = sanitize_input(message.text)
    email = data['email']

    try:
        await register_user(telegram_id, username, first_name, last_name, email, password)
        await message.answer("Чудово! Тепер Ви можете заходити у свій аккаунт на сайті.")
    except Exception as e:
        print(e)
        await message.answer("Ви вже зареєстровані.")
        raise e

    await state.finish()


def start_bot() -> None:
    """Start the Telegram bot."""
    executor.start_polling(dp, skip_updates=True)
