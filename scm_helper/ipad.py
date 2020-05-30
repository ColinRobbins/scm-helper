"""Null Encryption stuff for ipad."""
import os.path
from pathlib import Path

from scm_helper.config import CONFIG_DIR
from scm_helper.notify import interact, notify

WRITE_BINARY = "w"
READ_BINARY = "r"

# pylint: disable=unused-argument
# pylint: disable=no-self-use


class Crypto:
    """Encryption class copied from crypto - but does nothing."""

    def __init__(self, salt, password):
        """Initialise."""
        self.salt = salt

    def encrypt_file(self, name, data):
        """Encrypt file."""
        notify("Not implemented on iPad\n")

    def decrypt_file(self, name, xdate):
        """Decrypt file."""
        notify("Not implemented on iPad\n")

    def encrypt_backup(self, name, data):
        """Encrypt file."""
        notify("Not implemented on iPad\n")

    def decrypt_backup(self, name, xdate):
        """Decrypt file."""
        notify("Not implemented on iPad\n")

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
            return data.strip()

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
