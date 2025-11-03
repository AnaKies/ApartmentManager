class APIError(Exception):
    http_status = 500
    code = "UNEXPECTED"
    user_message = "internal_error"

    # * means the forcing of the named arguments
    def __init__(self, *, code=None, user_message=None, details=None):
        super().__init__(user_message or self.user_message) # for log tracing
        if code:
            self.code = code
        if user_message:
            self.user_message = user_message
        self.details = details or {} # trick: each call has its own dict

# All these error classes have the constructor method from their parent
class ValidationError(APIError):
    http_status = 400
    code = "VALIDATION_ERROR"
    user_message = "`user_input` is required"

class BadContentTypeError(APIError):
    http_status = 415
    code = "UNSUPPORTED_MEDIA_TYPE"
    user_message = "Content-Type must be application/json"

class NotFoundError(APIError):
    http_status = 404
    code = "NOT_FOUND"
    user_message = "not_found"

class ServiceUnavailableError(APIError):
    http_status = 503
    code = "SERVICE_UNAVAILABLE"
    user_message = "service_unavailable"

class LLMOverloadedError(ServiceUnavailableError):
    code = "LLM_OVERLOADED"
    user_message = "llm_unavailable"