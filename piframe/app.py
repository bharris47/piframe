import csv
import json
import os
from argparse import ArgumentParser
from collections import deque
from datetime import datetime
from pathlib import Path

import boto3
from PIL import Image

from piframe import models, image_utils, display
from piframe.models import Message, MessageContent
from piframe.prompts import image_description_prompt, image_generation_prompt
from piframe.weather import get_current_weather

def update_frame():
    parser = ArgumentParser()
    parser.add_argument("--output-directory", "-o", default=".")
    args = parser.parse_args()

    generate_and_render_image(output_directory=args.output_directory)

def generate_and_render_image(output_directory: str):
    bedrock = boto3.client(
        "bedrock-runtime",
    )

    description_model = models.Meta(
        client=bedrock,
        # model_id="us.meta.llama3-2-90b-instruct-v1:0",
        model_id="meta.llama3-1-405b-instruct-v1:0",
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
    # image_model = models.StableImage(
    #     client=bedrock,
    #     # model_id="stability.stable-image-core-v1:0",
    #     model_id="stability.sd3-large-v1:0",
    #     # model_id="stability.stable-image-ultra-v1:0",
    #     aspect_ratio="16:9",
    #     output_format="jpg",
    #     negative_prompt="hazy, cloudy, foggy, diffuse, blur",
    # )
    # image_model = models.StableDiffusion3x(
    #     model_id="sd3.5-large",
    #     api_key=os.environ["STABILITY_API_KEY"],
    #     aspect_ratio="16:9",
    #     negative_prompt="hazy, cloudy, foggy, diffuse, blur",
    # )
    image_model = models.StableImageUltra(
        model_id="stable-image-ultra-api",
        api_key=os.environ["STABILITY_API_KEY"],
        aspect_ratio="16:9",
        negative_prompt="hazy, cloudy, foggy, diffuse, blur",
    )
    # image_model = models.TitanImage(
    #     client=bedrock,
    #     model_id="amazon.titan-image-generator-v2:0",
    #     imageGenerationConfig={
    #         "quality": "premium",
    #         "width": 1280,
    #         "height": 768,
    #     }
    # )

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

    display_image = image_utils.scale_and_crop(image, 800, 480)
    display_image = image_utils.overlay_prompt(display_image, image_description)
    display.render(display_image)

    timestamp = datetime.now().isoformat()
    images_dir = Path(output_directory) / "images"
    images_dir.mkdir(exist_ok=True)
    image_path = images_dir / f"{timestamp}.jpg"
    image.save(image_path, quality=99)

    event = {
        "timestamp": timestamp,
        "description_model_id": description_model.model_id,
        "description": image_description,
        "image_model_id": image_model.model_id,
        "image_prompt": image_prompt,
    }
    log_path = Path(output_directory) / "piframe.log.csv"
    write_header = not log_path.exists()
    with open(log_path, "a") as f:
        writer = csv.DictWriter(f, fieldnames=event.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(event)


if __name__ == '__main__':
    update_frame()
