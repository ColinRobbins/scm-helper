"""Windows GUI."""
import os.path
import sys
import threading
import traceback
import webbrowser
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

from datetime import datetime
from func_timeout import FunctionTimedOut, func_timeout
from scm_helper.api import API
from scm_helper.config import (
    BACKUP_DIR,
    CONFIG_DIR,
    CONFIG_FILE,
    FILE_READ,
    FILE_WRITE,
    HELPURL,
)
from scm_helper.facebook import Facebook
from scm_helper.file import Csv
from scm_helper.issue import REPORTS, IssueHandler, debug
from scm_helper.license import LICENSE
from scm_helper.notify import set_notify
from scm_helper.version import VERSION

NSEW = N + S + E + W


class ScmGui:
    """Tkinter based GUI (for Windows)."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, master):
        """Initialise."""
        # pylint: disable=too-many-statements
        # super().__init__(None)
        self.master = master
        self.analysis_window = None
        self.result_text = None
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

        master.title("SCM Helper")

        self.create_main_window()
        self.create_menu()

        set_notify(self.notify)
        self.issues = IssueHandler()
        self.scm = API(self.issues)
        if self.scm.get_config_file() is False:
            msg = "Error in config file - see status window for details."
            messagebox.showerror("Error", msg, parent=self.master)

        self.api_init = False

        msg = "Welcome to SCM Helper by Colin Robbins.\nPlease enter your password.\n"
        self.notify.insert(END, msg)
        self.notify.config(state=DISABLED)

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

        self.notify = scrolledtext.ScrolledText(top_group, width=60, height=20)
        self.notify.grid(row=0, column=0, sticky=NSEW)

    def create_menu(self):
        """Create Menus."""
        menubar = Menu(self.master)
        file = Menu(menubar, tearoff=0)
        file.add_command(label="Open Archive", command=self.open_archive)
        file.add_separator()
        file.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file)

        cmd = Menu(menubar, tearoff=0)
        cmd.add_command(label="Edit Config", command=self.edit_config)
        cmd.add_separator()
        cmd.add_command(label="Create Lists", command=self.create_lists, state=DISABLED)
        self.menus.append([cmd, "Create Lists"])

        cmd.add_command(label="Fix Errors", command=self.fixit, state=DISABLED)
        self.menu_fixit = [cmd, "Fix Errors"]

        menubar.add_cascade(label="Edit", menu=cmd)

        cmd = Menu(menubar, tearoff=0)

        cmd.add_command(label="Analyse Facebook", command=self.facebook, state=DISABLED)
        self.menus.append([cmd, "Analyse Facebook"])

        cmd.add_command(
            label="Analyse Swim England File", command=self.swim_england, state=DISABLED
        )
        self.menus.append([cmd, "Analyse Swim England File"])

        cmd.add_command(label="List Coaches", command=self.coaches, state=DISABLED)
        self.menus.append([cmd, "List Coaches"])

        cmd.add_command(
            label="Show Not-confirmed Emails", command=self.confirm, state=DISABLED
        )
        self.menus.append([cmd, "Show Not-confirmed Emails"])

        menubar.add_cascade(label="Reports", menu=cmd)

        about = Menu(menubar, tearoff=0)
        about.add_command(label="About...", command=xabout)
        about.add_command(label="Help", command=xhelp)
        about.add_command(label="License", command=xlicense)
        menubar.add_cascade(label="About", menu=about)

        self.master.config(menu=menubar)

    def scm_init(self):
        """Initialise SCM."""
        self.notify.config(state=NORMAL)
        password = self.__password.get()

        self.clear_data()
        self.api_init = False

        if password:
            if self.scm.initialise(password) is False:
                messagebox.showerror("Error", "Cannot initialise SCM (wrong password?)")
                self.clear_data()
                self.notify.config(state=DISABLED)
                return False
            self.api_init = True
            return True

        messagebox.showerror("Password", "Please give a password!")
        self.notify.config(state=DISABLED)

        return False

    def prep_report(self):
        """Prepare for a report."""
        if self.gotdata is False:
            messagebox.showerror("Error", "Run analyse first to colect data")
            return False

        if self.report_window is None:
            self.create_report_window()

        self.report_text.delete("1.0", END)
        self.notify.delete("1.0", END)
        self.report_text.config(state=NORMAL)
        self.notify.config(state=NORMAL)

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
        dir_opt["title"] = "Find Swim Enngland File"
        dir_opt["initialdir"] = cfg
        dir_opt["parent"] = self.report_window
        dir_opt["defaultextension"] = ".csv"

        where = filedialog.askopenfilename(**dir_opt)
        if csv.readfile(where, self.scm) is False:
            messagebox.showerror("Error", "Could not read CSV file")
            self.notify.config(state=DISABLED)
            self.report_text.config(state=DISABLED)
            return

        if wrap(10, csv.analyse, self.scm) is False:
            self.notify.config(state=DISABLED)
            self.report_text.config(state=DISABLED)
            return

        output = csv.print_errors()

        del csv
        self.report_text.insert(END, output)
        self.report_text.config(state=DISABLED)
        self.notify.config(state=DISABLED)
        self.report_window.lift()

    def facebook(self):
        """Process a Facebook report."""
        if self.prep_report() is False:
            return

        fbook = Facebook()
        if fbook.readfiles(self.scm) is False:
            messagebox.showerror("Error", "Could not read facebook files")
            self.report_text.config(state=DISABLED)
            self.notify.config(state=DISABLED)
            return

        wrap(None, fbook.analyse)
        output = fbook.print_errors()

        fbook.delete()
        del fbook
        self.report_text.insert(END, output)
        self.report_text.config(state=DISABLED)
        self.notify.config(state=DISABLED)
        self.report_window.lift()

    def confirm(self):
        """Confirm email Report."""
        if self.prep_report() is False:
            return

        output = self.issues.confirm_email()
        self.report_text.insert(END, output)
        self.report_text.config(state=DISABLED)
        self.notify.config(state=DISABLED)
        self.report_window.lift()

    def coaches(self):
        """Coaches Report."""
        if self.prep_report() is False:
            return

        output = self.scm.sessions.print_coaches()
        self.report_text.insert(END, output)
        self.report_text.config(state=DISABLED)
        self.notify.config(state=DISABLED)
        self.report_window.lift()

    def edit_config(self):
        """Edit Config."""
        home = str(Path.home())
        cfg = os.path.join(home, CONFIG_DIR, CONFIG_FILE)

        Edit(self.master, cfg, self.scm)

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

    def fixit(self):
        """Window for reports."""
        if self.thread:
            return  # already running

        if self.gotdata is False:
            messagebox.showerror("Error", "Analyse data first, before fixing")
            return

        self.buttons(DISABLED)

        length = len(self.scm.fixable)
        if length == 0:
            messagebox.showerror("Error", "Nothing to fix")
            self.buttons(NORMAL)
            return

        wrap(None, self.scm.apply_fixes)

        self.buttons(NORMAL)

    def backup(self):
        """Window for reports."""
        if self.thread:
            return  # already running

        if self.scm_init() is False:
            return

        self.thread = BackupThread(self).start()

    def clear_data(self):
        """Prepare to rerun."""
        self.scm.delete()
        self.gotdata = False

    def buttons(self, status):
        """Change button state."""
        self.button_analyse.config(state=status)
        self.button_backup.config(state=status)

        for menu, item in self.menus:
            menu.entryconfig(item, state=status)

        menu, item = self.menu_fixit

        if status == NORMAL:
            self.notify.config(state=DISABLED)
            length = len(self.scm.fixable)
            if length == 0:
                self.button_fixit.config(state=DISABLED)
                menu.entryconfig(item, state=DISABLED)
                return
        else:
            self.notify.config(state=NORMAL)

        self.button_fixit.config(state=status)
        menu.entryconfig(item, state=status)

    def process_option(self, _):
        """Process an option selection."""
        report = self.reports.get()
        mode = self.grouping.get()

        self.result_text.config(state=NORMAL)
        self.notify.config(state=NORMAL)
        self.result_text.delete("1.0", END)

        if report == "All Reports":
            report = None
        else:
            report = report.lower()

        if mode == "Error":
            output = self.issues.print_by_error(report)
        else:
            output = self.issues.print_by_name(report)

        self.result_text.insert(END, output)
        self.result_text.config(state=DISABLED)
        self.notify.config(state=DISABLED)

    def create_report_window(self):
        """Create the reports window."""
        self.report_window = Toplevel(self.master)
        self.report_window.title("SCM Helper - Reports")

        top_frame = Frame(self.report_window)
        top_frame.grid(row=0, column=0, sticky=W + E)

        self.report_window.columnconfigure(0, weight=1)
        self.report_window.rowconfigure(0, weight=1)

        self.report_text = scrolledtext.ScrolledText(top_frame, width=80, height=40)
        self.report_text.grid(row=0, column=0, sticky=NSEW)

        self.report_window.protocol("WM_DELETE_WINDOW", self.close_report)

    def close_report(self):
        """Close report window."""
        self.report_window.destroy()
        self.report_window = None


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
        self.gui.buttons(DISABLED)

        if self.gui.analysis_window:
            self.gui.result_text.config(state=NORMAL)
            self.gui.result_text.delete("1.0", END)

        self.gui.notify.delete("1.0", END)

        if self.scm.get_config_file() is False:
            messagebox.showerror("Error", f"Error in config file.")
            self.gui.buttons(NORMAL)
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
                self.gui.buttons(NORMAL)
                return
        else:
            if wrap(None, self.scm.get_data, False) is False:
                messagebox.showerror("Analsyis", "Failed to read data")
                self.gui.buttons(NORMAL)
                self.gui.thread = None
                return

        if wrap(10, self.scm.linkage) is False:
            self.gui.buttons(NORMAL)
            self.gui.thread = None
            return

        if wrap(10, self.scm.analyse) is False:
            self.gui.buttons(NORMAL)
            self.gui.thread = None
            debug("Analyse returned False",1)
            return

        self.gui.gotdata = True

        if self.gui.analysis_window is None:
            self.create_window()

        debug("Analyse returned - creating result window", 1)
        
        output = self.gui.issues.print_by_error(None)
        
        result = self.scm.print_summary()

        self.gui.notify.insert(END, result)
        self.gui.notify.see(END)
        self.gui.result_text.insert(END, output)
        self.gui.analysis_window.lift()

        self.gui.buttons(NORMAL)
        self.gui.result_text.config(state=DISABLED)

        self.gui.thread = None

        debug("Analyse Thread complete, result posted", 1)
        print ("Is this a Windows error?")
        print (result)
        print ("Should see the report above?")


        return

    def create_window(self):
        """Create the results window."""
        self.gui.analysis_window = Toplevel(self.gui.master)
        self.gui.analysis_window.title("SCM Helper - Analysis")

        self.gui.reports = StringVar()
        self.gui.reports.set("All Reports")

        top_frame = Frame(self.gui.analysis_window)
        top_frame.grid(row=0, column=0, sticky=W + E)

        label = Label(top_frame, text="Select Report: ")
        label.grid(row=0, column=0, pady=10, padx=10)

        rpts = [resp.title() for resp in REPORTS]
        all_reports = ["All Reports"] + rpts

        menu = OptionMenu(
            top_frame, self.gui.reports, *all_reports, command=self.gui.process_option,
        )
        menu.grid(row=0, column=1, pady=10, padx=10)

        self.gui.grouping = StringVar()
        self.gui.grouping.set("Error")

        label = Label(top_frame, text="Group Report by: ")
        label.grid(row=0, column=2, pady=10, padx=10)

        menu = OptionMenu(
            top_frame,
            self.gui.grouping,
            "Error",
            "Member",
            command=self.gui.process_option,
        )
        menu.grid(row=0, column=3, pady=10, padx=10)

        txt = "Analysis..."
        top_group = LabelFrame(self.gui.analysis_window, text=txt, pady=5, padx=5)
        top_group.grid(row=1, column=0, columnspan=4, pady=10, padx=10, sticky=NSEW)

        self.gui.analysis_window.columnconfigure(0, weight=1)
        self.gui.analysis_window.rowconfigure(1, weight=1)

        top_group.columnconfigure(0, weight=1)
        top_group.rowconfigure(0, weight=1)

        self.gui.result_text = scrolledtext.ScrolledText(
            top_group, width=100, height=40
        )
        self.gui.result_text.grid(row=0, column=0, sticky=NSEW)

        self.gui.analysis_window.protocol("WM_DELETE_WINDOW", self.close_report)

    def close_report(self):
        """Close report window."""
        self.gui.analysis_window.destroy()
        self.gui.analysis_window = None


class BackupThread(threading.Thread):
    """Thread to run Backuo."""

    def __init__(self, gui):
        """Initialise."""
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm

    def run(self):
        """Run analyser."""
        self.gui.buttons(DISABLED)
        self.gui.notify.delete("1.0", END)

        if wrap(None, self.scm.backup_data):
            output = self.scm.print_summary(backup=True)
            self.gui.notify.insert(END, output)
            self.gui.notify.insert(END, "Backup Complete.")
            self.gui.notify.see(END)
        else:
            messagebox.showerror("Error", "Backup failure")

        self.gui.buttons(NORMAL)
        self.gui.thread = None


class UpdateThread(threading.Thread):
    """Thread to run Backuo."""

    def __init__(self, gui):
        """Initialise."""
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm

    def run(self):
        """Run analyser."""
        self.gui.buttons(DISABLED)
        self.gui.notify.delete("1.0", END)

        wrap(None, self.scm.update)

        self.gui.notify.see(END)
        self.gui.buttons(NORMAL)
        self.gui.thread = None


class Edit(Frame):  # pylint: disable=too-many-ancestors
    """Class to edit a frame."""

    def __init__(self, parent, filename, scm):
        """Initialise."""
        Frame.__init__(self, parent)
        self.parent = parent
        self.file = filename
        self.scm = scm

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

        if self.scm.get_config_file() is False:
            msg = "Error in config file - see status window for details."
            messagebox.showerror("Error", msg, parent=self.parent)
            return False

        self.text_pad.edit_modified(False)
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
                debug(f"   {key}: {value.name}", 0)
            # pylint: disable=bare-except
            except:
                continue


def wrap(xtime, func, arg=None):
    """Catch programming logic errors."""
    try:
        if xtime is None:
            if arg is not None:
                return func(arg)
            return func()
        if arg is not None:
            return func_timeout(xtime, func, args=args)
        return func_timeout(xtime, func)

    except FunctionTimedOut:
        errmsg = traceback.format_exc(10)
        debug(errmsg, 0)
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
        debug(errmsg, 0)
        msg = f"Internal SCM Helper Error:\n{err}\nPlease log an issue on github.\n"
        wrap_trace()
        messagebox.showerror("Error", msg)
        return False
