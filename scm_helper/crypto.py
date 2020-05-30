"""Encryption stuff."""
import base64
import getpass
import json
import os.path
from datetime import date
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from scm_helper.config import BACKUP_DIR, CONFIG_DIR
from scm_helper.notify import interact, notify

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

    def encrypt_file(self, filename, data):
        """Encrypt file."""
        try:
            fernet = Fernet(self.__key)

            encrypted_data = fernet.encrypt(data)
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

    def encrypt_backup(self, name, data):
        """Encrypt file."""
        try:
            today = date.today()
            home = str(Path.home())

            backup = os.path.join(home, CONFIG_DIR, BACKUP_DIR)
            directory = os.path.join(home, CONFIG_DIR, BACKUP_DIR, f"{today}")

            if os.path.exists(backup) is False:
                os.mkdir(backup)

            if os.path.exists(directory) is False:
                os.mkdir(directory)

            filename = os.path.join(directory, f"{name}.enc")

            return self.encrypt_file(filename, data.encode("utf-8"))

        except OSError as error:
            notify(f"Cannot open/write file: {error}\n")
            return False

    def decrypt_file(self, filename):
        """Decrypt file."""
        try:
            fernet = Fernet(self.__key)

            with open(filename, READ_BINARY) as file:
                data = file.read()
            file.close()

            decrypted = fernet.decrypt(data)
            return decrypted

        except OSError as error:
            notify(f"Cannot open file: {error}\n")
            return None
        except InvalidToken:
            notify("Cannot decrypt file - wrong password?\n")
            return None

    def decrypt_backup(self, name, xdate):
        """Decrypt file."""
        try:
            home = str(Path.home())
            backup = os.path.join(home, CONFIG_DIR, BACKUP_DIR)

            filename = os.path.join(backup, xdate, f"{name}.enc")

            data = self.decrypt_file(filename)
            return json.loads(data.decode())

        except OSError as error:
            notify(f"Cannot open file: {error}\n")
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
        home = str(Path.home())
        filename = os.path.join(home, CONFIG_DIR, filename)

        if not os.path.exists(filename):
            return self.get_key(filename)
        try:
            fernet = Fernet(self.__key)

            with open(filename, READ_BINARY) as file:
                data = file.read()
            file.close()

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
        apikey = interact("No SCM API keyfile, creating one.  Enter API key: ")

        try:
            fernet = Fernet(self.__key)

            encrypted_data = fernet.encrypt(apikey.encode("utf-8"))
            with open(filename, WRITE_BINARY) as file:
                file.write(encrypted_data)
            file.close()

            notify(f"Generated encrypted keyfile {filename}\n")
            return apikey

        except OSError as error:
            notify(f"Cannot open/write key file: {error}\n")
            return False
        except InvalidToken:
            notify("Cannot encrypt keyfile - token error?\n")
            return False

    def read_email_password(self, filename):
        """Read email password."""
        home = str(Path.home())
        filename = os.path.join(home, CONFIG_DIR, filename)

        if not os.path.exists(filename):
            return self.get_email_password(filename)
        try:
            fernet = Fernet(self.__key)

            with open(filename, READ_BINARY) as file:
                data = file.read()
            file.close()

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
            file.close()

            notify(f"Generate password keyfile {filename}\n")
            return apikey

        except OSError as error:
            notify(f"Cannot open/write email password file: {error}\n")
            return False
        except InvalidToken:
            notify("Cannot encrypt email password - token error?\n")
            return False
