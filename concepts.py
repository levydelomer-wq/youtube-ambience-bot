"""Pool of ambience concepts for random selection."""

import random
from bot_types import Concept

CONCEPTS: list[Concept] = [
    {
        "ambience": "cozy fireplace",
        "mood": "warm, relaxing, winter night",
        "duration": "2 hours"
    },
    {
        "ambience": "thunderstorm",
        "mood": "dramatic, powerful, rain, cozy indoor view",
        "duration": "2 hours"
    },
    {
        "ambience": "rainy window",
        "mood": "calm, peaceful, rain drops on glass, soft lighting",
        "duration": "2 hours"
    },
    {
        "ambience": "ocean waves",
        "mood": "serene, beach sunset, gentle waves, relaxing",
        "duration": "2 hours"
    },
    {
        "ambience": "forest stream",
        "mood": "peaceful, nature, flowing water, birds chirping",
        "duration": "2 hours"
    },
    {
        "ambience": "snowy cabin",
        "mood": "cozy, winter, snowfall outside window, warm interior",
        "duration": "2 hours"
    },
    {
        "ambience": "night rain city",
        "mood": "urban, neon lights, rain on window, lo-fi aesthetic",
        "duration": "2 hours"
    },
    {
        "ambience": "mountain sunrise",
        "mood": "peaceful, golden hour, misty mountains, serene",
        "duration": "2 hours"
    },
    {
        "ambience": "japanese garden",
        "mood": "zen, tranquil, water fountain, peaceful",
        "duration": "2 hours"
    },
    {
        "ambience": "autumn rain",
        "mood": "cozy, fall leaves, gentle rain, warm colors",
        "duration": "2 hours"
    },
]


def get_random_concept() -> Concept:
    """Return a random concept from the pool."""
    return random.choice(CONCEPTS)


def get_concept_by_name(name: str) -> Concept | None:
    """Return a concept by ambience name, or None if not found."""
    for concept in CONCEPTS:
        if concept["ambience"].lower() == name.lower():
            return concept
    return None
