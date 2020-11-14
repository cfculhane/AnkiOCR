from dataclasses import dataclass
from pathlib import Path
from typing import List

from anki import Collection
from anki.notes import Note
from .html_parser import FieldHTMLParser

VENDOR_DIR = Path(__file__).parent / "_vendor"
FIELD_PARSER = FieldHTMLParser()


class TqdmNullWrapper:
    def __init__(self, iterable, **kwargs):
        self.iterable = iterable

    def __iter__(self):
        for obj in self.iterable:
            yield obj

# TODO use https://github.com/pydanny/cached-property

@dataclass
class OCRImage:
    name: str  # E.g. Coronary_arteries
    src: str  # E.g coronary_arties.png
    text: str = None  # Where OCR'd text will be stored


@dataclass
class FieldImages:
    field_name: str  # Not unique, as a field can contain multiple images
    images: List['OCRImage'] = None


@dataclass
class NoteImages:
    note_id: int
    col: Collection

    @property
    def note(self) -> Note:
        return self.col.getNote(self.note_id)

    @property
    def field_images(self) -> List[FieldImages]:

        images = []
        for field_name, field_content in self.note.items():
            images.append(FieldImages(field_name, images=FIELD_PARSER.parse_images(field_content)))

        return images


@dataclass
class QueryImages:
    col: Collection
    query: str = ""

    @property
    def note_images(self) -> List[NoteImages]:
        return [NoteImages(note_id=nid, col=self.col) for nid in self.col.findNotes(query=self.query)]
