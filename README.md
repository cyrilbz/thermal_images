The flir_image_extractor.py tool comes from this repository : https://github.com/ITVRoC/FlirImageExtractor
It relies on Exiftool to work (https://exiftool.org/).

Image reistration is done using Affinder, a napari plugin (plugins->Affinder): https://www.napari-hub.org/plugins/affinder 
It assumes that there is an affine transformation between both images, once you provided at least three points of correspondence between both images (see the tutorial on Affinder website). Once registration is satisfying, simply close the napari viewer to continue with the program by giving the transformation matrix file name (whose name must be provided when lauchning Affinder). 
A future imporvement of the tool could probably be to select manually or automatically several points of correspondences between both images and perform a perspective registration.

Plant segmentation is done using the Segment Anything Model which can be downloaded and installed following : https://github.com/facebookresearch/segment-anything?tab=readme-ov-file
Install the model and its dependencies, as well as download the model checkpoints (link in the same web page).

The segmentation takes as input a point located at the center of the image (presumed location of the plant of interest).

#Usage:

Once all plugins and dependencies are installed, in extract_register_segment_thermal.py simply specify the path to your image, the name of the output file (csv file containing file name, mean plant temperature and standard deviation), and the path to the SAM model checkpoints and run!
