import json
import os
import re
from collections import OrderedDict
from collections import defaultdict

from settings import settings


def decode_satellite_filename(filename: str) -> dict[str] | None:
    """
    Decodes a Landsat satellite filename into its constituent components and returns
    a dictionary with these components.

    The filename is expected to follow a specific format outlined in the Landsat Collection 2 Data Dictionary

    Filename Format: LXSS_LLLL_PPPRRR_YYYYMMDD_yyyymmdd_CC_TX_<SX>_<BX>.TIF
    Link: https://www.usgs.gov/centers/eros/science/landsat-collection-2-data-dictionary#landsat_product_id_l2

    LXSS - L (Landsat), X (Sensor), SS (#Satellite)
    LLLL - Processing Correction Level
    PPPRRR - WRS (Path & Row)
    YYYYMMDD - Acquisition Date
    yyyymmdd - Processing Date
    CC - Collection number (02)
    TX - Collection category
    SX - Surface (Reflectance/Temperature)
    BX - Band

    Args:
        filename (str): The satellite filename to decode.

    Returns:
        dict[str] | None: A dictionary with the parsed filename components if the filename
        matches the expected format, None otherwise.
    """
    date_regex = r"(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])"
    pattern = re.compile(
        r"""
        (?P<satellite>L[COTEM][0-9]{2})_
        (?P<correction_level>L2SP|L2SR)_
        (?P<wrs>\d{6})_
        (?P<acquisition_date>"""
        + date_regex
        + r""")_
        (?P<processing_date>"""
        + date_regex
        + r""")_
        (?P<collection_number>[0-9]{2})_
        (?P<collection_category>RT|T1|T2)_
        (?P<surface>[A-Z]{2})_
        (?P<band>[A-Z0-9_]+)
        (\.TIF$)
    """,
        re.VERBOSE,
    )

    match = re.match(pattern, filename)
    if match:
        return match.groupdict()
    return None


def organize_satellite_data(files: list[str]) -> dict[str, dict]:
    """
    Organizes Landsat satellite file names into structured data by year.
    Extracts information such as satellite, collection details, and bands.

    Structured Data Format:
    {
        "year": {
            "satellites": ["LXSS"],
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
        files (list[str]): Satellite file names.

    Returns:
        dict[str, dict]: Structured data organized by year.
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

    for filename in files:
        details = decode_satellite_filename(filename)
        if details:
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
            structured_data[year]["collection_category"].add(
                details["collection_category"]
            )
            structured_data[year]["values"].setdefault(key, set()).add(
                f'{details["surface"]}_{details["band"]}'
            )
        else:
            print(f"Could not extract information from: {filename}")

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


def main():
    all_images_files = [
        file
        for file in os.listdir(settings.IMAGES_DATASET.ORIGINAL_DATASET_PATH)
        if file.endswith(".TIF")
    ]
    if not all_images_files:
        print(
            "The dataset is empty. Please check that you have images in the correct format."
        )
        print(decode_satellite_filename.__doc__)
        exit(1)

    satellite_data = organize_satellite_data(all_images_files)
    json_data = json.dumps(satellite_data, indent=4)
    with open(settings.IMAGES_DATASET.ORIGINAL_DATASET_METADATA_FILE, "w") as file:
        file.write(json_data)


if __name__ == "__main__":
    main()
