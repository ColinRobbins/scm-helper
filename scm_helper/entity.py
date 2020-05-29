"""SCM entity superclass."""
import csv
import datetime
import json
import pprint
import sys

from scm_helper.config import (
    A_ACTIVE,
    A_ARCHIVED,
    A_GUID,
    A_MEMBERS,
    CTYPE_COACH,
    CTYPE_COMMITTEE,
    CTYPE_OPENWATER,
    CTYPE_PARENT,
    CTYPE_POLO,
    CTYPE_SWIMMER,
    CTYPE_SYNCHRO,
    CTYPE_VOLUNTEER,
    SCM_DATE_FORMAT,
)
from scm_helper.issue import E_INACTIVE, debug, debug_trace, issue
from scm_helper.notify import interact, interact_yesno, notify


class Entities:
    """Superclass for Entities."""

    # pylint: disable=too-many-instance-attributes
    # Need them all!

    def __init__(self, scm, name, url):
        """Initialize."""
        self.entities = []
        self.by_guid = {}
        self.by_name = {}
        self.knownas = {}
        self.scm = scm
        self._name = name
        self._url = url
        self.count = 0
        self._raw_data = []

    def get_data(self):
        """Get data."""
        notify(f"{self._name}... ")
        loop = 100
        page = 1
        count = 0
        while loop == 100:
            if count != 0:
                notify(f"{count} ")
            data = self.scm.api_read(self._url, page)
            if data is None:
                return False
            loop = self.create_entities(data)
            self._raw_data += data
            page += 1
            count += loop

        notify(f"{count}\n")
        return True

    def parse_data(self, data):
        """Read data."""
        notify(f"{self._name}...\n")
        self._raw_data = data
        self.create_entities(self._raw_data)

    def create_entities(self, entities):
        """Create entities."""
        i = 0
        for entity in entities:
            data = self.new_entity(entity)
            if data:
                self.entities.append(data)
                if data.guid:  # Who's who does not have a GUID
                    self.by_guid[data.guid] = data
                self.by_name[data.name] = data
                if data.is_active:
                    self.count += 1
            i += 1
        return i

    def new_entity(self, entity):
        """Create a new entity - OVERRIDE expected."""
        return Entity(entity, self.scm, self._url)

    def analyse(self):
        """Analise the members."""
        for entity in self.entities:
            entity.analyse()

    def linkage(self):
        """Create Member links."""
        for entity in self.entities:
            entity.linkage(self.scm.members)

    def print_name(self):
        """Print name."""
        for entity in self.entities:
            print(entity.name)

    def delete(self):
        """Delete all members."""
        for entity in self.entities:
            entity.delete()
            del entity
        self.entities = []
        self.by_guid = {}
        self.by_name = {}
        self.knownas = {}
        self.count = 0
        self._raw_data = []

    def restore(self, xtype):
        """Restore a record."""
        name = interact(f"Enter name of {xtype} to restore: ")
        if name in self.by_name:
            return self.by_name[name].restore(self._url)
        if name in self.knownas:
            return self.knownas[name].restore(self._url)

        notify(f"{name} not found in backup of {xtype}.\n")
        return False

    @property
    def json(self):
        """JSON dump."""
        return json.dumps(self._raw_data)

    def pretty_print(self):
        """JSON dump."""
        print(json.dumps(self._raw_data, indent=4))

    def csv(self):
        """CSV dump."""
        output = csv.writer(sys.stdout)
        output.writerow(self._raw_data[0].keys())  # header row
        for row in self._raw_data:
            output.writerow(row.values())  # values row

    def print_summary(self):
        """Print a summary."""
        return f"{self._name}: {self.count}\n"

    @property
    def name(self):
        """Return name."""
        return self._name


