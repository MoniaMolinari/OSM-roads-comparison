# GRASS scripts
This folder contains, in the corresponding subfolders, three Python modules for [GRASS GIS](https://grass.osgeo.org/) aimed at performing a geometrical comparison between two road network datasets: one from the [OpenStreetMap (OSM)](http://openstreetmap.org) project and one from an authoritative source:
* [v.osm.precomp](https://github.com/MoniaMolinari/OSM-roads-comparison/tree/master/GRASS-scripts/v.osm.precomp) (Step 1) performs a preliminary comparison of the two datasets, computes global statistics and performs a sensitivity analysis to help users choosing a suitable value of the buffer parameter, which is key in Step 2
* [v.osm.preproc](https://github.com/MoniaMolinari/OSM-roads-comparison/tree/master/GRASS-scripts/v.osm.preproc) (Step 2) performs a geometric preprocessing of the OSM road network dataset to extract its subset representing the same road features of the authoritative dataset
* [v.osm.acc](https://github.com/MoniaMolinari/OSM-roads-comparison/tree/master/GRASS-scripts/v.osm.acc) (Step 3) evaluates the spatial accuracy of the OSM subset extracted in Step 2 using a grid-based approach 

The modules are independent, however users are suggested to apply them subsequently to maximize the effectiveness of the procedure.

**NOTE**: current versions are tested in GRASS GIS 7.1 (development version) and NOT in previous releases. Authors will update the modules as soon as the next stable release will come out.

## Installation (Linux)
* Copy the three folders in the `scripts` folder, which is inside the GRASS source code folder
* Open a terminal window, enter each of the three folders and compile the code. For example, for the `v.osm.precomp` module, type:
```
cd path-to-GRASS-folder/scripts/v.osm.precomp
sudo make
sudo make install
```
## Running the Script (Linux)
To simply run the scripts without installing them:
* From GRASS top menu select `File`
* Select `Launch Script`
* Select a ".py" module such as "v.osm.precomp.py"
* Select `Open`

## Related academic publications
* Brovelli M. A., Minghini M., Molinari M. & Mooney P. (2015) A FOSS4G-based procedure to compare OpenStreetMap and authoritative road network datasets. *Geomatics Workbooks* 12, pp. 235-238, ISSN 1591-092X [[pdf](http://geomatica.como.polimi.it/workbooks/n12/FOSS4G-eu15_submission_70.pdf)]
