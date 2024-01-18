import os

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from numpy import ndarray
from osgeo import gdal
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


def read_landsat_band(image_path: str) -> ndarray:
    """
    Reads a Landsat band and normalizes its data.

    Args:
        - image_path: Path to the Landsat band file.

    Returns:
        - ndarray: A normalized numpy array of the band data.
    """
    dataset = gdal.Open(image_path)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()
    return (data - np.min(data)) / (np.max(data) - np.min(data))


def create_true_color_images_from_landsat_bands(
    image_paths: list[str], output_directory: str
) -> None:
    """
    Creates true color images from grouped Landsat band files.

    Args:
        - image_paths: A list of paths to Landsat band images.
        - output_directory: Path to the directory where the output images will be saved.

    Returns:
        - None

    The function groups images by date, checks if the required bands for true color are present,
    and generates true color images saved as PNG files in the specified directory.
    Missing bands for a specific date are reported, and processing continues with the next group of images.
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
        band_data = [read_landsat_band(band) for band in bands_for_true_color]
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

    Args:
        image_paths: A list of paths to Landsat band images.
        output_directory: Path to the directory where the output images will be saved.

    The function groups images by date, verifies the presence of required bands for creating a binary image (based on
    settings.IMAGES_DATASET.BINARY_IMAGE_BANDS), and generates binary images based on the Normalized Difference Snow Index
    (NDSI) using bands B3 and B6. The binary images are saved as PNG files in the specified directory.
    Missing bands for a specific date are reported, and processing continues with the next group of images.
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
        ndsi = (band_b3_data - band_b6_data) / (band_b3_data + band_b6_data)

        binary_img = np.zeros_like(ndsi)
        binary_img[ndsi > 0.4] = 1

        plt.figure()
        plt.imshow(binary_img, cmap="gray")
        plt.axis("off")
        filename = os.path.basename(bands[0])
        new_filename = replace_suffix_and_extension(
            filename=filename, suffix="BINARY", extension="png"
        )
        output_image_path = os.path.join(output_directory, new_filename)
        plt.savefig(output_image_path, bbox_inches="tight", pad_inches=0)
        plt.close()
