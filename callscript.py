# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 19:33:00 2013

@author: Pete

This script tests the ability to call MakeWaves functionality from other
applications.

"""

import makewaves
import time

# Create a wave generation object
wavegen = makewaves.WaveGen(makewaves.PIERSON_MOSCOWITZ)
wavegen.wave.sig_height = 0.1
wavegen.start()

time.sleep(4)

wavegen.stop()