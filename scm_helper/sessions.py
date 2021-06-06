"""SCM Session."""
import datetime

from scm_helper.config import (
    A_ARCHIVED,
    A_DATEAGREED,
    A_GUID,
    A_LAST_ATTENDED,
    A_MAX_MEMBERS,
    A_MEMBERS,
    C_ABSENCE,
    C_CONDUCT,
    C_COVID,
    C_DATE,
    C_EXCLUDE_MAX,
    C_GROUPS,
    C_IGNORE_ATTENDANCE,
    C_REGISTER,
    C_SESSION,
    C_SESSIONS,
    PRINT_DATE_FORMAT,
    SCM_DATE_FORMAT,
    get_config,
)
from scm_helper.entity import Entities, Entity
from scm_helper.issue import (
    E_INACTIVE,
    E_NEVER_ATTENDED,
    E_NO_COACH,
    E_NO_REGISTER,
    E_NO_SWIMMERS,
    E_NOT_ATTENDED,
    E_NOT_IN_GROUP,
    E_TOO_MANY_SWIMMERS,
    debug_trace,
    issue,
)
from scm_helper.notify import notify

A_SESSION_NAME = "SessionName"
A_COACHES = "Coaches"


class Sessions(Entities):
    """Sessions."""

    def new_entity(self, entity):
        """Create a new entity."""
        return Session(entity, self.scm, self._url)

    def find_session_substr(self, substr):
        """Find a session from a substring."""
        for session in self.entities:
            if session.name.find(substr) >= 0:
                return session
        return None

    def print_coaches(self):
        """Print coaches per session."""
        res = ""
        for session in sorted(self.entities, key=lambda x: x.full_name):
            if session.is_active:
                res += f"{session.full_name}:\n"
                res += session.print_coaches()
                res += "\n"

        return res

    def print_swimmers_covid(self):
        """Print swimmers and coaches with no COVID dec."""
        covid = get_config(self.scm, C_SESSIONS, C_COVID)
        if covid is None:
            notify("Missing config for COVID option")
            return ""

        res = ""
        for session in sorted(self.entities, key=lambda x: x.full_name):
            if session.is_active:
                c_res = session.print_swimmer_covid()
                if c_res:
                    res += f"{session.full_name}\n{c_res}\n"

        return res


