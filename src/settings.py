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
    SHAPEFILE_SHP_FILE: str = "Demo.shp"
    ORIGINAL_DATASET_METADATA_FILE: str = "landsat_images_data.json"
    # Extra
    ORIGINAL_DATASET_IMAGE_EXTENSION: str = "TIF"


class Settings(BaseSettings):
    IMAGES_DATASET: ConfigSettings = ConfigSettings()


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
