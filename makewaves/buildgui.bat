echo Building GUI

call pyuic5 mainwindow.ui > mainwindow.py

echo Building resource file

call pyrcc5 -py3 icons/resources.qrc -o resources_rc.py

echo Done
