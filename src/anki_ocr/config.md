### AnkiOCR

Please note that the following settings do not sync and require a restart to apply:

- `batch_size` (int): Number of notes to process at once. Default `5`.
- `languages` (list): Languages in [ISO639-2 format](https://www.loc.gov/standards/iso639-2/php/code_list.php) for the
  OCR to recognise. Default `["eng"]`
- `num_threads`(int): Number of threads to use for OCR process. If `null`, will default to the number of cores available
  on the machine.
- `override_tesseract_exec` (boolean): If `true` , will allow the setting of the directory where the tesseract
  executable resides. Default `false`
- `overwrite_existing` (boolean): If true, will overwrite existing OCR field. If false, will skip. Default: `true`
- `tesseract_exec_path` (string): Path to the tesseract executable, only used if `override_tesseract_exec` is `true` .
  Default "" (empty string)
- `tesseract_install_valid` (boolean): Flag for valid tesseract installation. Do not modify!
- `text_output_location` (string): Where to put outputted text. "tooltip" is in a tooltip over the image "new_field" is
  in a new field. Default "tooltip"
- `use_batching` (bool): If true, use batching to increase processing speed. Disable if experiencing abnormally slow
  processing times. Default `true`
- `use_multithreading` (bool): If true, use multithreading to increase processing speed. Disable if experiencing
  abnormally slow processing times. Default `true`
- `preserve_interword_spaces` (bool): If true, detected inter-word spaces will be preserved, instead of being compressed
  to a single space character (default behavior). Default `false`
