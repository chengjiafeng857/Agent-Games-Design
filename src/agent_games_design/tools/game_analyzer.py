"""Game design analysis tool for analyzing game prompts."""

from langchain_core.tools import tool


@tool
def game_design_analyzer(prompt: str) -> dict[str, str]:
    """Analyze a game design prompt for key elements.

    Args:
        prompt: The game design prompt to analyze

    Returns:
        Dictionary with analysis results
    """
    prompt_lower = prompt.lower()
    
    # Detect game genre
    genres = {
        "puzzle": ["puzzle", "matching", "logic", "brain"],
        "action": ["action", "fighting", "shooter", "combat"],
        "strategy": ["strategy", "tactical", "turn-based", "real-time"],
        "rpg": ["rpg", "role-playing", "character", "leveling"],
        "simulation": ["simulation", "sim", "management", "city"],
        "platformer": ["platform", "jumping", "side-scroller"],
        "adventure": ["adventure", "exploration", "story"],
        "casual": ["casual", "mobile", "simple", "easy"]
    }
    
    detected_genre = "unknown"
    for genre, keywords in genres.items():
        if any(keyword in prompt_lower for keyword in keywords):
            detected_genre = genre
            break
    
    # Detect platform
    platforms = {
        "mobile": ["mobile", "phone", "android", "ios"],
        "pc": ["pc", "computer", "desktop", "steam"],
        "console": ["console", "xbox", "playstation", "nintendo"],
        "web": ["web", "browser", "html5"]
    }
    
    detected_platform = "unknown"
    for platform, keywords in platforms.items():
        if any(keyword in prompt_lower for keyword in keywords):
            detected_platform = platform
            break
    
    # Detect art style
    art_styles = {
        "pixel": ["pixel", "8-bit", "16-bit", "retro"],
        "realistic": ["realistic", "photorealistic", "3d"],
        "cartoon": ["cartoon", "stylized", "cute", "colorful"],
        "minimalist": ["minimal", "simple", "clean"],
        "fantasy": ["fantasy", "magic", "medieval"],
        "sci-fi": ["sci-fi", "futuristic", "space", "cyber"]
    }
    
    detected_style = "unknown"
    for style, keywords in art_styles.items():
        if any(keyword in prompt_lower for keyword in keywords):
            detected_style = style
            break
    
    return {
        "genre": detected_genre,
        "platform": detected_platform,
        "art_style": detected_style,
        "complexity": "high" if len(prompt.split()) > 20 else "low",
        "scope": "large" if any(word in prompt_lower for word in ["multiplayer", "open-world", "massive"]) else "small"
    }
