"""SCM Members."""
import datetime
import re

from scm_helper.coach import analyse_coach
from scm_helper.conduct import check_conduct
from scm_helper.config import (
    A_ACTIVE,
    A_ASA_CATEGORY,
    A_ASA_NUMBER,
    A_DOB,
    A_FIRSTNAME,
    A_GUID,
    A_ISCOACH,
    A_ISPARENT,
    A_ISVOLUNTEER,
    A_KNOWNAS,
    A_LASTNAME,
    A_PARENTS,
    A_USERNAME,
    C_ALIGN_QUARTER,
    C_CONFIRMATION,
    C_DBS,
    C_EXPIRY,
    C_GRACE,
    C_GROUP,
    C_GROUPS,
    C_IGNORE,
    C_IGNORE_COACH,
    C_IGNORE_COMMITTEE,
    C_IGNORE_UNKNOWN,
    C_INACTIVE,
    C_JOBTITLE,
    C_LISTS,
    C_MEMBERS,
    C_NAME,
    C_NEWSTARTER,
    C_PRIORITY,
    C_TIME,
    C_TYPES,
    CTYPE_COACH,
    CTYPE_COMMITTEE,
    CTYPE_PARENT,
    CTYPE_POLO,
    CTYPE_SWIMMER,
    CTYPE_SYNCHRO,
    CTYPE_VOLUNTEER,
    EXCEPTION_NODBS,
    EXCEPTION_NOEMAIL,
    EXCEPTION_NOSAFEGUARD,
    PRINT_DATE_FORMAT,
    SCM_DATE_FORMAT,
    get_config,
)
from scm_helper.entity import Entity, get_date, print_all
from scm_helper.issue import (
    E_CONFIRMATION_EXPIRED,
    E_DATE,
    E_DBS_EXPIRED,
    E_EMAIL_SPACE,
    E_INACTIVE_TOOLONG,
    E_JOB,
    E_NAME_CAPITAL,
    E_NO_DBS,
    E_NO_EMAIL,
    E_NO_JOB,
    E_NO_LEAVE_DATE,
    E_NO_SAFEGUARD,
    E_NOT_CONFIRMED,
    E_OWNPARENT,
    E_SAFEGUARD_EXPIRED,
    E_TOO_OLD,
    E_TOO_YOUNG,
    E_TYPE_GROUP,
    E_UNKNOWN,
    debug,
    debug_trace,
    issue,
)
from scm_helper.notify import notify
from scm_helper.parent import analyse_parent
from scm_helper.swimmer import analyse_swimmer

FACEBOOK_RE = re.compile(r"Facebook: *([a-zA-Z\- ]+)")
API_RE = re.compile(r"API:.+")  # The whole line
API_TEXT_RE = re.compile(r"API: *[a-zA-Z ]+")  # excluding date
DATE_RE = re.compile(r"\d\d-\d\d-\d\d\d\d")  # date
DATE2_RE = re.compile(r"\d\d/\d\d/\d\d\d\d")  # date

A_DATELEFT = "DateLeft"
A_DBS_RENEWAL_DATE = "DBSRenewalDate"
A_SAFEGUARDING_RENEWAL_DATE = "SafeguardingRenewalDate"
A_SWIMMERS = "Swimmers"


