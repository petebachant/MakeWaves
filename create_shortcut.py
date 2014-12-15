"""
This script creates Windows shortcuts.

"""

import os
from win32com.client import Dispatch

shortcut_path = "MakeWaves.lnk"
pythonw_path = r"C:\Anaconda\pythonw.exe"
makewaves_path = r"C:\Anaconda\Scripts\makewaves-script.py"
wdir = r"C:\temp"
icon = r"C:\Anaconda\Lib\site-packages\makewaves\icons\makewaves_icon.ico"
target_path = '{} {}'.format(pythonw_path, makewaves_path)
print target_path

shell = Dispatch("WScript.shell")
shortcut = shell.CreateShortCut(shortcut_path)
shortcut.Targetpath = pythonw_path
shortcut.Arguments = makewaves_path
shortcut.WorkingDirectory = wdir
shortcut.IconLocation = icon
shortcut.save()

