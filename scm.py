#!/usr/bin/env python3
"""SCM wrapper."""
import sys

# Black directive
# fmt: off
sys.path.append("scm_helper/")
if sys.version_info < (3, 6):
    raise AssertionError

# pylint: disable=wrong-import-position
from scm_helper import main

if __name__ == "__main__":
    main.main()
