from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class ConfigSettings(BaseModel):
    # Paths
    BASE_PATH: ClassVar[Path] = Path(__file__).resolve().parent.parent
    DATASET_PATH: Path = BASE_PATH / "dataset"
    SHAPEFILE_PATH: Path = BASE_PATH / "shapefile"
    ORIGINAL_DATASET_PATH: Path = DATASET_PATH / "original"
    ROI_CROPPED_DATASET_PATH: Path = DATASET_PATH / "roi_clipped"
    ROI_CROPPED_COLOR_DATASET_PATH: Path = DATASET_PATH / "roi_clipped_color"
    ROI_CROPPED_BINARY_DATASET_PATH: Path = DATASET_PATH / "roi_clipped_binary"
    ROI_CROPPED_NDSI_DATASET_PATH: Path = DATASET_PATH / "roi_clipped_ndsi"
    ROI_CROPPED_TEMPERATURE_DATASET_PATH: Path = (
        DATASET_PATH / "roi_clipped_temperature"
    )
    FRAME_VISUALIZATION_DATASET_PATH: Path = DATASET_PATH / "frame_visualization"
    FRAME_VIDEO_DATASET_PATH: Path = DATASET_PATH / "video"
    # Files
    SHAPEFILE_SHP_FILE: str = "demo.shp"
    ORIGINAL_DATASET_METADATA_FILE: str = "landsat_images_metadata.json"
    ORIGINAL_DATASET_REPORT_FILE: str = "landsat_images_report.txt"
    DATASET_METADATA_FILE_TAGS: str = "landsat_images_tags.json"
    TEMPERATURE_ROI_BOUNDARIES_FILE: str = "temperature_roi_boundaries.txt"
    FRAME_VIDEO_FILE: str = "oibur_video.mp4"
    # Factors
    BINARY_IMAGE_NDSI_THRESHOLD: float = 0.4
    CELCIUS_SCALER_FACTOR: float = 273.15
    L2SP_TEMPERATURE_SCALE_FACTOR: float = 0.00341802
    L2SP_TEMPERATURE_ADDITIVE_OFFSET: int = 149
    L2SP_REFLECTANCE_SCALE_FACTOR: float = 0.0000275
    L2SP_REFLECTANCE_ADDITIVE_OFFSET: float = -0.2
    # Extra
    ORIGINAL_DATASET_IMAGE_EXTENSION: str = "TIF"
    RGB_COLOR_IMAGE_BANDS: list = ["B4", "B3", "B2"]
    BINARY_IMAGE_BANDS: list = ["B3", "B6"]


class Settings(BaseSettings):
    IMAGES_DATASET: ConfigSettings = ConfigSettings()


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
