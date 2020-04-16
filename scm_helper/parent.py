"""Parent routines."""
from config import (
    A_ISPARENT,
    A_USERNAME,
    C_AGE,
    C_CHILD,
    C_LOGIN,
    C_MANDATORY,
    C_MIN_AGE,
    C_PARENTS,
    get_config,
)
from issue import (
    E_INACTIVE,
    E_NO_CHILD,
    E_NO_LOGIN,
    E_PARENT_AGE,
    E_PARENT_AGE_TOO_OLD,
    issue,
)


def analyse_parent(parent):
    """Analyse a parent..."""
    active = False
    inactive = None

    for swimmer in parent.swimmers:
        if swimmer.is_active:
            active = True
        else:
            inactive = swimmer.name

    if active is False:
        if inactive is None:
            issue(parent, E_NO_CHILD, "(fixable)")
            fix = {}
            fix[A_ISPARENT] = "0"
            parent.fixit(fix, "Remove 'is parent'")
        else:
            issue(parent, E_INACTIVE, f"child {inactive}")

    # TODO.  Iterate through children, and see if all new starter.
    # It they are, set parent to new starter.
    # Not seeing the error, so ignore for now!

    age = get_config(parent.scm, C_PARENTS, C_AGE, C_MIN_AGE)
    if parent.age and (parent.age < age):
        issue(parent, E_PARENT_AGE)

    age = get_config(parent.scm, C_PARENTS, C_AGE, C_CHILD)
    for swimmer in parent.swimmers:
        if active and swimmer.age and (swimmer.age >= age):
            issue(swimmer, E_PARENT_AGE_TOO_OLD, f"{swimmer.age}, {parent.name}")

    login = get_config(parent.scm, C_PARENTS, C_LOGIN, C_MANDATORY)
    if login and (parent.username is None):
        issue(parent, E_NO_LOGIN, "Parent (fixable)")
        fix = {}
        fix[A_USERNAME] = parent.email
        parent.fixit(fix, "Create login")
