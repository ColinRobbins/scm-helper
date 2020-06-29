"""Swimmer routines."""

from scm_helper.config import (
    C_ABSENCE,
    C_CHECK_SE_NUMBER,
    C_CONF_DIFF,
    C_GROUP,
    C_GROUPS,
    C_IGNORE_ATTENDANCE,
    C_MANDATORY,
    C_MAX_AGE,
    C_MIN_AGE,
    C_NO_CLUB_SESSIONS,
    C_PARENT,
    C_PARENTS,
    C_SESSION,
    C_SESSIONS,
    C_SWIMMERS,
    C_TIME,
    C_TYPES,
    C_UNIQUE,
    C_USERNAME,
    C_VERIFY,
    CTYPE_POLO,
    CTYPE_SYNCHRO,
    EXCEPTION_EMAILDIFF,
    EXCEPTION_NOGROUPS,
    EXCEPTION_TWOGROUPS,
    PRINT_DATE_FORMAT,
    get_config,
)
from scm_helper.issue import (
    E_ABSENT,
    E_ASA,
    E_CONFIRM_DIFF,
    E_DATE_JOINED,
    E_DOB,
    E_EMAIL_MATCH,
    E_GENDER,
    E_INACTIVE,
    E_LOGIN_TOO_YOUNG,
    E_NEVERSEEN,
    E_NO_GROUP,
    E_NO_PARENT,
    E_NUM_PARENTS,
    E_TWO_GROUPS,
    debug,
    issue,
)


def analyse_swimmer(swimmer):
    """Analyse a swimmer..."""
    # pylint: disable=too-many-branches
    if swimmer.in_ignore_group:
        return

    if swimmer.in_ignore_swimmer:
        return

    if len(swimmer.groups) == 0:
        if swimmer.print_exception(EXCEPTION_NOGROUPS):
            issue(swimmer, E_NO_GROUP)

    if swimmer.dob is None:
        issue(swimmer, E_DOB)

    if swimmer.gender is None:
        issue(swimmer, E_GENDER)

    if swimmer.date_joined is None:
        issue(swimmer, E_DATE_JOINED)

    check_asa(swimmer)
    check_lastseen(swimmer)
    check_two_groups(swimmer)
    check_login(swimmer)

    if swimmer.is_swimmer:
        check_parents(swimmer)
        return

    if swimmer.is_synchro:
        if get_config(swimmer.scm, C_TYPES, CTYPE_SYNCHRO, C_PARENTS) is False:
            pass
        else:
            check_parents(swimmer)
            return

    if swimmer.is_polo:
        if get_config(swimmer.scm, C_TYPES, CTYPE_POLO, C_PARENTS) is False:
            pass
        else:
            check_parents(swimmer)


def check_asa(swimmer):
    """Check ASA (Swim England) number is OK."""
    if swimmer.asa_number is None:
        cfg_synchro = get_config(swimmer.scm, C_TYPES, CTYPE_SYNCHRO, C_CHECK_SE_NUMBER)
        cfg_polo = get_config(swimmer.scm, C_TYPES, CTYPE_POLO, C_CHECK_SE_NUMBER)

        err = True
        if swimmer.is_polo and (cfg_polo is False):
            err = False
        if swimmer.is_synchro and (cfg_synchro is False):
            err = False
        if err:
            issue(swimmer, E_ASA)


def check_lastseen(swimmer):
    """Check when swimemr was last seen."""
    if swimmer.lastseen is None:
        if len(swimmer.sessions) > 0:
            # if no session, don't have data about when they have been seen
            check = True
            for session in swimmer.sessions:
                # pylint: disable=bad-continuation
                # black insists
                if get_config(
                    swimmer.scm,
                    C_SESSIONS,
                    C_SESSION,
                    session.name,
                    C_IGNORE_ATTENDANCE,
                ):
                    check = False
                    continue
            if check:
                issue(swimmer, E_NEVERSEEN)
    else:
        gap = (swimmer.scm.today - swimmer.lastseen).days
        absence = get_config(swimmer.scm, C_SWIMMERS, C_ABSENCE, C_TIME)
        if gap > absence:
            when = swimmer.lastseen.strftime(PRINT_DATE_FORMAT)
            issue(swimmer, E_ABSENT, f"Last seen: {when}")


def check_login(swimmer):
    """Check if the login is OK."""
    if swimmer.username:
        min_age = get_config(swimmer.scm, C_SWIMMERS, C_USERNAME, C_MIN_AGE)
        if min_age:
            if swimmer.age and (swimmer.age < min_age):
                issue(swimmer, E_LOGIN_TOO_YOUNG, f"Age: {swimmer.age}")


