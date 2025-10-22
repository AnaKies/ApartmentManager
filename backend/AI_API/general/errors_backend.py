from enum import Enum

class ErrorCode(str, Enum):
    LLM_RESPONSE_INTERPRETATION_ERROR = "Failed at interpretation the LLM response."
    INPUT_VALIDATION_FAILED = "INPUT_VALIDATION_FAILED"