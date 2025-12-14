"""Utility functions for the agent system."""

import os

from dotenv import load_dotenv

from .output_manager import OutputManager

# Load environment variables
load_dotenv()


def get_env_var(key: str, default: str | None = None) -> str:
    """Get an environment variable or raise an error if not found.

    Args:
        key: The environment variable key
        default: Default value if the key is not found

    Returns:
        The environment variable value

    Raises:
        ValueError: If the key is not found and no default is provided
    """
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable {key} not found")
    return value


__all__ = ["get_env_var", "OutputManager"]
