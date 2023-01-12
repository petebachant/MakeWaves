#!/usr/bin/env bash

echo Building GUI

pyuic5 makewaves/mainwindow.ui -o makewaves/mainwindow.py

echo Building resource file

pyrcc5 makewaves/icons/resources.qrc -o makewaves/resources_rc.py

echo Replacing relative import

sed -i 's/import resources_rc/from . import resources_rc/g' makewaves/mainwindow.py

echo Done
