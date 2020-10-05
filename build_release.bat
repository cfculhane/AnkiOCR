@ECHO OFF
REM Builds the addon for release
echo Copying source code to dist folder ...
robocopy .\anki_ocr .\dist\anki_ocr /E /PURGE /XD "__pycache__" "logs" /XF *.pickle *.pyc *.sqlite meta.json
cd .\dist\anki_ocr
del /f "..\anki_ocr.zip"
7z a "../anki_ocr.zip" .
cd ../..
ECHO Build complete!
pause
