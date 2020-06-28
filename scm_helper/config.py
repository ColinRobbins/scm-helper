"""Configuration stuff."""
from schema import And, Optional, Schema, SchemaError
from scm_helper.notify import notify
from scm_helper.version import VERSION

# SCM access URLs etc
URL_BASE = "https://api.swimclubmanager.co.uk"

URL_CONDUCT = f"{URL_BASE}/CodeOfConduct"
URL_EVENTS = f"{URL_BASE}/ClubEvents"
URL_GROUPS = f"{URL_BASE}/ClubGroups"
URL_INCIDENTBOOK = f"{URL_BASE}/IncidentBook"
URL_LISTS = f"{URL_BASE}/EmailLists"
URL_MEETS = f"{URL_BASE}/Meets"
URL_MEMBERS = f"{URL_BASE}/Members"
URL_NOTICE = f"{URL_BASE}/NoticeBoard"
URL_ROLES = f"{URL_BASE}/ClubRoles"
URL_SESSIONS = f"{URL_BASE}/ClubSessions"
URL_TRIALS = f"{URL_BASE}/TrialRequests"
URL_WAITINGLIST = f"{URL_BASE}/WaitingList"
URL_WHO = f"{URL_BASE}/WhosWho"

HELPURL = "https://github.com/ColinRobbins/scm-helper/wiki"

USER_AGENT = f"SCM-Helper-v{VERSION} ###CLUB_NAME###"

# Do not change below here...

BACKUP_DIR = "backups"
CONFIG_DIR = "scm-helper"
CONFIG_FILE = "config.yaml"
KEYFILE = "apikey.enc"
RECORDS_DIR = "records"

CODES_OF_CONDUCT = "Conduct"
EVENTS = "Club Events"
GROUPS = "Groups"
INCIDENTBOOK = "Incident Book"
LISTS = "Lists"
MEETS = "Meets"
MEMBERS = "Members"
NOTICE = "Notice Board"
ROLES = "Roles"
SESSIONS = "Sessions"
TRIALS = "Trial Requests"
WAITINGLIST = "Waiting List"
WHO = "Whos Who"

BACKUP_URLS = [
    [INCIDENTBOOK, URL_INCIDENTBOOK],
    [EVENTS, URL_EVENTS],
    [MEETS, URL_MEETS],
    [TRIALS, URL_TRIALS],
    [WAITINGLIST, URL_WAITINGLIST],
    [NOTICE, URL_NOTICE],
]


FILE_READ = "r"
FILE_WRITE = "w"

# JSON labels
GUID = "Guid"

# Exceptions in Notes
EXCEPTION_EMAILDIFF = "API: different email OK"
EXCEPTION_GENERAL = "API: Exception"
EXCEPTION_GROUPNOSESSION = "API: no sessions OK"
EXCEPTION_NODBS = "API: Coach no DBS OK"
EXCEPTION_NOEMAIL = "API: no email OK"
EXCEPTION_NOGROUPS = "API: no groups OK"
EXCEPTION_NONSWIMMINGMASTER = "API: non swimming master"
EXCEPTION_NOSAFEGUARD = "API: Coach no Safeguard OK"
EXCEPTION_NOSESSIONS = "API: Coach no sessions"
EXCEPTION_PERMISSIONS = "API: Coach permission OK"
EXCEPTION_TWOGROUPS = "API: two groups OK"

SCM_DATE_FORMAT = "%Y-%m-%d"
PRINT_DATE_FORMAT = "%d-%m-%Y"
SCM_CSV_DATE_FORMAT = "%d/%m/%Y"

# SCM Data Attributes
A_ACTIVE = "Active"
A_ARCHIVED = "Archived"
A_ASA_CATEGORY = "ASACategory"
A_ASA_NUMBER = "ASANumber"
A_DOB = "DOB"
A_FIRSTNAME = "Firstname"
A_GUID = "Guid"
A_ISCOACH = "IsACoach"
A_ISPARENT = "IsAParent"
A_ISVOLUNTEER = "IsAVolunteer"
A_KNOWNAS = "KnownAs"
A_LAST_ATTENDED = "LastAttended"
A_LASTNAME = "Lastname"
A_MEMBERS = "Members"
A_PARENTS = "Parents"
A_USERNAME = "Username"

