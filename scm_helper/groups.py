"""SCM Group."""
import datetime

from scm_helper.config import (
    C_CHECK_DBS,
    C_CONFIRMATION,
    C_GROUP,
    C_GROUPS,
    C_IGNORE_GROUP,
    C_IGNORE_SWIMMER,
    C_MAX_AGE,
    C_MIN_AGE,
    C_NO_CLUB_SESSIONS,
    C_NO_SESSION_ALLOWED,
    C_NO_SESSIONS,
    C_SESSIONS,
    C_TYPE,
    CTYPE_COACH,
    CTYPE_SWIMMER,
    EXCEPTION_GROUPNOSESSION,
    EXCEPTION_NONSWIMMINGMASTER,
    SCM_CSV_DATE_FORMAT,
    get_config,
)
from scm_helper.entity import Entities, Entity, check_type
from scm_helper.issue import (
    E_CONFIRMATION_EXPIRED,
    E_NO_SWIMMERS,
    E_NOT_IN_SESSION,
    E_SESSIONS,
    E_TYPE,
    debug,
    debug_trace,
    issue,
)
from scm_helper.notify import notify

A_GROUP_NAME = "GroupName"


class Groups(Entities):
    """Groups."""

    def new_entity(self, entity):
        """Create a new entity."""
        return Group(entity, self.scm, self._url)


class Group(Entity):
    """A group."""

    def linkage(self, members):
        """Link members."""
        super().linkage(members)

        no_session = self.config_item(C_NO_CLUB_SESSIONS)
        ignore_group = self.config_item(C_IGNORE_GROUP)
        ignore_swimmer = self.config_item(C_IGNORE_SWIMMER)

        if self.members:
            for swimmer in self.members:
                swimmer.add_group(self)
                if no_session:
                    swimmer.set_no_session_ok()
                if ignore_swimmer:
                    swimmer.set_ignore_swimmer(True)
                if ignore_group:
                    swimmer.set_ignore_group(True)

    @debug_trace(5)
    def analyse(self):
        """Analise the group."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        no_session = False
        check_dbs = False
        wanted_session = None
        allowed = None
        xtype = None
        ignore = None
        confirm = None

        if self.config:
            ignore = self.config_item(C_IGNORE_GROUP)
            no_session = self.config_item(C_NO_SESSIONS)
            check_dbs = self.config_item(C_CHECK_DBS)
            wanted_sessions = self.config_item(C_SESSIONS)
            allowed = self.config_item(C_NO_SESSION_ALLOWED)
            xtype = self.config_item(C_TYPE)
            confirm = self.config_item(C_CONFIRMATION)

        if ignore:
            debug(f"Ignoring group {self.name}", 7)
            return

        if len(self.members) == 0:
            issue(self, E_NO_SWIMMERS, "Group")
            return

        if no_session:
            for member in self.members:
                if len(member.sessions) > 0:
                    name = member.sessions[0].name
                    issue(member, E_SESSIONS, f"Group: {self.name}, Session: {name}")

        if confirm:
            try:
                date = datetime.datetime.strptime(confirm, SCM_CSV_DATE_FORMAT)
                confirm = date
            except ValueError:
                notify(
                    f"*** Error in date format in config file for groups config: {confirm} ***\n"
                )
                confirm = None

        for member in self.members:
            self.check_age(member)
            if check_dbs:
                member.check_dbs(self.name)

            if confirm:
                err = False
                if member.confirmed_date:
                    gap = (confirm - member.confirmed_date).days
                    if gap >= 0:
                        err = True
                else:
                    err = True

                if err:
                    issue(member, E_CONFIRMATION_EXPIRED, f"Group: {self.name}")
                    msg = f"Confirmation Expired for Group: {member.name}"
                    member.scm.lists.add(msg, member)

            if member.newstarter:
                continue

            if wanted_session:
                for session in wanted_sessions:
                    if check_in_session(member, session, allowed) is False:
                        res1 = self.print_exception(EXCEPTION_NONSWIMMINGMASTER)
                        res2 = self.print_exception(EXCEPTION_GROUPNOSESSION)
                        if res1 or res2:
                            issue(member, E_NOT_IN_SESSION, f"Group: {self.name}")
                    break

            if xtype:
                if check_type(member, xtype):
                    continue
                if xtype == CTYPE_SWIMMER:  # if swimmers wanted, allow it to be a coach
                    if check_type(member, CTYPE_COACH) is False:
                        msg = f"Group: {self.name}, Type required: {xtype}"
                        issue(member, E_TYPE, msg)

    def check_age(self, swimmer):
        """Check in right age group."""
        mymin = 3
        mymax = 100

        max_age = self.config_item(C_MAX_AGE)
        if max_age:
            mymax = max_age

        min_age = self.config_item(C_MIN_AGE)
        if min_age:
            mymin = min_age

        if max_age or min_age:
            swimmer.check_age(mymin, mymax, self.name)

    @property
    def name(self):
        """Guid."""
        return self.data[A_GROUP_NAME]

    @property
    def config(self):
        """Own config parameters..."""
        return get_config(self.scm, C_GROUPS, C_GROUP, self.name)

    def config_item(self, item):
        """Own config parameters..."""
        return get_config(self.scm, C_GROUPS, C_GROUP, self.name, item)


def check_in_session(swimmer, wanted_session, allowed):
    """Check swimmer in session."""
    in_session = False
    if swimmer.find_session_substr(wanted_session):
        in_session = True

    if allowed and in_session is False:
        for allow in allowed:
            if swimmer.find_group(allow):
                in_session = True

    if in_session is False:
        if swimmer.no_session_ok:
            return True
        if swimmer.is_coach:
            return True
        return False

    return True