def check_two_groups(swimmer):
    """Check if swimmer in two groups."""
    if get_config(swimmer.scm, C_GROUPS, C_GROUP) is None:
        return  # No config, so ignore error.

    g_count = 0
    errmsg = ""
    for group in swimmer.groups:

        nosession = get_config(
            swimmer.scm, C_GROUPS, C_GROUP, group.name, C_NO_CLUB_SESSIONS
        )
        if nosession is True:
            continue

        unique = get_config(swimmer.scm, C_GROUPS, C_GROUP, group.name, C_UNIQUE)
        if unique is None:
            unique = True

        if unique:
            g_count += 1
            if g_count > 1:
                errmsg += f", {group.name}"
            else:
                errmsg += group.name

    if g_count > 1:
        if swimmer.print_exception(EXCEPTION_TWOGROUPS):
            issue(swimmer, E_TWO_GROUPS, errmsg)


def check_parents(swimmer):
    """Check consistence between swimmer and parent email."""
    # pylint: disable=too-many-branches
    email = None
    match = False
    count = 0
    confirm_error = False

    confirm_verify = get_config(swimmer.scm, C_SWIMMERS, C_CONF_DIFF, C_VERIFY)
    max_age = get_config(swimmer.scm, C_SWIMMERS, C_PARENT, C_MAX_AGE)

    if swimmer.email:
        email = swimmer.email.split(";")

    for parent in swimmer.parents:
        count += 1
        if parent.is_active is False:
            issue(parent, E_INACTIVE, f"Swimmer {swimmer.name}")

        if match is False:
            match = check_parent_email_match(email, parent)

        if confirm_verify:
            confirm_error = check_confirmed_diff(swimmer, parent)
            if confirm_error:
                issue(swimmer, E_CONFIRM_DIFF, f"Parent {parent.name}")
    # pylint: disable=bad-continuation
    # black insists
    if (
        swimmer.parents
        and swimmer.age
        and (match is False)
        and (swimmer.age <= max_age)
    ):
        if swimmer.print_exception(EXCEPTION_EMAILDIFF):
            err = f"{swimmer.email} - {swimmer.parents[0].email}"
            issue(swimmer, E_EMAIL_MATCH, err)

    if count == 0:
        mandatory = get_config(swimmer.scm, C_SWIMMERS, C_PARENT, C_MANDATORY)
        if mandatory and max_age:
            if swimmer.age and (swimmer.age <= max_age):
                msg = f"{swimmer.first_group}, Age: {swimmer.age}"
                issue(swimmer, E_NO_PARENT, msg)

    if count > 2:
        issue(swimmer, E_NUM_PARENTS)


def check_parent_email_match(email, parent):
    """Check swimmer and parent have email in common."""
    if parent.email:
        pemail = parent.email.split(";")
    else:
        return True  # can't match if non existent
    if email:
        for loop in email:
            for ploop in pemail:
                if loop == ploop:
                    return True
    return False


def check_confirmed_diff(swimmer, parent):
    """Check for differences in swimmer and parent."""
    # pylint: disable=R0911
    # Need them all
    child_mon = 0
    parent_mon = 0

    if swimmer.confirmed_date:
        child_mon = int((swimmer.confirmed_date.month - 1) / 3) * 3
    if parent.confirmed_date:
        parent_mon = int((parent.confirmed_date.month - 1) / 3) * 3

    if swimmer.age > get_config(swimmer.scm, C_SWIMMERS, C_PARENT, C_MAX_AGE):
        return False

    if child_mon == parent_mon:
        return False

    prefix = "Different confirmed dates"
    postfix = "- checking other details for consistency"
    debug(f"{prefix} {swimmer.name}, {parent.name} {postfix}", 8)

    if swimmer.email != parent.email:
        return True

    if swimmer.homephone != parent.homephone:
        return True

    if swimmer.mobilephone != parent.mobilephone:
        return True

    if swimmer.address != parent.address:
        return True

    # Dates are different, but core attributes same
    # So set the confirmed date - to inhibit a confirm notice to parent

    if parent.confirmed_date is None:
        parent.set_confirmed(swimmer.confirmed_date)
        return False

    if swimmer.confirmed_date:
        if swimmer.confirmed_date > parent.confirmed_date:
            parent.set_confirmed(swimmer.confirmed_date)

    return False