# Config parameters
C_ABSENCE = "absence"
C_AGE = "age"
C_AGE_EOY = "age_eoy"
C_ALIGN_QUARTER = "align_quarter"
C_ALLOW_GROUP = "allow_group"
C_ALLOW_UPDATE = "allow_update"
C_ALL_AGES = "all_ages_u18"
C_BASE_URL = "base_url"
C_BROWSER = "browser"
C_CHECK_DBS = "check_dbs"
C_CHECK_PERMISSIONS = "check_permissions"
C_CHECK_RESTRICTIONS = "check_restrictions"
C_CHECK_SE_NUMBER = "check_se_number"
C_CHECK_URL = "check_url"
C_CHILD = "child"
C_CLASS = "class"
C_CLUB = "club"
C_COACH = "coach"
C_COACHES = "coaches"
C_CONDUCT = "conduct"
C_CONF_DIFF = "confirmation_difference"
C_CONFIRMATION = "confirmation"
C_DBS = "dbs"
C_DEBUG_LEVEL = "debug_level"
C_DOB_FORMAT = "dob_format"
C_EDIT = "edit"
C_EMAIL = "email"
C_EXPIRY = "expiry"
C_FACEBOOK = "facebook"
C_FILES = "files"
C_GENDER = "gender"
C_GRACE = "grace"
C_GROUP = "group"
C_GROUPS = "groups"
C_IGNORE = "ignore"
C_IGNORE_ATTENDANCE = "ignore_attendance"
C_IGNORE_COACH = "ignore_coach"
C_IGNORE_COMMITTEE = "ignore_committee"
C_IGNORE_ERROR = "ignore_error"
C_IGNORE_GROUP = "ignore_group"
C_IGNORE_SWIMMER = "ignore_swimmer"
C_IGNORE_UNKNOWN = "ignore_unknown"
C_INACTIVE = "inactive"
C_IS_COACH = "is_coach"
C_ISSUES = "issues"
C_JOBTITLE = "jobtitle"
C_LIST = "list"
C_LISTS = "lists"
C_LOGIN = "login"
C_MANDATORY = "mandatory"
C_MAPPING = "mapping"
C_MAX_AGE = "max_age"
C_MAX_AGE_EOY = "max_age_eoy"
C_MAX_YEAR = "max_year"
C_MEMBERS = "members"
C_MESSAGE = "message"
C_MIN_AGE = "min_age"
C_MIN_AGE_EOY = "min_age_eoy"
C_MIN_YEAR = "min_year"
C_NAME = "name"
C_NEWSTARTER = "newstarter"
C_NO_CLUB_SESSIONS = "no_club_sessions"
C_NO_SESSION_ALLOWED = "no_session_allowed"
C_NO_SESSIONS = "no_sessions"
C_OVERALL_FASTEST = "overall_fastest"
C_PARENT = "parent"
C_PARENTS = "parents"
C_PASSWORD = "password"
C_PRIORITY = "priority"
C_RECORDS = "records"
C_REGISTER = "register"
C_RELAY = "relay"
C_ROLE = "role"
C_ROLES = "roles"
C_SELENIUM = "selenium"
C_SEND_TO = "send_to"
C_SE_ONLY = "se_only"
C_SESSION = "session"
C_SESSIONS = "sessions"
C_SMTP_PORT = "smtp_port"
C_SMTP_SERVER = "smtp_server"
C_SUFFIX = "suffix"
C_SWIM_ENGLAND = "swim_england"
C_SWIMMER = "swimmer"
C_SWIMMERS = "swimmers"
C_TEST_ID = "test_id"
C_TIME = "time"
C_TLS = "tls"
C_TYPE = "type"
C_TYPES = "types"
C_UNIQUE = "unique"
C_UNUSED = "unused"
C_USERNAME = "username"
C_VERIFY = "verify"
C_VOLUNTEER = "volunteer"
C_WEB_DRIVER = "web_driver"


CTYPE_COACH = "coach"
CTYPE_COMMITTEE = "committee"
CTYPE_OPENWATER = "openwater"
CTYPE_PARENT = "parent"
CTYPE_POLO = "waterpolo"
CTYPE_SWIMMER = "swimmer"
CTYPE_SYNCHRO = "synchro"
CTYPE_VOLUNTEER = "volunteer"

CTYPES = [
    CTYPE_COACH,
    CTYPE_COMMITTEE,
    CTYPE_OPENWATER,
    CTYPE_PARENT,
    CTYPE_POLO,
    CTYPE_SWIMMER,
    CTYPE_SYNCHRO,
    CTYPE_VOLUNTEER,
]

O_NEWSTARTER = "--newstarter"
O_TO = "--to"
O_VERIFY = "--verify"
O_BACKUP = "--backup"
O_FORMAT = "--format"
O_FIX = "--fix"

