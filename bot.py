import logging
import sys

import os
import hashlib

import sqlite3

import telebot
from telebot import types

from config import TOKEN
from helper import select_admin, sum_element_in_list, return_one_value, insert_db, update_db, categories, \
    product, select_db, generate_name, hash_func, reg

logger = logging.getLogger('TeleBot')
formatter = logging.Formatter(
    '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
)

console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)

logger.setLevel(logging.ERROR)

bot = telebot.TeleBot(TOKEN)
db = sqlite3.connect("db/shop.db", check_same_thread=False)
cursor = db.cursor()

user_road = ["1"]
last_product = ""

id_edit_profile = 0

show_product_id = 1

messagebot = 0


class redactor:
    type = "user"
    access = "no"
    operation = "no"
    road = ["1"]


def delete_message():
    data_data = select_db("*", "for_delete_product")
    for i in data_data:
        cursor.execute(f"""DELETE FROM for_delete_product WHERE user_id = {i[1]}""")
        db.commit()
        bot.delete_message(chat_id=i[1], message_id=i[2])


@bot.message_handler(commands=['start', 'restart', 'help'])
def cmd_start(message):
    if message.from_user.first_name is None:
        first_name = ""
    else:
        first_name = message.from_user.first_name
    if message.from_user.last_name is None:
        last_name = ""
    else:
        last_name = message.from_user.last_name
    send_mess_help = "Помочь " + first_name + last_name + \
                     "?\nНажми пожалуйста на кнопку ниже, ну или напиши : \n<code>📁 Каталог</code>"

    send_mess_start = "Привет " + first_name + last_name + \
                      " 👋\nНажми пожалуйста на кнопку ниже, ну или напиши : \n<code>📁 Каталог</code>"
    keyboarder = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    first_button = types.KeyboardButton(text="📁 Каталог")
    second_button = types.KeyboardButton(text="🛍 Корзина")
    third_button = types.KeyboardButton(text="👩‍🦽 Профиль")
    fourth_button = types.KeyboardButton(text="📣 Информация")
    fifth_button = types.KeyboardButton(text="Получить прайс лист")
    keyboarder.add(first_button, second_button, third_button, fourth_button)
    if redactor.type != "user":
        admin = types.KeyboardButton(text="Админ панель")
        keyboarder.add(admin)
    if message.text == "/start" or "/restart":
        user_id = str(message.chat.id)
        username = message.from_user.username

        from datetime import datetime

        dt_created = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        if not select_db("_id", "clients", f"username = '{username}'"):
            cursor.execute("""INSERT INTO clients VALUES(?, ?, ?, ?, ?, ?, ?, ?);""",
                           (None, user_id, username, None, None, None, None, dt_created))
            db.commit()
    text = ""
    if message.text == "/start" or message.text == "/restart":
        text = send_mess_start
        reg(message.from_user.id, "artem", "admin")
        global messagebot
        messagebot = message
    elif message.text == "/help":
        text = send_mess_help
    else:
        text = "Ну чтож продолжим"
    bot.send_message(message.from_user.id, text,
                     reply_markup=keyboarder, parse_mode='html')


@bot.message_handler(content_types=["text"])
def accept_message(message):
    global user_road
    if message.text == "📁 Каталог":
        user_road = ["1"]
        do_order(message)
    elif message.text == "⏺В главное меню":
        user_road = ["1"]
        cmd_start(message)
    elif message.text == "Админ панель":
        redactor.operation = "show"
        super_menu(message)
    elif message.text == "📣 Информация":
        get_info(message)
    elif message.text == "< Назад":
        user_road = user_road[:-1]
        do_order(message)
    elif message.text == "🛍 Корзина":
        show_basket(message)
    elif message.text == "👩‍🦽 Профиль" or message.text == "Заполнить профиль":
        show_profile(message)
    elif message.text == "Редактировать профиль":
        edit_profile(message)
    elif message.text == "/" + select_db("*", "settings", "name = 'key_word'")[0][2]:
        activate_admin(message)
    elif message.text == "Отмена":
        if redactor.type != "user":
            activate_admin(message)
        return
    elif message.text == "/getid":
        bot.send_message(message.from_user.id,
                         f"Your id : <b>{message.from_user.id}</b>\nChat id : <b>{message.chat.id}</b>",
                         parse_mode='html')
    elif message.text == "-" * 40:
        do_order(message)
    else:
        bot.send_message(
            message.from_user.id,
            "Походу меня только что исправили\n<code>НУ ИЛИ ТЫ ЧТО-ТО НЕ ТО ВВЁЛ</code>\nНо сейчас уже всё ок)",
            parse_mode="html")
        user_road = ["1"]
        cmd_start(message)


