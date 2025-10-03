close("*");

// Ask user to select the directory containing thermal images
inputDir = getDirectory("Select input folder of thermal images");
list = getFileList(inputDir);

// Initialize an array to store FLIR names
flirNames = newArray(list.length);

// Initialize results table
run("Clear Results");

// Loop through all files in the directory
for (i = 0; i < list.length; i++) {
    //if (endsWith(list[i], "_thermal_image.tif")) {
        // Open the image
        path = inputDir + list[i];
        open(path);

        // Get the base name (first 8 characters)
        filename = File.nameWithoutExtension;
        flirName = substring(filename, 0, 8);
        rename(flirName);
        
        // Store the FLIR name in the array
        flirNames[i] = flirName;

        // Clean and change LUT
        roiManager("reset");
        close("\\Others");
        run("Rainbow");

        // Loop for re-segmentation
        redoSegmentation = true;
        do_threshold = false;
        while (redoSegmentation) {
            // User selects the plant
            waitForUser("Select the plant using the rectangle tool");

            // Run SAMJ annotator
            run("SAMJ Annotator", "model=[SAM2 Tiny] export=false");
            
            // Show all ROIs on the thermal image
            roiManager("Show All without labels");

            // Ask if the user wants to redo the segmentation
            Dialog.create("Happy?");
            Dialog.addMessage("Tick corresponding box if it's not the case!");
            Dialog.addCheckbox("Redo segementation", false);
            Dialog.addCheckbox("Do threshold", false);
            Dialog.show();
            redoSegmentation = Dialog.getCheckbox();
            do_threshold = Dialog.getCheckbox();

            // Clear previous ROIs if redoing
            if (redoSegmentation) {
                roiManager("reset");
            }
        }

        // Show all ROIs on the thermal image
        roiManager("Show All without labels");
        
        // add threshold if needed
        if (do_threshold) {
        	// run simple thresholding if necessary
			run("Threshold..."); 
			waitForUser("Threshold done?");  	
        }

        // Set measurements and measure
        run("Set Measurements...", "mean standard redirect=None decimal=3");
        roiManager("Measure");

        // Close the image but keep the results table
        close();
    //}
}
Table.setColumn("Label", flirNames)

// Open the save dialog box
saveAs("results");