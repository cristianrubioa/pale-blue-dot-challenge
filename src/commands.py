import typer

from src.handlers import process_and_clip_landsat_images
from src.handlers import process_bands_for_binary_image
from src.handlers import process_bands_for_ndsi_image
from src.handlers import process_bands_for_true_color_image
from src.handlers import process_satellite_images_metadata
from src.handlers import process_snow_cover_percentange
from src.handlers import process_temperature_roi

app = typer.Typer(help="Handler functions to execute.")


@app.command(
    short_help="Extract image files data and organize metadata in json file.",
    help=process_satellite_images_metadata.__doc__,
)
def metadata():
    process_satellite_images_metadata()


@app.command(
    short_help="Clips images based on shapefile geometries.",
    help=process_and_clip_landsat_images.__doc__,
)
def clipped():
    process_and_clip_landsat_images()


@app.command(
    short_help="Create true color images.",
    help=process_bands_for_true_color_image.__doc__,
)
def color():
    process_bands_for_true_color_image()


@app.command(
    short_help="Create binary images.", help=process_bands_for_binary_image.__doc__
)
def binary():
    process_bands_for_binary_image()


@app.command(
    short_help="Create ndsi images.", help=process_bands_for_ndsi_image.__doc__
)
def ndsi():
    process_bands_for_ndsi_image()


@app.command(
    short_help="Get and Add Snow cover percentage",
    help=process_snow_cover_percentange.__doc__,
)
def snow():
    process_snow_cover_percentange()


@app.command(
    short_help="Get and Add Temperature ROI", help=process_temperature_roi.__doc__
)
def temp():
    process_temperature_roi()