def get_info(message):
    info = select_db("value", "settings", "name = 'info'")[0][
               0] + "\n\nСодатель бота <a href='https://t.me/cha_artem'>ЭТОТ ЧЕЛОВЕК</a> "
    bot.send_message(message.from_user.id, info, parse_mode="html")


def activate_admin(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    manager = types.KeyboardButton("Я менеджер")
    admin = types.KeyboardButton("Я администратор")
    home = types.KeyboardButton("⏺В главное меню")
    keyboard.row(admin, manager)
    keyboard.row(home)
    bot.send_message(message.chat.id, "Какой твой уровень доступа", reply_markup=keyboard)
    bot.register_next_step_handler(message, who_you)


def who_you(message):
    if not select_admin("_id", "admin", f"user_id = {message.from_user.id}"):
        bot.send_message(message.from_user.id, "Я тебя не знаю")
        cmd_start(message)
    elif message.text == "Отмена":
        activate_admin(message)
    elif message.text == "⏺В главное меню":
        accept_message(message)
    elif "Я" in message.text:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Отмена"))
        if "админ" in message.text:
            bot.send_message(message.chat.id, "Введи пароль от панели администратора", reply_markup=markup)
            redactor.type = "admin"
        elif "менеджер" in message.text:
            bot.send_message(message.chat.id, "Введи пароль менеджера", reply_markup=markup)
            redactor.type = "manager"
        redactor.operation = "password"

        bot.register_next_step_handler(message, who_you)
    else:
        if redactor.type != "user":
            if redactor.operation == "password":
                if hash_func(message.from_user.id, message.text, "==") and \
                        select_admin("type", "admin", whereis=f"user_id = {message.from_user.id}")[0][
                            0] == redactor.type:
                    redactor.operation = "show"
                    super_menu(message)
                else:
                    bot.send_message(message.from_user.id, "Не правильно")
                    redactor.operation = "no"
                    redactor.type = "user"
                    who_you(message)
        else:
            activate_admin(message)


def super_menu(message):
    buttons = []
    if redactor.type == "admin":
        buttons = ["Каталог", "Информация", "+ менеджер", "- менеджер", "Изменить пароль", "Передать права"]
    elif redactor.type == "manager":
        buttons = ["Каталог", "Информация"]
    if redactor.operation == "show":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for i in list(range(len(buttons)))[::2]:
            markup.row(types.KeyboardButton(buttons[i]), types.KeyboardButton(buttons[i + 1]))
        bot.send_message(message.from_user.id, "Привет\nВыбирай что изменить", reply_markup=markup)
        bot.register_next_step_handler(message, super_menu)
        redactor.operation = "edit"
    elif redactor.operation == "edit":
        if message.text in buttons:
            if message.text == buttons[0]:
                global user_road
                user_road = ["1"]
                do_order(message)
            elif message.text == buttons[1]:
                pass
            elif len(buttons) > 2:
                if message.text == buttons[2]:
                    pass
                elif message.text == buttons[3]:
                    pass
                elif message.text == buttons[4]:
                    pass
                elif message.text == buttons[5]:
                    pass
            else:
                bot.send_message(message.from_user.id, "Команда не понятна\nДля кого кнопки сделаны?????")


def edit_profile(message):
    buttons = [["ФИО", "Телефон"], ["Город", "Адрес"]]

    dictionary = var = {"ФИО": ["Введите свои ФИО"], "Адрес": ["Введите адрес"], "Город": [
        "Введите название города"], "Телефон": ["Введите номер телефона"]}
    if message.text in list(dictionary.keys()):
        global last_bot_text
        last_bot_text = dictionary[message.text][0]
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton("Назад"))
        bot.send_message(
            message.chat.id, dictionary[message.text][0], reply_markup=markup)
        bot.register_next_step_handler(message, edit_cat_profile)
    elif message.text == "👩‍🦽 Профиль":
        show_profile(message)
    else:
        show_profile(message)
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        for i in buttons:
            markup.add(types.KeyboardButton(text=i[0]), types.KeyboardButton(text=i[1]))
        markup.add("👩‍🦽 Профиль")
        bot.send_message(message.chat.id, "Выберете что изменить",
                         parse_mode="html", reply_markup=markup)
        bot.register_next_step_handler(message, edit_profile)


last_bot_text = ""


