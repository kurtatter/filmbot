#!/usr/bin/env python3
import logging
import sqlite3
from datetime import datetime
import random
import os

from aiogram import Bot, Dispatcher, executor, types
from dotenv import dotenv_values

dotenvfile_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenvfile_path):
    config = dotenv_values(dotenvfile_path)
    API_TOKEN = config.get('API_TOKEN')

UNICODE_HEART_SMILE = '\U00002764'
UNICODE_PLUS_SMILE = '\U0000002B'
UNICODE_FILM_SMILE = '\U0001F3AC'
UNICODE_FILMS_SMILE = '\U0001F39E'
UNICODE_QUESTION_SMILE = '\U00002753'
UNICODE_ADD_FILM_SMILES = f'{UNICODE_PLUS_SMILE} {UNICODE_FILM_SMILE}'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

db_conn = sqlite3.connect('films.db')
db_cursor = db_conn.cursor()


def get_random_film_url():
    exists_films = db_cursor.execute("select * from films where showed=0").fetchall()
    exists_urls = list(map(lambda film: film[1], exists_films))
    if not exists_urls:
        return exists_urls
    return random.choice(exists_urls)


def get_random_film_inline_keyboard():
    inline_btn_film_showed = types.InlineKeyboardButton('Смотрели', callback_data='showed')
    inline_btn_film_another = types.InlineKeyboardButton('Ещё', callback_data='another')
    inline_film_keyboard = types.InlineKeyboardMarkup()
    inline_film_keyboard.add(inline_btn_film_showed)
    inline_film_keyboard.add(inline_btn_film_another)
    return inline_film_keyboard


@dp.message_handler(commands=['help', 'start'])
async def send_welcome(message: types.Message):
    btn_get_random_film = types.KeyboardButton(UNICODE_FILM_SMILE)
    btn_show_all_films = types.KeyboardButton(f'{UNICODE_FILMS_SMILE}')
    btn_help = types.KeyboardButton(f'{UNICODE_QUESTION_SMILE}')
    welcome_keyboard = types.ReplyKeyboardMarkup()
    welcome_keyboard.add(btn_get_random_film)
    welcome_keyboard.add(btn_show_all_films)
    welcome_keyboard.add(btn_help)
    await message.reply(f"Пора смотреть фильмы вместе! {UNICODE_HEART_SMILE}", reply_markup=welcome_keyboard)


@dp.message_handler(lambda message: message.text.lower() in ['stas', 'roxy', 'стас', 'рокси', 'роксана'])
async def show_heart(message: types.Message):
    await message.answer(UNICODE_HEART_SMILE)


@dp.callback_query_handler(lambda c: c.data == 'another')
async def process_another(callback_query: types.CallbackQuery):
    random_film = get_random_film_url()
    if not random_film:
        await bot.send_message(callback_query.from_user.id, 'Все фильмы уже просмотрены!')
    else:
        await bot.send_message(callback_query.from_user.id, random_film, reply_markup=get_random_film_inline_keyboard())


@dp.callback_query_handler(lambda c: c.data == 'showed')
async def process_showed(callback_query: types.CallbackQuery):
    db_cursor.execute(f'update films set showed=1 where url="{callback_query.message.text}"')
    db_conn.commit()
    random_film = get_random_film_url()
    if not random_film:
        await bot.send_message(callback_query.from_user.id, 'Все фильмы уже просмотрены!')
    else:
        await bot.send_message(callback_query.from_user.id, random_film, reply_markup=get_random_film_inline_keyboard())


@dp.message_handler(lambda message: message.text == UNICODE_FILM_SMILE)
async def get_random_film(message: types.Message):
    random_film = get_random_film_url()
    if not random_film:
        await message.answer('Все фильмы уже просмотрены!')
    else:
        await message.answer(random_film, reply_markup=get_random_film_inline_keyboard())


@dp.message_handler(lambda message: message.text == UNICODE_QUESTION_SMILE)
async def get_random_film(message: types.Message):
    await message.answer("/help помощь")


@dp.message_handler(lambda message: 'youtube' in message.text or 'kinopoisk' in message.text)
async def add_film(message: types.Message):
    username = message.from_user.first_name + ' ' + message.from_user.last_name
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')
    exists_film = db_cursor.execute(f'select * from films where url="{message.text}"').fetchone()
    if not exists_film:
        db_cursor.execute(f"""insert into films(url, addDate, addUser, showed) 
        values 
        ("{message.text}","{current_datetime}","{username}", 0);""")
        db_conn.commit()
        await message.answer('Фильм добавлен!')
    else:
        await message.answer(f"""
Фильм уже был добавлен ранее!
Кем: {exists_film[3]}
Когда: {exists_film[2]}
Был просмотрен: {"Да" if exists_film[-1] else "Нет"}
        """)


@dp.message_handler(lambda message: message.text == UNICODE_FILMS_SMILE)
async def show_all_films(message: types.Message):
    exists_films = db_cursor.execute("select * from films where showed=0").fetchall()
    exists_urls = list(map(lambda film: film[1], exists_films))
    if exists_urls:
        for url in exists_urls:
            await message.answer(url)
    else:
        await message.answer('Список фильмов пуст!')


if __name__ == '__main__':
    db_cursor.execute("""create table if not exists films(
    id integer primary key autoincrement,
    url text,
    addDate text,
    addUser text,
    showed int)""")
    executor.start_polling(dp, skip_updates=True)
