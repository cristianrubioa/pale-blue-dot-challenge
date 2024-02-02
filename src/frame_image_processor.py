import json
import os
from datetime import datetime
from datetime import timedelta

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from scipy.stats import linregress

from src.settings import settings
from src.utils import replace_suffix_and_extension

VISUALIZATION_PARAMS = {
    "Color": {
        "max": 1,
        "min": 0,
        "cmap": "gray",
        "title": "True Color",
        "axis": 0,
    },
    "Temperature": {
        "max": None,  # 60,
        "min": None,  # -75,
        "cmap": "RdYlBu_r",
        "title": "Surface Temperature [°C]",
        "axis": 1,
    },
    "NDSI": {
        "max": 1,
        "min": -1,
        "cmap": "RdBu",
        "title": "Snow Index (NDSI)",
        "axis": 2,
    },
}


def data_for_line_plot(json_data_filename: str, vis_params: dict) -> dict:
    """
    Extract and organize data from a JSON file for visualization in a line plot.

    Args:
        - json_data_filename: str
                              File path to the JSON dataset file.

        - vis_params: dict
                      Dictionary containing visualization parameters.

    Return:
        dict: Updated "vis_params" dictionary containing extracted data
              from JSON dataset.
    """
    # Data for line plot
    json_keys = []
    dates = []
    temperatures = []
    snow_cover_percentages = []
    cloud_presence = []

    # Read JSON data from file
    with open(json_data_filename) as file:
        json_data = json.load(file)

    # Read JSON dataset values
    for key, values in json_data.items():
        # Get date from JSON key
        date_str = key.split("_")[0]

        # Add data to memory
        json_keys.append(key)
        dates.append(datetime.strptime(date_str, "%Y%m%d"))
        temperatures.append(values["temperature_roi"])
        snow_cover_percentages.append(values["snow_cover_per"])
        cloud_presence.append(values["has_clouds"])

    my_dict = {
        "date": {
            "all": dates,
            "min": dates[0] - timedelta(days=90),
            "max": dates[-1] + timedelta(days=90),
        },
        "temperature": {
            "all": temperatures,
            "min": np.floor(min(temperatures) - 3),
            "max": np.ceil(max(temperatures) + 3),
        },
        "snow": {
            "all": snow_cover_percentages,
            "min": np.floor(min(snow_cover_percentages) - 3),
            "max": np.ceil(max(snow_cover_percentages) + 3),
        },
        "cloud": {
            "all": cloud_presence,
        },
        "key": {
            "all": json_keys,
        },
    }

    # Add read data to visualization params
    vis_params["JSON_DATA"] = my_dict

    return vis_params


def read_landsat_band(image_path, normalize=False, fill_value=0):
    """
    Reads a Landsat band from the given file path and returns its raster data
    as a numpy array and metadata as a dictionary. It can optionally normalize
    the band data.

    Args:
        - image_path: str
                      Image path and filename to read

        - normalize: bool
                     Whether to normalize band values or not

        - fill_value: int/float
                      Invalid band value to fill with np.nan

    Return:
        - tuple: returns the raster image and the metadata
    """
    # Read GeoTIF band
    with rasterio.open(image_path) as src:
        # Read raster data
        raster = src.read().astype(np.float32)
        raster[raster == fill_value] = np.nan

        # Read Metadata
        metadata = src.meta

    # Scaled values in range [0, 1]
    if normalize:
        raster -= np.nanmin(raster)
        raster /= np.nanmax(raster) - np.nanmin(raster)

    return raster.squeeze(), metadata


def compute_true_color(band_paths, normalize=True, fill_value=0):
    """
    Creates a True Color Image (TCI) from RGB corresponding satelite bands

    Args:
        - band_paths: list(str)
                      Path to band files in RGB sequence

        - normalize: bool
                     Whether to scale values in range [0, 1]
    """
    # RGB images data
    image_true_color = []

    for path in band_paths:
        # Read band data
        image, meta = read_landsat_band(
            image_path=path, normalize=normalize, fill_value=fill_value
        )

        image_true_color.append(image)

    return np.stack(image_true_color, axis=-1)