class Member(Entity):
    """A member."""

    # pylint: disable=too-many-instance-attributes
    # Need them all!
    # pylint: disable=too-many-public-methods
    # Need them all!

    def __init__(self, entity, scm, url):
        """Initialise."""
        super().__init__(entity, scm, url)
        self._parents = []
        self._swimmers = []
        self._sessions = []
        self._coach_sessions = []
        self._restricted = []
        self.facebook = []
        self.groups = []
        self._conduct = []
        self.ignore_errors = []
        self._in_ignore_swimmer = False
        self._in_ignore_group = False
        self._first_group = None
        self._lastseen = None
        self._in_coach_role = False
        self._no_session_ok = False

        self._dob = None
        self._date_joined = None
        self._last_modified = None
        self._confirmed_date = None
        self._last_login = None

        self.set_dates()
        self.get_notes()

    def get_notes(self):
        """Extract Facebook name from Notes."""
        notes = self.notes
        if notes is None:
            return

        note = FACEBOOK_RE.findall(notes)
        if note:
            for facebook in note:
                facebook = facebook.strip()
                self.facebook.append(facebook)
                debug(f"Found Facebook name in notes '{facebook}'", 8)

        note = API_RE.findall(notes)
        if note is None:
            return
        for api in note:
            exclusion = API_TEXT_RE.search(api)
            expiry = DATE_RE.search(api)
            when = self.scm.today
            gotdate = False
            if expiry:
                date = expiry.group(0)
                when = get_date(date, "%d-%m-%Y")
                gotdate = True
            else:
                expiry = DATE2_RE.search(api)
                if expiry:
                    date = expiry.group(0)
                    when = get_date(date, "%d/%m/%Y")
                    gotdate = True
            if when:
                excl = exclusion.group(0).strip()
                if (self.scm.today - when).days <= 0:
                    self.ignore_errors.append(excl)
                    debug(f"Found API token in notes {api}", 8)
                else:
                    debug(f"Token expired {api}", 8)
            elif gotdate:
                issue(self, E_DATE, f"Notes: {api}")

    def print_notes(self):
        """Print notes (if any)."""
        msg = f"{self.name}:\n"
        found = False
        for note in self.facebook:
            found = True
            msg += f"   Facebook: {note}\n"
        for note in self.ignore_errors:
            found = True
            msg += f"   {note}\n"
        if found:
            return msg
        return ""

    def linkage_parent(self, members):
        """Link parents."""
        for parent in self.data[A_PARENTS]:
            guid = members.by_guid[parent[A_GUID]]

            if guid == self.guid:
                issue(self, E_OWNPARENT)

            self._parents.append(guid)

    def linkage_swimmer(self, members):
        """Link swimmers."""
        for swimmer in self.data[A_SWIMMERS]:
            guid = members.by_guid[swimmer[A_GUID]]
            self._swimmers.append(guid)

    def linkage_restrictions(self):
        """Link restrictinos."""
        for session in self.session_restrictions:
            guid = self.scm.sessions.by_guid[session[A_GUID]]
            self._restricted.append(guid)

    def linkage2(self):
        """Link parents to swimmers."""
        # Hack - work around API issue.
        # if a parent, make sure swimmers are linked back
        # pylint: disable=protected-access
        for swimmer in self._swimmers:
            if len(swimmer._parents) == 0:
                debug(f"Found swimmer - API error - recovered {swimmer.name}", 7)
                swimmer._parents.append(self)

    def linkage(self, members):
        """Link parents and swimmers."""
        if self.data[A_PARENTS]:
            self.linkage_parent(members)

        if self.data[A_SWIMMERS]:
            self.linkage_swimmer(members)

        if self.session_restrictions:
            self.linkage_restrictions()

        self._first_group = self.set_first_group()

    def find_session_substr(self, substring):
        """Find a session containing substring."""
        for session in self.sessions:
            if session.name.find(substring) >= 0:
                return True
        return False

    def find_group(self, name):
        """Find a group containing string."""
        for group in self.groups:
            if name == group.name:
                return True
        return False

    def find_conduct(self, find):
        """Find a group containing string."""
        for codes in self._conduct:
            if find == codes:
                return True
        return False

    def check_email(self):
        """Check email."""
        email = self.email
        if email is None:
            if self.print_exception(EXCEPTION_NOEMAIL) is False:
                return
            issue(self, E_NO_EMAIL, f"{self.first_group}")
        else:
            space = re.search(" ", email)
            if space:
                issue(self, E_EMAIL_SPACE, f"{email}")

    def check_dbs(self, xtype):
        """Check DBS and Safeguarding."""
        if self.print_exception(EXCEPTION_NODBS) is False:
            debug(f"DBS Exception ignored: {self.name}", 7)
            return

        dbs_date = self.set_date(A_DBS_RENEWAL_DATE)
        safe_date = self.set_date(A_SAFEGUARDING_RENEWAL_DATE)
        notice = get_config(self.scm, C_MEMBERS, C_DBS, C_EXPIRY)

        if dbs_date:
            days = (dbs_date - self.scm.today).days
            if days < 0:
                dbs_date_str = dbs_date.strftime(PRINT_DATE_FORMAT)
                issue(self, E_DBS_EXPIRED, f"{xtype}, expired {dbs_date_str}")
            elif days < notice:
                dbs_date_str = dbs_date.strftime(PRINT_DATE_FORMAT)
                issue(self, E_DBS_EXPIRED, f"{xtype}, expires {dbs_date_str}")
        else:
            issue(self, E_NO_DBS, f"{xtype}")

        if self.print_exception(EXCEPTION_NOSAFEGUARD) is False:
            debug(f"Safeguard Exception ignored: {self.name}", 7)
            return

        if safe_date:
            if (safe_date - self.scm.today).days < 0:
                safe_date_str = safe_date.strftime(PRINT_DATE_FORMAT)
                issue(self, E_SAFEGUARD_EXPIRED, f"{xtype}, expired {safe_date_str}")
            elif (safe_date - self.scm.today).days < notice:
                safe_date_str = safe_date.strftime(PRINT_DATE_FORMAT)
                issue(self, E_SAFEGUARD_EXPIRED, f"{xtype}, expires {safe_date_str}")
        else:
            issue(self, E_NO_SAFEGUARD, f"{xtype}")

    def check_inactive(self):
        """Check an inactive member."""
        lastmod = self.last_modified_date
        if lastmod:
            gap = (self.scm.today - lastmod).days
            inactive = get_config(self.scm, C_MEMBERS, C_INACTIVE, C_TIME)
            if inactive and (gap > inactive):
                when = lastmod.strftime(PRINT_DATE_FORMAT)
                issue(self, E_INACTIVE_TOOLONG, f"Last Modified: {when}")

        if self.check_attribute(A_DATELEFT):
            return

        if lastmod:
            issue(self, E_NO_LEAVE_DATE, "fixable", -1)
            fix = {}
            fix[A_DATELEFT] = lastmod.strftime(SCM_DATE_FORMAT)
            self.fixit(fix, f"Add dataleft = {fix[A_DATELEFT]}")
            return

        issue(self, E_NO_LEAVE_DATE, "", -1)

    def _list_add(self, err):
        """Add a member to a confirmation list."""
        msg = "Not confirmed"
        if err == E_CONFIRMATION_EXPIRED:
            msg = "Confirmation expired"

        xtype = " (Other)"
        if self.is_parent:
            xtype = " (Parent)"
        if self.is_polo:
            xtype = " (Water Polo)"
            cfg = get_config(self.scm, C_TYPES, CTYPE_POLO, C_NAME)
            if cfg:
                xtype = f" ({cfg})"
        if self.is_synchro:
            xtype = " (Synchro)"
            cfg = get_config(self.scm, C_TYPES, CTYPE_SYNCHRO, C_NAME)
            if cfg:
                xtype = f" ({cfg})"
        if self.is_swimmer:
            xtype = " (Swimmer)"

        msg += xtype

        self.scm.lists.add(msg, self)

    def check_confirmation(self):
        """Check confimation status."""
        expiry = get_config(self.scm, C_MEMBERS, C_CONFIRMATION, C_EXPIRY)
        align = get_config(self.scm, C_MEMBERS, C_CONFIRMATION, C_ALIGN_QUARTER)
        xlist = get_config(self.scm, C_LISTS, C_CONFIRMATION)
        q_offset = 0

        if align:
            q_offset = self.scm.q_offset

        if self.confirmed_date:
            gap = (self.scm.today - self.confirmed_date).days
            if gap > (expiry + q_offset):
                issue(self, E_CONFIRMATION_EXPIRED, f"{self.first_group}")
                self.scm.members.count_not_confirmed += 1
                if xlist:
                    self._list_add(E_CONFIRMATION_EXPIRED)
        else:
            issue(self, E_NOT_CONFIRMED, f"{self.first_group}")
            self.scm.members.count_not_confirmed += 1
            if xlist:
                self._list_add(E_NOT_CONFIRMED)

    def check_name(self):
        """Check capitilisation of name."""
        firstname = self.data[A_FIRSTNAME]
        lastname = self.data[A_LASTNAME]
        knownas = self.data[A_KNOWNAS]
        ka_upper = True

        if knownas:
            ka_upper = knownas[0].isupper()

        fn_upper = firstname[0].isupper()
        ln_upper = lastname[0].isupper()

        if fn_upper and ln_upper and ka_upper:
            return

        if (fn_upper is False) or (ln_upper is False):
            issue(self, E_NAME_CAPITAL, "fixable", -1)

            fix = {}
            if fn_upper is False:
                fix[A_FIRSTNAME] = firstname.title()
            if ln_upper is False:
                fix[A_LASTNAME] = lastname.title()
            if ka_upper is False:
                fix[A_KNOWNAS] = knownas.title()

            self.fixit(fix, "Capitalisation of name")
            return

        issue(self, E_NAME_CAPITAL, f"Knownas = {knownas}", -1, "fixable")
        fix = {}
        fix[A_KNOWNAS] = knownas.title()
        self.fixit(fix, f"Capitalisation of {knownas}")

    def check_type(self, xtype):
        """Check the member type check box config."""
        cfg = get_config(self.scm, C_TYPES, xtype, C_GROUPS)
        name = get_config(self.scm, C_TYPES, xtype, C_NAME)
        if name is None:
            name = xtype
        jobtitle = get_config(self.scm, C_TYPES, xtype, C_JOBTITLE)
        if cfg:
            found = False
            for group in cfg:
                if self.find_group(group):
                    found = True
                    break
            if found is False:
                if self.in_ignore_group is False:
                    if self.in_ignore_swimmer is False:
                        issue(self, E_TYPE_GROUP, name)

        if jobtitle:
            if self.jobtitle:
                return
            issue(self, E_NO_JOB, f"{name}", 0, "fixable")
            fix = {}
            fix["JobTitle"] = xtype.title()
            self.fixit(fix, f"Add jobtitle: {name}")

    @debug_trace(5)
    def analyse(self):
        """Analise the member."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        if self.is_active is False:
            self.check_inactive()
            return

        self.check_name()

        found = False

        if self.is_coach:
            self.check_type(CTYPE_COACH)
            analyse_coach(self)
            found = True

        if self.newstarter:
            return

        if self.is_swimmer:
            self.check_type(CTYPE_SWIMMER)
            found = True

        if self.is_synchro:
            self.check_type(CTYPE_SYNCHRO)
            found = True

        if self.is_polo:
            self.check_type(CTYPE_POLO)
            found = True

        if self.is_swimmer or self.is_polo or self.is_synchro:
            analyse_swimmer(self)

        if self.is_parent:
            self.check_type(CTYPE_PARENT)
            analyse_parent(self)
            found = True

        if self.is_volunteer:
            vol = get_config(self.scm, C_TYPES, CTYPE_VOLUNTEER, C_IGNORE_COACH)
            ctte = get_config(self.scm, C_TYPES, CTYPE_VOLUNTEER, C_IGNORE_COMMITTEE)

            if vol or ctte or self.is_coach:
                pass
            else:
                self.check_type(CTYPE_VOLUNTEER)
            found = True

        if self.is_committee_member:
            found = True
            self.check_type(CTYPE_COMMITTEE)

        if self.jobtitle:
            # pylint: disable=bad-continuation
            # black insists
            if (
                (self.is_volunteer is not True)
                and (self.is_committee_member is not True)
                and (self.is_coach is not True)
            ):
                cfg = get_config(self.scm, C_JOBTITLE, C_IGNORE)
                if self.jobtitle not in cfg:
                    issue(self, E_JOB, self.jobtitle)

        if found:
            if self.in_ignore_swimmer:
                return
            self.check_email()
            self.check_confirmation()  # Must come after analyse_swimmer
            check_conduct(self, self._conduct)
            return

        for group in self.groups:
            if get_config(self.scm, C_GROUPS, C_GROUP, group.name, C_IGNORE_UNKNOWN):
                continue
            issue(self, E_UNKNOWN)

    def fix_search(self):
        """fix_search_index."""
        if A_KNOWNAS in self.data:
            if self.data[A_KNOWNAS]:

                self.newdata = {}
                self.newdata[A_GUID] = self.guid
                notify(f"Deleting index for {self.name}...")

                self.newdata[A_FIRSTNAME] = "XXX"

                res = self.scm.api_write(self, False)
                if res is False:
                    notify("Hit a snag!\n")
                    return False

                notify(f"Recreating...")

                self.newdata[A_FIRSTNAME] = self.data[A_FIRSTNAME]

                res = self.scm.api_write(self, False)
                if res is False:
                    msg = "Hit a snag - Firstname"
                    msg2 = "deleted - oops sorry - restore manually!\n"
                    notify(f"{msg} '{self.data[A_FIRSTNAME]}' {msg2}")
                    return False

                notify(f"Success.\n")

        return True

    def add_group(self, group):
        """Add a group to the swimmer."""
        debug(f"Added {self.name} to {group.name}", 9)
        self.groups.append(group)

    def add_session(self, session):
        """Add swimemrs sessions."""
        self._sessions.append(session)

    def add_conduct(self, conduct):
        """Add a conduct to the swimmer."""
        self._conduct.append(conduct)

    def add_coach_session(self, session):
        """Add coaches sessions."""
        self._coach_sessions.append(session)

    def add_restrictions(self, restriction):
        """Add swimmers restricted sessions."""
        self._restricted.append(restriction)

    def set_in_coach_role(self):
        """Member of a role."""
        self._in_coach_role = True

    def set_first_group(self):
        """Print the members primary group."""
        cfg_groups = self.scm.config(C_GROUPS)
        if cfg_groups is None:
            if self.groups:
                return self.groups[0]
            return None
        group_priority = cfg_groups[C_PRIORITY]
        if self.groups and group_priority:
            for group in self.groups:
                for priority in group_priority:
                    if group.name == priority:
                        return group

            # Pick the first one w
            return self.groups[0]
        return None

    def set_lastseen(self, lastseen):
        """Set when the swimmer was last seen."""
        when = datetime.datetime.strptime(lastseen, SCM_DATE_FORMAT)
        if self._lastseen is None:
            self._lastseen = when
            return
        if when > self._lastseen:
            self._lastseen = when

    def set_confirmed(self, date):
        """Set confirmed date."""
        self._confirmed_date = date

    def set_no_session_ok(self):
        """Set no session paramet to True."""
        self._no_session_ok = True

    def set_ignore_group(self, state):
        """Set ignore group."""
        self._in_ignore_group = state

    def set_ignore_swimmer(self, state):
        """Set ignore swimmer."""
        self._in_ignore_swimmer = state

    def print_exception(self, exception):
        """Return true if the exception allowable."""
        if len(self.ignore_errors) == 0:
            return True
        for item in self.ignore_errors:
            if exception == item:
                return False
        return True

    def print_links(self):
        """Print links."""
        # pylint: disable=no-self-use
        # override if anything needs doing
        res = "You will need to restore the following manually\n"
        res += "Sessions: "
        res += print_all(self.sessions)
        res += "\nGroups: "
        res += print_all(self.groups)
        res += "\nParents: "
        res += print_all(self.parents)
        res += "\nSwimmers: "
        res += print_all(self.swimmers)
        res += "\n"

    @property
    def first_group(self):
        """Print the members primary group."""
        if self._first_group:
            return self._first_group.name
        return "No Group"

    @property
    def name(self):
        """Name."""
        firstname = self.data[A_FIRSTNAME]
        lastname = self.data[A_LASTNAME]
        return f"{firstname} {lastname}"

    @property
    def full_name(self):
        """Full name - use Knownas."""
        firstname = self.data[A_FIRSTNAME]
        lastname = self.data[A_LASTNAME]
        if A_KNOWNAS in self.data:
            if self.data[A_KNOWNAS]:
                return f"{self.data[A_KNOWNAS]} ({firstname}) {lastname}"
        return self.name

    @property
    def knownas(self):
        """Known as."""
        firstname = self.data[A_FIRSTNAME]

        if A_KNOWNAS in self.data:
            if self.data[A_KNOWNAS]:
                firstname = self.data[A_KNOWNAS]

        lastname = self.data[A_LASTNAME]
        return f"{firstname} {lastname}"

    @property
    def knownas_only(self):
        """Known as."""
        firstname = self.data[A_FIRSTNAME]
        if A_KNOWNAS in self.data:
            if self.data[A_KNOWNAS]:
                firstname = self.data[A_KNOWNAS]
        return firstname

    @property
    def newstarter(self):
        """Is the member a new stater."""
        grace = get_config(self.scm, C_MEMBERS, C_NEWSTARTER, C_GRACE)
        if grace and self._date_joined:
            if (self.scm.today - self._date_joined).days < grace:
                return True
        return False

    @property
    def age(self):
        """Calculate age."""
        myage = None
        if self._dob:
            myage = (self.scm.today - self._dob).days // 365
        return myage

    @property
    def age_eoy(self):
        """Calculate age at eof of year."""
        myage = None
        if self._dob:
            myage = (self.scm.eoy - self._dob).days // 365
        return myage

    def check_age(self, xmin, xmax, group):
        """Check swimmer within age group."""
        if self.age and (self.age < xmin):
            issue(self, E_TOO_YOUNG, f"{group}: {self.age}")
        if self.age and (self.age > xmax):
            if not self.is_coach:
                issue(self, E_TOO_OLD, f"{group}: {self.age}")

    def set_dates(self):
        """Calculate dates."""
        self._dob = self.set_date(A_DOB)
        self._date_joined = self.set_date("DateJoinedClub")
        self._last_modified = self.set_date("LastModifiedDate")
        self._confirmed_date = self.set_date("DetailsConfirmedCorrect")
        self._last_login = self.set_date("LastLoggedIn")

    def set_joined_today(self):
        """Set joined date."""
        self._date_joined = self.scm.today

    @property
    def confirmed_date(self):
        """Set confirmed date Date."""
        return self._confirmed_date

    @property
    def dob(self):
        """Set DOB."""
        return self._dob

    @property
    def date_joined(self):
        """Set joining date."""
        return self._date_joined

    @property
    def last_login(self):
        """Set last login date."""
        return self._last_login

    @property
    def last_modified_date(self):
        """Set Last Modified Date."""
        return self._last_modified

    @property
    def asa_number(self):
        """Set ASA Number."""
        return self.check_attribute(A_ASA_NUMBER)

    @property
    def asa_category(self):
        """Set ASA Number."""
        return self.check_attribute(A_ASA_CATEGORY)

    @property
    def notes(self):
        """Set Notes."""
        return self.check_attribute("Notes")

    @property
    def username(self):
        """Set Username."""
        return self.check_attribute(A_USERNAME)

    @property
    def homephone(self):
        """Set Username."""
        return self.check_attribute("HomePhone")

    @property
    def mobilephone(self):
        """Set Username."""
        return self.check_attribute("MobilePhone")

    @property
    def address(self):
        """Set Username."""
        return self.check_attribute("Address1")

    @property
    def is_active(self):
        """Is the entry active..."""
        isa = self.check_attribute(A_ACTIVE)
        if isa == "1":
            return True
        return False

    @property
    def is_swimmer(self):
        """Is it a swimmer."""
        isa = self.check_attribute("IsASwimmer")
        if isa == "1":
            return True
        return False

    @property
    def is_coach(self):
        """Is it a Coach."""
        isa = self.check_attribute(A_ISCOACH)
        if isa == "1":
            return True
        return False

    @property
    def is_parent(self):
        """Is it a swimmer."""
        isa = self.check_attribute(A_ISPARENT)
        if isa == "1":
            return True
        return False

    @property
    def is_synchro(self):
        """Is it a syncro swimmer."""
        isa = self.check_attribute("SynchronisedSwimming")
        if isa == "1":
            return True
        return False

    @property
    def is_polo(self):
        """Is it a polo player."""
        isa = self.check_attribute("WaterPolo")
        if isa == "1":
            return True
        return False

    @property
    def is_committee_member(self):
        """Is it a CommitteeMember."""
        isa = self.check_attribute("CommitteeMember")
        if isa == "1":
            return True
        return False

    @property
    def is_volunteer(self):
        """Is it a Volunteer."""
        isa = self.check_attribute(A_ISVOLUNTEER)
        if isa == "1":
            return True
        return False

    @property
    def email(self):
        """Set email."""
        email = self.check_attribute("Email")
        if email:
            return email.lower()
        return None

    @property
    def gender(self):
        """Set Gender."""
        return self.check_attribute("Gender")

    @property
    def session_restrictions(self):
        """Return sessions restrictions."""
        return self.check_attribute("SessionRestrictions")

    @property
    def jobtitle(self):
        """Return job title."""
        return self.check_attribute("JobTitle")

    @property
    def lastseen_str(self):
        """Set lastseen as a string."""
        if self._lastseen:
            return self._lastseen.strftime(PRINT_DATE_FORMAT)
        return "Never"

    @property
    def lastseen(self):
        """Set lastseen."""
        return self._lastseen

    @property
    def swimmers(self):
        """Return swimmers."""
        return self._swimmers

    @property
    def parents(self):
        """Return parents."""
        return self._parents

    @property
    def sessions(self):
        """Return sessions."""
        return self._sessions

    @property
    def coach_sessions(self):
        """Return sessions."""
        return self._coach_sessions

    @property
    def restricted(self):
        """Return sessions."""
        return self._restricted

    @property
    def coach_role(self):
        """Return sessions."""
        return self._in_coach_role

    @property
    def no_session_ok(self):
        """Return true is no sessions OK."""
        return self._no_session_ok

    @property
    def in_ignore_group(self):
        """Return true is no sessions OK."""
        return self._in_ignore_group

    @property
    def in_ignore_swimmer(self):
        """Return true is no sessions OK."""
        return self._in_ignore_swimmer

    @property
    def print_groups(self):
        """Print out the groups."""
        return print_all(self.groups)
