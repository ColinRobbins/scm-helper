"""SCM List."""
from scm_helper.config import (
    A_GUID,
    A_MEMBERS,
    C_ALLOW_GROUP,
    C_EDIT,
    C_GENDER,
    C_GROUP,
    C_LIST,
    C_LISTS,
    C_MAX_AGE,
    C_MAX_AGE_EOY,
    C_MAX_YEAR,
    C_MIN_AGE,
    C_MIN_AGE_EOY,
    C_MIN_YEAR,
    C_SUFFIX,
    C_TYPE,
    C_UNIQUE,
    EXCEPTION_NOEMAIL,
    get_config,
)
from scm_helper.entity import Entities, Entity, check_type
from scm_helper.issue import E_LIST_ERROR, E_NO_SWIMMERS, debug_trace, issue
from scm_helper.notify import notify

A_LISTNAME = "ListName"


class Lists(Entities):
    """Lists."""

    def __init__(self, scm, name, url):
        """Initilaise."""
        super().__init__(scm, name, url)
        self._suffix = None
        self.by_name = {}
        self.newlists = []

    def new_entity(self, entity):
        """Create a new entity for list in SCM."""
        xlist = List(entity, self.scm, self._url)
        self.by_name[xlist.name] = xlist

        return xlist

    def update(self):
        """Create a new list to add to SCM."""
        cfg = get_config(self.scm, C_LISTS)
        if cfg is None:
            return

        if get_config(self.scm, C_LISTS, C_EDIT) is not True:
            notify("List update prohibited by config.\n")
            return

        lists = get_config(self.scm, C_LISTS, C_LIST)
        self._suffix = get_config(self.scm, C_LISTS, C_SUFFIX)

        if lists:
            for xlist in lists:
                newlist = NewList(self.scm, xlist, self._url)
                self.newlists.append(newlist)
                newlist.populate()

        # Separate for loop, as add_to_list may have created some too
        for xlist in self.newlists:
            xlist.generate_data(self._suffix)

            if xlist.upload() is None:
                pass  # not sure what to do, just carry on!

    def delete(self):
        """Delete all members."""
        super().delete()
        for entity in self.newlists:
            entity.delete()
            del entity
        self.newlists = []

    def add(self, name, person):
        """Add a person to a new list."""
        for xlist in self.newlists:
            if xlist.name == name:
                xlist.add_member(person)
                return

        newlist = NewList(self.scm, name, self._url)
        self.newlists.append(newlist)
        newlist.add_member(person)


class List(Entity):
    """An existing list."""

    @debug_trace(5)
    def analyse(self):
        """Analyse existing lists."""
        if len(self.members) == 0:
            issue(self, E_NO_SWIMMERS, "List")
            return

        for member in self.members:
            if member.is_active is False:
                # Never get here as entity linkage prevents it.
                msg = f"Inactive but on email list {self.name} (fixable)"
                issue(member, E_LIST_ERROR, msg)
                if self.newdata and (A_MEMBERS in self.newdata):
                    fix = self.newdata
                else:
                    fix = {}
                    fix[A_MEMBERS] = self.data[A_MEMBERS].copy()
                fix[A_MEMBERS].remove({A_GUID: member.guid})
                self.fixit(fix, f"Delete {member.name}")

            if member.email is None:
                issue(member, E_LIST_ERROR, f"No email, but on email list {self.name}")

    @property
    def name(self):
        """Guid."""
        return self.data["ListName"]


class NewList(Entity):
    """A list."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, scm, xlist, url):
        """Initilaise."""
        # pylint: disable=super-init-not-called
        # Do not call super...
        self.data = None
        self.members = []
        self._scm = scm
        self.ignore = False
        self._name = xlist
        self.new_list = True
        self.newdata = {}
        self.url = url

    def populate(self):
        """Search for entries and fill the list."""
        # pylint: disable=too-many-branches, too-many-statements
        cfg = get_config(self.scm, C_LISTS, C_LIST, self.name)

        # set defaults
        min_age = 0
        if C_MIN_AGE in cfg:
            min_age = cfg[C_MIN_AGE]

        max_age = 999
        if C_MAX_AGE in cfg:
            max_age = cfg[C_MAX_AGE]

        min_age_eoy = 0
        if C_MIN_AGE_EOY in cfg:
            min_age = cfg[C_MIN_AGE_EOY]

        max_age_eoy = 999
        if C_MAX_AGE_EOY in cfg:
            max_age = cfg[C_MAX_AGE_EOY]

        min_year = 1900
        if C_MIN_YEAR in cfg:
            min_year = cfg[C_MIN_YEAR]

        max_year = 2200
        if C_MAX_YEAR in cfg:
            max_year = cfg[C_MAX_YEAR]

        for member in self.scm.members.entities:

            if member.is_active is False:
                continue

            if member.in_ignore_group:
                continue

            if member.age and (member.age < min_age):
                continue

            if member.age and (member.age > max_age):
                continue

            if member.age_eoy and (member.age_eoy < min_age_eoy):
                continue

            if member.age_eoy and (member.age_eoy > max_age_eoy):
                continue

            if member.dob and (member.dob.year > max_year):
                continue

            if member.dob and (member.dob.year < min_year):
                continue

            if C_GROUP in cfg:
                if member.find_group(cfg[C_GROUP]) is False:
                    continue
                if C_UNIQUE in cfg:
                    if len(member.groups) > 1:
                        if C_ALLOW_GROUP not in cfg:
                            continue
                        if member.find_group(cfg[C_ALLOW_GROUP]) is False:
                            continue

            if C_GENDER in cfg:
                gender = cfg[C_GENDER]
                xgender = "F"
                if gender == "male":
                    xgender = "M"
                if member.gender != xgender:
                    continue

            if C_TYPE in cfg:
                xtype = cfg[C_TYPE]
                if check_type(member, xtype) is False:
                    continue

            if member.email is None:
                if member.print_exception(EXCEPTION_NOEMAIL):
                    msg = f"No email, but required for email list {self.name}"
                    issue(member, E_LIST_ERROR, msg)
                continue

            self.add_member(member)

    def generate_data(self, suffix):
        """Create data to upload."""
        listname = f"{self.name}{suffix}"
        self.newdata[A_LISTNAME] = listname
        self.newdata[A_MEMBERS] = []
        for member in self.members:
            self.newdata[A_MEMBERS].append({A_GUID: member})

        xlist = None
        if listname in self.scm.lists.by_name:
            xlist = self.scm.lists.by_name[listname]
            self.newdata[A_GUID] = xlist.guid
            self.new_list = False

    def upload(self):
        """Create data to upload."""
        notify(f"Creating / Updating list: {self.name}\n")
        return self.scm.api_write(self, self.new_list)

    def add_member(self, member):
        """Add a member to the list."""
        self.members.append(member.guid)

    @property
    def name(self):
        """name."""
        return self._name
