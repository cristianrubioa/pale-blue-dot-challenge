# pale-blue-dot-challenge

...

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python**: This project requires Python version 3.10 or higher. You can download Python from [python.org](https://www.python.org/downloads/).
- **Poetry**: Poetry is a tool for dependency management and packaging in Python. To install Poetry, follow the instructions at [poetry.eustace.io](https://python-poetry.org/docs/#installation).

## Project Setup

To set up the project, follow these steps:

1. Install Dependencies:
   Run the following command to install all the project dependencies, including GDAL, through Poetry:
   ```bash
   poetry install
   ```

2. Install GDAL:
   This project requires a specific installation of GDAL version 3.4.1 with NumPy support. Execute the following command to ensure GDAL is installed correctly:
   ```bash
   poetry run pip install --no-cache-dir --force-reinstall 'GDAL[numpy]==3.4.1'
   ```

   This command will reinstall GDAL to ensure that the correct version and configuration are used.

3. Download Sample Dataset:
You can download sample images for testing from the provided Google Drive link:
[Sample dataset](https://drive.google.com/drive/folders/1_DUHhFlpFfi1zrTE6V-uOZayNhzoUo3I?usp=sharing)
These images are test downloads from [The USGS Earth Explorer](https://earthexplorer.usgs.gov/), covering a specific area of interest defined by the shapefile files.  Access the 
[shapefile](https://github.com/cristianrubioa/pale-blue-dot-challenge/tree/main/shapefile) folder in the repository. The Google Drive folder contains a more extensive sample of the collected images. Here, we only include a couple of images as a demonstration of the tool's use, mainly due to the repository's space limitations.

Activate the Virtual Environment:

4. Activate the Virtual Environment:
   To activate the virtual environment created by Poetry, run:
   ```bash
   poetry shell
   ```

   This will allow you to run scripts and use packages within the virtual environment.

## Usage

...







