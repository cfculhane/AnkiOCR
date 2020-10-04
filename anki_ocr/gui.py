# import the main window object (mw) from aqt
from anki.hooks import addHook
from aqt import mw
# import all of the Qt GUI library
from aqt.browser import Browser
from aqt.qt import QAction
# import the "show info" tool from utils.py
from aqt.utils import showInfo


# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.

def onAnkiOCR(browser: Browser):
    selected_nids = browser.selectedNotes()
    showInfo(str(selected_nids))
    if len(selected_nids) == 0:
        showInfo("No cards selected.")
        return

    mw.progress.start(immediate=True)
    showInfo("would call OCR here")
    mw.progress.finish()
    browser.model.reset()
    mw.requireReset()
    showInfo(f"Processed OCR for X cards")


# def setupMenu(browser: Browser):
#     menu = browser.form.menuEdit
#     menu.addSeparator()
#     a = menu.addAction('AnkiOCR')
#     a.triggered.connect(lambda b=browser: onAdvCopyEdit(b))
#
#
# addHook("browser.setupMenus", setupMenu)
def on_menu_setup(browser: Browser):
    act = QAction(browser)
    act.setText("Run AnkiOCR")
    mn = browser.form.menu_Cards
    mn.addSeparator()
    mn.addAction(act)
    act.triggered.connect(lambda b=browser: onAnkiOCR(browser))


def create_menu():
    addHook("browser.setupMenus", on_menu_setup)
