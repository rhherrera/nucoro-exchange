"""Exceptions module."""
from typing import Optional


class ProviderUnavailable(Exception):
    """Class to represent an when a provider is not working."""
    message = 'Provider not working'

    def __init__(self, message: Optional[str] = None) -> None:
        if message:
            self.message = message
