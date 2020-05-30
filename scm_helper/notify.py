"""Notify."""
import sys

try:
    from tkinter import END, messagebox, simpledialog
except ImportError:
    pass  # ignore it, we'll be running command line only


WHERE = None

# Really horrid code, but a simple way of doing it.
# Can't import anything for this package either, otherwise an import loop.


def notify(msg):
    """Notify on STDERR."""
    # pylint: disable=global-statement
    global WHERE
    if WHERE:
        WHERE.insert(END, msg)
        WHERE.see(END)
    elif WHERE is None:
        sys.stderr.write(msg)
        sys.stderr.flush()
    # Where is False
    # Do nothing ==> quite mode.


def set_notify(where):
    """Where to report errors."""
    # pylint: disable=global-statement
    global WHERE
    WHERE = where


def interact(msg):
    """Get user input."""
    # pylint: disable=global-statement
    global WHERE
    if WHERE:
        prefix = "SCM-Helper: input needed"
        return simpledialog.askstring(prefix, msg, parent=WHERE.master)
    print(msg, end="")
    return input()


def interact_yesno(msg):
    """Get user input."""
    # pylint: disable=global-statement
    global WHERE
    if WHERE:
        msg += "?"
        return messagebox.askyesno("SCM-Helper: Yes / No?", msg, parent=WHERE.master)
    msg += " (y/n)?"
    print(msg, end="")

    resp = input()
    if resp == "y":
        return True
    return False
