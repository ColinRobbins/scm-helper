#!/usr/bin/env python3
"""SCM wrapper - command line."""
import sys
sys.path.append("scm_helper/")

from scm_helper import main


if __name__ == "__main__":
    main.cmd()
