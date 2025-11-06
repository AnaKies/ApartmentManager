from enum import Enum

class APIError(Exception):
    code = "UNEXPECTED"

    def __init__(self, error_code_obj, trace_id=None):
        # Extract a code and message from the enum ErrorCode
        error_code, error_message = error_code_obj.value
        self.code = error_code
        self.error_message = error_message

        if trace_id:
            self.trace_id = trace_id

    def __str__(self):
        if isinstance(self.code, Enum):
            error_code, error_text = self.code.value
        else:
            error_code = self.code or "-"
            error_text = getattr(self, "error_message", "-")

        trace = getattr(self, "trace_id", "-")
        return f"APIError {error_code}: {error_text} (trace_id={trace})"

    def __repr__(self):
        if isinstance(self.code, Enum):
            error_code, error_text = self.code.value
        else:
            error_code = self.code or "-"
            error_text = getattr(self, "error_message", "-")

        trace = getattr(self, "trace_id", "-")
        return f"<APIError code={error_code} message='{error_text}' trace_id={trace}>"

class ErrorCode(Enum):
    # LLM
    LLM_RESPONSE_INTERPRETATION_ERROR = (1001, "Failed at interpretation the LLM response.")
    LLM_ERROR_GETTING_CRUD_RESULT = (1002, "Failed at getting CRUD result.")
    LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW = (1004, "Failed collecting types of data to show.")
    LLM_ERROR_COLLECTING_DATA_TO_CREATE_ENTITY = (1005, "Failed collecting data to create entity.")
    LLM_ERROR_DOING_FUNCTION_CALL = (1006, "Failed doing function call.")
    LLM_ERROR_RETRIEVING_BOOLEAN_RESPONSE = (1007, "Failed retrieving boolean response.")
    LLM_ERROR_RETRIEVING_STRUCTURED_RESPONSE = (1008, "Failed retrieving structured response.")
    LLM_ERROR_EMPTY_ANSWER = (1010, "Empty LLM answer.")
    LLM_ERROR_NO_TEXT_ANSWER = (1011, "LLM does not have a text answer.")

    # SQL error
    SQL_ERROR_CREATING_NEW_PERSON = (1500, "Failed creating new person.")
    SQL_NOT_ALLOWED_FIELDS = (1501, "Not allowed fields for creating new entry in database.")
    SQL_LOG_ERROR_FOR_FUNCTION_CALLING = (3003, "Error writing log for function calling.")
    SQL_LOG_ERROR_FOR_BOOLEAN_RESPONSE = (3004, "Error writing log for boolean response.")
    SQL_LOG_ERROR_FOR_STRUCTURED_RESPONSE = (3005, "Error writing log for structured response.")

    # Flask error
    FLASK_ERROR_HTTP_REQUEST_INPUT_MUST_BY_JSON = (2007, "HTTP request must have the JSON type")
    FLASK_ERROR_USER_QUESTION_IS_NOT_STRING = (2008, "User question is not a string")

    # Generic glue / parsing
    ERROR_PARSING_BOOLEAN_RESPONSE = (3001, "Failed parsing boolean response.")
    ERROR_INJECTING_FIELDS_TO_PROMPT = (3002, "Failed injecting fields to prompt.")
    ERROR_CALLING_FUNCTION = (3006, "Error calling function.")
    ERROR_INTERPRETING_THE_FUNCTION_CALL = (3007, "Error interpreting the LLM response.")
    ERROR_DECODING_THE_STRUCT_ANSWER_TO_JSON = (3008, "Error decoding the LLM response.")
    ERROR_PERFORMING_CRUD_OPERATION = (3009, "Failed performing CRUD operations.")
    TYPE_ERROR_CREATING_NEW_ENTRY = (3010, "That data type can not be created, because it is not covered in the databank system.")
    LOG_ERROR_LOG_CREATION = (3011, "log_error requires at least one of 'error_details' or 'exception'.")

    WARNING_NOT_IMPLEMENTED = (9000, "Not implemented.")

    def __str__(self):
        error_code, error_text = self
        return f"ErrorCode: error code: {error_code}. message: {error_text}"

    def __repr__(self):
        error_code, error_text = self
        return f"ErrorCode: error code: {error_code}. message: {error_text}"