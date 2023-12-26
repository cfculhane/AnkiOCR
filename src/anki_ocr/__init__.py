from pathlib import Path

from . import gui

gui.create_menu()

__version__ = "0.7.1"
TEST_DIR = Path(__file__).parent.parent.parent / "tests"
TESTDATA_DIR = TEST_DIR / "testdata"