class Entity:
    """A entity."""

    def __init__(self, entity, scm, url):
        """Initialize."""
        self.data = entity
        self.newdata = None  # used if updating
        self.fixmsg = ""
        self.url = f"{url}/{self.guid}"
        self.members = []
        self._scm = scm

    def print_exception(self, exception):
        """Is the exception allowable."""
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        # Override uses exception
        return True

    @debug_trace(6)
    def linkage(self, members):
        """Link members."""
        if (A_MEMBERS in self.data) and (len(self.data[A_MEMBERS]) > 0):
            for swimmer in self.data[A_MEMBERS]:
                if swimmer[A_GUID] not in members.by_guid:
                    msg = (
                        f"GUID {swimmer[A_GUID]} missing in list - email address only?"
                    )
                    debug(msg, 7)
                    continue
                guid = members.by_guid[swimmer[A_GUID]]
                if guid.is_active:
                    self.members.append(guid)
                else:
                    name = guid.name
                    issue(self, E_INACTIVE, f"member {name}", 0, "Fixable")

                    if self.newdata and (A_MEMBERS in self.newdata):
                        fix = self.newdata
                    else:
                        fix = {}
                        fix[A_MEMBERS] = self.data[A_MEMBERS].copy()
                    remove = {A_GUID: guid.guid}
                    fix[A_MEMBERS].remove(remove)
                    self.fixit(fix, f"Delete {guid.name} (inactive)")

    def check_attribute(self, attribute):
        """Return the value, if there is one."""
        if attribute in self.data:
            if self.data[attribute]:
                return self.data[attribute]
        return None

    def set_date(self, field):
        """Set a date."""
        date = self.check_attribute(field)
        if date is None:
            return None
        return datetime.datetime.strptime(date, SCM_DATE_FORMAT)

    def delete(self):
        """Delete."""
        # pylint: disable=no-self-use
        # override if anything needs doing
        return

    def print_links(self):
        """Print links."""
        # pylint: disable=no-self-use
        # override if anything needs doing
        return ""

    def restore(self):
        """Update a record from backup."""
        # pylint: disable=too-many-return-statements
        self.newdata = self.data

        old = self.scm.api_read(self.url, 1)
        if old is None:
            notify("Error: Something went wrong connecting to SCM!\n")
            return False

        # API inconsistent in use of Archive or Active - check both.
        if A_ACTIVE in self.newdata:
            self.newdata[A_ACTIVE] = "1"  # Make sure active

        if A_ARCHIVED in self.newdata:
            self.newdata[A_ARCHIVED] = "1"  # Make sure active

        if old is False:
            del self.newdata[A_GUID]  # Will need a new GUID
            # SCM does not provide the PUSH/PUT options for sessions and groups
            # Would be a lot of code anyway - is it needed?
            # So print help...
            notify(self.print_links())
            return self.scm.api_write(self, True)

        if A_ACTIVE in old:
            if old[A_ACTIVE] == "1":
                return self.scm.api_write(self, False)

            notify("Error: Already exist, just inactive.  Re-activate in SCM.\n")
            return False

        if A_ARCHIVED in old:
            if old[A_ARCHIVED] == 0:
                # API is inconsistent here too - no quotes for this one.
                return self.scm.api_write(self, False)

            notify("Error: Already exist, just archived.  Re-activate in SCM\n")
            return False

        return self.scm.api_write(self, False)

    def fixit(self, fix, message):
        """Prepare to fix an entity."""
        if self.newdata is None:
            self.newdata = fix
            self.fixmsg = message
        else:
            self.newdata.update(fix)
            self.fixmsg += f", {message}"

        if self in self.scm.fixable:
            return
        self.scm.fixable.append(self)

    def apply_fix(self):
        """Fix an entity."""
        printer = pprint.PrettyPrinter(indent=4)
        data = printer.pformat(self.newdata)
        err = f"Fix '{self.name}' with:\n    {self.fixmsg}\nConfirm"
        debug("fixit:", 7)
        debug(data, 8)
        resp = interact_yesno(err)
        if resp is False:
            return False

        self.newdata[A_GUID] = self.guid

        notify(f"Fixing: {self.name}...")

        res = self.scm.api_write(self, False)

        if res:
            notify("Success.\n")
        return res

    @property
    def guid(self):
        """Guid."""
        if A_GUID in self.data:
            return self.data[A_GUID]
        return None

    @property
    def name(self):
        """Must override."""
        return "Name error - no override"

    @property
    def full_name(self):
        """Return full name (if overridden)."""
        return self.name

    @property
    def is_active(self):
        """Is the entity active - True unless overridden."""
        return True

    @property
    def newstarter(self):
        """Is the member a new stater - override in members.py."""
        return False

    @property
    def scm(self):
        """Return SCM entry."""
        return self._scm


# Not part of class
def check_type(member, xtype):
    """Check each type for a match."""
    # pylint: disable=too-many-return-statements
    # Need them all!
    if xtype == CTYPE_SWIMMER:
        return member.is_swimmer

    if xtype == CTYPE_SYNCHRO:
        return member.is_synchro

    if xtype == CTYPE_COACH:
        return member.is_coach

    if xtype == CTYPE_COMMITTEE:
        return member.is_committee

    if xtype == CTYPE_OPENWATER:
        return member.is_openwater

    if xtype == CTYPE_PARENT:
        return member.is_parent

    if xtype == CTYPE_POLO:
        return member.is_polo

    if xtype == CTYPE_VOLUNTEER:
        return member.is_volunteer

    return False


def get_date(date, xformat):
    """Parse a date."""
    try:
        res = datetime.datetime.strptime(date, xformat)
        return res
    except ValueError as error:
        notify(f"Error in date: {error}")
        return None


def print_all(xlist):
    """Print out the entity."""
    grp = None
    for obj in xlist:
        if grp:
            grp += f", {obj.name}"
        else:
            grp = obj.name
    if grp is None:
        grp = "None"

    return grp


class Who(Entities):
    """Subclass for Who's who."""

    # pylint: disable=too-many-instance-attributes
    # Need them all!

    def get_data(self):
        """Get data."""
        notify(f"{self._name}... ")

        data = self.scm.api_read(self._url, 1)
        if data is None:
            return False
        count = self.create_entities(data)
        # line below is subtly different, who's who data is already a list.
        self._raw_data = data

        notify(f"{count}\n")
        if count != 1:
            debug("Who's who assumption failure", 0)

        return True
