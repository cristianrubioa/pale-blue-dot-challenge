import json
import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from numpy import ndarray
from osgeo import gdal
from PIL import Image
from rasterio.features import geometry_mask
from rasterio.mask import mask
from shapely.geometry import mapping

from src.landsat_data_processor import decode_satellite_filename
from src.settings import settings
from src.utils import create_custom_filename
from src.utils import group_images_by_date
from src.utils import replace_suffix_and_extension


def clip_images_by_shapefile_geometries(
    image_paths: list[str], shapefile_path_file: str, output_directory: str
) -> None:
    """
    Clips images based on geometries from a shapefile.

    For each image path in images_paths, this function clips the image using the geometries
    from the shapefile located at shapefile path. The clipped images are saved in the
    output_directory. If the output directory does not exist, it is created.

    Args:
        - image_paths (list[str]): A list of paths to the images to be clipped.
        - shapefile_path_file (str): The path file to the shapefile containing the clipping geometries.
        - output_directory (str): The directory where the clipped images will be saved.

    Returns:
        - None
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    gdf = gpd.read_file(shapefile_path_file)

    for image_path in image_paths:
        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            continue

        with rasterio.open(image_path) as src:
            gdf = gdf.to_crs(src.crs)
            geoms = [mapping(geom) for geom in gdf.geometry.values]
            out_image, out_transform = mask(src, geoms, crop=True)

            filename = os.path.basename(image_path)
            old_filename_group = decode_satellite_filename(filename)
            if not old_filename_group:
                print(f"Could not extract information from: {filename}")

            new_filename = create_custom_filename(
                details=old_filename_group,
                suffix="CROPPED",
                extension=f"{settings.IMAGES_DATASET.ORIGINAL_DATASET_IMAGE_EXTENSION}",
            )
            output_path = os.path.join(output_directory, new_filename)
            with rasterio.open(
                output_path,
                "w",
                driver="GTiff",
                height=out_image.shape[1],
                width=out_image.shape[2],
                count=src.count,
                dtype=out_image.dtype,
                crs=src.crs,
                transform=out_transform,
            ) as dst:
                dst.write(out_image)


def read_landsat_band(image_path: str, is_normalize: bool = False) -> ndarray:
    """
    Reads a Landsat band from the given file path and returns its data as a numpy array.
    It can optionally normalize the band data.

    The function supports reading the band data using GDAL or rasterio libraries.
    If normalization is requested, the data is read using GDAL, and each pixel value
    is normalized to the range [0, 1]. If normalization is not requested, the data is
    read using rasterio, and zero values are replaced with NaN to handle no-data areas.

    Args:
        - image_path (str): Path to the Landsat band file.
        - is_normalize (bool, optional): Whether to normalize the band data. Defaults to False.

    Returns:
        - ndarray: A numpy array of the band data. If normalized, values range from 0 to 1.
            If not normalized, zero values are replaced with NaN.
    """
    if is_normalize:
        dataset = gdal.Open(image_path)
        band = dataset.GetRasterBand(1)
        data = band.ReadAsArray()
        return (data - np.min(data)) / (np.max(data) - np.min(data))

    with rasterio.open(image_path) as src:
        image = src.read().astype(np.float32)
        image[image == 0] = np.nan
    return image.squeeze()


def create_true_color_images_from_landsat_bands(
    image_paths: list[str], output_directory: str
) -> None:
    """
    Creates true color images from grouped Landsat band files.

    The function groups images by date, checks if the required bands for true color are present,
    and generates true color images saved as PNG files in the specified directory.
    Missing bands for a specific date are reported, and processing continues with the next group of images.

    Args:
        - image_paths: A list of paths to Landsat band images.
        - output_directory: Path to the directory where the output images will be saved.

    Returns:
        - None
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    grouped_paths = group_images_by_date(image_paths)
    required_bands = set(settings.IMAGES_DATASET.RGB_COLOR_IMAGE_BANDS)

    for key, bands in grouped_paths.items():
        found_bands = {
            band
            for band in required_bands
            if any(band in filename for filename in bands)
        }
        if found_bands != required_bands:
            print(
                f"Missing required bands for date {key}: {required_bands - found_bands} bands not found"
            )
            continue

        bands_for_true_color = [
            filename
            for filename in bands
            if any(
                band in filename
                for band in settings.IMAGES_DATASET.RGB_COLOR_IMAGE_BANDS
            )
        ]
        band_data = [
            read_landsat_band(band, is_normalize=True) for band in bands_for_true_color
        ]
        true_color_image = np.stack(band_data, axis=-1)

        plt.figure()
        plt.imshow(true_color_image)
        plt.axis("off")
        filename = os.path.basename(bands[0])
        new_filename = replace_suffix_and_extension(
            filename=filename, suffix="COLOR", extension="png"
        )
        output_image_path = os.path.join(output_directory, new_filename)
        plt.savefig(output_image_path, bbox_inches="tight", pad_inches=0)
        plt.close()