def edit_cat_profile(message):
    global last_bot_text
    if message.text != "Назад":
        data_to_db = {"Введите свои ФИО": "fio", "Введите номер телефона": "phone",
                      "Введите название города": "city", "Введите адрес": "address"}
        cursor.execute(
            f"""UPDATE clients SET {data_to_db[last_bot_text]} = '{message.text}' WHERE user_id = {message.chat.id};""")
        db.commit()
        edit_profile(message)
    else:
        edit_profile(message)


def show_profile(message):
    profile = select_db(
        "*", "clients", f"user_id = '{message.chat.id}'")
    fio = profile[0][3] if profile[0][3] is not None else "<code>не указано</code>"
    phone_number = profile[0][4] if profile[0][4] is not None else "<code>не указан</code>"
    city = profile[0][5] if profile[0][5] is not None else "<code>не указан</code>"
    address = profile[0][6] if profile[0][6] is not None else "<code>не указан</code>"
    text = f"""ФИО: {fio}\nНомер : {phone_number}\nГород : {city}\nАдрес : {address}"""
    keyboarding = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboarding.add(types.KeyboardButton(
        text="Редактировать профиль"), types.KeyboardButton(text="⏺В главное меню"))
    bot.send_message(message.chat.id, text, parse_mode="html",
                     reply_markup=keyboarding)


def show_basket(message):
    global show_product_id
    basket = select_db("*", "baskets", f"user_id = {message.from_user.id}")
    minimum = 1
    max_id = len(basket)
    if not basket:
        keyboarder = types.ReplyKeyboardMarkup(
            row_width=2, resize_keyboard=True)
        first_button = types.KeyboardButton(text="📁 Каталог")
        keyboarder.add(first_button)
        bot.send_message(message.from_user.id,
                         "В вашей корзине пусто!", reply_markup=keyboarder)

    if minimum <= show_product_id <= max_id:
        check_and_delete(message)
        aboutproduct = select_db(
            "*", "product", f"_id = {basket[show_product_id - 1][2]}")

        name_parents_category_for_this_product = select_db(
            "title", "categories", f"_id = {aboutproduct[0][5]}")

        name_cat_pr = name_parents_category_for_this_product[0][0] + " -> " + str(
            aboutproduct[0][1])

        markup = types.InlineKeyboardMarkup(row_width=1)

        summ = 0
        for i in basket:
            summ += i[3] * select_db("*", "product", f"_id = {i[2]}")[0][3]

        caption = f"Название:\n{name_cat_pr}\nКол - во : {basket[show_product_id - 1][3]} шт.\n\n{aboutproduct[0][3]} * {basket[show_product_id - 1][3]} = {aboutproduct[0][3] * basket[show_product_id - 1][3]} "

        img = open(aboutproduct[0][4], 'rb')
        bot.send_photo(message.chat.id, img, caption, reply_markup=button_basket(summ, show_product_id, basket))
    elif show_product_id > max_id:
        show_product_id = minimum

    elif show_product_id < minimum:
        show_product_id = max_id

    # bot.send_message(message.chat.id, text=text)


def button_basket(summ, show_product_id, basket):
    clear = types.InlineKeyboardButton(
        '✖️', callback_data='basket_clear')
    remove = types.InlineKeyboardButton(
        '➖', callback_data='basket_remove')
    add = types.InlineKeyboardButton(
        '➕', callback_data='basket_add')

    previous = types.InlineKeyboardButton(
        '◀️', callback_data='basket_previous')
    from_is = types.InlineKeyboardButton(
        f'{show_product_id} / {len(basket)}', callback_data='a')
    next = types.InlineKeyboardButton(
        '▶️', callback_data='basket_next')
    markup = types.InlineKeyboardMarkup(row_width=1)
    complete = types.InlineKeyboardButton(
        f'Сделать заказ на {summ} ₽', callback_data='complete')
    additionally = types.InlineKeyboardButton(
        'Добавить ещё товар', callback_data='additionally')

    markup.row(clear, remove, add)
    markup.row(previous, from_is, next)
    markup.row(complete)
    markup.row(additionally)
    return markup


