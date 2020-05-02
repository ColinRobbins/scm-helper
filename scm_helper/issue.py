"""Issue handling."""
from datetime import datetime

from scm_helper.config import C_IGNORE_ERROR, C_ISSUES, EXCEPTION_GENERAL, O_NEWSTARTER
from scm_helper.notify import notify

R_COACH = "coaches"
R_CONFIRMATION = "confirmation"
R_DBS = "dbs"
R_GROUP = "groups"
R_MEMBER = "members"
R_SESSION = "sessions"
R_LIST = "lists"
R_ROLE = "roles"

REPORTS = [R_MEMBER, R_COACH, R_DBS, R_GROUP, R_SESSION, R_LIST, R_ROLE, R_CONFIRMATION]

R_PRINT = {
    R_COACH: "Coaches Report",
    R_CONFIRMATION: "Confirmation Report",
    R_DBS: "DBS Report",
    R_GROUP: "Groups Report",
    R_MEMBER: "Members Report",
    R_SESSION: "Sessions Report",
    R_LIST: "Lists Report",
    R_ROLE: "Roles Report",
}

NAME = "name"
MESSAGE = "message"
REPORT = "report"
REVERSE = "reverse"

# errors

# Black directive
# fmt: off
E_ABSENT = {
    NAME: "E_ABSENT",
    MESSAGE: "Absent",
    REVERSE: False,
    REPORT: R_MEMBER}
E_ASA = {
    NAME: "E_ASA",
    MESSAGE: "No Swim England number",
    REVERSE: False,
    REPORT: R_MEMBER}
E_COACH_WITH_SESSIONS = {
    NAME: "E_COACH_WITH_SESSIONS",
    MESSAGE: "Coach with swim sessions in profile",
    REVERSE: False,
    REPORT: R_COACH}
E_COACH_ROLE = {
    NAME: "E_COACH_ROLE",
    MESSAGE: "In coach role, but not a coach",
    REVERSE: False,
    REPORT: R_ROLE}
E_CONFIRM_DIFF = {
    NAME: "E_CONFIRM_DIFF",
    MESSAGE: "Difference in confirmation dates",
    REVERSE: False,
    REPORT: R_CONFIRMATION}
E_CONFIRMATION_EXPIRED = {
    NAME: "E_CONFIRMATION_EXPIRED",
    MESSAGE: "Confirmation expired",
    REVERSE: True,
    REPORT: R_CONFIRMATION}
E_DATE = {
    NAME: "E_DATE",
    MESSAGE: "Error in date format",
    REVERSE: False,
    REPORT: R_MEMBER}
E_DATE_JOINED = {
    NAME: "E_DATE_JOINED",
    MESSAGE: "No date joined",
    REVERSE: False,
    REPORT: R_MEMBER}
E_DBS_EXPIRED = {
    NAME: "E_DBS_EXPIRED",
    MESSAGE: "DBS Expiring/Expired",
    REVERSE: False,
    REPORT: R_DBS}
E_DOB = {
    NAME: "E_DOB",
    MESSAGE: "No date of birth",
    REVERSE: False,
    REPORT: R_MEMBER}
E_DUPLICATE = {
    NAME: "E_DUPLICATE",
    MESSAGE: "Duplicate user",
    REVERSE: False,
    REPORT: R_MEMBER}
E_EMAIL_MATCH = {
    NAME: "E_EMAIL_MATCH",
    MESSAGE: "Swimmers email does not match parents",
    REVERSE: False,
    REPORT: R_MEMBER}
E_EMAIL_SPACE = {
    NAME: "E_EMAIL_SPACE",
    MESSAGE: "Space in email",
    REVERSE: False,
    REPORT: R_MEMBER}
E_GENDER = {
    NAME: "E_GENDER",
    MESSAGE: "No Gender",
    REVERSE: False,
    REPORT: R_MEMBER}
E_INACTIVE = {
    NAME: "E_INACTIVE",
    MESSAGE: "Inactive",
    REVERSE: False,
    REPORT: R_MEMBER}
E_INACTIVE_TOOLONG = {
    NAME: "E_INACTIVE_TOOLONG",
    MESSAGE: "Inactive for too long - consider archiving",
    REVERSE: False,
    REPORT: R_MEMBER}