def create_binary_images_from_landsat_bands(
    image_paths: list[str], output_directory: str
) -> None:
    """
    Creates binary images from specific Landsat bands.

    The function groups images by date, verifies the presence of required bands for creating a binary image (based on
    settings.IMAGES_DATASET.BINARY_IMAGE_BANDS), and generates binary images based on the Normalized Difference Snow Index
    (NDSI) using bands B3 and B6. The binary images are saved as PNG files in the specified directory.
    Missing bands for a specific date are reported, and processing continues with the next group of images.

    Args:
        - image_paths: A list of paths to Landsat band images.
        - output_directory: Path to the directory where the output images will be saved.
    Returns:
        - None
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    grouped_paths = group_images_by_date(image_paths)
    required_bands = set(settings.IMAGES_DATASET.BINARY_IMAGE_BANDS)

    for key, bands in grouped_paths.items():
        found_bands = {
            band
            for band in required_bands
            if any(band in filename for filename in bands)
        }
        if found_bands != required_bands:
            print(
                f"Missing required bands for date {key}: {required_bands - found_bands} bands not found"
            )
            continue

        band_b3_data = read_landsat_band(
            next(filename for filename in bands if "B3" in filename)
        )
        band_b6_data = read_landsat_band(
            next(filename for filename in bands if "B6" in filename)
        )
        np.seterr(divide="ignore", invalid="ignore")
        ndsi = (band_b3_data - band_b6_data) / (band_b3_data + band_b6_data)

        binary_img = np.zeros_like(ndsi)
        binary_img[ndsi > settings.IMAGES_DATASET.BINARY_IMAGE_NDSI_THRESHOLD] = 1
        binary_image = (binary_img * 255).astype(np.uint8)

        image = Image.fromarray(binary_image)
        filename = os.path.basename(bands[0])
        new_filename = replace_suffix_and_extension(
            filename=filename, suffix="BINARY", extension="png"
        )
        output_image_path = os.path.join(output_directory, new_filename)
        image.save(output_image_path)


def create_ndsi_images_from_landsat_bands(
    image_paths: list[str], output_directory: str
) -> None:
    """
    Creates images from specific Landsat bands using the Normalized Difference Snow Index (NDSI).

    The function groups Landsat band images by date, verifies the presence of the required bands for creating a binary
    image (based on settings.IMAGES_DATASET.BINARY_IMAGE_BANDS), and generates binary images using bands B3 and B6.
    The resulting binary images represent the NDSI and are saved as PNG files in the specified output directory.
    If any required bands are missing for a specific date, it reports the missing bands and continues processing with
    the next group of images.

    Args:
        - image_paths: A list of paths to Landsat band images.
        - output_directory: Path to the directory where the output images will be saved.
    Returns:
        - None
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    grouped_paths = group_images_by_date(image_paths)
    required_bands = set(settings.IMAGES_DATASET.BINARY_IMAGE_BANDS)

    for key, bands in grouped_paths.items():
        found_bands = {
            band
            for band in required_bands
            if any(band in filename for filename in bands)
        }
        if found_bands != required_bands:
            print(
                f"Missing required bands for date {key}: {required_bands - found_bands} bands not found"
            )
            continue

        band_b3_data = read_landsat_band(
            next(filename for filename in bands if "B3" in filename)
        )
        band_b6_data = read_landsat_band(
            next(filename for filename in bands if "B6" in filename)
        )
        np.seterr(divide="ignore", invalid="ignore")
        ndsi = (band_b3_data - band_b6_data) / (band_b3_data + band_b6_data)

        plt.figure()
        plt.imshow(ndsi, vmin=-1, vmax=1, cmap="RdBu")
        plt.axis("off")
        filename = os.path.basename(bands[0])
        new_filename = replace_suffix_and_extension(
            filename=filename, suffix="NDSI", extension="png"
        )
        output_image_path = os.path.join(output_directory, new_filename)
        plt.savefig(output_image_path, bbox_inches="tight", pad_inches=0)
        plt.close()


