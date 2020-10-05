import sys

sys.path.append("_vendor")
from .utils import path_to_tesseract

from . import gui

gui.create_menu()

__version__ = "0.2.2"
