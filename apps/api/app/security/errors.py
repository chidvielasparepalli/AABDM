"""Security-related exceptions."""


class SSrfBlocked(Exception):
    """Raised when a URL is rejected as a Server-Side Request Forgery risk."""