def create_temperature_images_from_landsat_bands(
    image_paths: list[str], output_directory: str, temperature_roi_boundaries_file: str
) -> None:
    """
    Generates temperature images from Landsat band images, with optional ROI (Region of Interest) temperature boundaries.

    This function processes each Landsat band image provided in `image_paths` to calculate and visualize temperature data.
    The temperature is calculated using scale factors and offsets defined in settings.IMAGES_DATASET. If a temperature ROI
    boundaries file is provided and exists, the temperature images are visualized with these min and max boundaries.
    Otherwise, the images are saved without defined limits. The temperature images are saved as PNG files in the
    specified `output_directory`.

    Args:
        - image_paths: A list of paths to Landsat band images.
        - output_directory: Path to the directory where the output images will be saved.
        - temperature_roi_boundaries_file: Path to a file containing temperature ROI boundaries, if available.

    Returns:
        - None
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    is_temp_boundaries_file = os.path.exists(temperature_roi_boundaries_file)
    if is_temp_boundaries_file:
        with open(temperature_roi_boundaries_file) as file:
            temperature_roi_boundaries_data = file.read().strip("'").split(",")

        temperature_roi_min = np.floor(
            float(temperature_roi_boundaries_data[0].split(":")[1].strip())
        )
        temperature_roi_max = np.floor(
            float(temperature_roi_boundaries_data[1].split(":")[1].strip())
        )
    else:
        print(
            f"The file at the specified path {temperature_roi_boundaries_file} does not exist in the directory"
        )
        print("The images will be saved but without defined minimum and maximum limits")

    for image_path in image_paths:
        image = read_landsat_band(image_path)
        value = (
            (image * settings.IMAGES_DATASET.L2SP_TEMPERATURE_SCALE_FACTOR)
            + settings.IMAGES_DATASET.L2SP_TEMPERATURE_ADDITIVE_OFFSET
            - settings.IMAGES_DATASET.CELCIUS_SCALER_FACTOR
        )
        plt.figure()
        if is_temp_boundaries_file:
            plt.imshow(
                value,
                vmin=temperature_roi_min,
                vmax=temperature_roi_max,
                cmap="RdYlBu_r",
            )
        plt.imshow(value, cmap="RdYlBu_r")
        plt.axis("off")
        filename = os.path.basename(image_path)
        new_filename = replace_suffix_and_extension(
            filename=filename, suffix="TEMPERATURE", extension="png"
        )
        output_image_path = os.path.join(output_directory, new_filename)
        plt.savefig(output_image_path, bbox_inches="tight", pad_inches=0)
        plt.close()


def get_and_add_snow_cover_percentage(
    base_mask_image_path: str,
    image_paths: list[str],
    shapefile_path_file: str,
    output_directory: str,
) -> None:
    """
    Calculates and adds snow cover percentage to existing data for each Landsat image.

    This function reads a shapefile to define the region of interest (ROI),
    creates a mask for the ROI, and calculates the percentage of snow cover in the ROI
    for each provided Landsat image. The snow cover percentages are then added to
    existing data and saved in a specified output directory.

    Args:
        - base_mask_image_path (str): Path to the base mask image.
        - image_paths (list[str]): List of paths to Landsat images.
        - shapefile_path_file (str): Path to the shapefile defining the ROI.
        - output_directory (str): Directory path to save the updated data.

    Returns:
        - None
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    gdf = gpd.read_file(shapefile_path_file)
    with rasterio.open(base_mask_image_path) as src:
        gdf = gdf.to_crs(src.crs)

        roi_mask = geometry_mask(
            geometries=gdf.geometry,
            out_shape=src.read().squeeze().shape,
            transform=src.transform,
        )
    roi_pixels = np.sum(np.invert(roi_mask))

    with open(output_directory) as file:
        landsat_images_data = json.load(file)

    results = {}
    for image_path in sorted(image_paths):
        key = "_".join(os.path.basename(image_path).split(".")[0].split("_")[0:2])
        binary_image = np.array(Image.open(image_path))
        snow_pixels = np.sum(binary_image == 255)
        snow_cover_percentage = np.round((snow_pixels / roi_pixels) * 100, 2)
        results[key] = {
            "snow_cover_per": snow_cover_percentage,
        }
    json_data = json.dumps(landsat_images_data, indent=4)
    with open(output_directory, "w") as file:
        file.write(json_data)


