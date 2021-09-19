from datetime import datetime
from os import name, write
from types import new_class
from typing import Counter, Text

import telebot
from telebot import types
from telebot.util import user_link


from dif_func import generate_name, categories, product, select_from_shop, insert_baskets, select_from_user_basket, return_one_value, update_baskets, sum_element_in_list, select_from_clients, create_basket
from message import message


from config import TOKEN
import sqlite3

bot = telebot.TeleBot(TOKEN)
db = sqlite3.connect("db/shop.db", check_same_thread=False)
cursor = db.cursor()

conBaskets = sqlite3.connect("db/baskets.db", check_same_thread=False)
curBaskets = conBaskets.cursor()

conUsers = sqlite3.connect("db/clients.db", check_same_thread=False)
curUsers = conUsers.cursor()

user_category = ["1"]
last_product = ""

id_edit_profile = 0

show_product_id = 1


@bot.message_handler(commands=['start', 'restart', 'help'])
def cmd_start(message):
    if message.from_user.first_name == None:
        first_name = ""
    else:
        first_name = message.from_user.first_name
    if message.from_user.last_name == None:
        last_name = ""
    else:
        last_name = message.from_user.last_name
    send_mess_help = "Помочь " + first_name + last_name + \
        "?\nНажми пожалуйста на кнопку ниже, ну или напиши : <code>📁 Каталог</code>"

    send_mess_start = "Привет " + first_name + last_name + \
        " 👋\nНажми пожалуйста на кнопку ниже, ну или напиши : <code>📁 Каталог</code>"
    keyboardmain = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    first_button = types.KeyboardButton(text="📁 Каталог")
    second_button = types.KeyboardButton(text="🛍 Корзина")
    third_button = types.KeyboardButton(text="👩‍🦽 Профиль")
    fourth_button = types.KeyboardButton(text="🅰️🅱️🅾️🅱️🅰️")
    keyboardmain.add(first_button, second_button, third_button, fourth_button)
    if message.text == "/start" or "/restart":
        user_id = str(message.chat.id)
        username = message.from_user.username

        create_basket(message)

        if select_from_clients_db("_id", "clients", f"user_name = '{username}'") == []:
            curUsers.execute("""INSERT INTO clients VALUES(?, ?, ?, ?, ?, ?, ?);""",
                             (None, user_id, username, None, None, None, None))
            conUsers.commit()
    text = ""
    if message.text == "/start" or message.text == "/restart":
        text = send_mess_start
    elif message.text == "/help":
        text = send_mess_help
    else:
        text = "Ну чтож продолжим"
    bot.send_message(message.from_user.id, text,
                     reply_markup=keyboardmain, parse_mode='html')


@bot.message_handler(content_types=["text"])
def аccept_message(message):
    print(message)
    global user_category
    if message.text == "📁 Каталог":
        user_category = ["1"]
        do_order(message)
    elif message.text == "⏺В главное меню":
        user_category = ["1"]
        cmd_start(message)
    elif message.text == "< Назад":
        user_category = user_category[:-1]
        do_order(message)
    elif message.text == "🛍 Корзина":
        show_basket(message)
    elif message.text == "👩‍🦽 Профиль" or message.text == "Заполнить профиль":
        show_profile(message)
    elif message.text == "Редактировать профиль":
        edit_profile(message)
    elif message.text == "/start" or message.text == "/restart" or message.text == "/help":
        cmd_start(message)
    else:
        bot.send_message(
            message.from_user.id, "Походу меня только что исправили, но сейчас уже всё ок")
        user_category = ["1"]
        cmd_start(message)


def edit_profile(message):
    buttons = ["ФИО", "Телефон", "Город", "Адрес"]
    data = {"ФИО": ["Введите свои ФИО"], "Адрес": ["Введите адрес"], "Город": [
        "Введите название города"], "Телефон": ["Введите номер телефона"]}
    if message.text in list(data.keys()):
        global last_bot_text
        last_bot_text = data[message.text][0]
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(types.KeyboardButton("Назад"))
        bot.send_message(
            message.chat.id, data[message.text][0], reply_markup=markup)
        bot.register_next_step_handler(message, edit_yaitsa)
    elif message.text == "👩‍🦽 Профиль":
        show_profile(message)
    # if message.text in ["Редактировать профиль","Назад"]:
    else:
        show_profile(message)
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        for i in buttons:
            markup.add(types.KeyboardButton(text=i))
        markup.add("👩‍🦽 Профиль")
        bot.send_message(message.chat.id, "Выберете что изменить",
                         parse_mode="html", reply_markup=markup)
        bot.register_next_step_handler(message, edit_profile)


