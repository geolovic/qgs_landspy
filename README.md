# QgsLandspy
QGIS implementation of the [landspy][landspy_link] python library for landscape analysis. 
This plugin implements some functionality of **landspy** to be used directly in QGIS by means of a processing provider and some buttons and tools. 
It requires to have installed the **landspy** library and its dependencies in QGIS, to see how to install them, see Installation section.

## Plugin installation
The **QgsLandspy** plugin is available for QGIS version 3.18, is developed with Python 3.7 and requires the installation of the [landspy][landspy_link] python library and its dependencies (GDAL, NumPy, SciPy, Scikit-Image and Matplotlib).

Before to install the plugin, it is necessary to install the **landspy** library in QGIS.

### Windows installation
- Open **OSGeo4W shell** (packed with QGIS in the start menu)

- Install **landspy** via pip by typing:

  `pip install landspy`

- If you want to upgrade the landspy version, execute:
  
  `pip install landspy --upgrade`

- Try it out by open the Python console inside QGIS, and type:

  `from landspy import DEM`

### Mac OSx installation
The installation in Mac OsX a bit more complex, because QGIS uses the python Framework of the system. Following this workaround should work. 
- Open one Terminal and go to the QGIS install folder (the folder can change depending on the installed version):
  
  `cd "/Applications/QGIS-LTR.app/Contents/MacOS/bin"`

- Install **landspy** via pip by typing:

  `./pip3 install landspy`

- If you want to upgrade the landspy version, execute:
  
  `./pip3 install landspy --upgrade`

- Try it out by open the Python console inside QGIS, and type:

  `from landspy import DEM`

## Using the plugin
#### TODO




[landspy_link]: https://github.com/geolovic/landspy