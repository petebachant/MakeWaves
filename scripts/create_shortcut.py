#!/usr/bin/env python
"""Creates Windows shortcut."""

import os

from win32com.client import Dispatch

shortcut_path = "MakeWaves.lnk"
this_dir = os.path.dirname(os.path.abspath(__file__))
wdir = os.path.dirname(this_dir)
icon = os.path.join(
    wdir,
    "makewaves",
    "icons",
    "makewaves_icon.ico",
)
exe = os.path.join(wdir, "dist", "makewaves", "makewaves.exe")
shell = Dispatch("WScript.shell")
shortcut = shell.CreateShortCut(shortcut_path)
shortcut.Targetpath = exe
shortcut.WorkingDirectory = wdir
shortcut.IconLocation = icon
shortcut.save()
