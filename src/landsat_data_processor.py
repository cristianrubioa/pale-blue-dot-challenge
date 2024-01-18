import os
from collections import OrderedDict
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.settings import settings
from src.utils import decode_satellite_filename


def organize_satellite_data(image_filenames: list[str]) -> dict[str, dict]:
    """
    Organizes Landsat satellite file names into structured data by year.
    Extracts information such as satellite, collection details, and bands.

    Structured Data Format:
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

    Args:
        - image_filenames (list[str]): Satellite file names.

    Returns:
        - dict[str, dict]: Structured data organized by year.
    """
    structured_data = defaultdict(
        lambda: {
            "satellites": set(),
            "correction_level": set(),
            "collection_number": set(),
            "collection_category": set(),
            "values": {},
        }
    )

    for filename in image_filenames:
        details = decode_satellite_filename(filename=filename)
        if not details:
            print(f"Could not extract information from: {filename}")
            continue

        year = details["acquisition_date"][:4]
        key = (
            details["satellite"],
            details["wrs"],
            details["acquisition_date"],
            details["processing_date"],
        )
        structured_data[year]["satellites"].add(details["satellite"])
        structured_data[year]["correction_level"].add(details["correction_level"])
        structured_data[year]["collection_number"].add(details["collection_number"])
        structured_data[year]["collection_category"].add(details["collection_category"])
        structured_data[year]["values"].setdefault(key, set()).add(
            f'{details["surface"]}_{details["band"]}'
        )

    for year in structured_data:
        sorted_values = sorted(
            structured_data[year]["values"].items(), key=lambda x: x[0][2]
        )
        structured_data[year]["values"] = [
            {
                "satellite": satellite,
                "wrs": wrs,
                "acquisition_date": date,
                "processing_date": processing_date,
                "bands": sorted(bands),
            }
            for (satellite, wrs, date, processing_date), bands in sorted_values
        ]
        all_months = {f"{index:02d}" for index in range(1, 13)}
        existing_months = {
            value["acquisition_date"][4:6] for value in structured_data[year]["values"]
        }
        structured_data[year]["missing_months"] = sorted(all_months - existing_months)

    organized_data = OrderedDict()
    for year in sorted(structured_data.keys()):
        organized_data[year] = {
            key: list(structured_data[year][key])
            if isinstance(structured_data[year][key], set)
            else structured_data[year][key]
            for key in structured_data[year]
        }

    return organized_data


def create_satellite_images_paths(
    landsat_images_data: dict[str, Any], image_directory: Path
) -> list[str]:
    """
    Generates a list of file paths for satellite images based on input data.

    Args:
        - landsat_images_data (dict[str, Any]): A dictionary containing satellite image metadata.
            The data of the file that is defined in <settings.IMAGES_DATASET.ORIGINAL DATASET METADATA_FILE>
        - image_directory (Path): The directory where the image files are stored.

    Returns:
        - list[str]: A list of file paths for the satellite images.
    """
    image_paths = []
    for year, image_data in landsat_images_data.items():
        _ = year
        correction_level = image_data["correction_level"][0]
        collection_number = image_data["collection_number"][0]
        collection_category = image_data["collection_category"][0]

        for value in image_data["values"]:
            for band in value["bands"]:
                filename = (
                    f'{value["satellite"]}_{correction_level}_{value["wrs"]}'
                    f'_{value["acquisition_date"]}_{value["processing_date"]}_{collection_number}'
                    f"_{collection_category}_{band}.{settings.IMAGES_DATASET.ORIGINAL_DATASET_IMAGE_EXTENSION}"
                )
                file_path = os.path.join(image_directory, filename)
                image_paths.append(file_path)
    return image_paths