E_LIST_ERROR = {
    NAME: "E_LIST_ERROR",
    MESSAGE: "Error in email list",
    REVERSE: False,
    REPORT: R_LIST}
E_LOGIN_TOO_YOUNG = {
    NAME: "E_LOGIN_TOO_YOUNG",
    MESSAGE: "Swimmer with login: too young",
    REVERSE: False,
    REPORT: R_MEMBER}
E_JOB = {
    NAME: "E_JOB",
    MESSAGE: "Job description but not a volunteer",
    REVERSE: False,
    REPORT: R_MEMBER}
E_NAME_CAPITAL = {
    NAME: "E_NAME_CAPITAL",
    MESSAGE: "Check name capitilisation",
    REVERSE: False,
    REPORT: R_MEMBER}
E_NEVERSEEN = {
    NAME: "E_NEVERSEEN",
    MESSAGE: "Never seen",
    REVERSE: False,
    REPORT: R_MEMBER}
E_NEVER_ATTENDED = {
    NAME: "E_NEVER_ATTENDED",
    MESSAGE: "Never attended",
    REVERSE: True,
    REPORT: R_SESSION}
E_NO_CHILD = {
    NAME: "E_NO_CHILD",
    MESSAGE: "Parent, no children",
    REVERSE: False,
    REPORT: R_MEMBER}
E_NO_COACH = {
    NAME: "E_NO_COACH",
    MESSAGE: "No coach",
    REVERSE: False,
    REPORT: R_COACH}
E_NO_CONDUCT = {
    NAME: "E_NO_CONDUCT",
    MESSAGE: "Code of Conduct missing",
    REVERSE: True,
    REPORT: R_CONFIRMATION}
E_NO_CONDUCT_DATE = {
    NAME: "E_NO_CONDUCT_DATE",
    MESSAGE: "Code of Conduct not signed",
    REVERSE: True,
    REPORT: R_CONFIRMATION}
E_NO_DBS = {
    NAME: "E_NO_DBS",
    MESSAGE: "No DBS",
    REVERSE: False,
    REPORT: R_DBS}
E_NO_EMAIL = {
    NAME: "E_NO_EMAIL",
    MESSAGE: "No email address",
    REVERSE: False,
    REPORT: R_MEMBER}
E_NO_GROUP = {
    NAME: "E_NO_GROUP",
    MESSAGE: "Swimmer with no group",
    REVERSE: False,
    REPORT: R_GROUP}
E_NO_JOB = {
    NAME: "E_NO_JOB",
    MESSAGE: "No job description",
    REVERSE: False,
    REPORT: R_ROLE}
E_NO_LEAVE_DATE = {
    NAME: "E_NO_LEAVE_DATE",
    MESSAGE: "Inactive member with no leaving date",
    REVERSE: False,
    REPORT: R_MEMBER}
E_NO_LOGIN = {
    NAME: "E_NO_LOGIN",
    MESSAGE: "No login",
    REVERSE: False,
    REPORT: R_MEMBER}
E_NO_PARENT = {
    NAME: "E_NO_PARENT",
    MESSAGE: "Swimmer with no parent",
    REVERSE: False,
    REPORT: R_MEMBER}
E_NO_REGISTER = {
    NAME: "E_NO_REGISTER",
    MESSAGE: "Register not taken",
    REVERSE: False,
    REPORT: R_SESSION}
E_NO_RESTRICTIONS = {
    NAME: "E_NO_RESTRICTIONS",
    MESSAGE: "In role with no restrictions",
    REVERSE: False,
    REPORT: R_ROLE}
E_NO_ROLE_COACH = {
    NAME: "E_NO_ROLE_COACH",
    MESSAGE: "Coach not in a coach role",
    REVERSE: False,
    REPORT: R_ROLE}
E_NO_SAFEGUARD = {
    NAME: "E_NO_SAFEGUARD",
    MESSAGE: "No Safeguarding",
    REVERSE: False,
    REPORT: R_DBS}
E_NO_SESSIONS = {
    NAME: "E_NO_SESSIONS",
    MESSAGE: "Coach with no sessions",
    REVERSE: False,
    REPORT: R_COACH}
E_NO_SWIMMERS = {
    NAME: "E_NO_SWIMMERS",
    MESSAGE: "No swimmers",
    REVERSE: False,
    REPORT: R_SESSION}