try:
    def edit_basket(user_id, id_parents_categories, id_product, what_do):
        global last_product
        title = last_product
        if id_product == 0:
            id_product = return_one_value(
                select_db("_id", "product",
                          "title = '{}' AND id_categories = '{}'".format(title, id_parents_categories)))
        select_amount = return_one_value(
            select_db("amount", "baskets", f"""product_id = {id_product} AND user_id = {user_id}"""))
        if select_amount is None:
            insert_db("baskets", None, user_id, id_product, 1)
        else:
            amount = select_amount
            if what_do != "x":
                if what_do == "+":
                    amount += 1
                elif what_do == "-":
                    amount -= 1
                update_db("baskets", "amount", amount, f"product_id = {id_product} AND user_id = {user_id};")
                if amount <= 0:
                    cursor.execute(
                        f"""DELETE FROM baskets WHERE product_id = {id_product} AND user_id = {user_id};""")
                    db.commit()

            else:
                cursor.execute(
                    f"""DELETE FROM baskets WHERE product_id = {id_product} AND user_id = {user_id};""")
                db.commit()
except Exception:
    pass


@bot.callback_query_handler(func=lambda call: True)
def data(call):
    if call.message:
        global user_road, keyboarding
    if "me" in call.data:
        pass
    elif call.data == "add":
        edit_basket(call.message.chat.id, int(user_road[-1]), 0, "+")

        global last_product
        title = last_product

        markup = types.InlineKeyboardMarkup(row_width=1)

        item3 = types.InlineKeyboardButton(
            "Добавить в корзину (+1)", callback_data="add")
        item2 = types.InlineKeyboardButton(
            "🛍 Корзина", callback_data="go to basket")
        markup.add(item2, item3)
        id_product = return_one_value(
            select_db("_id", "product",
                      f"""title = '{title}' AND id_categories = {int(user_road[-1])}"""))
        amount = return_one_value(select_db(
            "amount", "baskets", f"""product_id = {id_product} AND user_id = {call.message.chat.id}"""))
        all_about_product = []
        for i in select_db("*", "product", "title = '{}' AND id_categories = '{}'".format(title,
                                                                                          int(
                                                                                              user_road[
                                                                                                  -1]))):
            all_about_product = list(i)
        text = """Название: {}\nЦена: {} ₽\nОписание:\n{}\n\nКол-во в корзине: {}""".format(
            all_about_product[1], all_about_product[3], all_about_product[2], amount)
        bot.edit_message_caption(
            chat_id=call.message.chat.id, message_id=call.message.id, caption=text, reply_markup=markup)

    elif "basket" in call.data:
        global show_product_id
        basket = select_db(
            "*", "baskets", f"user_id = {call.message.chat.id}")
        minimum_id = 1
        max_id = len(basket)
        if "next" in call.data:
            show_product_id += 1

        elif "previous" in call.data:
            show_product_id -= 1

        if show_product_id < minimum_id:
            show_product_id = max_id
        elif show_product_id > max_id:
            show_product_id = minimum_id

        basket = select_db(
            "*", "baskets", f"user_id = {call.message.chat.id}")
        if basket:
            about_product = select_db(
                "*", "product", f"_id = {basket[show_product_id - 1][2]}")
        minimum_id = 1
        max_id = len(basket)

        basket = select_db("*", "baskets", f"user_id = {call.message.chat.id}")
        basket_ar(basket, call.message)
        if "add" in call.data:
            edit_basket(call.message.chat.id, 0, about_product[0][0], "+")
        elif "remove" in call.data:
            edit_basket(call.message.chat.id, 0, about_product[0][0], "-")
        elif "clear" in call.data:
            edit_basket(call.message.chat.id, 0, about_product[0][0], "x")

        basket = select_db(
            "*", "baskets", f"user_id = {call.message.chat.id}")
        max_id = len(basket)
        basket_ar(basket, call.message)
        if show_product_id < minimum_id:
            show_product_id = max_id
        elif show_product_id > max_id:
            show_product_id = minimum_id

        if minimum_id <= show_product_id <= max_id:
            about_product = select_db(
                "*", "product", f"_id = {basket[show_product_id - 1][2]}")
            name_parents_category_for_this_product = select_db(
                "title", "categories", f"_id = {about_product[0][5]}")

            name_cat_pr = name_parents_category_for_this_product[0][0] + " -> " + str(
                about_product[0][1])

            summ = 0
            for i in basket:
                summ += i[3] * select_db(
                    "*", "product", f"_id = {i[2]}")[0][3]

            caption = f"Название:\n{name_cat_pr}\nКол - во : {basket[show_product_id - 1][3]} шт.\n\n{about_product[0][3]} * {basket[show_product_id - 1][3]} = {about_product[0][3] * basket[show_product_id - 1][3]}"

            new_photo = open(about_product[0][4], 'rb')
            if caption != call.message.caption:
                bot.edit_message_media(
                    media=types.InputMedia(type='photo', media=new_photo, caption=caption),
                    chat_id=call.message.chat.id, message_id=call.message.message_id,
                    reply_markup=button_basket(summ, show_product_id, basket))

    elif call.data == "go to basket":
        show_basket(call.message)

    elif call.data == "complete":
        if None not in select_db("*", "clients", whereis=f"user_id = {call.message.chat.id}")[0][2:]:
            basket = select_db(
                "*", "baskets", f"user_id = {call.message.chat.id}")
            user_basket = ""
            all = 0
            for i in basket:
                about_product = select_db(
                    "*", "product", f"_id = {i[2]}")
                name_parents_category_product = select_db(
                    "title", whereis=f"_id = {about_product[0][5]}")
                price = about_product[0][3] * i[3]
                all += price
                h = f"<code>{i[3]}</code> X <code>{name_parents_category_product[0][0]} -> {about_product[0][1]}</code>\nСтоимость: <code>{price} ₽</code>\n\n"
                user_basket += h
            user_basket += f"<b>Всего: {all} ₽</b>"
            clients = select_db(
                "*", "clients", whereis=f"user_id = {call.message.chat.id}")[0][2:]
            username = "@" + clients[0]
            message_order = f"<b>Ссылка на пользователя</b>: {username}\n<b>ФИО</b>: <i>{clients[1]}</i>\n<b>Город</b>: <i>{clients[3]}</i>\n<b>Адрес</b>: <i>{clients[4]}</i>\n<b>Номер телефона</b>: <i>{clients[2]}</i>\n\n<b>Заказ: </b>\n" + user_basket

            from manager_bot import send_order
            send_order(message_order)
            new_photo = open("photo/complete.png", 'rb')
            markup = types.ReplyKeyboardMarkup(
                row_width=2, resize_keyboard=True)
            markup.add(types.KeyboardButton(text="⏺В главное меню"))
            bot.edit_message_media(media=types.InputMedia(type='photo', media=new_photo,
                                                          caption="Заказ оформлен, скоро с вами свяжется менеджер "
                                                                  "для отправки вам кода отслеживания"),
                                   chat_id=call.message.chat.id,
                                   message_id=call.message.message_id)  # , reply_markup=markup)
            tablename = "user_" + str(call.message.chat.id)
            cursor.execute(f"""DELETE FROM baskets WHERE user_id={call.message.chat.id}""")
            db.commit()
            # bot.send_message(call.message.chat.id, "Заказ оформлен, скоро с вами свяжется менеджер для отправки вам кода отслеживания")
        else:
            markup = types.ReplyKeyboardMarkup(
                row_width=2, resize_keyboard=True)
            markup.add(types.KeyboardButton(text="Заполнить профиль"))
            bot.send_message(
                call.message.chat.id, "Чтобы сделать заказ заполниете профиль в главном меню", reply_markup=markup)

    elif call.data == "additionally":
        keyboarding = types.ReplyKeyboardMarkup(
            row_width=2, resize_keyboard=True)
        first_button = types.KeyboardButton(text="📁 Каталог")
        keyboarding.add(first_button)
        bot.send_message(call.message.chat.id,
                         "Тогда давай сначала", reply_markup=keyboarding)


