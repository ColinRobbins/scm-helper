"""Notify."""
import sys

WHERE = None

# Really horrid code, but a simple way of doing it.
# Can't import anything for this package either, otherwise an import loop.


def notify(msg):
    """Notify on STDERR."""
    # pylint: disable=global-statement
    global WHERE
    if WHERE:
        WHERE.write(msg)
    elif WHERE is None:
        sys.stderr.write(msg)
        sys.stderr.flush()
    # Where is False
    # Do nothing ==> quite mode.


def set_notify(where):
    """Where to reprot errors."""
    # pylint: disable=global-statement
    global WHERE
    WHERE = where


def interact(msg):
    """Get user input."""
    # Simple, but ready to add GUI!
    print(msg, end="")
    return input()
