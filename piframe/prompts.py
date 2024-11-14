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
    "Pre-historic",
    "Futuristic",
    "Leisurely",
    "Smoking",
    "Binge-drinking",
    "Gambling",
    "Dancing",
    "Partying",
    "Baby",
    "Frozen",
    "Disproportionate",
    "Anthropomorphic",
    "Cute",
    "Evil",
]

NOUNS = [
    "Animals",
    "Hot Dogs",
    "Robots",
    "Pirates",
    "Astronauts",
    "Monsters",
    "Pickles",
    "Condiments",
    "Wizards",
    "Zombies",
    "Vampires",
    "Dogs",
    "Cats",
    "Garden Gnomes",
    "French Fries",
    "Musical Instruments",
    "Cigarettes",
    "Lobsters",
    "Computers",
    "Monsteras",
    "Planets",
]

STYLES = [
    "Pixel Art",
    "Comic Book",
    "Cel-Shaded",
    "Pop Art",
    "Art Deco",
    "1950s Cartoon",
    "Bauhaus",
    "Low-Fi",
    "Black and White",
]

TOPICS = [
    "Space",
    "Aviation",
    "Scenic Settings",
    "Historical Landmarks",
    "Animals",
    "Food",
    "Marijuana",
    "Drugs and Alcohol",
    "TV and Movies",
    "Video Games",
    "Houseplants",
    "Ancient Ruins",
    "Mythological Creatures",
    "Retro Technology",
    "Tropical Beaches",
    "Steampunk Cities",
    "Miniature Worlds",
    "Robots",
    "Dinosaurs",
    "Underwater Landscapes",
    "Alien Ecosystems",
    "Superheroes",
    "Video Game Characters",
    "Fairytale Forests",
    "Dystopian Societies",
    "Time Travel Scenarios",
    "Parallel Universes",
    "Weather Phenomena",
    "Celestial Bodies",
    "Mystical Artifacts",
    "Haunted Houses",
    "Cyberpunk Streets",
    "Outlandish Vehicles",
    "Futuristic Fashion",
    "Urban Legends",
    "Vintage Circus Acts",
    "Lost Civilizations",
    "Secret Laboratories",
    "Puppet Shows",
    "Ghost Towns",
    "Mini-Galaxies",
    "Wizardry Schools",
    "Everyday Objects as Giants",
    "Funky Patterns",
    "Sci-fi Gadgets",
    "Cathedrals",
    "Floating Islands",
    "Anthropomorphic Fruits",
    "Apocalyptic Landscapes",
    "Imaginary Friends",
    "Enchanted Castles",
    "Pop Culture Parodies",
    "Stealth Missions",
    "Extravagant Architecture",
    "Ridiculously Large Insects",
    "Alien Diners",
    "Abandoned Amusement Parks",
    "Cartoon Universes",
    "Haunted Forests",
    "Wacky Machines",
    "Alien Royalty",
    "Historical Villains",
    "Celestial Gardens",
    "Mad Scientist Labs",
    "Spectacular Failures",
    "Propaganda Posters",
    "Galactic Trading Posts",
    "Holographic Concerts",
    "Magical Portals",
    "Abnormal Animals",
    "Galactic Empires",
    "Galactic Junkyards",
    "Futuristic Appliances",
    "Underwater Wrecks",
    "Astronomical Events",
    "Nature Spirits",
    "Forbidden Libraries",
    "Villain Hideouts",
    "Samurai Warriors",
    "Alternate Earths",
    "Glamorous Monsters",
    "Legendary Battles",
    "Flying Islands",
    "Neon Cities",
    "Esoteric Symbols",
    "Sci-fi Sports",
    "Robot Dinosaurs",
    "Miniaturized Cities",
    "Cosmic Theaters",
    "Uncharted Planets",
    "Fantasy Flora",
    "Mythical Warriors",
    "Outlandish Pets",
    "Wondrous Dreams",
    "Comically Large Weapons",
    "Alien Holiday Traditions",
    "Intergalactic Zoos",
    "Mutant Powers",
    "Underwater Monsters",
    "Surrealist Landscapes",
    "Extravagant Costumes",
    "Life on Mars",
    "Sorcery Schools",
    "Legendary Swords",
    "Riddles and Ciphers",
    "Impossible Geometry",
    "Genetic Mutations",
    "Forgotten Artifacts",
    "Fantasy Cuisine",
    "Interactive Holograms",
    "Extraterrestrial Festivals",
    "San Francisco, CA",
    "Houston, TX"
]

IMAGE_DESCRIPTION_PROMPT ="""You generate image descriptions for a text-to-image generator.

Requirements
- Limit the description to 15 words.
- Be extremely detailed about the setting and subject.
- Descriptions must be hilarious.
- The day of the week cannot be directly represented visually, but abstract is fine.
- Exclude quotes, exclamations, or other sayings as they will not be reflected in the image.
- Nudity is strictly forbidden.
- Do not mention real people.

Use the following context to tailor your descriptions
- prefer holiday themes on known holidays
- incorporate weather conditions where it makes sense
- morning/afternoon/evening/night scenes based on the time
- wakeful, or sleepy themes depending on my wake up and bed times

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
        f"- Wake Up Time: 09:00 AM",
        f"- Bed Time: 11:00 PM",
    ]
    if weather:
        contexts.append(f"- Weather: {weather.temperature:.0f} °F {weather.description}")
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
    return (f"{image_description} High-contrast, flat, solid colors with bold lines, minimal shading, simplified details, {style} style.")