def basket_ar(basket, message):
    if not basket:
        keyboarding = types.ReplyKeyboardMarkup(
            row_width=2, resize_keyboard=True)
        first_button = types.KeyboardButton(text="📁 Каталог")
        keyboarding.add(first_button)
        bot.delete_message(message.chat.id,
                           message.message_id)
        bot.send_message(
            message.chat.id, "В вашей корзине <b>пусто</b> !", reply_markup=keyboarding, parse_mode="html")
        return


def show_product(message):
    _list = ["Добавить\nкатегорию", "Добавить\nтовар", "Добавить\nтовар", "Изменить\nтовар", "Удалить\nтовар"]
    global user_road
    user_category = int(user_road[-1])
    list_for_check = product(user_category=user_category)
    if message.text in list_for_check:
        global last_product

        # last_message.append(message.message_id + 1)
        check_and_delete(message)
        last_product = message.text

        all_about_product = []
        for i in select_db("*", "product",
                           "title = '{}' AND id_categories = '{}'".format(message.text, user_category)):
            # bot.send_message(message.from_user.id, "Нажимай пожалуйста на кнопки, а то я непойму =)")
            all_about_product = list(i)
        img = open(all_about_product[4], 'rb')
        id_product = return_one_value(
            select_db("_id", "product", "title = '{}' AND id_categories = '{}'".format(
                message.text, int(user_road[-1]))))
        amount_product = return_one_value(select_db(
            "amount", "baskets", f"""product_id = {id_product} AND user_id = {message.from_user.id}"""))

        if amount_product is not None:
            pass
        else:
            amount_product = 0
        caption = """Название: {}\nЦена: {} ₽\nОписание:\n{}\n\nКол-во в корзине: {}""".format(
            all_about_product[1], all_about_product[3], all_about_product[2], amount_product)

        markup = types.InlineKeyboardMarkup(row_width=1)
        item3 = types.InlineKeyboardButton(
            "Добавить в корзину (+1)", callback_data="add")
        item2 = types.InlineKeyboardButton(
            "🛍 Корзина", callback_data="go to basket")
        markup.add(item2, item3)
        text = "Выбирай категорию"
        bot.send_photo(message.from_user.id, img, caption, reply_markup=markup)
        bot.register_next_step_handler(message, show_product)
    elif message.text in _list:
        global product_data
        if message.text == "Добавить\nкатегорию":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Отмена")
            bot.send_message(message.from_user.id, "Введи название дириктории :", reply_markup=markup)
            bot.register_next_step_handler(message, add_category)
        elif message.text == "Добавить\nтовар":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Отмена")

            product_data["do"] = "title"
            bot.send_message(message.from_user.id, "Введи название продукта :", reply_markup=markup)
            bot.register_next_step_handler(message, add_product)
            # bot.register_next_step_handler(message, add_product)
        elif message.text == "Изменить\nтовар":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Отмена")
            text = "Введите номер чтобы изменить: "
            for i in list_for_check:
                _str = f"\n>> {list_for_check.index(i) + 1} << - {i}"
                text += _str
            product_data["do"] = "define_id"
            bot.send_message(message.from_user.id, text, reply_markup=markup)
            bot.register_next_step_handler(message, edit_product)
        elif message.text == "Удалить\nтовар":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Отмена")
            text = "Введите номер чтобы изменить: "
            for i in list_for_check:
                _str = f"\n>> {list_for_check.index(i) + 1} << - {i}"
                text += _str
            product_data["do"] = "define_id"
            bot.send_message(message.from_user.id, text, reply_markup=markup)
            bot.register_next_step_handler(message, delete_product)
    else:
        accept_message(message)


