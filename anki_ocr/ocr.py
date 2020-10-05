import logging
import re
from copy import deepcopy
from pathlib import Path
from typing import Dict, Sequence, Optional, List

import anki
from anki.collection import Collection
from anki.notes import Note

try:
    from aqt import mw

    print("Running in anki")
    ANKI_ENV = True
except ModuleNotFoundError:
    print("Not running in anki")
    ANKI_ENV = False

if ANKI_ENV is False:
    ProgressManager = None
    import pytesseract
    from PIL import Image
    from reportlab.graphics import renderPM
    from svglib.svglib import svg2rlg
    from tqdm import tqdm

else:
    from aqt.progress import ProgressManager
    from ._vendor import pytesseract

    Image = None
    renderPM = None
    svg2rlg = None
    from .utils import tqdm_null_wrapper as tqdm

from .utils import path_to_tesseract

SCRIPT_DIR = Path(__file__).parent
logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO)
logger = logging.getLogger(__name__)


class OCR:

    def __init__(self, col: Collection, progress: Optional['ProgressManager'] = None,
                 languages: Optional[List[str]] = None):
        self.col = col
        self.media_dir = col.media.dir()
        self.progress = progress
        # ISO 639-2 Code, see https://www.loc.gov/standards/iso639-2/php/code_list.php
        self.languages = languages or ["eng"]

        CONFIG = mw.addonManager.getConfig(__name__)
        tesseract_cmd, platform_name = path_to_tesseract()
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def get_images_from_note(self, note):
        pattern = r'(?:<img src=")(.*?)(?:"(?:>|\B))'
        images = {}
        for field_name, field_content in note.items():
            img_fnames = re.findall(pattern, field_content)
            for img_fname in img_fnames:
                images[Path(img_fname).stem] = {"path": Path(self.media_dir, img_fname),
                                                "field": field_name}
        return images

    def process_imgs(self, images: Dict):
        for img_name, img_data in images.items():
            logger.debug(f"Processing {img_data['path']} from field {img_data['field']}")
            if img_data["path"].suffix == ".svg":
                if ANKI_ENV is True:
                    # TODO attempt to vendorize reportlab, svglib
                    img_data["text"] = ""
                    continue
                else:
                    svg_draw = svg2rlg(str(img_data["path"].absolute()))
                    renderPM.drawToFile(svg_draw, "temp.png", fmt="PNG")
                    img = Image.open("temp.png")
            else:
                # img = Image.open(img_data["path"])
                img = str(img_data["path"].absolute())

            ocr_result = pytesseract.image_to_string(img, lang="+".join(self.languages))
            ocr_result = "\n".join([line.strip() for line in ocr_result.splitlines() if line.strip() != ""])
            img_data["text"] = ocr_result
        return images

    @staticmethod
    def add_imgdata_to_note(note: Note, images: Dict):
        note["OCR"] = ""
        for img_name, img_data in images.items():
            if img_data['text'] != "":
                note["OCR"] += f"Image: {img_name}\n{'-' * 20}\n{img_data['text']}".replace('\n', '<br/>')
        note.flush()
        return note

    @staticmethod
    def is_OCR_note(note: Note) -> bool:
        return note.model()["name"].endswith("_OCR")

    @staticmethod
    def create_OCR_notemodel(src_model: Dict):
        assert src_model["name"].endswith("_OCR") is False
        ocr_model = deepcopy(src_model)
        ocr_model["name"] += "_OCR"
        # if "OCR" not in ocr_model["flds"].
        ocr_model["flds"].append(
            {'name': 'OCR', 'ord': len(ocr_model["flds"]), 'sticky': False, 'rtl': False, 'font': 'Arial', 'size': 12,
             'media': []})
        ocr_model["tmpls"][0]["name"] += "_OCR"
        return ocr_model

    @staticmethod
    def create_orig_notemodel(src_model: Dict):
        assert src_model["name"].endswith("_OCR") is True
        orig_model = deepcopy(src_model)
        orig_model["name"] = orig_model["name"].replace("_OCR", "")
        orig_model["flds"] = [fld for fld in orig_model["flds"] if fld["name"] != "OCR"]
        orig_model["tmpls"][0]["name"] = orig_model["tmpls"][0]["name"].replace("_OCR", "")
        return orig_model

    def add_model_to_db(self, ocr_model: Dict):
        self.col.models.add(ocr_model)
        self.col.models.save()
        self.col.models.flush()

    def convert_note_to_OCR(self, note_id: int) -> Note:
        # TODO Change this to process multiple note IDs at once?
        note = self.col.getNote(note_id)
        orig_model = note.model()
        if self.is_OCR_note(note):
            logger.info("Note is already an OCR-type, no need to convert")
            return note

        ocr_model_name = orig_model["name"] + "_OCR"
        if ocr_model_name in self.col.models.allNames():
            logger.debug(f"Model already exists, using '{ocr_model_name}'")
            ocr_model = self.col.models.byName(ocr_model_name)
        else:
            logger.info(f"Creating new model named '{ocr_model_name}'")
            ocr_model = self.create_OCR_notemodel(note.model())
            self.add_model_to_db(ocr_model=ocr_model)

        field_mapping = {i: i for i in range(len(orig_model["flds"]))}
        card_mapping = {i: i for i in range(len(note.cards()))}
        self.col.models.change(orig_model, nids=[note.id], newModel=ocr_model, fmap=field_mapping, cmap=card_mapping)
        self.col.models.save(m=ocr_model)
        self.col.models.flush()
        return self.col.getNote(note_id)

    def undo_convert_note_to_OCR(self, note_id: int) -> Note:
        # TODO Change this to process multiple note IDs at once?
        note = self.col.getNote(note_id)
        ocr_model = note.model()
        if self.is_OCR_note(note) is False:
            logger.info("Note is already NOT an OCR-type, no need to undo the conversion")
            return note
        ocr_model_name = ocr_model["name"]
        orig_model_name = ocr_model_name.replace("_OCR", "")

        if orig_model_name in self.col.models.allNames():
            logger.debug(f"Original Model already exists, using '{orig_model_name}'")
            orig_model = self.col.models.byName(orig_model_name)
        else:
            logger.info(f"Creating new (original) model named '{orig_model_name}'")
            orig_model = self.create_orig_notemodel(note.model())
            self.add_model_to_db(ocr_model=orig_model)

        field_mapping = {i: i for i in range(len(orig_model["flds"]))}
        card_mapping = {i: i for i in range(len(note.cards()))}
        self.col.models.change(ocr_model, nids=[note.id], newModel=orig_model, fmap=field_mapping, cmap=card_mapping)
        self.col.models.save(m=orig_model)
        self.col.models.flush()
        return self.col.getNote(note_id)

    def ocr_process(self, note_ids: Sequence[int], overwrite_existing, save_every_n=50):
        logger.info(f"Processing {len(note_ids)} notes ...")
        # tqdm_out = TqdmToLogger(logger, level=logging.INFO)
        for i, note_id in tqdm(enumerate(note_ids), desc=f"Processing notes", total=len(note_ids)):
            if self.progress is not None:
                self.progress.update(value=i, max=len(note_ids))
            note = self.col.getNote(note_id)
            if self.is_OCR_note(note) is True and overwrite_existing is False:
                logger.info(f"Note id {note_id} is already processd. Set overwrite_existing=True to force reprocessing")
                continue

            # Run this first, so that tesseract install is implicitly checked before modifying notes!
            note_images = self.get_images_from_note(note)
            note_images = self.process_imgs(images=note_images)

            if self.is_OCR_note(note) is False:
                note = self.convert_note_to_OCR(note_id)

            if len(note_images) > 0:
                self.add_imgdata_to_note(note=note, images=note_images)

            if i % save_every_n == 0:
                self.col.save()
            logger.debug(f"Added OCR data to note id {note_id}")

        self.col.save()

    def run_ocr_on_query(self, query: str, overwrite_existing=True):
        """ Main method for the ocr class. Runs OCR on a sequence of notes returned from a collection query.

        :param query: Query to collection, see https://docs.ankiweb.net/#/searching for more info.
        """
        note_ids = self.col.findNotes(query=query)
        # self.col.modSchema(check=True)
        self.ocr_process(note_ids=note_ids, overwrite_existing=overwrite_existing)
        self.col.reset()
        logger.info("Databased saved and closed")

    def run_ocr_on_notes(self, note_ids: List[int], overwrite_existing=True):
        """ Main method for the ocr class. Runs OCR on a sequence of notes returned from a collection query.

        :param note_ids: List of note ids
        """
        # self.col.modSchema(check=True)
        self.ocr_process(note_ids=note_ids, overwrite_existing=overwrite_existing)
        self.col.reset()
        logger.info("Databased saved and closed")

    def remove_ocr_on_notes(self, note_ids: List[int]):
        """ Removes the OCR field on a sequence of notes returned from a collection query.

        :param note_ids: List of note ids
        """
        # self.col.modSchema(check=True)
        for note_id in note_ids:
            self.undo_convert_note_to_OCR(note_id=note_id)
        self.col.reset()
        logger.info("Databased saved and closed")


# %%
if __name__ == '__main__':
    # Not to be run inside Anki
    PROFILE_HOME = Path(r"C:\GitHub\anki\User 1")
    cpath = PROFILE_HOME / "collection.anki2"
    try:
        collection = Collection(str(cpath), log=True)  # Collection is locked from here on
    except anki.rsbackend.DBError:
        print("Anki collection already open, attempting to continue")

    ocr = OCR(col=collection)
    QUERY = "tag:RG::MS::RG4.00_Lab"
    QUERY = "tag:OCR"
    # QUERY = ""
    ocr.run_ocr_on_query(QUERY)
    # collection.close(save=True)
    # note_ids_c = collection.findNotes(QUERY)
    # ocr.remove_ocr_on_notes(note_ids_c)
