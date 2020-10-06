import logging
from pathlib import Path

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FieldHTMLParser:
    def __init__(self):
        pass

    def parse_images(self, field_text):
        soup = BeautifulSoup(field_text, "html.parser")
        images = {}
        for img in soup.find_all("img"):
            fname = Path(img["src"]).stem
            images[fname] = img.attrs
        return images

    def insert_ocr_text(self, images, field_text):
        soup = BeautifulSoup(field_text, "html.parser")
        for img_name, img_data in images.items():
            html_tags = soup.find_all(name="img", attrs={"src": img_data["src"]})
            for html_tag in html_tags:
                html_tag.attrs["title"] = img_data["text"]
        return str(soup)

    def remove_ocr_text(self, images, field_text):
        soup = BeautifulSoup(field_text, "html.parser")
        for img_name, img_data in images.items():
            html_tags = soup.find_all(name="img", attrs={"src": img_data["src"]})
            for html_tag in html_tags:
                if html_tag.attrs.get("title") is not None:
                    del html_tag.attrs["title"]
        return str(soup)




if __name__ == '__main__':
    parser = FieldHTMLParser()
    p_field_text = 'This is some extra text with an image below<div><img src="tmp3zud1urq.png"><br></div>'
    p_images = parser.parse_images(p_field_text)
    for img in p_images.values():
        img["text"] = 'Lateral and Medial divisions\nTract\nLATERAL\n- Lateral corticospinal\n- Rubrospinal\nMEDIAL\n- Tecto-, vestibulospinal\n- Reticulospinal\n- Anterior corticospinal\nFunction\nFine control of distal musculature\nPrimary p/w for voluntary limb movements esp. precise\nmovements of hand and fingers\nBackup for corticospinal tract, movement velocity, learned\nmovements\nControl of axial and proximal musculature\nKeep head balanced on shoulders as the body navigates\nthrough space and head turns to stimuli\nModulate anti-gravity reflexes of the spinal cord; automatic\nposture and gait\nControl of trunk'
    modified_field = parser.insert_ocr_text(p_images, p_field_text)
    removed_field = parser.remove_ocr_text(p_images, p_field_text)

