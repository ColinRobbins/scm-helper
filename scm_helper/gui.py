"""Windows GUI."""
import os.path
import sys
import threading
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import (
    DISABLED,
    END,
    NORMAL,
    Button,
    E,
    Entry,
    Frame,
    Label,
    LabelFrame,
    Menu,
    N,
    OptionMenu,
    S,
    StringVar,
    Toplevel,
    W,
    filedialog,
    messagebox,
    scrolledtext,
)

from func_timeout import FunctionTimedOut, func_timeout
from scm_helper.api import API
from scm_helper.config import (
    BACKUP_DIR,
    CONFIG_DIR,
    CONFIG_FILE,
    FILE_READ,
    FILE_WRITE,
    HELPURL,
    check_default,
)
from scm_helper.facebook import Facebook
from scm_helper.file import Csv
from scm_helper.issue import REPORTS, IssueHandler, debug
from scm_helper.license import LICENSE
from scm_helper.notify import set_notify
from scm_helper.records import Records
from scm_helper.version import VERSION

NSEW = N + S + E + W
AFTER = 2500  # How log to wait for Windows to catchup after processing


class ScmGui:
    """Tkinter based GUI (for Windows)."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    def __init__(self, master):
        """Initialise."""
        # pylint: disable=too-many-statements
        # super().__init__(None)
        self.master = master
        self.issue_window = None
        self.issue_text = None
        self.report_window = None
        self.report_text = None
        self.issues = None
        self.scm = None
        self.gotdata = False
        self.thread = None
        self.grouping = None
        self.reports = None
        self.menus = []
        self.menu_fixit = None
        self.notify_text = None

        master.title("SCM Helper")

        self.create_main_window()
        self.create_menu()

        set_notify(self.notify_text)
        self.issues = IssueHandler()
        self.scm = API(self.issues)

        if self.scm.get_config_file() is False:
            msg = "Error in config file - see status window for details."
            messagebox.showerror("Error", msg, parent=self.master)
            cfgmsg = ""
        else:
            cfgmsg = check_default(self.scm)

        self.api_init = False

        msg = "Welcome to SCM Helper by Colin Robbins.\n"
        msg += cfgmsg
        msg += "Please enter your password.\n"
        self.notify_text.insert(END, msg)
        self.notify_text.config(state=DISABLED)

    def create_main_window(self):
        """Create the main window."""
        top_frame = Frame(self.master)
        top_frame.grid(row=0, column=0, sticky=W + E)

        label = Label(top_frame, text="Password: ")
        label.grid(row=0, column=0, pady=10, padx=10)

        self.__password = StringVar()
        self.__password.set("")
        password = Entry(top_frame, show="*", textvariable=self.__password, width=20)
        password.grid(row=0, column=1, pady=10, padx=10)

        msg = "Analyse"
        self.button_analyse = Button(top_frame, text=msg, command=self.analyse_window)
        self.button_analyse.grid(row=0, column=2, pady=10, padx=10)

        self.button_backup = Button(top_frame, text="Backup", command=self.backup)
        self.button_backup.grid(row=0, column=3, pady=10, padx=10)

        self.button_fixit = Button(top_frame, text="Fixit", command=self.fixit)
        self.button_fixit.config(state=DISABLED)
        self.button_fixit.grid(row=0, column=4, pady=10, padx=10)

        top_group = LabelFrame(self.master, text="Notifications...", pady=5, padx=5)
        top_group.grid(row=1, column=0, columnspan=5, pady=10, padx=10, sticky=NSEW)

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)

        top_group.columnconfigure(0, weight=1)
        top_group.rowconfigure(0, weight=1)

        self.notify_text = scrolledtext.ScrolledText(top_group, width=60, height=20)
        self.notify_text.grid(row=0, column=0, sticky=NSEW)

    def create_menu(self):
        """Create Menus."""
        menubar = Menu(self.master)
        file = Menu(menubar, tearoff=0)
        file.add_command(label="Open Archive", command=self.open_archive)
        self.menus.append([file, "Open Archive"])
        file.add_separator()
        file.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file)

        cmd = Menu(menubar, tearoff=0)
        cmd.add_command(label="Edit Config", command=self.edit_config)
        self.menus.append([cmd, "Edit Config"])
        cmd.add_separator()
        cmd.add_command(label="Create Lists", command=self.create_lists, state=DISABLED)
        self.menus.append([cmd, "Create Lists"])

        cmd.add_command(label="Fix Errors", command=self.fixit, state=DISABLED)
        self.menu_fixit = [cmd, "Fix Errors"]

        label = "Fix Search index"
        cmd.add_command(label=label, command=self.fix_search, state=DISABLED)
        self.menus.append([cmd, label])

        menubar.add_cascade(label="Edit", menu=cmd)

        cmd = Menu(menubar, tearoff=0)

        cmd.add_command(label="Analyse Facebook", command=self.facebook, state=DISABLED)
        self.menus.append([cmd, "Analyse Facebook"])

        label = "Analyse Swim England File"
        cmd.add_command(label=label, command=self.swim_england, state=DISABLED)
        self.menus.append([cmd, label])

        label = "Analyse Swim England Registrations Online"
        cmd.add_command(label=label, command=self.swim_england_online, state=DISABLED)
        self.menus.append([cmd, label])

        cmd.add_command(label="List Coaches", command=self.coaches, state=DISABLED)
        self.menus.append([cmd, "List Coaches"])

        label = "Show Not-confirmed Emails"
        cmd.add_command(label=label, command=self.confirm, state=DISABLED)
        self.menus.append([cmd, label])

        menubar.add_cascade(label="Reports", menu=cmd)

        record = Menu(menubar, tearoff=0)

        record.add_command(label="Process Records", command=self.process_records)

        label = "Read New Swim Times"
        record.add_command(label=label, command=self.new_times, state=DISABLED)
        self.menus.append([record, label])

        menubar.add_cascade(label="Records", menu=record)

        about = Menu(menubar, tearoff=0)
        about.add_command(label="About...", command=xabout)
        about.add_command(label="Help", command=xhelp)
        about.add_command(label="License", command=xlicense)
        menubar.add_cascade(label="About", menu=about)

        self.master.config(menu=menubar)

    def scm_init(self):
        """Initialise SCM."""
        self.notify_text.config(state=NORMAL)
        password = self.__password.get()

        self.clear_data()
        self.api_init = False

        if password:
            if self.scm.initialise(password) is False:
                messagebox.showerror("Error", "Cannot initialise SCM (wrong password?)")
                self.clear_data()
                self.notify_text.config(state=DISABLED)
                return False
            self.api_init = True
            return True

        messagebox.showerror("Password", "Please give a password!")
        self.notify_text.config(state=DISABLED)

        return False

    def prep_report(self, create=True, delete=True):
        """Prepare for a report."""
        if self.gotdata is False:
            messagebox.showerror("Error", "Run analyse first to collect data")
            return False

        if create and (self.report_window is None):
            self.create_report_window()

        if self.report_window:
            self.report_text.config(state=NORMAL)
            self.report_text.delete("1.0", END)

        self.notify_text.config(state=NORMAL)
        if delete:
            self.notify_text.delete("1.0", END)

        return True

    def open_archive(self):
        """Open Archive file."""
        if self.thread:
            return  # already running

        if self.scm_init() is False:
            return

        self.thread = AnalysisThread(self, True).start()

    def swim_england(self):
        """Process Swim England File."""
        if self.prep_report() is False:
            return

        csv = Csv()

        home = str(Path.home())
        cfg = os.path.join(home, CONFIG_DIR)

        dir_opt = {}
        dir_opt["title"] = "Find Swim England File"
        dir_opt["initialdir"] = cfg
        dir_opt["parent"] = self.report_window
        dir_opt["defaultextension"] = ".csv"

        where = filedialog.askopenfilename(**dir_opt)
        if csv.readfile(where, self.scm) is False:
            messagebox.showerror("Error", "Could not read CSV file")
            self.notify_text.config(state=DISABLED)
            self.report_text.config(state=DISABLED)
            return

        if wrap(10, csv.analyse, self.scm) is False:
            self.notify_text.config(state=DISABLED)
            self.report_text.config(state=DISABLED)
            return

        output = wrap(None, csv.print_errors)

        del csv
        self.report_text.insert(END, output)
        self.report_text.config(state=DISABLED)
        self.notify_text.config(state=DISABLED)
        self.report_window.lift()

    def swim_england_online(self):
        """Window for reports."""
        if self.thread:
            return  # already running

        if self.prep_report(False) is False:
            return

        self.thread = SwimEnglandThread(self).start()

    def facebook(self):
        """Window for reports."""
        if self.thread:
            return  # already running

        if self.prep_report(False) is False:
            return

        self.thread = FacebookThread(self).start()

    def confirm(self):
        """Confirm email Report."""
        if self.prep_report() is False:
            return

        output = self.issues.confirm_email()
        self.report_text.insert(END, output)
        self.report_text.config(state=DISABLED)
        self.notify_text.config(state=DISABLED)
        self.report_window.lift()

    def coaches(self):
        """Coaches Report."""
        if self.prep_report() is False:
            return

        output = wrap(None, self.scm.sessions.print_coaches)
        self.report_text.insert(END, output)
        self.report_text.config(state=DISABLED)
        self.notify_text.config(state=DISABLED)
        self.report_window.lift()

    def edit_config(self):
        """Edit Config."""
        home = str(Path.home())
        cfg = os.path.join(home, CONFIG_DIR, CONFIG_FILE)

        Edit(self.master, cfg, self.scm, self)

    def create_lists(self):
        """Create Lists."""
        if self.gotdata is False:
            messagebox.showerror("Error", "Run analyse first to collect data")
            return

        if self.thread:
            return  # already running

        self.thread = UpdateThread(self).start()

    def analyse_window(self):
        """Window for analysis result."""
        if self.thread:
            return  # already running

        if self.scm_init() is False:
            return

        self.thread = AnalysisThread(self, False).start()

    def fix_search(self):
        """Window for reports."""
        if self.thread:
            return  # already running

        if self.gotdata is False:
            messagebox.showerror("Error", "Analyse data first, before fixing (2)")
            return

        self.thread = SearchThread(self).start()

    def fixit(self):
        """Window for reports."""
        if self.thread:
            return  # already running

        if self.gotdata is False:
            messagebox.showerror("Error", "Analyse data first, before fixing")
            return

        self.set_buttons(DISABLED)

        length = len(self.scm.fixable)
        if length == 0:
            messagebox.showerror("Error", "Nothing to fix")
            self.set_buttons(NORMAL)
            return

        wrap(None, self.scm.apply_fixes)

        self.set_buttons(NORMAL)

    def backup(self):
        """Window for reports."""
        if self.thread:
            return  # already running

        if self.scm_init() is False:
            return

        self.thread = BackupThread(self).start()

    def clear_data(self):
        """Prepare to rerun."""
        wrap(None, self.scm.delete)
        self.gotdata = False

    def create_report_window(self):
        """Create the reports window."""
        self.report_window = Toplevel(self.master)
        self.report_window.title("SCM Helper - Report Window")

        top_frame = Frame(self.report_window)
        top_frame.grid(row=0, column=0, sticky=W + E)

        self.report_window.columnconfigure(0, weight=1)
        self.report_window.rowconfigure(0, weight=1)

        self.report_text = scrolledtext.ScrolledText(top_frame, width=80, height=40)
        self.report_text.grid(row=0, column=0, sticky=NSEW)

        self.report_window.protocol("WM_DELETE_WINDOW", self.close_report_window)

    def close_report_window(self):
        """Close report window."""
        self.report_window.destroy()
        self.report_window = None

    def create_issue_window(self):
        """Create the results window."""
        self.issue_window = Toplevel(self.master)
        self.issue_window.title("SCM Helper - Issue Window")

        self.reports = StringVar()
        self.reports.set("All Reports")

        top_frame = Frame(self.issue_window)
        top_frame.grid(row=0, column=0, sticky=W + E)

        label = Label(top_frame, text="Select Report: ")
        label.grid(row=0, column=0, pady=10, padx=10)

        rpts = [resp.title() for resp in REPORTS]
        all_reports = ["All Reports"] + rpts

        menu = OptionMenu(
            top_frame, self.reports, *all_reports, command=self.process_issue_option,
        )
        menu.grid(row=0, column=1, pady=10, padx=10)

        self.grouping = StringVar()
        self.grouping.set("Error")

        label = Label(top_frame, text="Group Report by: ")
        label.grid(row=0, column=2, pady=10, padx=10)

        menu = OptionMenu(
            top_frame,
            self.grouping,
            "Error",
            "Member",
            command=self.process_issue_option,
        )
        menu.grid(row=0, column=3, pady=10, padx=10)

        txt = "Analysis..."
        top_group = LabelFrame(self.issue_window, text=txt, pady=5, padx=5)
        top_group.grid(row=1, column=0, columnspan=4, pady=10, padx=10, sticky=NSEW)

        self.issue_window.columnconfigure(0, weight=1)
        self.issue_window.rowconfigure(1, weight=1)

        top_group.columnconfigure(0, weight=1)
        top_group.rowconfigure(0, weight=1)

        self.issue_text = scrolledtext.ScrolledText(top_group, width=100, height=40)
        self.issue_text.grid(row=0, column=0, sticky=NSEW)

        self.issue_window.protocol("WM_DELETE_WINDOW", self.close_issue_window)

    def close_issue_window(self):
        """Close issue window."""
        self.issue_window.destroy()
        self.issue_window = None

    def process_issue_option(self, _):
        """Process an option selection."""
        report = self.reports.get()
        mode = self.grouping.get()

        self.issue_text.config(state=NORMAL)
        self.notify_text.config(state=NORMAL)
        self.issue_text.delete("1.0", END)

        if report == "All Reports":
            report = None
        else:
            report = report.lower()

        if mode == "Error":
            output = self.issues.print_by_error(report)
        else:
            output = self.issues.print_by_name(report)

        self.issue_text.insert(END, output)

        self.master.update_idletasks()
        self.master.after(AFTER, self.set_normal)

    def set_buttons(self, status):
        """Change button state."""
        self.button_analyse.config(state=status)
        self.button_backup.config(state=status)

        for menu, item in self.menus:
            menu.entryconfig(item, state=status)

        menu, item = self.menu_fixit

        if status == NORMAL:
            self.notify_text.config(state=DISABLED)
            length = len(self.scm.fixable)
            if length == 0:
                self.button_fixit.config(state=DISABLED)
                menu.entryconfig(item, state=DISABLED)
                return
            if self.issue_window:
                self.issue_text.config(state=DISABLED)
        else:
            self.notify_text.config(state=NORMAL)

        self.button_fixit.config(state=status)
        menu.entryconfig(item, state=status)

    def set_normal(self):
        """Set GUI to normal state after processing."""
        self.set_buttons(NORMAL)

    def new_times(self):
        """Add new time and process."""
        self.process_records(True)

    def process_records(self, newtimes=False):
        """Process Records."""
        if self.thread:
            return  # already running

        if self.scm_init() is False:
            return

        self.thread = RecordThread(self, newtimes).start()


class AnalysisThread(threading.Thread):
    """Thread to run analysis."""

    def __init__(self, gui, archive):
        """Initialise."""
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm
        self.archive = archive

    def run(self):
        """Run analyser."""
        self.gui.set_buttons(DISABLED)

        if self.gui.issue_window:
            self.gui.issue_text.config(state=NORMAL)
            self.gui.issue_text.delete("1.0", END)

        self.gui.notify_text.delete("1.0", END)

        if self.scm.get_config_file() is False:
            messagebox.showerror("Error", "Error in config file.")
            self.gui.set_buttons(NORMAL)
            return

        if self.archive:

            home = str(Path.home())
            backup = os.path.join(home, CONFIG_DIR, BACKUP_DIR)

            dir_opt = {}
            dir_opt["initialdir"] = backup
            dir_opt["mustexist"] = True
            dir_opt["parent"] = self.gui.master

            where = filedialog.askdirectory(**dir_opt)
            if wrap(None, self.scm.decrypt, where) is False:
                messagebox.showerror("Error", f"Cannot read from archive: {where}")
                self.gui.master.after(AFTER, self.gui.set_normal)
                self.gui.thread = None
                return
        else:
            if wrap(None, self.scm.get_data, False) is False:
                messagebox.showerror("Analsyis", "Failed to read data")
                self.gui.master.after(AFTER, self.gui.set_normal)
                self.gui.thread = None
                return

        if wrap(10, self.scm.linkage) is False:
            self.gui.master.after(AFTER, self.gui.set_normal)
            self.gui.thread = None
            return

        if wrap(10, self.scm.analyse) is False:
            self.gui.master.after(AFTER, self.gui.set_normal)
            self.gui.thread = None
            return

        self.gui.gotdata = True

        if self.gui.issue_window is None:
            self.gui.create_issue_window()

        debug("Analyse returned - creating result window", 8)

        output = self.gui.issues.print_by_error(None)
        result = self.scm.print_summary()

        self.gui.notify_text.insert(END, result)
        self.gui.notify_text.see(END)
        self.gui.issue_text.insert(END, output)

        self.gui.master.update_idletasks()
        self.gui.issue_window.lift()
        self.gui.master.after(AFTER, self.gui.set_normal)

        self.gui.thread = None

        debug("Analyse Thread complete, result posted", 8)

        return


class BackupThread(threading.Thread):
    """Thread to run Backuo."""

    def __init__(self, gui):
        """Initialise."""
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm

    def run(self):
        """Run analyser."""
        self.gui.set_buttons(DISABLED)
        self.gui.notify_text.delete("1.0", END)

        if wrap(None, self.scm.backup_data):
            output = self.scm.print_summary(backup=True)
            self.gui.notify_text.insert(END, output)
            self.gui.notify_text.insert(END, "Backup Complete.")
            self.gui.notify_text.see(END)
        else:
            messagebox.showerror("Error", "Backup failure")

        self.gui.master.update_idletasks()
        self.gui.master.after(AFTER, self.gui.set_normal)

        self.gui.thread = None


class FacebookThread(threading.Thread):
    """Thread for Facebook."""

    def __init__(self, gui):
        """Initialise."""
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm

    def run(self):
        """Process a Facebook report."""

        fbook = Facebook()
        if fbook.read_data(self.scm) is False:
            messagebox.showerror("Error", "Could not read facebook files")
            self.gui.report_text.config(state=DISABLED)
            self.gui.notify_text.config(state=DISABLED)
            return

        wrap(None, fbook.analyse)
        output = wrap(None, fbook.print_errors)

        if self.gui.prep_report(True, False) is False:
            return

        wrap(None, fbook.delete)
        del fbook
        self.gui.report_text.insert(END, output)
        self.gui.report_text.config(state=DISABLED)
        self.gui.notify_text.config(state=DISABLED)
        self.gui.report_window.lift()


class RecordThread(threading.Thread):
    """Thread for Records."""

    def __init__(self, gui, newtimes):
        """Initialise."""
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm
        self.newtimes = newtimes

    def run(self):
        """Process Records."""
        self.gui.notify_text.config(state=NORMAL)
        self.gui.notify_text.delete("1.0", END)

        record = Records(self.scm)

        output = wrap(None, record.read_baseline)
        if output is False:
            self.gui.notify_text.config(state=DISABLED)
            messagebox.showerror("Error", "Cannot read records baseline")
            return

        dir_opt = {}
        dir_opt["title"] = "Locate new swim times CSV file from SCM"
        dir_opt["parent"] = self.gui.master
        dir_opt["defaultextension"] = ".csv"

        if self.newtimes:
            filename = filedialog.askopenfilename(**dir_opt)
            output = wrap(None, record.read_newtimes, filename)
            if output is False:
                self.gui.notify_text.config(state=DISABLED)
                messagebox.showerror("Error", "Cannot read new swim times")
                return

        output = wrap(None, record.create_html)
        if output:
            webbrowser.open_new(output)
        else:
            self.gui.notify_text.config(state=DISABLED)
            messagebox.showerror("Error", "Cannot Create HTML")
            return

        self.gui.notify_text.config(state=DISABLED)


class SwimEnglandThread(threading.Thread):
    """Thread for SwimEngland."""

    def __init__(self, gui):
        """Initialise."""
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm

    def run(self):
        """Process a Swim England online report."""
        output = wrap(None, self.scm.se_check)

        if self.gui.prep_report(True, False) is False:
            return

        self.gui.report_text.insert(END, output)
        self.gui.report_text.config(state=DISABLED)
        self.gui.notify_text.config(state=DISABLED)
        self.gui.report_window.lift()


class UpdateThread(threading.Thread):
    """Thread to run Backuo."""

    def __init__(self, gui):
        """Initialise."""
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm

    def run(self):
        """Run analyser."""
        self.gui.set_buttons(DISABLED)
        self.gui.notify_text.delete("1.0", END)

        wrap(None, self.scm.update)

        self.gui.notify_text.see(END)

        self.gui.master.update_idletasks()
        self.gui.master.after(AFTER, self.gui.set_normal)

        self.gui.thread = None


class SearchThread(threading.Thread):
    """Thread to run Search fix."""

    def __init__(self, gui):
        """Initialise."""
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm

    def run(self):
        """Run analyser."""

        self.gui.set_buttons(DISABLED)

        if wrap(None, self.scm.fix_search) is False:
            messagebox.showerror("Error", "fix search error")
            self.gui.set_buttons(NORMAL)
            return

        self.gui.set_buttons(NORMAL)


class Edit(Frame):  # pylint: disable=too-many-ancestors
    """Class to edit a frame."""

    def __init__(self, parent, filename, scm, gui):
        """Initialise."""
        Frame.__init__(self, parent)
        self.parent = parent
        self.file = filename
        self.scm = scm
        self.gui = gui

        self.edit_win = Toplevel(self.master)
        self.edit_win.title("SCM Helper - Edit Config")

        top_frame = Frame(self.edit_win)
        top_frame.grid(row=0, column=0, sticky=W + E)

        abtn = Button(top_frame, text="Save", command=self.save_command)
        abtn.grid(row=0, column=0, pady=10, padx=10)

        cbtn = Button(top_frame, text="Close", command=self.on_exit)
        cbtn.grid(row=0, column=1, pady=10, padx=10)

        top_group = LabelFrame(self.edit_win, text=filename, pady=5, padx=5)
        top_group.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky=NSEW)

        self.edit_win.columnconfigure(0, weight=1)
        self.edit_win.rowconfigure(1, weight=1)

        top_group.columnconfigure(0, weight=1)
        top_group.rowconfigure(0, weight=1)

        self.text_pad = scrolledtext.ScrolledText(top_group, width=80, height=40)
        self.text_pad.grid(row=0, column=0, sticky=NSEW)

        with open(self.file, FILE_READ) as file:
            contents = file.read()
            self.text_pad.insert("1.0", contents)
            file.close()

        self.text_pad.edit_modified(False)

        self.edit_win.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self):
        """Close."""
        if self.text_pad.edit_modified():
            title = "SCM-Helper: Save Config"
            msg = "Save Config?"
            resp = messagebox.askyesno(title, msg, parent=self.edit_win)
            if resp:
                if self.save_command() is False:
                    return
        self.edit_win.destroy()

    def save_command(self):
        """Save."""
        with open(self.file, FILE_WRITE) as file:
            # slice off the last character from get, as an extra return is added
            data = self.text_pad.get("1.0", END)
            file.write(data)
            file.close()

        self.gui.notify_text.config(state=NORMAL)

        if self.scm.get_config_file() is False:
            msg = "Error in config file - see status window for details."
            messagebox.showerror("Error", msg, parent=self.parent)
            self.gui.notify_text.config(state=DISABLED)
            return False

        self.text_pad.edit_modified(False)
        self.gui.notify_text.config(state=DISABLED)
        return True


def xlicense():
    """Show License."""
    messagebox.showinfo("License", LICENSE)


def xabout():
    """About message."""
    home = str(Path.home())
    cfg = os.path.join(home, CONFIG_DIR)

    msg = "SCM Helper by Colin Robbins.\n\n"
    msg += f"Version: {VERSION}.\n\n"
    msg += f"Config directory: {cfg}"

    messagebox.showinfo("About", msg)


def xhelp():
    """|Help message."""
    webbrowser.open_new(HELPURL)


def wrap_trace():
    """Give as many error details as possible."""
    tback = sys.exc_info()[2]
    while 1:
        if not tback.tb_next:
            break
        tback = tback.tb_next
    stack = []
    xframe = tback.tb_frame
    while xframe:
        stack.append(xframe)
        xframe = xframe.f_back
    stack.reverse()
    for frame in stack:
        for key, value in frame.f_locals.items():
            # Print likely to cause error itself, but should get enough out of it...
            try:
                debug(f"   {key}: {value.name}", 1)
            # pylint: disable=bare-except
            except:  # noqa: E722
                continue


def wrap(xtime, func, arg=None):
    """Catch programming logic errors."""
    try:
        if xtime is None:
            if arg is not None:
                return func(arg)
            return func()
        if arg is not None:
            return func_timeout(xtime, func, args=[arg])
        return func_timeout(xtime, func)

    except FunctionTimedOut:
        errmsg = traceback.format_exc(10)
        debug(errmsg, 1)
        nowtime = datetime.now().time()
        msg = f"{nowtime}: Abandon {func.__name__} due to timeout ({xtime} secs)"
        wrap_trace()
        messagebox.showerror("Error", msg)
        return False

    # pylint: disable=bad-continuation
    except (
        AssertionError,
        AttributeError,
        LookupError,
        NameError,
        TypeError,
        ValueError,
    ) as err:
        errmsg = traceback.format_exc(10)
        debug(errmsg, 1)
        msg = f"Internal SCM Helper Error:\n{err}\nPlease log an issue on github.\n"
        wrap_trace()
        messagebox.showerror("Error", msg)
        return False
