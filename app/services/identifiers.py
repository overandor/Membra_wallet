def normalize_alias(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("Identifier is required")
    return text