E_NOT_A_COACH = {
    NAME: "E_NOT_A_COACH",
    MESSAGE: "Not a coach, but in coach role",
    REVERSE: False,
    REPORT: R_ROLE}
E_NOT_ATTENDED = {
    NAME: "E_NOT_ATTENDED",
    MESSAGE: "Swimmer not attended a session for given period of time",
    REVERSE: True,
    REPORT: R_SESSION}
E_NOT_CONFIRMED = {
    NAME: "E_NOT_CONFIRMED",
    MESSAGE: "Not confirmed",
    REVERSE: True,
    REPORT: R_CONFIRMATION}
E_NOT_IN_SESSION = {
    NAME: "E_NOT_IN_SESSION",
    MESSAGE: "Member not is any sessions for the group",
    REVERSE: True,
    REPORT: R_GROUP}
E_NOT_IN_GROUP = {
    NAME: "E_NOT_IN_GROUP",
    MESSAGE: "Member not in group required for the session",
    REVERSE: True,
    REPORT: R_GROUP}
E_TYPE_GROUP = {
    NAME: "E_TYPE_GROUP",
    MESSAGE: "Member not in group required for the type",
    REVERSE: True,
    REPORT: R_GROUP}
E_NUM_PARENTS = {
    NAME: "E_NUM_PARENTS",
    MESSAGE: "More than two parents",
    REVERSE: False,
    REPORT: R_MEMBER}
E_OWNPARENT = {
    NAME: "E_OWNPARENT",
    MESSAGE: "Swimmer is own parent",
    REVERSE: False,
    REPORT: R_MEMBER}
E_PARENT_AGE = {
    NAME: "E_PARENT_AGE",
    MESSAGE: "Parent too young",
    REVERSE: False,
    REPORT: R_MEMBER}
E_PARENT_AGE_TOO_OLD = {
    NAME: "E_PARENT_AGE_TOO_OLD",
    MESSAGE: "Child too old to have parent",
    REVERSE: False,
    REPORT: R_MEMBER}
E_PERMISSION_EXTRA = {
    NAME: "E_PERMISSION_EXTRA",
    MESSAGE: "Extra session permission",
    REVERSE: False,
    REPORT: R_ROLE}
E_PERMISSION_MISSING = {
    NAME: "E_PERMISSION_MISSING",
    MESSAGE: "Missing permission",
    REVERSE: False,
    REPORT: R_ROLE}
E_SAFEGUARD_EXPIRED = {
    NAME: "E_SAFEGUARD_EXPIRED",
    MESSAGE: "Safeguarding Expiring/Expired",
    REVERSE: False,
    REPORT: R_DBS}
E_SESSIONS = {
    NAME: "E_SESSIONS",
    MESSAGE: "Members has session, but in no sessions group",
    REVERSE: True,
    REPORT: R_SESSION}
E_TOO_OLD = {
    NAME: "E_TOO_OLD",
    MESSAGE: "Too old for group",
    REVERSE: False,
    REPORT: R_GROUP}
E_TOO_YOUNG = {
    NAME: "E_TOO_YOUNG",
    MESSAGE: "Too young for group",
    REVERSE: False,
    REPORT: R_GROUP}
E_TWO_GROUPS = {
    NAME: "E_TWO_GROUPS",
    MESSAGE: "Swimmers in two groups",
    REVERSE: True,
    REPORT: R_GROUP}
E_TYPE = {
    NAME: "E_TYPE",
    MESSAGE: "swimmer has wrong type for group",
    REVERSE: False,
    REPORT: R_GROUP}
E_TYPE_GROUP = {
    NAME: "E_TYPE_GROUP",
    MESSAGE: "Member not in group required for the type",
    REVERSE: True,
    REPORT: R_GROUP}
E_UNKNOWN = {
    NAME: "E_UNKNOWN",
    MESSAGE: "Not a swimmers/parent/coach/official.  Who are they?",
    REVERSE: False,
    REPORT: R_MEMBER}
E_UNUSED_LOGIN = {
    NAME: "E_UNUSED_LOGIN",
    MESSAGE: "Login not used",
    REVERSE: False,
    REPORT: R_ROLE}
E_VOLUNTEER = {
    NAME: "E_VOLUNTEER",
    MESSAGE: "Not marked as a volunteer",
    REVERSE: False,
    REPORT: R_ROLE}

