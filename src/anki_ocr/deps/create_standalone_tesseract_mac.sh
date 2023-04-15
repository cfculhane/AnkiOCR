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

sudo rm -rf ./mac
mkdir mac
cp -r /usr/local/Cellar/tesseract mac/
cp -r /usr/local/Cellar/leptonica mac/
cp -r /usr/local/Cellar/libpng mac/
cp -r /usr/local/Cellar/libtiff mac/
cp -r /usr/local/Cellar/webp mac/
cp -r /usr/local/Cellar/openjpeg mac/
cp -r /usr/local/Cellar/jpeg mac/
cp -r /usr/local/Cellar/giflib mac/
cp -r /usr/local/Cellar/little-cms2 mac/

sudo chown -R Chris ./mac
sudo chmod -R u+rw ./mac

GIFLIB_VERSION="5.2.1"
LEPTONICA_VERSION="1.81.1"
LIBPNG_VERSION="1.6.37"
LIBTIFF_VERSION="4.3.0"
LITTLE_CMS_VERSION="2.12"
OPENJPEG_VERSION="2.4.0"
TESSERACT_VERSION="4.1.1"
WEBP_VERSION="1.2.1"


cd "mac/tesseract/${TESSERACT_VERSION}/bin/"

# NOTE that libopenjp2.7.dylib, libopenjp2.2.4.0.dylib, libopenjp2.dylib are actuall all the same file, just symlinked to libopenjp2.2.4.0.dylib

# Modifying libtesseract.4.dylib
install_name_tool -change "/usr/local/Cellar/tesseract/${TESSERACT_VERSION}/lib/libtesseract.4.dylib" "@executable_path/../lib/libtesseract.4.dylib" tesseract
install_name_tool -change "/usr/local/opt/leptonica/lib/liblept.5.dylib" "@executable_path/../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib" "../../../tesseract/${TESSERACT_VERSION}/lib/libtesseract.4.dylib"

# Modifying tesseract
install_name_tool -change "/usr/local/opt/leptonica/lib/liblept.5.dylib" "@executable_path/../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib" tesseract

# Modifying liblept.5.dylib
install_name_tool -change "/usr/local/opt/libpng/lib/libpng16.16.dylib" "@executable_path/../../../libpng/${LIBPNG_VERSION}/lib/libpng16.16.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

install_name_tool -change "/usr/local/opt/jpeg/lib/libjpeg.9.dylib" "@executable_path/../../../jpeg/9d/lib/libjpeg.9.dylib" ."./../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

install_name_tool -change "/usr/local/opt/giflib/lib/libgif.7.dylib" "@executable_path/../../../giflib/${GIFLIB_VERSION}/lib/libgif.7.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"
install_name_tool -change "/usr/local/opt/giflib/lib/libgif.dylib" "@executable_path/../../../giflib/${GIFLIB_VERSION}/lib/libgif.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

install_name_tool -change "/usr/local/opt/libtiff/lib/libtiff.5.dylib" "@executable_path/../../../libtiff/${LIBTIFF_VERSION}/lib/libtiff.5.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

install_name_tool -change "/usr/local/opt/webp/lib/libwebp.7.dylib" "@executable_path/../../../webp/${WEBP_VERSION}/lib/libwebp.7.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"
install_name_tool -change "/usr/local/opt/webp/lib/libwebpmux.3.dylib" "@executable_path/../../../webp/${WEBP_VERSION}/lib/libwebpmux.3.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

install_name_tool -change "/usr/local/opt/openjpeg/lib/libopenjp2.7.dylib" "@executable_path/../../../openjpeg/${OPENJPEG_VERSION}/lib/libopenjp2.2.4.0.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.5.dylib"

# Same as above but for liblept
install_name_tool -change "/usr/local/opt/libpng/lib/libpng16.16.dylib" "@executable_path/../../../libpng/${LIBPNG_VERSION}/lib/libpng16.16.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"

install_name_tool -change "/usr/local/opt/jpeg/lib/libjpeg.9.dylib" "@executable_path/../../../jpeg/9d/lib/libjpeg.9.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"

install_name_tool -change "/usr/local/opt/giflib/lib/libgif.7.dylib" "@executable_path/../../../giflib/${GIFLIB_VERSION}/lib/libgif.7.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"
install_name_tool -change "/usr/local/opt/giflib/lib/libgif.dylib" "@executable_path/../../../giflib/${GIFLIB_VERSION}/lib/libgif.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"

install_name_tool -change "/usr/local/opt/libtiff/lib/libtiff.5.dylib" "@executable_path/../../../libtiff/${LIBTIFF_VERSION}/lib/libtiff.5.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"

install_name_tool -change "/usr/local/opt/webp/lib/libwebp.7.dylib" "@executable_path/../../../webp/${WEBP_VERSION}/lib/libwebp.7.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"
install_name_tool -change "/usr/local/opt/webp/lib/libwebpmux.3.dylib" "@executable_path/../../../webp/${WEBP_VERSION}/lib/libwebpmux.3.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"

install_name_tool -change "/usr/local/opt/openjpeg/lib/libopenjp2.7.dylib" "@executable_path/../../../openjpeg/${OPENJPEG_VERSION}/lib/libopenjp2.2.4.0.dylib" "../../../leptonica/${LEPTONICA_VERSION}/lib/liblept.dylib"


# Modifying libtiff
install_name_tool -change "/usr/local/opt/jpeg/lib/libjpeg.9.dylib" "@executable_path/../../../jpeg/9d/lib/libjpeg.9.dylib" "../../../libtiff/${LIBTIFF_VERSION}/lib/libtiff.5.dylib"

# Modifying openjpeg
install_name_tool -change "/usr/local/opt/openjpeg/lib/libopenjp2.7.dylib" "@executable_path/../../../openjpeg/${OPENJPEG_VERSION}/lib/libopenjp2.7.dylib" "../../../openjpeg/${OPENJPEG_VERSION}/lib/libopenjp2.2.4.0.dylib"


# Modifying little-cms2

# Modifying libwebpmux
install_name_tool -change "/usr/local/Cellar/webp/${WEBP_VERSION}/lib/libwebp.7.dylib" "@executable_path/../../../webp/${WEBP_VERSION}/lib/libwebp.7.dylib" "../../../webp/${WEBP_VERSION}/lib/libwebpmux.3.dylib"


# # Fix symlinks in openjpeg
# cd "../../../openjpeg/${OPENJPEG_VERSION}/lib/"
# # ls -all
# sudo rm libopenjp2.7.dylib
# sudo rm libopenjp2.dylib
# sudo ln -s libopenjp2.2.4.0.dylib libopenjp2.7.dylib
# sudo ln -s libopenjp2.2.4.0.dylib libopenjp2.dylib