def compute_landsat_temperature(image_path, band_factors, celcius=True, fill_value=0):
    """
    Compute temperature values from Landsat 8/9 Collection-2 Level-2 data.

    Reads the surface temperature band data from the specified Landsat thermal
    band image and applies the provided scale factors and offset to convert
    the data to temperature values in Kelvin. Optionally, the values can be
    further converted to Celsius.

    Args:
        - image_path: str
                      Path to Landsat thermal band.

        - band_factors: dict
                        Landsat 8/9 Level-2 product scale factors and offset.
                        Must have "SCALE_FACTOR" and "ADDITIVE_OFFSET" keys.

        - celcius: bool, optional
                   Whether to convert temperature values to Celsius.
                   Defaults to True.

        - fill_value: int/float, optional
                      Invalid band value to fill with np.nan.
                      Defaults to 0.

    Returns:
        - ndarray: Array of temperature values in °K or °C, based on the
                   "celcius" argument.
    """

    # Read surface temperature band data
    st_band, meta = read_landsat_band(
        image_path=image_path, normalize=False, fill_value=fill_value
    )

    # Get scale and offset factors
    scale_factor = band_factors["SCALE_FACTOR"]
    offset = band_factors["ADDITIVE_OFFSET"]

    # Convert uint to floating point values in °K
    temperature = (st_band * scale_factor) + offset

    # Convert values to °C
    if celcius:
        temperature -= settings.IMAGES_DATASET.CELCIUS_SCALER_FACTOR

    return temperature


def compute_ndsi(green_path, swir_path, fill_value=0):
    """
    Compute Normalized Differenced Snow Index (NDSI) using Landsat green and
    shortwave infrared bands. The result is an array of NDSI values, where
    invalid divisions are ignored.

    Args:
        - green_path: str
                      Path to Landsat green band

        - swir_path: str
                     Path to Landsat shortwave infrared band

        - fill_value: int/float, optional
                      Invalid band value to fill with np.nan. Defaults to 0.

    Returns:
        - ndarray: Array of NDSI values.
    """
    # Read green band data
    green, meta = read_landsat_band(
        image_path=green_path, normalize=False, fill_value=fill_value
    )

    # Read shortwave infrared band data
    swir, meta = read_landsat_band(
        image_path=swir_path, normalize=False, fill_value=fill_value
    )

    # Compute NDSI (ignoring invalid divisions)
    np.seterr(divide="ignore", invalid="ignore")
    return (green - swir) / (green + swir)


def get_images_to_show(image_filename):
    """
    Generate and return various processed images for visualization.

    Parameters:
        - image_filename: str
                          Base filename format for Landsat image bands.

    Returns:
        dict: A dictionary containing different processed images:

            - "Color": True Color Image (TCI) computed from Red, Green,
                       and Blue bands.

            - "Temperature": Temperature image computed from the thermal band.

            - "NDSI": Normalized Difference Snow Index (NDSI) computed from
                      Green and Shortwave Infrared bands.
    """
    # True Color Image (TCI)
    # ---------------------------------------------------------------------------
    # Get paths for RGB image
    true_color_paths = [
        os.path.join(
            settings.IMAGES_DATASET.ROI_CROPPED_DATASET_PATH,
            image_filename.format(band=band_name),
        )
        for band_name in ["SR_B4", "SR_B3", "SR_B2"]
    ]

    # Compute TCI
    image_true_color = compute_true_color(
        band_paths=true_color_paths, normalize=True, fill_value=0
    )

    # NaN mask for RGB bands
    nan_mask = np.logical_or(
        ~np.isfinite(image_true_color[:, :, 0]),
        ~np.isfinite(image_true_color[:, :, 1]),
        ~np.isfinite(image_true_color[:, :, 2]),
    )

    # Fill RGB bands based on mask
    image_true_color[nan_mask, 0] = np.nan
    image_true_color[nan_mask, 1] = np.nan
    image_true_color[nan_mask, 2] = np.nan
    # ---------------------------------------------------------------------------

    # Temperature image
    # ---------------------------------------------------------------------------
    # Get path for thermal band
    thermal_path = os.path.join(
        settings.IMAGES_DATASET.ROI_CROPPED_DATASET_PATH,
        image_filename.format(band="ST_B10"),
    )

    # Compute the temperature in °C
    image_temperature = compute_landsat_temperature(
        image_path=thermal_path,
        band_factors={
            "SCALE_FACTOR": settings.IMAGES_DATASET.L2SP_TEMPERATURE_SCALE_FACTOR,
            "ADDITIVE_OFFSET": settings.IMAGES_DATASET.L2SP_TEMPERATURE_ADDITIVE_OFFSET,
        },
        celcius=True,
        fill_value=0,
    )
    # ---------------------------------------------------------------------------

    # NDSI image
    # ---------------------------------------------------------------------------
    # Get green band path
    green_path = os.path.join(
        settings.IMAGES_DATASET.ROI_CROPPED_DATASET_PATH,
        image_filename.format(band="SR_B3"),
    )

    # Get shortwave infrared band path
    swir_path = os.path.join(
        settings.IMAGES_DATASET.ROI_CROPPED_DATASET_PATH,
        image_filename.format(band="SR_B6"),
    )

    # Compute NDSI
    image_ndsi = compute_ndsi(green_path=green_path, swir_path=swir_path, fill_value=0)
    # ---------------------------------------------------------------------------

    return {
        "Color": image_true_color,
        "Temperature": image_temperature,
        "NDSI": image_ndsi,
    }