last_bot_text = ""


def edit_yaitsa(message):
    global last_bot_text
    # data = {"ФИО":["Введите имя"], "Адрес": ["Введите адрес"], "Город":["Введите название города"], "Телефон":["Введите номер телефона"]}
    if message.text != "Назад":
        data_to_db = {"Введите свои ФИО": "fio", "Введите номер телефона": "phone_number",
                      "Введите название города": "city", "Введите адрес": "address"}
        curUsers.execute(
            f"""UPDATE clients SET {data_to_db[last_bot_text]} = '{message.text}' WHERE user_id = {message.chat.id};""")
        conUsers.commit()
        # show_profile(message)
        edit_profile(message)
    else:
        edit_profile(message)


def show_profile(message):
    profile = select_from_clients_db(
        "*", "clients", f"user_id = '{message.chat.id}'")
    fio = profile[0][3] if profile[0][3] != None else "<code>не указано</code>"
    phone_number = profile[0][4] if profile[0][4] != None else "<code>не указан</code>"
    city = profile[0][5] if profile[0][5] != None else "<code>не указан</code>"
    address = profile[0][6] if profile[0][6] != None else "<code>не указан</code>"
    text = f"""ФИО: {fio}\nНомер : {phone_number}\nГород : {city}\nАдрес : {address}"""
    keyboardmain = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboardmain.add(types.KeyboardButton(
        text="Редактировать профиль"), types.KeyboardButton(text="⏺В главное меню"))
    bot.send_message(message.chat.id, text, parse_mode="html",
                     reply_markup=keyboardmain)


def show_basket(message):

    global show_product_id
    basket = select_from_user_basket_db("*", f"user_{message.chat.id}")
    min_id = 1
    max_id = len(basket)
    if basket == []:
        keyboardmain = types.ReplyKeyboardMarkup(
            row_width=2, resize_keyboard=True)
        first_button = types.KeyboardButton(text="📁 Каталог")
        keyboardmain.add(first_button)
        bot.send_message(message.from_user.id,
                         "В вашей корзине пусто!", reply_markup=keyboardmain)

    if show_product_id >= min_id and show_product_id <= max_id:
        about_product = select_from_shop_db(
            "*", "product", f"_id = {basket[show_product_id - 1][1]}")

        name_parents_category_for_this_product = select_from_shop_db(
            "title", whereis=f"_id = {about_product[0][5]}")

        name_cat_pr = name_parents_category_for_this_product[0][0] + " -> " + str(
            about_product[0][1])

        markup = types.InlineKeyboardMarkup(row_width=1)
        clear = telebot.types.InlineKeyboardButton(
            '✖️', callback_data='basket_clear')
        remove = telebot.types.InlineKeyboardButton(
            '➖', callback_data='basket_remove')
        add = telebot.types.InlineKeyboardButton(
            '➕', callback_data='basket_add')

        previos = telebot.types.InlineKeyboardButton(
            '◀️', callback_data='basket_previos')
        from_is = telebot.types.InlineKeyboardButton(
            f'{show_product_id} / {len(basket)}', callback_data='a')
        next = telebot.types.InlineKeyboardButton(
            '▶️', callback_data='basket_next')

        summ = 0
        for i in basket:
            summ += i[2] * \
                select_from_shop_db("*", "product", f"_id = {i[1]}")[0][3]

        complite = telebot.types.InlineKeyboardButton(
            f'Сделать заказ на {summ} ₽', callback_data='complite')
        additionally = telebot.types.InlineKeyboardButton(
            'Добавить ещё товар', callback_data='additionally')

        markup.row(clear, remove, add)
        markup.row(previos, from_is, next)
        markup.row(complite)
        markup.row(additionally)
        caption = f"Название:\n{name_cat_pr}\nКол - во : {basket[show_product_id - 1][2]} шт.\n\n{about_product[0][3]} * {basket[show_product_id -1][2]} = {about_product[0][3] * basket[show_product_id - 1][2]}"

        img = open(about_product[0][4], 'rb')
        bot.send_photo(message.chat.id, img, caption, reply_markup=markup)
    elif show_product_id > max_id:
        show_product_id = min_id

    elif show_product_id < min_id:
        show_product_id = max_id

    # bot.send_message(message.chat.id, text=text)


