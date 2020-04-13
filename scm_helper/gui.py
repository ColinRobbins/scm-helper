from tkinter import Tk, Label, Button, Scrollbar, Entry, OptionMenu, Radiobutton, IntVar, Toplevel, Text, END, Frame, StringVar, messagebox, W
from issue import issue
from api import API
from issue import IssueHandler, REPORTS
import sys
from notify import set_notify
import threading

class ScmGui(Tk):
    
    def __init__(self, master):
        self.master = master
        self.result_window = None
        self.result_text = None
        self.issues = None
        self.scm = None
        self.gotdata = None
        self.thread = None

        master.title("SCM Helper")

        self.label = Label(master, text="This is our first GUI!")
        
        # Row 1
        myrow = 1
        label = Label(master, text = "Password: ")
        label.grid(row=myrow, column=1, sticky = W, pady = 2)
        self.__password = StringVar()
        self.__password.set("")
        password = Entry(master, show="*", textvariable=self.__password, width=15)
        password.grid(row=myrow, column=2, sticky = W)
        
        # Row 2
        myrow = 2
        self.report_option = StringVar()
        self.report_option.set("--error")
        
        label = Label(master, text = "Report Format: ")
        label.grid(row=myrow, column=1, sticky = W, pady = 2)

        radio = Radiobutton(master, text="By error", variable=self.report_option, value="--error")
        radio.grid(row=myrow, column=2, sticky = W)

        radio = Radiobutton(master, text="By member", variable=self.report_option, value="--member")
        radio.grid(row=myrow, column=3, sticky = W)
        
        # Row 3
        myrow = 3
        self.src_option = StringVar()
        self.src_option.set("--scm")
        
        label = Label(master, text = "Data source: ")
        label.grid(row=myrow, column=1, sticky = W, pady = 2)

        radio = Radiobutton(master, text="SCM", variable=self.src_option, value="--scm")
        radio.grid(row=myrow, column=2, sticky = W)

        radio = Radiobutton(master, text="Archive", variable=self.src_option, value="--archive")
        radio.grid(row=myrow, column=3, sticky = W)

        self.archive = StringVar()
        self.archive.set("")
        archive = Entry(master, textvariable=self.archive, width=15)
        archive.grid(row=myrow, column=4, sticky = W)
        
        # Row 4
        myrow = 4

        self.reports = StringVar()
        self.reports.set("All")
        
        label = Label(master, text = "Reports required: ")
        label.grid(row=myrow, column=1, sticky = W, pady = 2)
        
        all_reports = ["all"] + REPORTS

        self.reports_menu = OptionMenu(master, self.reports, *all_reports)
        self.reports_menu.grid(row=myrow, column=2, sticky = W)
        
        # Row 5
        myrow = 5

        button = Button(master, text="Analyse", command=self.report_window)
        button.grid(row=myrow, column=1, pady = 2)

        button = Button(master, text="Backup", command=self.backup_window)
        button.grid(row=myrow, column=2)
        
        button = Button(master, text="Clear Data", command=self.clear_data)
        button.grid(row=myrow, column=3)
        
        button = Button(master, text="Close", command=master.quit)
        button.grid(row=myrow, column=4)
        
        # Row 6
        myrow = 6
        self.notify = TextScrollCombo(master)
        self.notify.config(width=500, height=200)
        self.notify.grid(row=myrow, column=1, columnspan = 4, pady = 2 )
        set_notify(self.notify)
      
    def scm_init(self):
        """Initalise SCM."""
        password = self.__password.get()
        if password:
            self.issues = IssueHandler()
            self.scm = API(self.issues)
            if self.scm.initialise(password) is False:
                del self.scm
                del self.issues
                self.scm = None
                self.issues = None
                messagebox.showerror("Error", "Cannot initialise SCM (wrong password?)")
                return False
                
            return True
            
        messagebox.showerror("Password", "Please give a password!")
        return False
            

    def report_window(self):
        """Window for reports."""
        if self.scm is None:
            if self.scm_init() is False:
                return
            
        if self.thread:
            return      # already runnning
        
        self.thread = AnalysisThread(self).start()

    def backup_window(self):
        """Window for reports."""
        if self.scm is None:
            if self.scm_init() is False:
                return
            
        if self.scm.backup_data():
            output = self.scm.print_summary()
            self.notify.insert(END, output)
            return
            
        messagebox.showerror("Backup", "Backup failed")

    def clear_data(self):
        """Prepare to rerun."""
        if self.scm:
            self.scm.delete()
        self.gotdata = None
        messagebox.showerror("Clear Data", "Data cleared")

class AnalysisThread(threading.Thread):
    def __init__(self, gui):
        threading.Thread.__init__(self)
        self.gui = gui
        self.scm = gui.scm
        
    def run(self):
        """Run analyser."""
        
        archive = self.gui.src_option.get()
        print (archive)
        if archive == "--archive":
            if self.scm.decrypt(self.gui.archive.get()) is False:
                messagebox.showerror("Error", f"Cannot read from archive: {archive}")
        else:
            if self.scm.get_data(False) is False:
                messagebox.showerror("Analsyis", "Failed to read data")
                return
        
        if self.scm.linkage() is False:
            messagebox.showerror("Analsyis", "Error processing data")
            return

        self.scm.analyse()
        self.gotdata = archive

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
        
        return
    
    
class TextScrollCombo(Frame):
    """Text scrolling combo."""
    # Credit: https://stackoverflow.com/questions/13832720/how-to-attach-a-scrollbar-to-a-text-widget
    def __init__(self, *args, **kwargs):

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
        scrollb.grid(row=0, column=1, sticky='nsew')
        self.txt['yscrollcommand'] = scrollb.set
        
    def insert(self, where, what):
        self.txt.insert(where, what)
        
    def write(self, what):
        self.txt.insert(END, what)
        
    def flush(self):
        # not sure we need to do anything.
        pass
