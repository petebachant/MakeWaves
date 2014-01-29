MakeWaves
=========
MakeWaves is an app for generating regular and random waves with UNH's flap-style wavemaker. The app is still in development.


To-do
-----
  * Calculate limits for random wave parameters based on Random Seas LabVIEW code.
    * This will involve checking if the maximum piston stroke is beyond the physical limit.
  * Properly organize folders of code, resources, etc. 
  * Make regular waves in a similar way to random, i.e. use sub-buffers so ramping down can happen more quickly?

Dependencies
--------
  * Python 2.7x
  * numpy
  * matplotlib (for testing output of wavetsgen.py)
  * daqmx
  * PyDAQmx
  * PyQt4
  * NI DAQmx driver


License
-------
MakeWaves Copyright (c) 2013 Peter Bachant.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see http://www.gnu.org/licenses.
