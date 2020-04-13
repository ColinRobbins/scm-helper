"""Notify."""
import sys

WHERE = None

# Really horrid code, but a simple way of doing it.

def notify(msg):
    """Notify on STDERR."""
    global WHERE
    if WHERE:
        WHERE.write(msg)
    else:
        sys.stderr.write(msg)
        sys.stderr.flush()

def set_notify(where):
    """Where to reprot errors."""
    global WHERE
    WHERE = where
    
def interact(msg):
    """Get user input."""
    # Simple, but ready to add GUI!
    print(msg)
    return input()
