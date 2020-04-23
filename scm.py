#!/usr/bin/env python3
"""SCM wrapper."""
import sys

sys.path.append("scm_helper/")
assert sys.version_info >= (3, 7)

from scm_helper import main


if __name__ == "__main__":
    main.main()
