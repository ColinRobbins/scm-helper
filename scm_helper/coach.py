"""Coach routines."""
from scm_helper.config import (
    A_GUID,
    A_ISCOACH,
    C_COACHES,
    C_MANDATORY,
    C_ROLE,
    EXCEPTION_NOSESSIONS,
    EXCEPTION_PERMISSIONS,
    get_config,
)
from scm_helper.issue import (
    E_COACH_WITH_SESSIONS,
    E_NO_ROLE_COACH,
    E_NO_SESSIONS,
    E_NOT_A_COACH,
    E_PERMISSION_EXTRA,
    E_PERMISSION_MISSING,
    debug,
    issue,
)


def analyse_coach(coach):
    """Analyse a coach..."""
    if coach.coach_role is False:
        if get_config(coach.scm, C_COACHES, C_ROLE, C_MANDATORY):
            issue(coach, E_NO_ROLE_COACH)

    if len(coach.coach_sessions) == 0:
        if coach.print_exception(EXCEPTION_NOSESSIONS):
            issue(coach, E_NO_SESSIONS)

    coach.check_dbs("Coach")


def check_coach_permissions(coach, role):
    """Check a coaches permissions."""
    debug(f"Permission check: {coach.name}, {role.name}", 7)
    if coach.is_coach is False:
        issue(coach, E_NOT_A_COACH, f"Role: {role.name} (fixable)")
        fix = {}
        fix[A_ISCOACH] = "1"
        coach.fixit(fix, "Add 'Is a coach'")

    coach.set_in_coach_role()

    if coach.is_swimmer is False:
        if len(coach.sessions) > 0:
            issue(coach, E_COACH_WITH_SESSIONS, f"Role: {role.name}")

    if coach.print_exception(EXCEPTION_PERMISSIONS) is False:
        return

    for session in coach.coach_sessions:
        match = False
        for permission in coach.restricted:
            if session == permission:
                match = True
                break
        if match is False:
            # SCM bug 6588
            issue(coach, E_PERMISSION_MISSING, session.full_name)
            # TODO
            # fix = {}
            # data = coach.data["SessionRestrictions"]
            # fix["SessionRestrictions"] = data.copy()
            # fix["SessionRestrictions"].append({A_GUID: session.guid})
            # coach.fixit(fix, f"Add permission for {session.name}")

    for permission in coach.restricted:
        match = False
        for session in coach.coach_sessions:
            if session == permission:
                match = True
                break
        if match is False:
            # SCM bug 6588
            issue(coach, E_PERMISSION_EXTRA, permission.full_name)
            # TODO
            # fix = {}
            # data = coach.data["SessionRestrictions"]
            # debug(f"Session restriction deletion - before:\n{data}\n", 9)
            # fix["SessionRestrictions"] = data.copy()
            # fix["SessionRestrictions"].remove({A_GUID: permission.guid})
            # coach.fixit(fix, f"Remove permission for {permission.name}")
