import json
import os

from src.image_processor import clip_images_by_shapefile_geometries
from src.image_processor import create_binary_images_from_landsat_bands
from src.image_processor import create_true_color_images_from_landsat_bands
from src.landsat_data_processor import create_satellite_images_paths
from src.landsat_data_processor import organize_satellite_data_json
from src.landsat_data_processor import organize_satellite_data_txt
from src.settings import settings
from src.utils import decode_satellite_filename


def process_satellite_images_metadata() -> None:
    """
    Processes Landsat satellite image files to extract and organize metadata into JSON and text report formats.

    This function scans a designated directory for satellite images, extracts metadata using filename decoding,
    and organizes this data by year. It then writes the organized data into two files: one in JSON format and another
    as a structured text report. If no images are found in the dataset, the function exits with an error message.

    Args:
        None

    Returns:
        None

    The function creates two files:
    - A JSON file containing structured metadata organized by year.
    - A text file providing a metadata report organized by year and month.
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

    # Create metadata json file
    satellite_data_json = organize_satellite_data_json(image_filenames=image_filenames)
    output_json_path_file = os.path.join(
        settings.IMAGES_DATASET.DATASET_PATH,
        settings.IMAGES_DATASET.ORIGINAL_DATASET_METADATA_FILE,
    )
    json_data = json.dumps(satellite_data_json, indent=4)
    with open(output_json_path_file, "w") as file:
        file.write(json_data)

    # Create report txt file
    satellite_data_txt = organize_satellite_data_txt(image_filenames=image_filenames)
    output_txt_path_file = os.path.join(
        settings.IMAGES_DATASET.DATASET_PATH,
        settings.IMAGES_DATASET.ORIGINAL_DATASET_REPORT_FILE,
    )
    with open(output_txt_path_file, "w") as file:
        file.write(satellite_data_txt)


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


def process_bands_for_true_color_image() -> None:
    """
    Processes Landsat band images to create true color images.

    This function reads Landsat band images from a specified directory, filters them based on the file extension,
    and then uses these images to create true color images. The resulting true color images are saved
    in a designated output directory.
    """
    image_paths = [
        os.path.join(settings.IMAGES_DATASET.ROI_CROPPED_DATASET_PATH, file)
        for file in os.listdir(settings.IMAGES_DATASET.ROI_CROPPED_DATASET_PATH)
        if file.endswith(f".{settings.IMAGES_DATASET.ORIGINAL_DATASET_IMAGE_EXTENSION}")
    ]
    create_true_color_images_from_landsat_bands(
        image_paths=image_paths,
        output_directory=settings.IMAGES_DATASET.ROI_CROPPED_COLOR_DATASET_PATH,
    )


def process_bands_for_binary_image() -> None:
    """
    Processes Landsat band images to create binary images.

    This function reads Landsat band images from a specified directory, filters them based on the file extension,
    and then uses these images to create binary images. The binary images are generated based on the Normalized
    Difference Snow Index (NDSI) using specific bands. The resulting binary images are saved in a designated
    output directory.
    """
    image_paths = [
        os.path.join(settings.IMAGES_DATASET.ROI_CROPPED_DATASET_PATH, file)
        for file in os.listdir(settings.IMAGES_DATASET.ROI_CROPPED_DATASET_PATH)
        if file.endswith(f".{settings.IMAGES_DATASET.ORIGINAL_DATASET_IMAGE_EXTENSION}")
    ]
    create_binary_images_from_landsat_bands(
        image_paths=image_paths,
        output_directory=settings.IMAGES_DATASET.ROI_CROPPED_BINARY_DATASET_PATH,
    )
