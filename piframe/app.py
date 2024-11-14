import json
from collections import deque
from datetime import datetime

import boto3

from piframe import models
from piframe.models import Message, MessageContent
from piframe.prompts import image_description_prompt, image_generation_prompt
from piframe.weather import get_current_weather


def main():
    bedrock = boto3.client(
        "bedrock-runtime",
    )

    description_model = models.Meta(
        client=bedrock,
        model_id="us.meta.llama3-2-90b-instruct-v1:0",
        max_gen_len=100,
        temperature=1.0,
    )
    # description_model = models.Anthropic(
    #     client=bedrock,
    #     model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    #     anthropic_version="bedrock-2023-05-31",
    #     max_tokens=100,
    #     temperature=1.0,
    # )
    image_model = models.StableImage(
        client=bedrock,
        model_id="stability.stable-image-core-v1:0",
        # model_id="stability.sd3-large-v1:0",
        # model_id="stability.stable-image-ultra-v1:0",
        aspect_ratio="16:9",
        output_format="jpg",
    )

    prompt_history = deque(maxlen=10)
    try:
        with open("prompt_history.json") as f:
            for row in map(json.loads, f):
                prompt_history.append(row["description"])
    except FileNotFoundError:
        pass

    battery = 1.0
    weather = get_current_weather()
    description_prompt = image_description_prompt(
        battery=battery,
        history=[],
        weather=weather,
    )
    print(description_prompt)
    image_description = description_model.invoke([Message(content=[MessageContent(text=description_prompt)])]).strip()

    image_prompt = image_generation_prompt(image_description=image_description)
    print(image_prompt)
    image = image_model.invoke([Message(content=[MessageContent(text=image_prompt)])])
    image.save(f"images/{datetime.now().isoformat()}.jpg", quality=99)

    with open("prompt_history.json", "a") as f:
        f.write(json.dumps({"timestamp": datetime.now().isoformat(), "description": image_description}) + "\n")


if __name__ == '__main__':
    main()