VAR_CONDUCT = []
VAR_GROUP = []
VAR_ISSUE = []
VAR_ROLE = []
VAR_SESSION = []


def group(data):
    """Register group."""
    VAR_GROUP.append(data)
    return True


def session(data):
    """Register session."""
    VAR_SESSION.append(data)
    return True


def conduct(data):
    """Register conduct."""
    VAR_CONDUCT.append(data)
    return True


def role(data):
    """Register role."""
    VAR_ROLE.append(data)
    return True


def issue(data):
    """Register issues."""
    VAR_ISSUE.append(data)
    return True


def member_type(data):
    """check_type."""
    if data in CTYPES:
        return True
    return False


SCHEMA = Schema(
    {
        C_CLUB: str,
        C_ALLOW_UPDATE: bool,
        Optional(C_DEBUG_LEVEL): int,
        Optional(C_EMAIL): {
            C_USERNAME: str,
            C_SMTP_SERVER: str,
            C_SMTP_PORT: int,
            C_SEND_TO: str,
            C_TLS: bool,
            C_PASSWORD: str,
        },
        C_SWIMMERS: {
            C_USERNAME: {C_MIN_AGE: int},
            C_PARENT: {C_MANDATORY: bool, C_MAX_AGE: int},
            Optional(C_CONF_DIFF): {C_VERIFY: bool},
            Optional(C_ABSENCE): {C_TIME: int},
        },
        C_PARENTS: {
            Optional(C_AGE): {C_MIN_AGE: int, C_CHILD: int},
            Optional(C_LOGIN): {C_MANDATORY: bool},
        },
        C_MEMBERS: {
            Optional(C_CONFIRMATION): {C_EXPIRY: int, Optional(C_ALIGN_QUARTER): bool},
            Optional(C_DBS): {C_EXPIRY: int},
            Optional(C_NEWSTARTER): {C_GRACE: int},
            Optional(C_INACTIVE): {C_TIME: int},
        },
        C_COACHES: {C_ROLE: {C_MANDATORY: bool}},
        Optional(C_ROLES): {
            Optional(C_VOLUNTEER): {C_MANDATORY: bool},
            Optional(C_LOGIN): {C_UNUSED: int},
            Optional(C_ROLE): {
                role: {
                    Optional(C_CHECK_PERMISSIONS): bool,
                    Optional(C_IS_COACH): bool,
                    Optional(C_CHECK_RESTRICTIONS): bool,
                }
            },
        },
        Optional(C_GROUPS): {
            Optional(C_PRIORITY): [group],
            Optional(C_GROUP): {
                group: {
                    Optional(C_CHECK_DBS): bool,
                    Optional(C_CONFIRMATION): str,
                    Optional(C_IGNORE_GROUP): bool,
                    Optional(C_IGNORE_SWIMMER): bool,
                    Optional(C_IGNORE_UNKNOWN): bool,
                    Optional(C_MAX_AGE): int,
                    Optional(C_MIN_AGE): int,
                    Optional(C_NO_CLUB_SESSIONS): bool,
                    Optional(C_NO_SESSION_ALLOWED): [group],
                    Optional(C_NO_SESSIONS): bool,
                    Optional(C_SESSIONS): [session],
                    Optional(C_TYPE): member_type,
                    Optional(C_UNIQUE): bool,
                }
            },
        },
        Optional(C_SESSIONS): {
            Optional(C_ABSENCE): int,
            Optional(C_REGISTER): int,
            Optional(C_SESSION): {
                session: {
                    Optional(C_GROUPS): [group],
                    Optional(C_IGNORE_ATTENDANCE): bool,
                }
            },
        },
        Optional(C_CONDUCT): {
            conduct: {C_TYPES: [member_type], Optional(C_IGNORE_GROUP): [group]}
        },
        Optional(C_ISSUES): {
            issue: {Optional(C_MESSAGE): str, Optional(C_IGNORE_ERROR): bool}
        },
        Optional(C_JOBTITLE): {C_IGNORE: [str]},
        Optional(C_FILES): {
            str: {
                Optional(C_CHECK_SE_NUMBER): bool,
                Optional(C_IGNORE_GROUP): [group],
                C_MAPPING: {
                    A_FIRSTNAME: str,
                    A_LASTNAME: str,
                    Optional(A_KNOWNAS): str,
                    Optional(A_ASA_NUMBER): str,
                    Optional(A_ASA_CATEGORY): str,
                    Optional(A_DOB): str,
                    Optional(C_DOB_FORMAT): str,
                },
            }
        },
        Optional(C_TYPES): {
            member_type: {
                Optional(C_CHECK_SE_NUMBER): bool,
                Optional(C_IGNORE_COACH): bool,
                Optional(C_IGNORE_COMMITTEE): bool,
                Optional(C_NAME): str,
                Optional(C_JOBTITLE): bool,
                Optional(C_GROUPS): [group],
                Optional(C_PARENTS): bool,
            }
        },
        Optional(C_LISTS): {
            C_SUFFIX: str,
            C_EDIT: bool,
            C_CONFIRMATION: bool,
            Optional(C_CONDUCT): [conduct],
            Optional(C_LIST): {
                str: {
                    Optional(C_GENDER): And(str, lambda s: s in ("male", "female")),
                    Optional(C_GROUP): group,
                    Optional(C_ALLOW_GROUP): group,
                    Optional(C_UNIQUE): bool,
                    Optional(C_MAX_AGE): int,
                    Optional(C_MAX_AGE_EOY): int,
                    Optional(C_MAX_YEAR): int,
                    Optional(C_MIN_AGE): int,
                    Optional(C_MIN_AGE_EOY): int,
                    Optional(C_MIN_YEAR): int,
                    Optional(C_TYPE): member_type,
                }
            },
        },
        Optional(C_FACEBOOK): {Optional(C_FILES): [str], Optional(C_GROUPS): [str]},
        Optional(C_SELENIUM): {C_BROWSER: str, C_WEB_DRIVER: str},
        Optional(C_SWIM_ENGLAND): {C_BASE_URL: str, C_CHECK_URL: str, C_TEST_ID: int},
        Optional(C_RECORDS): {
            Optional(C_RELAY): bool,
            Optional(C_AGE_EOY): bool,
            Optional(C_VERIFY): bool,
            Optional(C_SE_ONLY): bool,
            Optional(C_ALL_AGES): bool,
            Optional(C_OVERALL_FASTEST): bool,
        },
    }
)


