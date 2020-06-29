"""Interface to SCM API."""
import os.path
import platform
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
    C_DEBUG_LEVEL,
    CODES_OF_CONDUCT,
    CONFIG_DIR,
    CONFIG_FILE,
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
    URL_WHO,
    USER_AGENT,
    WHO,
    get_config,
    verify_schema,
    verify_schema_data,
)
from scm_helper.default import create_default_config
from scm_helper.entity import Entities, Who
from scm_helper.groups import Groups
from scm_helper.issue import debug, set_debug_level
from scm_helper.lists import Lists
from scm_helper.members import Members
from scm_helper.notify import notify
from scm_helper.roles import Roles
from scm_helper.sessions import Sessions
from scm_helper.version import VERSION


class API:
    """Main SCM object."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
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
        self.ipad = False

        self.today = datetime.now()
        q_month = (int((self.today.month - 1) / 3) * 3) + 1
        q_year = self.today.year
        self.eoy = datetime(int(q_year), 12, 31)
        offset = datetime(int(q_year), int(q_month), 1)
        self.q_offset = (self.today - offset).days

        if "iPad" in platform.machine():
            self.ipad = True

    def get_config_file(self):
        """Read configuration file."""
        home = str(Path.home())
        cfg = os.path.join(home, CONFIG_DIR, CONFIG_FILE)

        if os.path.isfile(cfg) is False:
            if create_default_config() is False:
                return False
            nmsg = "You will now be asked to provide a password.\n"
            nmsg += "This is used to protect the API key.\n"
            notify(nmsg)

        try:
            with open(cfg) as file:
                self._config = yaml.safe_load(file)
        except EnvironmentError:
            notify(f"Cannot open configuration file: {cfg}\n")
            return False
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as error:
            notify(f"Error in configuration file: {error}\n")
            return False

        if verify_schema(self._config) is False:
            return False

        return True

    def get_config(self, password):
        """Get API key."""
        # pylint: disable=import-outside-toplevel
        if self._config is None:
            if self.get_config_file() is False:
                return False

        if self.ipad:
            from scm_helper.ipad import Crypto

            self.crypto = Crypto(self._config[C_CLUB], password)  # Salt
        else:
            from scm_helper.crypto import Crypto

            self.crypto = Crypto(self._config[C_CLUB], password)  # Salt

        home = str(Path.home())

        keyfile = os.path.join(home, CONFIG_DIR, KEYFILE)
        self._key = self.crypto.read_key(keyfile)
        if self._key is None:
            return False

        debug_config = self.config(C_DEBUG_LEVEL)
        set_debug_level(debug_config)

        debug(f"Quarter offset: {self.q_offset}", 9)

        return True

    def initialise(self, password):
        """Initialise."""

        if self.ipad:
            password = "dummy"  # Can't to crypto on iPad

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

        # Finally who's who
        entity = Who(self, WHO, URL_WHO)
        self.backup_classes.append(entity)
        name = WHO.lower()
        self.class_byname[name] = entity

        return True

    def get_data(self, backup):
        """Get data."""
        notify(f"Reading Data...\n")
        debug(f"(version: {VERSION})", 1)

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

    def se_check(self):
        """Get member data."""
        return self.members.se_check()

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

        notify("Done.\n")

    def update(self):
        """Update (lists)."""
        notify("Updating...\n")
        self.lists.update()
        notify("Done.\n")

    def restore(self, xclass):
        """Restore data..."""
        if self.ipad:
            notify("Not implemented on iPad")
            return False

        xclass = xclass.lower()
        if xclass in self.class_byname:
            item = self.class_byname[xclass]
            notify(f"Restoring {item.name}...\n")
            return item.restore(xclass)
        notify(f"Backup type {xclass} not found\n")
        return False

    def dump(self, xclass):
        """Dump data..."""
        if self.ipad:
            notify("Not implemented on iPad")
            return False

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
        if self.ipad:
            notify("Not implemented on iPad")
            return False

        if self.get_data(True) is False:
            return False

        backup = self.classes + self.backup_classes
        for aclass in backup:
            if self.crypto.encrypt_backup(aclass.name, aclass.json) is False:
                return False

        # Backup config file too.
        home = str(Path.home())
        today = date.today()
        cfg = os.path.join(home, CONFIG_DIR)
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
        if self.ipad:
            notify("Not implemented on iPad")
            return False

        restore = self.classes + self.backup_classes

        for aclass in restore:
            decrypted = self.crypto.decrypt_backup(aclass.name, xdate)
            if decrypted is None:
                return False
            aclass.parse_data(decrypted)

        notify("\n")
        return True

    def print_summary(self, backup=False):
        """Print summary."""
        debug("Print summary called", 6)
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
            output += f"\n{length} fixable errors...\n"
            output += self.list_fixes()

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
        club = self._config[C_CLUB]
        user_agent = USER_AGENT.replace("###CLUB_NAME###", club)

        headers = {
            "User-Agent": user_agent,
            "Authorization-Token": self._key,
            "Page": str(page),
        }

        debug(f"URL:\n{url}", 9)
        debug(f"Headers:\n{headers}", 8)

        response = requests.get(url, headers=headers)
        if response.ok:
            return response.json()

        if response.status_code == 404:  # Worked, but not found
            return False

        notify(f"\nErroring getting data from {url}, page:{page}\n")
        notify(response.reason)
        notify("\n")
        return None

    def api_write(self, entity, create):
        """Write data back to SCM."""
        club = self._config[C_CLUB]
        user_agent = USER_AGENT.replace("###CLUB_NAME###", club)

        headers = {
            "content-type": "application/json",
            "User-Agent": user_agent,
            "Authorization-Token": self._key,
        }

        if get_config(entity.scm, C_ALLOW_UPDATE) is False:
            notify("Update prohibited by config.\n")
            return None

        debug(f"URL:\n{entity.url}", 9)
        debug(f"Headers:\n{headers}", 8)

        data = entity.newdata
        if create:
            debug(f"Post request:\n{data}", 7)
            response = requests.post(entity.url, json=data, headers=headers)
        else:
            debug(f"Put request:\n{data}", 7)
            response = requests.put(entity.url, json=data, headers=headers)
        if response.ok:
            return response

        if response.status_code == 404:  # Worked, but not found
            return False

        notify(f"\nErroring posting data {entity.name}\n")
        notify(response.reason)
        notify("\n")
        return None

    def fix_search(self):
        """fix_search_index."""

        home = str(Path.home())
        cfg = os.path.join(home, CONFIG_DIR, "fixed_search.txt")
        if os.path.isfile(cfg) is True:
            notify("Not required - already fixed")
            return False

        res = self.members.fix_search()
        if res is False:
            return res

        with open(cfg, mode="w") as file:
            file.write(f"Fixed index: {self.today}")

        msg = "Index recreated - give SCM time to process changes before testing."
        notify(f"\n{msg}\n")

        return True

    def apply_fixes(self):
        """Apply any fixes."""
        if len(self.fixable) == 0:
            notify("Nothing to fix\n")
            return False

        for fix in self.fixable:
            if fix.apply_fix() is None:
                self.fixable = []
                return False

        self.fixable = []
        return True

    def list_fixes(self):
        """List any fixes."""
        if len(self.fixable) == 0:
            notify("Nothing to fix\n")
            return False

        res = ""
        for fix in self.fixable:
            res += f"{fix.name}: {fix.fixmsg}\n"

        return res

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