def get_and_add_temperature_roi(
    image_paths: list[str], output_directory: str, output_directory_temp_boundaries: str
) -> None:
    """
    Calculates and adds temperature Region of Interest (ROI) data
    to Landsat images metadata and saves temperature boundaries.

    This function processes each Landsat band image in `image_paths` to calculate the temperature using specific
    scale factors and offsets defined in settings.IMAGES_DATASET. It updates the metadata of each Landsat image
    with the calculated mean temperature as the temperature ROI. The updated metadata is saved in JSON format
    in `output_directory`. Additionally, the function determines the minimum and maximum temperatures across
    all images and saves these as temperature ROI boundaries in a text file in `output_directory_temp_boundaries`.

    Args:
        - image_paths: A list of paths to Landsat band images.
        - output_directory: Path to the directory where the updated metadata JSON file will be saved.
        - output_directory_temp_boundaries: Path to the directory where the temperature ROI boundaries
            text file will be saved.

    Returns:
        - None
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    with open(output_directory) as file:
        landsat_images_data = json.load(file)

    temp_min, temp_max = 100, -100
    for image_path in sorted(image_paths):
        key = "_".join(os.path.basename(image_path).split(".")[0].split("_")[0:2])
        image = read_landsat_band(image_path)
        value = (
            (image * settings.IMAGES_DATASET.L2SP_TEMPERATURE_SCALE_FACTOR)
            + settings.IMAGES_DATASET.L2SP_TEMPERATURE_ADDITIVE_OFFSET
            - settings.IMAGES_DATASET.CELCIUS_SCALER_FACTOR
        )
        temp_mean = np.nanmean(value).astype(float)
        landsat_images_data[key]["temperature_roi"] = np.round(temp_mean, 2)
        if np.nanmin(value) < temp_min:
            temp_min = np.nanmin(value)
        if np.nanmax(value) > temp_max:
            temp_max = np.nanmax(value)

    json_data = json.dumps(landsat_images_data, indent=4)
    with open(output_directory, "w") as file:
        file.write(json_data)

    txt_data = f"temperature_roi_min: {temp_min}, temperature_roi_max: {temp_max}"
    with open(output_directory_temp_boundaries, "w") as file:
        file.write(txt_data)
