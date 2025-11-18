"""SCM Members."""

from scm_helper.config import (
    C_NAME,
    C_TYPES,
    CTYPE_SYNCHRO,
    get_config,
)
from scm_helper.entity import Entities
from scm_helper.issue import E_DUPLICATE, debug, issue
from scm_helper.member import Member
from scm_helper.notify import notify


class Members(Entities):
    """Members."""

    # pylint: disable=too-many-instance-attributes
    # Need them all!

    def __init__(self, scm, name, url, jtag):
        """Initialize."""
        # pylint: disable=W0231
        # DO NOT call super() - it re-reads the data in the wrong class.
        # pylint: disable=too-many-instance-attributes
        # Need them all!
        self.entities = []
        self.by_guid = {}
        self.by_name = {}
        self.knownas = {}
        self.by_asa = {}
        self._name = name
        self._url = url
        self._raw_data = []
        self.jtag = jtag

        self.facebook = {}
        self.count_coaches = 0
        self.count_parents = 0
        self.count_inactive = 0
        self.count_swimmers = 0
        self.count_waterpolo = 0
        self.count_synchro = 0
        self.count_volunteer = 0
        self.count_not_confirmed = 0
        self.count = 0

        self.scm = scm

    def check_duplicate(self, member):
        """See if member already exists before adding."""
        name = member.name
        if name in self.by_name:
            if member.is_active and self.by_name[name].is_active:
                issue(self.by_name[name], E_DUPLICATE, name)
            else:
                if member.is_archived:
                    return
                active = self.by_name[name].is_active
                if member.is_active is False and active is False:
                    issue(self.by_name[name], E_DUPLICATE, "BOTH inactive", 9)
                else:
                    issue(self.by_name[name], E_DUPLICATE, "One is inactive", -1)
            return
        if name in self.knownas:
            if member.is_active and self.knownas[name].is_active:
                issue(self.knownas[name], E_DUPLICATE, name, 0, "(Known as)")
            else:
                if member.is_archived:
                    return
                issue(self.knownas[name], E_DUPLICATE, "One is inactive (Known as)", -1)

    def create_entities(self, entities):
        """Create a member objects."""
        # pylint: disable=too-many-branches
        i = 0
        for member in entities:
            data = Member(member, self.scm, self._url)

            if data.is_archived is False:
                self.check_duplicate(data)
                self.by_name[data.name] = data
                self.knownas[data.knownas] = data
                self.entities.append(data)
                if data.asa_number:
                    self.by_asa[data.asa_number] = data

                if data.facebook:
                    for face in data.facebook:
                        self.facebook[face] = data

            self.by_guid[data.guid] = data

            if data.is_active:
                if data.is_coach:
                    self.count_coaches += 1
                if data.is_parent:
                    self.count_parents += 1
                if data.is_swimmer:
                    self.count_swimmers += 1
                if data.is_polo:
                    self.count_waterpolo += 1
                if data.is_synchro:
                    self.count_synchro += 1
                if data.is_volunteer:
                    self.count_volunteer += 1
                self.count += 1
            else:
                if data.is_archived is False:
                    self.count_inactive += 1
                msg = f"Inactive Member: {data.name} / {data.guid} / {data.is_archived}"
                debug(msg, 5)
            i += 1

        return i

    def find_member(self, find):
        """Find a member."""
        if find in self.by_name:
            return self.by_name[find]
        if find in self.knownas:
            return self.knownas[find]
        return None

    def linkage(self):
        """Create Member links."""
        for member in self.entities:
            member.linkage(self.scm.members)

        for member in self.entities:
            # pylint: disable=fixme
            # Fix API error. not all parent links are returned ,so reverse link
            # TODO remove when API fixed.
            member.linkage2()

    def fix_secat(self):
        """fix_se categories."""
        for member in self.entities:
            res = member.fix_secat()
            if res is False:
                return False
        return True

    def fix_search(self):
        """fix_search_index."""
        for member in self.entities:
            res = member.fix_search()
            if res is False:
                return False
        return True

    def print_notes(self):
        """Print the notes."""
        res = ""
        for member in self.entities:
            res += member.print_notes()
        return res

    def se_check(self):
        """Check against an SE online."""
        if self.scm.ipad:
            notify("Not implemented on iPad")
            return False

        # pylint: disable=import-outside-toplevel
        from scm_helper.browser import se_check

        return se_check(self.scm, self.entities)

    def print_summary(self):
        """Print a summary."""
        name = get_config(self.scm, C_TYPES, CTYPE_SYNCHRO, C_NAME)

        opt = ""

        opt += f"Members: {self.count}\n"
        opt += f"   Swimmers: {self.count_swimmers}\n"
        opt += f"   {name}: {self.count_synchro}\n"
        opt += f"   Water Polo: {self.count_waterpolo}\n"
        opt += f"   Volunteers: {self.count_volunteer}\n"
        opt += f"   Coaches: {self.count_coaches}\n"
        opt += f"   Parents: {self.count_parents}\n"
        opt += f"   Inactive: {self.count_inactive}\n"

        return opt

    def print_swimmers_sessions(self):
        """Print sessions each swimmer is in."""
        res = "Name,Group,"
        for session in self.scm.sessions.entities:
            if session.is_active:
                res += f'"{session.full_name}",'
        res += "\n"

        for swimmer in self.entities:
            if swimmer.is_active:
                sessions = swimmer.print_swimmer_sessions(True)
                if sessions:
                    res += f"{swimmer.name},{swimmer.first_group},"
                    res += sessions
                    res += "\n"

        return res

    @property
    def url(self):
        """Return URL."""
        return self._url
