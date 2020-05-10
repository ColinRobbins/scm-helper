"""Null Encryption stuff for ipad."""
import getpass
import os.path
from pathlib import Path

WRITE_BINARY = "w"
READ_BINARY = "r"

class Crypto:
    """Encryption class copyed from crypto - but does nothing."""

    def __init__(self, salt, password):
        """Initialise."""
        self.salt = salt
        self.__key = self.get_encryption_key(self.__password)

    def encrypt_file(self, name, data):
        """Encrypt file."""
        notify("Not implemented on iPad\n")
        return None

    def decrypt_file(self, name, xdate):
        """Decrypt file."""
        notify("Not implemented on iPad\n")
        return None

    def read_key(self, filename):
        """Read API key."""
        home = str(Path.home())
        filename = os.path.join(home, CONFIG_DIR, filename)

        if not os.path.exists(filename):
            return self.get_key(filename)
        try:
            with open(filename, READ_BINARY) as file:
                data = file.read()
            file.close()
            return data

        except OSError as error:
            notify(f"Cannot open key file: {error}\n")
            return None


    def get_key(self, filename):
        """Encrypt file."""
        apikey = interact("No SCM API keyfile, creating one.  Enter API key: ")

        try:
            with open(filename, WRITE_BINARY) as file:
                file.write(apikey)
            file.close()

            notify(f"Generate encrypted keyfille {filename}\n")
            return apikey

        except OSError as error:
            notify(f"Cannot open/write key file: {error}\n")
            return False

    def read_email_password(self, filename):
        """Read email password."""
        notify("Not implemented on iPad\n")
        return False

    def get_email_password(self, filename):
        """Encrypt Password file."""
        notify("Not implemented on iPad\n")
        return False
