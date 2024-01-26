# pale-blue-dot-challenge

Development of the submission for the NASA's challenge to create a visualization using Earth observation data that advances at least one of the following Sustainable Development Goals (SDGs):

*  Zero Hunger
*  Clean Water and Sanitation
*  Climate Action


## Summary

The visual representation depicts annual climate trends in [Los Glaciares National Park, Argentina](https://whc.unesco.org/en/list/145/), from 2013 to 2024. The visualization reveals a warmer climate, evidenced by a positive slope in surface temperature, along with a decreasing trend in the percentage of snow cover, indicating the impact of climate change. This comprehensive analysis uses the [Landsat Collection-2 Level-2](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products) data set for the Landsat 8 and 9 OLI/TIRS satellites. The main Sustainable Development Goal (SDG) addressed is [SDG 13: Climate Action](https://www.un.org/sustainabledevelopment/climate-change/). The tools used for this visualization include Python for data processing, Matplotlib for plotting, and Geographic Information System (GIS) tools for spatial analysis.


## Dataset

The [USGS EarthExplorer](https://earthexplorer.usgs.gov/) is the source of our satellite imagery datasets. We utilized the **Landsat Collection 2 Level 2** dataset from **Landsat 8 and 9 OLI/TIRS C2 L2** satellites. These datasets provide high-resolution images with atmospheric and geometric corrections, making them ideal for detailed earth surface analysis.

Sample images are available for testing via this Google Drive link: [Sample dataset](https://drive.google.com/drive/folders/1_DUHhFlpFfi1zrTE6V-uOZayNhzoUo3I?usp=sharing). These samples cover an area of interest as defined by the shapefile files. Access the shapefile folder in the repository [here](https://github.com/cristianrubioa/pale-blue-dot-challenge/tree/main/shapefile). The Google Drive folder contains a broader sample of our collected images. Due to space limitations in the repository, only a couple of images are included [here](https://github.com/cristianrubioa/pale-blue-dot-challenge/tree/main/dataset/original) as a tool demonstration.

## Prerequisites

Before starting, ensure you have the following installed:

- **[Python](https://www.python.org/downloads/)**: The programming language used for project development. This project requires Python version 3.10 or higher.
- **[Poetry](https://python-poetry.org/docs/#installation)**: A tool for dependency management and packaging in Python.
- **[Jupyter Notebook](https://jupyter.org/)**: An interactive development environment for writing and executing code.

## Project Setup

Follow these steps to set up the project:

1. **Install Dependencies**:
   Use the following command to install all project dependencies via Poetry:
   ```bash
   poetry install
   ```

2. **Install GDAL**:
   This project requires GDAL version 3.4.1 with NumPy support. Use the following command for the correct installation:
   ```bash
   poetry run pip install --no-cache-dir --force-reinstall 'GDAL[numpy]==3.4.1'
   ```

   This ensures the proper version and configuration of GDAL.

3. **Activate the Virtual Environment**:
   Activate the Poetry-created virtual environment with:
   ```bash
   poetry shell
   ```

   This allows for running scripts and using packages within this environment.

4. **Set Up Jupyter Kernel**:
   To use Jupyter notebooks with the project's virtual environment, set up a Jupyter kernel:
   ```bash
   python -m ipykernel install --user --name=<project_name>
   ```

   Replace `project_name` with a desired name for the Jupyter kernel. This integrates the virtual environment and dependencies with Jupyter notebooks.

## Usage
We've encapsulated certain tasks within the code. While [frame_image_processor](https://github.com/cristianrubioa/pale-blue-dot-challenge/blob/main/src/frame_image_processor.py) generates individual images for video creation using [frame_video_processor](https://github.com/cristianrubioa/pale-blue-dot-challenge/blob/main/src/frame_video_processor.py), pre-processing is required to organize everything.

### CLI and/or Jupyter Lab Demo
A basic guide to using the functions:

#### Generate Image Metadata
Use the command:
```
oibur make metadata
```
In the lab, `process_satellite_images_metadata` is called. This extracts and organizes image information in the [original](https://github.com/cristianrubioa/pale-blue-dot-challenge/tree/main/dataset/original) directory and creates a JSON file with the following structure:
```json
{
        "year": {
            "satellites": ["LXSS"],
            "correction_level": ["L2SP"],
            "collection_number": ["CC"],
            "collection_category": ["TX"],
            "values": [
                {
                    "satellite": "LXSS",
                    "wrs": "PPPRRR",
                    "acquisition_date": "YYYYMMDD",
                    "processing_date": "yyyymmdd",
                    "bands": ["SX_BX", ...]
                },
                ...
            ],
            "missing_months": ["01", "02", ...]
        },
        ...
    }
```
This is saved as [landsat_images_metadata.json](https://github.com/cristianrubioa/pale-blue-dot-challenge/blob/main/dataset/landsat_images_metadata.json). A report file detailing images, dates, and bands available is also created and saved as [landsat_images_report.txt](https://github.com/cristianrubioa/pale-blue-dot-challenge/blob/main/dataset/landsat_images_report.txt).

This step is crucial as it informs subsequent operations.

#### Clip the Area of Interest in the Image
```
oibur make clipped
```
In the lab, `process_and_clip_landsat_images` is used. This command crops the images, focusing only on the desired area. The downloaded images are large in terms of coverage, so we select a specific area of interest, defined using shapefiles. Check the path [dataset/roi_clipped](https://github.com/cristianrubioa/pale-blue-dot-challenge/tree/main/dataset/roi_clipped).

#### Calculate the Temperature of the Region of Interest (ROI) for Each Image
```
oibur make temproi
```
In the lab, `process_temperature_roi` is called. This calculates and adds temperature_roi information to each image in [landsat_images_tags.json](https://github.com/cristianrubioa/pale-blue-dot-challenge/blob/main/dataset/landsat_images_tags.json).

#### Create the Temperature Image
```
oibur make temp
```
In the lab, `process_bands_for_temperature_image` is used. 

#### Create the True Color Image
```
oibur make color
```
In the lab, `process_bands_for_true_color_image` is called. 

#### Create the Binary Image
```
oibur make binary
```
In the lab, `process_bands_for_binary_image` is used. 

#### Calculate and Store Snow Cover Percentages
```
oibur make snow
```
In the lab, `process_snow_cover_percentange` is called. This calculates and adds snow_cover_per information to each image in [landsat_images_tags.json](https://github.com/cristianrubioa/pale-blue-dot-challenge/blob/main/dataset/landsat_images_tags.json).

#### Generate the NDSI Image
```
oibur make ndsi
```

In the lab, `process_bands_for_ndsi_image` is used. 


#### Calculate Cloud Existence
This process is manual and involves identifying images with clouds. Updates are made to [landsat_images_tags.json](https://github.com/cristianrubioa/pale-blue-dot-challenge/blob/main/dataset/landsat_images_tags.json) under the key `has_clouds`.

#### Final Combined Image
See the final result of one of the images comprising the final output, generated using `main_image_frame_visualization` from [frame_image_processor](https://github.com/cristianrubioa/pale-blue-dot-challenge/blob/main/src/frame_image_processor.py).
![Final Image Example](https://github.com/cristianrubioa/pale-blue-dot-challenge/blob/main/dataset/frame_visualization/20130813_VIDEO_FRAME.png)

### Main Jupyter Lab
This explains the end-to-end process for obtaining the final visualization and results. If you're interested in a quick implementation of this visualization, open this lab in Colab. This bypasses the need to set up a virtual environment and install dependencies. Ensure it's synchronized with your images on Drive, for example.
