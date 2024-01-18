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
    ORIGINAL_DATASET_PATH: Path = DATASET_PATH / "original_dataset"
    ROI_CROPPED_DATASET_PATH: Path = DATASET_PATH / "roi_cropped_dataset"
    ROI_CROPPED_COLOR_DATASET_PATH: Path = DATASET_PATH / "roi_cropped_color_dataset"
    ROI_CROPPED_BINARY_DATASET_PATH: Path = DATASET_PATH / "roi_cropped_binary_dataset"
    # Files
    SHAPEFILE_SHP_FILE: str = "demo.shp"
    ORIGINAL_DATASET_METADATA_FILE: str = "landsat_images_data.json"
    ORIGINAL_DATASET_REPORT_FILE: str = "landsat_images_report.txt"
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
