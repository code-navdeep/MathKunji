"""
Ensures the project root is importable (so `import core...` / `import utils...`
work from anywhere pytest is invoked) without needing a package install step.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
