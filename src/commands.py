import typer

from src.handlers import process_and_clip_landsat_images
from src.handlers import process_bands_for_binary_image
from src.handlers import process_bands_for_true_color_image
from src.handlers import process_satellite_images_metadata

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
def cropped():
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
