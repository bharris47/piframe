import csv
import json
import logging
import os
from argparse import ArgumentParser
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Type

import boto3
from croniter import croniter

from piframe import image_utils
from piframe.config import Config
from piframe.hardware import display, power
from piframe.models import Message, MessageContent, BedrockModel, StableApi, Model
from piframe.prompts import image_description_prompt, image_generation_prompt, PromptContext, image_title_prompt
from piframe.reflection import load_class, ModuleDefinition, T
from piframe.weather import get_current_weather

logging.basicConfig(level=logging.ERROR)

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
    power.set_current_time()

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

    battery_level = log_battery_status(config)

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
    title_prompt = image_title_prompt(description=image_description)
    image_title = description_model.invoke([Message(content=[MessageContent(text=title_prompt)])]).strip()
    image_prompt = image_generation_prompt(image_description=image_description)
    print(f"{image_title=} {image_prompt=}")

    image = image_model.invoke([Message(content=[MessageContent(text=image_prompt)])])
    display_image = image_utils.scale_and_crop(image, 800, 480)
    display_image = image_utils.overlay_prompt(display_image, image_title)

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
        "title": image_title,
        "description": image_description,
        "image_model_id": image_model.model_id,
        "image_prompt": image_prompt,
    }
    write_log(
        output_directory=config.artifact_directory,
        log_name="piframe.log.csv",
        log_event=generation_log
    )

    cron = croniter(config.schedule, datetime.now())
    wakeup = cron.get_next(datetime)
    print(f"Next wake up at {wakeup}.")
    power.set_alarm(wakeup)

    if power.is_battery_powered():
        print(f"Shutting down...")
        power.shutdown()


def log_battery_status(config):
    battery_info = power.get_battery_info()
    if battery_info:
        print(f"{battery_info=}")
        battery_log = {
            "timestamp": datetime.now().isoformat(),
            "battery_level": battery_info["charge_level"],
            "battery_status": battery_info["status"],
            "power_input": battery_info["power_input"],
            "power_input_5v": battery_info["power_input_5v"],
            "temperature_c": battery_info["temperature_c"],
            "voltage_mv": battery_info["voltage_mv"],
            "current_ma": battery_info["current_ma"],
            "io_voltage_mv": battery_info["io_voltage_mv"],
            "io_current_ma": battery_info["io_current_ma"],
            "profile": json.dumps(battery_info["profile"]),
            "faults": json.dumps(battery_info["faults"]),
        }
        write_log(
            output_directory=config.artifact_directory,
            log_name="battery.log.csv",
            log_event=battery_log
        )
    return battery_info.get("charge_level")


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