def delete_product(message):
    global product_data
    if product_data["do"] == "define_id":
        try:
            _list = product(int(user_road[-1]))
            if 0 < int(message.text) <= len(_list):
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                edit_id = select_db("_id", "product", f"id_categories = {int(user_road[-1])} AND nodelete = 1")[
                    abs(int(message.text)) - 1][0]
                update_db("product", "nodelete", 0, f"_id = {edit_id}")
                product_data["do"] = "none"
                do_order(message)
        except Exception as e:
            do_order(message)


def edit_product(message):
    if redactor.type != "user":
        global product_data
        parts_list = ["Название", "Описание", "Цена", "Фотография"]
        if product_data["do"] == "define_id":
            try:
                _list = product(int(user_road[-1]))
                if 0 < int(message.text) <= len(_list):
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                    for i in list(range(len(parts_list)))[::2]:
                        markup.add(parts_list[i], parts_list[i + 1])
                    edit_id = select_db("_id", "product", f"id_categories = {int(user_road[-1])} AND nodelete = 1")[
                        abs(int(message.text)) - 1][0]
                    # edit_id = _list[int(message.text) - 1]
                    print(_list, edit_id)
                    product_data["id"] = edit_id
                    product_data["do"] = "none"
                    bot.send_message(message.from_user.id, "Выбери что изменить", reply_markup=markup)
                    bot.register_next_step_handler(message, edit_product)
                else:
                    do_order(message)
            except Exception as e:
                print(e)
                do_order(message)
        elif message.text == "Отмена":
            do_order(message)
        elif message.text in parts_list:
            markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            markup.add("Отмена")
            if message.text == "Название":
                product_data["do"] = "edit_name"
                bot.send_message(message.from_user.id, "Введи новое название", reply_markup=markup)
            elif message.text == "Описание":
                product_data["do"] = "edit_about"
                bot.send_message(message.from_user.id, "Введи новое описание", reply_markup=markup)
            elif message.text == "Цена":
                product_data["do"] = "edit_price"
                bot.send_message(message.from_user.id, "Введи новую цену", reply_markup=markup)
            elif message.text == "Фотография":
                product_data["do"] = "edit_photo"
                bot.send_message(message.from_user.id, "Отправь новое фото", reply_markup=markup)
            bot.register_next_step_handler(message, edit_product)
        elif product_data["do"] in ["edit_name", "edit_photo", "edit_price", "edit_about"]:
            do = product_data["do"]
            if do == "edit_name":
                product_data["title"] = message.text
                print(product_data["title"])
                update_db("product", "title", f'"{message.text}"', f"_id = {product_data['id']}")
                do_order(message)
            elif do == "edit_about":
                product_data["about"] = message.text
                update_db("product", "about", f'"{message.text}"', f"_id = {product_data['id']}")
                do_order(message)
            elif do == "edit_price":
                try:
                    product_data["price"] = int(message.text)
                    update_db("product", "price", product_data["price"], f"_id = {product_data['id']}")
                    do_order(message)
                except Exception:
                    bot.send_message(message.from_user.id, "ВВЕДИ ЕЩЁ РАЗ (должно быть просто число)")
                    bot.register_next_step_handler(message, edit_product)
            elif do == "edit_photo":
                try:
                    file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
                    downloaded_file = bot.download_file(file_info.file_path)
                    src = 'photo/' + generate_name("filename") + ".jpg"
                    with open(src, 'wb') as new_file:
                        new_file.write(downloaded_file)
                    product_data["photo_src"] = src
                    update_db("product", "photo_src", f"'{src}'", f"_id = {product_data['id']}")
                    do_order(message)
                except TypeError:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add("Отмена")
                    img = open("photo/send_photo.png", 'rb')
                    product_data["do"] = "edit_photo"
                    bot.send_photo(message.from_user.id, img, "Отправь повторно, сделав как на картинке",
                                   reply_markup=markup)
                    bot.register_next_step_handler(message, edit_product)

    else:
        do_order(message)


