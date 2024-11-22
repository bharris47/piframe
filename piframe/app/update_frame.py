import csv
import json
import os
from argparse import ArgumentParser
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Type

import boto3
from docutils.nodes import description

from piframe import models, image_utils
from piframe.config import Config
from piframe.hardware import display, power
from piframe.models import Message, MessageContent, BedrockModel, StableApi, Model
from piframe.prompts import image_description_prompt, image_generation_prompt, PromptContext
from piframe.reflection import load_class, ModuleDefinition, T
from piframe.weather import get_current_weather

def update_frame():
    parser = ArgumentParser()
    parser.add_argument("--config-path", "-c", default="config.json")
    args = parser.parse_args()

    generate_and_render_image(config_path=args.config_path)

def _instantiate_model(definition: ModuleDefinition[T], model_type_extras: dict[Type[Model], dict]) -> T:
    model_class = load_class(definition)
    model_args = definition.args
    for model_type, extras in model_type_extras.items():
        if issubclass(model_class, model_type):
            model_args.update(extras)
    return model_class(**model_args)


def generate_and_render_image(config_path: str):
    with open(config_path) as config_file:
        config = Config(**json.load(config_file))

    Path(config.artifact_directory).mkdir(exist_ok=True)

    print("Enabling display...")
    power.enable_display_power()

    bedrock = boto3.client(
        "bedrock-runtime",
    )

    model_type_extras = {
        BedrockModel: {"client": bedrock},
        StableApi: {"api_key": os.environ["STABILITY_API_KEY"]}
    }
    description_model = _instantiate_model(config.description_model, model_type_extras)
    image_model = _instantiate_model(config.image_model, model_type_extras)

    prompt_history = deque(maxlen=10)
    try:
        with open("prompt_history.json") as f:
            for row in map(json.loads, f):
                prompt_history.append(row["description"])
    except FileNotFoundError:
        pass

    battery_status = power.get_power_status()
    battery_level = power.get_battery_level()
    if battery_status:
        print(f"{battery_status=} {battery_level=}")
        battery_log = {
            "timestamp": datetime.now().isoformat(),
            "battery_level": battery_level,
            "battery_status": battery_status["battery"],
        }
        write_log(
            output_directory=config.artifact_directory,
            log_name="battery.log.csv",
            log_event=battery_log
        )

    topic_strategy = load_class(config.topic_strategy)(**config.topic_strategy.args)
    context = PromptContext(
        weather=get_current_weather(),
        battery_level=battery_level if battery_level is not None else 1.0,
        history=prompt_history,
    )
    description_prompt = image_description_prompt(
        topic_strategy=topic_strategy,
        context=context,
    )
    print(description_prompt)
    image_description = description_model.invoke([Message(content=[MessageContent(text=description_prompt)])]).strip()

    image_prompt = image_generation_prompt(image_description=image_description)
    print(image_prompt)
    image = image_model.invoke([Message(content=[MessageContent(text=image_prompt)])])

    display_image = image_utils.scale_and_crop(image, 800, 480)
    display_image = image_utils.overlay_prompt(display_image, image_description)

    print("Rendering image...")
    display.render(display_image)

    timestamp = datetime.now().isoformat()
    images_dir = Path(config.artifact_directory) / "images"
    images_dir.mkdir(exist_ok=True)
    image_path = images_dir / f"{timestamp}.jpg"
    image.save(image_path, quality=99)

    generation_log = {
        "timestamp": timestamp,
        "description_model_id": description_model.model_id,
        "description": image_description,
        "image_model_id": image_model.model_id,
        "image_prompt": image_prompt,
    }
    write_log(
        output_directory=config.artifact_directory,
        log_name="piframe.log.csv",
        log_event=generation_log
    )

    min_hour = 9
    max_hour = 23
    wakeup = datetime.now().replace(minute=0, second=0, microsecond=0)
    if wakeup.hour >= max_hour:
        wakeup = (wakeup + timedelta(days=1)).replace(hour=min_hour)
    elif wakeup.hour < min_hour:
        wakeup = wakeup.replace(hour=min_hour)
    else:
        wakeup = wakeup + timedelta(hours=1)
    print(f"Next wake up at {wakeup}.")
    power.set_current_time()
    power.set_alarm(wakeup)

    if power.is_battery_powered():
        print(f"Shutting down...")
        power.shutdown()


def write_log(output_directory: str, log_name: str, log_event: dict):
    log_path = Path(output_directory) / log_name
    write_header = not log_path.exists()
    with open(log_path, "a") as f:
        writer = csv.DictWriter(f, fieldnames=log_event.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(log_event)


if __name__ == '__main__':
    generate_and_render_image("config.json")
