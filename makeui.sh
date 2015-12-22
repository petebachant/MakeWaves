#!/usr/bin/env bash

echo Building GUI

python -m PyQt4.uic.pyuic.py makewaves/mainwindow.ui -o makewaves/mainwindow.py

echo Building resource file

pyrcc4 -py3 makewaves/icons/resources.qrc -o makewaves/resources_rc.py

echo Replacing relative import

sed -i 's/import resources_rc/from . import resources_rc/g' makewaves/mainwindow.py

echo Done