def add_product(message):
    global product_data
    try:
        if message.text.lower() != "отмена":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Отмена")
            if product_data["do"] == "title":
                product_data["title"] = message.text
                product_data["do"] = "about"
                bot.send_message(message.from_user.id, "Введи описание продукта :", reply_markup=markup)
                bot.register_next_step_handler(message, add_product)
            elif product_data["do"] == "about":
                product_data["about"] = message.text
                product_data["do"] = "price"
                bot.send_message(message.from_user.id, "Введи цену продукта :", reply_markup=markup)
                bot.register_next_step_handler(message, add_product)
            elif product_data["do"] == "price":
                try:
                    product_data["price"] = int(message.text)
                    product_data["do"] = "photo_src"
                    bot.send_message(message.from_user.id, "Отправь фото продукта", reply_markup=markup)
                    bot.register_next_step_handler(message, add_product)
                except Exception:
                    product_data["do"] = "price"
                    bot.send_message(message.from_user.id,
                                     "Введи повторно цену продукта\n<code>Скорее всего ты ввёл не число</code>",
                                     reply_markup=markup, parse_mode="html")
                    bot.register_next_step_handler(message, add_product)


        else:
            do_order(message)
    except AttributeError:
        try:
            if product_data["do"] == "photo_src":
                file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                src = 'photo/' + generate_name("filename") + ".jpg"
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file)
                product_data["photo_src"] = src
                insert_db("product", None, product_data["title"], product_data["about"], product_data["price"],
                          product_data["photo_src"], int(user_road[-1]), 1)
                do_order(message)
        except TypeError:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Отмена")
            img = open("photo/send_photo.png", 'rb')
            product_data["do"] = "photo_src"
            bot.send_photo(message.from_user.id, img, "Отправь повторно, сделав как на картинке", reply_markup=markup)
            bot.register_next_step_handler(message, add_product)


def add_category(message):
    if message.text != "Отмена":
        global user_road
        insert_db("categories", None, message.text, 1, int(user_road[-1]))
        do_order(message)
    else:
        do_order(message)


# требуется только для переименовки дирикторий
id_cat = 0

# требуется только для редактирования продуктов
product_data = {
    "do": "none",
    "title": "",
    "about": "",
    "price": 0,
    "photo_src": "",
    "id": 0
}


def rename_category(message):
    try:
        global user_road
        global id_cat
        id_cat = select_db("_id", "categories", f"parents_categories = {int(user_road[-1])} AND nodelete = 1")[
            int(message.text) - 1][0]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Отмена")
        bot.send_message(message.from_user.id, "Введи новое название", reply_markup=markup)
        bot.register_next_step_handler(message, update_name_cat)
    except Exception as e:
        do_order(message)


