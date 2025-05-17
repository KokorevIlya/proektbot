import logging
import aiohttp
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from telegram import ReplyKeyboardMarkup
from config import BOT_TOKEN
from random import randint, random
import requests
from deep_translator import GoogleTranslator
import sqlite3
from config import apikey


# немного кнопок
start_keyboard = [['/dice', '/weather', '/coin', '/reviews', '/meme', '/cat'],
                  ['/timer', '/help', '/transl', '/gen_nick', '/gen_password']]
dice_keyboard = [['кинуть один шестигранный кубик', 'кинуть 2 шестигранных кубика одновременно'],
                  ['кинуть 20-гранный кубик', 'вернуться назад']]
timer_keyboard = [['30 секунд', '1 минута'],
                  ['5 минут', 'вернуться назад']]
come_back_keyboard = [['вернуться назад']]
pass_keyboard = [['/gen_password'], ['вернуться назад']]
nick_keyboard = [['/gen_nick'], ['вернуться назад']]
close_keyboard = [['/close']]
heads_tails_keyboard = [['/coin'], ['вернуться назад']]
translate_keyboard = [['С русского на английский'], ['С английского на русский'], ['вернуться назад']]
meme_keyboard = [['/meme'], ['вернуться назад']]
cat_keyboard = [['/cat'], ['вернуться назад']]
markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
markup_dice = ReplyKeyboardMarkup(dice_keyboard, one_time_keyboard=False)
markup_timer = ReplyKeyboardMarkup(timer_keyboard, one_time_keyboard=False)
markup_close = ReplyKeyboardMarkup(close_keyboard, one_time_keyboard=False)
markup_comeback = ReplyKeyboardMarkup(come_back_keyboard, one_time_keyboard=False)
markup_comeback_heads_tails = ReplyKeyboardMarkup(heads_tails_keyboard, one_time_keyboard=False)
markup_transl = ReplyKeyboardMarkup(translate_keyboard, one_time_keyboard=False)
markup_password = ReplyKeyboardMarkup(pass_keyboard, one_time_keyboard=False)
markup_nick = ReplyKeyboardMarkup(nick_keyboard, one_time_keyboard=False)
markup_meme = ReplyKeyboardMarkup(meme_keyboard, one_time_keyboard=False)
markup_cat = ReplyKeyboardMarkup(cat_keyboard, one_time_keyboard=False)

# подключаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

# старт
async def start(update, context):
    await update.message.reply_text(
        "Я бот-помощник. Сделаю вашу жизнь лучше!",
        reply_markup=markup
    )


# кидаем рандомный мем
async def meme(update, context):
    n = randint(1, 20)
    file_path = f'img/meme/{n}.jpg'
    file_data = open(file_path, 'rb')
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=file_data,
        caption="Мем",
        reply_markup = markup_meme
    )
    file_data.close()


# кидаем рандомного кота
async def cats(update, context):
    n = randint(1, 99)
    file_path = f'img/cat/{n}.jpg'
    file_data = open(file_path, 'rb')
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=file_data,
        caption="Котик",
        reply_markup = markup_cat
    )
    file_data.close()


# генерируем пароль
async def gen_password(update, context):
    words = "qwertyuiopasdfghjklzxcvbnm"
    words_pass = words + words.upper() + '1234567890!#$%&*'
    password = ''
    for i in range(randint(8, 16)):
        password += words_pass[randint(0, len(words_pass))]
    await update.message.reply_text(
        f'Ваш пароль: {password}',
        reply_markup=markup_password
    )


# генерируем ник
async def gen_nick(update, context):
    words = "qwertyuiopasdfghjklzxcvbnm"
    words_pass = words + words.upper() + '1234567890'
    password = ''
    for i in range(randint(4, 16)):
        password += words_pass[randint(0, len(words_pass))]
    await update.message.reply_text(
        f'Ваш ник: {password}',
        reply_markup=markup_nick
    )


