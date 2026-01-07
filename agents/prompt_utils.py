def flatten_prompt(prompt: str | dict[str, str]) -> str:
    """Convert a prompt to a flat string format.

    Args:
        prompt: Either a string or a dict with string keys and values.

    Returns:
        A string representation of the prompt.

    Raises:
        TypeError: If prompt is neither str nor dict.
    """
    if isinstance(prompt, str):
        return prompt

    if isinstance(prompt, dict):
        return "\n".join(
            f"{key.replace('_', ' ').capitalize()}: {value}"
            for key, value in prompt.items()
        )

    raise TypeError("Prompt must be str or dict")