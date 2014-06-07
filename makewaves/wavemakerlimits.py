# -*- coding: utf-8 -*-
"""
Created on Thu Jun 06 00:44:28 2013

@author: Pete

This module replicates the logic of the Regular Waves VI to calculate a
safe wave height.

"""
from __future__ import division, print_function
import numpy as np
import os
import sys

_thisdir = sys.prefix + "/Lib/site-packages/makewaves"

if not os.path.isdir(_thisdir):
    _thisdir = ""
else:
    _thisdir += "/"

max_halfstroke = 0.16 # Was 0.16
flap_height = 3.3147
depth = 2.44
min_period = 0.5
max_period = 5.0
max_H_L = 0.1
max_H_d = 0.65


def dispsolver(rad_frequency, depth, decimals=2):
    """Solves for surface wavenumber to a specified number of decimals."""
    g = 9.81
    k = np.arange(0, 30, 10**-(decimals))
    r = np.abs(rad_frequency**2 - g*k*np.tanh(k*depth))
#    if np.min(r) > 10**(-decimals-1):
#        return np.nan
#    else:
    return k[np.where(r == np.min(r))[0][0]]

    
def revdispsolver(wavenumber, depth, decimals=2):
    """Returns radian frequency given wavenumber and depth"""
    g = 9.81
    k = wavenumber
    sigma = np.arange(0, 10, 10**-(decimals))
    r = np.abs(sigma**2 - g*k*np.tanh(k*depth))
#    if np.min(r) > 10**(-decimals):
#        return np.nan
#    else:
    return sigma[np.where(r == np.min(r))[0][0]]
        

def height_to_stroke_amp(wave_height, period, flap_height, depth):
    sigma = 2*np.pi/period
    h = depth
    k = dispsolver(sigma, h)
    H = wave_height
    S = H/(4*(np.sinh(k*h)/(k*h))*(k*h*np.sinh(k*h) - \
    np.cosh(k*h) + 1)/(np.sinh(2*k*h) + 2*k*h))
    return flap_height/depth*S/2.0
    

def stroke_amp_to_height(stroke_amp, period, flap_height, depth):
    sigma = 2*np.pi/period
    h = depth
    k = dispsolver(sigma, h)
    S = 2*stroke_amp*depth/flap_height
    H = S*(4*(np.sinh(k*h)/(k*h))*(k*h*np.sinh(k*h) - \
    np.cosh(k*h) + 1)/(np.sinh(2*k*h) + 2*k*h))
    return H
    

def calc_safe_height(H, T):
    sta_spec = height_to_stroke_amp(H, T, flap_height, depth)
    
    # Wave height using max piston stroke
    wh1 = stroke_amp_to_height(max_halfstroke, T, flap_height, depth)
    
    # Wave height using max H/L
    wh2 = max_H_L * 2*np.pi/dispsolver(2*np.pi/T, depth)
    
    # Wave height using max H/d
    wh3 = max_H_d * depth
    
    # Stroke amplitude calculated using max H/L
    sta2 = height_to_stroke_amp(wh2, T, flap_height, depth)
    
    # Stroke amplitude calculated using max H/d
    sta3 = height_to_stroke_amp(wh3, T, flap_height, depth)
    
    if sta_spec > np.min([max_halfstroke, sta2, sta3]):
        return np.min([wh1, wh2, wh3])
    else: 
        return H
    

def findlimits(plot=False, save=True):
    periods = np.arange(0.5, 5.01, 0.001)
    mh = np.zeros(len(periods))
    
    for n in range(len(periods)):
        progress = np.round(n/len(periods)*100, decimals=2)
        sys.stdout.write("\rComputing wavemaker limits... \t" + str(progress)+"%")
        sys.stdout.flush()
        mh[n] = calc_safe_height(50, periods[n])
    
    if plot:
        import matplotlib.pyplot as plt
        plt.close('all')
        plt.plot(periods, mh)
        plt.show()
        
    if save:
        if not os.path.isdir(_thisdir + "settings"):
            os.mkdir(_thisdir + "settings")    
        np.save(_thisdir + "settings/periods", periods)
        np.save(_thisdir + "settings/maxH", mh)
        
    return periods, mh

    
if __name__ == "__main__":
    findlimits(plot=False, save=False)
