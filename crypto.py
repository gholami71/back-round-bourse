from cryptography.fernet import Fernet

key = b'MYZ2MqLhKxYhjPnwYlUBHqJUcVn5OHGXPHjjtG41Pco='
cipher_suite = Fernet(key)

def encrypt(message):
    encrypted_message = cipher_suite.encrypt(message.encode())
    return encrypted_message.decode()


def decrypt(encrypted_message):
    decrypted_message = cipher_suite.decrypt(encrypted_message)
    return decrypted_message.decode()