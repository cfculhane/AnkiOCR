import logging
import re
from copy import deepcopy
from pathlib import Path
from typing import Dict, Sequence

import pytesseract
from PIL import Image
from anki.collection import Collection
from anki.notes import Note
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg
from tqdm import tqdm

PROJECT_DIR = Path(__file__).parent.parent
logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO)
logger = logging.getLogger(__name__)


class OCR:
    LANGUAGES = ["eng"]  # ch_sim, de, etc
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

    def __init__(self, col: Collection):
        self.col = col
        self.media_dir = col.media.dir()

    def get_images_from_note(self, note):
        pattern = r'(?:<img src=")(.*?)(?:"(?:>|\B))'
        images = {}
        for field_name, field_content in note.items():
            img_fnames = re.findall(pattern, field_content)
            for img_fname in img_fnames:
                images[Path(img_fname).stem] = {"path": Path(self.media_dir, img_fname),
                                                "field": field_name}
        return images

    @staticmethod
    def process_imgs(images: Dict):
        for img_name, img_data in images.items():
            logger.debug(f"Processing {img_data['path']} from field {img_data['field']}")
            if img_data["path"].suffix == ".svg":
                svg_draw = svg2rlg(str(img_data["path"].absolute()))
                renderPM.drawToFile(svg_draw, "temp.png", fmt="PNG")
                img = Image.open("temp.png")
            else:
                img = Image.open(img_data["path"])
            ocr_result = pytesseract.image_to_string(img)
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

    def add_ocr_model_to_db(self, ocr_model: Dict):
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
            self.add_ocr_model_to_db(ocr_model=ocr_model)
        field_mapping = {i: i for i in range(len(orig_model["flds"]))}
        card_mapping = {i: i for i in range(len(note.cards()))}
        self.col.models.change(orig_model, nids=[note.id], newModel=ocr_model, fmap=field_mapping, cmap=card_mapping)
        self.col.models.save()
        self.col.models.flush()
        return self.col.getNote(note_id)

    def ocr_process(self, note_ids: Sequence[int], overwrite_existing=False, save_every_n=50):
        logger.info(f"Processing {len(note_ids)} notes ...")
        # tqdm_out = TqdmToLogger(logger, level=logging.INFO)
        for i, note_id in tqdm(enumerate(note_ids), desc=f"Processing notes", total=len(note_ids)):
            note = self.col.getNote(note_id)
            if self.is_OCR_note(note) is False:
                note = self.convert_note_to_OCR(note_id)
            elif self.is_OCR_note(note) is True and overwrite_existing is False:
                logger.info(f"Note id {note_id} is already processd. Set overwrite_existing=True to force reprocessing")
                continue

            note_images = self.get_images_from_note(note)
            note_images = self.process_imgs(images=note_images)
            if len(note_images) > 0:
                self.add_imgdata_to_note(note=note, images=note_images)

            if i % save_every_n == 0:
                self.col.save()
            logger.debug(f"Added OCR data to note id {note_id}")

        self.col.save()

    def run_ocr_on_query(self, query: str):
        """ Main method for the ocr class. Runs OCR on a sequence of notes returned from a collection query.

        :param query: Query to collection, see https://docs.ankiweb.net/#/searching for more info.
        """
        note_ids = self.col.findNotes(query=query)
        self.col.modSchema(check=True)
        self.ocr_process(note_ids=note_ids, overwrite_existing=True)
        self.col.reset()
        self.col.close()
        logger.info("Databased saved and closed")


# %%
if __name__ == '__main__':
    # Not to be run inside Anki
    PROFILE_HOME = Path(r"C:\GitHub\anki\User 1")
    cpath = PROFILE_HOME / "collection.anki2"
    collection = Collection(str(cpath), log=True)  # Collection is locked from here on
    ocr = OCR(col=collection)
    QUERY = "tag:RG::MS::RG4.00_Lab"
    # QUERY = "tag:OCR"
    # QUERY = ""
    ocr.run_ocr_on_query(QUERY)