def display_images(images, vis_params, axes, figure):
    """
    Display multiple images on specified axes with given visualization
    parameters.

    Args:
        - images: dict
                  A dictionary containing image names as keys and corresponding
                  image data as values. Must be three.

        - vis_params: dict
                      Visualization parameters for each image, including:
                      axis number, min, max, cmap, and title. The primary keys
                      must match with "images" argument keys.

        - axes: list
                List of matplotlib axes where images will be displayed.

        - figure: matplotlib.pyplot.figure
                  Current matplotlib figure object where the images are
                  displayed

    Raises:
        - ValueError: If the number of images does not match the number of axes.

    Returns:
        None
    """
    # Check input args
    if len(images) != len(axes):
        error_message = "Number of images must be the same of axes."
        raise ValueError(error_message)

    # Display images
    for image_name, image in images.items():
        # Get visualization parameters
        axis_num = vis_params[image_name]["axis"]
        vmin = vis_params[image_name]["min"]
        vmax = vis_params[image_name]["max"]
        cmap = vis_params[image_name]["cmap"]
        title = vis_params[image_name]["title"]

        if (vmin is None) or (vmax is None):
            vmin = np.nanmin(image)
            vmax = np.nanmax(image)

        # Get axis
        ax = axes[axis_num]

        # Display image
        image_plot = ax.imshow(image, cmap=cmap, vmin=vmin, vmax=vmax)
        ax.axis("off")

        # Include title and color bar
        ax.set_title(title)
        if (image.ndim == 2) and (cmap != "gray"):
            figure.colorbar(image_plot, ax=ax, orientation="vertical")


