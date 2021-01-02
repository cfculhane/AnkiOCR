import sys
from pathlib import Path

sys.path.append("_vendor")

from . import gui

gui.create_menu()

__version__ = "0.4.2"
TEST_DIR = Path(__file__).parent.parent / "tests"
TESTDATA_DIR = TEST_DIR / "testdata"