# Отзывы о боте
async def reviews(update, context):
    con = sqlite3.connect("reviews.sqlite")
    cur = con.cursor()
    result = cur.execute("""SELECT user_id, reviews FROM reviews""").fetchall()
    users_list = [int(elem[0]) for elem in result]
    if not context.args:
        if result:
            reviews_number = sum(int(elem[1]) for elem in result) / len(result)
            await update.message.reply_text(f'Средняя оценка бота: {str(reviews_number)[:4]}',
                                            reply_markup=markup_comeback)
        else:
            await update.message.reply_text('Ещё нет оценок', reply_markup=markup_comeback)
        con.close()
        return
    if len(context.args) > 1:
        await update.message.reply_text('Укажите только одну оценку', reply_markup=markup_comeback)
        con.close()
        return
    try:
        rating = int(context.args[0])
        if not (0 <= rating <= 10):
            raise ValueError
    except ValueError:
        await update.message.reply_text('Оценка должна быть числом от 0 до 10',
                                        reply_markup=markup_comeback)
        con.close()
        return
    if update.message.from_user.id in users_list:
        cur.execute("""UPDATE reviews SET reviews = ? WHERE user_id = ?""",
                    (rating, update.message.from_user.id))
    else:
        cur.execute("""INSERT INTO reviews (user_id, reviews) VALUES (?, ?)""",
                    (update.message.from_user.id, rating))
    con.commit()
    await update.message.reply_text('Оценка сохранена!', reply_markup=markup_comeback)
    con.close()


# переводчик
async def transl(update, context):
    words = ''
    for i in range(len(context.args)):
        words += context.args[i] + ' '
    words = words[0:-1]
    print(words)
    if context.args:
        try:
            f = open(f'translate/{update.message.from_user.id}.txt', 'r')
            name = f.readlines()
            if name[0] == "С русского на английский":
                translated = GoogleTranslator(source="ru", target="en").translate(words)
            else:
                translated = GoogleTranslator(source="en", target="ru").translate(words)
            await update.message.reply_text(translated, reply_markup=markup_transl)
        except FileNotFoundError:
            await update.message.reply_text(
                'Выберите направление перевода',
                reply_markup=markup_transl)
    else:
        await update.message.reply_text(
            'Введите слово',
            reply_markup=markup_transl)


# калькулятор
async def calc(update, context):
    expression = ''
    if context.args:
        try:
            for i in range(len(context.args)):
                expression += context.args[i]
            numbers = eval(expression)
            await update.message.reply_text(
                numbers,
                reply_markup=markup_comeback)
        except Exception as es:
            await update.message.reply_text(
                f'Произошла ошибка {es}, введите корректное выражение',
                reply_markup=markup_comeback)
    else:
        await update.message.reply_text(
            'Введите выражение',
            reply_markup=markup_comeback)


# помощь
async def help(update, context):
    await update.message.reply_text(
        "Свяжитесь с администраторами:\n @Ilya06247 или @Volody_razmarin",
        reply_markup=markup_comeback
    )


# кидать кубики
async def dice(update, context):
    if update.message.text == '/dice':
        await update.message.reply_text(
        "Выберите режим",
        reply_markup=markup_dice
        )


# орёл - решка
async def coin(update, context):
    n = randint(0, 1)
    if n == 1:
        name = 'Решка'
    else:
        name = 'Орёл'
    await update.message.reply_text(
        name,
        reply_markup=markup_comeback_heads_tails
    )


# таймер
async def timer(update, context):
    if update.message.text == '/timer':
        await update.message.reply_text(
        "Выберите время",
        reply_markup=markup_timer
        )


async def task(context):
    await context.bot.send_message(context.job.chat_id, text=f'КУКУ, Время прошло!!')


# работаем с чатом
async def echo(update, context):
    if update.message.text == "С русского на английский": # обрабатываем конфиг перевода
        f = open(f'translate/{update.message.from_user.id}.txt', 'w')
        f.write("С русского на английский")
        await update.message.reply_text(
            "Настройки перевода сохранены",
            reply_markup=markup
        )
    elif update.message.text == 'С английского на русский': # обрабатываем конфиг перевода
        f = open(f'translate/{update.message.from_user.id}.txt', 'w')
        f.write('С английского на русский')
        await update.message.reply_text(
            "Настройки перевода сохранены",
            reply_markup=markup
        )
    if update.message.text == 'кинуть один шестигранный кубик':
        print(rool_dice(1))
        await update.message.reply_text(rool_dice(1))
    if update.message.text == 'кинуть 2 шестигранных кубика одновременно':
        await update.message.reply_text(f'{rool_dice(1)} {rool_dice(1)}')
    if update.message.text == 'кинуть 20-гранный кубик':
        await update.message.reply_text(rool_dice(3))
    if update.message.text == 'вернуться назад':
        await update.message.reply_text(
            "Я бот-помощник. Сделаю вашу жизнь лучше!   ",
            reply_markup=markup
        )
    # работаем с кубиками
    chat_id = update.effective_message.chat_id
    if update.message.text == '30 секунд':
        context.job_queue.run_once(task, 30, chat_id=chat_id, name=str(chat_id), data=30)
        await update.message.reply_text('вернусь через 30 секунд', reply_markup=markup_close)
    if update.message.text == '1 минута':
        context.job_queue.run_once(task, 60, chat_id=chat_id, name=str(chat_id), data=60)
        await update.message.reply_text('вернусь через 1 минуту', reply_markup=markup_close)
    if update.message.text == '5 минут':
        context.job_queue.run_once(task, 300, chat_id=chat_id, name=str(chat_id), data=300)
        await update.message.reply_text('вернусь через 5 минут', reply_markup=markup_close)
    # таймер


