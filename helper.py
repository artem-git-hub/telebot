import random
import sqlite3


db = sqlite3.connect("db/shop.db", check_same_thread=False)
cursor = db.cursor()

user_product = False


def generate_name():
    # choose from all lowercase letter
    characters = """*!@#$%^&~`-_+={}[]()|:;"'?>.,< qwertyuiopasdfghjklzxcvbnm1234567890"""
    result_str = ''.join(random.choice(characters) for el in range(40))
    return result_str


def categories(user_category=1):
    cursor.execute(
        """SELECT title FROM categories WHERE nodelete = 1 AND parents_categories = {};""".format(user_category))
    list_categories = []
    for i in cursor.fetchall():
        for h in i:
            list_categories.append(h)

    return list_categories


def product(user_category):
    cursor.execute("""SELECT title FROM product WHERE nodelete = 1 AND id_categories = {};""".format(user_category))
    list_product = []
    for i in cursor.fetchall():
        for h in i:
            list_product.append(h)
    global user_product
    user_product = True
    return list_product


def select_from_shop(whatis="*", fromis="categories", whereis=''):
    cursor.execute("""SELECT {} FROM {} WHERE {};""".format(
        whatis, fromis, whereis))
    return cursor.fetchall()


def select_db(whatis="*", fromis="baskets", whereis=''):
    if whereis == "":
        cursor.execute("""SELECT {} FROM {};""".format(whatis, fromis))
    else:
        cursor.execute(
            """SELECT {} FROM {} WHERE {};""".format(whatis, fromis, whereis))
    return cursor.fetchall()


def insert_db(name_table, *values_for_paste):
    amount_values = len(values_for_paste)
    _vars = ("? ," * amount_values)[:-2]
    cursor.execute(
        f"""INSERT INTO {name_table} VALUES({_vars});""", values_for_paste)
    db.commit()


def update_db(name_table, column, value, whereis):
    # print(f"""UPDATE {name_table} SET {column} = {value} WHERE {whereis};""")
    cursor.execute(
        f"""UPDATE {name_table} SET {column} = {value} WHERE {whereis}""")
    db.commit()


def create_basket(message):
    from datetime import datetime
    user_id = str(message.chat.id)
    username = message.from_user.username
    dt_created = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    tableName = "user_" + user_id

    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {tableName}(
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_product INTEGER,
        amount INTEGER
    );""")
    if not select_db("_id", "baskets", "username = '{}'".format(username)):
        cursor.execute(f"""INSERT INTO baskets VALUES(?, ?, ?, ?);""",
                       (None, username, user_id, dt_created))
        db.commit()


# def select_from_clients(whatis="*", fromis="clients", whereis=''):
#     if whereis == "":
#         curUsers.execute("""SELECT {} FROM '{}';""".format(whatis, fromis))
#     else:
#         curUsers.execute("""SELECT {} FROM '{}' WHERE {};""".format(
#             whatis, fromis, whereis))
#     return curUsers.fetchall()


def return_one_value(t):
    for i in t:
        for el in i:
            return el


def sum_element_in_list(_list):
    _str = ""
    for i in _list:
        _str += i
    return _str
