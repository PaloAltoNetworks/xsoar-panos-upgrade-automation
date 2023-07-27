#
# conftest.py
# Fixes the directory path to ensure you can run the tests from whereever.
import sys
from os.path import dirname as d
from os.path import abspath
root_dir = d(d(abspath(__file__)))
sys.path.append(root_dir)