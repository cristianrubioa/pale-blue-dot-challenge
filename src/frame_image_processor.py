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


def data_for_line_plot():
    # Data for line plot
    json_keys = []
    dates = []
    temperatures = []
    snow_cover_percentages = []
    cloud_presence = []

    JSON_DATA_FILENAME = os.path.join(
        settings.IMAGES_DATASET.DATASET_PATH,
        settings.IMAGES_DATASET.DATASET_METADATA_FILE_TAGS,
    )

    # Read JSON data from file
    with open(JSON_DATA_FILENAME) as file:
        json_data = json.load(file)

    for key, values in json_data.items():
        json_keys.append(key)
        date_str = key.split("_")[0]
        dates.append(datetime.strptime(date_str, "%Y%m%d"))
        temperatures.append(values["temperature_roi"])
        snow_cover_percentages.append(values["snow_cover_per"])
        cloud_presence.append(values["has_clouds"])

    my_dict = {
        "date": {
            "all": dates,
            "start": dates[0] - timedelta(days=90),
            "end": dates[-1] + timedelta(days=90),
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
    VISUALIZATION_PARAMS["JSON_DATA"] = my_dict

    return VISUALIZATION_PARAMS


def get_images_to_show(image_filename):
    # Bands information in memory
    bands_data = {}

    # Read needed bands
    band_names = ["SR_B4", "SR_B3", "SR_B2", "SR_B6", "ST_B10"]
    for band_name in band_names:
        # Get band path
        path = os.path.join(
            settings.IMAGES_DATASET.ROI_CROPPED_DATASET_PATH,
            image_filename.format(band=band_name),
        )
        # Read image -> read_landsat_band()
        with rasterio.open(path) as src:
            image = src.read().astype(np.float32)
            image[image == 0] = np.nan

        # Save band in memory
        bands_data[band_name] = image.squeeze()

    red = bands_data["SR_B4"]
    green = bands_data["SR_B3"]
    blue = bands_data["SR_B2"]
    swir1 = bands_data["SR_B6"]
    st_b10 = bands_data["ST_B10"]

    # Stack bands read in RGB sequence and normalize
    nan_mask = np.logical_or(~np.isfinite(red), ~np.isfinite(green), ~np.isfinite(blue))
    image = np.stack([red, green, blue], axis=-1)
    image[nan_mask, 0] = np.nan
    image[nan_mask, 1] = np.nan
    image[nan_mask, 2] = np.nan
    image_true_color = (image - np.nanmin(image)) / (
        np.nanmax(image) - np.nanmin(image)
    )
    image_true_color = np.nan_to_num(image_true_color, nan=1)

    # Convert int values to °K and then convert to °C
    image_temperature = (
        (st_b10 * settings.IMAGES_DATASET.L2SP_TEMPERATURE_SCALE_FACTOR)
        + settings.IMAGES_DATASET.L2SP_TEMPERATURE_ADDITIVE_OFFSET
        - settings.IMAGES_DATASET.CELCIUS_SCALER_FACTOR
    )

    # Compute NDSI
    np.seterr(divide="ignore", invalid="ignore")
    image_ndsi = (green - swir1) / (green + swir1)

    return {
        "Color": image_true_color,
        "Temperature": image_temperature,
        "NDSI": image_ndsi,
    }


def display_images(images, axes, figure):
    if len(images) != len(axes):
        error_message = "Number of images must be the same of axes."
        raise ValueError(error_message)

    # Show images
    for image_name, image in images.items():
        # Get visualization parameters
        axis_num = VISUALIZATION_PARAMS[image_name]["axis"]
        vmin = VISUALIZATION_PARAMS[image_name]["min"]
        vmax = VISUALIZATION_PARAMS[image_name]["max"]
        cmap = VISUALIZATION_PARAMS[image_name]["cmap"]
        title = VISUALIZATION_PARAMS[image_name]["title"]

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


def display_line_plot(index, visualization_params, ax=None):
    # Config plot axis
    if ax is None:
        fig, ax1 = plt.subplots()
    else:
        ax1 = ax

    # Temperature plot (left y-axis)
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Mean temperature (°C)", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax1.set_ylim(
        bottom=visualization_params["JSON_DATA"]["temperature"]["min"],
        top=visualization_params["JSON_DATA"]["temperature"]["max"],
    )
    ax1.set_xlim(
        visualization_params["JSON_DATA"]["date"]["start"],
        visualization_params["JSON_DATA"]["date"]["end"],
    )
    (temp_line,) = ax1.plot(
        visualization_params["JSON_DATA"]["date"]["all"][0 : index + 1],
        visualization_params["JSON_DATA"]["temperature"]["all"][0 : index + 1],
        color="tab:red",
        label="Temperature",
        marker="o",
    )

    # Add trendline for temperature
    slope_temp, intercept_temp, _, _, _ = linregress(
        range(len(visualization_params["JSON_DATA"]["date"]["all"][0 : index + 1])),
        visualization_params["JSON_DATA"]["temperature"]["all"][0 : index + 1],
    )
    trendline_temp = [
        slope_temp * i + intercept_temp
        for i in range(
            len(visualization_params["JSON_DATA"]["date"]["all"][0 : index + 1])
        )
    ]
    (trendline1,) = ax1.plot(
        visualization_params["JSON_DATA"]["date"]["all"][0 : index + 1],
        trendline_temp,
        linestyle="dashed",
        color="tab:red",
        label="Temperature Trendline",
    )

    # Snow cover percentage plot (right y-axis)
    ax2 = ax1.twinx()
    ax2.set_ylabel("Snow Cover (%)", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax2.set_ylim(
        bottom=visualization_params["JSON_DATA"]["snow"]["min"],
        top=visualization_params["JSON_DATA"]["snow"]["max"],
    )
    (snow_line,) = ax2.plot(
        visualization_params["JSON_DATA"]["date"]["all"][0 : index + 1],
        visualization_params["JSON_DATA"]["snow"]["all"][0 : index + 1],
        color="tab:blue",
        label="Snow Cover",
        marker="o",
    )

    # Add trendline for snow cover percentage
    slope_snow, intercept_snow, _, _, _ = linregress(
        range(len(visualization_params["JSON_DATA"]["date"]["all"][0 : index + 1])),
        visualization_params["JSON_DATA"]["snow"]["all"][0 : index + 1],
    )
    trendline_snow = [
        slope_snow * i + intercept_snow
        for i in range(
            len(visualization_params["JSON_DATA"]["date"]["all"][0 : index + 1])
        )
    ]
    (trendline2,) = ax2.plot(
        visualization_params["JSON_DATA"]["date"]["all"][0 : index + 1],
        trendline_snow,
        linestyle="dashed",
        color="tab:blue",
        label="Snow Cover Trendline",
    )

    # Vertical dotted line for cloud presence
    for i, cloud in enumerate(
        visualization_params["JSON_DATA"]["cloud"]["all"][0 : index + 1]
    ):
        if cloud:
            ax1.axvline(
                x=visualization_params["JSON_DATA"]["date"]["all"][0 : index + 1][i],
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


visualization_params = data_for_line_plot()
for index in range(len(visualization_params["JSON_DATA"]["date"]["all"])):
    fig = plt.figure(figsize=(11, 8))
    gs = GridSpec(2, 3, figure=fig)

    # create sub plots as grid
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax4 = fig.add_subplot(gs[1, :])

    image_filename = (
        visualization_params["JSON_DATA"]["key"]["all"][index] + "_{band}_CROPPED.TIF"
    )
    images_dict = get_images_to_show(image_filename)

    # Display images at row 0
    display_images(images=images_dict, axes=[ax1, ax2, ax3], figure=fig)

    # Display line plot
    display_line_plot(index, visualization_params, ax=ax4)
    subtitle_date = visualization_params["JSON_DATA"]["date"]["all"][index].strftime(
        "%B %d, %Y"
    )
    plt.suptitle(
        subtitle_date,
        fontsize=14,
        fontweight="bold",
        color="white",
        # x=0.05,
        y=0.98,
        bbox={"facecolor": "#ff5555", "edgecolor": "gray", "boxstyle": "round,pad=0.3"},
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
