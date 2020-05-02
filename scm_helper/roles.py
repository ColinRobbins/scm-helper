"""SCM Role."""
from scm_helper.coach import check_coach_permissions
from scm_helper.config import (
    A_GUID,
    A_ISVOLUNTEER,
    A_MEMBERS,
    C_CHECK_PERMISSIONS,
    C_CHECK_RESTRICTIONS,
    C_IS_COACH,
    C_LOGIN,
    C_MANDATORY,
    C_ROLE,
    C_ROLES,
    C_UNUSED,
    C_VOLUNTEER,
    get_config,
)
from scm_helper.entity import Entities, Entity
from scm_helper.issue import (
    E_COACH_ROLE,
    E_INACTIVE,
    E_NO_LOGIN,
    E_NO_RESTRICTIONS,
    E_NO_SWIMMERS,
    E_UNUSED_LOGIN,
    E_VOLUNTEER,
    debug_trace,
    issue,
)


class Roles(Entities):
    """Roles."""

    def new_entity(self, entity):
        """Create a new entity."""
        return Role(entity, self.scm, self._url)


class Role(Entity):
    """A role."""

    @debug_trace(5)
    def analyse(self):
        """Analise the role."""
        cfg = get_config(self.scm, C_ROLES, C_ROLE)
        unused = get_config(self.scm, C_ROLES, C_LOGIN, C_UNUSED)

        if len(self.members) == 0:
            issue(self, E_NO_SWIMMERS, "Role")
            return

        for member in self.members:
            self.check_role_member(member, unused)

            if cfg and (self.name in cfg):
                self.check_role_permissions(member)

    def check_role_member(self, member, unused):
        """Check out a role member."""
        if member.is_active is False:
            issue(member, E_INACTIVE, f"Member of role {self.name} (fixable)")
            if self.newdata and (A_MEMBERS in self.newdata):
                fix = self.newdata
            else:
                fix = {}
                fix[A_MEMBERS] = self.data[A_MEMBERS].copy()
            fix[A_MEMBERS].remove({A_GUID: member.guid})
            self.fixit(fix, f"Delete from role {self.name}")

        if member.username is None:
            issue(member, E_NO_LOGIN, f"Member of role {self.name}, so cannot login")

        if get_config(self.scm, C_ROLES, C_ROLE, self.name, C_IS_COACH):
            if member.is_coach is False:
                issue(member, E_COACH_ROLE, f"Role: {self.name}")

        if get_config(self.scm, C_ROLES, C_VOLUNTEER, C_MANDATORY):
            if member.is_volunteer is False:
                issue(member, E_VOLUNTEER, f"Role: {self.name} (fixable)")
                fix = {}
                fix[A_ISVOLUNTEER] = "1"
                member.fixit(fix, "Mark as volunteer")

        if member.last_login:
            if (self.scm.today - member.last_login).days > unused:
                issue(
                    member,
                    E_UNUSED_LOGIN,
                    f"Role: {self.name} [Last login: {member.last_login}]",
                )
        else:
            issue(member, E_UNUSED_LOGIN, f"Role: {self.name} [Never]")

    def check_role_permissions(self, member):
        """Check out a role permissions."""
        lookup = get_config(self.scm, C_ROLES, C_ROLE, self.name)
        if lookup is None:
            return

        if (C_CHECK_PERMISSIONS in lookup) and lookup[C_CHECK_PERMISSIONS]:
            check_coach_permissions(member, self)

        if (C_CHECK_RESTRICTIONS in lookup) and lookup[C_CHECK_RESTRICTIONS]:
            if len(member.restricted) == 0:
                issue(member, E_NO_RESTRICTIONS, f"Role: {self.name}")

    @property
    def name(self):
        """Guid."""
        return self.data["RoleName"]
