MakeWaves
=========
MakeWaves is an app for generating regular and random waves with UNH's flap-style wavemaker. The app is still in development.

Contributing
------------

See the [wiki](https://github.com/petebachant/MakeWaves/wiki#wiki-contributing).

## To-do ##
  * Calculate safe limits for random wave parameters based on Random Seas LabVIEW code.
    This will involve checking if the maximum piston stroke is beyond the physical limit.
  * Properly organize folders of code, resources, etc. 

Dependencies
--------
  * Python 2.7
  * Numpy
  * matplotlib (for testing output of wavetsgen.py)
  * [daqmx](http://github.com/petebachant/daqmx.git)
  * [PyDAQmx](http://github.com/clade/PyDAQmx.git)
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
