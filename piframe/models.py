import json
from abc import ABC, abstractmethod
from base64 import b64decode
from dataclasses import dataclass, asdict
from io import BytesIO
from typing import Literal, TypeVar, Generic

from PIL import Image

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
    def __init__(self, client, model_id: str, **kwargs):
        self._client = client
        self.model_id = model_id
        self._model_args = kwargs

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


class Anthropic(Model[str]):
    def _get_request_body(self, messages: list[Message]) -> dict:
        messages = [asdict(message) for message in messages]
        return {
            "messages": messages,
            **self._model_args,
        }

    def _parse_response(self, response: dict) -> str:
        return response["content"][0]["text"]

class Meta(Model[str]):
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

class StableImage(Model[Image.Image]):
    def _get_request_body(self, messages: list[Message]) -> dict:
        return {
            "prompt": messages[0].content[0].text,
            "mode": "text-to-image",
            **self._model_args,
        }

    def _parse_response(self, response: dict) -> Image.Image:
        image_bytes = b64decode(response["images"][0])
        return Image.open(BytesIO(image_bytes))


class StableXL(Model[Image.Image]):
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

class TitanImage(Model[Image.Image]):
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