# Black directive
# fmt: on

ISSUE_LIST = [
    E_ABSENT,
    E_ASA,
    E_COACH_ROLE,
    E_COACH_WITH_SESSIONS,
    E_CONFIRM_DIFF,
    E_CONFIRMATION_EXPIRED,
    E_DATE,
    E_DATE_JOINED,
    E_DBS_EXPIRED,
    E_DOB,
    E_DUPLICATE,
    E_EMAIL_MATCH,
    E_EMAIL_SPACE,
    E_GENDER,
    E_INACTIVE,
    E_INACTIVE_TOOLONG,
    E_JOB,
    E_LIST_ERROR,
    E_LOGIN_TOO_YOUNG,
    E_NAME_CAPITAL,
    E_NEVER_ATTENDED,
    E_NEVERSEEN,
    E_NO_CHILD,
    E_NO_COACH,
    E_NO_CONDUCT,
    E_NO_CONDUCT_DATE,
    E_NO_DBS,
    E_NO_EMAIL,
    E_NO_GROUP,
    E_NO_JOB,
    E_NO_LEAVE_DATE,
    E_NO_LOGIN,
    E_NO_PARENT,
    E_NO_REGISTER,
    E_NO_RESTRICTIONS,
    E_NO_ROLE_COACH,
    E_NO_SAFEGUARD,
    E_NO_SESSIONS,
    E_NO_SWIMMERS,
    E_NOT_A_COACH,
    E_NOT_ATTENDED,
    E_NOT_CONFIRMED,
    E_NOT_IN_GROUP,
    E_NOT_IN_SESSION,
    E_NUM_PARENTS,
    E_OWNPARENT,
    E_PARENT_AGE,
    E_PARENT_AGE_TOO_OLD,
    E_PERMISSION_EXTRA,
    E_PERMISSION_MISSING,
    E_SAFEGUARD_EXPIRED,
    E_SESSIONS,
    E_TOO_OLD,
    E_TOO_YOUNG,
    E_TWO_GROUPS,
    E_TYPE,
    E_TYPE_GROUP,
    E_TYPE_GROUP,
    E_UNKNOWN,
    E_UNUSED_LOGIN,
    E_VOLUNTEER,
]

# Handler
HANDLER = None


def issue(xobject, error, msg=None, level=0, msg2=""):
    """Record an issue."""

    debug(f"ISSUE: {xobject.name}, {error[MESSAGE]} / {msg}", 5)

    if level != -1:
        if xobject.print_exception(EXCEPTION_GENERAL) is False:
            debug(f"Error ignored due to exception {xobject.name}", 3)
            return

        if level > HANDLER.debug_level:
            return

        if xobject.newstarter:
            if xobject.scm.option(O_NEWSTARTER):
                pass
            else:
                prefix = "Error ignored - new starter - "
                debug(f"{prefix}{xobject.name}, {error[MESSAGE]} ({msg})", 3)
                return

    HANDLER.add_issue(xobject, error, msg, msg2)


def debug(msg, level):
    """Debug error handler."""
    if level > HANDLER.debug_level:
        return

    msg += "\n"
    notify(msg)


def set_debug_level(level):
    """Set debugging level."""
    if level is None:
        HANDLER.debug_level = 0
        return

    HANDLER.debug_level = level


def debug_trace(level):
    """Decorator to provide a trace capability."""

    def wrap(func):
        def wrapped_f(self, *args):
            name = func.__name__
            xclass = self.__class__.__name__
            xtime = datetime.now().time()
            debug(f"{xtime}: Entry {name}/{xclass}/{self.name}", level)
            retval = func(self, *args)
            debug(f"Exit {self.name}", level)
            return retval

        return wrapped_f

    return wrap