# закрыть таймер
async def close(update, context):
    """Удаляет задачу, если пользователь передумал"""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Таймер отменен!' if job_removed else 'У вас нет активных таймеров'
    await update.message.reply_text(text, reply_markup=markup_timer)


# погода + карта
async def weather(update, context):
    global apikey
    city = ""
    if not context.args:
        print(context.args)
        await update.message.reply_text('Введите /weather "название города"')
    else:
        try:
            for i in range(len(context.args)):
                city += context.args[i] + ' '
            city = city[0:-1]
            url = f"http://api.weatherapi.com/v1/current.json?key={apikey}&q={city}&lang=ru"
            response = requests.get(url)
            weathers = response.json()
            city_output = (weathers["location"]["name"])
            temperature = (weathers["current"]["temp_c"])
            sun = (weathers["current"]["condition"]["text"])
            humidity = (weathers["current"]["humidity"])
            speed = (weathers["current"]["wind_kph"])
            geocoder_uri = "http://geocode-maps.yandex.ru/1.x/"
            response = await get_response(geocoder_uri, params={
                "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
                "format": "json",
                "geocode": city
            })
            toponym = response["response"]["GeoObjectCollection"][
                "featureMember"][0]["GeoObject"]
            print(toponym)
            ll, spn = get_ll_spn(toponym)
            static_api_request = f"http://static-maps.yandex.ru/1.x/?ll={ll}&spn={spn}&l=map"
            await context.bot.send_photo(
                update.message.chat_id,
                static_api_request,
                caption=f'Погода в городе {city_output}\n \t Температура: {temperature}\n \t Небо: {sun}\n \t Влажность: {humidity}\n \t Скорость ветра {speed}',
                reply_markup=markup_comeback
            )

        except KeyError:
            await update.message.reply_text(f'Произошла ошибка, проверьте название города', reply_markup=markup_comeback)


# удаление таймера
def remove_job_if_exists(name, context):
    """Удаляем задачу по имени.
    Возвращаем True если задача была успешно удалена."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True



async def get_response(url, params):
    logger.info(f"getting {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            return await resp.json()


def get_ll_spn(toponym):
    toponym_coodrinates = toponym["Point"]["pos"]
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
    ll = ",".join([toponym_longitude, toponym_lattitude])
    envelope = toponym["boundedBy"]["Envelope"]
    l, b = envelope["lowerCorner"].split(" ")
    r, t = envelope["upperCorner"].split(" ")
    dx = abs(float(l) - float(r)) / 2.0
    dy = abs(float(t) - float(b)) / 2.0
    span = f"{dx},{dy}"

    return ll, span


def rool_dice(n):
    if n == 1:
        return int(randint(1, 6))
    if n == 3:
        return randint(1, 20)


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, echo)
    application.add_handler(text_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("timer", timer))
    application.add_handler(CommandHandler("dice", dice))
    application.add_handler(CommandHandler("close", close))
    application.add_handler(CommandHandler("weather", weather))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("calc", calc))
    application.add_handler(CommandHandler("coin", coin))
    application.add_handler(CommandHandler("transl", transl))
    application.add_handler(CommandHandler("reviews", reviews))
    application.add_handler(CommandHandler("gen_password", gen_password))
    application.add_handler(CommandHandler("gen_nick", gen_nick))
    application.add_handler(CommandHandler("meme", meme))
    application.add_handler(CommandHandler("cat", cats))
    application.run_polling()


if __name__ == '__main__':
    main()
