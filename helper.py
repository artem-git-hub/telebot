import hashlib
import sqlite3
import uuid

db = sqlite3.connect("db/shop.db", check_same_thread=False)
cursor = db.cursor()

dbAdmin = sqlite3.connect("db/admin.db", check_same_thread=False)
curAdmin = dbAdmin.cursor()

user_product = False


def generate_filename():
    return str(uuid.uuid4())


def generate_salt():
    return uuid.uuid4().hex


def reg(user_id, password, type):
    if not select_admin("_id", "admin", f"user_id = {user_id}"):
        l = hash_func(user_id=user_id, password=password)
        insert_admin("admin", None, l[0], type, l[1], l[2], None, None)


def hash_func(user_id, password="", what_do="gen"):
    user_id_byte = str(user_id)[2:7].encode("utf-8")
    if what_do == "gen":
        salt = generate_salt()
        salt_byte = salt.encode("utf-8")
        password_gen = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_byte, 100000).hex()

         # ниже строчка тебе точно нужна? она вроде бездействует!
        user_id_gen = hashlib.pbkdf2_hmac('sha256', str(user_id).encode('utf-8'), user_id_byte, 100000).hex()
        return [user_id, salt, password_gen]
    elif what_do == "edit_pass":
        salt = select_admin("salt", "admin", f"user_id = {user_id}")[0][0]
        salt_byte = salt.encode("utf-8")
        new_password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_byte, 100000).hex()
        update_admin("admin", "password", f"'{new_password}'", f"user_id = {user_id}")
        return True
    else:
        data = select_admin("salt, password", "admin", f"user_id = {user_id}")[0]
        salt = data[0]
        old_password = data[1]
        salt_byte = salt.encode("utf-8")
        new_password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_byte, 100000).hex()
        if old_password == new_password:
            return True
        else:
            return False


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


def select_admin(whatis="*", fromis="admin", whereis=''):
    if whereis == "":
        # print("""SELECT {} FROM {};""".format(whatis, fromis))
        curAdmin.execute("""SELECT {} FROM {};""".format(whatis, fromis))
    else:
        curAdmin.execute(
            """SELECT {} FROM {} WHERE {};""".format(whatis, fromis, whereis))
    return curAdmin.fetchall()


def insert_admin(name_table, *values_for_paste):
    amount_values = len(values_for_paste)
    _vars = ("?, " * amount_values)[:-2]
    curAdmin.execute(
        f"""INSERT INTO {name_table} VALUES({_vars});""", values_for_paste)
    dbAdmin.commit()


def select_db(whatis="*", fromis="baskets", whereis=''):
    if whereis == "":
        cursor.execute("""SELECT {} FROM {};""".format(whatis, fromis))
    else:
        cursor.execute(
            """SELECT {} FROM {} WHERE {};""".format(whatis, fromis, whereis))
    return cursor.fetchall()


def insert_db(name_table, *values_for_paste):
    amount_values = len(values_for_paste)
    _vars = ("?, " * amount_values)[:-2]
    cursor.execute(
        f"""INSERT INTO {name_table} VALUES({_vars});""", values_for_paste)
    db.commit()


def delete_db(name_table, where):
    cursor.execute(
        f"""DELETE FROM {name_table} WHERE {where};""")
    db.commit()


def update_db(name_table, column, value, whereis):
    cursor.execute(
        f"""UPDATE {name_table} SET {column} = {value} WHERE {whereis}""")
    db.commit()


def update_admin(name_table="admin", column="", value="", whereis=""):
    curAdmin.execute(
        f"""UPDATE {name_table} SET {column} = {value} WHERE {whereis}""")
    dbAdmin.commit()


def return_one_value(t):
    for i in t:
        for el in i:
            return el


def sum_element_in_list(_list):
    _str = ""
    for i in _list:
        _str += i
    return _str


def return_list(_tuple):
    _list = []
    for i in _tuple:
        for g in i:
            _list.append(g)
    return _list
