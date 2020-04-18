"""Windows GUI."""
import threading
import webbrowser
import os.path

from tkinter import (
    DISABLED,
    END,
    NORMAL,
    Button,
    Entry,
    filedialog,
    Frame,
    Label,
    Menu,
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
from config import VERSION, CONFIG_DIR, BACKUP_DIR, HELPURL, CONFIG_FILE, FILE_WRITE


from pathlib import Path



class ScmGui(Tk):
    """Tkinter based GUI (for Windows)."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, master):
        """Initialise."""
        # pylint: disable=too-many-statements
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
        self.scm.get_config_file()
        self.api_init = False
        
        msg = ("Welcome to SCM Helper by Colin Robbins.\nPlease enter your password.\n")
        self.notify.txt.insert(END, msg)

    def create_main_window(self):
        """Create the main window."""
        # Row 1
        myrow = 1
        label = Label(self.master, text="Password: ")
        label.grid(row=myrow, column=1, sticky=W, pady=2)
        self.__password = StringVar()
        self.__password.set("")
        password = Entry(self.master, show="*", textvariable=self.__password, width=20)
        password.grid(row=myrow, column=2, sticky=W)

        self.button_analyse = Button(self.master, text="Analyse", command=self.analyse_window)
        self.button_analyse.grid(row=myrow, column=3, pady=2, sticky=W)

        self.button_backup = Button(self.master, text="Backup", command=self.backup)
        self.button_backup.grid(row=myrow, column=4, sticky=W)

        self.button_fixit = Button(self.master, text="Fixit", command=self.fixit, state=DISABLED)
        self.button_fixit.grid(row=myrow, column=5, sticky=W)

        # Row 2
        myrow = 2
        self.notify = ScrollingText(self.master)
        self.notify.config(width=600, height=250)
        self.notify.grid(row=myrow, column=1, columnspan=5, pady=2)
        

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
        file.add_separator()
        cmd.add_command(label="Create Lists", command=self.create_lists)
        cmd.add_command(label="Fix Errors", command=self.fixit)
        menubar.add_cascade(label="Edit", menu=cmd)
        
        cmd = Menu(menubar, tearoff=0)
        cmd.add_command(label="Analyse Swim England File", command=self.swim_england)
        cmd.add_command(label="Analyse Facebook", command=self.facebook)
        cmd.add_command(label="List Coaches", command=self.coaches)
        cmd.add_command(label="Show Not-confirmed Emails", command=self.confirm)
        menubar.add_cascade(label="Reports", menu=cmd)
        
        about = Menu(menubar, tearoff=0)
        about.add_command(label="About...", command=self.about)
        about.add_command(label="Help.", command=self.help)
        menubar.add_cascade(label="About", menu=about)
        
        self.master.config(menu=menubar)
        
    def scm_init(self):
        """Initialise SCM."""
        password = self.__password.get()
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
        self.report_text.txt.delete("1.0", END)
        
        return True
        
    def open_archive(self):
        """Open Archive file."""

        if self.api_init is False:
            if self.scm_init() is False:
                return

        if self.thread:
            return  # already running

        self.thread = AnalysisThread(self, True).start()

    def swim_england(self):
        """Process Swim England File."""

        if self.prep_report() is False:
            return

        home = str(Path.home())
        cfg = os.path.join(home, CONFIG_DIR)

        dir_opt = {}
        dir_opt['initialdir'] = cfg
        dir_opt['mustexist'] = True
        dir_opt['parent'] = self.gui.master
        dir_opt['defaultextension'] = ".csv"

        where = filedialog.askfilename(**dir_opt)
        
        output = csv.print_errors()
        self.report_text.insert(END, output)

    def facebook(self):
        """Process a Facebook report."""
        if self.prep_report() is False:
            return
        
        fbook = Facebook()
        if fbook.readfiles(scm) is False:
            messagebox.showerror("Error", "Could not read facebook files")
            return
        
        fbook.analyse()
        output = fbook.print_errors()
        self.report_text.insert(END, output)


    def confirm(self):
        """Confirmation Report."""
        if self.prep_report() is False:
            return
        
        output = self.issues.confirm_email()
        self.report_text.insert(END, output)

    def coaches(self):
        """Coaches Report."""
        if self.prep_report() is False:
            return
        
        output = scm.sessions.print_coaches()
        self.report_text.insert(END, output)
        
    def edit_config(self):
        """Edit Config."""

        home = str(Path.home())
        cfg = os.path.join(home, CONFIG_DIR, CONFIG_FILE)

        dir_opt = {}
        dir_opt['initialdir'] = cfg
        dir_opt['mustexist'] = True
        dir_opt['parent'] = self.gui.master
        dir_opt['defaultextension'] = ".yaml"

        where = filedialog.askfilename(**dir_opt)
        
        edit(self.master, where)
        
    def create_lists(self):
        """Create Lists."""
        if self.gotdata is False:
            messagebox.showerror("Error", "Run analyse first to collect data")
            return False

        if self.thread:
            return  # already running
        
        self.thread = UpdateThread(self).start()

    def about(self):
        """About message."""
        home = str(Path.home())
        cfg = os.path.join(home, CONFIG_DIR)
        
        msg = "SCM Helper by Colin Robbins.\n"
        msg += f"Version: {VERSION}.\n"
        msg += f"Config directory: {cfg}"
        
        messagebox.showinfo("About", msg)

    def help(self):
        """help message."""
        webbrowser.open_new(HELPURL)

    def analyse_window(self):
        """Window for analysis result."""
        if self.api_init is False:
            if self.scm_init() is False:
                return

        if self.thread:
            return  # already running

        self.thread = AnalysisThread(self, False).start()

    def fixit(self):
        """Window for reports."""
        if self.api_init is False:
            if self.scm_init() is False:
                return

        if self.thread:
            return  # already running
        
        if self.gotdata == False:
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
        if self.api_init is False:
            if self.scm_init() is False:
                return

        if self.thread:
            return  # already running

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

    def process_option(self, dummy):
        """Process an option selection."""
        report = self.reports.get()
        mode = self.grouping.get()
        
        self.result_text.txt.delete("1.0", END)
        
        if report == "all reports":
            report = None

        if mode == "error":
            output = self.issues.print_by_error(report)
        else:
            output = self.issues.print_by_name(report)
            
        self.result_text.insert(END, output)
        
    def create_report_window(self):
        """Create the reports window."""
        self.report_window = Toplevel(self.gui.master)
        self.report_window.title("SCM Helper - Reports")
        
        self.report_text = ScrollingText(self.gui.result_window)
        self.report_text.config(width=800, height=800)
        self.report_text.grid(row=1, column=1)

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

        self.gui.notify.txt.delete("1.0", END)
        self.gui.clear_data()
        if self.gui.get_config_file() is False:
            messagebox.showerror("Error", f"Error in config file.")
            return

        if self.archive:
            
            home = str(Path.home())
            cfg = os.path.join(home, CONFIG_DIR)
            backup = os.path.join(home, CONFIG_DIR, BACKUP_DIR)

            dir_opt = {}
            dir_opt['initialdir'] = backup
            dir_opt['mustexist'] = True
            dir_opt['parent'] = self.gui.master
    
            where = filedialog.askdirectory(**dir_opt)
            if self.scm.decrypt(where) is False:
                messagebox.showerror("Error", f"Cannot read from archive: {where}")
                self.gui.clear_data()
                self.gui.buttons(NORMAL)
                return
        else:
            if self.scm.get_data(False) is False:
                messagebox.showerror("Analsyis", "Failed to read data")
                self.gui.clear_data()
                self.gui.buttons(NORMAL)
                self.gui.thread = None
                return

        if self.scm.linkage() is False:
            messagebox.showerror("Analsyis", "Error processing data")
            self.gui.clear_data()
            self.gui.buttons(NORMAL)
            self.gui.thread = None
            return

        self.scm.analyse()
        self.gui.gotdata = True

        if self.gui.result_window is None:
            self.create_window()

        output = self.gui.issues.print_by_error(None)

        self.gui.result_text.insert(END, output)
        self.gui.master.lift()

        self.gui.buttons(NORMAL)
        self.gui.thread = None

        return

    def create_window(self):
        """Create the results window."""
        self.gui.result_window = Toplevel(self.gui.master)
        self.gui.result_window.title("SCM Helper - Results")
        
        # Row 1
        myrow = 1

        self.gui.reports = StringVar()
        self.gui.reports.set("all reports")

        label = Label(self.gui.result_window, text="Select Report: ")
        label.grid(row=myrow, column=1, sticky=W, pady=2)

        all_reports = ["all reports"] + REPORTS

        menu = OptionMenu(self.gui.result_window, self.gui.reports, *all_reports, command=self.gui.process_option)
        menu.grid(row=myrow, column=2, sticky=W)
        
        self.gui.grouping = StringVar()
        self.gui.grouping.set("Error")

        label = Label(self.gui.result_window, text="Group Report by: ")
        label.grid(row=myrow, column=3, sticky=W, pady=2)

        menu = OptionMenu(self.gui.result_window, self.gui.grouping, "Error", "Member", command=self.gui.process_option)
        menu.grid(row=myrow, column=4, sticky=W)

        # Row 2
        myrow = 2
        
        self.gui.result_text = ScrollingText(self.gui.result_window)
        self.gui.result_text.config(width=800, height=800)
        self.gui.result_text.grid(row=myrow, column=1, columnspan=6)
        

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

        self.gui.notify.txt.delete("1.0", END)
        self.gui.clear_data()

        if self.scm.backup_data():
            output = self.scm.print_summary(backup=True)
            self.gui.notify.txt.insert(END, output)
            self.gui.notify.txt.insert(END, "Backup Complete.")
        else:
            messagebox.showerror("Error", "Backup failure")


        self.gui.buttons(NORMAL)
        self.gui.thread = None

        return
    
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

        self.gui.notify.txt.delete("1.0", END)
        self.gui.clear_data()

        self.scm.update()
        
        self.gui.notify.txt.insert(END, "Lists Created.")

        self.gui.buttons(NORMAL)
        self.gui.thread = None

        return

class ScrollingText(Frame):
    """Text scrolling combo."""

    # Credit: https://stackoverflow.com/questions/13832720/
    # how-to-attach-a-scrollbar-to-a-text-widget

    def __init__(self, *args, **kwargs):
        """Initialise."""
        super().__init__(*args, **kwargs)

        # ensure a consistent GUI size
        self.grid_propagate(False)
        # implement stretchability
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # create a Text widget
        self.txt = Text(self)
        self.txt.grid(row=2, column=1, columnspan=3, sticky="nsew", padx=2, pady=2)

        # create a Scrollbar and associate it with txt
        scrollb = Scrollbar(self, command=self.txt.yview)
        scrollb.grid(row=2, column=4, sticky="nsew")
        self.txt["yscrollcommand"] = scrollb.set
        
    def insert(self, where, what):
        """Insert text."""
        self.txt.insert(where, what)

    def write(self, what):
        """Insert text at the end."""
        self.txt.insert(END, what)


class Edit(Frame):

    def __init__(self, parent, file):
        Frame.__init__(self, parent)
        self.parent = parent
        self.file = file
        self.initUI()

    def initUI(self):

        self.textPad = ScrolledText(self)
        self.textPad.grid(row=1, column=1, columnspan=2, rowspan=4, padx=5, sticky=E+W+S+N)

        abtn = Button(self, text="Save",command=self.save_command)
        abtn.grid(row=2, column=1)

        cbtn = Button(self, text="Close", command=self.onExit)
        cbtn.grid(row=2, column=2, pady=4)

    def onExit(self):
        resp = messagebox.askyesno("SCM-Helper: Yes / No?", "Save Config?", parent=self.parent)
        if resp:
            save_command()
        self.parent.destroy()

    def save_command(self):
        with open(self.file, FILE_WRITE) as file:
        # slice off the last character from get, as an extra return is added
            data = self.textPad.get('1.0', 'end-1c')
            file.write(data)
            file.close()
