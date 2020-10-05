@ECHO OFF
REM Builds the addon for release
echo Copying source code to dist folder ...
robocopy .\anki_ocr .\dist\anki_ocr /E /PURGE /XD "__pycache__" "logs" /XF *.pickle *.pyc *.sqlite
cd .\dist\anki_ocr
7z a "../anki_ocr.zip" .
ECHO Build complete!
pause
