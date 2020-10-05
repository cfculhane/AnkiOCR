# import the main window object (mw) from aqt
from pathlib import Path

from anki.hooks import addHook
from aqt import mw
from aqt.browser import Browser, QMenu
from aqt.qt import QAction
from aqt.utils import showInfo, askUser, showCritical

from ._vendor import pytesseract
from .ocr import OCR
from .utils import path_to_tesseract

# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
CONFIG = mw.addonManager.getConfig(__name__)
SCRIPT_DIR = Path(__file__).parent


def on_run_ocr(browser: Browser):
    try:
        tesseract_pth = check_tesseract_install()
    except pytesseract.TesseractNotFoundError:
        return None

    selected_nids = browser.selectedNotes()
    num_notes = len(selected_nids)
    if num_notes == 0:
        showInfo("No cards selected.")
        return
    elif askUser(f"Are you sure you wish to run OCR processing on {num_notes} notes?") is False:
        return

    progress = mw.progress
    ocr = OCR(col=mw.col, progress=progress, languages=CONFIG["languages"], tesseract_pth=tesseract_pth)
    progress.start(immediate=True, min=0, max=num_notes)
    ocr.run_ocr_on_notes(note_ids=selected_nids,
                         overwrite_existing=CONFIG["overwrite_existing"])
    progress.finish()
    browser.model.reset()
    mw.requireReset()
    showInfo(f"Processed OCR for {num_notes} cards")


def on_rm_ocr_fields(browser: Browser):
    try:
        tesseract_pth = check_tesseract_install()
    except pytesseract.TesseractNotFoundError:
        return None

    selected_nids = browser.selectedNotes()
    num_notes = len(selected_nids)
    if num_notes == 0:
        showInfo("No cards selected.")
        return
    elif askUser(f"Are you sure you wish to remove the OCR field from {num_notes} notes?") is False:
        return

    progress = mw.progress
    progress.start(immediate=True)
    ocr = OCR(col=mw.col, progress=progress, languages=CONFIG["languages"], tesseract_pth=tesseract_pth)
    ocr.remove_ocr_on_notes(note_ids=selected_nids)
    mw.progress.finish()
    browser.model.reset()
    mw.requireReset()
    showInfo(f"Removed the OCR field from {num_notes} cards")


def on_menu_setup(browser: Browser):
    anki_ocr_menu = QMenu(("AnkiOCR"), browser)

    act_run_ocr = QAction(browser, text="Run AnkiOCR on selected notes")
    act_run_ocr.triggered.connect(lambda b=browser: on_run_ocr(browser))
    anki_ocr_menu.addAction(act_run_ocr)

    act_rm_ocr_fields = QAction(browser, text="Remove OCR field from selected notes")
    act_rm_ocr_fields.triggered.connect(lambda b=browser: on_rm_ocr_fields(browser))
    anki_ocr_menu.addAction(act_rm_ocr_fields)

    browser_cards_menu = browser.form.menu_Cards
    browser_cards_menu.addSeparator()
    browser_cards_menu.addMenu(anki_ocr_menu)


def check_tesseract_install():
    tesseract_cmd, platform_name = path_to_tesseract()
    if platform_name == "Windows":
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    if CONFIG.get("tesseract_install_valid") is not True:
        try:
            test_txt = pytesseract.image_to_string(str(Path(SCRIPT_DIR, "example.png")))
            showInfo(
                f"Note that because this addon changes the note template, you will see a warning about changing the database and uploading to AnkiWeb. \n"
                f"This is normal, and will be shown each time you modify a note template.\n"
                f"Successfully checked for Tesseract on platform '{platform_name}\n"
                f"This message will be only be shown once.")
            CONFIG["tesseract_install_valid"] = True
            mw.addonManager.writeConfig(__name__, CONFIG)
            return pytesseract.pytesseract.tesseract_cmd

        except pytesseract.TesseractNotFoundError:

            CONFIG["tesseract_install_valid"] = False
            mw.addonManager.writeConfig(__name__, CONFIG)
            showCritical(text=f"Could not find a valid Tesseract-OCR installation. \n"
                              f"Please visit the addon page in at https://ankiweb.net/shared/info/450181164 for"
                              f" install instructions")
            raise pytesseract.TesseractNotFoundError()
    else:
        return pytesseract.pytesseract.tesseract_cmd


def create_menu():
    addHook("browser.setupMenus", on_menu_setup)
