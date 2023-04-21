# Installation Instructions
## Command Line Version
The installation instructions for the necessary environment using a cmd terminal are:
- conda create -n PyHCs3 python=3.10
- conda activate PyHCs3
- pip install jupyter   
- pip install pyspedas
- pip install plasmapy
- git clone https://github.com/spacepy/spacepy.git
- pip install ./spacepy
- git clone https://github.com/nasa/Kamodo.git
- pip install -e ./Kamodo
- pip install s3fs
- pip install h5netcdf
- cd ./Kamodo/kamodo_ccmc/readers/OCTREE_BLOCK_GRID
- python interpolate_amrdata_extension_build.py
- cd ../../../..

## Notebook Version
Assuming the notebook is in a python 3.10 environment, the commands are:
- import os
- print(os.popen('pip install pyspedas').read())
- print(os.popen('pip install plasmapy').read())
- print(os.popen('git clone https://github.com/spacepy/spacepy.git').read())
- print(os.popen('pip install ./spacepy').read())
- print(os.popen('git clone https://github.com/rebeccaringuette/Kamodo.git').read())
- print(os.popen('pip install -e ./Kamodo').read())
- print(os.popen('pip install s3fs').read())
- print(os.popen('pip install h5netcdf').read())
- os.chdir('./Kamodo/kamodo_ccmc/readers/OCTREE_BLOCK_GRID')
- print(os.popen('python interpolate_amrdata_extension_build.py').read())
- os.chdir('../../../..')
