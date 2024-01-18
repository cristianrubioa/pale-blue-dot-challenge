import json
import os

from src.image_processor import clip_images_by_shapefile_geometries
from src.landsat_data_processor import create_satellite_images_paths
from src.landsat_data_processor import decode_satellite_filename
from src.landsat_data_processor import organize_satellite_data
from src.settings import settings


def process_satellite_images_metadata() -> None:
    """
    Processes Landsat satellite image files to extract and organize metadata.

    Scans the designated directory for satellite images, extracts metadata using filename decoding,
    organizes this data by year, and writes it as a JSON file. If no images are found, it exits with an error message.

    Args:
        - None

    Returns:
        - None
    """
    image_filenames = [
        file
        for file in os.listdir(settings.IMAGES_DATASET.ORIGINAL_DATASET_PATH)
        if file.endswith(f".{settings.IMAGES_DATASET.ORIGINAL_DATASET_IMAGE_EXTENSION}")
    ]
    if not image_filenames:
        print(
            "The dataset is empty. Please check that you have images in the correct format."
        )
        print(decode_satellite_filename.__doc__)
        exit(1)

    satellite_data = organize_satellite_data(image_filenames=image_filenames)
    json_data = json.dumps(satellite_data, indent=4)
    output_json_path = os.path.join(
        settings.IMAGES_DATASET.DATASET_PATH,
        settings.IMAGES_DATASET.ORIGINAL_DATASET_METADATA_FILE,
    )
    with open(output_json_path, "w") as file:
        file.write(json_data)


def process_and_clip_landsat_images() -> None:
    """
    Processes Landsat images data and clips images based on shapefile geometries.

    Loads metadata of Landsat images, generates paths for satellite images, and clips the
    first six images using specified shapefile geometries. The clipped images are saved
    in a designated output directory.
    """
    json_path_file = os.path.join(
        settings.IMAGES_DATASET.DATASET_PATH,
        settings.IMAGES_DATASET.ORIGINAL_DATASET_METADATA_FILE,
    )
    with open(json_path_file) as file:
        landsat_images_data = json.load(file)

    image_paths = create_satellite_images_paths(
        landsat_images_data=landsat_images_data,
        image_directory=settings.IMAGES_DATASET.ORIGINAL_DATASET_PATH,
    )
    shapefile_path_file = os.path.join(
        settings.IMAGES_DATASET.SHAPEFILE_PATH,
        settings.IMAGES_DATASET.SHAPEFILE_SHP_FILE,
    )
    clip_images_by_shapefile_geometries(
        image_paths=image_paths,
        shapefile_path_file=shapefile_path_file,
        output_directory=settings.IMAGES_DATASET.ROI_CROPPED_DATASET_PATH,
    )
