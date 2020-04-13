"""Notify."""
import sys


def notify(msg):
    """Notify on STDERR."""
    sys.stderr.write(msg)
    sys.stderr.flush()


def interact(msg):
    """Get user input."""
    # Simple, but ready to add GUI!
    print(msg)
    return input()