def get_config(scm, item, item1=None, item2=None, item3=None):
    """Get config parameters..."""
    # pylint: disable=too-many-return-statements
    # Yes, need them all...

    cfg = scm.config(item)
    if cfg is None:
        return None

    if item1 is None:
        return cfg

    if item1 not in cfg:
        return None

    if item2 is None:
        return cfg[item1]

    if item2 not in cfg[item1]:
        return None

    if item3 is None:
        return cfg[item1][item2]

    if item3 not in cfg[item1][item2]:
        return None

    return cfg[item1][item2][item3]


def verify_schema(data):
    """Verify the config file."""
    try:
        SCHEMA.validate(data)
        return True
    except SchemaError as error:
        notify(f"Error in config file:\n{error}\n")
        return False


def verify_schema_data(scm):
    """Verify the data in the schema."""
    error = False
    for xgroup in VAR_GROUP:
        if xgroup not in scm.groups.by_name:
            notify(f"Error in config file: Group '{xgroup}' not found\n")
            error = True

    for code in VAR_CONDUCT:
        if code not in scm.conduct.by_name:
            notify(f"Error in config file: Code of Conduct '{code}' not found\n")
            error = True

    for xrole in VAR_ROLE:
        if xrole not in scm.roles.by_name:
            notify(f"Error in config file: Role '{xrole}' not found\n")
            error = True

    for xsession in VAR_SESSION:
        if scm.sessions.find_session_substr(xsession) is None:
            notify(f"Error in config file: Session '{xsession}' not found\n")
            error = True

    for xissue in VAR_ISSUE:
        if scm.issue_handler.check_issue(xissue) is False:
            notify(f"Error in config file: Issue '{xissue}' not found\n")
            error = True

    if error:
        return False
    return True


def check_default(scm):
    """Give warning if config not made."""

    msg = ""
    if get_config(scm, C_ROLES, C_ROLE) is None:
        msg += " - No Roles configured\n"
    if get_config(scm, C_GROUPS) is None:
        msg += " - No Groups configured\n"
    if get_config(scm, C_SESSIONS, C_SESSION) is None:
        msg += " - No Sessions configured\n"
    if get_config(scm, C_CONDUCT) is None:
        msg += " - No Code of Conduct configured\n"
    if get_config(scm, C_LISTS, C_LIST) is None:
        msg += " - No Lists configured\n"

    if msg:
        msg = "\nIn your configuration file, you have:\n" + msg
        msg += "By configuring these, SCM Helper can do a more for you!\n\n"

    return msg
