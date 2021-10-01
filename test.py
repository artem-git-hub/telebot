import hashlib
import os

users = {}  # Простое демо хранилище

# Add a user
username = 'Brent'  # Имя пользователя
password = 'mypassword'  # Пароль пользователя

# username = input(print("username"))
# password = input(print("password"))

salt = "asdasd".encode("utf-8")  # Новая соль для данного пользователя
key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
users[username] = {  # Хранение ключа и соли
    'salt': salt,
    'key': key
}

# Попытка проверки 1 (неправильный пароль)
username = 'Brent'
password = 'notmypassword'

salt = users[username]['salt']  # Получение соли
key = users[username]['key']  # Получение правильного ключа
new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

assert key != new_key  # Ключи не совпадают, следовательно, пароли не совпадают

# Попытка проверки 2 (правильный пароль)
username = 'Brent'
password = 'mypassword'

salt = users[username]['salt']
key = users[username]['key']
new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
print(key.hex() == new_key.hex())
print(key.hex(), "\n", new_key.hex())
