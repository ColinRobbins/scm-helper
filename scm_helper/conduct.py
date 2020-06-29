"""SCM Conduct."""
from scm_helper.config import (
    A_GUID,
    A_MEMBERS,
    C_CONDUCT,
    C_IGNORE_GROUP,
    C_LISTS,
    C_TYPES,
    CTYPE_COACH,
    CTYPE_COMMITTEE,
    CTYPE_PARENT,
    CTYPE_SWIMMER,
    CTYPE_VOLUNTEER,
    get_config,
)
from scm_helper.entity import Entities, Entity
from scm_helper.issue import E_NO_CONDUCT, E_NO_CONDUCT_DATE, debug_trace, issue
from scm_helper.notify import notify


class CodesOfConduct(Entities):
    """Conduct."""

    def get_data(self):
        """
        Get member data.

        For some reason the API behaves differently,
        we need to read each one...
        """
        self._raw_data = []

        notify(f"{self._name}... ")

        entities = self.scm.api_read(self._url, 1)
        if entities is None:
            return False
        page = 1

        for entity in entities:
            guid = entity["Guid"]
            notify(f"{page} ")

            api_data = self.scm.api_read(f"{self._url}/{guid}", 1)
            if api_data is None:
                return False
            self._raw_data += [api_data]

            data = self.new_entity(api_data)
            self.entities.append(data)
            self.by_guid[data.guid] = data
            self.by_name[data.name] = data

            if data.is_active:
                self.count += 1
            page += 1

        notify("\n")

        return True

    def new_entity(self, entity):
        """Create a new entity."""
        return Conduct(entity, self.scm, self._url)

    @debug_trace(5)
    def analyse(self):
        """Analise the conduct class."""
        if get_config(self.scm, C_CONDUCT) is None:
            return

        for code in self.entities:
            code.analyse()


class Conduct(Entity):
    """A conduct instance."""

    def __init__(self, entity, scm, url):
        """Initialise."""
        super().__init__(entity, scm, url)
        self._raw_data = entity

    def linkage(self, members):
        """Link code."""
        super().linkage(members)
        for member in self.members:
            member.add_conduct(self)

    def analyse(self):
        """Analise the conduct entry."""
        # A better way of doing this would be to add
        # the attribute to the swimmer in linkage.
        # This approach breaks the model. Oh well.
        for member in self.data[A_MEMBERS]:

            if member["DateAgreed"]:
                continue

            person = self.scm.members.by_guid[member[A_GUID]]
            if person.confirmed_date:  # Will get a not confirmed error later in not set
                issue(person, E_NO_CONDUCT_DATE, self.name)
                codes = get_config(self.scm, C_LISTS, C_CONDUCT)
                if codes:
                    for code in codes:
                        if self.name == code:
                            msg = f"{self.name} missing"
                            self.scm.lists.add(msg, person)

    @property
    def name(self):
        """Name."""
        return self.data["Title"]


# Outside of class
def check_conduct(member, my_codes):
    """Analise a code of conduct."""
    # pylint: disable=too-many-branches

    if get_config(member.scm, C_CONDUCT) is None:
        return

    type_dict = {
        CTYPE_SWIMMER: member.is_swimmer,
        CTYPE_PARENT: member.is_parent,
        CTYPE_COACH: member.is_coach,
        CTYPE_COMMITTEE: member.is_committee_member,
        CTYPE_VOLUNTEER: member.is_volunteer,
    }

    codes = member.scm.conduct.entities

    for code in codes:
        ignores = get_config(member.scm, C_CONDUCT, code.name, C_IGNORE_GROUP)

        found_ignore = False
        if ignores:
            for ignore in ignores:
                if member.find_group(ignore):
                    found_ignore = True
        if found_ignore:
            continue

        types = get_config(member.scm, C_CONDUCT, code.name, C_TYPES)
        if types is None:
            return

        for atype in types:
            found = False
            func = type_dict[atype]
            if func is True:
                for my_code in my_codes:
                    if my_code == code:
                        found = True
                        break
                if found is False:
                    issue(member, E_NO_CONDUCT, f"{code.name}")

                    # TODO - Need SCM bug fix first
                    # if code.newdata and (A_MEMBERS in code.newdata):
                    #    fix = code.newdata
                    # else:
                    #    fix = {}
                    #    fix[A_MEMBERS] = code.data[A_MEMBERS].copy()
                    # add = {A_GUID: member.guid}
                    # fix[A_MEMBERS].append(add)
                    # code.fixit(fix, f"Add {member.name}")
