from enum import Enum

class APIError(Exception):
    http_status = 500
    code = "UNEXPECTED"

    # * means the forcing of the named arguments
    def __init__(self, error_code_obj, *, details=None):
        error_code, error_message, http_status = error_code_obj
        self.code = error_code
        self.error_message = error_message
        self.http_status = http_status
        self.details = details or {} # {} is protection from None

# One-file catalog: number, message, and http_status live together here.
class ErrorCode(Enum):
    # LLM / orchestration
    LLM_RESPONSE_INTERPRETATION_ERROR = (1001, "Failed at interpretation the LLM response.", 500)
    LLM_ERROR_GETTING_CRUD_RESULT = (1002, "Failed at getting CRUD result.", 500)
    LLM_ERROR_COLLECTING_FIELDS_FOR_ENTITY_CREATION = (1003, "Failed collecting fields for creation of entity.", 400)
    LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW = (1004, "Failed collecting types of data to show.", 400)
    LLM_ERROR_COLLECTING_DATA_TO_CREATE_ENTITY = (1005, "Failed collecting data to create entity.", 400)
    LLM_ERROR_DOING_FUNCTION_CALL = (1006, "Failed doing function call.", 502)
    LLM_ERROR_RETRIEVING_BOOLEAN_RESPONSE = (1007, "Failed retrieving boolean response.", 502)
    LLM_ERROR_RETRIEVING_STRUCTURED_RESPONSE = (1008, "Failed retrieving structured response.", 502)
    LLM_ERROR_GETTING_LLM_ANSWER = (1009, "Failed getting LLM answer.", 502)
    LLM_ERROR_EMPTY_ANSWER = (1010, "Empty LLM answer.", 502)
    LLM_ERROR_NO_TEXT_ANSWER = (1011, "LLM does not have a text answer.", 502)

    # Flask error
    FLASK_ERROR_HTTP_REQUEST_INPUT_MUST_BY_JSON = (2007, "HTTP request must have the JSON type", 500)
    FLASK_ERROR_USER_QUESTION_IS_NOT_STRING = (2008, "User question is not a string", 500)

    # Generic glue / parsing
    ERROR_PARSING_BOOLEAN_RESPONSE = (3001, "Failed parsing boolean response.", 400)
    ERROR_INJECTING_FIELDS_TO_PROMPT = (3002, "Failed injecting fields to prompt.", 500)
    LOG_ERROR_FOR_FUNCTION_CALLING = (3003, "Error writing log for function calling.", 500)
    LOG_ERROR_FOR_BOOLEAN_RESPONSE = (3004, "Error writing log for boolean response.", 500)
    LOG_ERROR_FOR_STRUCTURED_RESPONSE = (3005, "Error writing log for structured response.", 500)
    ERROR_CALLING_FUNCTION = (3006, "Error calling function.", 500)
    ERROR_INTERPRETING_THE_FUNCTION_CALL = (3007, "Error interpreting the LLM response.", 500)
    ERROR_DECODING_THE_STRUCT_ANSWER_TO_JSON = (3008, "Error decoding the LLM response.", 500)
    ERROR_PERFORMING_CRUD_OPERATION = (3009, "Failed performing CRUD operations.", 500)
    TYPE_ERROR_CREATING_NEW_ENTRY = (3010, "That data type can not be created, because it is not covered in the databank system.", 400)

    WARNING_NOT_IMPLEMENTED = (9000, "Not implemented.", 501)

    def __str__(self):
        error_code, error_text, http_status = self
        return f"ErrorCode: error code: {error_code}. message: {error_text}, http status:{http_status}"

    def __repr__(self):
        error_code, error_text, http_status = self
        return f"ErrorCode: error code: {error_code}. message: {error_text}, http status:{http_status}"