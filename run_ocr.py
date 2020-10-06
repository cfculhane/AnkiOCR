import logging
from pathlib import Path

from anki import Collection
from anki.rsbackend import DBError
from anki_ocr.ocr import SCRIPT_DIR, OCR

if __name__ == '__main__':
    logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=logging_format, level=logging.INFO)
    # Not to be run inside Anki
    PROFILE_HOME = Path(SCRIPT_DIR.parent, "tests/User 1")
    cpath = PROFILE_HOME / "collection.anki2"

    try:
        collection = Collection(str(cpath), log=True)  # Collection is locked from here on
    except DBError:
        pass

    ocr = OCR(col=collection)
    QUERY = "tag:RG::MS::RG4.00_Lab"
    QUERY = "tag:OCR"
    # QUERY = ""
    ocr.run_ocr_on_query(QUERY)
    # collection.close(save=True)
    note_ids_c = collection.findNotes(QUERY)
    example_note = collection.getNote(note_ids_c[0])
    # ocr.remove_ocr_on_notes(note_ids_c)
