import random
import sqlite3

from certifi import where

connect = sqlite3.connect("shop.db", check_same_thread=False)
coursor = connect.cursor()

user_product = False

connect_user_basket = sqlite3.connect(
    "db/user_basket.db", check_same_thread=False)
coursor_user_basket = connect_user_basket.cursor()

connect_user_data = sqlite3.connect("db/user_data.db", check_same_thread=False)
coursor_user_data = connect_user_data.cursor()


def generate_name():
    # choose from all lowercase letter
    characters = """*!@#$%^&~`-_+={}[]()|:;"'?>.,< qwertyuiopasdfghjklzxcvbnm1234567890"""
    result_str = ''.join(random.choice(characters) for i in range(40))
    return result_str


def categories(user_category=1):
    coursor.execute("""
    SELECT title FROM categories WHERE nodelete = 1 AND parents_categories = {}
    ;""".format(user_category))
    list_categories = []
    for i in coursor.fetchall():
        for h in i:
            list_categories.append(h)
    # if list_categories == []:
    #     return product(user_category)

    # else:
    return list_categories


def product(user_category):
    coursor.execute("""
    SELECT title FROM product WHERE nodelete = 1 AND id_categories = {}
    ;""".format(user_category))
    list_product = []
    for i in coursor.fetchall():
        for h in i:
            list_product.append(h)
    global user_product
    user_product = True
    return list_product


def select_from_shop_db(whatis="*", fromis="categories", whereis=''):
    coursor.execute("""SELECT {} FROM '{}' WHERE {};""".format(
        whatis, fromis, whereis))
    return coursor.fetchall()


def select_from_user_basket_db(whatis="*", fromis="user_basket", whereis=''):
    if whereis == "":
        coursor_user_basket.execute(
            """SELECT {} FROM '{}';""".format(whatis, fromis))
    else:
        coursor_user_basket.execute(
            """SELECT {} FROM '{}' WHERE {};""".format(whatis, fromis, whereis))
    return coursor_user_basket.fetchall()


def insert_to_user_basket_db(name_table, *values_for_paste):
    amount_values = len(values_for_paste)
    _vars = ("? ," * amount_values)[:-2]
    coursor_user_basket.execute(
        f"""INSERT INTO {name_table} VALUES({_vars});""", values_for_paste)
    connect_user_basket.commit()


def update_to_user_basket_db(name_table, column, value, whereis):
    coursor_user_basket.execute(
        f"""UPDATE {name_table} SET {column} = {value} WHERE {whereis};""")
    connect_user_basket.commit()


def create_basket(message):
    from datetime import datetime
    user_id = str(message.chat.id)
    username = message.from_user.username
    dt_created = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    title_for_table = "user_" + user_id

    coursor_user_basket.execute(f"""CREATE TABLE IF NOT EXISTS {title_for_table}(
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_product INTEGER,
        amount INTEGER
    );""")
    if select_from_user_basket_db("_id", "user_basket", "username = '{}'".format(username)) == []:
        coursor_user_basket.execute(
            f"""INSERT INTO user_basket VALUES(?, ?, ?, ?);""", (None, username, user_id, dt_created))
        connect_user_basket.commit()


def select_from_user_data_db(whatis="*", fromis="users_data", whereis=''):
    if whereis == "":
        coursor_user_data.execute(
            """SELECT {} FROM '{}';""".format(whatis, fromis))
    else:
        coursor_user_data.execute(
            """SELECT {} FROM '{}' WHERE {};""".format(whatis, fromis, whereis))
    return coursor_user_data.fetchall()


def return_one_value(t):
    for i in t:
        for l in i:
            return l


def sum_element_in_list(_list):
    _str = ""
    for i in _list:
        _str += i
    return _str
