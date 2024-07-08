APP_NAME=QPy7zipExplorer
APP_ICON=app.icns

rm -R dist/$APP_NAME 2>/dev/null
rm -R dist/$APP_NAME.app 2>/dev/null
rm -R dist/$APP_NAME.dmg 2>/dev/null

#pyinstaller --noupx -w -i "$APP_ICON" -n "$APP_NAME" -D main.py --exclude-module _bootlocale
pyinstaller QPy7zipExplorer.spec


#cp -R resources/* dist/$APP_NAME.app/Contents/Resources/
#rm -R dist/$APP_NAME.app/Contents/Resources/bash
#rm -R dist/$APP_NAME.app/Contents/Resources/bin/win
#rm -R dist/$APP_NAME.app/Contents/Resources/pymediainfo-6.1.0.dist-info


cp resources/main.ui "dist/$APP_NAME.app/Contents/Resources/"
cp resources/main.rcc "dist/$APP_NAME.app/Contents/Resources/"
mkdir -p "dist/$APP_NAME.app/Contents/Resources/bin/macos"
cp -R resources/bin/macos/* "dist/$APP_NAME.app/Contents/Resources/bin/macos/"

rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/uic
rm -R dist/$APP_NAME.app/Contents/Resources/PyQt5/uic

rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/translations
rm -R dist/$APP_NAME.app/Contents/Resources/PyQt5/Qt5/translations

rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtQml.framework
rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtQmlModels.framework
rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtQuick.framework
rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtSvg.framework
rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtWebSockets.framework

rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/lib/QtNetwork.framework

rm dist/$APP_NAME.app/Contents/Frameworks/libcrypto.3.dylib
rm dist/$APP_NAME.app/Contents/Frameworks/libssl.3.dylib

rm dist/$APP_NAME.app/Contents/Frameworks/QtNetwork
rm dist/$APP_NAME.app/Contents/Frameworks/QtQml
rm dist/$APP_NAME.app/Contents/Frameworks/QtQmlModels
rm dist/$APP_NAME.app/Contents/Frameworks/QtQuick
rm dist/$APP_NAME.app/Contents/Frameworks/QtSvg
rm dist/$APP_NAME.app/Contents/Frameworks/QtWebSockets

rm dist/$APP_NAME.app/Contents/Resources/libcrypto.3.dylib
rm dist/$APP_NAME.app/Contents/Resources/libssl.3.dylib

rm dist/$APP_NAME.app/Contents/Resources/QtNetwork
rm dist/$APP_NAME.app/Contents/Resources/QtQml
rm dist/$APP_NAME.app/Contents/Resources/QtQmlModels
rm dist/$APP_NAME.app/Contents/Resources/QtQuick
rm dist/$APP_NAME.app/Contents/Resources/QtSvg
rm dist/$APP_NAME.app/Contents/Resources/QtWebSockets

#rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/bearer
rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/generic
rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/iconengines
rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/imageformats
rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/platformthemes

rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/platforms/libqminimal.dylib
rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/platforms/libqoffscreen.dylib
rm -R dist/$APP_NAME.app/Contents/Frameworks/PyQt5/Qt5/plugins/platforms/libqwebgl.dylib

#rm -R dist/$APP_NAME/
#mkdir dist/$APP_NAME
#mv dist/presets.db dist/$APP_NAME/
#mv dist/$APP_NAME.app dist/$APP_NAME/

#cd dist
#rm $APP_NAME-macos.zip 2>/dev/null
#zip -q -r $APP_NAME-macos.zip $APP_NAME
#cd ..

# mkdir dist/dmg
# mv dist/$APP_NAME.app dist/dmg/
# python make_dmg.py "dist/dmg" "dist/$APP_NAME.dmg" "$APP_NAME"
# mv dist/dmg/$APP_NAME.app dist/
# rm -R dist/dmg
