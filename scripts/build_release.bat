@ECHO OFF
REM Builds the addon for release
echo Copying source code to dist folder ...
cd ..
robocopy .\anki_ocr .\dist\anki_ocr /E /PURGE /XD "__pycache__" "logs" /XF *.pickle *.pyc *.sqlite meta.json
cd .\dist\anki_ocr
IF EXIST "..\anki_ocr.ankiaddon" (
    del /f  "..\anki_ocr.ankiaddon"
)
7z a "../anki_ocr.zip" .
cd ..
REN "anki_ocr.zip" "anki_ocr.ankiaddon"
cd ..
ECHO Build complete!
pause
