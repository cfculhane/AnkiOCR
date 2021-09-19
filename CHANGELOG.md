## 0.7.1 - 2021-09-19
- Removing Chinese, German, French and Spanish language data to reduce filesize
- Updating readme with link to language data

## 0.7.0 - 2021-09-19
- Updating vendorised pytesseract
- Updating mac tesseract dependencies
- Updated build script for tesseract for mac
- The above fixes #27, #28, #29

## 0.6.1 - 2021-09-17

- Attempting to fix error where image does not exist
- Improved exception display to end user if processing fails unexpectedly, adding debug info

## 0.6.0 - 2021-09-13

- Fixes [#26](https://github.com/cfculhane/AnkiOCR/issues/26), thanks @bwhurd for the bug report
- Other small fixes to support Anki 2.2.41 and beyond
- Drop support for Anki versions prior to 2.1.41, but it should still work.

## 0.5.3 - 2021-09-04

- Fix raising of KeyError when img src is not found, thanks @thiswillbeyourgithub for the fix!

## 0.5.2 - 2021-05-22

- Fix error on some Linux environments, see https://github.com/cfculhane/AnkiOCR/issues/20 , thanks to user
  thiswillbeyourgithub for the fix!

## 0.5.1 - 2021-05-02

- Hotfix to include accidentally gitignored tesseract mac libs

## 0.5.0 - 2021-05-02

- Added bundled tesseract for Mac, no longer any need to install it seperately
- Split out `tessdata` to its own folder, allowing easier installation of new languages
- Change in the way note ID's are processed, no longer limited to 1000 cards
- Fixed issue causing a crash in anki versions > 2.1.40
- Added some log text that will appear when invalid notes are encountered during a processing run

## 0.4.3 - 2021-01-22

- Hotfix for config.json syntax error

## 0.4.2 - 2021-01-19

- Add `num_threads` config option to allow manual setting of number of threads
- Add `use_batching` config option to allow disabling of batching for those for which this causes performance issues
- Added more unit tests to releasing new versions
- Fixed an issue where OCR text containing "::" would break clozes, now cleans duplicate colons in text

## 0.4.1 - 2021-01-01

- Reduced batch_size default to 5 to improve the progress bar updating frequency and feel of speed
- added total time readout to final message on completion
- added ability to cancel during processing

## 0.4.0 - 2020-12-31

- Major feature update, now is multithreaded for roughly a 10x speed improvement
- Complete refactor of code for readibility and maintability
- Addition of basic unit tests for OCR section of codebase
- Improved progress bar messaging

## 0.3.1 - 2020-10-11

- Config setting for `text_output_location` is now read properly when starting OCR class
- More detailed exception readout when exception occurs during processing

## 0.3.0 - 2020-10-06

- New method for storing the OCR text, now stores it in `title` attr of the img html tag
- Handle old versions of Anki not having different progressbar.update()

## 0.2.5 - 2020-10-06

- Add alternate import method for Collection due to API changes in Anki

## 0.2.4 - 2020-10-05

- Changed order of operations so that OCR is attempted before notes are modified to elimainate risk of database errors
- Updated path to tesseract executable for mac and linux

## 0.2.3 - 2020-10-05

- HOTFIX for tesseract cmd path on Mac

## 0.2.2 - 2020-10-05

- Removed the install file for Tesseract-OCR for windows, now that the binaries themselves are included.
- Updated the inital message the user sees to notify re: the database change message Anki will show.

## 0.2.1 - 2020-10-05

- HOTFIX for Fixing tesseract executable detection

## 0.2.0 - 2020-10-05

- Now packaged with windows binaries for Tesseract-OCR, no install neccesary!
- Added flag in config.json to indicate valid tesseract exec
- Updates to README to reflect above changes

## 0.1.0 - 2020-10-05

- Initial release
