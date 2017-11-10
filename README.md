MakeWaves
=========

MakeWaves is an app for generating regular and random waves with UNH's flap-style wavemaker. The app is still in development.
See below for how to help.

![Main window](http://i.imgur.com/9If9o2u.png)


Installation/running
--------------------

1. Install dependencies
    1. NI DAQmx driver (See National Instruments website for download)
    1. [Python (x,y)](http://ftp.ntua.gr/pub/devel/pythonxy/Python%28x,y%29-2.7.10.0.exe) (uninstalling any existing Python
     distributions first is recommmended)
    1. [PyDAQmx](http://github.com/clade/PyDAQmx.git) (`pip install pydaqmx`)
    1. [daqmx](http://github.com/petebachant/daqmx.git) (`pip install https://github.com/petebachant/daqmx/archive/master.zip`)
2. Clone this repository locally (`git clone https://github.com/petebachant/MakeWaves`)
3. Move into the repository directory and install with `pip install .`
4. Optional: Create a shortcut by running `python create_shortcut.py`.


Contributing
------------

See the [wiki](https://github.com/petebachant/MakeWaves/wiki#wiki-contributing).
