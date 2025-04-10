# MakeWaves

MakeWaves is an app for generating regular and random waves with UNH's
flap-style wavemaker.

![Main window](http://i.imgur.com/9If9o2u.png)

## Installation/running

1. Install system-level dependencies:
   1. Git (`winget install git`).
   1. NI DAQmx driver (See National Instruments website for download).
   1. [Miniforge Python](https://conda-forge.org/miniforge/)
      (skip this step if you already have `conda` or `installed).
   1. `make` (Recommend installing with Chocolatey on Windows).
   1. [uv](https://docs.astral.sh/uv/#installation)
2. Clone this repository locally
   (`git clone https://github.com/petebachant/MakeWaves.git makewaves`).
3. Move into the repository directory and execute `make` to run the app in
   development mode.
4. Build an executable and create a shortcut by running `make shortcut`.

## Contributing

See the [wiki](https://github.com/petebachant/MakeWaves/wiki#wiki-contributing).

### Development tips

To rebuild the UI after editing `mainwindow.ui` in Qt Designer, run `make ui`.
Note this will change the `mainwindow.py` module, which will need to be
committed to the repo.
