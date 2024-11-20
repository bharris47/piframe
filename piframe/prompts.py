import random
from datetime import datetime
from typing import Iterable

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
    "Pixel Art",
    "Comic Book",
    "Pop Art",
    "Art Deco",
    "1950s Cartoon",
    "Bauhaus",
    "Low-Fi",
    "Surrealist",
    "Ukiyo-e",
]

IMAGE_DESCRIPTION_PROMPT ="""You generate ridiculous image descriptions for a text-to-image generator.

Requirements
- Limit the description to 15 words.
- Be extremely detailed about the setting and subject.
- Descriptions must be non-sensical and hilarious.
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

SIMPLE_PROMPT = """Give me 5 sentences in the form of <adjective> <noun> in <location> <action>. 
- Make them funny and moderately ridiculous.
- Nudity is strictly forbidden.
- Do not mention real people.

The sentences must match the vibe of the current conditions:
{context}

Respond only a JSON list containing the sentences."""

def image_description_prompt(battery: float, history: Iterable[str], weather: Weather):
    date = datetime.now()
    date_str = date.strftime("%A, %B %d, %Y")
    time_str = date.strftime("%I:%M %p")

    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS) if battery > 0.05 else "Batteries"
    topics_str = f"{adjective} {noun}"

    history_str = ""
    if history:
        history_str = "Do not repeat concepts. Here are some recent descriptions you've generated:\n"
        history_str += "\n".join([f"- {desc}" for desc in history])

    contexts = [
        f"- Date: {date_str}",
        f"- Time: {time_str}",
    ]
    if weather:
        contexts.append(f"- Current Weather: {weather.temperature:.0f} °F {weather.description}")
    context_str = "\n".join(contexts)

    return IMAGE_DESCRIPTION_PROMPT.format(
        context=context_str,
        topic=topics_str,
        history=history_str,
    )

def image_generation_prompt(image_description: str):
    style = random.choice(STYLES)
    if not image_description.endswith("."):
        image_description += "."
    return (f"{image_description} High-contrast, sharp lines, minimal shading, black, white, red, yellow, green, blue, and orange, vibrant colors, {style} style.")
