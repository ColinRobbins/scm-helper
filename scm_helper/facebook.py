"""Read and process a file of Facebook date."""
import ntpath
import os
import re
from pathlib import Path

from scm_helper.config import (
    C_FACEBOOK,
    C_FILES,
    C_GROUPS,
    CONFIG_DIR,
    FILE_READ,
    get_config,
)
from scm_helper.files import Files
from scm_helper.notify import notify

# should probably parse the structure, but a simple regex seems to work...
FACEBOOK_RE = re.compile(
    'ref=MEMBER_LIST" rel="dialog" title="([a-zA-Z -]*)" tabindex='
)


class Facebook:
    """Read and process all facebook files."""

    def __init__(self):
        """Initialise."""
        self.scm = None
        self.facebook = []

    def read_data(self, scm):
        """Read each file."""
        self.scm = scm

        home = str(Path.home())
        mydir = os.path.join(home, CONFIG_DIR)

        cfg = get_config(scm, C_FACEBOOK, C_FILES)
        if cfg:
            for facebook in cfg:
                face = FacebookPage()
                filename = os.path.join(mydir, facebook)
                res = face.readfile(filename, scm)
                if res:
                    self.facebook.append(face)
                    if face.parse() is False:
                        return False
                else:
                    return False
            return True

        cfg = get_config(scm, C_FACEBOOK, C_GROUPS)
        if cfg:
            for facebook in cfg:
                face = FacebookPage()
                res = face.readurl(facebook, scm)
                if res:
                    self.facebook.append(face)
                else:
                    return False

            return True

        return False

    def analyse(self):
        """Analyse filebook files."""
        for facebook in self.facebook:
            facebook.analyse()

    def print_errors(self):
        """Print errors."""
        res = ""
        for facebook in self.facebook:
            res += facebook.print_errors()

        if res == "":
            res = "Nothing to report"
        return res

    def delete(self):
        """Delete."""
        for facebook in self.facebook:
            del facebook


class FacebookPage(Files):
    """Manage a facebook file."""

    def __init__(self):
        """Initilaise Facebook."""
        super().__init__()
        self._filename = None
        self.scm = None
        self.data = None
        self.users = []

    def readfile(self, filename, scm):
        """Read Facebook file."""
        self._filename = filename
        self.scm = scm

        shortfile = ntpath.basename(filename)

        notify(f"Reading {shortfile}...\n")

        try:
            with open(filename, FILE_READ, encoding="utf8") as file:
                self.data = file.read().replace("\n", "")
            file.close()
            return True

        except EnvironmentError:
            notify(f"Cannot open facebook file: {filename}\n")
            return False

    def readurl(self, url, scm):
        """Read Facebook page."""
        self._filename = url.rstrip("/")  # Remove '/' for result printing

        self.scm = scm

        if self.scm.ipad:
            notify("Not implemented on iPad")
            return False

        # pylint: disable=import-outside-toplevel
        from scm_helper.browser import fb_read_url

        res = fb_read_url(scm, url)

        if res is None:
            return False

        self.users = res
        return True

    def parse(self):
        """Parse file to find strings."""
        users = FACEBOOK_RE.findall(self.data)

        if users is None:
            notify("Could not parse Facebook file")
            return False

        count = 0
        for user in users:
            count += 1
            self.users.append(user)

        notify(f"Read {count} members.\n")

        if count == 0:
            notify("Error: No members found")
            return False
        return True

    def analyse(self):
        """Analyse Facebook file."""
        members = self.scm.members.by_name
        knownas = self.scm.members.knownas
        facebook = self.scm.members.facebook

        for user in self.users:
            inactive = False
            if user in members:
                if members[user].is_active:
                    continue
                inactive = True

            if user in knownas:
                if knownas[user].is_active:
                    continue
                inactive = True

            if user in facebook:  # NB this can override inactive = True above
                # could be active in a different entry (eg parent)
                if facebook[user].is_active:
                    continue
                inactive = True

            if inactive:
                self.file_error(user, "Facebook user is inactive in SCM (resigned?)")
            else:
                self.file_error(user, "Facebook user not in SCM")
