import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from piframe.weather import Weather

ADJECTIVES = [
    "Cozy",
    "Mischevious",
    "Space",
    "Office-worker",
    "Glamorous",
    "Deceptive",
    "Stylish",
    "Leisurely",
    "Lounging",
    "Smoking",
    "Binge-drinking",
    "Dancing",
    "Partying",
    "Cute",
    "Evil",
    "Psychedelic",
    "Gangster",
]

NOUNS = [
    "Animals",
    "Hot Dogs",
    "Robots",
    "Astronauts",
    "Pickles",
    "Condiments",
    "Wizards",
    "Zombies",
    "Dogs",
    "Cats",
    "Garden Gnomes",
    "French Fries",
    "Musical Instruments",
    "Lobsters",
    "Monsteras",
    "House Plants",
    "Aliens",
    "Fruits",
]

STYLES = [
    "Line Art, filled with flat, vibrant colors, clean lines, minimal shading.",
    "Ink Drawing, bright colors, clean lines, minimal shading.",
    "Comic Book style, bold colors, high contrast, strong use of negative space.",
    "Pixel Art, colorful, sharp, stylized, retro video game feel.",
    "Stippling portrait, smooth, colorfully, inked outlines with gentle stipple-style shading.",
    "Vector Art style, hard-edged shapes and limited color palette, no gradients, no shading bold colors, geometric.",
    "Gouache style, deep midtones, high saturation, soft gradients, gentle blending, minimal outlines.",
    "Retro Risograph, grain textures, high contrast colors, duotone feel.",
]

IMAGE_DESCRIPTION_PROMPT = """You generate ridiculous image descriptions for a text-to-image generator.

Requirements
- Be extremely detailed about the setting and subject.
- Descriptions must be hilarious.
- The day of the week cannot be directly represented visually, but abstract is fine.
- Exclude quotes, exclamations, or other sayings as they will not be reflected in the image.
- Nudity is strictly forbidden.
- Do not mention real people.

Use the following context to tailor your descriptions
- morning/afternoon/evening/night scenes based on the time
- incorporate current weather conditions
- holiday themes on known holidays

{context}

Write a description about {topic}.

Respond only with the image description in plain text.
"""

IMAGE_TITLE_PROMPT = """You generate artsy-fartsy artwork titles given an image description.

Titles should be succinct, mildly cryptic, but capture the overall vibes of the description.

Image description:
{description}

Limit titles to 10 words or fewer.
Respond only with the title in plain text.
"""


@dataclass
class PromptContext:
    battery_level: float
    weather: Weather
    history: Iterable[str]


class TopicStrategy(ABC):
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_topic(self, context: PromptContext):
        raise NotImplementedError


class RandomAdlib(TopicStrategy):
    def __init__(
        self, adjectives: Optional[list[str]] = None, nouns: Optional[list[str]] = None
    ):
        super().__init__()
        self._adjectives = adjectives or ADJECTIVES
        self._nouns = nouns or NOUNS

    def get_topic(self, context: PromptContext):
        adjective = random.choice(self._adjectives)
        noun = random.choice(self._nouns)
        return f"{adjective} {noun}"


def image_description_prompt(topic_strategy: TopicStrategy, context: PromptContext):
    timestamp = datetime.now()
    date_str = timestamp.strftime("%A, %B %d, %Y")
    time_str = timestamp.strftime("%I:%M %p")

    history_str = ""
    if context.history:
        history_str = "Do not repeat concepts. Here are some recent descriptions you've generated:\n"
        history_str += "\n".join([f"- {desc}" for desc in context.history])

    contexts = [
        f"- Date: {date_str}",
        f"- Time: {time_str}",
    ]
    if weather := context.weather:
        contexts.append(
            f"- Current Weather: {weather.temperature:.0f} °F {weather.description}"
        )
    context_str = "\n".join(contexts)

    topic = topic_strategy.get_topic(context)

    if context.battery_level <= 0.2:
        topic = f"{topic} and drained batteries"
    else:
        if timestamp.hour >= 18:
            topic = f"{topic} at happy hour"

    return IMAGE_DESCRIPTION_PROMPT.format(
        context=context_str,
        topic=topic,
        history=history_str,
    )


def image_title_prompt(description: str):
    return IMAGE_TITLE_PROMPT.format(description=description)


def image_generation_prompt(image_description: str):
    style = random.choice(STYLES)
    if not image_description.endswith("."):
        image_description += "."
    return f"{image_description} {style}"
