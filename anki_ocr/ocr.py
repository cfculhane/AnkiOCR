import logging
import platform
import sys
from copy import deepcopy
from pathlib import Path
from typing import Dict, Sequence, Optional, List

try:
    from anki.collection import Collection
except ImportError:  # Older anki versions
    from anki.storage import Collection

from anki.notes import Note

if "python" in Path(sys.executable).stem:
    print("Not running in anki")
    ANKI_ENV = False
else:  # anki.exe or equivalent
    ANKI_ENV = True
    print("Running in anki")

SCRIPT_DIR = Path(__file__).parent
DEPS_DIR = SCRIPT_DIR / "deps"

if ANKI_ENV is False:
    sys.path.append(SCRIPT_DIR)
    ProgressManager = None
    import pytesseract
    from PIL import Image
    from reportlab.graphics import renderPM
    from svglib.svglib import svg2rlg
    from tqdm import tqdm
    from .html_parser import FieldHTMLParser

else:
    from aqt.progress import ProgressManager
    from ._vendor import pytesseract

    Image = None
    renderPM = None
    svg2rlg = None
    from .utils import tqdm_null_wrapper as tqdm
    from .html_parser import FieldHTMLParser

logger = logging.getLogger(__name__)
FIELD_PARSER = FieldHTMLParser()


class OCR:

    def __init__(self, col: Collection, progress: Optional['ProgressManager'] = None,
                 languages: Optional[List[str]] = None, text_output_location="tooltip"):
        self.col = col
        self.media_dir = col.media.dir()
        self.progress = progress
        # ISO 639-2 Code, see https://www.loc.gov/standards/iso639-2/php/code_list.php
        self.languages = languages or ["eng"]

        tesseract_cmd, platform_name = self.path_to_tesseract()
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        assert text_output_location in ["tooltip", "new_field"]
        self.text_output_location = text_output_location

    @staticmethod
    def get_images_from_note(note: Note):
        images = {}
        for field_name, field_content in note.items():
            images[field_name] = FIELD_PARSER.parse_images(field_content)
        return images

    def process_imgs(self, images: Dict):
        for field_name, field_images in images.items():
            for img_name, img_data in field_images.items():
                logger.debug(f"Processing {img_name} from field {field_name}")
                img_path = Path(self.media_dir, img_data["src"])
                if img_path.suffix == ".svg":
                    if ANKI_ENV is True:
                        # TODO attempt to vendorize reportlab, svglib
                        img_data["text"] = ""
                        continue
                    else:
                        svg_draw = svg2rlg(str(img_path.absolute()))
                        renderPM.drawToFile(svg_draw, "temp.png", fmt="PNG")
                        img = Image.open("temp.png")
                else:
                    # img = Image.open(img_path)
                    img = str(img_path.absolute())

                ocr_result = pytesseract.image_to_string(img, lang="+".join(self.languages))
                ocr_result = "\n".join([line.strip() for line in ocr_result.splitlines() if line.strip() != ""])
                img_data["text"] = ocr_result
        return images

    @staticmethod
    def add_imgdata_to_note(note: Note, images: Dict, method="tooltip"):
        if method == "tooltip":
            for field_name, field_images in images.items():
                note[field_name] = FIELD_PARSER.insert_ocr_text(images=field_images, field_text=note[field_name])
        elif method == "new_field":
            note["OCR"] = ""
            for field_name, field_images in images.items():
                for img_name, img_data in field_images.items():
                    if img_data['text'] != "":
                        note["OCR"] += f"Image: {img_name}\n{'-' * 20}\n{img_data['text']}".replace('\n', '<br/>')
        else:
            raise ValueError(f"method {method} not valid. Only 'new_field' and 'tooltip' (default) are allowed.")
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
        images = self.get_images_from_note(note)
        for field_name, field_text in note.items():
            note[field_name] = FIELD_PARSER.remove_ocr_text(images[field_name], field_text)
        note.flush()

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
                try:
                    self.progress.update(value=i, max=len(note_ids))
                except TypeError:  # old version of Qt/Anki
                    pass

            note = self.col.getNote(note_id)
            if self.is_OCR_note(note) is True and overwrite_existing is False:
                logger.info(f"Note id {note_id} is already processd. Set overwrite_existing=True to force reprocessing")
                continue

            # Run this first, so that tesseract install is implicitly checked before modifying notes!
            note_images = self.get_images_from_note(note)
            note_images = self.process_imgs(images=note_images)

            if self.is_OCR_note(note) is False and self.text_output_location == "new_field":
                note = self.convert_note_to_OCR(note_id)

            if len(note_images) > 0:
                self.add_imgdata_to_note(note=note, images=note_images, method=self.text_output_location)

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
        logger.info("Databased saved")

    def run_ocr_on_notes(self, note_ids: List[int], overwrite_existing=True):
        """ Main method for the ocr class. Runs OCR on a sequence of notes returned from a collection query.

        :param note_ids: List of note ids
        """
        # self.col.modSchema(check=True)
        self.ocr_process(note_ids=note_ids, overwrite_existing=overwrite_existing)
        self.col.reset()
        logger.info("Databased saved")

    def remove_ocr_on_notes(self, note_ids: List[int]):
        """ Removes the OCR field on a sequence of notes returned from a collection query.

        :param note_ids: List of note ids
        """
        # self.col.modSchema(check=True)
        for note_id in note_ids:
            self.undo_convert_note_to_OCR(note_id=note_id)
        self.col.reset()
        logger.info("Databased saved")

    @staticmethod
    def path_to_tesseract():
        exec_data = {"Windows": str(Path(DEPS_DIR, "win", "tesseract", "tesseract.exe")),
                     "Darwin": "/usr/local/bin/tesseract",
                     "Linux": "/usr/local/bin/tesseract"}

        platform_name = platform.system()  # E.g. 'Windows'
        return exec_data[platform_name], platform_name
