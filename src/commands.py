import typer

from src.handlers import process_and_clip_landsat_images
from src.handlers import process_bands_for_binary_image
from src.handlers import process_bands_for_true_color_image
from src.handlers import process_satellite_images_metadata

app = typer.Typer(help="Handler functions to execute.")


@app.command(help="Extract image files data and organize metadata in json file.")
def metadata():
    process_satellite_images_metadata()


@app.command(help="Clips images based on shapefile geometries.")
def cropped():
    process_and_clip_landsat_images()


@app.command(help="Create true color images.")
def color():
    process_bands_for_true_color_image()


@app.command(help="Create binary images.")
def binary():
    process_bands_for_binary_image()
