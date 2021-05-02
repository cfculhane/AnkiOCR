import logging
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from anki import Collection
from anki.notes import Note
from bs4 import BeautifulSoup

VENDOR_DIR = Path(__file__).parent / "_vendor"
logger = logging.getLogger("anki_ocr")


# TODO potentially use https://github.com/pydanny/cached-property ?


@dataclass
class OCRImage:
    name: str  # E.g. Coronary_arteries
    src: str  # E.g coronary_arties.png
    note_id: int
    field_name: str
    media_dir: str = None  # media dir of collection
    text: str = None  # Where OCR'd text will be stored

    @property
    def img_pth(self) -> str:
        return str(Path(self.media_dir, self.src).absolute())


@dataclass
class OCRField:
    field_name: str  # Should be unique for the note_id, as a field can contain multiple images
    field_text: str
    media_dir: str
    note_id: int
    images: List[OCRImage] = None
    allowed_img_formats = [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".jfif", ".pnm"]

    def __post_init__(self):
        self.images = self.parse_images()

    def parse_images(self) -> List[OCRImage]:
        soup = BeautifulSoup(self.field_text, "html.parser")
        images = []
        for img in soup.find_all("img"):
            img_pth = Path(img["src"])
            full_pth = Path(self.media_dir, img_pth)
            try:
                if full_pth.exists() is False:
                    logger.warning(f"For note id {self.note_id}, image path {img_pth} does not exist in media dir")
                    continue
            except OSError:
                logger.warning(f"For note id {self.note_id}, image path {img_pth} is invalid")
                continue

            if img_pth.suffix in self.allowed_img_formats:

                images.append(OCRImage(name=img_pth.stem, src=img.attrs["src"],
                                       media_dir=self.media_dir, note_id=self.note_id,
                                       field_name=self.field_name))
            else:
                logger.debug(f"For note id {self.note_id}, ignoring unsupported image: {img_pth}")

        return images

    def insert_ocr_text(self):
        soup = BeautifulSoup(self.field_text, "html.parser")
        for ocr_img in self.images:
            html_tags = soup.find_all(name="img", attrs={"src": ocr_img.src})
            for html_tag in html_tags:
                html_tag.attrs["title"] = ocr_img.text

        self.field_text = str(soup)

    def remove_ocr_text(self):
        soup = BeautifulSoup(self.field_text, "html.parser")
        for ocr_image in self.images:
            html_tags = soup.find_all(name="img", attrs={"src": ocr_image.src})
            for html_tag in html_tags:
                if html_tag.attrs.get("title") is not None:
                    del html_tag.attrs["title"]
            del ocr_image.text
        self.field_text = str(soup)


@dataclass
class OCRNote:
    note_id: int
    col: Collection
    field_images: List[OCRField] = None

    @property
    def note(self) -> Note:
        return self.col.getNote(self.note_id)

    def __post_init__(self):
        self.field_images = self._get_field_images()

    def _get_field_images(self) -> List[OCRField]:
        images = []
        for field_name, field_text in self.note.items():
            images.append(OCRField(field_name=field_name, field_text=field_text,
                                   media_dir=self.col.media.dir(), note_id=self.note_id))

        return images

    @property
    def has_OCR_field(self) -> bool:
        return self.note.model()["name"].endswith("_OCR")

    def convert_note_to_OCR(self) -> None:
        # TODO Change this to process multiple note IDs at once?
        orig_model = self.note.model()
        if self.has_OCR_field:
            logger.info("Note is already an OCR-type, no need to convert")
            return

        ocr_model_name = orig_model["name"] + "_OCR"
        if ocr_model_name in self.col.models.allNames():
            logger.debug(f"Model already exists, using '{ocr_model_name}'")
            ocr_model = self.col.models.byName(ocr_model_name)
        else:
            logger.info(f"Creating new model named '{ocr_model_name}'")
            ocr_model = self.create_OCR_notemodel(orig_model)
            self.add_model_to_db(ocr_model=ocr_model)

        field_mapping = {i: i for i in range(len(orig_model["flds"]))}
        card_mapping = {i: i for i in range(len(self.note.cards()))}
        self.col.models.change(orig_model, nids=[self.note_id], newModel=ocr_model, fmap=field_mapping,
                               cmap=card_mapping)
        self.col.models.save(m=ocr_model)
        self.col.models.flush()

    def remove_OCR_text(self):
        note = self.note
        if self.has_OCR_field:
            print("Removing OCR Field from note")
            ocr_model = note.model()
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
            self.col.models.change(ocr_model, nids=[note.id], newModel=orig_model, fmap=field_mapping,
                                   cmap=card_mapping)
            self.col.models.save(m=orig_model)
            self.col.models.flush()
            note = self.note
            note.flush()
            self.field_images = self._get_field_images()

        for field_img in self.field_images:
            print("Removing OCR text from title attr")
            field_img.remove_ocr_text()
            note[field_img.field_name] = field_img.field_text

        note.flush()

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

    def add_imgdata_to_note(self, method="tooltip"):
        note = self.note
        if method == "tooltip":
            for field_img in self.field_images:
                field_img.insert_ocr_text()
                note[field_img.field_name] = field_img.field_text

        elif method == "new_field":
            if self.has_OCR_field is False:
                self.convert_note_to_OCR()
                note = self.note
            note["OCR"] = ""
            for field_img in self.field_images:
                for ocr_img in field_img.images:
                    if ocr_img.text != "":
                        note["OCR"] += f"Image: {ocr_img.name}\n{'-' * 20}\n{ocr_img.text}".replace('\n', '<br/>')
        else:
            raise ValueError(f"method {method} not valid. Only 'new_field' and 'tooltip' (default) are allowed.")
        note.flush()
        self.col.save()


@dataclass
class NotesQuery:
    """ Represents a collection of Notes from a query of the Collection db"""
    col: Collection
    query: str = ""
    notes: List[OCRNote] = None
    notes_to_process: List[OCRNote] = None

    def __post_init__(self):
        self.notes = [OCRNote(note_id=nid, col=self.col) for nid in self.col.findNotes(query=self.query)]

    def __len__(self):
        return len(self.notes)

    def __iter__(self):
        return self.notes.__iter__()