def edit_basket(user_id, id_parents_categories, id_product, what_do):
    global last_product
    title = last_product
    if id_product == 0:
        id_product = return_one_value(select_from_shop_db(
            "_id", "product", "title = '{}' AND id_categories = '{}'".format(title, id_parents_categories)))
    select_amount = select_from_user_basket_db(
        "amount", "user_"+str(user_id), f"""id_product = {id_product}""")
    if select_amount == []:
        insert_baskets("user_"+str(user_id), None, id_product, 1)
    else:
        amount = return_one_value(select_amount)
        if what_do != "x":
            if what_do == "+":
                amount += 1
            elif what_do == "-":
                amount -= 1
            if amount <= 0:
                table_name = "user_"+str(user_id)
                curBaskets.execute(
                    f"DELETE FROM {table_name} WHERE id_product = {id_product}")
                conBaskets.commit()

            update_baskets("user_"+str(user_id), "amount",
                           amount, f"id_product = {id_product}")
        else:
            table_name = "user_"+str(user_id)
            curBaskets.execute(
                f"DELETE FROM {table_name} WHERE id_product = {id_product}")
            conBaskets.commit()


def next_category(message):
    global user_category
    use_user_category = int(sum_element_in_list(user_category)[-1])
    if categories(use_user_category) != []:
        list_fo_check = categories(use_user_category)
        if int(sum_element_in_list(user_category)) < 2:
            list_fo_check.append("📁 Каталог")
        if message.text in list_fo_check:
            use_user_category = int(sum_element_in_list(user_category)[-1])
            user_category.append(str(return_one_value(select_from_shop_db(
                "_id", "categories", "title = '{}' AND parents_categories = '{}'".format(message.text, use_user_category)))))
            do_order(message)
        else:
            аccept_message(message)


def show_product(message):
    if message.text != "< Назад" and message.text != "⏺В главное меню" and message.text != "Заполнить профиль":
        global user_category
        global last_product
        last_product = message.text

        use_user_category = int(sum_element_in_list(user_category)[-1])
        all_about_product = []
        for i in select_from_shop_db("*", "product", "title = '{}' AND id_categories = '{}'".format(message.text, use_user_category)):
            # bot.send_message(message.from_user.id, "Нажимай пожалуйста на кнопки, а то я непойму =)")
            all_about_product = list(i)
        img = open(all_about_product[4], 'rb')
        id_product = return_one_value(select_from_shop_db("_id", "product", "title = '{}' AND id_categories = '{}'".format(
            message.text, int(sum_element_in_list(user_category)[-1]))))
        amount_product = return_one_value(select_from_user_basket_db(
            "amount", "user_"+str(message.from_user.id), f"""id_product = {id_product}"""))

        if amount_product != None:
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
        bot.send_photo(message.from_user.id, img, caption, reply_markup=markup)
        bot.register_next_step_handler(message, show_product)
    else:
        аccept_message(message)


