"""Errors that can be shown directly to a CLI user."""


class InputError(ValueError):
    """Invalid configuration, repository metadata, or analysis request."""
