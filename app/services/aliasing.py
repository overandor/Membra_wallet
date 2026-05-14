def normalize_alias(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("Alias is required")
    return text
