# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 10:34:40 2025

@author: cbozonnet
"""

'''
This program performs the temperature values extraction from FLIR thermal camera,
allows performing registration of visible to thermal image,
then segment the visible image to extract the plant temperature values.
'''

######## FLIR image file name ##########
########################################
file_name = 'FLIR0530_T_SH_3_2.jpg'
#file_name = 'FLIR0528_O70_SH_3_2.jpg'
#file_name = 'FLIR0526_O85_SH_3_2.jpg'

#file_name = 'FLIR0536_T_SH_16_2.jpg'
#file_name = 'FLIR0534_O70_SH_16_2.jpg'
#file_name = 'FLIR0532_O85_SH_16_2.jpg'
########################################
######## csv filename ##################
csv_filename = 'buffer.csv'
######## Path to SAM model #############
model_path = "C:/Documents/traitement_image/SAM_model/sam_vit_h_4b8939.pth"
########################################

import time
start_time = time.time()

from skimage import io
from skimage import transform
import cv2
import numpy as np

import flir_image_extractor 

from matplotlib import pyplot as plt
import napari
from napari.settings import get_settings
from matplotlib import cm
from PIL import Image

import torch
import torchvision
from segment_anything import sam_model_registry, SamPredictor

import sys
import os.path
import csv
sys.path.append("..")

################## Run FLIR image extractor ###########################

print('Run extractor')
fir = flir_image_extractor.FlirImageExtractor()

fir.process_image(file_name)
# fir.plot()

#original = io.imread(file_name)
visible_img = fir.get_rgb_np()
thermal_img = fir.get_thermal_np()
print('Done')

################# Compute transformation matrix using Affinder ##########

# napari settings
settings = get_settings()
settings.application.ipy_interactive = False

# open napari viewer
viewer = napari.Viewer() # create a viewer
viewer.add_image(thermal_img)
viewer.add_image(visible_img)
#viewer.add_image(IJ_rgb)

print('Compute transformation matrix using Affinder, do not forget to specify the transformation matrix')
print('Then close the Napari viewer to continue the code.')
napari.run() # open napari to do your stuff before continuing the code

###################### Perform registration #################
print("Starting registration")  
# ask the matrix filename
filename = input("Enter the matrix filename: ")

# load the matrix created by affinder
mat = np.loadtxt(filename, delimiter=',')

# function to rearrange the matrix
def matrix_arrange(affine_matrix):
    swapped_cols = affine_matrix[:, [1, 0, 2]]
    swapped_rows = swapped_cols[[1, 0, 2], :]
    return swapped_rows

swapped = matrix_arrange(mat)

# apply transformation using scikit image
registered = transform.warp(visible_img, np.linalg.inv(swapped),output_shape=thermal_img.shape)
print("Done")  

################################ Segmentation using SAM model ###################

print("Starting segmentation")  
# add center marker to ease segmentation
height, width, zdim = registered.shape
x_center = width//2
y_center = height//2

# Choose the model type (vit_h, vit_l, or vit_b) : so far I only have vit_h
model_type = "vit_h"

# Specify device
device = "cpu"

#specify prompt point at the center
mypoint = np.array([[x_center,y_center]]) 
mylabel = np.array([1])

# specify the model
sam = sam_model_registry[model_type](checkpoint=model_path) 
sam.to(device=device) # device

# Create predictor
predictor = SamPredictor(sam) 
predictor.set_image(registered) # give it the image

# run mask generation using prompt (center point)
masks, scores, logits = predictor.predict(
    point_coords=mypoint,
    point_labels=mylabel,
    multimask_output=False,
)

# get result
resulting_mask = masks[0,:,:] # extract plant mask
final_data = thermal_img*resulting_mask # multiply thermal data by plant mask

print("Done")  

########################## Computations ####################

thermal_data = thermal_img[resulting_mask] # extract data as a 1D data vector

# Calculate mean and standard deviation
mean_temp = np.mean(thermal_data)
std_dev_temp = np.std(thermal_data)

print(file_name)
print(f"Mean temperature: {mean_temp}")  
print(f"Std temeprature: {std_dev_temp}")  

# time the total execution
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Execution time: {elapsed_time:.4f} seconds")

print("Close Napari viewer to end the program and save the data")  

###################### save data in csv file #######################

with open(csv_filename, 'a', newline='') as csvfile:
    fieldnames = ['File name', 'Mean plant temperature (°C)', 'Standard Deviation (°C)']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writerow({'File name': file_name, 'Mean plant temperature (°C)': mean_temp, 'Standard Deviation (°C)': std_dev_temp})# write data

########################## plots #################################

# check
viewer = napari.Viewer() # create a viewer
viewer.add_image(thermal_img)
viewer.add_image(registered)
viewer.add_image(resulting_mask)
viewer.add_image(final_data)
napari.run()


