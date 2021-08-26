import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

from database import SQLdatabase

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv('API_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
db = SQLdatabase()


class Reminder(StatesGroup):
    choose_name = State()
    choose_level = State()


available_power = ["очень важно", "средне", "заметка"]


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    """Начало работы  """
    if not db.user_exist(message.from_user.id):
        db.create_user(message.from_user.id)
    await message.answer(
        f"Привет ,{message.from_user.full_name}! Я бот напоминалка 👩‍⚕️. Делай заметки и смотри их на любом "
        f"устройстве чтобы ничего не забыть.\nСписок команд /help ")


@dp.message_handler(commands=['help'])
async def process_start_command(message: types.Message):
    """Хелп """
    text = "Список команд:\n📝 Создание записи /add\n🗂 Все записи /get\n📊 Записи по важности /list"
    await message.answer(text)


@dp.message_handler(commands=['add'], state="*")
async def rem_start(message: types.Message):
    """Добавление заметок в трёх стейтах """
    await message.answer("Введите текст заметки:")
    await Reminder.choose_name.set()


@dp.message_handler(state=Reminder.choose_name)
async def rem_chosen(message: types.Message, state: FSMContext):
    if message.text.lower() in ["/get", "/add", "/help"]:
        await message.answer("Не корректный текст ⚠️")
        return

    id_u = db.get_id(message.from_user.id)
    await state.update_data(id_u=id_u)
    db.make_record(message.text, id_u)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for size in available_power:
        keyboard.add(size)
    await Reminder.next()
    await message.answer("Теперь выберите срочность:", reply_markup=keyboard)


@dp.message_handler(state=Reminder.choose_level)
async def rem_power_chosen(message: types.Message, state: FSMContext):
    if message.text.lower() not in available_power:
        await message.answer("Пожалуйста, выберите из предложенных вариантов")
        return
    date = await state.get_data()
    id_note = date["id_u"]
    power = {
        "очень важно": 1,
        "средне": 2,
        "заметка": 3
    }
    db.add_power(id_note, power[message.text.lower()])

    await message.answer("Заметка добавлена 📩\nВсе заметки /get", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()


@dp.message_handler(commands=['get'])
async def get_notes(message: types.Message):
    """Получение всех заметок юзера"""
    id_u = db.get_id(message.from_user.id)
    rec = db.get_records(id_u)
    try:
        await message.answer(rec)
    except Exception:
        await message.answer("Записи не найдены ⚠️\nНовая запись /add")


@dp.message_handler(lambda message: message.text.startswith('/del'))
async def delete(message: types.Message):
    """Удаление записи"""
    row_id = int(message.text[4:])
    id_u = db.get_id(message.from_user.id)
    try:
        db.delete_record(row_id, id_u)
    except Exception:
        await message.answer("Не правильный запрос ⚠️")
        return
    await message.answer('Запись удалена♻️\nВернуться к записям /get')


@dp.message_handler(commands=["list"], state="*")
async def list_notes(message: types.Message):
    """ Получение количества записей по важности"""
    id_u = db.get_id(message.from_user.id)
    power = db.get_counts(id_u)
    buttons = [types.InlineKeyboardButton(text=f"очень важно ({power[0]})", callback_data="1"),
               types.InlineKeyboardButton(text=f"средне ({power[1]})", callback_data="2"),
               types.InlineKeyboardButton(text=f"заметка ({power[2]})", callback_data="3")]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await message.answer("Выбирете срочность 📢", reply_markup=keyboard)


powers = ["1", "2", "3"]


@dp.callback_query_handler(text=powers)
async def send_power(call: types.CallbackQuery):
    id_u = db.get_id(call.from_user.id)
    rec = db.get_records_power(id_u, int(call.data))
    try:
        await call.message.answer(rec)
    except Exception:
        await call.message.answer("Записи не найдены ⚠️\nНовая запись /add")


@dp.message_handler()
async def echo(message: types.Message):
    reply = message.from_user.full_name
    await message.answer(f"Не верная команда , {reply}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
