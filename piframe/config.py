from PIL.Image import Image
from pydantic import BaseModel

from piframe import models, prompts
from piframe.reflection import ModuleDefinition


class Config(BaseModel):
    artifact_directory: str
    description_model: ModuleDefinition[models.Model[str]]
    image_model: ModuleDefinition[models.Model[Image]]
    topic_strategy: ModuleDefinition[prompts.TopicStrategy]