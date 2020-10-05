import sys
sys.path.append("_vendor")
from ._vendor import pytesseract
from . import gui
gui.create_menu()

__version__ = "0.1.0"
