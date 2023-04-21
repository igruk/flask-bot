import os
import re
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app import app, generate_password_hash
from models import db, User


token = os.environ.get('BOT_TOKEN')
bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class UserState(StatesGroup):
    email = State()
    password = State()


async def save_user_to_db(telegram_id, username, first_name, last_name, email, password, image):

    password_hash = generate_password_hash(password)

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


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Вітаю! Для реєстрації на сайті натисніть команду /register")


@dp.message_handler(commands=['register'])
async def register(message: types.Message):
    await message.answer("Введіть свій email:")
    await UserState.email.set()


@dp.message_handler(state=UserState.email)
async def get_username(message: types.Message, state: FSMContext):
    email = message.text
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await state.update_data(email=email)
        await message.answer("Введіть пароль:")
        await UserState.password.set()
    else:
        await message.answer("Введений email некоректний. Будь ласка, введіть правильний email:")


@dp.message_handler(state=UserState.password)
async def get_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)

    data = await state.get_data()

    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    email = data['email']
    password = data['password']

    profile_pictures = await dp.bot.get_user_profile_photos(message.from_user.id)
    photo_file = await dp.bot.get_file(profile_pictures.photos[0][-1].file_id)
    photo_url = f"https://api.telegram.org/file/bot{token}/{photo_file.file_path}"
    filename = f"user_{message.from_user.id}_{photo_url.split('/')[-1]}"
    dir_path = "static/images/"
    os.makedirs(dir_path, exist_ok=True)
    photo_path = os.path.join(dir_path, filename)
    image = photo_path[7:]
    async with aiohttp.ClientSession() as session:
        async with session.get(photo_url) as resp:
            with open(photo_path, 'wb') as photo:
                photo.write(await resp.read())

    try:
        await save_user_to_db(telegram_id, username, first_name, last_name, email, password, image)
        await message.answer("Чудово! Тепер Ви можете заходити у свій аккаунт на сайті.")
    except Exception as e:
        print(e)
        await message.answer("Ви вже зареєстровані.")

    await state.finish()


executor.start_polling(dp, skip_updates=True)
