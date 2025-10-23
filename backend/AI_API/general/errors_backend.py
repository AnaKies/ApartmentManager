from enum import Enum

class ErrorCode(str, Enum):
    LLM_RESPONSE_INTERPRETATION_ERROR = "Failed at interpretation the LLM response."
    LLM_ERROR_GETTING_CRUD_RESULT = "Failed at getting CRUD result."
    LLM_ERROR_COLLECTING_FIELDS_FOR_ENTITY_CREATION = "Failed collecting fields for creation of entity."
    LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW = "Failed collecting types of data to show."
    LLM_ERROR_COLLECTING_DATA_TO_CREATE_ENTITY = "Failed collecting data to create entity."

    ERROR_INJECTING_FIELDS_TO_PROMPT = "Failed injecting fields to prompt."
    LOG_ERROR_FOR_FUNCTION_CALLING = "Error writing log for function calling."
    ERROR_CALLING_FUNCTION = "Error calling function."
    ERROR_INTERPRETING_THE_FUNCTION_CALL = "Error interpreting the LLM response."
