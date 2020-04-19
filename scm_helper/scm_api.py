"""Interface to SCM API."""
import os.path
from datetime import date, datetime
from pathlib import Path
from shutil import copyfile

import requests
import yaml

from scm_helper.conduct import CodesOfConduct
from scm_helper.config import (
    BACKUP_DIR,
    BACKUP_URLS,
    C_ALLOW_UPDATE,
    C_CLUB,
    CODES_OF_CONDUCT,
    CONFIG_DIR,
    CONFIG_FILE,
    DEBUG_LEVEL,
    GROUPS,
    KEYFILE,
    LISTS,
    MEMBERS,
    O_FIX,
    O_FORMAT,
    O_VERIFY,
    ROLES,
    SESSIONS,
    URL_CONDUCT,
    URL_GROUPS,
    URL_LISTS,
    URL_MEMBERS,
    URL_ROLES,
    URL_SESSIONS,
    USER_AGENT,
    get_config,
    verify_schema,
    verify_schema_data,
)
from scm_helper.crypto import Crypto
from scm_helper.default import create_default_config
from scm_helper.entity import Entities
from scm_helper.groups import Groups
from scm_helper.issue import debug, set_debug_level
from scm_helper.lists import Lists
from scm_helper.members import Members
from scm_helper.notify import notify
from scm_helper.roles import Roles
from scm_helper.sessions import Sessions


