"""Windows GUI."""
import os.path
import threading
import webbrowser
from pathlib import Path
from tkinter import (
    DISABLED,
    END,
    NORMAL,
    Button,
    Entry,
    Frame,
    Label,
    LabelFrame,
    Menu,
    OptionMenu,
    Scrollbar,
    StringVar,
    Text,
    Tk,
    Toplevel,
    W,E,S,N,
    filedialog,
    messagebox,
    scrolledtext,
)

from api import API
from config import (
    BACKUP_DIR,
    CONFIG_DIR,
    CONFIG_FILE,
    FILE_READ,
    FILE_WRITE,
    HELPURL,
)
from facebook import Facebook
from file import Csv
from issue import REPORTS, IssueHandler
from notify import set_notify
from license import LICENSE
from version import VERSION


class ScmGui():
    """Tkinter based GUI (for Windows)."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, master):
        """Initialise."""
        # pylint: disable=too-many-statements
        # super().__init__(None)
        self.master = master
        self.result_window = None
        self.result_text = None
        self.report_window = None
        self.report_text = None
        self.issues = None
        self.scm = None
        self.gotdata = False
        self.thread = None
        self.grouping = None
        self.reports = None

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

    def create_main_window(self):
        """Create the main window."""
        # Row 1
        myrow = 1

        top_frame = Frame(self.master)
        top_frame.grid(row=0, column=0, sticky=W+E)
        
        label = Label(top_frame, text="Password: ")
        label.grid(row=0, column=0, pady=10, padx=10, )

        self.__password = StringVar()
        self.__password.set("")
        password = Entry(top_frame, show="*", textvariable=self.__password, width=20)
        password.grid(row=0, column=1, pady=10, padx=10)

        msg = "Analyse"
        self.button_analyse = Button(top_frame, text=msg, command=self.analyse_window)
        self.button_analyse.grid(row=0, column=2, pady=10, padx=10)

        self.button_backup = Button(top_frame, text="Backup", command=self.backup)
        self.button_backup.grid(row=0, column=3, pady=10, padx=10)

        self.button_fixit = Button( top_frame, text="Fixit", command=self.fixit)
        self.button_fixit.config(state=DISABLED)
        self.button_fixit.grid(row=0, column=4, pady=10, padx=10)

        top_group = LabelFrame(self.master, text="Notifications", pady=5, padx=5)
        top_group.grid(row=1, column=0, columnspan=5, pady=10, padx=10, sticky=E+W+N+S)
        
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)
        
        top_group.columnconfigure(0, weight=1)
        top_group.rowconfigure(0, weight=1)

        self.notify = scrolledtext.ScrolledText(top_group, width=60, height=20)
        self.notify.grid(row=0, column=0, sticky=E+W+N+S)

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
        cmd.add_command(label="Create Lists", command=self.create_lists)
        cmd.add_command(label="Fix Errors", command=self.fixit)
        menubar.add_cascade(label="Edit", menu=cmd)

        cmd = Menu(menubar, tearoff=0)
        cmd.add_command(label="Analyse Facebook", command=self.facebook)
        cmd.add_command(label="Analyse Swim England File", command=self.swim_england)
        cmd.add_command(label="List Coaches", command=self.coaches)
        cmd.add_command(label="Show Not-confirmed Emails", command=self.confirm)
        menubar.add_cascade(label="Reports", menu=cmd)

        about = Menu(menubar, tearoff=0)
        about.add_command(label="About...", command=xabout)
        about.add_command(label="Help", command=xhelp)
        about.add_command(label="License", command=license)
        menubar.add_cascade(label="About", menu=about)

        self.master.config(menu=menubar)

    def scm_init(self):
        """Initialise SCM."""
        password = self.__password.get()
        
        self.clear_data()
        self.api_init = False
        
        if password:
            if self.scm.initialise(password) is False:
                messagebox.showerror("Error", "Cannot initialise SCM (wrong password?)")
                self.clear_data()
                return False
            self.api_init = True
            return True

        messagebox.showerror("Password", "Please give a password!")
        return False

    def prep_report(self):
        """Prepare for a report."""
        if self.gotdata is False:
            messagebox.showerror("Error", "Run analyse first to colect data")
            return False

        if self.report_window is None:
            self.create_report_window()
        self.report_text.delete("1.0", END)

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
        dir_opt["mustexist"] = True
        dir_opt["parent"] = self.master
        dir_opt["defaultextension"] = ".csv"

        where = filedialog.askopenfilename(**dir_opt)
        if csv.readfile(where, self.scm) is False:
            messagebox.showerror("Error", "Could not read CSV file")
            return

        csv.analyse(self.scm)
        output = csv.print_errors()
        self.report_text.insert(END, output)

    def facebook(self):
        """Process a Facebook report."""
        if self.prep_report() is False:
            return

        fbook = Facebook()
        if fbook.readfiles(self.scm) is False:
            messagebox.showerror("Error", "Could not read facebook files")
            return

        fbook.analyse()
        output = fbook.print_errors()
        self.report_text.insert(END, output)

    def confirm(self):
        """Confirm email Report."""
        if self.prep_report() is False:
            return

        output = self.issues.confirm_email()
        self.report_text.insert(END, output)

    def coaches(self):
        """Coaches Report."""
        if self.prep_report() is False:
            return

        output = self.scm.sessions.print_coaches()
        self.report_text.insert(END, output)

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

        self.scm.apply_fixes()

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
        if status == NORMAL:
            length = len(self.scm.fixable)
            if length == 0:
                self.button_fixit.config(state=DISABLED)
                return
        self.button_fixit.config(state=status)

    def process_option(self, _):
        """Process an option selection."""
        report = self.reports.get()
        mode = self.grouping.get()

        self.result_text.config(state=NORMAL)
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

    def create_report_window(self):
        """Create the reports window."""
        self.report_window = Toplevel(self.master)
        self.report_window.title("SCM Helper - Reports")
        
        top_frame = Frame(self.report_window)
        top_frame.grid(row=0, column=0, sticky=W+E)

        self.report_window.columnconfigure(0, weight=1)
        self.report_window.rowconfigure(0, weight=1)

        self.report_text = scrolledtext.ScrolledText(top_frame, width=80, height=40)
        self.report_text.grid(row=0, column=0, sticky=E+W+N+S)
        
        self.report_window.protocol("WM_DELETE_WINDOW", self.close_report)

    def close_report(self):
        """Action on close."""
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

        if self.gui.result_window:
            self.gui.result_text.config(state=NORMAL)
            self.gui.result_text.delete("1.0", END)

        self.gui.notify.delete("1.0", END)
            
        if self.scm.get_config_file() is False:
            messagebox.showerror("Error", f"Error in config file.")
            return

        if self.archive:

            home = str(Path.home())
            backup = os.path.join(home, CONFIG_DIR, BACKUP_DIR)

            dir_opt = {}
            dir_opt["initialdir"] = backup
            dir_opt["mustexist"] = True
            dir_opt["parent"] = self.gui.master

            where = filedialog.askdirectory(**dir_opt)
            if self.scm.decrypt(where) is False:
                messagebox.showerror("Error", f"Cannot read from archive: {where}")
                self.gui.buttons(NORMAL)
                return
        else:
            if self.scm.get_data(False) is False:
                messagebox.showerror("Analsyis", "Failed to read data")
                self.gui.buttons(NORMAL)
                self.gui.thread = None
                return

        if self.scm.linkage() is False:
            messagebox.showerror("Analsyis", "Error processing data")
            self.gui.buttons(NORMAL)
            self.gui.thread = None
            return

        self.scm.analyse()
        self.gui.gotdata = True

        if self.gui.result_window is None:
            self.create_window()

        output = self.gui.issues.print_by_error(None)
        
        self.gui.notify.insert(END, self.scm.print_summary())
        self.gui.result_text.insert(END, output)
        self.gui.result_window.lift()

        self.gui.buttons(NORMAL)
        self.gui.result_text.config(state=DISABLED)

        self.gui.thread = None
        
        return

    def create_window(self):
        """Create the results window."""
        self.gui.result_window = Toplevel(self.gui.master)
        self.gui.result_window.title("SCM Helper - Results")

        self.gui.reports = StringVar()
        self.gui.reports.set("All Reports")
        
        top_frame = Frame(self.gui.result_window)
        top_frame.grid(row=0, column=0, sticky=W+E)

        label = Label(top_frame, text="Select Report: ")
        label.grid(row=0, column=0, pady=10, padx=10)
        
        rpts = [resp.title() for resp in REPORTS]
        all_reports = ["All Reports"] + rpts

        menu = OptionMenu(
            top_frame,
            self.gui.reports,
            *all_reports,
            command=self.gui.process_option,
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

        top_group = LabelFrame(self.gui.result_window, text="Analysis...", pady=5, padx=5)
        top_group.grid(row=1, column=0, columnspan=4, pady=10, padx=10, sticky=E+W+N+S)
        
        self.gui.result_window.columnconfigure(0, weight=1)
        self.gui.result_window.rowconfigure(1, weight=1)
        
        top_group.columnconfigure(0, weight=1)
        top_group.rowconfigure(0, weight=1)

        self.gui.result_text = scrolledtext.ScrolledText(top_group, width=100, height=40)
        self.gui.result_text.grid(row=0, column=0, sticky=E+W+N+S)

        self.gui.result_window.protocol("WM_DELETE_WINDOW", self.close_report)

    def close_report(self):
        """Action on close."""
        self.gui.result_window.destroy()
        self.gui.result_window = None


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

        if self.scm.backup_data():
            output = self.scm.print_summary(backup=True)
            self.gui.notify.insert(END, output)
            self.gui.notify.insert(END, "Backup Complete.")
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
        self.scm.update()
        self.gui.notify.insert(END, "Lists Created.")

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
        top_frame.grid(row=0, column=0, sticky=W+E)

        abtn = Button(top_frame, text="Save", command=self.save_command)
        abtn.grid(row=0, column=0, pady=10, padx=10)

        cbtn = Button(top_frame, text="Close", command=self.on_exit)
        cbtn.grid(row=0, column=1, pady=10, padx=10)
        
        top_group = LabelFrame(self.edit_win, text=filename, pady=5, padx=5)
        top_group.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky=E+W+N+S)
        
        self.edit_win.columnconfigure(0, weight=1)
        self.edit_win.rowconfigure(1, weight=1)
        
        top_group.columnconfigure(0, weight=1)
        top_group.rowconfigure(0, weight=1)

        self.text_pad = scrolledtext.ScrolledText(top_group, width=80, height=40)
        self.text_pad.grid(row=0, column=0, sticky=E+W+N+S)

        with open(self.file, FILE_READ) as file:
            contents = file.read()
            self.text_pad.insert("1.0", contents)
            file.close()
            
        self.text_pad.edit_modified(False)
        
        self.edit_win.protocol("WM_DELETE_WINDOW", self.on_exit)

    def on_exit(self):
        """Close."""
        if (self.text_pad.edit_modified()):
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

def license():
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
