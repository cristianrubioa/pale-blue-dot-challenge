import os
import re
from collections import defaultdict

DATE_REGEX = r"(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])"


def decode_satellite_filename(filename: str) -> dict[str, str] | None:
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
    BX - Satellite bands
    TIF - Image Data Extension

    Args:
        - filename (str): The satellite filename to decode.

    Returns:
        - dict[str, str] | None: A dictionary with the parsed filename components if the filename
        matches the expected format, None otherwise.
    """
    pattern = re.compile(
        r"""
        (?P<satellite>L[COTEM][0-9]{2})_
        (?P<correction_level>L2SP|L2SR)_
        (?P<wrs>\d{6})_
        (?P<acquisition_date>"""
        + DATE_REGEX
        + r""")_
        (?P<processing_date>"""
        + DATE_REGEX
        + r""")_
        (?P<collection_number>[0-9]{2})_
        (?P<collection_category>RT|T1|T2)_
        (?P<surface>ST|SR)_
        (?P<band>[A-Z0-9_]+)
        (\.TIF$)
    """,
        re.VERBOSE,
    )

    match = re.match(pattern, filename)
    if match:
        return match.groupdict()
    return None


def create_custom_filename(details: dict[str, str], suffix: str, extension: str) -> str:
    """
    Creates a custom filename using provided details, a suffix, and an extension.

    Args:
        - details (dict[str, str]): A dictionary containing specific details for the filename.
        - suffix (str): A string to append before the file extension.
        - extension (str): The file extension.

    Returns:
        - str: The custom formatted filename.
    """
    return (
        f'{details["acquisition_date"]}_{details["wrs"]}_'
        f'{details["surface"]}_{details["band"]}_{suffix}.{extension}'
    )


def group_images_by_date(image_paths: list[str]) -> dict[str, list[str]]:
    """
    Groups image file paths by date extracted from their filenames.

    Args:
        - image_paths: A list of image file paths.

    Returns:
        - dict[str, list[str]]: A dictionary mapping dates to lists of image paths.
    """
    grouped_images = defaultdict(list)
    for image_path in image_paths:
        filename = os.path.basename(image_path)
        match = re.search(r"(\d{8})_(\d{6})_(ST|SR)_([A-Z0-9_]+)", filename)
        if match:
            date = match.group(1)
            grouped_images[date].append(image_path)
    return grouped_images


def replace_suffix_and_extension(
    filename: str, suffix: str | None = None, extension: str | None = None
) -> str:
    """
    Replaces the suffix and extension of a filename.

    Args:
        - filename: The original filename.
        - suffix: The new suffix to replace the existing one. If None, the existing suffix is {UNDEFINED}.
        - extension: The new extension to replace the existing one, without the leading dot.

    Returns:
        - str: The modified filename with the new suffix and/or extension.
    """
    name, ext = os.path.splitext(filename)
    name = name.rsplit("_", 3)[0]
    name += f"_{suffix}" if suffix else "UNDEFINED"
    ext = extension if extension else ext
    return f"{name}.{ext}"
