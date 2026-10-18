def clean_code(raw: str) -> str:
    raw = raw.replace("```html", "").replace("```", "").strip()
    return raw