@bot.callback_query_handler(func=lambda call: True)
def data(call):
    if call.message:
        global user_category
        if call.data == "add":
            edit_basket(call.message.chat.id, int(
                sum_element_in_list(user_category)[-1]), 0, "+")

            global last_product
            title = last_product

            markup = types.InlineKeyboardMarkup(row_width=1)

            item3 = types.InlineKeyboardButton(
                "Добавить в корзину (+1)", callback_data="add")
            item2 = types.InlineKeyboardButton(
                "🛍 Корзина", callback_data="go to basket")
            markup.add(item2, item3)
            id_product = return_one_value(select_from_shop_db("_id", "product", "title = '{}' AND id_categories = '{}'".format(
                title, int(sum_element_in_list(user_category)[-1]))))
            amount = return_one_value(select_from_user_basket_db(
                "amount", "user_"+str(call.message.chat.id), f"""id_product = {id_product}"""))
            all_about_product = []
            for i in select_from_shop_db("*", "product", "title = '{}' AND id_categories = '{}'".format(title, int(sum_element_in_list(user_category)[-1]))):
                all_about_product = list(i)
            text = """Название: {}\nЦена: {} ₽\nОписание:\n{}\n\nКол-во в корзине: {}""".format(
                all_about_product[1], all_about_product[3], all_about_product[2], amount)
            bot.edit_message_caption(
                chat_id=call.message.chat.id, message_id=call.message.id, caption=text, reply_markup=markup)

        elif "basket" in call.data:
            global show_product_id
            basket = select_from_user_basket_db(
                "*", f"user_{call.message.chat.id}")
            min_id = 1
            max_id = len(basket)
            if "next" in call.data:
                show_product_id += 1

            elif "previos" in call.data:
                show_product_id -= 1

            if show_product_id < min_id:
                show_product_id = max_id
            elif show_product_id > max_id:
                show_product_id = min_id

            basket = select_from_user_basket_db(
                "*", f"user_{call.message.chat.id}")
            if basket != []:
                about_product = select_from_shop_db(
                    "*", "product", f"_id = {basket[show_product_id - 1][1]}")
            min_id = 1
            max_id = len(basket)

            basket = select_from_user_basket_db(
                "*", f"user_{call.message.chat.id}")
            if basket == []:
                keyboardmain = types.ReplyKeyboardMarkup(
                    row_width=2, resize_keyboard=True)
                first_button = types.KeyboardButton(text="📁 Каталог")
                keyboardmain.add(first_button)
                bot.delete_message(call.message.chat.id,
                                   call.message.message_id)
                bot.send_message(
                    call.message.chat.id, "В вашей корзине **пусто** !", reply_markup=keyboardmain)
                return
            if "add" in call.data:
                edit_basket(call.message.chat.id, 0, about_product[0][0], "+")
            elif "remove" in call.data:
                edit_basket(call.message.chat.id, 0, about_product[0][0], "-")
            elif "clear" in call.data:
                edit_basket(call.message.chat.id, 0, about_product[0][0], "x")

            basket = select_from_user_basket_db(
                "*", f"user_{call.message.chat.id}")
            max_id = len(basket)
            if show_product_id < min_id:
                show_product_id = max_id
            elif show_product_id > max_id:
                show_product_id = min_id

            if show_product_id >= min_id and show_product_id <= max_id:
                about_product = select_from_shop_db(
                    "*", "product", f"_id = {basket[show_product_id - 1][1]}")

                name_parents_category_for_this_product = select_from_shop_db(
                    "title", whereis=f"_id = {about_product[0][5]}")

                name_cat_pr = name_parents_category_for_this_product[0][0] + " -> " + str(
                    about_product[0][1])

                markup = types.InlineKeyboardMarkup(row_width=1)
                clear = telebot.types.InlineKeyboardButton(
                    '✖️', callback_data='basket_clear')
                remove = telebot.types.InlineKeyboardButton(
                    '➖', callback_data='basket_remove')
                add = telebot.types.InlineKeyboardButton(
                    '➕', callback_data='basket_add')

                previos = telebot.types.InlineKeyboardButton(
                    '◀️', callback_data='basket_previos')
                from_is = telebot.types.InlineKeyboardButton(
                    f'{show_product_id} / {len(basket)}', callback_data='a')
                next = telebot.types.InlineKeyboardButton(
                    '▶️', callback_data='basket_next')

                summ = 0
                for i in basket:
                    summ += i[2] * \
                        select_from_shop_db(
                            "*", "product", f"_id = {i[1]}")[0][3]

                complite = telebot.types.InlineKeyboardButton(
                    f'Сделать заказ на {summ} ₽', callback_data='complite')
                additionally = telebot.types.InlineKeyboardButton(
                    'Добавить ещё товар', callback_data='additionally')

                markup.row(clear, remove, add)
                markup.row(previos, from_is, next)
                markup.row(complite)
                markup.row(additionally)
                caption = f"Название:\n{name_cat_pr}\nКол - во : {basket[show_product_id - 1][2]} шт.\n\n{about_product[0][3]} * {basket[show_product_id - 1][2]} = {about_product[0][3] * basket[show_product_id - 1][2]}"

                new_photo = open(about_product[0][4], 'rb')
                if caption != call.message.caption:
                    bot.edit_message_media(media=telebot.types.InputMedia(type='photo', media=new_photo, caption=caption),
                                           chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

        elif call.data == "go to basket":
            show_basket(call.message)

        elif call.data == "complite":
            if None not in select_from_clients_db("*", "clients", whereis=f"user_id = {call.message.chat.id}")[0][2:]:
                basket = select_from_user_basket_db(
                    "*", f"user_{call.message.chat.id}")
                user_basket = ""
                всего = 0
                for i in basket:
                    about_product = select_from_shop_db(
                        "*", "product", f"_id = {i[1]}")
                    name_parents_category_product = select_from_shop_db(
                        "title", whereis=f"_id = {about_product[0][5]}")
                    price = about_product[0][3] * i[2]
                    всего += price
                    h = f"<code>{i[2]}</code> * <code>{name_parents_category_product[0][0]} -> {about_product[0][1]}</code>\nСтоимость: <code>{price} ₽</code>\n\n"
                    user_basket += h
                user_basket += f"<b>Всего: {всего} ₽</b>"
                clients = select_from_clients_db(
                    "*", "clients", whereis=f"user_id = {call.message.chat.id}")[0][2:]
                username = "@" + clients[0]
                message_order = f"<b>Ссылка на пользователя</b>: {username}\n<b>ФИО</b>: <i>{clients[1]}</i>\n<b>Город</b>: <i>{clients[3]}</i>\n<b>Адрес</b>: <i>{clients[4]}</i>\n<b>Номер телефона</b>: <i>{clients[2]}</i>\n\n<b>Заказ: </b>\n" + user_basket

                bot.send_message(850731060, message_order,  parse_mode='html')
                new_photo = open("photo/complite.png", 'rb')
                markup = types.ReplyKeyboardMarkup(
                    row_width=2, resize_keyboard=True)
                markup.add(types.KeyboardButton(text="⏺В главное меню"))
                bot.edit_message_media(media=telebot.types.InputMedia(type='photo', media=new_photo, caption="Заказ оформлен, скоро с вами свяжется менеджер для отправки вам кода отслеживания"),
                                       chat_id=call.message.chat.id, message_id=call.message.message_id)  # , reply_markup=markup)
                tablename = "user_" + str(call.message.chat.id)
                curBaskets.execute(f"""DELETE FROM {tablename}""")
                conBaskets.commit()
                # bot.send_message(call.message.chat.id, "Заказ оформлен, скоро с вами свяжется менеджер для отправки вам кода отслеживания")
            else:
                markup = types.ReplyKeyboardMarkup(
                    row_width=2, resize_keyboard=True)
                markup.add(types.KeyboardButton(text="Заполнить профиль"))
                bot.send_message(
                    call.message.chat.id, "Чтобы сделать заказ заполниете профиль в главном меню", reply_markup=markup)

        elif call.data == "additionally":
            keyboardmain = types.ReplyKeyboardMarkup(
                row_width=2, resize_keyboard=True)
            first_button = types.KeyboardButton(text="📁 Каталог")
            keyboardmain.add(first_button)
            bot.send_message(call.message.chat.id,
                             "Тогда давай сначала", reply_markup=keyboardmain)


def do_order(message):
    global user_category
    try:
        use_user_category = int(sum_element_in_list(
            sum_element_in_list(user_category)[-1]))

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        if categories(use_user_category) != []:
            for i in categories(use_user_category):
                button_name = types.KeyboardButton(i)
                markup.add(button_name)
            if int(sum_element_in_list(user_category)) > 1:
                markup.add("⏺В главное меню", "< Назад")
            else:
                markup.add("⏺В главное меню")
            bot.send_message(
                message.from_user.id, "Отлично, нажимай на нужную категорию", reply_markup=markup)
            bot.register_next_step_handler(message, next_category)
        else:
            for i in product(use_user_category):
                button_name = types.KeyboardButton(i)
                markup.add(button_name)
            markup.add("⏺В главное меню", "< Назад")
            # markup.add("< Назад")
            bot.send_message(message.from_user.id,
                             "Отлично, выбери продукт", reply_markup=markup)
            bot.register_next_step_handler(message, show_product)
    except IndexError:
        user_category = ["1"]
        cmd_start(message)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
