"""Read and process a file of Facebook date."""
import re

from config import C_FACEBOOK, FILE_READ, get_config
from files import Files
from notify import notify

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

    def readfiles(self, scm):
        """Read each file."""
        self.scm = scm

        cfg = get_config(scm, C_FACEBOOK)
        if cfg:
            for facebook in cfg:
                face = FacebookPage()
                res = face.readfile(facebook, scm)
                if res:
                    self.facebook.append(face)
                    if face.parse() is False:
                        return False
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

        notify(f"Reading {filename}...\n")

        try:
            with open(filename, FILE_READ) as file:
                self.data = file.read().replace("\n", "")
            file.close()
            return True

        except EnvironmentError:
            notify(f"Cannot open facebook file: {filename}\n")
            return False

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
