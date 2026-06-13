# Simple safety check for user input.

# Words that suggest a prompt injection attack
INJECTION_WORDS = [
    "ignore previous",
    "forget your instructions",
    "you are now",
    "new instructions",
    "act as",
    "pretend you are",
    "jailbreak",
    "override",
]

# Food-related words — input must contain at least one of these
FOOD_WORDS = [
    "recipe", "food", "cook", "meal", "ingredient", "eat", "diet",
    "nutrition", "vegan", "vegetarian", "breakfast", "lunch", "dinner",
    "snack", "dessert", "protein", "calorie", "spice", "bake", "fry",
    "boil", "grill", "steam", "plan", "gluten", "dairy", "chicken",
    "beef", "fish", "pasta", "soup", "salad", "bread", "cake",
]


def is_safe(text: str) -> bool:
    """
    Returns True if the input is safe and on-topic.
    Returns False if it looks like an attack or is off-topic.
    """
    lower = text.lower()

    # Block prompt injection attempts
    for word in INJECTION_WORDS:
        if word in lower:
            print(f"[SAFETY BLOCKED] Injection attempt: '{word}'")
            return False

    # Short greetings are fine (hi, hello, thanks)
    if len(text.strip()) < 20:
        return True

    # Longer messages must mention food
    if not any(word in lower for word in FOOD_WORDS):
        print(f"[SAFETY BLOCKED] Off-topic message: '{text[:60]}'")
        return False

    return True