class API:
    """Main SCM object."""

    # pylint: disable=too-many-instance-attributes
    # Need them all!

    def __init__(self, issues):
        """Initialize SCM main class."""
        # pylint: disable=too-many-instance-attributes
        # Need them all!
        self._options = {}
        self._config = None
        self._key = None
        self.groups = None
        self.lists = None
        self.roles = None
        self.sessions = None
        self.members = None
        self.conduct = None
        self.classes = []
        self.backup_classes = []
        self.class_byname = {}
        self.issue_handler = issues
        self.fixable = []
        self.crypto = None

        self.today = datetime.now()
        q_month = (int((self.today.month - 1) / 3) * 3) + 1
        q_year = self.today.year
        self.eoy = datetime(int(q_year), 12, 31)
        offset = datetime(int(q_year), int(q_month), 1)
        self.q_offset = (self.today - offset).days

    def get_config_file(self):
        """Read configuration file."""
        home = str(Path.home())
        cfg = os.path.join(home, CONFIG_DIR, CONFIG_FILE)

        if os.path.isfile(cfg) is False:
            if create_default_config() is False:
                return False

        try:
            with open(cfg) as file:
                self._config = yaml.safe_load(file)
        except EnvironmentError:
            notify(f"Cannot open configuration file: {cfg}\n")
            return False
        except yaml.scanner.ScannerError as error:
            notify(f"Error in configuration file: {error}\n")
            return False

        if verify_schema(self._config) is False:
            return False

        file.close()

        return True

    def get_config(self, password):
        """Get API key."""
        if self._config is None:
            if self.get_config_file() is False:
                return False

        self.crypto = Crypto(self._config[C_CLUB], password)  # Salt

        home = str(Path.home())

        keyfile = os.path.join(home, CONFIG_DIR, KEYFILE)
        self._key = self.crypto.read_key(keyfile)
        if self._key is None:
            return False

        debug_config = self.config(DEBUG_LEVEL)
        set_debug_level(debug_config)

        debug(f"Quarter offset: {self.q_offset}", 7)

        return True

    def initialise(self, password):
        """Initialise."""
        if self.get_config(password) is False:
            return False

        mapping = [
            [SESSIONS, URL_SESSIONS, Sessions],
            [GROUPS, URL_GROUPS, Groups],
            [LISTS, URL_LISTS, Lists],
            [ROLES, URL_ROLES, Roles],
            [CODES_OF_CONDUCT, URL_CONDUCT, CodesOfConduct],
            [MEMBERS, URL_MEMBERS, Members],
        ]

        for item in mapping:
            name, url, xclass = item
            res = xclass(self, name, url)
            self.classes.append(res)

            # Ugly, but can's see how else to do it
            if name == SESSIONS:
                self.sessions = res
            elif name == GROUPS:
                self.groups = res
            elif name == LISTS:
                self.lists = res
            elif name == ROLES:
                self.roles = res
            elif name == CODES_OF_CONDUCT:
                self.conduct = res
            elif name == MEMBERS:
                self.members = res

            name = name.rstrip("s")  # remove any plural!
            name = name.lower()
            self.class_byname[name] = res

        for xclass in BACKUP_URLS:
            name, url = xclass
            entity = Entities(self, name, url)
            self.backup_classes.append(entity)
            name = name.rstrip("s")  # remove any plural!
            name = name.lower()
            self.class_byname[name] = entity

        return True

    def get_data(self, backup):
        """Get data."""
        notify("Reading Data...\n")

        loop = self.classes
        if backup:
            loop = self.classes + self.backup_classes

        for aclass in loop:
            if aclass.get_data() is False:
                return False

        return True

    def get_members_only(self):
        """Get member data."""
        self.members.get_data()

    def linkage(self):
        """Set up cross reference links between Entities."""
        notify("Linking...\n")

        for aclass in self.classes:
            aclass.linkage()

        if verify_schema_data(self) is False:
            return False
        return True

    def analyse(self):
        """Analise the data."""
        notify("Analysing...\n")

        for aclass in self.classes:
            aclass.analyse()

    def update(self):
        """Update (lists)."""
        notify("Updating...\n")
        self.lists.update()
        notify("Done.\n")

    def restore(self, xclass):
        """Restore data..."""
        xclass = xclass.lower()
        if xclass in self.class_byname:
            item = self.class_byname[xclass]
            notify(f"Restoring {item.name}...\n")
            return item.restore(xclass)
        notify(f"Backup type {xclass} not found\n")
        return False

    def dump(self, xclass):
        """Dump data..."""
        f_csv = "CSV"
        f_json = "JSON"
        xlist = [f_json, f_csv]
        xformat = f_json
        if self.option(O_FORMAT):
            xformat = self.option(O_FORMAT)

        if xformat not in xlist:
            notify(f"Unknown class {xformat}")

        xclass = xclass.lower()
        if xclass in self.class_byname:
            if xformat == f_json:
                return self.class_byname[xclass].pretty_print()
            return self.class_byname[xclass].csv()
        notify(f"Dump type {xclass} not found\n")
        return ""

    def delete(self):
        """Delete all entities."""
        delete = self.classes + self.backup_classes
        for aclass in delete:
            aclass.delete()

        self.issue_handler.delete()

        self.groups = None
        self.lists = None
        self.roles = None
        self.sessions = None
        self.members = None
        self.conduct = None
        self.classes = []
        self.backup_classes = []
        self.class_byname = {}
        self.fixable = []

    def backup_data(self):
        """Backup."""
        if self.get_data(True) is False:
            return False

        backup = self.classes + self.backup_classes
        for aclass in backup:
            if self.crypto.encrypt_file(aclass.name, aclass.json) is False:
                return False

        # Backup config file too.
        home = str(Path.home())
        today = date.today()
        cfg = os.path.join(home, CONFIG_DIR)
        backup = os.path.join(home, CONFIG_DIR, BACKUP_DIR)
        directory = os.path.join(home, CONFIG_DIR, BACKUP_DIR, f"{today}")

        src = os.path.join(cfg, CONFIG_FILE)
        dst = os.path.join(directory, CONFIG_FILE)
        copyfile(src, dst)

        # Backup keyfile file too.
        src = os.path.join(cfg, KEYFILE)
        dst = os.path.join(directory, KEYFILE)
        copyfile(src, dst)

        return True

    def decrypt(self, xdate):
        """Decrypt file."""
        restore = self.classes + self.backup_classes

        for aclass in restore:
            decrypted = self.crypto.decrypt_file(aclass.name, xdate)
            if decrypted is None:
                return False
            aclass.parse_data(decrypted)

        notify("\n")
        return True

    def print_summary(self, backup=False):
        """Print summary."""
        output = ""
        for aclass in self.classes:
            output += aclass.print_summary()
        output += f"   Not confirmed: {self.members.count_not_confirmed}\n"

        if backup and self.backup_classes:
            for aclass in self.backup_classes:
                output += aclass.print_summary()

        if self.option(O_FIX):  # fixed them!
            return output

        if self.option(O_VERIFY):
            return output  # fixable not available with backup data

        length = len(self.fixable)
        if length > 0:
            output += f"\n{length} fixable errors."

        output += "\n"
        return output

    def setopt(self, opt, args):
        """Set options."""
        if args:
            self._options[opt] = args
        else:
            self._options[opt] = True

    def api_read(self, url, page):
        """Read URL page."""
        headers = {
            "User-Agent": USER_AGENT,
            "Authorization-Token": self._key,
            "Page": str(page),
        }

        response = requests.get(url, headers=headers)
        if response.ok:
            return response.json()

        if response.status_code == 404:  # Worked, but not found
            return False

        notify(f"Erroring getting data from {url}, page:{page}\n")
        notify(response.reason)
        notify("\n")
        return None

    def api_write(self, entity, create):
        """Write data back to SCM."""
        headers = {
            "content-type": "application/json",
            "User-Agent": USER_AGENT,
            "Authorization-Token": self._key,
        }

        if get_config(entity.scm, C_ALLOW_UPDATE) is False:
            notify("Update prohibited by config.\n")
            return None

        data = entity.newdata
        if create:
            response = requests.post(entity.url, json=data, headers=headers)
        else:
            response = requests.put(entity.url, json=data, headers=headers)
        if response.ok:
            return response

        if response.status_code == 404:  # Worked, but not found
            return False

        notify(f"Erroring posting data {entity.name}\n")
        notify(response.reason)
        notify("\n")
        return None

    def apply_fixes(self):
        """Apply any fixes."""
        for fix in self.fixable:
            if fix.apply_fix() is None:
                return False
        return True

    def option(self, option):
        """Options."""
        if option in self._options:
            return self._options[option]
        return None

    def config(self, option):
        """Options."""
        if option in self._config:
            return self._config[option]
        return None
