"""Interface to SCM API."""
from datetime import date, datetime
import requests
import yaml

from .conduct import CodesOfConduct
from .config import (BACKUP_URLS, C_ALLOW_UPDATE, C_CLUB, CODES_OF_CONDUCT,
                    CONFIG_FILE, DEBUG_LEVEL, FILE_READ, GROUPS, KEYFILE,
                    LISTS, MEMBERS, ROLES, SESSIONS, URL_CONDUCT, URL_GROUPS,
                    URL_LISTS, URL_MEMBERS, URL_ROLES, URL_SESSIONS,
                    O_VERIFY,  O_BACKUP, O_FORMAT, O_FIX,
                    USER_AGENT, get_config, verify_schema, verify_schema_data)
from .crypto import Crypto
from .entity import Entities
from .groups import Groups
from .issue import debug, set_debug_level
from .lists import Lists
from .members import Members
from .notify import notify
from .roles import Roles
from .sessions import Sessions
from shutil import copyfile
import os.path


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

    def get_config(self):
        """Read configuration file."""
        try:
            with open(CONFIG_FILE) as file:
                self._config = yaml.safe_load(file)
        except EnvironmentError:
            notify(f"Cannot open configuration file: {'config.yaml'}\n")
            return False
        except yaml.scanner.ScannerError as error:
            notify(f"Error in configuration file: {error}\n")
            return False

        if verify_schema(self._config) is False:
            return False
        
        self.crypto = Crypto(self._config[C_CLUB])  # Salt

        keyfile = self.config(KEYFILE)
        if keyfile is None:
            keyfile = "configuration/key.enc"
        self._key = self.crypto.read_key(keyfile)
        if self._key is None:
            return False

        debug_config = self.config(DEBUG_LEVEL)
        set_debug_level(debug_config)

        debug(f"Quarter offset: {self.q_offset}", 7)

        return True

    def initialise(self):
        """Initialise."""
        if self.get_config() is False:
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

        if self.option(O_VERIFY) or self.option(O_BACKUP):
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
            if aclass.get_data() is None:
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
        for aclass in self.classes:
            aclass.delete()

    def backup_data(self):
        """Backup."""
        if self.get_data(True) is False:
            return False

        backup = self.classes + self.backup_classes
        for aclass in backup:
            if self.crypto.encrypt_file(aclass.name, aclass.json) is False:
                return False
        
        # Backup config file too.
        src = CONFIG_FILE
        today = date.today()
        dst = os.path.join("backups", f"{today}", "config.yaml")
        copyfile(src,dst)

        return True

    def decrypt(self, date):
        """Decrypt file."""
        restore = self.classes + self.backup_classes

        for aclass in restore:
            decrypted = self.crypto.decrypt_file(aclass.name, date)
            if decrypted is None:
                return False
            aclass.parse_data(decrypted)

        notify("\n")
        return True

    def print_summary(self):
        """Print summary."""
        for aclass in self.classes:
            aclass.print_summary()
        print (f"   Not confirmed: {self.members.count_not_confirmed}\n")

        if self.backup_classes:
            for aclass in self.backup_classes:
                aclass.print_summary()
                
        if self.option(O_FIX): # fixed them!
            return
        
        if self.option(O_VERIFY):
            return  # fixable not available with backup data

        length = len(self.fixable)
        if length > 0:
            print (f"{length} fixable errors, rerun with --fix to apply.")

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
