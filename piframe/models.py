import json
from abc import ABC, abstractmethod
from base64 import b64decode
from dataclasses import dataclass, asdict
from io import BytesIO
from typing import Literal, TypeVar, Generic, Optional

import requests
from PIL import Image
from openai import OpenAI


@dataclass
class MessageContent:
    text: str
    type: Literal["text"] = "text"


@dataclass
class Message:
    content: list[MessageContent]
    role: Literal["user", "assistant"] = "user"

T = TypeVar("T")

class Model(ABC, Generic[T]):
    def __init__(self, model_id: str, *args, **kwargs):
        self.model_id = model_id
        self._model_args = kwargs

    @abstractmethod
    def invoke(self, messages: list[Message]) -> T:
        raise NotImplementedError

class BedrockModel(Model[T]):
    def __init__(self, client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = client

    def invoke(self, messages: list[Message]) -> T:
        body = self._get_request_body(messages)
        response = self._client.invoke_model(
            body=json.dumps(body),
            modelId=self.model_id,
        )
        response_content = json.loads(response.get("body").read())
        log_content = {k: v for k, v in response_content.items() if k != "images"}
        print(f"{log_content=}")
        return self._parse_response(response_content)

    @abstractmethod
    def _get_request_body(self, messages: list[Message]) -> dict:
        raise NotImplementedError

    @abstractmethod
    def _parse_response(self, response: dict) -> T:
        raise NotImplementedError


class Anthropic(BedrockModel[str]):
    def _get_request_body(self, messages: list[Message]) -> dict:
        messages = [asdict(message) for message in messages]
        return {
            "messages": messages,
            **self._model_args,
        }

    def _parse_response(self, response: dict) -> str:
        return response["content"][0]["text"]

class Meta(BedrockModel[str]):
    def _get_request_body(self, messages: list[Message]) -> dict:
        formatted_prompt = f"""<|begin_of_text|><|start_header_id|>user<|end_header_id|>
{messages[0].content[0].text}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""
        return {
            "prompt": formatted_prompt,
            **self._model_args,
        }

    def _parse_response(self, response: dict) -> str:
        return response["generation"]

class StableImage(BedrockModel[Image.Image]):
    def _get_request_body(self, messages: list[Message]) -> dict:
        return {
            "prompt": messages[0].content[0].text,
            "mode": "text-to-image",
            **self._model_args,
        }

    def _parse_response(self, response: dict) -> Image.Image:
        image_bytes = b64decode(response["images"][0])
        return Image.open(BytesIO(image_bytes))


class StableXL(BedrockModel[Image.Image]):
    def _get_request_body(self, messages: list[Message]) -> dict:
        return {
            "text_prompts": [
                {
                    "text": messages[0].content[0].text,
                }
            ],
            **self._model_args,
        }

    def _parse_response(self, response: dict) -> Image.Image:
        image_bytes = b64decode(response.get("artifacts")[0].get("base64"))
        return Image.open(BytesIO(image_bytes))

class TitanImage(BedrockModel[Image.Image]):
    def _get_request_body(self, messages: list[Message]) -> dict:
        return {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": messages[0].content[0].text,
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                **self._model_args.get("imageGenerationConfig", {})
            }
        }

    def _parse_response(self, response: dict) -> Image.Image:
        image_bytes = b64decode(response.get("images")[0].encode())
        return Image.open(BytesIO(image_bytes))

class StableApi(Model[Image.Image]):
    def __init__(
            self,
            api_key: str,
            aspect_ratio: str,
            cfg_scale: Optional[int] = 8,
            negative_prompt: Optional[str] = None,
            output_format: str = "jpeg",
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._api_key = api_key
        self._aspect_ratio = aspect_ratio
        self._cfg_scale = cfg_scale
        self._negative_prompt = negative_prompt
        self._output_format = output_format

    def invoke(self, messages: list[Message]) -> T:
        response = requests.post(
            self.url,
            headers={
                "authorization": f"Bearer {self._api_key}",
                "accept": "image/*"
            },
            files={"none": ""},
            data={
                "model": self.model_id,
                "mode": "text-to-image",
                "prompt": messages[0].content[0].text,
                "aspect_ratio": self._aspect_ratio,
                "negative_prompt": self._negative_prompt,
                "cfg_scale": self._cfg_scale,
                "output_format": self._output_format,
            },
        )
        response.raise_for_status()
        return Image.open(BytesIO(response.content))

    @property
    @abstractmethod
    def url(self):
        raise NotImplementedError

class StableDiffusion3x(StableApi):
    @property
    def url(self):
        return "https://api.stability.ai/v2beta/stable-image/generate/sd3"

class StableImageUltra(StableApi):
    @property
    def url(self):
        return "https://api.stability.ai/v2beta/stable-image/generate/ultra"

class OpenAIImage(Model[Image.Image]):
    def __init__(self, client: Optional[OpenAI] = None, quality: Literal["low", "medium", "high"] = "medium", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = client or OpenAI()
        self._quality = quality

    def invoke(self, messages: list[Message]) -> Image.Image:
        image_description = messages[0].content[0].text
        result = self._client.images.generate(
            model=self.model_id,
            prompt=image_description,
            quality=self._quality,
            size="1536x1024",
            background="opaque",
            output_format="jpeg",
            output_compression=99,
            **self._model_args,
        )
        image_base64 = result.data[0].b64_json
        image_bytes = b64decode(image_base64)
        return Image.open(BytesIO(image_bytes))
