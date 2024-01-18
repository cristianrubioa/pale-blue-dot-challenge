from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class ConfigSettings(BaseModel):
    BASE_PATH: ClassVar[Path] = Path(__file__).resolve().parent.parent / "dataset"
    ORIGINAL_DATASET_PATH: Path = BASE_PATH / "original_dataset"
    ORIGINAL_DATASET_METADATA_FILE: str = "landsat_images_data.json"


class Settings(BaseSettings):
    IMAGES_DATASET: ConfigSettings = ConfigSettings()


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
