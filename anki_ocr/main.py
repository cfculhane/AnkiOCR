import re
from pathlib import Path
from pprint import pprint

import easyocr as easyocr
import numpy as np
import torch
import torchvision
from PIL import Image
from tqdm import tqdm

from anki.storage import Collection

PROJECT_DIR = Path(__file__).parent.parent

# %%
LANGUAGES = ["en"]  # ch_sim, de, etc
if torch.cuda.is_available():
    print("Cuda available, yay!")

print("Loading model into memory..")
READER = easyocr.Reader(["en"])
print("Loading model complete")
IMG_SHORTEST_EDGE = 1600  # All images will be scaled to this size

# %%
IMG_DIR = PROJECT_DIR / "input_imgs"
text_blocks = []
transform = torchvision.transforms.Resize(size=IMG_SHORTEST_EDGE)
for img_path in tqdm(list(IMG_DIR.glob("*"))):
    print(f"Processing {img_path}")
    img_p = Image.open(img_path)
    img_p = transform(img_p)
    text_blocks.append(READER.readtext(image=np.array(img_p), detail=0, paragraph=True))
# https://github.com/JaidedAI/EasyOCR
pprint(text_blocks)

# %%

PROFILE_HOME = Path(r"C:\GitHub\anki\User 1")
OUTPUT_DIRECTORY = PROJECT_DIR / "output"
cpath = PROFILE_HOME / "collection.anki2"
col = Collection(str(cpath), log=True)  # Entry point to the API

# %%
test_note = col.getNote("1601546351025")
media_dir = col.media.dir()


# %%
def get_images_from_note(note):
    pattern = r'(?:<img src=")(.*?)(?:">)'
    images = {}
    for field_name, field_content in note.items():
        img_fnames = re.findall(pattern, field_content)
        for img_fname in img_fnames:
            images[Path(img_fname).stem] = {"path": Path(media_dir, img_fname),
                                            "field": field_name}
    return images


transform = torchvision.transforms.Resize(size=IMG_SHORTEST_EDGE)


def preprocess_img(img_pth: Path) -> np.ndarray:
    img = Image.open(img_pth)
    img = transform(img)
    return np.array(img)


def process_imgs(images):
    for img_name, img_data in tqdm(images.items()):
        print(f"Processing {img_data['path']} from field {img_data['field']}")
        img_arr = preprocess_img(img_data["path"])
        img_data["text"] = "\n".join(READER.readtext(image=img_arr, detail=0, paragraph=True))
    return images




note_images = get_images_from_note(test_note)
note_images = process_imgs(images=note_images)
# %%
def add_imgdata_to_note(note, images):
    for img in images.values():
        note["Extra"] += f"\n %%% OCR DATA : \n\n {img['field']}\n{img['text']} %%%"
    note.flush()
    return note

updated_note = add_imgdata_to_note(test_note, images=note_images)
#%%
col.save()
