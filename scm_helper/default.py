"""Default config file."""

from pathlib import Path
from notify import interact, notify
from config import FILE_WRITE, CONFIG_DIR, CONFIG_FILE
import os


def create_default_config():
    """Create a default config file."""

    home = str(Path.home())

    cfg = os.path.join(home, CONFIG_DIR)
    cfg_file = os.path.join(home, CONFIG_DIR, CONFIG_FILE)
    
    msg = "Welcome to SCM Helper.\nPlease enter Swimming Club Name: "
    clubname = interact(msg)
    
    msg = f"Create initial configuration file {cfg_file} for '{clubname}' (y/N)? "
    if interact(msg) != "y":
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
#############################################
# Configuration of SCM-Helper
# Colin Robbins
# March 2020
#
# You will need to change these parameters
# to reflect the situation at your cluv
#############################################

# Your swimming club name.
club: "###CLUB_NAME###"


allow_update:  False   # Set to true if this tool is allowed to edit SCM
                       # Set to false if you don't trust the software to be reliable.

# Debug level, set to 0 for no debug info
debug_level: 0


#############################################
# Email config.
# Only needed if using --email from command line
#############################################

# email:
#  smtp_server: smtp.server.address
#    smtp_port: 25
#    username:
#   send_to:
#   tls: False
#   password: "email.enc"

#############################################
# File input, for correlation of
# Swim England file
#############################################
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
#         ignore_group:  # Dont report errors if swimmer is in these groups
#           - 'Resignations'


#############################################
# Configure Swimmer Checks
#############################################
swimmers:
    username:
        min_age: 17     # Min age to have a user name
    parent:
        mandatory: True # Must have a parent
        max_age: 17     # Age a parent is mandatory until
    confirmation_difference:
        verify: True    # if there is > 3 month difference in confirm date
                        # between parent and child, report an issue.
    absence:
        time:  182      # Warn if not seen at swimming for this period of time

#############################################
# Configure Parent Checks
#############################################
parents:
    age:
        min_age: 17   # min age to be a parent
        child: 21     # Age at which child should not longer have a parent
    login:
        mandatory: True         # must have a login to SCM
        
#############################################
# Configure Member Checks
#############################################
members:
    confirmation:
        expiry: 365             # Warn if confirmation more than this many day old.
        align_quarter: True     # Align expiry to calender quarter
                                # So reminders go in batches.
    dbs:
        expiry: 60      # Days waring prior to expiry.
    newstarter:
        grace:  90      # Don't give errors for 90 days, giving admin time to sort it all out
    inactive:
        time: 365       # Warn if member in inactive state for this many days

#############################################
# Configure Coaches
#############################################
coaches:
    role:
        mandatory: False # All coaches, must be in a coach role
   
#############################################
# Configure Roles
#############################################
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

#############################################
# Configure Groups
#############################################
# groups:
#  priority:   # If a user is in multiple groups - these take priority (in this order)
#    - 'Water Polo'
#    - 'Masters'
    
# Examples...
#   group:
#     'Membership Only':
#         no_sessions: true
#     'Senior Development':
#         session: 'Senior Development'
#         type: swimmer
#     'Masters':
#         session: 'Masters'
#         no_session_allowed:
#           - 'Life Members and Past Presidents'
#           - 'Membership Only'
#         unique: false
#         min_age: 17
#         type: swimmer
#     'Water Polo':
#         session: 'Water Polo'
#         unique: false
#         no_session_allowed:
#           - 'Life Members and Past Presidents'
#           - 'Membership Only'
#           - 'Student'
#         type: "waterpolo"
#     'Life Members and Past Presidents':
#         ignore_unknown: true    # Don't raise error if not a swimmer, parent or coach.
#         unique: false
#     'Team Manager':
#         check_dbs: true
#         type: volunteer
#         unique: false
#     'Club Timekeeper':
#         unique: false
#         type: volunteer
#     'Resignations':
#         ignore_swimmer: true
#
#############################################
# Configure Sessions
#
# Sessions not listed will not be checked
#############################################
sessions:
  absence:  120  # Number of days allowed to miss a sesssion
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

#############################################
# Facebook Correlations
#############################################

# facebook:
#     - "files/Nottingham Leander Swimmers.html"
#

#############################################
# Lists
#
# Configure the criteria for auto-generated lists
#
#############################################
lists:
    suffix: " (Generated)"  # Use to identity generated lists
    edit: False             # Allow script to modify generated lists
    confirmation: False     # Generate lists of non-confirmed and expired confirmation members
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


#############################################
# Entity Types
#############################################

types:
    synchro:
        name: "Synchro"
        check_se_number: false
        parents: False  # Don't check parents, overrides Mandatory above.
    waterpolo:
        name: "Water Polo"
#         groups:
#           - "Water Polo"
    volunteer:
        ignore_coach: True          # If coach, do not need to be a volunteer
        ignore_committee: True      # If committee, do not need to be a volunteer
#         groups:
#           - "Team Manager"
#           - "Club Timekeeper"
#           - "Licensed Officals"
    committee:
        jobtitle: True      # must have a job title

jobtitle:
  ignore:
    - "Vice President"      # If VP, dont need to be a committee member.
    
#############################################
# Issue handling
#
# Override the default message for an error.
# Set ignore: true to ignore the message
# See issue.py for a list of issues.
#############################################

# issues:
#     E_CONFIRMATION_EXPIRED:
#         ignore_error: true
#


"""