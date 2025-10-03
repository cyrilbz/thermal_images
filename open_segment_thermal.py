# -*- coding: utf-8 -*-
"""
Created on Mon Mar  3 11:23:46 2025

@author: cbozonnet
"""

# a program that tries to segment the termal images directly

import time
import os
import flir_image_extractor 
import tifffile

from matplotlib import pyplot as plt
from skimage.morphology import remove_small_objects, remove_small_holes
import numpy as np
import cv2

from segment_anything import sam_model_registry, SamPredictor

import csv

########## File name ###################
directory = './wetransfer_photo-ir-lavande_2025-10-01_0805/2025_IR/' # do not forget the "/" ; './' for current directory
#directory = './'
file_name = ['FLIR1001'] # list of file names without extension
extension = '.jpg'
csv_filename = 'results.csv' # to write outputs
######## Path to SAM model #############
model_path = "/home/cbozonnet/Documents/image_processing/SAM_model/sam_vit_h_4b8939.pth"
########################################

def thermal_processing(directory,file_name,extension, output_name):
    full_path = directory + file_name + extension 
    start_time = time.time()
    
    #################### Run thermal image extraction #############################
    fir = flir_image_extractor.FlirImageExtractor() # initialization
    fir.process_image(full_path) # run extractor
    thermal_array = fir.get_thermal_np() # get thermal image as 2D numpy array
    fir.save_images()
    
    # Save as 32-bit TIFF to read in ImageJ
    # Convert to 32-bit float
    thermal_image_32 = thermal_array.astype(np.float32)
    tifffile.imwrite(f'{file_name}_thermal_image.tif', thermal_image_32)
    
    # # Read the TIFF file back into a numpy array
    # loaded_image = tifffile.imread(f'{file_name}_thermal_image.tif')

    # # Verify the data type and values
    # print(loaded_image.dtype)  # Should be float32
    
    # # open napari viewer & plot both images
    # settings = get_settings()
    # settings.application.ipy_interactive = True
    # viewer = napari.Viewer() 
    # viewer.add_image(thermal_img)
    # napari.run()
    #viewer.add_image(visible_img)
    
    ################### Run semgentation using Segment-Anything-Model ############
    ################### first : specify prompts 
    thermal_img_path = directory + file_name + '_thermal.png'
    thermal_img = cv2.imread(thermal_img_path) 
    #os.remove(thermal_img_path)
    
    height, width, _ = thermal_img.shape
    x_center = width//2
    y_center = height//2
    bf = 8 # border factor for negative prompts
    #specify prompts points (1 for positives, 0 for negatives)
    prompts = np.array([[x_center,round(0.95*y_center)],\
                        [round(0.95*x_center),y_center],\
                        [round(1.05*x_center),y_center],\
                        [x_center,round(1.05*y_center)],\
                        [x_center/bf,y_center/bf], \
                        [x_center/bf,y_center*(2*bf-1)/bf],\
                        [x_center*(2*bf-1)/bf,y_center/bf],[x_center*(2*bf-1)/bf,y_center*(2*bf-1)/bf]]) 
    mylabel = np.array([1,1,1,1,0,0,0,0]) # prompt values
    
    
    # prompts = np.array([[x_center,round(0.95*y_center)],\
    #                     [x_center,round(1.05*y_center)],\
    #                     [x_center/bf,y_center/bf]])
    # mylabel = np.array([1,1,0]) # prompt values
    
    plt.figure(figsize=(10,10))
    plt.imshow(thermal_img[:,:,0])
    plt.scatter(x=prompts[0:4,0],y=prompts[0:4,1], c='g', s=80)
    plt.scatter(x=prompts[4:,0],y=prompts[4:,1], c='r', s=40)
    plt.axis('off')
    plt.title("Original image with point prompts (green = positive, red=negative)", fontsize=18)
    plt.show()
    
    ##################### Second : use of SAM  model 
    
    # Choose the model type (vit_h, vit_l, or vit_b) : so far I only have vit_h
    model_type = "vit_h"
    
    # Specify device
    device = "cuda"
    
    # specify the model
    sam = sam_model_registry[model_type](checkpoint=model_path) 
    sam.to(device=device) # device
    
    # Create predictor
    predictor = SamPredictor(sam) 
    predictor.set_image(thermal_img) # give it the image
    
    # run mask generation using prompts
    masks, scores, logits = predictor.predict(
        point_coords=prompts,
        point_labels=mylabel,
        multimask_output=False,
    )
    
    # get result
    nmask ,nx,ny = masks.shape 
    
    # # view all masks for multiple masks output
    if (nmask>1):
        for i in range(nmask):
            plt.figure(figsize=(10,10))
            plt.imshow(thermal_img[:,:,0])
            plt.contour(masks[i,:,:], colors='red', levels=[0.5])
            plt.axis('off')
            plt.title(f"Mask {i+1}, Score {scores[i]:3f}", fontsize=18)
            plt.show
    
    get_mask = masks[0,:,:] # extract plant mask
    
    # clean mask
    resulting_mask = remove_small_objects(get_mask, min_size=90)
    resulting_mask = remove_small_holes(resulting_mask, area_threshold=80)
    
    plt.figure(figsize=(10,10))
    plt.imshow(thermal_img[:,:,0])
    plt.contour(resulting_mask, colors='red', levels=[0.5])
    plt.axis('off')
    plt.title(f"{file_name} with final mask (open_segment_thermal.py)", fontsize=18)
    plt.show
    
    ################ Computations ###############################
    
    thermal_data = thermal_array[resulting_mask] # extract data as a 1D data vector
    
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
    
    ###################### save data in csv file #######################
    
    with open(output_name, 'a', newline='') as csvfile:
        fieldnames = ['File name', 'Mean plant temperature (°C)', 'Standard Deviation (°C)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'File name': file_name, 'Mean plant temperature (°C)': mean_temp, 'Standard Deviation (°C)': std_dev_temp})# write data
       
##################### MAIN LOOP #####################
nfiles = len(file_name)       
for k in range(nfiles):   
    thermal_processing(directory,file_name[k],extension,csv_filename)
