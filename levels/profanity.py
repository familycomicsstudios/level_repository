from typing import Optional
from better_profanity import profanity  # pyright: ignore[reportMissingImports]

# Load the built-in profanity dictionary once at import time.
profanity.load_censor_words()


def find_profanity(text: str) -> Optional[str]:
    if not text:
        return None

    return "__blocked__" if profanity.contains_profanity(text) else None
