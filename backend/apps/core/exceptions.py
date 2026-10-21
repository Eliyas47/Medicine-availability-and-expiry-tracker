"""
Custom exception handler that returns a consistent error envelope.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Wrap DRF's default exception response in a consistent structure:

    {
        "error": {
            "code": "validation_error",
            "message": "...",
            "details": { ... }   # only on validation errors
        }
    }
    """
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception — let Django's 500 handler deal with it
        return None

    error_payload = {}

    if response.status_code == status.HTTP_400_BAD_REQUEST:
        error_payload["code"] = "validation_error"
        error_payload["message"] = "Invalid input."
        error_payload["details"] = response.data

    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
        error_payload["code"] = "authentication_required"
        error_payload["message"] = _extract_message(response.data, "Authentication credentials were not provided.")

    elif response.status_code == status.HTTP_403_FORBIDDEN:
        error_payload["code"] = "permission_denied"
        error_payload["message"] = _extract_message(response.data, "You do not have permission to perform this action.")

    elif response.status_code == status.HTTP_404_NOT_FOUND:
        error_payload["code"] = "not_found"
        error_payload["message"] = _extract_message(response.data, "Resource not found.")

    elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        error_payload["code"] = "method_not_allowed"
        error_payload["message"] = _extract_message(response.data, "Method not allowed.")

    elif response.status_code == status.HTTP_409_CONFLICT:
        error_payload["code"] = "conflict"
        error_payload["message"] = _extract_message(response.data, "A conflict occurred.")

    elif response.status_code == 422:
        error_payload["code"] = "business_rule_violation"
        error_payload["message"] = _extract_message(response.data, "Business rule violation.")
        error_payload["details"] = response.data

    else:
        error_payload["code"] = "error"
        error_payload["message"] = _extract_message(response.data, "An error occurred.")

    response.data = {"error": error_payload}
    return response


def _extract_message(data, default: str) -> str:
    if isinstance(data, dict):
        for key in ("detail", "message", "non_field_errors"):
            if key in data:
                val = data[key]
                if isinstance(val, list) and val:
                    return str(val[0])
                return str(val)
    if isinstance(data, list) and data:
        return str(data[0])
    return default
