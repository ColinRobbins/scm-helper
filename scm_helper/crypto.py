"""Encryption stuff."""
import base64
import getpass
import json
import os.path
from datetime import date

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from notify import notify, interact

WRITE_BINARY = "wb"
READ_BINARY = "rb"


class Crypto:
    """Encryption class."""

    def __init__(self, salt, password):
        """Initialise."""
        self.salt = salt
        if password is None:
            self.__password = getpass.getpass("Enter SCM helper password: ")
        else:
            self.__password = password
            
        self.__key = self.get_encryption_key(self.__password)

    def encrypt_file(self, name, data):
        """Encrypt file."""
        try:
            fernet = Fernet(self.__key)

            today = date.today()

            directory = os.path.join("backups", f"{today}")

            if not os.path.exists("backups"):
                os.mkdir("backups")
                
            if not os.path.exists(directory):
                os.mkdir(directory)

            filename = os.path.join("backups", f"{today}", f"{name}.enc")

            encrypted_data = fernet.encrypt(data.encode("utf-8"))
            with open(filename, WRITE_BINARY) as file:
                file.write(encrypted_data)

            notify(f"Encrypted {filename}\n")
            return True

        except OSError as error:
            notify(f"Cannot open/write file: {error}\n")
            return False
        except InvalidToken:
            notify("Cannot encrypt file - token error?\n")
            return False

    def decrypt_file(self, name, xdate):
        """Decrypt file."""
        try:
            fernet = Fernet(self.__key)
            filename = os.path.join("backups", xdate, f"{name}.enc")

            with open(filename, READ_BINARY) as file:
                data = file.read()

            decrypted = fernet.decrypt(data)
            return json.loads(decrypted.decode())

        except OSError as error:
            notify(f"Cannot open file: {error}\n")
            return None
        except InvalidToken:
            notify("Cannot decrypt file - wrong password?\n")
            return None

    def get_encryption_key(self, password):
        """Generate a Fremat password from password and salt."""
        password = password.encode()
        salt = self.salt.encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(password))


    def read_key(self, filename):
        """Read API key."""

        if not os.path.exists(filename):
            return self.get_key(filename)
        try:
            fernet = Fernet(self.__key)

            with open(filename, READ_BINARY) as file:
                data = file.read()

            decrypted = fernet.decrypt(data)
            return decrypted.decode()

        except OSError as error:
            notify(f"Cannot open key file: {error}\n")
            return None
        except InvalidToken:
            notify("Cannot decrypt key file - wrong password?\n")
            return None

    def get_key(self, filename):
        """Encrypt file."""
        apikey = interact("No keyfile, creating one\nEnter API key: ")
        
        try:
            fernet = Fernet(self.__key)

            encrypted_data = fernet.encrypt(apikey.encode("utf-8"))
            with open(filename, WRITE_BINARY) as file:
                file.write(encrypted_data)

            notify(f"Generate encrypted keyfille {filename}\n")
            return apikey

        except OSError as error:
            notify(f"Cannot open/write key file: {error}\n")
            return False
        except InvalidToken:
            notify("Cannot encrypt keyfile - token error?\n")
            return False

    def read_email_password(self, filename):
        """Read email password."""

        if not os.path.exists(filename):
            return self.get_email_password(filename)
        try:
            fernet = Fernet(self.__key)

            with open(filename, READ_BINARY) as file:
                data = file.read()

            decrypted = fernet.decrypt(data)
            return decrypted.decode()

        except OSError as error:
            notify(f"Cannot open password file: {error}\n")
            return None
        except InvalidToken:
            notify("Cannot decrypt password file - wrong password?\n")
            return None

    def get_email_password(self, filename):
        """Encrypt Password file."""
        apikey = getpass.getpass("Enter email password: ")
        
        try:
            fernet = Fernet(self.__key)

            encrypted_data = fernet.encrypt(apikey.encode("utf-8"))
            with open(filename, WRITE_BINARY) as file:
                file.write(encrypted_data)

            notify(f"Generate password keyfile {filename}\n")
            return apikey

        except OSError as error:
            notify(f"Cannot open/write email password file: {error}\n")
            return False
        except InvalidToken:
            notify("Cannot encrypt email password - token error?\n")
            return False