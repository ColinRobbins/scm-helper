"""Windows GUI."""
import threading
from tkinter import (
    DISABLED,
    END,
    NORMAL,
    Button,
    Entry,
    Frame,
    Label,
    OptionMenu,
    Radiobutton,
    Scrollbar,
    StringVar,
    Text,
    Tk,
    Toplevel,
    W,
    messagebox,
)

from api import API
from issue import REPORTS, IssueHandler
from notify import set_notify


class ScmGui(Tk):
    """Tkinter based GUI (for Windows)."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, master):
        """Initialise."""
        # pylint: disable=too-many-statements
        self.master = master
        self.result_window = None
        self.result_text = None
        self.issues = None
        self.scm = None
        self.gotdata = False
        self.thread = None

        master.title("SCM Helper")

        # Row 1
        myrow = 1
        label = Label(master, text="Password: ")
        label.grid(row=myrow, column=1, sticky=W, pady=2)
        self.__password = StringVar()
        self.__password.set("")
        password = Entry(master, show="*", textvariable=self.__password, width=15)
        password.grid(row=myrow, column=2, sticky=W)

        # Row 2
        myrow = 2
        self.report_option = StringVar()
        self.report_option.set("--error")

        label = Label(master, text="Report Format: ")
        label.grid(row=myrow, column=1, sticky=W, pady=2)

        radio = Radiobutton(
            master, text="By error", variable=self.report_option, value="--error"
        )
        radio.grid(row=myrow, column=2, sticky=W)

        radio = Radiobutton(
            master, text="By member", variable=self.report_option, value="--member"
        )
        radio.grid(row=myrow, column=3, sticky=W)

        # Row 3
        myrow = 3
        self.src_option = StringVar()
        self.src_option.set("--scm")

        label = Label(master, text="Data source: ")
        label.grid(row=myrow, column=1, sticky=W, pady=2)

        radio = Radiobutton(master, text="SCM", variable=self.src_option, value="--scm")
        radio.grid(row=myrow, column=2, sticky=W)

        radio = Radiobutton(
            master, text="Archive", variable=self.src_option, value="--archive"
        )
        radio.grid(row=myrow, column=3, sticky=W)

        self.archive = StringVar()
        self.archive.set("")
        archive = Entry(master, textvariable=self.archive, width=15)
        archive.grid(row=myrow, column=4, sticky=W)

        # Row 4
        myrow = 4

        self.reports = StringVar()
        self.reports.set("All")

        label = Label(master, text="Reports required: ")
        label.grid(row=myrow, column=1, sticky=W, pady=2)

        all_reports = ["all"] + REPORTS

        self.reports_menu = OptionMenu(master, self.reports, *all_reports)
        self.reports_menu.grid(row=myrow, column=2, sticky=W)

        # Row 5
        myrow = 5

        self.button_analyse = Button(master, text="Analyse", command=self.report_window)
        self.button_analyse.grid(row=myrow, column=1, pady=2)

        self.button_backup = Button(master, text="Backup", command=self.backup_window)
        self.button_backup.grid(row=myrow, column=2)

        button = Button(master, text="Close", command=master.quit)
        button.grid(row=myrow, column=4)

        # Row 6
        myrow = 6
        self.notify = TextScrollCombo(master)
        self.notify.config(width=500, height=200)
        self.notify.grid(row=myrow, column=1, columnspan=4, pady=2)
        set_notify(self.notify)
        self.issues = IssueHandler()
        self.scm = API(self.issues)
        self.scm.get_config_file()
        self.api_init = False

    def scm_init(self):
        """Initialise SCM."""
        password = self.__password.get()
        if password:
            if self.scm.initialise(password) is False:
                messagebox.showerror("Error", "Cannot initialise SCM (wrong password?)")
                return False
            self.api_init = True
            return True
            
        messagebox.showerror("Password", "Please give a password!")
        return False

    def report_window(self):
        """Window for reports."""
        if self.api_init is False:
            if self.scm_init() is False:
                return

        if self.thread:
            return  # already running

        self.thread = AnalysisThread(self).start()

    def backup_window(self):
        """Window for reports."""
        if self.api_init is False:
            if self.scm_init() is False:
                return

        if self.thread:
            return  # already running

        self.thread = BackupThread(self).start()

    def clear_data(self):
        """Prepare to rerun."""
        if self.gotdata:
            self.scm.delete()
        self.gotdata = False


class AnalysisThread(threading.Thread):
    """Thread to run analysis."""

    def __init__(self, gui):
        """Initialise."""
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm

    def run(self):
        """Run analyser."""
        self.gui.button_analyse.config(state=DISABLED)
        self.gui.button_backup.config(state=DISABLED)

        self.gui.notify.txt.delete("1.0", END)
        self.gui.clear_data()

        archive = self.gui.src_option.get()
        if archive == "--archive":
            if self.scm.decrypt(self.gui.archive.get()) is False:
                messagebox.showerror("Error", f"Cannot read from archive: {archive}")
        else:
            if self.scm.get_data(False) is False:
                messagebox.showerror("Analsyis", "Failed to read data")
                self.gui.button_analyse.config(state=NORMAL)
                self.gui.button_backup.config(state=NORMAL)
                self.gui.thread = None
                return

        if self.scm.linkage() is False:
            messagebox.showerror("Analsyis", "Error processing data")
            self.gui.button_analyse.config(state=NORMAL)
            self.gui.button_backup.config(state=NORMAL)
            self.gui.thread = None
            return

        self.scm.analyse()
        self.gui.gotdata = True

        reports = self.gui.reports.get()
        if reports == "All":
            reports = None

        if self.gui.result_window is None:
            self.gui.result_window = Toplevel(self.gui.master)
            self.gui.result_window.title("SCM Helper - Results")
            self.gui.result_text = TextScrollCombo(self.gui.result_window)
            self.gui.result_text.config(width=800, height=800)
            self.gui.result_text.grid(row=1, column=1)

        if self.gui.report_option.get() == "--error":
            output = self.gui.issues.print_by_error(reports)
        else:
            output = self.gui.issues.print_by_name(reports)

        self.gui.result_text.insert(END, output)

        self.gui.button_analyse.config(state=NORMAL)
        self.gui.button_backup.config(state=NORMAL)
        self.gui.thread = None

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
        self.gui.button_analyse.config(state=DISABLED)
        self.gui.button_backup.config(state=DISABLED)

        self.gui.notify.txt.delete("1.0", END)
        self.gui.clear_data()

        if self.scm.backup_data():
            output = self.scm.print_summary()
            self.notify.txt.insert(END, output)

        self.gui.button_analyse.config(state=NORMAL)
        self.gui.button_backup.config(state=NORMAL)
        self.gui.thread = None

        return

class TextScrollCombo(Frame):
    """Text scrolling combo."""

    # Credit: https://stackoverflow.com/questions/13832720/
    # how-to-attach-a-scrollbar-to-a-text-widget

    def __init__(self, *args, **kwargs):
        """Initialise."""
        super().__init__(*args, **kwargs)

        # ensure a consistent GUI size
        self.grid_propagate(False)
        # implement stretchability
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # create a Text widget
        self.txt = Text(self)
        self.txt.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # create a Scrollbar and associate it with txt
        scrollb = Scrollbar(self, command=self.txt.yview)
        scrollb.grid(row=0, column=1, sticky="nsew")
        self.txt["yscrollcommand"] = scrollb.set

    def insert(self, where, what):
        """Insert text."""
        self.txt.insert(where, what)

    def write(self, what):
        """Insert text at the end."""
        self.txt.insert(END, what)
