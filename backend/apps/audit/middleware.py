"""
Audit middleware — captures the current request user and IP address
and makes them available to signal handlers via thread-local storage.
"""
import threading

_thread_locals = threading.local()


def get_current_user():
    """Return the user from the current request (or None for system actions)."""
    return getattr(_thread_locals, "user", None)


def get_current_ip():
    """Return the IP address from the current request."""
    return getattr(_thread_locals, "ip_address", None)


class AuditMiddleware:
    """
    Stores the authenticated user and client IP in thread-local storage
    so that Django signal handlers (post_save, post_delete) can log them
    without having access to the request object.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, "user", None)
        _thread_locals.ip_address = self._get_client_ip(request)

        response = self.get_response(request)

        # Clean up after request to avoid stale data
        _thread_locals.user = None
        _thread_locals.ip_address = None

        return response

    @staticmethod
    def _get_client_ip(request) -> str:
        """Extract real client IP, respecting X-Forwarded-For in production."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
