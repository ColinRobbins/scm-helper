"""SCM Members."""
from scm_helper.config import (
    A_ACTIVE,
    A_FIRSTNAME,
    A_LASTNAME,
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

    def __init__(self, scm, name, url):
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
        firtname = member[A_FIRSTNAME]
        lastname = member[A_LASTNAME]
        name = f"{firtname} {lastname}"
        if name in self.by_name:
            if member[A_ACTIVE] == "1" and self.by_name[name].is_active:
                act1 = member[A_ACTIVE]
                act2 = self.by_name[name].is_active
                debug(f"{name}: {act1}-{act2}", 6)
                issue(self.by_name[name], E_DUPLICATE, name)
            else:
                active = self.by_name[name].is_active
                if member[A_ACTIVE] == "0" and active is False:
                    issue(self.by_name[name], E_DUPLICATE, "BOTH inactive", 9)
                else:
                    issue(self.by_name[name], E_DUPLICATE, "One is inactive", -1)
            return
        if name in self.knownas:
            if member[A_ACTIVE] == "1" and self.knownas[name].is_active:
                issue(self.knownas[name], E_DUPLICATE, name, "(Known as)")
            else:
                issue(self.knownas[name], E_DUPLICATE, "One is inactive (Known as)", -1)

    def create_entities(self, entities):
        """Create a member objects."""
        i = 0
        for member in entities:
            self.check_duplicate(member)

            data = Member(member, self.scm, self._url)
            self.entities.append(data)
            self.by_guid[data.guid] = data
            self.by_name[data.name] = data
            self.knownas[data.knownas] = data
            if data.asa_number:
                self.by_asa[data.asa_number] = data
            if data.facebook:
                for face in data.facebook:
                    self.facebook[face] = data
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
                self.count_inactive += 1
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

    @property
    def url(self):
        """Return URL."""
        return self._url
