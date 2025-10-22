from enum import Enum

class ErrorCode(str, Enum):
    LLM_RESPONSE_INTERPRETATION_ERROR = "Failed at interpretation the LLM response."
    LLM_ERROR_GETTING_CRUD_RESULT = "Failed at getting CRUD result."

    ERROR_INJECTING_FIELDS_TO_PROMPT = "Failed injecting fields to prompt."
    LOG_ERROR_FOR_FUNCTION_CALLING = "Error writing log for function calling."
    ERROR_AT_CALLING_FUNCTION = "Error calling function."
    ERROR_INTERPRETING_THE_FUNCTION_CALL = "Error interpreting the LLM response."
