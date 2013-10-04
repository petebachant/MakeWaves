MakeWaves
=========
MakeWaves is an app for generating regular and random waves with UNH's flap-style wavemaker. The app is still in development.


To-do
-----
  * Figure out why random wave output amplitudes seem to be half what they are compared to Random Seas.
    * Run through and check all math for random waves again!
  * Calculate limits for random wave parameters based on Random Seas LabVIEW code.
    * This will involve checking if the maximum piston stroke is beyond the physical limit.
  * Listen to ACS controller for E-stop presses, or better yet hard wire E-stop into digital inputs of NI DAQ?
  * Properly organize folders of code, resources, etc. 
  * Put searching for new wave height limits in its own thread so GUI doesn't feel laggy -- maybe not necessary.
  * Make regular waves in a similar way to random, i.e. use sub-buffers so ramping down can happen more quickly. 
  * Implement scale ratio in Pierson-Moskowitz waves. Look in comments of wavetsgen.py for more info.

Dependencies
--------
  * Python 2.7x
  * numpy
  * matplotlib (for testing output of wavetsgen.py)
  * daqmx.py (see misc_python)
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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
