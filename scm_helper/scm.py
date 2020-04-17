#!/usr/bin/python3
"""SCM support tools."""
import getopt
import platform
import sys
from tkinter import Tk  # only import tkiner if needed.

from api import API
from facebook import Facebook
from file import Csv
from gui import ScmGui
from issue import REPORTS, IssueHandler
from notify import notify, set_notify
from sendmail import send_email

USAGE = """
   --analyse = run analysis on archive date
   --archive <date> = which archive to use in restore
   --backup = backup
   --coaches = report of coaches per session
   --confirm_email = print email addresses for confirm errors
   --csv <csvfile> = read and validate file
   --dump <type> = dump entities of <type>
   --error = print sorted by error
   --email = send report as an email
   --facebook = check Facebook membership issues
   -f --fix = fix issues (after confirmation of each)
   --format <format> = CSV or JSON dump format
   --help = help
   -l --lists = update lists
   -m, --member = print sorted by member
   --newstarter = report on new starters anyway (normally inhibited)
   --notes = print notes
   --password <password> = supply the password - useful for scripting.
   -q, --quiet = quiet mode
   --report <report> = which reports to run
   --restore <type> = restore an entity of <type> (need -archive as well)
   --to <email> = Who to send the emial to (used with --email)
   --verify <date> = use archive backup
"""

SHORT_OPTS = "hlmfq"
LONG_OPTS = [
    "analyse",
    "archive=",
    "backup",
    "coaches",
    "confirm_email",
    "csv=",
    "dump=",
    "email",
    "error",
    "facebook",
    "fix",
    "format=",
    "help",
    "lists",
    "member",
    "newstarter",
    "notes",
    "password",
    "quiet",
    "report=",
    "restore=",
    "to=",
    "verify=",
]

MAPPING = {
    "--archive": "--verify",
    "-h": "--help",
    "-q": "--quiet",
    "-m": "--member",
    "-l": "--lists",
    "-f": "--fix",
}


def parse_opts(argv, scm):
    """Parse Options."""
    try:
        opts, remainder = getopt.getopt(argv, SHORT_OPTS, LONG_OPTS)
    except getopt.GetoptError as error:

        print(f"Option error: {error}")
        print("Use --help for options")
        sys.exit(2)

    for opt, args in opts:
        opt = MAPPING.get(opt, opt)
        if opt == "--help":
            print(USAGE)
            sys.exit()
        else:
            scm.setopt(opt, args)

    if len(remainder) > 0:
        print(f"Unknown option: {remainder}")
        print("Use --help for options")
        sys.exit()


def main(argv=None):
    """Start everything."""
    # Yes, its complicated...
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    fbook = None
    csv = None

    if argv is None:
        argv = sys.argv[1:]

    issues = IssueHandler()

    # Initiate the API Class
    scm = API(issues)

    parse_opts(argv, scm)

    if scm.initialise(scm.option("--password")) is False:
        sys.exit()

    output = ""

    reports = scm.option("--report")
    if reports:
        if reports in REPORTS:
            reports = reports.lower()
        else:
            print(f"Unknown Report: {reports}")
            sys.exit(2)

    if scm.option("--backup"):
        if scm.backup_data():
            scm.print_summary()
        sys.exit()

    if scm.option("--csv"):
        csv = Csv()
        if csv.readfile(scm.option("--csv"), scm) is False:
            sys.exit(2)

    if scm.option("--facebook"):
        fbook = Facebook()
        if fbook.readfiles(scm) is False:
            sys.exit(2)

    if scm.option("--verify"):
        if scm.decrypt(scm.option("--verify")) is False:
            sys.exit(2)
    else:
        if scm.get_data(False) is False:
            sys.exit(2)

    if scm.option("--restore"):
        xtype = scm.option("--restore")
        if scm.restore(xtype):
            notify("Success.\n")
        sys.exit()

    if scm.option("--notes"):
        output = scm.members.print_notes()
        if scm.option("--email"):
            send_email(scm, output, "SCM: Notes")
        else:
            print(output)
        sys.exit()

    if scm.option("--dump"):
        what = scm.option("--dump")
        output = scm.dump(what)
        if scm.option("--email"):
            send_email(scm, output, f"SCM: Dump of {what}")
        else:
            print(output)
        sys.exit()

    quiet = False
    if scm.option("--quiet"):
        quiet = True
        set_notify(False)

    if scm.linkage() is False:
        sys.exit()

    if scm.option("--coaches"):
        output = scm.sessions.print_coaches()
        if scm.option("--email"):
            send_email(scm, output, "SCM: Coaches Report")
        else:
            print(output)
        sys.exit()

    if scm.option("--csv"):
        csv.analyse(scm)
        output = csv.print_errors()
        if scm.option("--email"):
            send_email(scm, output, "SCM: CSV Analysis")
        else:
            print(output)
        sys.exit()

    if scm.option("--facebook"):
        fbook.analyse()
        output = fbook.print_errors()
        if scm.option("--email"):
            send_email(scm, output, "SCM: Facebook Report")
        else:
            print(output)
        sys.exit()

    scm.analyse()

    if scm.option("--lists"):
        if scm.option("--verify"):
            print("--lists can only be used with live data")
        else:
            scm.update()
        sys.exit()

    if scm.option("--confirm_email"):
        output = issues.confirm_email()
        if scm.option("--email"):
            send_email(scm, output, "SCM: Confirmation email addresses")
        else:
            print(output)
        sys.exit()

    if scm.option("--fix"):
        if scm.option("--verify"):
            print("--fix can only be used with live data")
        else:
            scm.apply_fixes()
        sys.exit()

    if scm.option("--errors"):
        output = issues.print_by_error(reports)
    elif scm.option("--member"):
        output = issues.print_by_name(reports)
    else:
        output = issues.print_by_error(reports)

    if scm.option("--email"):
        if reports:
            send_email(scm, output, f"SCM: {reports} report")
        else:
            send_email(scm, output, "SCM: Report")
    else:
        print(output)

    if quiet is False:
        print("Summary...")
        print(scm.print_summary())

    # not needed here, but used to prove point
    scm.delete()
    if fbook:
        fbook.delete()
    del fbook
    del csv
    del scm
    del issues


def gui(argv=None):
    """Start GUI."""
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) > 0:
        main()  # Command line options = run command line version
    else:
        root = Tk()
        ScmGui(root)
        root.mainloop()


if __name__ == "__main__":
    PLATFORM = platform.system()
    if PLATFORM == "Windows":
        gui()
    else:
        main()
