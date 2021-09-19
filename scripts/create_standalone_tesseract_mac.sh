#!/bin/sh

# From https://yui-spl2.medium.com/making-tesseract-portable-in-macos-with-runtime-linking-f25c8159727a

if ! command -v tesseract &> /dev/null
then
    brew install tesseract
fi

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

mkdir tesseract_standalone
cp -r /usr/local/Cellar/tesseract tesseract_standalone/
cp -r /usr/local/Cellar/leptonica tesseract_standalone/
cp -r /usr/local/Cellar/libpng tesseract_standalone/
cp -r /usr/local/Cellar/libtiff tesseract_standalone/
cp -r /usr/local/Cellar/webp tesseract_standalone/
cp -r /usr/local/Cellar/openjpeg tesseract_standalone/
cp -r /usr/local/Cellar/jpeg tesseract_standalone/
cp -r /usr/local/Cellar/giflib tesseract_standalone/
cp -r /usr/local/Cellar/little-cms2 tesseract_standalone/

GIFLIB_VERSION="5.2.1"
LEPTONICA_VERSION="1.81.1"
LIBPNG_VERSION="1.6.37"
LIBTIFF_VERSION="4.3.0"
LITTLE_CMS_VERSION="2.12"
OPENJPEG_VERSION="2.4.0"
TESSERACT_VERSION="4.1.1"
WEBP_VERSION="1.2.1"



cd "tesseract_standalone/tesseract/${TESSERACT_VERSION}/bin/"


# Modifying libtesseract.4.dylib
install_name_tool -change "/usr/local/Cellar/tesseract/${TESSERACT_VERSION}/lib/libtesseract.4.dylib" "@executable_path/../lib/libtesseract.4.dylib" tesseract
install_name_tool -change "/usr/local/opt/leptonica/lib/liblept.5.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib" "../../../tesseract/${TESSERACT_VERSION}/lib/libtesseract.4.dylib"

# Modifying tesseract
install_name_tool -change "/usr/local/opt/leptonica/lib/liblept.5.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib" tesseract

# Modifying liblept.5.dylib
install_name_tool -change "/usr/local/opt/libpng/lib/libpng16.16.dylib" "../../../libpng/${LIBPNG_VERSION}/lib/libpng16.16.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

install_name_tool -change "/usr/local/opt/jpeg/lib/libjpeg.9.dylib" "../../../jpeg/9d/lib/libjpeg.9.dylib" ."./../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

install_name_tool -change "/usr/local/opt/giflib/lib/libgif.7.dylib" "../../../giflib/${GIFLIB_VERSION}/lib/libgif.7.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"
install_name_tool -change "/usr/local/opt/giflib/lib/libgif.dylib" "../../../giflib/${GIFLIB_VERSION}/lib/libgif.dylib" ."./../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

install_name_tool -change "/usr/local/opt/libtiff/lib/libtiff.5.dylib" "../../../libtiff/${LIBTIFF_VERSION}/lib/libtiff.5.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

install_name_tool -change "/usr/local/opt/webp/lib/libwebp.7.dylib" "../../../webp/${WEBP_VERSION}/lib/libwebp.7.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"
install_name_tool -change "/usr/local/opt/webp/lib/libwebpmux.3.dylib" "../../../webp/${WEBP_VERSION}/lib/libwebpmux.3.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

install_name_tool -change "/usr/local/opt/openjpeg/lib/libopenjp2.7.dylib" "../../../openjpeg/${OPENJPEG_VERSION}/lib/libopenjp2.2.4.0.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

# Same as above but for liblept
install_name_tool -change "/usr/local/opt/libpng/lib/libpng16.16.dylib" "../../../libpng/${LIBPNG_VERSION}/lib/libpng16.16.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"

install_name_tool -change "/usr/local/opt/jpeg/lib/libjpeg.9.dylib" "../../../jpeg/9d/lib/libjpeg.9.dylib" ."./../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"

install_name_tool -change "/usr/local/opt/giflib/lib/libgif.7.dylib" "../../../giflib/${GIFLIB_VERSION}/lib/libgif.7.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"
install_name_tool -change "/usr/local/opt/giflib/lib/libgif.dylib" "../../../giflib/${GIFLIB_VERSION}/lib/libgif.dylib" ."./../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"

install_name_tool -change "/usr/local/opt/libtiff/lib/libtiff.5.dylib" "../../../libtiff/${LIBTIFF_VERSION}/lib/libtiff.5.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"

install_name_tool -change "/usr/local/opt/webp/lib/libwebp.7.dylib" "../../../webp/${WEBP_VERSION}/lib/libwebp.7.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"
install_name_tool -change "/usr/local/opt/webp/lib/libwebpmux.3.dylib" "../../../webp/${WEBP_VERSION}/lib/libwebpmux.3.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"

install_name_tool -change "/usr/local/opt/openjpeg/lib/libopenjp2.7.dylib" "../../../openjpeg/${OPENJPEG_VERSION}/lib/libopenjp2.2.4.0.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"


# Modifying libtiff
install_name_tool -change "/usr/local/opt/jpeg/lib/libjpeg.9.dylib" "../../../jpeg/9d/lib/libjpeg.9.dylib" "../../../libtiff/${LIBTIFF_VERSION}/lib/libtiff.5.dylib"