def update_name_cat(message):
    if message.text != "Отмена":
        global id_cat
        update_db("categories", "title", f"'{message.text}'", f"_id = {id_cat}")
        do_order(message)
    else:
        do_order(message)


def delete_category(message):
    try:
        global user_road
        id_cat = select_db("_id", "categories", f"parents_categories = {int(user_road[-1])} AND nodelete = 1")[
            abs(int(message.text)) - 1][0]
        # cursor.execute(f"""DELETE FROM categories where _id = {id_cat}""")
        update_db("categories", "nodelete", 0, f"_id = {id_cat}")
        do_order(message)
    except Exception as e:
        do_order(message)


def next_category(message):
    global user_road
    user_category = int(user_road[-1])
    if categories(user_category):
        list_fo_check = categories(user_category)
        if int(sum_element_in_list(user_road)) < 2:
            list_fo_check.append("📁 Каталог")
        if message.text in list_fo_check:
            user_category = int(user_road[-1])
            user_road.append(str(return_one_value(select_db(
                "_id", "categories",
                "title = '{}' AND parents_categories = '{}'".format(message.text, user_category)))))
            do_order(message)
        elif message.text.lower() == "< назад" or message.text.lower() == "⏺в главное меню":
            accept_message(message)
        elif redactor.type != "user":
            if message.text == "Добавить\nкатегорию":
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add("Отмена")
                bot.send_message(message.chat.id, "Введите название категории", reply_markup=markup)
                bot.register_next_step_handler(message, add_category)
            elif message.text == "Переименовать\nкатегорию":
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add("Отмена")
                text = "Введите номер чтобы переименовать: "
                for i in list_fo_check[:-1]:
                    _str = f"\n>> {list_fo_check.index(i) + 1} << - {i}"
                    text += _str
                bot.send_message(message.from_user.id, text, reply_markup=markup)
                bot.register_next_step_handler(message, rename_category)
            elif message.text == "Удалить\nкатегорию":
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add("Отмена")
                text = "Введите номер чтобы удалить: "
                if int(user_category) < 2:
                    list_fo_check = list_fo_check[:-1]
                for i in list_fo_check:
                    _str = f"\n<< {list_fo_check.index(i) + 1} >> - {i}"
                    text += _str
                bot.send_message(message.from_user.id, text, reply_markup=markup)
                bot.register_next_step_handler(message, delete_category)
        else:
            accept_message(message)


def do_order(message):
    global user_road
    try:
        user_category = int(user_road[-1])

        markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        if categories(user_category):
            for i in categories(user_category):
                button_name = types.KeyboardButton(i)
                markup.add(button_name)
            if int(sum_element_in_list(user_road)) > 1:
                markup.add("⏺В главное меню", "< Назад")
            else:
                markup.add("⏺В главное меню")
            if redactor.type != "user":
                markup.add("-" * 40)
                markup.add("Добавить\nкатегорию", "Переименовать\nкатегорию", "Удалить\nкатегорию")
            bot.send_message(
                message.from_user.id, "Отлично, нажимай на нужную категорию", reply_markup=markup)
            bot.register_next_step_handler(message, next_category)
        else:
            for i in product(user_category):
                button_name = types.KeyboardButton(i)
                markup.add(button_name)
            markup.add("⏺В главное меню", "< Назад")
            text = "Отлично, выбери продукт"
            if redactor.type != "user":
                markup.add("-" * 40)
                if not product(user_category):
                    markup.add("Добавить\nкатегорию", "Добавить\nтовар")
                    text = "В одну категорию можно добавить ТОЛЬКО КАТЕГОРИИ ЛИБО ТОЛЬКО ПРОДУКТЫ "
                else:
                    markup.add("Добавить\nтовар", "Изменить\nтовар", "Удалить\nтовар")
            else:
                if not product(user_category):
                    text = "Пока здесь ни товаров, ни категорий"
            bot.send_message(message.from_user.id,
                             text, reply_markup=markup)
            bot.register_next_step_handler(message, show_product)
    except IndexError:
        user_road = ["1"]
        cmd_start(message)


def check_and_delete(message):
    insert_db("for_delete_product", None, message.chat.id, message.message_id + 1)
    last_message = select_db("*", "for_delete_product", f"user_id = {message.chat.id}")
    if len(last_message) > 1:
        bot.delete_message(chat_id=last_message[0][1], message_id=last_message[0][2])
        cursor.execute(
            f"""DELETE FROM for_delete_product WHERE user_id = {last_message[0][1]} AND message_id = {last_message[0][2]}""")
        db.commit()


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
    delete_message()
