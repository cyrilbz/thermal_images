#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  1 17:15:02 2025

@author: cbozonnet
"""


# batch extraction of Flir images temperature value
# save as 32 bit images (ImageJ ready) 

import flir_image_extractor 
import tifffile
import numpy as np
from tqdm import tqdm
import os
import re


########## Inputs ###################
input_directory = './wetransfer_photo-ir-lavande_2025-10-01_0805/2025_IR/' # do not forget the "/" ; './' for current directory
#directory = './'
#file_name = ['FLIR1001', 'FLIR0987'] # list of file names without extension
extension = '.jpg'
output_directory = './tif_images/'
########################################

def extract_export(directory,file_name,extension, output_dir):
    full_path = directory + file_name #+ extension 
    #################### Run thermal image extraction #############################
    fir = flir_image_extractor.FlirImageExtractor() # initialization
    fir.process_image(full_path) # run extractor
    thermal_array = fir.get_thermal_np() # get thermal image as 2D numpy array
    
    # Save as 32-bit TIFF to read in ImageJ
    # Convert to 32-bit float
    thermal_image_32 = thermal_array.astype(np.float32)
    name_without_ext = os.path.splitext(file_name)[0]
    output_path = output_dir + f'{name_without_ext}_thermal_data.tif'
    tifffile.imwrite(output_path, thermal_image_32)
    
    
##################### FILE SELECTION ###############
    
# List to store filenames with odd last digit
file_name = []

# Iterate over all files in the directory
for filename in os.listdir(input_directory):
    # Check if the file matches the pattern FLIRXXXX.jpg
    match = re.match(r'^FLIR(\d{4})\.jpg$', filename)
    if match:
        # Extract the last digit of XXXX
        last_digit = int(match.group(1)[-1])

        # Check if the last digit is odd
        if last_digit % 2 != 0:
            file_name.append(filename)

    
##################### MAIN LOOP #####################
nfiles = len(file_name)       
for k in tqdm(range(nfiles), desc="Processing files"):  
    extract_export(input_directory,file_name[k],extension,output_directory)
    
