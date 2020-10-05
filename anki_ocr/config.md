### AnkiOCR

Please note that the following settings do not sync and require a restart to apply:

- `overwrite_existing` (boolean): If true, will overwrite existing OCR field. If false, will skip. Default: `true`
- `languages` (list): Languages in [ISO639-2 format](https://www.loc.gov/standards/iso639-2/php/code_list.php) for the OCR to recognise. Default `["eng"]`
- `tesseract_install_valid` (boolean): Flag for valid tesseract installation. Do not modify!
- `text_output_location` (string): Where to put outputted text. "tooltip" is in a tooltip over the image "new_field" is in a new field. Default "tooltip"
