def flatten_prompt(prompt):
    if isinstance(prompt, str):
        return prompt

    if isinstance(prompt, dict):
        return "\n".join(
            f"{key.replace('_', ' ').capitalize()}: {value}"
            for key, value in prompt.items()
        )

    raise TypeError("Prompt must be str or dict")

# TODO move to utils/