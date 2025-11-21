"""Interface to SCM API."""

import os.path
import platform
from datetime import date, datetime
from pathlib import Path
from shutil import copyfile

import parse
import requests
import yaml

from scm_helper.conduct import CodesOfConduct
from scm_helper.config import (
    API_SUFFIX,
    BACKUP_DIR,
    C_ALLOW_UPDATE,
    C_CLUB,
    C_DEBUG_LEVEL,
    C_SCM_URL,
    CODES_OF_CONDUCT,
    CONFIG_DIR,
    CONFIG_FILE,
    ENDPOINT_CONDUCT,
    ENDPOINT_EVENTS,
    ENDPOINT_GROUPS,
    ENDPOINT_INCIDENTBOOK,
    ENDPOINT_LISTS,
    ENDPOINT_MEETS,
    ENDPOINT_MEMBERS,
    ENDPOINT_NOTICE,
    ENDPOINT_ROLES,
    ENDPOINT_SESSIONS,
    ENDPOINT_TRIALS,
    ENDPOINT_WAITINGLIST,
    EVENTS,
    GROUPS,
    INCIDENTBOOK,
    JTAG_CODES_OF_CONDUCT,
    JTAG_EVENTS,
    JTAG_GROUPS,
    JTAG_INCIDENTBOOK,
    JTAG_LISTS,
    JTAG_MEETS,
    JTAG_MEMBERS,
    JTAG_NOTICE,
    JTAG_ROLES,
    JTAG_SESSIONS,
    JTAG_TRIALS,
    JTAG_WAITINGLIST,
    KEYFILE,
    LISTS,
    MEETS,
    MEMBERS,
    NOTICE,
    O_FIX,
    O_FORMAT,
    O_VERIFY,
    ROLES,
    SCMAPI_URL,
    SESSIONS,
    TRIALS,
    USER_AGENT,
    VERSIONURL,
    WAITINGLIST,
    delete_schema,
    get_config,
    verify_schema,
    verify_schema_data,
)
from scm_helper.default import create_default_config
from scm_helper.entity import Entities
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
        self._config = []
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
            with open(cfg, encoding="utf8") as file:
                self._config = None
                delete_schema()
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
        if len(self._config) == 0:
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
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        if self.ipad:
            password = "dummy"  # Can't to crypto on iPad

        if self.get_config(password) is False:
            return False

        scm_url = f"{SCMAPI_URL}/{API_SUFFIX}"
        if C_SCM_URL in self._config:
            scm_url = self._config[C_SCM_URL]

        url_sessions = f"{scm_url}/{ENDPOINT_SESSIONS}"
        url_groups = f"{scm_url}/{ENDPOINT_GROUPS}"
        url_lists = f"{scm_url}/{ENDPOINT_LISTS}"
        url_roles = f"{scm_url}/{ENDPOINT_ROLES}"
        url_conduct = f"{scm_url}/{ENDPOINT_CONDUCT}"
        url_members = f"{scm_url}/{ENDPOINT_MEMBERS}"

        mapping = [
            [SESSIONS, url_sessions, Sessions, JTAG_SESSIONS],
            [GROUPS, url_groups, Groups, JTAG_GROUPS],
            [LISTS, url_lists, Lists, JTAG_LISTS],
            [ROLES, url_roles, Roles, JTAG_ROLES],
            [CODES_OF_CONDUCT, url_conduct, CodesOfConduct, JTAG_CODES_OF_CONDUCT],
            [MEMBERS, url_members, Members, JTAG_MEMBERS],
        ]

        for item in mapping:
            name, url, xclass, jtag = item
            res = xclass(self, name, url, jtag)
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

        url_incident = f"{scm_url}/{ENDPOINT_INCIDENTBOOK}"
        url_events = f"{scm_url}/{ENDPOINT_EVENTS}"
        url_meets = f"{scm_url}/{ENDPOINT_MEETS}"
        url_trials = f"{scm_url}/{ENDPOINT_TRIALS}"
        url_wait = f"{scm_url}/{ENDPOINT_WAITINGLIST}"
        url_notice = f"{scm_url}/{ENDPOINT_NOTICE}"

        mapping = [
            [INCIDENTBOOK, url_incident, JTAG_INCIDENTBOOK],
            [EVENTS, url_events, JTAG_EVENTS],
            [MEETS, url_meets, JTAG_MEETS],
            [TRIALS, url_trials, JTAG_TRIALS],
            [WAITINGLIST, url_wait, JTAG_WAITINGLIST],
            [NOTICE, url_notice, JTAG_NOTICE],
        ]

        for xclass in mapping:
            name, url, jtag = xclass
            entity = Entities(self, name, url, jtag)
            self.backup_classes.append(entity)
            name = name.rstrip("s")  # remove any plural!
            name = name.lower()
            self.class_byname[name] = entity

        return True

    def version_check(self):
        """Check we are the latest version by fetching version from GitHub repo"""
        latest = None
        try:
            response = requests.get(VERSIONURL, timeout=30)

            if response.status_code == 404:  # Worked, but not found - old API
                debug(f"Cannot access {VERSIONURL}", 1)
                return

            lines = response.text.splitlines()
            latest = parse.parse('VERSION = "{}"', lines[2])
            latest = latest[0]

        # pylint: disable=bare-except
        except:
            debug(f"Running version: {VERSION}", 1)
            debug("Error geting latest available version", 1)
            return

        if latest == VERSION:
            debug(f"(version: {VERSION})", 1)
        else:
            notify(
                f"*** Running {VERSION} whereas {latest} is the latest release. ***\n"
            )

    def get_data(self, backup):
        """Get data."""
        self.version_check()

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
        """Analyse the data."""
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
            "Authorization": self._key,
        }

        purl = url
        if page != 1:
            purl = f"{url}?page={page}"

        debug(f"URL:\n{purl}", 5)
        debug(f"Headers:\n{headers}", 8)

        response = requests.get(purl, headers=headers, timeout=30)
        debug(f"Get response {response}, {response.status_code}", 6)

        if response.status_code == 404:  # Worked, but not found - old API
            debug(f"Page not found:\n{purl}", 1)
            return None

        if response.ok:
            return response.json()

        notify(f"\nErroring getting data from {url}, page:{page}\n")
        notify(f"{response.reason}:{response.text}")
        notify("\n")
        return None

    def api_write(self, entity, create):
        """Write data back to SCM."""
        club = self._config[C_CLUB]
        user_agent = USER_AGENT.replace("###CLUB_NAME###", club)

        headers = {
            "content-type": "application/json",
            "User-Agent": user_agent,
            "Authorization": self._key,
        }

        if get_config(entity.scm, C_ALLOW_UPDATE) is False:
            notify("Update prohibited by config.\n")
            return None

        debug(f"URL:\n{entity.url}", 6)
        debug(f"Headers:\n{headers}", 7)
        debug(f"Data:\n{entity.newdata}", 8)
        debug(f"ORIG Data:\n{entity.data}", 9)

        data = entity.newdata
        if create:
            debug(f"Post request:\n{data}", 5)
            response = requests.post(entity.url, json=data, headers=headers, timeout=30)
        else:
            debug(f"Put request:\n{data}", 5)
            response = requests.put(entity.url, json=data, headers=headers, timeout=30)

        debug(f"Write response {response}, {response.status_code}", 6)

        if response.status_code == 404:  # Worked, but not found
            return None

        if response.ok:
            return response

        notify(f"\nErroring posting data {entity.name}...\n")
        notify(f"{response.reason}:{response.text}")
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

        with open(cfg, mode="w", encoding="utf8") as file:
            file.write(f"Fixed index: {self.today}")

        msg = "Index recreated - give SCM time to process changes before testing."
        notify(f"\n{msg}\n")

        return True

    def fix_secat(self):
        """fix_se categories."""
        res = self.members.fix_secat()
        if res is False:
            return res

        msg = "Fixed SE Catagories"
        notify(f"\n{msg}\n")

        return True

    def apply_fixes(self):
        """Apply any fixes."""
        if len(self.fixable) == 0:
            notify("Nothing to fix\n")
            return False

        for fix in self.fixable:
            fix.apply_fix()

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
