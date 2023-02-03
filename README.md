# MakeWaves

MakeWaves is an app for generating regular and random waves with UNH's flap-style wavemaker.

![Main window](http://i.imgur.com/9If9o2u.png)

## Installation/running

1. Install system dependencies:
   1. Git, of course.
   1. NI DAQmx driver (See National Instruments website for download).
   1. [Mambaforge](https://github.com/conda-forge/miniforge#mambaforge)
      (skip this step if you already have `conda` or `mamba` installed).
   1. `make` (Recommend installing with Chocolatey on Windows).
2. Clone this repository locally
   (`git clone https://github.com/petebachant/MakeWaves.git makewaves`).
3. Move into the repository directory and create the environment with either
   `mamba env create` or `conda env create`.
   Alternatively, you can install the dependencies manually into a base
   environment.
4. Activate the `makewaves` environment with `conda activate makewaves`
   (not necessary if installing into a base environment) and
   install with `pip install .`
5. Optional: Create a shortcut by running `make shortcut`.

## Contributing

See the [wiki](https://github.com/petebachant/MakeWaves/wiki#wiki-contributing).

### Development tips

Additional dev dependencies can be installed with

```sh
pip install black isort
```

To run from the repository, e.g., for testing changes, run `make`.
To rebuild the UI after editing `mainwindow.ui` in Qt Designer, run `make ui`.
Note this will change the `mainwindow.py` module, which will need to be
committed to the repo.
