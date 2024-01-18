import os

import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping


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
            output_path = os.path.join(output_directory, os.path.basename(image_path))

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