def display_line_plot_by_index(index, json_data, ax=None):
    """
    Display a line plot with temperature, snow cover percentage, and cloud
    presence up to a specified index.

    Args:
        - index: int
                 Index up to which data will be displayed on the line plot.

        - json_data: dict
                     Dictionary containing historical temperature,
                     snow cover, date, and cloud presence data.

                    Each primary value is a dictionary with a mandatory
                    key: "all" and two optional keys: "min", "max"

        - ax: matplotlib.axes.Axes, optional
              Matplotlib axes for plotting. If None, a new subplot is created.

    Returns:
        None
    """
    # Get axis to plot
    if ax is None:
        fig, ax1 = plt.subplots()
    else:
        ax1 = ax

    # Get plot data from JSON
    temperature_data = json_data["temperature"]
    date_data = json_data["date"]
    snow_data = json_data["snow"]
    cloud_data = json_data["cloud"]

    # Create temperature line plot (left y-axis)
    (temp_line,) = ax1.plot(
        date_data["all"][0 : index + 1],
        temperature_data["all"][0 : index + 1],
        color="tab:red",
        label="Temperature",
        marker="o",
    )

    # Config temperature line plot
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Mean temperature [°C]", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax1.set_ylim(
        bottom=temperature_data["min"],
        top=temperature_data["max"],
    )
    ax1.set_xlim(
        left=date_data["min"],
        right=date_data["max"],
    )

    # Add trendline for temperature
    slope_temp, intercept_temp, _, _, _ = linregress(
        range(len(date_data["all"][0 : index + 1])),
        temperature_data["all"][0 : index + 1],
    )
    trendline_temp = [
        slope_temp * i + intercept_temp
        for i in range(len(date_data["all"][0 : index + 1]))
    ]
    (trendline1,) = ax1.plot(
        date_data["all"][0 : index + 1],
        trendline_temp,
        linestyle="dashed",
        color="tab:red",
        label="Temperature Trendline",
    )

    # Snow cover percentage plot (right y-axis)
    ax2 = ax1.twinx()
    (snow_line,) = ax2.plot(
        date_data["all"][0 : index + 1],
        snow_data["all"][0 : index + 1],
        color="tab:blue",
        label="Snow Cover",
        marker="o",
    )

    # Config snow cover line plot
    ax2.set_ylabel("Snow Cover [%]", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax2.set_ylim(
        bottom=snow_data["min"],
        top=snow_data["max"],
    )

    # Add trendline for snow cover percentage
    slope_snow, intercept_snow, _, _, _ = linregress(
        range(len(date_data["all"][0 : index + 1])),
        snow_data["all"][0 : index + 1],
    )
    trendline_snow = [
        slope_snow * i + intercept_snow
        for i in range(len(date_data["all"][0 : index + 1]))
    ]
    (trendline2,) = ax2.plot(
        date_data["all"][0 : index + 1],
        trendline_snow,
        linestyle="dashed",
        color="tab:blue",
        label="Snow Cover Trendline",
    )

    # Vertical dotted line for cloud presence
    for i, cloud in enumerate(cloud_data["all"][0 : index + 1]):
        if cloud:
            ax1.axvline(
                x=date_data["all"][0 : index + 1][i],
                linestyle="dotted",
                color="gray",
            )

    # Custom legend entry for cloud presence
    legend_elements = [
        Line2D(
            xdata=[0],
            ydata=[0],
            linestyle="dotted",
            color="gray",
            label="Cloud Presence",
        )
    ]

    # Combine legend handles for line plots and cloud presence
    legend_handles = [temp_line, snow_line, trendline1, trendline2, *legend_elements]

    # Hide the legend for ax2
    ax2.legend().set_visible(False)

    # Legend below the line plot
    ax1.legend(
        handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=4
    )


def main_image_frame_visualization():
    json_data_filename = os.path.join(
        settings.IMAGES_DATASET.DATASET_PATH,
        settings.IMAGES_DATASET.DATASET_METADATA_FILE_TAGS,
    )
    visualization_params = data_for_line_plot(json_data_filename, VISUALIZATION_PARAMS)
    json_data = visualization_params["JSON_DATA"]
    key_list = json_data["key"]["all"]
    date_values = json_data["date"]["all"]
    total_samples = len(key_list)
    for index in range(total_samples):
        fig = plt.figure(figsize=(12, 10))
        gs = GridSpec(2, 3, figure=fig)

        # create sub plots as grid
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[0, 2])
        ax4 = fig.add_subplot(gs[1, :])

        image_filename = key_list[index] + "_{band}_CROPPED.TIF"
        images_dict = get_images_to_show(image_filename)

        # Display images at row 0
        display_images(
            images=images_dict,
            vis_params=visualization_params,
            axes=[ax1, ax2, ax3],
            figure=fig,
        )

        # Display line plot
        display_line_plot_by_index(index, json_data, ax=ax4)
        subtitle_date = date_values[index].strftime("%B %d, %Y")
        ax4.set_title(
            subtitle_date,
            fontsize=14,
            fontweight="bold",
            color="white",
            # x=0.05,
            y=1.05,
            bbox={
                "facecolor": "#ff5555",
                "edgecolor": "gray",
                "boxstyle": "round,pad=0.3",
            },
        )
        plt.tight_layout()
        new_filename = replace_suffix_and_extension(
            filename=image_filename, suffix="VIDEO_FRAME", extension="png"
        )
        output_directory = os.path.join(
            settings.IMAGES_DATASET.DATASET_PATH,
            settings.IMAGES_DATASET.FRAME_VISUALIZATION_DATASET_PATH,
        )
        output_image_path = os.path.join(output_directory, new_filename)
        plt.savefig(output_image_path, bbox_inches="tight", pad_inches=0, dpi=300)
        plt.close()