class Session(Entity):
    """A session."""

    def __init__(self, entity, scm, url):
        """Initialise."""
        super().__init__(entity, scm, url)
        self.coaches = []
        self.swimmers = []

        self.ignore_attendance = False
        self.exclude_max = False

        cfg = get_config(
            self.scm, C_SESSIONS, C_SESSION, self.name, C_IGNORE_ATTENDANCE
        )
        if cfg:
            self.ignore_attendance = cfg

        cfg = get_config(self.scm, C_SESSIONS, C_SESSION, self.name, C_EXCLUDE_MAX)
        if cfg:
            self.exclude_max = cfg

    def linkage(self, members):
        """Link coaches and swimmers."""
        if self.is_active is False:
            return

        super().linkage(members)

        if self.data[A_COACHES]:
            for coach in self.data[A_COACHES]:
                guid = members.by_guid[coach[A_GUID]]
                if guid.is_active:
                    self.coaches.append(guid)
                    guid.add_coach_session(self)
                else:
                    if self.ignore_attendance is False:
                        issue(self, E_INACTIVE, "(Coach)")
                if A_LAST_ATTENDED in coach:
                    lastseen = coach[A_LAST_ATTENDED]
                    if lastseen:
                        guid.set_lastseen(lastseen)
        else:
            if self.is_active:
                issue(self, E_NO_COACH)

        # super() has already done member links, now search for last seen...
        if A_MEMBERS in self.data:
            for swimmer in self.data[A_MEMBERS]:
                guid = members.by_guid[swimmer[A_GUID]]
                guid.add_session(self)
                if A_LAST_ATTENDED in swimmer:
                    lastseen = swimmer[A_LAST_ATTENDED]
                    if lastseen:
                        guid.set_lastseen(lastseen)

    def print_coaches(self):
        """Print coaches."""
        res = ""
        absence = get_config(self.scm, C_SESSIONS, C_ABSENCE)
        for coach in self.data[A_COACHES]:
            guid = self.scm.members.by_guid[coach[A_GUID]]
            if guid.is_active:
                msg = ""
                lastseen = coach.get(A_LAST_ATTENDED, None)
                if lastseen:
                    when = datetime.datetime.strptime(lastseen, SCM_DATE_FORMAT)
                    if (self.scm.today - when).days > absence:
                        msg = f"(Lastseen: {lastseen})"
                else:
                    msg = "(Never seen)"
                res += f"   {guid.name} {msg}\n"

        return res

    def print_swimmer_covid(self):
        """Print swimmers."""
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        res = None
        covid = get_config(self.scm, C_SESSIONS, C_COVID)
        c_date_str = get_config(self.scm, C_CONDUCT, covid, C_DATE)
        if c_date_str is None:
            c_date_str = "1900-01-01"
        c_date = datetime.datetime.strptime(c_date_str, SCM_DATE_FORMAT)

        c_res = "  Coaches:\n"
        found = False
        for coach in self.data[A_COACHES]:
            swimmer = self.scm.members.by_guid[coach[A_GUID]]

            if swimmer.is_active:
                declaration = False
                code = swimmer.get_conduct_name(covid)
                if code:
                    code_members = code.data[A_MEMBERS]
                    for member in code_members:
                        code_member = self.scm.members.by_guid[member[A_GUID]]
                        if code_member == swimmer:
                            if member[A_DATEAGREED]:
                                m_date = datetime.datetime.strptime(
                                    member[A_DATEAGREED], SCM_DATE_FORMAT
                                )
                                if m_date > c_date:
                                    declaration = True

                if not declaration:
                    c_res += f"   {swimmer.name} (last seen: {swimmer.lastseen_str})\n"
                    found = True

        if found:
            res = c_res

        s_res = "  Swimmers:\n"
        found = False
        for swimmer in self.members:
            if swimmer.is_active:
                declaration = False
                code = swimmer.get_conduct_name(covid)
                if code:
                    code_members = code.data[A_MEMBERS]
                    for member in code_members:
                        code_member = self.scm.members.by_guid[member[A_GUID]]
                        if code_member == swimmer:
                            if member[A_DATEAGREED]:
                                m_date = datetime.datetime.strptime(
                                    member[A_DATEAGREED], SCM_DATE_FORMAT
                                )
                                if m_date > c_date:
                                    declaration = True

                if not declaration:
                    s_res += f"   {swimmer.name} (last seen: {swimmer.lastseen_str})\n"
                    found = True
        if found:
            if res:
                res += s_res
            else:
                res = s_res

        return res

    @debug_trace(5)
    def analyse(self):
        """Analyse the session."""
        # pylint: disable=too-many-branches
        if self.is_active is False:
            return

        if len(self.members) == 0:
            issue(self, E_NO_SWIMMERS, "Session")
            return

        cfg = get_config(self.scm, C_SESSIONS)
        absence = cfg.get(C_ABSENCE, 9999)
        register = cfg.get(C_REGISTER, 9999)

        groups = get_config(self.scm, C_SESSIONS, C_SESSION, self.name, C_GROUPS)

        seen = None
        n_swimmers = 0

        for swimmer in self.data[A_MEMBERS]:
            found = False
            lastseen = None
            person = self.scm.members.by_guid[swimmer[A_GUID]]

            n_swimmers += 1

            if person.newstarter:
                continue

            if groups:
                for group in groups:
                    if person.find_group(group):
                        found = True
                        break

                if found is False:
                    issue(
                        person,
                        E_NOT_IN_GROUP,
                        f"{self.full_name}",
                        0,
                        person.print_groups,
                    )

            if self.ignore_attendance is False:
                attr = swimmer.get(A_LAST_ATTENDED, False)
                if attr:
                    lastseen = datetime.datetime.strptime(attr, SCM_DATE_FORMAT)
                    if (self.scm.today - lastseen).days > absence:
                        msg = lastseen.strftime(PRINT_DATE_FORMAT)
                        issue(
                            person,
                            E_NOT_ATTENDED,
                            f"{self.full_name}",
                            0,
                            f"Last seen: {msg}",
                        )
                    if (seen is None) or (lastseen > seen):
                        seen = lastseen
                else:
                    if absence != 9999:
                        issue(person, E_NEVER_ATTENDED, f"{self.full_name}")

        if n_swimmers > self.max_members:
            issue(self, E_TOO_MANY_SWIMMERS, f"{n_swimmers} > {self.max_members}")

        if (self.ignore_attendance is False) and (register != 9999):
            msg = "Never"
            if seen:
                if (self.scm.today - seen).days > register:
                    msg = seen.strftime(PRINT_DATE_FORMAT)
                else:
                    return
            issue(self, E_NO_REGISTER, f"last taken: {msg} ({self.full_name})")

    @property
    def name(self):
        """Name."""
        return self.data[A_SESSION_NAME]

    @property
    def full_name(self):
        """Full session name."""
        name = self.data[A_SESSION_NAME]
        weekday = self.data["WeekDay"]
        location = self.data["SessionLocation"]
        time = self.data["StartTime"]
        return f"{name}, {weekday}, {location}, {time}"

    @property
    def is_active(self):
        """Is the entry active..."""
        if A_ARCHIVED in self.data:
            if self.data[A_ARCHIVED] == 0:
                return True
        return False

    @property
    def max_members(self):
        """Is the entry active..."""
        if A_MAX_MEMBERS in self.data:
            return self.data[A_MAX_MEMBERS]

        return 9999
