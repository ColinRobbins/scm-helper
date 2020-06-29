"""Default config file."""

import os
from pathlib import Path

from scm_helper.config import CONFIG_DIR, CONFIG_FILE, FILE_WRITE
from scm_helper.notify import interact, interact_yesno, notify


def create_default_config():
    """Create a default config file."""
    home = str(Path.home())

    cfg = os.path.join(home, CONFIG_DIR)
    cfg_file = os.path.join(home, CONFIG_DIR, CONFIG_FILE)

    notify("Welcome to SCM Helper.\nStarting configuration for first time use..\n")

    msg = "Please enter your Swimming Club Name: "
    clubname = interact(msg)

    msg = f"Create initial configuration file:\n   {cfg_file}\nfor '{clubname}'"
    if interact_yesno(msg) is False:
        return False

    content = DEFAULT_CONFIG.replace("###CLUB_NAME###", clubname)

    try:
        if os.path.exists(cfg) is False:
            os.mkdir(cfg)

        with open(cfg_file, FILE_WRITE) as file:
            file.write(content)

        notify("Done.\n")

        return True

    except OSError as error:
        notify(f"Cannot create file: {error}\n")
        return False


DEFAULT_CONFIG = f"""
################################################################
# Configuration of SCM-Helper
#
# https://github.com/ColinRobbins/scm-helper/
#
# You will need to change these parameters
# to reflect the situation at your club.
# See above link for documentation and a full example.
#
# Some lines are commented out with "# "
# To reactivate, remove the '#' and one ' '.
# I.e. YAML files are very sensitive to the exact spacing.
# Errors will be created if you get the spacing wrong.
# Use spaces not tabs.
################################################################

# Your swimming club name.
# If you change this, you will not be able to access
# backups taken before the change.
club: "###CLUB_NAME###"


allow_update:  False   # Set to true if this tool is allowed to edit SCM
                       # Set to false if you don't trust the software to be reliable.


################################################################
# Email config.
# Only needed if using --email from command line
################################################################

# email:
#  smtp_server: smtp.server.address
#    smtp_port: 25
#    username:
#   send_to:
#   tls: False
#   password: "email.enc"       # Created when needed.

################################################################
# File input, for correlation of Swim England file
#
# File must have a header row.
# The mapping maps this headers to the required fields.
################################################################
files:
    "swim_england.csv":
        check_se_number: true
        mapping:
          Firstname: 'First Name'
          Lastname: 'Surname'
          KnownAs: 'Known As'
          ASANumber: 'Member ID'
          ASACategory: 'Category'
          DOB: 'Date of Birth'
          dob_format: '%d/%m/%Y'
#         ignore_group:  # Don't report errors if swimmer is in these groups
#           - 'Resignations'


#############################################
# Swim England Correlations
#############################################
swim_england:
    base_url: "https://www.swimmingresults.org/"
    check_url: "https://www.swimmingresults.org/membershipcheck/member_details.php?myiref="
    test_id: 516115

################################################################
# Configure Swimmer Checks
################################################################
swimmers:
    username:
        min_age: 17     # Min age to have a user name
    parent:
        mandatory: True # Must have a parent
        max_age: 17     # Age a parent is mandatory until
    confirmation_difference:
        verify: False    # if there is > 3 month difference in confirm date
                        # between parent and child, report an issue.
    absence:
        time:  182      # Warn if not seen at swimming for this period of time

################################################################
# Configure Parent Checks
################################################################
parents:
    age:
        min_age: 17   # min age to be a parent
        child: 21     # Age at which child should not longer have a parent
    login:
        mandatory: True         # must have a login to SCM

################################################################
# Configure Member Checks
################################################################
members:
    confirmation:
        expiry: 365             # Warn if confirmation more than this many day old.
        align_quarter: True     # Align expiry to calendar quarter
                                # So reminders go in batches.
    dbs:
        expiry: 60      # Days warning prior to expiry.
    newstarter:
        grace:  90      # Don't give errors for 90 days,
                        # giving admin time to sort it all out
    inactive:
        time: 365       # Warn if member in inactive state for this many days

################################################################
# Configure Coaches
################################################################
coaches:
    role:
        mandatory: False # All coaches, must be in a coach role

################################################################
# Configure Roles
################################################################
roles:
    volunteer:
        mandatory: True       # if user in a role, the volunteer flag must be set
    login:
        unused: 180           # Error if not used in 180 days

# Examples...
#   role:
#     "Coaches":
#         check_permissions: False
#         is_coach: True                # Should have "Is A Coach" ticked.
#     "Register Taker":
#         check_restrictions: True        # Check they have session restrictions

jobtitle:
    ignore:
        - "Vice President"      # If VP, don't need to be a committee member.

################################################################
# Configure Groups
#
# Check this members of the group are in a relevant swimming session
################################################################
# groups:
#  priority:    # If a user is in multiple groups
                # these take priority (in this order) when printing
#    - 'Water Polo'
#    - 'Masters'

#   group:
#     'Membership Only':
#         no_sessions: true
#     'Senior Development':
#         session:
#           - Senior Development'
#         type: swimmer
#     'Masters':
#         sessions:
#           - 'Masters'
#         no_session_allowed:
#           - 'Life Members and Past Presidents'
#           - 'Membership Only'
#         unique: false
#         min_age: 17
#         type: swimmer
#     'Life Members and Past Presidents':
#         ignore_unknown: true    # Don't raise issue if not a swimmer, parent or coach.
#         unique: false
#     'Team Manager':
#         check_dbs: true
#         type: volunteer       # Must be of this type
#         unique: false
#     'Club Timekeeper':
#         unique: false
#         type: volunteer
#     'Resignations':
#         ignore_swimmer: true
#
################################################################
# Configure Sessions
#
# Check for attendance and correlation with group memberhip.
# Sessions not listed will not be checked for group correlation.
################################################################
sessions:
  absence:  120  # Number of days allowed to miss a session
  register: 60   # Alert if register not taken for this many days
#   session:
#     'Junior Squad':
#         groups:
#           - 'Junior Squad'
#     'Masters':
#         groups:
#           - 'Masters'
#     'Transition':
#         groups:
#           - 'Tadpoles'
#           - 'Development'
#           - 'Transition'
#         ignore_attendance: True
#     'Starts and Turns':
#         ignore_attendance: True

#############################################
# Codes of Conduct
#############################################

# conduct:
#    "Code of Conduct for Coaches":
#       types:
#         - "coach"
#     "Code of Conduct for Swimmers and Water Polo Players":
#       types:
#         - "swimmer"
#       ignore_group:
#         - "Tadpoles"

################################################################
# Facebook Correlations
################################################################

# facebook:
#   files:
#     - "Nottingham Leander Swimmers.html"
#   groups:
#     - https://www.facebook.com/groups/NottinghamLeander/
#     - https://www.facebook.com/groups/LeanderMasters/

################################################################
# Lists
#
# Configure the criteria for auto-generated lists
#
################################################################
lists:
    suffix: " (Generated)"  # Use to identity generated lists
    edit: False             # Allow script to modify generated lists
    confirmation: False     # Generate lists of non-confirmed and
                            # expired confirmation members
#    conduct:               # Create a list of memebrs who have not signed the code of conduct
#      - "Code of Conduct Name"

#     list:
#        "Swimmer: Development Only":
#             group: "Development"
#             unique: True                # ONLY the group, no others
#             allow_group: "Water Polo"   # If unique is set, allow this too
#        "Swimmers: 17 and under on Dec 31":
#            type: "swimmer"
#            max_age_eoy: 17
#        "Water Polo: Men: 16 and over":
#            group: "Water Polo"
#            min_age: 16
#            gender: "male"

################################################################
# Entity Types
#
# These are reflected by the "Is a Coach"  etc
# Boxes in a members details page
################################################################

types:
    synchro:
        name: "Synchro"
        check_se_number: False
        parents: False              # Don't check parents, overrides Mandatory above.
    waterpolo:
        name: "Water Polo"
#         groups:                   # Specify if they must be members
#           - "Water Polo"          # of a specific group
    volunteer:
        ignore_coach: True          # If coach, do not need to be a volunteer
        ignore_committee: True      # If committee, do not need to be a volunteer
#         groups:
#           - "Team Manager"
#           - "Club Timekeeper"
#           - "Licensed Officials"
    committee:
        jobtitle: True              # must have a job title

################################################################
# Issue handling
#
# Override the default message for an issue.
# Set ignore: true to ignore the message.
#
# For a list of issue codes see:
# https://github.com/ColinRobbins/scm-helper/wiki/Configuration-Issues
#
################################################################

issues:
    E_CONFIRMATION_EXPIRED:
        ignore_error: False
        message: "Confirmation expired"

##################################################
# Selenium
# Used for Swim England and Facebook checking
##################################################

#selenium:
#    browser: "Chrome"
#    web_driver: "C:\\Program Files (x86)\\Python37-32\\Scripts\\chromedriver.exe"


##################################################
# Records
##################################################

#records:
#    relay: false
#    age_eoy: true   # Calculate age at EOY, not age from SCM export file (where possible)
#    verify: true  # Check a club member at time of swim (where possible)
#    se_only: false



# Debug level, set to 0 for no debug info
debug_level: 0


"""