class IssueHandler:
    """report to handle issues."""

    def __init__(self):
        """Initialise."""
        self.issues = []
        self.by_name = {}
        self.by_error = {}
        self.debug_level = 0
        self._config = None
        self.scm = None

        global HANDLER  # pylint: disable=global-statement
        HANDLER = self

    def delete(self):
        """Clear database, ready for rerun."""
        self.issues = []
        self.by_name = {}
        self.by_error = {}

    def add_issue(self, xobject, error, msg, msg2):
        """Record an issue."""
        # Yes, its complicated...
        # pylint: disable=too-many-branches

        if self._config is None:
            self._config = xobject.scm.config(C_ISSUES)
        if self._config is None:
            self._config = []

        if self.scm is None:
            # pylint: disable=protected-access
            self.scm = xobject._scm  # Yuck, but otherwise a loop

        ignore = False

        if error[NAME] in self._config:
            if C_IGNORE_ERROR in self._config[error[NAME]]:
                ignore = self._config[error[NAME]][C_IGNORE_ERROR]
            if MESSAGE in self._config[error[NAME]]:
                error[MESSAGE] = self._config[error[NAME]][MESSAGE]

        if ignore:
            return

        err = error[MESSAGE]
        rpt = error[REPORT]
        rev = error[REVERSE]
        name = xobject.full_name
        create_dict(self.by_name, name, err, msg, msg2, rpt, False, xobject)
        if rev:
            create_dict(self.by_error, err, msg, name, msg2, rpt, rev, xobject)
        else:
            create_dict(self.by_error, err, name, msg, msg2, rpt, rev, xobject)

    def print_by_name(self, reports):
        """Print all issues by name."""
        debug(f"Print by name called {reports}", 6)
        return print_dict(self.by_name, reports)

    def print_by_error(self, reports):
        """Print all issues by error."""
        debug(f"Print by error called {reports}", 6)
        if reports is None:
            res = ""
            for report in REPORTS:
                res += f"========= {R_PRINT[report]} ========\n"
                res += print_dict(self.by_error, report)
            res += "======================="
            return res

        return print_dict(self.by_error, reports)

    def check_issue(self, xissue):
        """Check if this is a valid issue."""
        # pylint: disable=no-self-use
        # if it was a function, you end up with circualr imports
        for anissue in ISSUE_LIST:
            if anissue[NAME] == xissue:
                return True
        return False

    def confirm_email(self):
        """Print email addresses for confirmation errors."""
        matrix = {}
        for anissue in self.by_error:
            for anerror in self.by_error[anissue]:
                pkg = self.by_error[anissue][anerror]
                for line in pkg:
                    _, _, report, _, entity = line
                    if report == R_CONFIRMATION:
                        key = "Other"
                        if entity.is_parent:
                            key = "parent"
                        if entity.is_polo:
                            key = "polo"
                        if entity.is_synchro:
                            key = "synchro"
                        if entity.is_swimmer:
                            key = "swimmer"
                        if key in matrix:
                            matrix[key].append(entity)
                        else:
                            matrix[key] = [entity]

        res = ""
        for msg in matrix:
            res += f"{msg}: \n"
            for entity in matrix[msg]:
                res += f"{entity.email}; "
            res += "\n\n"
        return res


def create_dict(xdict, key1, key2, val1, val2, rpt, rev, entity):
    """Create 2 dimensiaonal dictionary."""
    # pylint: disable=too-many-arguments
    if key1 not in xdict:
        xdict[key1] = {}
    if key2 not in xdict[key1]:
        xdict[key1][key2] = []
    xdict[key1][key2].append([val1, val2, rpt, rev, entity])


def print_dict(xdict, reports):
    """Print all issues."""
    # pylint: disable=too-many-nested-blocks
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    res = ""

    for key1 in sorted(xdict.keys()):
        match = False
        to_print = f"{key1}:\n"
        for key2 in sorted(xdict[key1]):
            to_print += f"    {key2}"

            debug(f"PRINT ISSUE: {key1} / {key2}", 6)
            inner_match = False
            first = True
            length = len(xdict[key1][key2])
            for xissue in sorted(xdict[key1][key2], key=lambda x: x[0]):
                val1, val2, rpt, rev, _ = xissue
                if (first and rev) or (first and (length > 1)):
                    to_print += "\n"
                    first = False
                if (reports and (rpt in reports)) or (reports is None):
                    match = True
                if val1:
                    inner_match = True
                    if rev:
                        spacer = "        "
                    else:
                        val1 = f" ({val1})"
                        if length > 1:
                            spacer = "        "
                        else:
                            spacer = ""
                    if val2:
                        val2 = f" ({val2})"
                    to_print += f"{spacer}{val1}{val2}\n"
            if inner_match is False:
                to_print += "\n"

        if match:
            res += to_print
            res += "\n"

    if res:
        return res
    return "Nothing to report.\n"
