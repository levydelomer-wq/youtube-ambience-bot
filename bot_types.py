from typing import TypedDict


class Concept(TypedDict):
    ambience: str
    mood: str
    duration: str


class Metadata(TypedDict):
    title: str
    description: str
    tags: list[str]


class Prompts(TypedDict):
    image_prompt: str
    video_prompt: str
