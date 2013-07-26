# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 19:33:00 2013

@author: Pete

This script tests the ability to call MakeWaves functionality from other
applications.

It works, but the calls are a bit awkward. Classes should be rearranged a bit.

"""

import makewaves
import time

# Create a wave generation object
wavegen = makewaves.MainWindow.WaveGen("Regular")
wavegen.wave.height = 0.1
wavegen.start()

time.sleep(4)

wavestop = makewaves.MainWindow.WaveStop(wavegen)
wavestop.start()