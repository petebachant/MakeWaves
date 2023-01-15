#!/usr/bin/env bash

echo Building GUI

python -m PyQt5.uic.pyuic makewaves/mainwindow.ui -o makewaves/mainwindow.py

echo Building resource file

python -m PyQt5.pyrcc_main makewaves/icons/resources.qrc -o makewaves/resources_rc.py

echo Replacing relative import

sed -i 's/import resources_rc/from . import resources_rc/g' makewaves/mainwindow.py

echo Done
