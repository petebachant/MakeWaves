# -*- coding: utf-8 -*-
"""
Created on Wed Jul 03 22:02:15 2013

@author: Pete
"""

import numpy as np
import matplotlib.pyplot as plt
from wavetsgen import Wave

wave = Wave("Regular")

wave.gen_ts()

y = wave.ts

rampfull = np.ones(len(y))

ramp = np.hanning(len(y))

rampfull[-len(ramp)/2:] = ramp[len(ramp)/2:]

rampedy = y*rampfull

plt.plot(rampedy)